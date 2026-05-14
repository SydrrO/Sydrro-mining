import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

# Enable persistence mode
stdin, stdout, stderr = ssh.exec_command('nvidia-smi -pm 1')
print('Persistence:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

# Check current clocks
stdin, stdout, stderr = ssh.exec_command('nvidia-smi -q -d CLOCK')
print('Clocks:')
print(stdout.read().decode('gbk', errors='replace'))

# Try memory overclock +1000 MHz (RTX 2080 Ti typically handles +800 to +1200)
# nvidia-smi -ac to set application clocks, or -lgc for lock gpu clock
# For memory OC, we use nvidia-smi -ac with memory clock
stdin, stdout, stderr = ssh.exec_command('nvidia-smi -ac 1560,8400')
print('Set clocks:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

time.sleep(2)

# Verify
stdin, stdout, stderr = ssh.exec_command('nvidia-smi --query-gpu=clocks.sm,clocks.mem,power.draw,temperature.gpu --format=csv')
print('After OC:')
print(stdout.read().decode('gbk', errors='replace'))

ssh.close()
