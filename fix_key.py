import paramiko, time

# Get 002 pubkey
ssh002 = paramiko.SSHClient()
ssh002.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh002.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)
pubkey_path = r'C:\Users\sydrro_ssh\.ssh\id_ed25519.pub'
stdin, stdout, stderr = ssh002.exec_command('type ' + pubkey_path)
pubkey = stdout.read().decode('gbk', errors='replace').strip()
ssh002.close()
print('Pubkey:', pubkey[:60])

# Write to 3.8 via SFTP
ssh38 = paramiko.SSHClient()
ssh38.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh38.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# Create .ssh dir
ssh38.exec_command('mkdir C:\\Users\\sydrro_ssh\\.ssh 2>nul')
time.sleep(1)

# Write key via SFTP
sftp = ssh38.open_sftp()
f = sftp.open('C:/Users/sydrro_ssh/.ssh/authorized_keys', 'w')
f.write(pubkey + '\n')
f.close()
sftp.close()
print('Key written')

# Test now
ssh002b = paramiko.SSHClient()
ssh002b.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh002b.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)
test = 'ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 sydrro_ssh@192.168.3.8 echo KEY_OK'
stdin, stdout, stderr = ssh002b.exec_command(test)
result = stdout.read().decode('gbk', errors='replace').strip()
err = stderr.read().decode('gbk', errors='replace').strip()
print('Test:', result, err[:100])

if 'KEY_OK' in result:
    print('SUCCESS! Passwordless SSH 002 -> 3.8')

    # Start SOCKS5 tunnel: 002:17890 -> via 3.8
    ssh002b.exec_command('taskkill /f /im ssh.exe 2>nul')
    time.sleep(2)
    tunnel = 'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -fN -D 0.0.0.0:17890 sydrro_ssh@192.168.3.8'
    ssh002b.exec_command(tunnel)
    time.sleep(5)

    # Update cfx.bat
    base = r'D:\Donwlaods\rigel-1.23.1-win'
    cfx = '@echo off\r\n:: CFX via 3.8 SOCKS5 proxy\r\ncd /d \"%~dp0\"\r\nrigel.exe -a octopus -o stratum+tcp://cfx.f2pool.com:6800 -u sydrro.5070ti --proxy 127.0.0.1:17890 --api-bind 0.0.0.0:5002 --log-file logs/miner.log\r\npause\r\n'
    sftp = ssh002b.open_sftp()
    f = sftp.open(base + '/cfx.bat', 'w')
    f.write(cfx)
    f.close()
    sftp.close()

    print('SOCKS5 tunnel active! 002:17890 -> 3.8 -> F2Pool')
    print('cfx.bat updated with proxy 127.0.0.1:17890')
else:
    print('Key auth still failing')

ssh38.close()
ssh002b.close()
