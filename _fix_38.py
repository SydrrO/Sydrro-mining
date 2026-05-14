import paramiko, time, base64

# Read local config.yaml
with open(r'd:\sydrro-projects\sydrro-mining\miner-monitor\config.yaml', 'rb') as f:
    local_content = f.read()

print(f'Local config size: {len(local_content)} bytes')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# Kill Python first
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(1)

# Upload via base64 encoding
b64 = base64.b64encode(local_content).decode('ascii')

# Split into chunks to avoid command line length limits
chunk_size = 4000
chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]
print(f'Uploading in {len(chunks)} chunks...')

# Write chunks to a temp file
for i, chunk in enumerate(chunks):
    cmd = f'powershell -Command "Add-Content -Path C:\\Users\\sydrro_ssh\\Desktop\\miner308\\config.b64 -Value \'{chunk}\'"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    err = stderr.read().decode('gbk', errors='replace')
    if err and 'error' in err.lower():
        print(f'Chunk {i} error: {err[:100]}')

print('Decoding on remote...')
stdin, stdout, stderr = ssh.exec_command(
    'powershell -Command "$b64 = Get-Content C:\\Users\\sydrro_ssh\\Desktop\\miner308\\config.b64 -Raw; '
    '$bytes = [Convert]::FromBase64String($b64); '
    '[System.IO.File]::WriteAllBytes(\'C:\\Users\\sydrro_ssh\\Desktop\\miner308\\config.yaml\', $bytes)"'
)
err = stderr.read().decode('gbk', errors='replace')
out = stdout.read().decode('gbk', errors='replace')
print(f'Decode: out={out[:100]}, err={err[:100]}')

# Clean up temp file
ssh.exec_command('del C:\\Users\\sydrro_ssh\\Desktop\\miner308\\config.b64 2>nul')

# Verify
stdin, stdout, stderr = ssh.exec_command('type "C:\\Users\\sydrro_ssh\\Desktop\\miner308\\config.yaml" | findstr "user:"')
verify = stdout.read().decode('gbk', errors='replace').strip()
print(f'\n=== Verification ===')
print(verify)

if 'VolcMiner-D1-MINI' not in verify:
    print('[FAIL] Config not updated correctly')
    ssh.close()
    exit(1)

# Also verify YAML is valid by running a quick Python check
stdin, stdout, stderr = ssh.exec_command(
    'cmd /c "cd /d C:\\Users\\sydrro_ssh\\Desktop\\miner308 && '
    'python312\\python.exe -c \\"import yaml; yaml.safe_load(open(\'config.yaml\')); print(\'YAML OK\')\\" "'
)
yaml_check = stdout.read().decode('gbk', errors='replace').strip()
err = stderr.read().decode('gbk', errors='replace').strip()
print(f'\nYAML check: {yaml_check}')
if err: print(f'YAML err: {err[:200]}')

# Now start the app
print('\nStarting app...')
ssh.exec_command('cmd /c "cd /d C:\\Users\\sydrro_ssh\\Desktop\\miner308 && start /b python312\\python.exe app.py > startup.log 2>&1"')
time.sleep(5)

# Check
stdin, stdout, stderr = ssh.exec_command('tasklist | findstr python')
procs = stdout.read().decode('gbk', errors='replace').strip()
print(f'Python: {procs if procs else "NOT RUNNING"}')

stdin, stdout, stderr = ssh.exec_command('type C:\\Users\\sydrro_ssh\\Desktop\\miner308\\startup.log 2>nul')
log = stdout.read().decode('gbk', errors='replace').strip()
if log and 'Error' in log and 'Traceback' not in log:
    # Show last few lines
    for line in log.split('\n')[-5:]:
        print(f'  LOG: {line}')

# Test API from within the machine
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:5000/api/miner-config 2>nul')
api = stdout.read().decode('gbk', errors='replace').strip()
print(f'\nAPI test: {api[:300] if api else "empty"}')

ssh.close()
