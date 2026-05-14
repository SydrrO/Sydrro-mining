"""Quick fix: GPU proxy on 3.8 + rigel restart on 3.6"""
import paramiko, base64, time, urllib.request, json

# ── Step 1: Write proxy files on 3.8 ─────────────────────────────

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

def write_file(remote_path, content):
    b64 = base64.b64encode(content.encode('utf-8')).decode('ascii')
    ps = '[System.IO.File]::WriteAllBytes("' + remote_path + '", [System.Convert]::FromBase64String("' + b64 + '"))'
    ps_bytes = ps.encode('utf-16-le')
    ps_b64 = base64.b64encode(ps_bytes).decode('ascii')
    stdin, out, err = ssh.exec_command('powershell -EncodedCommand ' + ps_b64)
    e = err.read().decode('gbk', errors='replace')
    return e == '' or 'success' in e.lower()

# Write GPU proxy
proxy_code = '''import socket, threading
LOCAL_HOST, LOCAL_PORT = "0.0.0.0", 16900
REMOTE_HOST, REMOTE_PORT = "202.173.11.130", 6800
def pipe(src, dst):
    try:
        while True:
            data = src.recv(65536)
            if not data: break
            dst.sendall(data)
    except: pass
def handle(client_sock, addr):
    remote = None
    try:
        remote = socket.socket(); remote.settimeout(10)
        remote.connect((REMOTE_HOST, REMOTE_PORT))
        remote.settimeout(None); client_sock.settimeout(None)
        print(f"[gpu-proxy] {addr[0]}:{addr[1]} -> {REMOTE_HOST}:{REMOTE_PORT}")
        t1 = threading.Thread(target=pipe, args=(client_sock, remote), daemon=True)
        t2 = threading.Thread(target=pipe, args=(remote, client_sock), daemon=True)
        t1.start(); t2.start()
        t1.join(); t2.join()
    except Exception as e:
        print(f"[gpu-proxy] error: {e}")
    finally:
        try: client_sock.close()
        except: pass
        if remote:
            try: remote.close()
            except: pass
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((LOCAL_HOST, LOCAL_PORT)); s.listen(50)
print(f"[gpu-proxy] {LOCAL_HOST}:{LOCAL_PORT} -> {REMOTE_HOST}:{REMOTE_PORT}")
while True:
    try:
        c, a = s.accept()
        threading.Thread(target=handle, args=(c, a), daemon=True).start()
    except KeyboardInterrupt: break
s.close()
'''

ok = write_file('C:\\Users\\sydrro_ssh\\gpu_stratum_proxy.py', proxy_code)
print(f'Write proxy: {"OK" if ok else "FAILED"}')

# Write batch launcher
py_path = 'C:\\Users\\sydrro_ssh\\Desktop\\miner308\\python312\\pythonw.exe'
script = 'C:\\Users\\sydrro_ssh\\gpu_stratum_proxy.py'
bat = '@echo off\r\nstart "" /b "' + py_path + '" "' + script + '"\r\n'
ok2 = write_file('C:\\Users\\sydrro_ssh\\start_gpu_proxy.bat', bat)
print(f'Write bat: {"OK" if ok2 else "FAILED"}')

# Kill any existing 16900, then start via scheduled task
ssh.exec_command('for /f "tokens=5" %a in (\'netstat -ano ^| findstr :16900 ^| findstr LISTENING\') do taskkill /f /pid %a 2>nul')
time.sleep(1)

# Delete and recreate scheduled task
ssh.exec_command('schtasks /delete /tn GpuStratumProxy /f 2>nul')
time.sleep(1)

# Create task that runs on startup
task_xml = '''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers><LogonTrigger><Enabled>true</Enabled></LogonTrigger></Triggers>
  <Principals><Principal id="Author"><UserId>sydrro_ssh</UserId><LogonType>InteractiveToken</LogonType><RunLevel>HighestAvailable</RunLevel></Principal></Principals>
  <Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries><StopIfGoingOnBatteries>false</StopIfGoingOnBatteries><AllowHardTerminate>true</AllowHardTerminate><StartWhenAvailable>true</StartWhenAvailable><RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable><IdleSettings><StopOnIdleEnd>false</StopOnIdleEnd><RestartOnIdle>false</RestartOnIdle></IdleSettings><AllowStartOnDemand>true</AllowStartOnDemand><Enabled>true</Enabled><Hidden>true</Hidden><RunOnlyIfIdle>false</RunOnlyIfIdle><WakeToRun>false</WakeToRun><ExecutionTimeLimit>PT0S</ExecutionTimeLimit><Priority>7</Priority></Settings>
  <Actions Context="Author"><Exec><Command>cmd</Command><Arguments>/c C:\\Users\\sydrro_ssh\\start_gpu_proxy.bat</Arguments></Exec></Actions>
</Task>'''

