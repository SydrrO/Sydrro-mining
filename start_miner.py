import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

rigel_dir = 'C:\\Users\\25623\\OneDrive\\Desktop\\rigel-1.23.1-win'
cmd = f'cd /d "{rigel_dir}" && start /b rigel.exe -a octopus -o stratum+tcp://cfx.f2pool.com:6800 -u sydrro.rtx2080ti'

stdin, stdout, stderr = ssh.exec_command(cmd)
print('Started!')
time.sleep(5)

# Verify it's running
stdin2, stdout2, stderr2 = ssh.exec_command('tasklist /fi "imagename eq rigel.exe"')
print(stdout2.read().decode('gbk', errors='replace'))

ssh.close()
