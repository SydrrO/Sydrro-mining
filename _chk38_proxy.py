import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    out = stdout.read().decode('gbk', errors='replace').strip()
    err = stderr.read().decode('gbk', errors='replace').strip()
    return out, err

# DNS resolution
out, err = run('nslookup ltc.f2pool.com 2>nul')
print(f'=== DNS: ltc.f2pool.com ===')
print(out[:500] if out else 'FAILED')
if err: print(f'stderr: {err[:200]}')
print()

# TCP connectivity test to upstream
out, err = run('powershell -Command "Test-NetConnection -ComputerName ltc.f2pool.com -Port 3335 -WarningAction SilentlyContinue | Format-List"')
print(f'=== Test-NetConnection ltc.f2pool.com:3335 ===')
print(out[:500] if out else 'FAILED')
print()

# Check the proxy EXE status - what is it forwarding to
out, err = run('wmic process where "name=\'proxy_silent.exe\'" get commandline 2>nul')
print(f'=== proxy_silent.exe commandlines ===')
print(out[:800])

# Also try to read the proxy log if it exists
out, err = run('type C:\\Users\\sydrro_ssh\\Desktop\\miner308\\proxy.log 2>nul')
print(f'\n=== proxy.log ===')
print(out[:500] if out else 'NOT FOUND')

# Check start_gpu_proxy.bat
out, err = run('type C:\\Users\\sydrro_ssh\\start_gpu_proxy.bat 2>nul')
print(f'\n=== start_gpu_proxy.bat ===')
print(out[:1000] if out else 'NOT FOUND')

ssh.close()
