"""Deploy via HTTP — write remote download script as base64, decode & run."""
import paramiko, time, threading, os, base64
from http.server import HTTPServer, SimpleHTTPRequestHandler

serve_dir = r'd:\sydrro-projects\sydrro-mining\miner-monitor'
os.chdir(serve_dir)

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

httpd = HTTPServer(('0.0.0.0', 8888), Handler)
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
print('HTTP server ready on :8888')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# Kill Python
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(1)

# Create a Python download script, base64 it, send via PS
dl_script = (
    "import urllib.request\r\n"
    "import os\r\n"
    "base = r'C:\\Users\\sydrro_ssh\\Desktop\\miner308'\r\n"
    "for f in ['syslog.py', 'app.py']:\r\n"
    "    url = f'http://192.168.3.2:8888/{f}'\r\n"
    "    dst = os.path.join(base, f)\r\n"
    "    urllib.request.urlretrieve(url, dst)\r\n"
    "    size = os.path.getsize(dst)\r\n"
    "    print(f'{f}: {size} bytes')\r\n"
)
b64 = base64.b64encode(dl_script.encode('utf-8')).decode('ascii')

# Write base64, decode, run
ssh.exec_command(
    f'powershell -Command '
    f'"Set-Content -Path C:\\Users\\sydrro_ssh\\Desktop\\miner308\\_dl.py.b64 -Value \'{b64}\'"'
)
ssh.exec_command(
    'powershell -Command '
    '"$b64=Get-Content C:\\Users\\sydrro_ssh\\Desktop\\miner308\\_dl.py.b64 -Raw; '
    '[System.IO.File]::WriteAllBytes(\'C:\\Users\\sydrro_ssh\\Desktop\\miner308\\_dl.py\', [Convert]::FromBase64String($b64))"'
)

print('Downloading files via remote Python...')
stdin, stdout, stderr = ssh.exec_command(
    'cmd /c "cd /d C:\\Users\\sydrro_ssh\\Desktop\\miner308 && python312\\python.exe _dl.py"',
    timeout=20
)
out = stdout.read().decode('gbk', errors='replace')
err = stderr.read().decode('gbk', errors='replace')
print(out.strip())
if err:
    print(f'ERR: {err[:300]}')

# Clean up temp files
ssh.exec_command('del C:\\Users\\sydrro_ssh\\Desktop\\miner308\\_dl.py 2>nul')
ssh.exec_command('del C:\\Users\\sydrro_ssh\\Desktop\\miner308\\_dl.py.b64 2>nul')

# Verify sizes
for fname in ['syslog.py', 'app.py']:
    stdin, stdout, stderr = ssh.exec_command(
        f'powershell -Command "(Get-Item C:\\Users\\sydrro_ssh\\Desktop\\miner308\\{fname}).Length"'
    )
    size = stdout.read().decode('gbk', errors='replace').strip()
    local_size = os.path.getsize(os.path.join(serve_dir, fname))
    match = 'OK' if size and int(size) == local_size else f'MISMATCH (local: {local_size})'
    print(f'{fname}: {size} bytes [{match}]')

# Restart
print('\nRestarting via scheduled task...')
ssh.exec_command('schtasks /run /tn "MinerDashboard"')
time.sleep(12)

stdin, stdout, stderr = ssh.exec_command('tasklist | findstr python')
procs = stdout.read().decode('gbk', errors='replace').strip()
print(f'Python: {procs[:100] if procs else "NOT RUNNING"}')

stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr 5000 | findstr LISTENING')
port = stdout.read().decode('gbk', errors='replace').strip()
print(f'Port 5000: {port if port else "NOT LISTENING"}')

ssh.close()
httpd.shutdown()

# Test
if port:
    import requests
    time.sleep(10)
    try:
        r = requests.get('http://192.168.3.8:5000/api/syslog/summary', timeout=15)
        if r.ok and r.text.strip():
            data = r.json()
            print(f'\nSyslog: snapshots={data.get("snapshots")}, events={data.get("event_counts", {})}')
        else:
            print(f'\nSyslog empty: {r.status_code}')
    except Exception as e:
        print(f'\nAPI error: {e}')
