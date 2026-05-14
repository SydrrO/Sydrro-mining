import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)

# Generate key for 002 -> 3.8 if needed
stdin, stdout, stderr = ssh.exec_command('cmd /c "if exist C:\\Users\\sydrro_ssh\\.ssh\\id_ed25519.pub (echo KEY_EXISTS) else (ssh-keygen -t ed25519 -f C:\\Users\\sydrro_ssh\\.ssh\\id_ed25519 -N \"\" -q && echo KEY_CREATED)"')
time.sleep(1)

stdin, stdout, stderr = ssh.exec_command('cmd /c "type C:\\Users\\sydrro_ssh\\.ssh\\id_ed25519.pub"')
pubkey = stdout.read().decode('gbk', errors='replace').strip()
print('Key:', pubkey[:50] + '...')

# Add 002's key to 3.8
ssh38 = paramiko.SSHClient()
ssh38.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh38.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)
ssh38.exec_command('cmd /c "if not exist C:\\Users\\sydrro_ssh\\.ssh mkdir C:\\Users\\sydrro_ssh\\.ssh"')
time.sleep(1)
add_key = 'cmd /c "echo ' + pubkey + ' >> C:\\Users\\sydrro_ssh\\.ssh\\authorized_keys"'
ssh38.exec_command(add_key)
ssh38.close()
print('Key added to 3.8')

# Start SSH tunnel: 002:17890 -> 3.8:127.0.0.1:7892
ssh.exec_command('taskkill /f /im ssh.exe 2>nul')
time.sleep(2)

tunnel = 'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ExitOnForwardFailure=yes -fN -L 0.0.0.0:17890:127.0.0.1:7892 sydrro_ssh@192.168.3.8'
ssh.exec_command(tunnel)
time.sleep(5)

# Test from 002 to its own localhost:17890
stdin, stdout, stderr = ssh.exec_command('powershell -Command \"Test-NetConnection -ComputerName 127.0.0.1 -Port 17890 -WarningAction SilentlyContinue | Select-Object TcpTestSucceeded\"')
print('Local tunnel:', stdout.read().decode('gbk', errors='replace'))

# Test from 002 to F2Pool through the tunnel
stdin, stdout, stderr = ssh.exec_command('powershell -Command \"Test-NetConnection -ComputerName cfx.f2pool.com -Port 6800 -WarningAction SilentlyContinue | Select-Object TcpTestSucceeded\"')
print('F2Pool direct:', stdout.read().decode('gbk', errors='replace'))

ssh.close()
print()
print('Tunnel: 002:17890 -> 3.8:127.0.0.1:7892 (proxy)')
print('Rigel can now use: --proxy 127.0.0.1:17890')
