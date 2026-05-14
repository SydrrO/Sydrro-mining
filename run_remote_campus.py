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

# Write config to deployed location
sftp = ssh.open_sftp()
cfg_path = 'C:/Users/25623/AppData/Local/CampusEportal/campus_config.json'
f = sftp.open(cfg_path, 'w')
f.write(json.dumps(config, indent=4, ensure_ascii=False))
f.close()
sftp.close()
print('Config updated')

# Kill old daemon
ssh.exec_command('schtasks /end /tn CampusLoginDaemon /f 2>nul')
ssh.exec_command('schtasks /delete /tn CampusLoginDaemon /f 2>nul')
# Kill any running python campus process
ssh.exec_command('taskkill /f /im python.exe /fi "WINDOWTITLE eq Campus*" 2>nul')
time.sleep(2)

# Run once to verify login
py = r'C:\Users\25623\AppData\Local\Programs\Python\Python312\python.exe'
script = r'C:\Users\25623\AppData\Local\CampusEportal\campus_login.py'
cmd = f'"{py}" "{script}" --once'
print('Running:', cmd)
stdin, stdout, stderr = ssh.exec_command(cmd)
time.sleep(6)
out = stdout.read().decode('gbk', errors='replace')
err = stderr.read().decode('gbk', errors='replace')
print(out)
if err:
    print('STDERR:', err)

# Set up scheduled task for auto-start + keepalive
# Run --loop mode as a startup task
loop_cmd = f'"{py}" "{script}" --loop'
task_cmd = f'schtasks /create /tn CampusLoginDaemon /tr "{loop_cmd}" /sc onstart /ru 25623 /f'
stdin, stdout, stderr = ssh.exec_command(task_cmd)
print('Task:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

# Also run it now
ssh.exec_command('schtasks /run /tn CampusLoginDaemon')
time.sleep(2)
print('Daemon started!')

ssh.close()
