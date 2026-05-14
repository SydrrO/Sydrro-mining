import paramiko
import os

host = '192.168.3.6'
user = 'sydrro_ssh'
pwd = '061021'

base = 'C:/Users/25623/AppData/Local/com.ccswitch.desktop/EBWebView/Default'
local_base = 'D:/ccswitch_data'

dirs = ['Session Storage', 'shared_proto_db', 'shared_proto_db/metadata']

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=pwd, timeout=10)
sftp = ssh.open_sftp()

for d in dirs:
    remote_dir = base + '/' + d
    local_dir = os.path.join(local_base, d.replace('/', '_'))
    os.makedirs(local_dir, exist_ok=True)
    try:
        for item in sftp.listdir_attr(remote_dir):
            rp = remote_dir + '/' + item.filename
            lp = local_dir + '/' + item.filename
            try:
                sftp.get(rp, lp)
                print(f'OK  {d}/{item.filename} ({item.st_size} bytes)')
            except Exception as e:
                print(f'ERR {d}/{item.filename}: {e}')
    except Exception as e:
        print(f'ERR listing {d}: {e}')

sftp.close()
ssh.close()
print('Done!')
