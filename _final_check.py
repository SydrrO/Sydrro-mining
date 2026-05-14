"""Final diagnosis: check proxy IP, cgminer status, and try to fix."""
import paramiko, time, urllib.request, json

# Check 3.8 proxy
print("="*50)
print("3.8 PROXY STATUS")
print("="*50)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

def run(ssh_conn, cmd, timeout=10):
    stdin, stdout, stderr = ssh_conn.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('gbk', errors='replace').strip()
    err = stderr.read().decode('gbk', errors='replace').strip()
    return out, err

# Current proxy IP
out, err = run(ssh, 'type C:\\Users\\sydrro_ssh\\Desktop\\proxy_fixed.py 2>nul | findstr REMOTE_HOST')
print(f'Current REMOTE_HOST: {out[:200]}')

# Port status
out, err = run(ssh, 'powershell -Command "Get-NetTCPConnection -LocalPort 3335 -ErrorAction SilentlyContinue | Select-Object LocalPort,RemoteAddress,RemotePort,State"')
print(f'\nPort 3335 connections:')
print(out[:500])

# Check what gpu_stratum_proxy.py does
out, err = run(ssh, 'type C:\\Users\\sydrro_ssh\\gpu_stratum_proxy.py 2>nul | findstr /i "f2pool host port remote"')
print(f'\ngpu_stratum_proxy references: {out[:300]}')

ssh.close()

# Check 3.5 cgminer
print("\n" + "="*50)
print("3.5 ASIC/MINER STATUS")
print("="*50)
ash = paramiko.SSHClient()
ash.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ash.connect('192.168.3.5', username='root', password='ltc@dog', timeout=10)

# Check cgminer if running
out, err = run(ash, 'pidof cgminer')
print(f'cgminer PID: {out}')

# Try cgminer API
out, err = run(ash, 'echo -n "summary+pools" | nc -w 3 127.0.0.1 4028 2>/dev/null', timeout=8)
print(f'\ncgminer API raw: {out[:500]}')

# Check cgminer restart/recovery mechanism
out, err = run(ash, 'cat /config/cgminer.conf', timeout=5)
print(f'\ncgminer config: {out[:500]}')

# Check cgminer log
out, err = run(ash, 'tail -30 /fpgabit/logs/log_current.txt 2>/dev/null')
print(f'\ncgminer/FPGA log tail:')
print(out[:1000] if out else 'NO LOG')

# Check /var/log
out, err = run(ash, 'ls /var/log/ 2>/dev/null; cat /var/log/messages 2>/dev/null | tail -10')
print(f'\n/var/log/messages tail: {out[:500]}')

# Importance: check what pool the cgminer actually uses
out, err = run(ash, 'grep -r "url\|stratum\|pool" /config/cgminer.conf 2>/dev/null')
print(f'\nPool config: {out[:300]}')

ash.close()

# Check dashboard summary for latest
print("\n" + "="*50)
print("DASHBOARD")
print("="*50)
try:
    r = urllib.request.urlopen('http://192.168.3.8:5000/api/syslog/summary', timeout=5)
    data = json.loads(r.read())
    s = data.get('summary', {})
    print(f'Snapshots: {data.get("snapshots")}')
    print(f'Last ts: {data.get("last_snapshot_ts")}')
    for k in ['ghs5s', 'ghsav', 'pool_status', 'hw_total', 'temp1', 'temp2', 'fan2', 'fan3']:
        v = s.get(k, {})
        print(f'  {k}: {v}')
except Exception as e:
    print(f'Dashboard: {e}')
