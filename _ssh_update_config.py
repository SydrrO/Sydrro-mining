import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# Verify config is correct
stdin, stdout, stderr = ssh.exec_command('type C:\\Users\\sydrro_ssh\\Desktop\\miner308\\config.yaml | findstr "user:"')
out = stdout.read().decode('gbk', errors='replace').strip()
print(f'Config user lines:\n{out}')

# Find the scheduled task name
stdin, stdout, stderr = ssh.exec_command('schtasks /query /fo LIST | findstr -i "miner dashboard"')
tasks = stdout.read().decode('gbk', errors='replace').strip()
print(f'\nTasks:\n{tasks[:400]}')

# Try running the MinerDashboard task
print('\nRunning MinerDashboard task...')
stdin, stdout, stderr = ssh.exec_command('schtasks /run /tn "MinerDashboard"')
out = stdout.read().decode('gbk', errors='replace').strip()
err = stderr.read().decode('gbk', errors='replace').strip()
print(f'Run task stdout: {out}')
print(f'Run task stderr: {err}')

time.sleep(5)

# Check if python is running now
stdin, stdout, stderr = ssh.exec_command('tasklist | findstr python')
procs = stdout.read().decode('gbk', errors='replace').strip()
print(f'\nPython processes: {procs if procs else "STILL NOT RUNNING"}')

# Check if the API is responding
if procs:
    stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:5000/api/miner-config 2>nul')
    api = stdout.read().decode('gbk', errors='replace').strip()
    print(f'\nAPI Response: {api[:300]}')

ssh.close()
