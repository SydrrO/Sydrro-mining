import paramiko, time, base64

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

def run(cmd):
    stdin, out, err = ssh.exec_command(cmd)
    return out.read().decode('gbk', errors='replace') + err.read().decode('gbk', errors='replace')

# Kill rigel
print('Killing rigel...')
run('taskkill /f /im rigel.exe 2>nul')
time.sleep(2)

# Verify killed
o = run('tasklist | findstr rigel')
print(f'Rigel: {"STILL ALIVE" if o.strip() else "KILLED"}')

# Write new start_miner.bat with direct f2pool IP
bat_content = (
    '@echo off\r\n'
    'cd /d "C:\\Users\\25623\\OneDrive\\Desktop\\rigel-1.23.1-win"\r\n'
    'rigel.exe -a octopus -o stratum+tcp://202.173.11.130:6800 -u sydrro.rtx2080ti '
    '--cclock 100 --mclock 800 --api-bind 0.0.0.0:5000 --log-file logs/miner.log --no-tui\r\n'
)

b64 = base64.b64encode(bat_content.encode('utf-8')).decode('ascii')
target = r'C:\Users\25623\OneDrive\Desktop\rigel-1.23.1-win\start_miner.bat'
ps = '[System.IO.File]::WriteAllBytes("' + target + '", [System.Convert]::FromBase64String("' + b64 + '"))'
ps_bytes = ps.encode('utf-16-le')
ps_b64 = base64.b64encode(ps_bytes).decode('ascii')
o = run('powershell -EncodedCommand ' + ps_b64)
print(f'Write bat: {"OK" if not o.strip() else o[:80]}')

# Start rigel via scheduled task (uses updated bat)
print('Starting via GpuMiner task...')
run('schtasks /run /tn GpuMiner 2>nul')
time.sleep(8)

# Quick check
o = run('tasklist | findstr rigel')
print(f'Rigel: {"RUNNING" if "rigel" in o else "NOT RUNNING"}')

ssh.close()
