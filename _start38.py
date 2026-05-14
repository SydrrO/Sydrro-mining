import paramiko, time, requests

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# Kill any stuck Python
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(2)

# Start via scheduled task
print('Starting app...')
ssh.exec_command('schtasks /run /tn "MinerDashboard"')

# Wait and poll
for i in range(8):
    time.sleep(5)
    stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr 5000 | findstr LISTENING')
    port = stdout.read().decode('gbk', errors='replace').strip()
    stdin2, stdout2, stderr2 = ssh.exec_command('tasklist | findstr python')
    procs = stdout2.read().decode('gbk', errors='replace').strip()
    elapsed = (i + 1) * 5
    print(f'  [{elapsed}s] Python: {"RUNNING" if procs else "NO"} | Port 5000: {"LISTENING" if port else "NO"}')
    if port:
        break

ssh.close()

if port:
    # Test API
    time.sleep(5)
    for attempt in range(5):
        try:
            r = requests.get('http://192.168.3.8:5000/api/syslog/summary', timeout=10)
            if r.ok and r.text.strip():
                data = r.json()
                print(f'\n=== SUCCESS ===')
                print(f'Syslog snapshots: {data.get("snapshots")}')
                print(f'Event counts: {data.get("event_counts", {})}')
                print(f'Last snapshot: {data.get("last_snapshot_ts")}')

                # Also check events
                r2 = requests.get('http://192.168.3.8:5000/api/syslog/events?n=10', timeout=10)
                events = r2.json().get('events', [])
                print(f'\nRecent events:')
                for e in events[-10:]:
                    print(f'  [{e["ts"]}] [{e["type"]}] {e["msg"]}')
                break
        except Exception as e:
            print(f'  Attempt {attempt+1}: {e}')
            time.sleep(5)
else:
    print('\nApp failed to start.')
