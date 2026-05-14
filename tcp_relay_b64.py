import paramiko, time, base64, socket, json

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
        param($o) $arr=$o -as [System.IO.Stream[]]
        try { $arr[0].CopyTo($arr[1]) } catch {}
    }, @($cs, $ts))
    [System.Threading.ThreadPool]::QueueUserWorkItem({
        param($o) $arr=$o -as [System.IO.Stream[]]
        try { $arr[0].CopyTo($arr[1]) } catch {}
    }, @($ts, $cs))
}
'''

# Encode to base64
ps_b64 = base64.b64encode(relay_ps.encode('utf-16-le')).decode()

# Write to 3.8 via PowerShell base64 decode
ssh38 = paramiko.SSHClient()
ssh38.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh38.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# Use PowerShell to decode and save
write_cmd = 'powershell -Command "[System.IO.File]::WriteAllBytes(\'C:\\Users\\sydrro_ssh\\tcp_relay.ps1\', [System.Convert]::FromBase64String(\'' + ps_b64 + '\'))"'
stdin, stdout, stderr = ssh38.exec_command(write_cmd)
time.sleep(2)

# Verify file
stdin, stdout, stderr = ssh38.exec_command('cmd /c "dir C:\\Users\\sydrro_ssh\\tcp_relay.ps1"')
print('File:', stdout.read().decode('gbk', errors='replace')[:100])

# Start relay via task
ssh38.exec_command('schtasks /delete /tn TCPRelay38 /f 2>nul')
time.sleep(1)
task = 'schtasks /create /tn TCPRelay38 /tr "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File C:\\Users\\sydrro_ssh\\tcp_relay.ps1" /sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
ssh38.exec_command(task)
time.sleep(1)
ssh38.exec_command('schtasks /run /tn TCPRelay38')
time.sleep(8)
ssh38.close()

# Test relay
s = socket.socket(); s.settimeout(5)
try:
    s.connect(('192.168.3.8', 16800))
    print('TCP relay 16800: OPEN!')
    s.close()
except Exception as e:
    print(f'TCP relay: {e}')

# 2. Update 002 miner
ssh002 = paramiko.SSHClient()
ssh002.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh002.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)
ssh002.exec_command('taskkill /f /im rigel.exe 2>nul')
time.sleep(3)

base = r'D:\Donwlaods\rigel-1.23.1-win'
bat = '@echo off\r\ncd /d "' + base + '"\r\nrigel.exe -a octopus -o stratum+tcp://192.168.3.8:16800 -u sydrro.5070ti --api-bind 0.0.0.0:5002 --log-file logs/miner.log --no-tui\r\n'

sftp = ssh002.open_sftp()
f = sftp.open(base + '/start_miner.bat', 'w')
f.write(bat)
f.close()
sftp.close()

# Restart
ssh002.exec_command('schtasks /run /tn Miner002')
time.sleep(20)

# Check
stdin, stdout, stderr = ssh002.exec_command('curl -s http://127.0.0.1:5002')
try:
    d = json.loads(stdout.read().decode())
    hr = d['hashrate']['octopus'] / 1e6
    mi = d['devices'][0]['monitoring_info']
    pool = d['pools']['octopus'][0]
    print(f'Hashrate: {hr:.1f} MH/s | Power: {mi["power_usage"]:.0f}W | Temp: {mi["core_temperature"]}C')
    print(f'Pool latency: {pool["average_latency_ms"]:.0f}ms')
except:
    print('Miner initializing...')

ssh002.close()
print('Done: 002 -> 3.8:16800(TCP relay) -> F2Pool')
