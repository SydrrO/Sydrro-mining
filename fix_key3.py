import paramiko, time

# Get pubkey from 002
ssh002 = paramiko.SSHClient()
ssh002.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh002.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)
stdin, stdout, stderr = ssh002.exec_command('type ' + r'C:\Users\sydrro_ssh\.ssh\id_ed25519.pub')
pubkey = stdout.read().decode('gbk', errors='replace').strip()
ssh002.close()

# Write to 3.8 using a batch file approach
ssh38 = paramiko.SSHClient()
ssh38.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh38.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# Create .ssh dir
ssh38.exec_command('mkdir C:\\Users\\sydrro_ssh\\.ssh 2>nul')
time.sleep(1)

# Write a temporary batch file that writes the key, then run it
# The batch file uses set /p which handles special chars better
bat = '@echo off\r\n'
bat += 'set "KEY=' + pubkey + '"\r\n'
bat += 'echo %KEY%> C:\\Users\\sydrro_ssh\\.ssh\\authorized_keys\r\n'

sftp = ssh38.open_sftp()
f = sftp.open('C:/Users/sydrro_ssh/write_key.bat', 'w')
f.write(bat)
f.close()
sftp.close()

# Run the batch
stdin, stdout, stderr = ssh38.exec_command('C:\\Users\\sydrro_ssh\\write_key.bat')
time.sleep(2)

# Check result
stdin, stdout, stderr = ssh38.exec_command('type C:\\Users\\sydrro_ssh\\.ssh\\authorized_keys')
print('Content:', stdout.read().decode('gbk', errors='replace')[:120])

# Clean up
ssh38.exec_command('del C:\\Users\\sydrro_ssh\\write_key.bat 2>nul')
ssh38.close()

# Test
ssh002b = paramiko.SSHClient()
ssh002b.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh002b.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)
test = 'ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 sydrro_ssh@192.168.3.8 echo KEY_OK'
stdin, stdout, stderr = ssh002b.exec_command(test)
result = stdout.read().decode('gbk', errors='replace').strip()
print('Test:', result)
ssh002b.close()
