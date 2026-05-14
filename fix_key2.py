import paramiko, time

# Connect 002
ssh002 = paramiko.SSHClient()
ssh002.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh002.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)

# Read 002's pubkey into a temp file on 002, then scp to 3.8 via ssh
pubkey_path = r'C:\Users\sydrro_ssh\.ssh\id_ed25519.pub'
stdin, stdout, stderr = ssh002.exec_command('type ' + pubkey_path)
pubkey = stdout.read().decode('gbk', errors='replace').strip()

# Create a batch file on 002 that will:
# 1. SSH to 3.8 with password (using sshpass - but it's not available on Windows)
# 2. Or use the key directly

# Alternative: use SSH from 002 to pipe the key to 3.8
# ssh sydrro_ssh@192.168.3.8 "mkdir .ssh && echo KEY >> .ssh/authorized_keys"
# But this requires password input...

# Let me try using Python's paramiko to write to 3.8 by reading the key here,
# then using exec_command with proper base64 encoding

import base64
pubkey_b64 = base64.b64encode(pubkey.encode()).decode()

# On 3.8: decode and write
write_cmd = 'powershell -Command "[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String(\'' + pubkey_b64 + '\')) | Out-File -FilePath C:\\Users\\sydrro_ssh\\.ssh\\authorized_keys -Encoding ASCII"'

ssh38 = paramiko.SSHClient()
ssh38.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh38.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

ssh38.exec_command('mkdir C:\\Users\\sydrro_ssh\\.ssh 2>nul')
time.sleep(1)

stdin, stdout, stderr = ssh38.exec_command(write_cmd)
out = stdout.read().decode('gbk', errors='replace')
err = stderr.read().decode('gbk', errors='replace')
print('Write:', out, err[:200])

ssh38.close()
time.sleep(1)

# Test passwordless SSH
test = 'ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 sydrro_ssh@192.168.3.8 echo KEY_OK'
stdin, stdout, stderr = ssh002.exec_command(test)
result = stdout.read().decode('gbk', errors='replace').strip()
err = stderr.read().decode('gbk', errors='replace').strip()
print('Test:', result, err[:100])

if 'KEY_OK' in result:
    print('SUCCESS!')

    # Clean old tunnels
    ssh002.exec_command('taskkill /f /im ssh.exe 2>nul')
    time.sleep(2)

    # Start SOCKS5 tunnel
    ssh002.exec_command('ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -fN -D 0.0.0.0:17890 sydrro_ssh@192.168.3.8')
    time.sleep(5)

    # Update cfx.bat
    base = r'D:\Donwlaods\rigel-1.23.1-win'
    cfx = '@echo off\r\n:: CFX via 3.8 SOCKS5\r\ncd /d \"%~dp0\"\r\nrigel.exe -a octopus -o stratum+tcp://cfx.f2pool.com:6800 -u sydrro.5070ti --proxy 127.0.0.1:17890 --api-bind 0.0.0.0:5002 --log-file logs/miner.log\r\npause\r\n'
    sftp = ssh002.open_sftp()
    f = sftp.open(base + '/cfx.bat', 'w')
    f.write(cfx)
    f.close()
    sftp.close()

    print('SOCKS5 tunnel: 002:17890 -> 3.8 -> F2Pool')
    print('cfx.bat updated!')
else:
    print('Still failing. May need to check SSH config on 3.8.')

ssh002.close()
