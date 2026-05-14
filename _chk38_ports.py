import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# Check ALL listening ports
stdin, stdout, stderr = ssh.exec_command('netstat -ano 2>nul | findstr LISTENING')
out = stdout.read().decode('gbk', errors='replace').strip()
print('=== All listening ports ===')
print(out)

# Check miner308 config
stdin, stdout, stderr = ssh.exec_command('type C:\\Users\\sydrro_ssh\\Desktop\\miner308\\config.yaml 2>nul')
out = stdout.read().decode('gbk', errors='replace').strip()
print('\n=== miner308 config.yaml ===')
print(out[:1500])

# Check stratum proxy config if exists
stdin, stdout, stderr = ssh.exec_command('type C:\\Users\\sydrro_ssh\\Desktop\\miner308\\stratum_proxy_config.json 2>nul')
out = stdout.read().decode('gbk', errors='replace').strip()
print('\n=== stratum_proxy_config ===')
print(out[:1000] if out else 'NOT FOUND')

ssh.close()
