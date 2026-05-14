"""Upload SOCKS5 proxy with proven base64 method and start."""
import paramiko, time, base64, urllib.request, json

proxy_code = '''import socket, threading, struct

LOCAL_HOST = "0.0.0.0"
LOCAL_PORT = 3335
REMOTE_HOST = "ltc.f2pool.com"
REMOTE_PORT = 3335
SOCKS_HOST = "127.0.0.1"
SOCKS_PORT = 7897

def socks5_connect(host, port, timeout=10):
    s = socket.socket()
    s.settimeout(timeout)
    s.connect((SOCKS_HOST, SOCKS_PORT))
    s.sendall(b"\\x05\\x01\\x00")
    resp = s.recv(2)
    if resp != b"\\x05\\x00":
        raise Exception(f"SOCKS5 auth failed: {resp}")
    host_bytes = host.encode()
    req = b"\\x05\\x01\\x00\\x03" + bytes([len(host_bytes)]) + host_bytes + struct.pack(">H", port)
    s.sendall(req)
    resp = s.recv(10)
    if len(resp) < 2 or resp[1] != 0x00:
        raise Exception(f"SOCKS5 connect failed: code={resp[1] if len(resp)>1 else '?'}")
    s.settimeout(None)
    return s

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
        remote = socks5_connect(REMOTE_HOST, REMOTE_PORT, timeout=10)
        client_sock.settimeout(None)
        print(f"[proxy] {addr[0]}:{addr[1]} -> {REMOTE_HOST}:{REMOTE_PORT} (via SOCKS5)")
        t1 = threading.Thread(target=pipe, args=(client_sock, remote), daemon=True)
        t2 = threading.Thread(target=pipe, args=(remote, client_sock), daemon=True)
        t1.start(); t2.start()
        t1.join(); t2.join()
    except Exception as e:
        print(f"[proxy] Error {addr}: {e}")
    finally:
        try: client_sock.close()
        except: pass
        if remote:
            try: remote.close()
            except: pass
        print(f"[proxy] {addr[0]}:{addr[1]} disconnected")

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((LOCAL_HOST, LOCAL_PORT))
s.listen(50)
print(f"[proxy] {LOCAL_HOST}:{LOCAL_PORT} -> {REMOTE_HOST}:{REMOTE_PORT} (via SOCKS5 {SOCKS_HOST}:{SOCKS_PORT})")
while True:
    try:
        c, a = s.accept()
        threading.Thread(target=handle, args=(c, a), daemon=True).start()
    except KeyboardInterrupt: break
s.close()
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=15)

def run(cmd, timeout=10):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('gbk', errors='replace').strip()
    err = stderr.read().decode('gbk', errors='replace').strip()
    return out, err

# Upload proxy_socks5.py via base64 chunk method (PROVEN to work)
print("=== Upload SOCKS5 proxy (base64 chunks) ===")
b64 = base64.b64encode(proxy_code.encode()).decode()
print(f'Script: {len(proxy_code)} bytes, b64: {len(b64)} chars')

chunk_size = 4000
chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]
for i, chunk in enumerate(chunks):
    run(f'powershell -Command "Add-Content -Path C:\\Users\\sydrro_ssh\\Desktop\\proxy_socks5.b64 -Value \'{chunk}\'"')
print(f'Uploaded {len(chunks)} chunks')

# Decode
run('powershell -Command "$b64 = Get-Content C:\\Users\\sydrro_ssh\\Desktop\\proxy_socks5.b64 -Raw; $bytes = [Convert]::FromBase64String($b64.Trim()); [System.IO.File]::WriteAllBytes(\'C:\\Users\\sydrro_ssh\\Desktop\\proxy_socks5.py\', $bytes)"')
run('del C:\\Users\\sydrro_ssh\\Desktop\\proxy_socks5.b64 2>nul')

# Verify file exists and has content
out, err = run('dir C:\\Users\\sydrro_ssh\\Desktop\\proxy_socks5.py 2>nul')
print(f'File: {out[:200] if out else "NOT FOUND!"}')

out, err = run('type C:\\Users\\sydrro_ssh\\Desktop\\proxy_socks5.py 2>nul | findstr SOCKS')
print(f'Content: {out[:200]}')

# Update batch file (PROVEN method)
print("\n=== Update batch file ===")
batch = '@echo off\r\ncd /d "C:\\Users\\sydrro_ssh\\Desktop"\r\nstart "" /b "C:\\Users\\sydrro_ssh\\Desktop\\miner308\\python312\\pythonw.exe" "C:\\Users\\sydrro_ssh\\Desktop\\proxy_socks5.py"\r\n'
ps = '[System.IO.File]::WriteAllBytes("C:\\Users\\sydrro_ssh\\Desktop\\start_ltc_proxy.bat", [System.Convert]::FromBase64String("' + base64.b64encode(batch.encode()).decode() + '"))'
ps_bytes = ps.encode('utf-16-le')
ssh.exec_command('powershell -EncodedCommand ' + base64.b64encode(ps_bytes).decode())
time.sleep(1)

out, err = run('type C:\\Users\\sydrro_ssh\\Desktop\\start_ltc_proxy.bat 2>nul')
print(f'Batch: {out[:300]}')

# Kill old
print("\n=== Kill old & start ===")
run('for /f "tokens=5" %a in (\'netstat -ano ^| findstr :3335 ^| findstr LISTENING\') do taskkill /f /pid %a 2>nul')
time.sleep(2)

# Start via scheduled task
run('schtasks /run /tn LtcStratumProxy')
time.sleep(10)

# Verify
out, err = run('netstat -ano 2>nul | findstr ":3335" | findstr LISTENING')
print(f'Port 3335: {out if out else "NOT LISTENING"}')

out, err = run('tasklist 2>nul | findstr python')
print(f'Python procs: {out[:500]}')

# If still not running, something deeper is wrong
out, err = run('netstat -ano 2>nul | findstr ":3335" | findstr LISTENING')
if not out:
    print("\n=== Still not running - trying direct cmd ===")
    # Try with plain cmd execution (not batch)
    ssh.exec_command('cmd /c "C:\\Users\\sydrro_ssh\\Desktop\\start_ltc_proxy.bat"')
    time.sleep(8)
    out, err = run('netstat -ano 2>nul | findstr ":3335" | findstr LISTENING')
    print(f'After direct cmd: {out if out else "NOT LISTENING"}')

# If running, monitor
out, err = run('netstat -ano 2>nul | findstr ":3335" | findstr LISTENING')
if out:
    print("\n=== Monitor ===")
    for i in range(6):
        time.sleep(10)
        out2, _ = run('netstat -ano 2>nul | findstr ":3335" | findstr "192.168.3.5"')
        out3, _ = run('netstat -ano 2>nul | findstr ":7897" | findstr "ESTABLISHED"')
        if out2 and out3:
            print(f'[{(i+1)*10}s] Miner connected + SOCKS5 active!')
            out4, _ = run('netstat -ano 2>nul | findstr ":3335" | findstr "7897"')
            print(f'  Proxy<->SOCKS5: {out4[:200] if out4 else "checking..."}')

    try:
        r = urllib.request.urlopen('http://192.168.3.8:5000/api/syslog/events?n=5', timeout=5)
        events = json.loads(r.read()).get('events', [])
        print('\nLatest events:')
        for e in events:
            print(f'  [{e.get("ts","")}] [{e.get("type","")}] {e.get("msg","")[:120]}')
    except Exception as e:
        print(f'Dashboard: {e}')

ssh.close()
print("\nDone!")
