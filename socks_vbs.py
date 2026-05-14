import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)

base = r'D:\Donwlaods\rigel-1.23.1-win'

# Create VBS script that starts SSH SOCKS tunnel with password
# Uses SendKeys to type password
vbs = '''Set ws = CreateObject("WScript.Shell")
ws.Run "cmd /c ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -N -D 0.0.0.0:17890 sydrro_ssh@192.168.3.8", 0, False
WScript.Sleep 2000
ws.SendKeys "061021"
ws.SendKeys "{ENTER}"
WScript.Sleep 500
ws.SendKeys "061021"
ws.SendKeys "{ENTER}"
'''

# Actually SendKeys is unreliable. Use a simpler approach:
# Create a batch that uses plink (PuTTY command line) which supports -pw
# Or use ssh with sshpass... not available on Windows

# SIMPLEST APPROACH: use Python script on 002
# But 002 doesn't have Python...

# ACTUALLY SIMPLEST: Use PowerShell with Posh-SSH or a simple TCP
# Or just run ssh and accept password manually once

# THE REAL SIMPLEST: Write a small batch that:
# 1. Uses ssh with -N -D to create SOCKS proxy
# 2. Needs password

# For automated password, let's use a different approach:
# Create a scheduled task on 002 that runs the SSH tunnel
# The task stores credentials (like we did for 001)

tunnel_bat = '@echo off\r\n'
tunnel_bat += ':loop\r\n'
tunnel_bat += 'echo [%date% %time%] SOCKS5 tunnel to 3.8\r\n'
tunnel_bat += 'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes -NT -D 0.0.0.0:17890 sydrro_ssh@192.168.3.8\r\n'
tunnel_bat += 'echo Down, retry in 10s...\r\n'
tunnel_bat += 'timeout /t 10 /nobreak >nul\r\n'
tunnel_bat += 'goto loop\r\n'

sftp = ssh.open_sftp()
f = sftp.open(base + '/proxy_tunnel.bat', 'w')
f.write(tunnel_bat)
f.close()
sftp.close()

# Create scheduled task with stored password for auto-auth
ssh.exec_command('schtasks /delete /tn ProxyTunnel /f 2>nul')
time.sleep(1)

bat_path = base + '\\proxy_tunnel.bat'
task = 'schtasks /create /tn ProxyTunnel /tr "' + bat_path + '" /sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
ssh.exec_command(task)
time.sleep(1)

# Start now
ssh.exec_command('schtasks /run /tn ProxyTunnel')
time.sleep(8)

# Verify
stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr ":17890.*LISTEN"')
print('Port 17890:', stdout.read().decode('gbk', errors='replace')[:100])

# Update cfx.bat
cfx = '@echo off\r\n:: CFX via 3.8 SOCKS5\r\ncd /d "%~dp0"\r\nrigel.exe -a octopus -o stratum+tcp://cfx.f2pool.com:6800 -u sydrro.5070ti --proxy 127.0.0.1:17890 --api-bind 0.0.0.0:5002 --log-file logs/miner.log\r\npause\r\n'
f = sftp.open(base + '/cfx.bat', 'w')
f.write(cfx)
f.close()
sftp.close()

ssh.close()
print('Done!')
print('SOCKS5 tunnel: 002:17890 -> 3.8 (global proxy) -> F2Pool')
print('cfx.bat updated: --proxy 127.0.0.1:17890')
