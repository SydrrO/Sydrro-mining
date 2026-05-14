import paramiko, time, socket

# 1. Get 002 public key
ssh002 = paramiko.SSHClient()
ssh002.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh002.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)

pubkey_path = r'C:\Users\sydrro_ssh\.ssh\id_ed25519.pub'
stdin, stdout, stderr = ssh002.exec_command('cmd /c "type ' + pubkey_path + '"')
pubkey = stdout.read().decode('gbk', errors='replace').strip()
print('002 pubkey:', pubkey[:50] + '...')

# 2. Add 002 key to 3.8 authorized_keys
ssh38 = paramiko.SSHClient()
ssh38.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh38.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)
ssh38.exec_command('cmd /c "if not exist C:\\Users\\sydrro_ssh\\.ssh mkdir C:\\Users\\sydrro_ssh\\.ssh"')
time.sleep(1)
# Use echo to add key
add = 'cmd /c "echo ' + pubkey + ' > C:\\Users\\sydrro_ssh\\.ssh\\authorized_keys"'
stdin, stdout, stderr = ssh38.exec_command(add)
out = stdout.read().decode('gbk', errors='replace')
err = stderr.read().decode('gbk', errors='replace')
print('Add key:', out, err[:100])
ssh38.close()

# 3. Test passwordless SSH from 002 to 3.8
test = 'ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 sydrro_ssh@192.168.3.8 echo KEY_TEST_OK'
stdin, stdout, stderr = ssh002.exec_command(test)
result = stdout.read().decode('gbk', errors='replace').strip()
err = stderr.read().decode('gbk', errors='replace').strip()
print('Key test:', result, err[:100])

if 'KEY_TEST_OK' in result:
    print('Passwordless SSH OK!')

    # 4. Kill old SSH and start SOCKS5 tunnel
    ssh002.exec_command('taskkill /f /im ssh.exe 2>nul')
    time.sleep(2)

    # -D creates a SOCKS5 proxy: 002:17890 -> routes through 3.8
    tunnel = 'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -fN -D 0.0.0.0:17890 sydrro_ssh@192.168.3.8'
    ssh002.exec_command(tunnel)
    time.sleep(5)

    # 5. Test from 002: can we reach F2Pool through the SOCKS5 proxy?
    # Test with PowerShell using a simple TCP connection test
    test_proxy = 'powershell -Command "Test-NetConnection 127.0.0.1 -Port 17890 | Select-Object TcpTestSucceeded"'
    stdin, stdout, stderr = ssh002.exec_command(test_proxy)
    print('SOCKS5 tunnel:', stdout.read().decode('gbk', errors='replace'))

    # 6. Update cfx.bat on 002
    base = r'D:\Donwlaods\rigel-1.23.1-win'
    cfx = '@echo off\r\n:: CFX via 3.8 proxy\r\ncd /d "%~dp0"\r\nrigel.exe -a octopus -o stratum+tcp://cfx.f2pool.com:6800 -u sydrro.5070ti --proxy 127.0.0.1:17890 --api-bind 0.0.0.0:5002 --log-file logs/miner.log\r\npause\r\n'
    sftp = ssh002.open_sftp()
    f = sftp.open(base + '/cfx.bat', 'w')
    f.write(cfx)
    f.close()
    sftp.close()
    print('cfx.bat updated!')

    print()
    print('=== Done ===')
    print('002 -> SOCKS5 tunnel -> 3.8 (global proxy) -> F2Pool')
    print('Rigel proxy: 127.0.0.1:17890')
else:
    print('Key auth failed. Admin might need to approve or SSH config issue.')

ssh002.close()
