"""Deploy via SFTP to 192.168.3.8 (Windows OpenSSH supports SFTP)."""
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# Try SFTP
try:
    sftp = ssh.open_sftp()
    print('SFTP connection OK!')

    # Upload syslog.py
    local_syslog = r'd:\sydrro-projects\sydrro-mining\miner-monitor\syslog.py'
    remote_syslog = 'C:/Users/sydrro_ssh/Desktop/miner308/syslog.py'
    sftp.put(local_syslog, remote_syslog)
    print(f'Uploaded syslog.py ({sftp.stat(remote_syslog).st_size} bytes)')

    # Upload app.py
    local_app = r'd:\sydrro-projects\sydrro-mining\miner-monitor\app.py'
    remote_app = 'C:/Users/sydrro_ssh/Desktop/miner308/app.py'
    sftp.put(local_app, remote_app)
    print(f'Uploaded app.py ({sftp.stat(remote_app).st_size} bytes)')

    sftp.close()
except Exception as e:
    print(f'SFTP failed: {e}')

# Kill and restart
print('\nRestarting...')
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(2)
ssh.exec_command('schtasks /run /tn "MinerDashboard"')
print('Scheduled task triggered')

# Wait and check
time.sleep(10)
for i in range(5):
    stdin, stdout, stderr = ssh.exec_command('tasklist | findstr python')
    procs = stdout.read().decode('gbk', errors='replace').strip()
    if procs:
        print(f'Python running: {procs[:100]}')
        break
    print(f'  [{i*2+10}s] Waiting...')
    time.sleep(2)

# Check port
stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr 5000 | findstr LISTENING')
port = stdout.read().decode('gbk', errors='replace').strip()
print(f'Port 5000: {port if port else "NOT LISTENING"}')

ssh.close()

# Test API
if port:
    import requests
    time.sleep(5)
    try:
        r = requests.get('http://192.168.3.8:5000/api/syslog/summary', timeout=10)
        print(f'\nSyslog: {r.status_code} - {r.text[:300]}')
    except Exception as e:
        print(f'\nAPI: {e}')
