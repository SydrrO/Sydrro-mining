import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

def run(cmd, timeout=15):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('gbk', errors='replace').strip()
    err = stderr.read().decode('gbk', errors='replace').strip()
    return out, err

# Upload a PowerShell script to add hosts entry (requires admin via Start-Process -Verb RunAs)
# Since we don't have interactive admin, let's try a different approach:
# Deploy a new Python proxy that uses the IP directly

# First, check what Python versions are available on 3.8
out, err = run('where python.exe 2>nul & where pythonw.exe 2>nul')
print(f'Python paths: {out[:500]}')
print()

# Check if there's a writable Python proxy script
# The proxy on port 3335 is proxy_silent.exe (compiled). Let's deploy a Python version.
out, err = run('dir C:\\Users\\sydrro_ssh\\Desktop\\proxy*.py /b 2>nul')
print(f'Proxy py files: {out[:500] if out else "NONE"}')
print()

# Check if we have the source stratum_proxy.py already
out, err = run('dir C:\\Users\\sydrro_ssh\\Desktop\\miner308\\proxy*.py /b 2>nul')
print(f'miner308 proxy py: {out[:500] if out else "NONE"}')
print()

# Check the Desktop for any Python files
out, err = run('dir C:\\Users\\sydrro_ssh\\Desktop\\*.py /b 2>nul')
print(f'Desktop py files: {out[:500]}')
print()

# Test if we can write a test file
out, err = run('echo test > C:\\Users\\sydrro_ssh\\Desktop\\test_write.txt 2>&1 && type C:\\Users\\sydrro_ssh\\Desktop\\test_write.txt')
print(f'Write test: {out[:200]}')

ssh.close()
