import paramiko, time

IP = '192.168.3.7'
SERVER_IP = '47.111.182.166'
SERVER_PORT = 80
TUNNEL_PORT = 2224  # Different from 001 which uses 2223

# 1. Connect to 002
ssh002 = paramiko.SSHClient()
ssh002.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh002.connect(IP, username='sydrro_ssh', password='061021', timeout=10)

# 2. Generate SSH key
ssh002.exec_command('mkdir C:\\Users\\sydrro_ssh\\.ssh 2>nul')
time.sleep(1)
stdin, stdout, stderr = ssh002.exec_command('ssh-keygen -t ed25519 -f C:\\Users\\sydrro_ssh\\.ssh\\id_ed25519 -N "" -q 2>&1')
time.sleep(1)
stdin, stdout, stderr = ssh002.exec_command('type C:\\Users\\sydrro_ssh\\.ssh\\id_ed25519.pub')
pubkey = stdout.read().decode().strip()
print('Key:', pubkey[:60] + '...')

# 3. Add key to server
ssh_srv = paramiko.SSHClient()
ssh_srv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_srv.connect(SERVER_IP, port=SERVER_PORT, username='root', password='Dymc12138', timeout=10)
cmd = 'grep -q "DESKTOP-DR9MRH8" ~/.ssh/authorized_keys 2>/dev/null || echo "' + pubkey + '" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo KEY_OK'
stdin, stdout, stderr = ssh_srv.exec_command(cmd)
print('Server:', stdout.read().decode().strip())

# 4. Clean old and start tunnel
ssh002.exec_command('taskkill /f /im ssh.exe 2>nul')
time.sleep(3)
tunnel_cmd = 'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -fN -R 0.0.0.0:' + str(TUNNEL_PORT) + ':localhost:22 -p ' + str(SERVER_PORT) + ' root@' + SERVER_IP
ssh002.exec_command(tunnel_cmd)
time.sleep(5)

# 5. Verify from server
stdin, stdout, stderr = ssh_srv.exec_command('ss -tlnp | grep ' + str(TUNNEL_PORT))
print('Port:', stdout.read().decode().strip()[:80])

stdin, stdout, stderr = ssh_srv.exec_command('sshpass -p 061021 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -p ' + str(TUNNEL_PORT) + ' sydrro_ssh@localhost whoami && hostname && echo TUNNEL_OK')
print('Test:', stdout.read().decode().strip())

# 6. Persistent auto-reconnect
sftp = ssh002.open_sftp()
bat = '@echo off\r\n:loop\r\necho [%date% %time%] Tunnel to server\r\nssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes -NT -R 0.0.0.0:' + str(TUNNEL_PORT) + ':localhost:22 -p ' + str(SERVER_PORT) + ' root@' + SERVER_IP + '\r\necho Down, retry in 10s...\r\ntimeout /t 10 /nobreak >nul\r\ngoto loop\r\n'
f = sftp.open('C:/Users/sydrro_ssh/tunnel_keep.bat', 'w')
f.write(bat)
f.close()
sftp.close()

ssh002.exec_command('schtasks /delete /tn SSHTunnel /f 2>nul')
time.sleep(1)
task_cmd = 'schtasks /create /tn SSHTunnel /tr "C:\\Users\\sydrro_ssh\\tunnel_keep.bat" /sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
ssh002.exec_command(task_cmd)
time.sleep(1)
ssh002.exec_command('schtasks /run /tn SSHTunnel')

print()
print('=' * 55)
print('  002 公网访问已配置')
print('=' * 55)
print('  ssh -J root@47.111.182.166:80 -p 2224 sydrro_ssh@localhost')
print('  密码: 服务器 Dymc12138 / 002 061021')
print('=' * 55)

ssh002.close()
ssh_srv.close()
