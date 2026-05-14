import paramiko, time

ssh = paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)

# Create task that runs interactively in user session
cmd = 'schtasks /create /tn Msg002 /tr "cmd /c start D:\\ujlzmnfg43\\index.html" /sc once /st 00:00 /sd 2024/01/01 /it /f'
ssh.exec_command(cmd)
time.sleep(1)
ssh.exec_command('schtasks /run /tn Msg002')
time.sleep(3)
ssh.exec_command('schtasks /delete /tn Msg002 /f 2>nul')

print('Pop-up sent to 002 desktop!')
ssh.close()
