import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

exe = r"C:\Users\25623\OneDrive\Desktop\rigel-1.23.1-win\rigel.exe"
wd = r"C:\Users\25623\OneDrive\Desktop\rigel-1.23.1-win"
args = "-a octopus -o stratum+tcp://cfx.f2pool.com:6800 -u sydrro.rtx2080ti"

# Create a scheduled task that runs immediately
task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers><TimeTrigger><StartBoundary>2024-01-01T00:00:00</StartBoundary></TimeTrigger></Triggers>
  <Actions Context="Author">
    <Exec>
      <Command>"{exe}"</Command>
      <Arguments>{args}</Arguments>
      <WorkingDirectory>{wd}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''

# Write XML to remote temp file
xml_path = r"C:\Users\25623\AppData\Local\Temp\miner_task.xml"
write_xml = f'powershell.exe -Command "Set-Content -Path \'{xml_path}\' -Value @\'\\n{task_xml}\\n\'@"'
stdin, stdout, stderr = ssh.exec_command(write_xml)
print('Write XML:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

# Create and run task
create_task = f'schtasks /create /tn "MinerRigel" /xml "{xml_path}" /f'
stdin, stdout, stderr = ssh.exec_command(create_task)
print('Create task:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

# Run task
run_task = 'schtasks /run /tn "MinerRigel"'
stdin, stdout, stderr = ssh.exec_command(run_task)
print('Run task:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

time.sleep(5)

# Check process
stdin2, stdout2, stderr2 = ssh.exec_command('powershell.exe -Command "Get-Process -Name rigel -ErrorAction SilentlyContinue | Select-Object Id, CPU"')
result = stdout2.read().decode('gbk', errors='replace')
if result.strip():
    print('SUCCESS! Rigel is running:')
    print(result)
else:
    print('Process not found, checking task scheduler...')
    stdin3, stdout3, stderr3 = ssh.exec_command('schtasks /query /tn "MinerRigel"')
    print(stdout3.read().decode('gbk', errors='replace'))

ssh.close()
