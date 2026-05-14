import paramiko
import sys

host = '192.168.3.6'
user = 'sydrro_ssh'
pwd = '061021'

base = 'C:/Users/25623/AppData/Local/com.ccswitch.desktop/EBWebView/Default'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=pwd, timeout=10)

# Check IndexedDB
for subdir in ['IndexedDB', 'Session Storage', 'Cache', 'blob_storage', 'Code Cache', 'shared_proto_db']:
    path = base + '/' + subdir
    stdin, stdout, stderr = ssh.exec_command(f'cmd /c "dir /s /b \"{path}\" 2>nul"')
    out = stdout.read()
    try:
        out_str = out.decode('gbk').strip()
    except:
        out_str = out.decode('utf-8', errors='replace').strip()
    if out_str:
        print(f'=== {subdir} ===')
        for line in out_str.split('\n')[:30]:
            print(f'  {line}')

ssh.close()
