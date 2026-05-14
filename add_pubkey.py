import paramiko

# Read pubkey from 001
ssh001 = paramiko.SSHClient()
ssh001.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh001.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)
key_path = r'C:\Users\sydrro_ssh\.ssh\id_ed25519.pub'
stdin, stdout, stderr = ssh001.exec_command('type ' + key_path)
pubkey = stdout.read().decode().strip()
print('Pubkey:', pubkey[:50] + '...')
ssh001.close()

# Add to server
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('47.111.182.166', port=80, username='root', password='Dymc12138', timeout=10)
cmd = 'mkdir -p ~/.ssh && echo "' + pubkey + '" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo ADDED'
stdin, stdout, stderr = ssh.exec_command(cmd)
print('Server:', stdout.read().decode().strip(), stderr.read().decode().strip())
ssh.close()
print('Done - key added!')
