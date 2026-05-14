import paramiko, time

TARGET = '192.168.3.7'
SERVER = '47.111.182.166'
SERVER_PORT = 80
TUNNEL_PORT = 2224

ssh002 = paramiko.SSHClient()
ssh002.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh002.connect(TARGET, username='sydrro_ssh', password='061021', timeout=10)

# 1. Ensure key exists
ssh002.exec_command('mkdir C:\\Users\\sydrro_ssh\\.ssh 2>nul')
time.sleep(1)
stdin, stdout, stderr = ssh002.exec_command('type C:\\Users\\sydrro_ssh\\.ssh\\id_ed25519.pub 2>nul')
pubkey = stdout.read().decode('gbk', errors='replace').strip()
if not pubkey:
    ssh002.exec_command('ssh-keygen -t ed25519 -f C:\\Users\\sydrro_ssh\\.ssh\\id_ed25519 -N "" -q')
    time.sleep(1)
    stdin, stdout, stderr = ssh002.exec_command('type C:\\Users\\sydrro_ssh\\.ssh\\id_ed25519.pub')
    pubkey = stdout.read().decode('gbk', errors='replace').strip()
print('Key:', pubkey[:50] + '...')

# 2. Add key to server
ssh_srv = paramiko.SSHClient()
ssh_srv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_srv.connect(SERVER, port=SERVER_PORT, username='root', password='Dymc12138', timeout=10)
cmd = 'grep -q "DESKTOP-DR9MRH8" ~/.ssh/authorized_keys 2>/dev/null && echo KEY_EXISTS || (echo "' + pubkey + '" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo KEY_ADDED)'
stdin, stdout, stderr = ssh_srv.exec_command(cmd)
print('Server:', stdout.read().decode().strip())
ssh_srv.close()

# 3. Write persistent tunnel script
sftp = ssh002.open_sftp()
bat = '@echo off\r\n'
bat += ':loop\r\n'
bat += 'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes -NT -R 0.0.0.0:' + str(TUNNEL_PORT) + ':localhost:22 -p ' + str(SERVER_PORT) + ' root@' + SERVER + '\r\n'
bat += 'timeout /t 10 /nobreak >nul\r\n'
bat += 'goto loop\r\n'
f = sftp.open('C:/Users/sydrro_ssh/tunnel_keep.bat', 'w')
f.write(bat)
f.close()
sftp.close()

# 4. Schedule as auto-start task
ssh002.exec_command('schtasks /delete /tn SSHTunnel002 /f 2>nul')
time.sleep(1)
task = 'schtasks /create /tn SSHTunnel002 /tr "C:\\Users\\sydrro_ssh\\tunnel_keep.bat" /sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
ssh002.exec_command(task)
time.sleep(1)
ssh002.exec_command('schtasks /run /tn SSHTunnel002')
time.sleep(8)

# 5. Verify
stdin, stdout, stderr = ssh002.exec_command('netstat -ano | findstr ":80.*' + SERVER + '.*ESTABLISHED"')
conn = stdout.read().decode('gbk', errors='replace').strip()
print('Tunnel:', 'ACTIVE' if conn else 'connecting...')

ssh_srv2 = paramiko.SSHClient()
ssh_srv2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_srv2.connect(SERVER, port=SERVER_PORT, username='root', password='Dymc12138', timeout=10)
stdin, stdout, stderr = ssh_srv2.exec_command('ss -tlnp | grep ' + str(TUNNEL_PORT))
print('Port ' + str(TUNNEL_PORT) + ':', stdout.read().decode().strip()[:80])
ssh_srv2.close()

ssh002.close()
print()
print('002 tunnel: ssh -J root@' + SERVER + ':' + str(SERVER_PORT) + ' -p ' + str(TUNNEL_PORT) + ' sydrro_ssh@localhost')
