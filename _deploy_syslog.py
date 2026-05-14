"""Quick redeploy of syslog.py to 192.168.3.8."""
import paramiko, time, base64

local_path = r'd:\sydrro-projects\sydrro-mining\miner-monitor\syslog.py'
with open(local_path, 'rb') as f:
    content = f.read()
print(f'syslog.py: {len(content)} bytes')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

remote_dir = 'C:\\Users\\sydrro_ssh\\Desktop\\miner308'
remote_path = f'{remote_dir}\\syslog.py'
b64 = base64.b64encode(content).decode('ascii')
chunk_size = 4000
chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]

ssh.exec_command(f'del {remote_dir}\\upload.b64 2>nul')
for i, chunk in enumerate(chunks):
    cmd = f'powershell -Command "Add-Content -Path {remote_dir}\\upload.b64 -Value \'{chunk}\'"'
    ssh.exec_command(cmd)

decode_cmd = (
    f'powershell -Command "$b64 = Get-Content {remote_dir}\\upload.b64 -Raw; '
    f'$bytes = [Convert]::FromBase64String($b64); '
    f'[System.IO.File]::WriteAllBytes(\'{remote_path}\', $bytes)"'
)
ssh.exec_command(decode_cmd)
ssh.exec_command(f'del {remote_dir}\\upload.b64 2>nul')
print('syslog.py uploaded')

# Kill and restart
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(2)
ssh.exec_command('schtasks /run /tn "MinerDashboard"')
time.sleep(8)

# Check
stdin, stdout, stderr = ssh.exec_command('tasklist | findstr python')
print(f'Python: {stdout.read().decode("gbk", errors="replace").strip()}')

# Wait for syslog to collect
print('Waiting 20s for collector...')
time.sleep(20)

# Check syslog
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content C:\\Users\\sydrro_ssh\\Desktop\\miner308\\syslog.log -Tail 5"')
print(f'syslog.log: {stdout.read().decode("gbk", errors="replace").strip()}')

ssh.close()

# Test from local
import requests
try:
    r = requests.get('http://192.168.3.8:5000/api/syslog/summary', timeout=10)
    if r.status_code == 200 and r.text.strip():
        import json
        data = r.json()
        print(f'\nSyslog summary: snapshots={data.get("snapshots")} events={data.get("event_counts", {})}')
    else:
        print(f'\nSummary: status={r.status_code} body={r.text[:200]}')
except Exception as e:
    print(f'\nAPI error: {e}')
