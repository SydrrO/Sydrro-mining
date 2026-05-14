import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

exe = r"C:\Users\25623\OneDrive\Desktop\rigel-1.23.1-win\rigel.exe"
args = "-a octopus -o stratum+tcp://cfx.f2pool.com:6800 -u sydrro.rtx2080ti"

cmd = f'wmic process call create "{exe} {args}"'
print('Running:', cmd)

stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('gbk', errors='replace')
err = stderr.read().decode('gbk', errors='replace')
print('STDOUT:', out)
print('STDERR:', err)
ssh.close()
