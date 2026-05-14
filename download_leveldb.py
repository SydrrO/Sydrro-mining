import paramiko
import os

host = '192.168.3.6'
user = 'sydrro_ssh'
pwd = '061021'

remote_dir = 'C:/Users/25623/AppData/Local/com.ccswitch.desktop/EBWebView/Default/Local Storage/leveldb'
local_dir = 'D:/ccswitch_leveldb'

os.makedirs(local_dir, exist_ok=True)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=pwd, timeout=10)
sftp = ssh.open_sftp()

for item in sftp.listdir_attr(remote_dir):
    rp = remote_dir + '/' + item.filename
    lp = local_dir + '/' + item.filename
    try:
        sftp.get(rp, lp)
        print(f'OK  {item.filename} ({item.st_size} bytes)')
    except Exception as e:
        print(f'ERR {item.filename}: {e}')

sftp.close()
ssh.close()
print('Done!')
