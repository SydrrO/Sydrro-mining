import paramiko
import time

# Connect to 001
ssh001 = paramiko.SSHClient()
ssh001.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh001.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

# Get pubkey from 001
stdin, stdout, stderr = ssh001.exec_command('type C:\\Users\\sydrro_ssh\\.ssh\\id_ed25519.pub')
pubkey = stdout.read().decode().strip()
print(f'Pubkey: {pubkey[:60]}...')

# Use 001 as jumphost to reach server
transport = ssh001.get_transport()
channel = transport.open_channel('direct-tcpip', ('47.111.182.166', 22), ('127.0.0.1', 0))

ssh_srv = paramiko.SSHClient()
ssh_srv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_srv.connect('47.111.182.166', username='root', password='Dymc12138', sock=channel, timeout=15)

# Add pubkey
cmd = f'mkdir -p ~/.ssh && echo "{pubkey}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo DONE'
stdin, stdout, stderr = ssh_srv.exec_command(cmd)
print('Add key:', stdout.read().decode().strip())
ssh_srv.close()

# Test passwordless SSH from 001 to server
test = 'ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 root@47.111.182.166 echo OK'
stdin, stdout, stderr = ssh001.exec_command(test)
print('Test:', stdout.read().decode('gbk', errors='replace').strip())

# Start reverse tunnel
tunnel = 'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -fN -R 0.0.0.0:2222:localhost:22 root@47.111.182.166'
stdin, stdout, stderr = ssh001.exec_command(tunnel)
time.sleep(3)

# Verify tunnel from server side
channel2 = transport.open_channel('direct-tcpip', ('47.111.182.166', 22), ('127.0.0.1', 0))
ssh_srv2 = paramiko.SSHClient()
ssh_srv2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_srv2.connect('47.111.182.166', username='root', password='Dymc12138', sock=channel2, timeout=15)
stdin, stdout, stderr = ssh_srv2.exec_command('ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 -p 2222 sydrro_ssh@localhost whoami')
out = stdout.read().decode().strip()
err = stderr.read().decode().strip()
print(f'Tunnel test: {out} {err}')
ssh_srv2.close()

# Create persistent auto-start script
bat = '@echo off\r\n:loop\r\nssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ExitOnForwardFailure=yes -NT -R 0.0.0.0:2222:localhost:22 root@47.111.182.166\r\ntimeout /t 10 >nul\r\ngoto loop\r\n'
sftp = ssh001.open_sftp()
f = sftp.open('C:/Users/sydrro_ssh/tunnel.bat', 'w')
f.write(bat)
f.close()
sftp.close()

# Schedule task
ssh001.exec_command('schtasks /delete /tn SSHTunnel /f 2>nul')
time.sleep(1)
task = 'schtasks /create /tn SSHTunnel /tr "C:\\Users\\sydrro_ssh\\tunnel.bat" /sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
stdin, stdout, stderr = ssh001.exec_command(task)
print('Task:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

ssh001.exec_command('schtasks /run /tn SSHTunnel')
print('\n=== DONE ===')
print('ssh sydrro_ssh@47.111.182.166 -p 2222')

ssh001.close()
