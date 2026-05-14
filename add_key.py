import paramiko

# Get pubkey from 001
ssh001 = paramiko.SSHClient()
ssh001.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh001.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

path = r'C:\Users\sydrro_ssh\.ssh\id_ed25519.pub'
stdin, stdout, stderr = ssh001.exec_command('type ' + path)
pubkey = stdout.read().decode().strip()
print('Pubkey:', pubkey[:60] + '...')
ssh001.close()

# Add to server on port 80
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('47.111.182.166', port=80, username='root', password='Dymc12138', timeout=10)

cmd = 'mkdir -p ~/.ssh && echo "' + pubkey + '" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo DONE'
stdin, stdout, stderr = ssh.exec_command(cmd)
print('Server:', stdout.read().decode().strip(), stderr.read().decode().strip())

# Now test: from 001, passwordless SSH to server on port 80
ssh001b = paramiko.SSHClient()
ssh001b.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh001b.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

test_cmd = 'ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 -p 80 root@47.111.182.166 echo KEY_OK'
stdin, stdout, stderr = ssh001b.exec_command(test_cmd)
result = stdout.read().decode('gbk', errors='replace').strip()
err = stderr.read().decode('gbk', errors='replace').strip()
print('Test from 001:', result, err[:100])

if 'KEY_OK' in result:
    print('\n=== Passwordless SSH working! ===')

    # Start reverse tunnel from 001
    tunnel = 'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -fN -R 0.0.0.0:2222:localhost:22 -p 80 root@47.111.182.166'
    stdin, stdout, stderr = ssh001b.exec_command(tunnel)
    print('Tunnel started:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

    import time
    time.sleep(3)

    # Test tunnel from server side
    stdin, stdout, stderr = ssh.exec_command('sleep 5 && ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -p 2222 sydrro_ssh@localhost whoami 2>&1')
    result2 = stdout.read().decode().strip()
    err2 = stderr.read().decode().strip()
    print('Tunnel test:', result2, err2[:100])

    if 'sydrro_ssh' in result2:
        print('\n=== SUCCESS! ===')
        print('Access 001: ssh sydrro_ssh@47.111.182.166 -p 2222')

    # Persistent tunnel batch
    sftp = ssh001b.open_sftp()
    bat = '@echo off\r\n:loop\r\nssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ExitOnForwardFailure=yes -NT -R 0.0.0.0:2222:localhost:22 -p 80 root@47.111.182.166\r\ntimeout /t 10 >nul\r\ngoto loop\r\n'
    f = sftp.open('C:/Users/sydrro_ssh/tunnel.bat', 'w')
    f.write(bat)
    f.close()
    sftp.close()

    # Schedule task
    ssh001b.exec_command('schtasks /delete /tn SSHTunnel /f 2>nul')
    time.sleep(1)
    task = 'schtasks /create /tn SSHTunnel /tr "C:\\Users\\sydrro_ssh\\tunnel.bat" /sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
    stdin, stdout, stderr = ssh001b.exec_command(task)
    print('Task:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

    ssh001b.exec_command('schtasks /run /tn SSHTunnel')
    print('Persistent tunnel configured.')

else:
    print('Passwordless SSH failed. Check key setup.')

ssh001b.close()
ssh.close()
