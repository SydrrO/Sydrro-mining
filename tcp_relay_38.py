import paramiko, time, socket

# 1. Deploy TCP relay on 3.8
ssh38 = paramiko.SSHClient()
ssh38.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh38.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# PowerShell TCP relay: 0.0.0.0:16800 -> cfx.f2pool.com:6800
# Uses ThreadPool for background copy (works on PS 5.1+)
relay_ps = '''
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, 16800)
$listener.Start()
Add-Type -AssemblyName System.Threading
while ($true) {
    $client = $listener.AcceptTcpClient()
    $target = [System.Net.Sockets.TcpClient]::new("cfx.f2pool.com", 6800)
    $cs = $client.GetStream()
    $ts = $target.GetStream()
    [System.Threading.ThreadPool]::QueueUserWorkItem({
        param($o)
        $arr = $o -as [System.IO.Stream[]]
        try { $arr[0].CopyTo($arr[1]) } catch {}
    }, @($cs, $ts))
    [System.Threading.ThreadPool]::QueueUserWorkItem({
        param($o)
        $arr = $o -as [System.IO.Stream[]]
        try { $arr[0].CopyTo($arr[1]) } catch {}
    }, @($ts, $cs))
}
'''

sftp = ssh38.open_sftp()
f = sftp.open('C:/Users/sydrro_ssh/tcp_relay.ps1', 'w')
f.write(relay_ps)
f.close()
sftp.close()

# Start via scheduled task (runs in background, survives logoff)
ssh38.exec_command('schtasks /delete /tn TCPRelay38 /f 2>nul')
time.sleep(1)

task = 'schtasks /create /tn TCPRelay38 /tr "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File C:\\Users\\sydrro_ssh\\tcp_relay.ps1" /sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
ssh38.exec_command(task)
time.sleep(1)
ssh38.exec_command('schtasks /run /tn TCPRelay38')
time.sleep(8)

# Test relay from here
s = socket.socket(); s.settimeout(5)
try:
    s.connect(('192.168.3.8', 16800))
    print('TCP relay 16800: OPEN!')
    s.close()
except Exception as e:
    print(f'TCP relay: {e}')

ssh38.close()

# 2. Update miner on 002 to use relay
ssh002 = paramiko.SSHClient()
ssh002.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh002.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)

# Stop miner
ssh002.exec_command('taskkill /f /im rigel.exe 2>nul')
time.sleep(3)

base = r'D:\Donwlaods\rigel-1.23.1-win'

# Update batch: connect directly to 3.8 relay, no SOCKS5 proxy
bat = '@echo off\r\ncd /d "' + base + '"\r\nrigel.exe -a octopus -o stratum+tcp://192.168.3.8:16800 -u sydrro.5070ti --api-bind 0.0.0.0:5002 --log-file logs/miner.log --no-tui\r\n'

sftp2 = ssh002.open_sftp()
f = sftp2.open(base + '/start_miner.bat', 'w')
f.write(bat)
f.close()

cfx = bat + 'pause\r\n'
f = sftp2.open(base + '/cfx.bat', 'w')
f.write(cfx)
f.close()
sftp2.close()

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
    print(f'\nHashrate: {hr:.1f} MH/s | Power: {mi["power_usage"]:.0f}W | Temp: {mi["core_temperature"]}C')
    print(f'Pool latency: {pool["average_latency_ms"]:.0f}ms')
except:
    print('Miner still initializing...')

ssh002.close()
print('\nDone: 002 -> 3.8:16800(TCP relay) -> F2Pool')
