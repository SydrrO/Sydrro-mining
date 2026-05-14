import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# PowerShell TCP relay script
ps_script = '''
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, 17890)
$listener.Start()
Write-Output "Relay started on port 17890"
while ($true) {
    $client = $listener.AcceptTcpClient()
    $backend = [System.Net.Sockets.TcpClient]::new("127.0.0.1", 7892)
    $cs = $client.GetStream()
    $bs = $backend.GetStream()
    # Copy both directions in background
    $job1 = Start-Job -ScriptBlock {
        param($s1, $s2)
        try { $s1.CopyTo($s2) } catch {}
    } -ArgumentList $cs, $bs
    $job2 = Start-Job -ScriptBlock {
        param($s1, $s2)
        try { $s1.CopyTo($s2) } catch {}
    } -ArgumentList $bs, $cs
}
'''

sftp = ssh.open_sftp()
f = sftp.open('C:/Users/sydrro_ssh/proxy_relay.ps1', 'w')
f.write(ps_script)
f.close()
sftp.close()

# Run it in background via PowerShell
ssh.exec_command('powershell -WindowStyle Hidden -File C:\\Users\\sydrro_ssh\\proxy_relay.ps1')
time.sleep(5)

# Test
import socket
s = socket.socket(); s.settimeout(3)
try:
    s.connect(('192.168.3.8', 17890))
    print('3.8:17890 OPEN! Relay working!')
    s.close()
except Exception as e:
    print(f'Still closed: {e}')

ssh.close()
