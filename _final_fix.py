"""Final fix: start GPU proxy on 3.8 + restart rigel on 3.6."""
import paramiko, base64, time, urllib.request, json

# ── Part 1: Start GPU stratum proxy on 3.8 ─────────────────────────

pythonw = r'C:\Users\sydrro_ssh\Desktop\miner308\python312\pythonw.exe'
proxy_script = r'C:\Users\sydrro_ssh\gpu_stratum_proxy.py'
bat_path = r'C:\Users\sydrro_ssh\start_gpu_proxy.bat'

ssh38 = paramiko.SSHClient()
ssh38.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh38.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

def run38(cmd):
    stdin, out, err = ssh38.exec_command(cmd)
    return out.read().decode('gbk', errors='replace') + err.read().decode('gbk', errors='replace')

# Create batch file via PowerShell
bat_content = '@echo off\r\nstart "" "' + pythonw + '" "' + proxy_script + '"\r\n'
b64 = base64.b64encode(bat_content.encode('utf-8')).decode('ascii')
ps = '[System.IO.File]::WriteAllBytes("' + bat_path + '", [System.Convert]::FromBase64String("' + b64 + '"))'
ps_bytes = ps.encode('utf-16-le')
ps_b64 = base64.b64encode(ps_bytes).decode('ascii')
run38('powershell -EncodedCommand ' + ps_b64)
print('Batch file written')

# Kill any existing proxy on 16900
run38('for /f "tokens=5" %a in (\'netstat -ano ^| findstr :16900 ^| findstr LISTENING\') do taskkill /f /pid %a 2>nul')
time.sleep(1)

# Start via batch file
run38('cmd /c "' + bat_path + '"')
time.sleep(4)

# Verify
o = run38('netstat -an | findstr :16900')
proxy_up = 'LISTENING' in o
print(f'Proxy port 16900: {"UP" if proxy_up else "DOWN"}')
if not proxy_up:
    # Try one more time with full path
    run38('cmd /c start "" /b "' + pythonw + '" "' + proxy_script + '"')
    time.sleep(3)
    o = run38('netstat -an | findstr :16900')
    proxy_up = 'LISTENING' in o
    print(f'Proxy retry: {"UP" if proxy_up else "FAILED"}')

# Update scheduled task
run38('schtasks /delete /tn GpuStratumProxy /f 2>nul')
time.sleep(1)
# Use cmd /c to run the batch file
task = 'schtasks /create /tn GpuStratumProxy /tr "cmd /c ' + bat_path + '" /sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
run38(task)
print('Scheduled task updated')

ssh38.close()

# ── Part 2: Update and restart rigel on 3.6 ──────────────────────

print('\n--- Restarting Rigel ---')

ssh36 = paramiko.SSHClient()
ssh36.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh36.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

def run36(cmd):
    stdin, out, err = ssh36.exec_command(cmd)
    return out.read().decode('gbk', errors='replace') + err.read().decode('gbk', errors='replace')

rigel_dir = r'C:\Users\25623\OneDrive\Desktop\rigel-1.23.1-win'
bat_target = rigel_dir + r'\start_miner.bat'

# Kill rigel
print('Killing rigel...')
run36('taskkill /f /im rigel.exe 2>nul')
time.sleep(2)

# Write updated bat - use proxy if it's up, otherwise direct IP
if proxy_up:
    pool = 'stratum+tcp://192.168.3.8:16900'
    print(f'Using proxy: {pool}')
else:
    pool = 'stratum+tcp://202.173.11.130:6800'
    print(f'Using direct IP: {pool}')

new_bat = '@echo off\r\ncd /d "' + rigel_dir + '"\r\nrigel.exe -a octopus -o ' + pool + ' -u sydrro.rtx2080ti --cclock 100 --mclock 800 --api-bind 0.0.0.0:5000 --log-file logs/miner.log --no-tui\r\n'

b64_bat = base64.b64encode(new_bat.encode('utf-8')).decode('ascii')
ps = '[System.IO.File]::WriteAllBytes("' + bat_target + '", [System.Convert]::FromBase64String("' + b64_bat + '"))'
ps_bytes = ps.encode('utf-16-le')
ps_b64_bat = base64.b64encode(ps_bytes).decode('ascii')
run36('powershell -EncodedCommand ' + ps_b64_bat)
print('start_miner.bat updated')

# Start rigel
run36('cmd /c "' + bat_target + '"')
time.sleep(8)

# Check status
o = run36('tasklist | findstr rigel')
print('Rigel: ' + ('RUNNING' if 'rigel' in o else 'NOT RUNNING'))

ssh36.close()

# ── Part 3: Monitor GPU ──────────────────────────────────────────

print('\n--- GPU Status Monitor ---')
for i in range(6):
    time.sleep(15)
    try:
        r = urllib.request.urlopen('http://192.168.3.6:5000/summary', timeout=5)
        d = json.loads(r.read())
        dev = d['devices'][0]
        pool = d['pools']['octopus'][0]
        state = dev['state']
        hr = dev['hashrate']['octopus']
        temp = dev['monitoring_info']['core_temperature']
        power = dev['monitoring_info']['power_usage']
        shares = dev['solution_stat']['octopus']['accepted']
        pool_state = pool.get('state', '?')
        print(f'[{i+1}] State={state} HR={hr:.1f}MH/s Temp={temp}C Power={power:.0f}W Shares={shares} Pool={pool_state}')
        if state == 'active' and hr > 0:
            print('\nGPU mining ACTIVE!')
            break
    except Exception as e:
        print(f'[{i+1}] API error: {e}')

print('\nDone!')
