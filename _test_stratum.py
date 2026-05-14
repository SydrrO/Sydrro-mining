"""Upload and run stratum test on 3.8 via base64."""
import paramiko, time, base64

TEST_SCRIPT = '''
import socket, json, time

targets = [
    ("172.65.249.114", 3335),
    ("172.65.249.114", 8888),
    ("202.173.11.130", 3335),
    ("202.173.11.130", 8888),
    ("202.173.11.130", 25),
]

for host, port in targets:
    try:
        s = socket.socket()
        s.settimeout(5)
        s.connect((host, port))
        print(f"TCP OK: {host}:{port}")

        msg = json.dumps({"id": 1, "method": "mining.subscribe", "params": ["cpuminer/2.5.0"]})
        s.sendall((msg + "\\n").encode())

        time.sleep(2)
        s.settimeout(3)
        try:
            data = s.recv(4096)
            print(f"  STRATUM: {data[:200]}")
        except socket.timeout:
            print(f"  NO RESP")
        except Exception as e:
            print(f"  RECV: {e}")
        s.close()
    except Exception as e:
        print(f"FAIL: {host}:{port} - {e}")
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

def run(cmd, timeout=10):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('gbk', errors='replace').strip()
    err = stderr.read().decode('gbk', errors='replace').strip()
    return out, err

# Upload via base64
b64 = base64.b64encode(TEST_SCRIPT.encode()).decode()
chunks = [b64[i:i+4000] for i in range(0, len(b64), 4000)]
for chunk in chunks:
    run(f'powershell -Command "Add-Content -Path C:\\Users\\sydrro_ssh\\Desktop\\test_stratum.b64 -Value \'{chunk}\'"')

run('powershell -Command "$b64 = Get-Content C:\\Users\\sydrro_ssh\\Desktop\\test_stratum.b64 -Raw; $bytes = [Convert]::FromBase64String($b64.Trim()); [System.IO.File]::WriteAllBytes(\'C:\\Users\\sydrro_ssh\\Desktop\\test_stratum.py\', $bytes)"')

# Verify
out, err = run('type C:\\Users\\sydrro_ssh\\Desktop\\test_stratum.py 2>nul | findstr "targets"')
print(f'Verify: {out[:100]}')

# Run
print('\nRunning test...')
stdin, stdout, stderr = ssh.exec_command(
    'C:\\Users\\sydrro_ssh\\Desktop\\miner308\\python312\\python.exe C:\\Users\\sydrro_ssh\\Desktop\\test_stratum.py',
    timeout=60
)

# Read with timeout
import select
start = time.time()
out_data = b''
err_data = b''
while time.time() - start < 50:
    if stdout.channel.recv_ready():
        out_data += stdout.channel.recv(4096)
    if stderr.channel.recv_ready():
        err_data += stderr.channel.recv(4096)
    if stdout.channel.exit_status_ready():
        # Read remaining
        while stdout.channel.recv_ready():
            out_data += stdout.channel.recv(4096)
        while stderr.channel.recv_ready():
            err_data += stderr.channel.recv(4096)
        break
    time.sleep(0.5)

print(f'stdout:\n{out_data.decode("gbk", errors="replace")}')
if err_data:
    print(f'stderr:\n{err_data.decode("gbk", errors="replace")}')

# Cleanup
run('del C:\\Users\\sydrro_ssh\\Desktop\\test_stratum.b64 2>nul')
run('del C:\\Users\\sydrro_ssh\\Desktop\\test_stratum.py 2>nul')

ssh.close()
