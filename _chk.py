import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# Get all HW_SPIKE and restart events from watchdog log
cmd = 'powershell -Command "Get-Content C:/Users/sydrro_ssh/Desktop/miner308/watchdog.log | Select-String -Pattern \'HW_SPIKE|RESTART|FREQ_DROP\'"'
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8', errors='replace').strip()

print("=== All HW_SPIKE / RESTART events ===")
if out:
    for line in out.split('\n'):
        print(line.strip())
else:
    print('(none)')

# Also count OK events to see normal runtime intervals
cmd2 = 'powershell -Command "Get-Content C:/Users/sydrro_ssh/Desktop/miner308/watchdog.log | Select-String -Pattern \'\\[OK\\]|\\[HW_SPIKE\\]|\\[ACTION\\] RESTART|\\[ACTION\\] FREQ\' | Select-Object -Last 30"'
stdin, stdout, stderr = ssh.exec_command(cmd2)
out2 = stdout.read().decode('utf-8', errors='replace').strip()

print("\n=== Last 30 OK / HW_SPIKE / RESTART ===")
if out2:
    for line in out2.split('\n'):
        print(line.strip())

ssh.close()
