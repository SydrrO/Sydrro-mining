"""Fix: download syslog.py only, using PowerShell Invoke-WebRequest."""
import paramiko, time, threading, os
from http.server import HTTPServer, SimpleHTTPRequestHandler

serve_dir = r'd:\sydrro-projects\sydrro-mining\miner-monitor'
os.chdir(serve_dir)

httpd = HTTPServer(('0.0.0.0', 8888), SimpleHTTPRequestHandler)
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
time.sleep(0.5)
print('HTTP ready')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# Kill python (it's running but port not listening — crashed)
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(2)

# Download syslog.py ONLY via PowerShell Invoke-WebRequest
print('Downloading syslog.py...')
cmd = (
    'powershell -Command '
    '"Invoke-WebRequest -Uri http://192.168.3.2:8888/syslog.py '
    '-OutFile C:\\Users\\sydrro_ssh\\Desktop\\miner308\\syslog.py"'
)
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
err = stderr.read().decode('gbk', errors='replace')
out = stdout.read().decode('gbk', errors='replace')
if err: print(f'PS err: {err[:300]}')
if out: print(f'PS out: {out[:300]}')

# Verify
stdin, stdout, stderr = ssh.exec_command(
    'powershell -Command "(Get-Item C:\\Users\\sydrro_ssh\\Desktop\\miner308\\syslog.py).Length"'
)
size = stdout.read().decode('gbk', errors='replace').strip()
local_size = os.path.getsize(os.path.join(serve_dir, 'syslog.py'))
print(f'syslog.py: {size} bytes (local: {local_size}) [{"OK" if size and int(size) == local_size else "MISMATCH"}]')

# Also verify integrity by running Python import test
stdin, stdout, stderr = ssh.exec_command(
    'cmd /c "cd /d C:\\Users\\sydrro_ssh\\Desktop\\miner308 && python312\\python.exe -c \\"import syslog; print(\'syslog OK\')\\" 2>&1"',
    timeout=10
)
out = stdout.read().decode('gbk', errors='replace')
err = stderr.read().decode('gbk', errors='replace')
print(f'Import test: {out.strip()} {err.strip()[:200]}')

# If OK, restart
if 'syslog OK' in out:
    print('\nStarting app...')
    ssh.exec_command('schtasks /run /tn "MinerDashboard"')
    time.sleep(15)

    stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr 5000 | findstr LISTENING')
    port = stdout.read().decode('gbk', errors='replace').strip()
    print(f'Port 5000: {port if port else "NOT LISTENING"}')

    if port:
        import requests
        time.sleep(5)
        try:
            r = requests.get('http://192.168.3.8:5000/api/syslog/summary', timeout=10)
            print(f'\nSyslog: {r.status_code}')
            if r.ok:
                data = r.json()
                print(f'  Snapshots: {data.get("snapshots")}')
                print(f'  Events: {data.get("event_counts", {})}')
        except Exception as e:
            print(f'API: {e}')
else:
    print('\nsyslog import failed - app will crash if started. Check file integrity.')

ssh.close()
httpd.shutdown()
