import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

# Kill old task
ssh.exec_command('schtasks /end /tn "MinerRigel" 2>nul')
ssh.exec_command('schtasks /delete /tn "MinerRigel" /f 2>nul')
ssh.exec_command('taskkill /f /im rigel.exe 2>nul')
time.sleep(2)

# Create new bat file with API and logging
bat_content = '@echo off\r\ncd /d "%~dp0"\r\nrigel.exe -a octopus -o stratum+tcp://cfx.f2pool.com:6800 -u sydrro.rtx2080ti --api-bind 0.0.0.0:5000 --log-file rigel.log\r\n'
bat_path = r'"C:\Users\25623\OneDrive\Desktop\rigel-1.23.1-win\a_api.bat"'

# Write bat file
write_cmd = f'powershell.exe -Command \"Set-Content -Path {bat_path} -Value @\\\"\\r\\n{bat_content}\\r\\n\\\"@\"'
stdin, stdout, stderr = ssh.exec_command(write_cmd)
err = stderr.read().decode('gbk', errors='replace')
if err:
    print('Write error:', err)

# Create and run task as user 25623
tr = r'"C:\Users\25623\OneDrive\Desktop\rigel-1.23.1-win\a_api.bat"'
create = f'schtasks /create /tn "MinerRigel" /tr {tr} /sc once /st 00:00 /sd 01/01/2024 /ru 25623 /f'
print('Create task...')
stdin, stdout, stderr = ssh.exec_command(create)
print(stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

time.sleep(1)
print('Run task...')
stdin, stdout, stderr = ssh.exec_command('schtasks /run /tn "MinerRigel"')
print(stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

time.sleep(8)
print('Miner started, checking API...')

# Query API
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:5000 2>nul')
api_data = stdout.read().decode('gbk', errors='replace')
if api_data:
    print('API Response:')
    print(api_data[:2000])
else:
    print('API not ready yet, checking process...')
    stdin, stdout, stderr = ssh.exec_command('powershell.exe -Command "Get-Process -Name rigel -ErrorAction SilentlyContinue"')
    print(stdout.read().decode('gbk', errors='replace'))

ssh.close()
