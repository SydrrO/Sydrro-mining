import subprocess
import time
import json
import urllib.request
import os

rigel_dir = r'D:\rigel-1.23.1-win'
exe = os.path.join(rigel_dir, 'rigel.exe')

# Check max power limit first
result = subprocess.run(['nvidia-smi', '-q', '-d', 'POWER'], capture_output=True, text=True)
print(result.stdout)

# Start miner with a.bat config + API + more aggressive OC
# RTX 5060 Ti: try --mclock +3000, --cclock -200 (save core power for memory)
# --pl 0 means no power limit change
cmd = [
    exe,
    '-a', 'octopus',
    '-o', 'stratum+tcp://cfx.f2pool.com:6800',
    '-u', 'sydrro.rtx5060ti',
    '--cclock', '-200',
    '--mclock', '+3000',
    '--api-bind', '0.0.0.0:5000',
    '--log-file', os.path.join(rigel_dir, 'logs', 'miner.log')
]

print('Starting:', ' '.join(cmd))
print()

# Start miner in background
proc = subprocess.Popen(cmd, cwd=rigel_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f'Miner PID: {proc.pid}')

# Wait and poll API
time.sleep(10)
for i in range(5):
    time.sleep(4)
    try:
        with urllib.request.urlopen('http://127.0.0.1:5000', timeout=5) as resp:
            data = json.loads(resp.read().decode())
            hr = data['hashrate']['octopus']
            dev = data['devices'][0]
            mi = dev['monitoring_info']
            pwr = mi['power_usage']
            temp = mi['core_temperature']
            core = mi['core_clock']
            mem = mi['memory_clock']
            print(f'+{4*(i+1)+10}s | Hashrate: {hr/1e6:.1f} MH/s | Power: {pwr:.0f}W | Temp: {temp}C | Core: {core}MHz | Mem: {mem}MHz')
            if hr > 0:
                print()
                print('SUCCESS! Miner running.')
                break
    except Exception as e:
        print(f'Waiting... ({e})')
