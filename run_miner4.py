import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

# Delete old task
ssh.exec_command('schtasks /delete /tn "MinerRigel" /f 2>nul')
time.sleep(1)

bat_path = r'"C:\Users\25623\OneDrive\Desktop\rigel-1.23.1-win\a.bat"'

# Create task that runs as user 25623 (interactive user with GPU access)
# Use /it to allow interactive mode
create_cmd = f'schtasks /create /tn "MinerRigel" /tr {bat_path} /sc once /st 00:00 /sd 01/01/2024 /ru 25623 /f'
print('Create:', create_cmd)
stdin, stdout, stderr = ssh.exec_command(create_cmd)
out = stdout.read().decode('gbk', errors='replace')
err = stderr.read().decode('gbk', errors='replace')
print('OUT:', out)
print('ERR:', err)

# Run task
stdin, stdout, stderr = ssh.exec_command('schtasks /run /tn "MinerRigel"')
print('Run:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

time.sleep(5)

# Check
stdin2, stdout2, stderr2 = ssh.exec_command('powershell.exe -Command "Get-Process -Name rigel -ErrorAction SilentlyContinue | Select-Object Id, CPU"')
result = stdout2.read().decode('gbk', errors='replace')
if result.strip():
    print('SUCCESS! Rigel running:')
    print(result)
else:
    print('Not running. Task status:')
    stdin3, stdout3, stderr3 = ssh.exec_command('schtasks /query /tn "MinerRigel"')
    print(stdout3.read().decode('gbk', errors='replace'))

ssh.close()
