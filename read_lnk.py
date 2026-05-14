import paramiko
import re

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)
sftp = ssh.open_sftp()

path = 'C:/Users/25623/OneDrive/Desktop/a - 快捷方式.lnk'
f = sftp.open(path, 'rb')
data = f.read()
f.close()

strings = re.findall(b'[\\x20-\\x7E\\\\]{4,}', data)
for s in strings:
    decoded = s.decode('utf-8', errors='replace')
    if any(k in decoded.lower() for k in ['bat', 'exe', '.\\\\', 'mining', 'miner', 'pool']):
        print(decoded)

print('---')
# Also print all possible paths
paths = re.findall(b'[A-Z]:\\\\[^\\x00]{3,}', data)
for p in paths:
    print(p.decode('utf-8', errors='replace'))

sftp.close()
ssh.close()
