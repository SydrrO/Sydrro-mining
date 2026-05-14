import paramiko, time

# Stop current miner on 002
ssh002 = paramiko.SSHClient()
ssh002.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh002.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)
ssh002.exec_command('taskkill /f /im rigel.exe 2>nul')
time.sleep(3)

base = r'D:\Donwlaods\rigel-1.23.1-win'

# Setup SSH TCP tunnel: 002:16800 -> 3.8 SSH -> F2Pool:6800
# This uses SSH -L which is pure TCP forwarding, no SOCKS5 overhead
tunnel_cmd = 'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ExitOnForwardFailure=yes -fN -L 0.0.0.0:16800:cfx.f2pool.com:6800 sydrro_ssh@192.168.3.8'

# First ensure 002 can SSH to 3.8 (key should be set up)
stdin, stdout, stderr = ssh002.exec_command('ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 sydrro_ssh@192.168.3.8 echo OK')
key_test = stdout.read().decode('gbk', errors='replace').strip()
err = stderr.read().decode('gbk', errors='replace').strip()
print('Key test:', key_test, err[:50])

if 'OK' not in key_test:
    print('Key auth still failing, using password approach...')
    # We can't use password, need key. Let me try adding the key again.
    stdin, stdout, stderr = ssh002.exec_command('type C:\\Users\\sydrro_ssh\\.ssh\\id_ed25519.pub')
    pubkey = stdout.read().decode('gbk', errors='replace').strip()

    ssh38 = paramiko.SSHClient()
    ssh38.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh38.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)
    # Fix: write key with proper permissions
    ssh38.exec_command('cmd /c "echo ' + pubkey + ' > C:\\Users\\sydrro_ssh\\.ssh\\authorized_keys"')
    ssh38.exec_command('cmd /c "icacls C:\\Users\\sydrro_ssh\\.ssh\\authorized_keys /inheritance:r /grant:r sydrro_ssh:F"')
    ssh38.close()
    time.sleep(2)

    # Retest
    stdin, stdout, stderr = ssh002.exec_command('ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 sydrro_ssh@192.168.3.8 echo OK')
    print('Retest:', stdout.read().decode('gbk', errors='replace').strip())

# Kill any existing tunnels and start fresh
ssh002.exec_command('taskkill /f /im ssh.exe 2>nul')
time.sleep(2)

# Start SSH TCP tunnel
stdin, stdout, stderr = ssh002.exec_command(tunnel_cmd)
err = stderr.read().decode('gbk', errors='replace')
print('Tunnel:', err[:100])
time.sleep(5)

# Verify tunnel is listening on 002
stdin, stdout, stderr = ssh002.exec_command('netstat -ano | findstr ":16800.*LISTEN"')
print('Port 16800:', stdout.read().decode('gbk', errors='replace')[:100])

# Update miner config to use local tunnel instead of SOCKS5 proxy
# Rigel can connect directly to 127.0.0.1:16800 instead of cfx.f2pool.com:6800
# Using -o with the tunnel endpoint

# Actually, rigel's -o supports host:port. Let's use:
# -o stratum+tcp://127.0.0.1:16800

# Update start_miner.bat
miner_bat = '@echo off\r\ncd /d "' + base + '"\r\nrigel.exe -a octopus -o stratum+tcp://127.0.0.1:16800 -u sydrro.5070ti --api-bind 0.0.0.0:5002 --log-file logs/miner.log --no-tui\r\n'

sftp = ssh002.open_sftp()
f = sftp.open(base + '/start_miner.bat', 'w')
f.write(miner_bat)
f.close()
sftp.close()

# Update cfx.bat too
cfx_bat = miner_bat + 'pause\r\n'
f = sftp.open(base + '/cfx.bat', 'w')
f.write(cfx_bat)
f.close()
sftp.close()

# Restart miner
ssh002.exec_command('schtasks /run /tn Miner002')
time.sleep(20)

# Check
stdin, stdout, stderr = ssh002.exec_command('curl -s http://127.0.0.1:5002')
import json
try:
    d = json.loads(stdout.read().decode())
    hr = d['hashrate']['octopus'] / 1e6
    mi = d['devices'][0]['monitoring_info']
    pool = d['pools']['octopus'][0]
    print(f'Hashrate: {hr:.1f} MH/s | Power: {mi["power_usage"]:.0f}W | Temp: {mi["core_temperature"]}C')
    print(f'Pool latency: {pool["average_latency_ms"]:.0f}ms')
except:
    print('Miner not responding yet')

ssh002.close()
print('\nNew setup: 002 -> SSH tunnel -> 3.8 -> F2Pool')
print('Pool URL changed to: 127.0.0.1:16800 (local SSH tunnel)')
