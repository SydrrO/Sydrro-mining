import paramiko, random, string, time

ssh = paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)

# Random folder on D:
name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
folder = 'D:\\' + name
ssh.exec_command('mkdir ' + folder + ' 2>nul')
time.sleep(1)

# HTML content
html = '<html><body style="background:#000;display:flex;align-items:center;justify-content:center;height:100vh;margin:0"><h1 style="color:red;font-size:80px;font-family:Microsoft YaHei">沙先涛是你爸爸</h1></body></html>'

# Write via SFTP
sftp = ssh.open_sftp()
f = sftp.open(folder + '/index.html', 'w')
f.write(html)
f.close()
sftp.close()

# Open on desktop
ssh.exec_command('cmd /c "start ' + folder + '\\index.html"')

print('Path:', folder + '\\index.html')
print('Opened on 002!')
ssh.close()
