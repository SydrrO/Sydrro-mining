import paramiko
import json
import time

config = {
    "user_id": "2410501002",
    "password": "@bkxBilBil0711",
    "service": "电信互联网服务",
    "portal_host": "172.168.100.21",
    "accounts": [
        {"user_id": "2410501002", "password": "@bkxBilBil0711", "service": "电信互联网服务"},
        {"user_id": "2511507067", "password": "Sydrro061021.", "service": "电信互联网服务"}
    ]
}

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

# Write config via SFTP
sftp = ssh.open_sftp()
cfg_path = 'C:/Users/25623/OneDrive/Desktop/campus-eportal/campus-eportal/campus_config.json'
f = sftp.open(cfg_path, 'w')
f.write(json.dumps(config, indent=4, ensure_ascii=False))
f.close()
sftp.close()
print('Config written')

# Run login once
proj_dir = 'C:\\Users\\25623\\OneDrive\\Desktop\\campus-eportal\\campus-eportal'
cmd = f'cd /d "{proj_dir}" && python campus_login.py --once'
stdin, stdout, stderr = ssh.exec_command(cmd)
time.sleep(5)
print(stdout.read().decode('gbk', errors='replace'))
print(stderr.read().decode('gbk', errors='replace'))

# Schedule daemon if needed - run loop mode via task
# Create startup task
ssh.exec_command('schtasks /end /tn CampusLogin /f 2>nul')
ssh.exec_command('schtasks /delete /tn CampusLogin /f 2>nul')
time.sleep(1)

bat = f'"{proj_dir}\\start-campus-eportal.bat"'
create = f'schtasks /create /tn CampusLogin /tr {bat} /sc onstart /ru 25623 /f'
stdin, stdout, stderr = ssh.exec_command(create)
out = stdout.read().decode('gbk', errors='replace')
err = stderr.read().decode('gbk', errors='replace')
print('Task create:', out, err)

ssh.close()
print('Done!')
