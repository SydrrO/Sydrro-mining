import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# Test summary API from within 3.8
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:5000/api/syslog/summary 2>nul')
out = stdout.read().decode('gbk', errors='replace').strip()
print(f'Summary (internal): {out[:500]}')

# Test events
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:5000/api/syslog/events?n=10 2>nul')
out = stdout.read().decode('gbk', errors='replace').strip()
print(f'\nEvents (internal): {out[:500]}')

# Check latest syslog entries
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content C:\\Users\\sydrro_ssh\\Desktop\\miner308\\syslog.log -Tail 20"')
log = stdout.read().decode('gbk', errors='replace').strip()
print(f'\nsyslog.log tail:')
print(log)

ssh.close()
