import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

xmrig_dir = r'C:\Users\25623\OneDrive\Desktop\xmrig\xmrig-6.22.2'

# Create batch file via SFTP
bat_path = 'C:/Users/25623/OneDrive/Desktop/xmrig/xmrig-6.22.2/start.bat'
sftp = ssh.open_sftp()

# Ryzen 5800X has 8 cores / 16 threads. Use 14 threads (leave 2 for system/GPU)
# --threads=14 --cpu-affinity to pin threads
bat = '@echo off\r\n'
bat += 'cd /d "%~dp0"\r\n'
bat += 'xmrig.exe -o stratum+tcp://xmr.f2pool.com:5700 -u sydrro.5800x -p x --coin monero --threads=14 --cpu-priority=5 --donate-level=1 --http-host=0.0.0.0 --http-port=6000 --log-file=xmrig.log\r\n'

f = sftp.open(bat_path, 'w')
f.write(bat)
f.close()
sftp.close()
print('Batch file written')

# Kill old task if exists
ssh.exec_command('schtasks /end /tn "CPUMiner" 2>nul')
ssh.exec_command('schtasks /delete /tn "CPUMiner" /f 2>nul')
time.sleep(1)

# Create scheduled task
tr = '"' + bat_path + '"'
create = f'schtasks /create /tn "CPUMiner" /tr {tr} /sc once /st 00:00 /sd 01/01/2024 /ru 25623 /f'
stdin, stdout, stderr = ssh.exec_command(create)
print('Create:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

time.sleep(1)
stdin, stdout, stderr = ssh.exec_command('schtasks /run /tn "CPUMiner"')
print('Run:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

time.sleep(10)

# Check if running
stdin, stdout, stderr = ssh.exec_command('powershell.exe -Command "Get-Process -Name xmrig -ErrorAction SilentlyContinue | Select-Object Id, CPU"')
result = stdout.read().decode('gbk', errors='replace')
if result.strip():
    print('SUCCESS! XMRig running:')
    print(result)

    # Try API
    time.sleep(5)
    stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:6000/1/summary 2>nul')
    api = stdout.read().decode('gbk', errors='replace')
    if api:
        import json
        try:
            data = json.loads(api)
            hr = data.get('hashrate', {}).get('total', [0, 0, 0])
            print(f'Hashrate: {hr[0]/1000:.1f} KH/s (10s), {hr[1]/1000:.1f} KH/s (60s), {hr[2]/1000:.1f} KH/s (15m)')
        except:
            print('API:', api[:500])
    else:
        print('API not ready yet')
else:
    print('XMRig not running! Checking...')
    # Check if exe exists
    check_cmd = 'cmd /c "dir ' + xmrig_dir + '\\xmrig.exe"'
    stdin, stdout, stderr = ssh.exec_command(check_cmd)
    print(stdout.read().decode('gbk', errors='replace'))
    # Try to run directly and see error
    help_cmd = 'cmd /c "cd /d ' + xmrig_dir + ' && xmrig.exe --help 2>&1 | findstr Usage"'
    stdin, stdout, stderr = ssh.exec_command(help_cmd)
    print('Help:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

ssh.close()
