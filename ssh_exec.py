import paramiko
import sys

host = '192.168.3.6'
user = sys.argv[2] if len(sys.argv) > 2 else 'sydrro_ssh'
pwd = '061021'

cmd = sys.argv[1] if len(sys.argv) > 1 else 'whoami'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=pwd, timeout=10)
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read()
try:
    print(out.decode('utf-8').strip())
except UnicodeDecodeError:
    print(out.decode('gbk').strip())
err_raw = stderr.read()
try:
    err = err_raw.decode('utf-8').strip()
except UnicodeDecodeError:
    err = err_raw.decode('gbk').strip()
if err:
    print("STDERR:", err)
ssh.close()