# Write XML then import
ok3 = write_file('C:\\Users\\sydrro_ssh\\gpu_proxy_task.xml', task_xml)
print(f'Write XML: {"OK" if ok3 else "FAILED"}')

ssh.exec_command('schtasks /create /tn GpuStratumProxy /xml "C:\\Users\\sydrro_ssh\\gpu_proxy_task.xml" /ru sydrro_ssh /rp 061021')
time.sleep(1)

# Run the task now
ssh.exec_command('schtasks /run /tn GpuStratumProxy')
time.sleep(4)

# Check port
stdin, out, err = ssh.exec_command('netstat -an | findstr :16900')
o = out.read().decode('gbk', errors='replace') + err.read().decode('gbk', errors='replace')
proxy_up = 'LISTENING' in o
print(f'Port 16900: {"UP" if proxy_up else "DOWN"}')

# Also verify Python processes
stdin, out, err = ssh.exec_command('tasklist | findstr python')
p = out.read().decode('gbk', errors='replace')
print(f'Python procs: {p.count(chr(10))}')

ssh.close()

# ── Step 2: Restart rigel on 3.6 ─────────────────────────────────

print('\n--- GPU Miner ---')
ssh2 = paramiko.SSHClient()
ssh2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh2.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

# Kill and update
ssh2.exec_command('taskkill /f /im rigel.exe 2>nul')
time.sleep(2)

# Update bat with correct pool target
if proxy_up:
    pool = 'stratum+tcp://192.168.3.8:16900'
else:
    pool = 'stratum+tcp://202.173.11.130:6800'

bat2 = '@echo off\r\ncd /d "C:\\Users\\25623\\OneDrive\\Desktop\\rigel-1.23.1-win"\r\nrigel.exe -a octopus -o ' + pool + ' -u sydrro.rtx2080ti --cclock 100 --mclock 800 --api-bind 0.0.0.0:5000 --log-file logs/miner.log --no-tui\r\n'
b64_2 = base64.b64encode(bat2.encode('utf-8')).decode('ascii')
ps2 = '[System.IO.File]::WriteAllBytes("C:\\Users\\25623\\OneDrive\\Desktop\\rigel-1.23.1-win\\start_miner.bat", [System.Convert]::FromBase64String("' + b64_2 + '"))'
ps_bytes2 = ps2.encode('utf-16-le')
ps_b64_2 = base64.b64encode(ps_bytes2).decode('ascii')
ssh2.exec_command('powershell -EncodedCommand ' + ps_b64_2)
print(f'Pool target: {pool}')

# Start
ssh2.exec_command('cmd /c "C:\\Users\\25623\\OneDrive\\Desktop\\rigel-1.23.1-win\\start_miner.bat"')
time.sleep(10)

ssh2.close()

# ── Step 3: Monitor ──────────────────────────────────────────────

print('\n--- Monitoring ---')
for i in range(4):
    time.sleep(15)
    try:
        r = urllib.request.urlopen('http://192.168.3.6:5000/summary', timeout=5)
        d = json.loads(r.read())
        dev = d['devices'][0]
        pool = d['pools']['octopus'][0]
        hr = dev['hashrate']['octopus']
        state = dev['state']
        temp = dev['monitoring_info']['core_temperature']
        power = dev['monitoring_info']['power_usage']
        shares = dev['solution_stat']['octopus']['accepted']
        pstate = pool.get('state', '?')
        conn_err = pool.get('connection_error', '')
        print(f'[{i+1}] {state} | {hr:.1f}MH/s | {temp}C | {power:.0f}W | shares={shares} | pool={pstate}')
        if conn_err:
            print(f'     Pool error: {conn_err}')
        if state == 'active' and hr > 100:
            print('\n>>> GPU MINING ACTIVE! <<<')
            break
    except Exception as e:
        print(f'[{i+1}] API error: {e}')

print('\nDone.')
