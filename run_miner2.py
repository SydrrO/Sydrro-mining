import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

exe = r"C:\Users\25623\OneDrive\Desktop\rigel-1.23.1-win\rigel.exe"
args = "-a octopus -o stratum+tcp://cfx.f2pool.com:6800 -u sydrro.rtx2080ti"

# Use PowerShell Start-Process
ps_cmd = f'powershell.exe -Command "Start-Process -FilePath \\"{exe}\\" -ArgumentList \\"{args}\\""'
print('Running:', ps_cmd)

stdin, stdout, stderr = ssh.exec_command(ps_cmd)
time.sleep(3)

# Check if running
stdin2, stdout2, stderr2 = ssh.exec_command('powershell.exe -Command "Get-Process -Name rigel -ErrorAction SilentlyContinue | Select-Object Id, CPU"')
print('Process check:', stdout2.read().decode('gbk', errors='replace'))

ssh.close()
