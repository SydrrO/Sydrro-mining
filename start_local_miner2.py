import subprocess
import time
import json
import urllib.request
import os

rigel_dir = r'D:\rigel-1.23.1-win'
exe = os.path.join(rigel_dir, 'rigel.exe')

# Kill any existing
subprocess.run(['taskkill', '/f', '/im', 'rigel.exe'], capture_output=True)
time.sleep(2)

# Start with --pl 220, conservative mem OC for GDDR7
cmd = [
    exe,
    '-a', 'octopus',
    '-o', 'stratum+tcp://cfx.f2pool.com:6800',
    '-u', 'sydrro.rtx5060ti',
    '--pl', '220',
    '--cclock', '-200',
    '--mclock', '+2000',
    '--api-bind', '0.0.0.0:5000',
    '--log-file', os.path.join(rigel_dir, 'logs', 'miner.log')
]

print('Starting: --pl 220 --cclock -200 --mclock +2000')
proc = subprocess.Popen(cmd, cwd=rigel_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f'PID: {proc.pid}')

for i in range(8):
    time.sleep(5)
    try:
        with urllib.request.urlopen('http://127.0.0.1:5000', timeout=3) as resp:
            data = json.loads(resp.read().decode())
        hr = data['hashrate']['octopus']
        dev = data['devices'][0]
        mi = dev['monitoring_info']
        pwr = mi['power_usage']
        temp = mi['core_temperature']
        core = mi['core_clock']
        mem = mi['memory_clock']
        shares = dev['solution_stat']['octopus']['accepted']
        print(f'+{5*(i+1)}s | {hr/1e6:.1f} MH/s | {pwr:.0f}W | {temp}C | Core:{core} Mem:{mem} | OK:{shares}')
        if hr > 0 and i >= 2:
            break
    except Exception as e:
        print(f'+{5*(i+1)}s | waiting... ({e})')

# Final
print()
try:
    with urllib.request.urlopen('http://127.0.0.1:5000', timeout=3) as resp:
        data = json.loads(resp.read().decode())
    hr_mhs = data['hashrate']['octopus'] / 1e6
    mi = data['devices'][0]['monitoring_info']
    pwr = mi['power_usage']
    temp = mi['core_temperature']
    core = mi['core_clock']
    mem = mi['memory_clock']
    fan = mi['fan_speed']
    print('=' * 50)
    print('  LOCAL MINING - RTX 5060 Ti - Conflux (CFX)')
    print('=' * 50)
    print(f'  Hashrate:  {hr_mhs:.1f} MH/s')
    print(f'  Power:     {pwr:.0f}W')
    print(f'  Temp:      {temp}C')
    print(f'  Core:      {core}MHz')
    print(f'  Memory:    {mem}MHz')
    print(f'  Fan:       {fan}%')
    print(f'  API:       http://127.0.0.1:5000')
except Exception as e:
    print(f'Error: {e}')
    result = subprocess.run(['tasklist', '/fi', 'imagename eq rigel.exe'], capture_output=True, text=True)
    print(result.stdout)
