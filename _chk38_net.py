import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    out = stdout.read().decode('gbk', errors='replace').strip()
    err = stderr.read().decode('gbk', errors='replace').strip()
    return out, err

# Check general internet connectivity
out, err = run('ping -n 2 8.8.8.8 2>nul')
print(f'=== ping 8.8.8.8 ===')
print(out[:400])
print()

out, err = run('ping -n 2 223.5.5.5 2>nul')
print(f'=== ping 223.5.5.5 ===')
print(out[:400])
print()

# Check DNS more carefully
out, err = run('nslookup ltc.f2pool.com 223.5.5.5 2>nul')
print(f'=== nslookup via 223.5.5.5 ===')
print(out[:400])
print()

# Try resolving other domains
for d in ['f2pool.com', 'www.baidu.com', 'google.com']:
    out, err = run(f'nslookup {d} 2>nul')
    print(f'=== nslookup {d} ===')
    print(out[:200] if out else 'FAILED')
    print()

# Check proxy startup script for any config
out, err = run('type C:\\Users\\sydrro_ssh\\start_proxy.ps1 2>nul')
print(f'=== start_proxy.ps1 ===')
print(out[:800] if out else 'NOT FOUND')
print()

# Check gpu_stratum_proxy.py
out, err = run('type C:\\Users\\sydrro_ssh\\gpu_stratum_proxy.py 2>nul | head -30')
print(f'=== gpu_stratum_proxy.py (first 30 lines) ===')
print(out[:800] if out else 'NOT FOUND')

ssh.close()
