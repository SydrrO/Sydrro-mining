import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

# Check power limits
stdin, stdout, stderr = ssh.exec_command('nvidia-smi -q -d POWER')
print(stdout.read().decode('gbk', errors='replace'))

ssh.close()
