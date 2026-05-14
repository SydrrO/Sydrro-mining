"""Deploy stratum proxy on 192.168.3.8 for GPU miner (cfx octopus)."""
import paramiko, base64, time

PROXY_SCRIPT = r'''
import socket, threading, sys

LOCAL_HOST = "0.0.0.0"
LOCAL_PORT = 16900
REMOTE_HOST = "cfx.f2pool.com"
REMOTE_PORT = 6800

def pipe(src, dst, name):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except Exception:
        pass

def handle_client(client_sock, addr):
    remote = None
    try:
        remote = socket.socket()
        remote.settimeout(10)
        remote.connect((REMOTE_HOST, REMOTE_PORT))
        remote.settimeout(None)
        client_sock.settimeout(None)
        print(f"[gpu-proxy] {addr[0]}:{addr[1]} -> {REMOTE_HOST}:{REMOTE_PORT}")
        t1 = threading.Thread(target=pipe, args=(client_sock, remote, "c2r"), daemon=True)
        t2 = threading.Thread(target=pipe, args=(remote, client_sock, "r2c"), daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    except Exception as e:
        print(f"[gpu-proxy] error: {e}")
    finally:
        try:
            client_sock.close()
        except Exception:
            pass
        if remote:
            try:
                remote.close()
            except Exception:
                pass

def main():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((LOCAL_HOST, LOCAL_PORT))
    s.listen(50)
    print(f"[gpu-proxy] Listening on {LOCAL_HOST}:{LOCAL_PORT} -> {REMOTE_HOST}:{REMOTE_PORT}")
    while True:
        try:
            c, a = s.accept()
            threading.Thread(target=handle_client, args=(c, a), daemon=True).start()
        except KeyboardInterrupt:
            break
    s.close()

if __name__ == "__main__":
    main()
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

def run(cmd):
    stdin, out, err = ssh.exec_command(cmd)
    return out.read().decode('gbk', errors='replace') + err.read().decode('gbk', errors='replace')

# Upload proxy script via PowerShell base64
b64 = base64.b64encode(PROXY_SCRIPT.encode('utf-8')).decode('ascii')
target = r'C:\Users\sydrro_ssh\gpu_stratum_proxy.py'
ps_cmd = '[System.IO.File]::WriteAllBytes("' + target + '", [System.Convert]::FromBase64String("' + b64 + '"))'
ps_bytes = ps_cmd.encode('utf-16-le')
ps_b64 = base64.b64encode(ps_bytes).decode('ascii')
o = run(f'powershell -EncodedCommand {ps_b64}')
print(f'Upload: {"OK" if not o.strip() else o[:80]}')

# Kill old proxy on 16900 if any
run('for /f "tokens=5" %a in (\'netstat -ano ^| findstr :16900 ^| findstr LISTENING\') do taskkill /f /pid %a 2>nul')
time.sleep(1)

# Start proxy in background
run('pythonw C:\\Users\\sydrro_ssh\\gpu_stratum_proxy.py')
time.sleep(2)

# Verify
o = run('netstat -an | findstr :16900')
print(f'Port 16900: {"LISTENING" if "LISTENING" in o else "NOT LISTENING"}')
print(o.strip())

# Create scheduled task for auto-start
run(r'schtasks /delete /tn "GpuStratumProxy" /f 2>nul')
time.sleep(1)

ps_exe = r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
# Actually use pythonw directly
task_cmd = (
    'schtasks /create /tn "GpuStratumProxy" '
    '/tr "pythonw C:\\Users\\sydrro_ssh\\gpu_stratum_proxy.py" '
    '/sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
)
o = run(task_cmd)
print(f'Scheduled task: {o[:100]}')

ssh.close()
print('\nDone! GPU stratum proxy deployed on 192.168.3.8:16900')
