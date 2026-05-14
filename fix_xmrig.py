import paramiko
import time
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

bat_path = 'C:/Users/25623/OneDrive/Desktop/xmrig/xmrig-6.22.2/start.bat'
sftp = ssh.open_sftp()

# Try supportxmr.com pool - reliable and widely used
bat = '@echo off\r\n'
bat += 'cd /d "%~dp0"\r\n'
bat += 'xmrig.exe -o stratum+tcp://pool.supportxmr.com:3333 -u sydrro.5800x -p x --threads=14 --cpu-priority=5 --donate-level=1 --http-host=0.0.0.0 --http-port=6000 --log-file=xmrig.log\r\n'

f = sftp.open(bat_path, 'w')
f.write(bat)
f.close()
sftp.close()
print('Batch file updated with supportxmr.com')

# Restart via task
ssh.exec_command('schtasks /run /tn "CPUMiner"')
print('Task triggered')

# Wait and poll
for i in range(6):
    time.sleep(5)
    stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:6000/1/summary')
    try:
        data = json.loads(stdout.read().decode())
        hr = data.get('hashrate', {}).get('total', [0, 0, 0])
        conn = data.get('connection', {})
        pool = conn.get('pool', '?')
        accepted = conn.get('accepted', 0)
        print(f'+{5*(i+1)}s | Hashrate: {hr[0]/1000:.1f} KH/s | Accepted: {accepted} | Pool: {pool}')
        if hr[0] > 0:
            print('SUCCESS! CPU mining is working!')
            break
    except Exception as e:
        print(f'Error: {e}')

ssh.close()
