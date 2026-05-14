import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

# Kill old tunnels
ssh.exec_command('taskkill /f /im ssh.exe 2>nul')
time.sleep(2)

# Create reconnect loop batch
sftp = ssh.open_sftp()
bat = '@echo off\r\n'
bat += ':loop\r\n'
bat += 'echo [%date% %time%] Tunnel connecting...\r\n'
bat += 'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ExitOnForwardFailure=yes -NT -R 0.0.0.0:2222:localhost:22 -p 80 root@47.111.182.166\r\n'
bat += 'echo Tunnel down, retry in 10s...\r\n'
bat += 'timeout /t 10 /nobreak >nul\r\n'
bat += 'goto loop\r\n'
f = sftp.open('C:/Users/sydrro_ssh/tunnel_keep.bat', 'w')
f.write(bat)
f.close()
sftp.close()
print('Batch written')

# Delete old task
ssh.exec_command('schtasks /delete /tn SSHTunnel /f 2>nul')
time.sleep(1)

# Create task
bat_path = r'C:\Users\sydrro_ssh\tunnel_keep.bat'
task_cmd = 'schtasks /create /tn SSHTunnel /tr "' + bat_path + '" /sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
stdin, stdout, stderr = ssh.exec_command(task_cmd)
out = stdout.read().decode('gbk', errors='replace')
err = stderr.read().decode('gbk', errors='replace')
print('Task:', out, err)

# Run now
ssh.exec_command('schtasks /run /tn SSHTunnel')
time.sleep(5)

# Verify
stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr "47.111"')
print('Tunnel:', stdout.read().decode('gbk', errors='replace')[:200])

print('\nDone!')
print('Connect: ssh -J root@47.111.182.166:80 sydrro_ssh@localhost -p 2222')
print('  Server pass: Dymc12138')
print('  001 pass:    061021')

ssh.close()
