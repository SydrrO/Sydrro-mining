import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

# GPU power
stdin, stdout, stderr = ssh.exec_command('nvidia-smi --query-gpu=power.draw,power.limit --format=csv,noheader,nounits')
gpu_pwr = stdout.read().decode().strip().split(', ')
gpu_w = float(gpu_pwr[0])

# Check CPU miner hashrate for utilization estimate
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:6000/1/summary')
cpu_data = json.loads(stdout.read().decode())
cpu_hr = cpu_data['hashrate']['total'][0] or 0

# Ryzen 5800X PPT is 142W by default. 14/16 threads on RandomX typically uses 80-100W
cpu_est = 95
other = 50  # MB + RAM + fans + drives
total = gpu_w + cpu_est + other

print('=' * 45)
print('  WHOLE SYSTEM POWER ESTIMATE')
print('=' * 45)
print(f'  GPU (RTX 2080 Ti) : {gpu_w:.0f}W  (measured via nvidia-smi)')
print(f'  CPU (Ryzen 5800X) : ~{cpu_est}W (estimated, 14T RandomX)')
print(f'  MB+RAM+Fans+SSD  : ~{other}W')
print(f'  {"─" * 30}')
print(f'  TOTAL            : ~{total:.0f}W')
print(f'  {"─" * 30}')
print()
print(f'Note: GPU limit is {gpu_pwr[1]}W')
print(f'      CPU hashrate: {cpu_hr/1000:.1f} KH/s')
print()
print('Actual total can only be measured with a wattmeter.')
print('Estimated range: 410-440W under full dual-mining load.')

ssh.close()
