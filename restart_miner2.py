import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

# Kill old
ssh.exec_command('schtasks /end /tn "MinerRigel" 2>nul')
ssh.exec_command('schtasks /delete /tn "MinerRigel" /f 2>nul')
ssh.exec_command('taskkill /f /im rigel.exe 2>nul')
time.sleep(2)

# Write bat via SFTP
bat_path = '/Users/25623/OneDrive/Desktop/rigel-1.23.1-win/a_api.bat'
sftp = ssh.open_sftp()
bat = '@echo off\r\ncd /d "%~dp0"\r\nrigel.exe -a octopus -o stratum+tcp://cfx.f2pool.com:6800 -u sydrro.rtx2080ti --api-bind 0.0.0.0:5000 --log-file rigel.log\r\n'
f = sftp.open('C:' + bat_path, 'w')
f.write(bat.replace('\r\n', '\r\n'))
f.close()
sftp.close()
print('Bat file written')

# Create and run task
tr = '"C:\\Users\\25623\\OneDrive\\Desktop\\rigel-1.23.1-win\\a_api.bat"'
create = f'schtasks /create /tn "MinerRigel" /tr {tr} /sc once /st 00:00 /sd 01/01/2024 /ru 25623 /f'
stdin, stdout, stderr = ssh.exec_command(create)
out = stdout.read().decode('gbk', errors='replace')
err = stderr.read().decode('gbk', errors='replace')
print('Create:', out, err)

time.sleep(1)
stdin, stdout, stderr = ssh.exec_command('schtasks /run /tn "MinerRigel"')
print('Run:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

print('Waiting 10s for miner to start...')
time.sleep(10)

# Try API
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:5000 2>nul')
data = stdout.read().decode('gbk', errors='replace').strip()
if data:
    print('=== API Response ===')
    print(data[:3000])
else:
    print('API not available, checking log...')
    stdin, stdout, stderr = ssh.exec_command('type C:\\Users\\25623\\OneDrive\\Desktop\\rigel-1.23.1-win\\rigel.log 2>nul')
    log = stdout.read().decode('gbk', errors='replace')
    if log:
        print(log[-2000:])
    else:
        stdin, stdout, stderr = ssh.exec_command('powershell.exe -Command "Get-Process -Name rigel -ErrorAction SilentlyContinue | Select-Object Id"')
        print('Rigel process:', stdout.read().decode('gbk', errors='replace'))

ssh.close()
