import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

cmds = [
    ('Python process detail', 'wmic process where name="python.exe" get ProcessId,CommandLine /format:list'),
    ('Check users', 'dir C:\\Users 2>nul'),
    ('Powershell find config', 'powershell -Command "Get-ChildItem -Path C:\\Users\\sydrro_ssh -Filter config.yaml -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName"'),
    ('Check home dirs', 'powershell -Command "Get-ChildItem C:\\Users\\sydrro_ssh -Directory -ErrorAction SilentlyContinue | Select-Object Name"'),
]
for label, cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('gbk', errors='replace').strip()
    err = stderr.read().decode('gbk', errors='replace').strip()
    print(f'\n=== {label} ===')
    if out: print(out[:1000])
    if err: print('ERR:', err[:200])

ssh.close()
