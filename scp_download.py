import paramiko
import os
import sys

host = '192.168.3.6'
user = 'sydrro_ssh'
pwd = '061021'

remote_root = 'C:/Users/25623/OneDrive/Desktop/campus-eportal'
local_root = 'D:/campus-eportal'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=pwd, timeout=10)
sftp = ssh.open_sftp()

def download_dir(remote_dir, local_dir):
    os.makedirs(local_dir, exist_ok=True)
    for item in sftp.listdir_attr(remote_dir):
        rp = remote_dir + '/' + item.filename
        lp = local_dir + '/' + item.filename
        if item.st_mode & 0o40000:  # directory
            print(f'DIR  {rp}')
            download_dir(rp, lp)
        else:
            print(f'FILE {rp} ({item.st_size} bytes)')
            sftp.get(rp, lp)

print(f'Downloading from {remote_root} to {local_root}...')
download_dir(remote_root, local_root)
print('Done!')
sftp.close()
ssh.close()
