import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

log_path = r'C:\Users\25623\OneDrive\Desktop\xmrig\xmrig-6.22.2\xmrig.log'

# Read log
stdin, stdout, stderr = ssh.exec_command('type ' + log_path + ' 2>nul')
log = stdout.read().decode('gbk', errors='replace')
if log:
    print('=== XMRig LOG ===')
    # Show last 50 lines
    lines = log.split('\n')
    for line in lines[-50:]:
        print(line)
else:
    print('No log file found')

# Process
print('\n=== Process ===')
stdin, stdout, stderr = ssh.exec_command('powershell.exe -Command "Get-Process -Name xmrig -ErrorAction SilentlyContinue | Select-Object Id, CPU, WorkingSet64"')
print(stdout.read().decode('gbk', errors='replace'))

# API
print('\n=== API ===')
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:6000/1/summary')
print(stdout.read().decode('gbk', errors='replace')[:1500])

ssh.close()
