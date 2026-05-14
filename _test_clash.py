"""Test DNS and update proxy to use domain (for Clash routing)."""
import paramiko, time, base64

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

def run(cmd, timeout=10):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('gbk', errors='replace').strip()
    err = stderr.read().decode('gbk', errors='replace').strip()
    return out, err

# 1. Check GPU proxy - is IT working? (It uses domain cfx.f2pool.com)
print("=== GPU proxy connections (port 16900) ===")
out, err = run('netstat -ano 2>nul | findstr "16900"')
print(out[:500])

# Check if GPU proxy has upstream connections working
out, err = run('netstat -ano 2>nul | findstr "6800"')
print(f'\nPort 6800 connections:')
print(out[:500] if out else 'NONE')

# 2. Test Python DNS resolution
print("\n=== DNS test ===")
# Quick inline test
cmd = 'C:\\Users\\sydrro_ssh\\Desktop\\miner308\\python312\\python.exe -c "import socket; print(socket.gethostbyname(\'ltc.f2pool.com\'))"'
out, err = run(cmd, timeout=10)
print(f'gethostbyname ltc.f2pool.com: {out}')
if err: print(f'err: {err[:200]}')

cmd = 'C:\\Users\\sydrro_ssh\\Desktop\\miner308\\python312\\python.exe -c "import socket; print(socket.gethostbyname(\'cfx.f2pool.com\'))"'
out, err = run(cmd, timeout=10)
print(f'gethostbyname cfx.f2pool.com: {out}')
if err: print(f'err: {err[:200]}')

# 3. Check if Clash TUN mode is on by checking network interfaces
print("\n=== Network interfaces ===")
out, err = run('ipconfig 2>nul | findstr /i "tun clash tun"')
print(out[:500] if out else 'No TUN found')

# Check for clash TUN via netsh
out, err = run('netsh interface show interface 2>nul | findstr /i "clash tun"')
print(out[:500] if out else 'No clash TUN interface')

# 4. Most importantly: update proxy_fixed.py to use DOMAIN
# This is the fix - use domain so Clash routes it through VPN
print("\n=== Updating proxy to use DOMAIN ===")

NEW_PROXY = '''
import socket, threading, sys

LOCAL_HOST = "0.0.0.0"
LOCAL_PORT = 3335
REMOTE_HOST = "ltc.f2pool.com"
REMOTE_PORT = 3335

def pipe(src, dst):
    try:
        while True:
            data = src.recv(4096)
            if not data: break
            dst.sendall(data)
    except: pass

def handle_client(client_sock, addr):
    remote = None
    try:
        remote = socket.socket()
        remote.settimeout(8)
        remote.connect((REMOTE_HOST, REMOTE_PORT))
        remote.settimeout(None)
        client_sock.settimeout(None)
        print(f"[proxy] {addr[0]}:{addr[1]} -> {REMOTE_HOST}:{REMOTE_PORT}")
        t1 = threading.Thread(target=pipe, args=(client_sock, remote), daemon=True)
        t2 = threading.Thread(target=pipe, args=(remote, client_sock), daemon=True)
        t1.start(); t2.start()
        t1.join(); t2.join()
    except Exception as e:
        print(f"[proxy] Error {addr}: {e}")
    finally:
        for s in [client_sock, remote]:
            if s:
                try: s.close()
                except: pass
        print(f"[proxy] {addr[0]}:{addr[1]} disconnected")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LOCAL_HOST, LOCAL_PORT))
    server.listen(10)
    print(f"[proxy] {LOCAL_HOST}:{LOCAL_PORT} -> {REMOTE_HOST}:{REMOTE_PORT}")
    while True:
        try:
            client, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(client, addr), daemon=True)
            t.start()
        except KeyboardInterrupt: break
        except Exception as e:
            print(f"[proxy] Accept error: {e}")
    server.close()

if __name__ == "__main__":
    main()
'''

# Upload via base64
b64 = base64.b64encode(NEW_PROXY.encode()).decode()
chunks = [b64[i:i+4000] for i in range(0, len(b64), 4000)]
for chunk in chunks:
    run(f'powershell -Command "Add-Content -Path C:\\Users\\sydrro_ssh\\Desktop\\proxy_domain.b64 -Value \'{chunk}\'"')
run('powershell -Command "$b64 = Get-Content C:\\Users\\sydrro_ssh\\Desktop\\proxy_domain.b64 -Raw; $bytes = [Convert]::FromBase64String($b64.Trim()); [System.IO.File]::WriteAllBytes(\'C:\\Users\\sydrro_ssh\\Desktop\\proxy_domain.py\', $bytes)"')

# Verify domain
out, err = run('type C:\\Users\\sydrro_ssh\\Desktop\\proxy_domain.py 2>nul | findstr REMOTE_HOST')
print(f'New proxy: {out[:200]}')

# 5. Kill current proxy, start new domain-based one
print("\n=== Switching to domain-based proxy ===")
# Kill all python proxies on 3335
out, err = run('netstat -ano 2>nul | findstr ":3335" | findstr LISTENING')
if out:
    for line in out.split('\n'):
        parts = line.strip().split()
        if parts:
            pid = parts[-1]
            if pid.isdigit():
                run(f'taskkill /f /pid {pid} 2>nul')
                print(f'Killed PID {pid}')
    time.sleep(2)

# Start new (use direct python.exe for visibility)
run('cmd /c start "ProxyDomain" /b /min C:\\Users\\sydrro_ssh\\Desktop\\miner308\\python312\\python.exe C:\\Users\\sydrro_ssh\\Desktop\\proxy_domain.py')
time.sleep(5)

# Verify
out, err = run('netstat -ano 2>nul | findstr ":3335" | findstr LISTENING')
print(f'Port 3335: {out if out else "NOT LISTENING"}')

out, err = run('tasklist 2>nul | findstr python')
print(f'\nPython procs:\n{out[:500]}')

# 6. Wait and check dashboard
print("\n=== Waiting 20s for miner to reconnect... ===")
time.sleep(20)

import urllib.request, json
try:
    r = urllib.request.urlopen('http://192.168.3.8:5000/api/syslog/events?n=5', timeout=5)
    data = json.loads(r.read())
    events = data.get('events', [])
    print('Latest events:')
    for e in events:
        print(f'  [{e.get("ts")}] [{e.get("type")}] {e.get("msg")[:120]}')
except Exception as e:
    print(f'Dashboard: {e}')

ssh.close()
print("\nDone!")
