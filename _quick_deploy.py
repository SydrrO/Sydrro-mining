"""Quick redeploy syslog.py via HTTP."""
import paramiko, time, threading, os
from http.server import HTTPServer, SimpleHTTPRequestHandler

serve_dir = r'd:\sydrro-projects\sydrro-mining\miner-monitor'
os.chdir(serve_dir)
httpd = HTTPServer(('0.0.0.0', 8888), SimpleHTTPRequestHandler)
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
time.sleep(1)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(2)

# Download via PS (this worked before for syslog.py)
ps_cmd = (
    'powershell -Command '
    '"Invoke-WebRequest -Uri http://192.168.3.2:8888/syslog.py '
    '-OutFile C:\\Users\\sydrro_ssh\\Desktop\\miner308\\syslog.py"'
)
ssh.exec_command(ps_cmd)
time.sleep(4)

# Verify
stdin, stdout, stderr = ssh.exec_command(
    'powershell -Command "(Get-Item C:\\Users\\sydrro_ssh\\Desktop\\miner308\\syslog.py).Length"'
)
size = stdout.read().decode('gbk', errors='replace').strip()
local = os.path.getsize(os.path.join(serve_dir, 'syslog.py'))
ok = size and int(size) == local
print(f'syslog.py: {size} bytes (local: {local}) [{"OK" if ok else "FAIL"}]')

if ok:
    ssh.exec_command('schtasks /run /tn "MinerDashboard"')
    time.sleep(15)

    # Test internally
    stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:5000/api/syslog/summary 2>nul')
    out = stdout.read().decode('gbk', errors='replace').strip()
    print(f'\nInternal test: {out[:500]}')

    # Test events
    stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:5000/api/syslog/events?n=5 2>nul')
    evts = stdout.read().decode('gbk', errors='replace').strip()
    print(f'Events: {evts[:300]}')

ssh.close()
httpd.shutdown()

if ok:
    import requests
    time.sleep(5)
    try:
        r = requests.get('http://192.168.3.8:5000/api/syslog/summary', timeout=10)
        if r.ok:
            import json
            print(f'\nExternal test: {json.dumps(r.json(), indent=2)}')
    except Exception as e:
        print(f'External: {e}')

print('\nDone')
