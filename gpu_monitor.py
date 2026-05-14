import paramiko
import time
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

os.system('cls' if os.name == 'nt' else 'clear')
print('RTX 2080 Ti - Conflux Octopus Mining Monitor')
print('=' * 55)
print(f'{"Time":<10} {"GPU%":<7} {"Mem%":<7} {"Power":<8} {"Temp":<7} {"Fan%":<7}')
print('-' * 55)

try:
    while True:
        stdin, stdout, stderr = ssh.exec_command(
            'nvidia-smi --query-gpu=utilization.gpu,utilization.memory,power.draw,temperature.gpu,fan.speed --format=csv,noheader,nounits'
        )
        data = stdout.read().decode('gbk', errors='replace').strip()
        now = time.strftime('%H:%M:%S')
        parts = data.split(', ')
        if len(parts) >= 5:
            print(f'{now:<10} {parts[0]:<7} {parts[1]:<7} {parts[2]:<8} {parts[3]:<7} {parts[4]:<7}')
        time.sleep(3)
except KeyboardInterrupt:
    print('\nStopped.')
    ssh.close()
