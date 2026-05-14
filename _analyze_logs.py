"""Analyze current logs to understand disconnect patterns."""
import paramiko

print("=" * 60)
print("MINER SIDE - Log Analysis")
print("=" * 60)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.5', username='root', password='ltc@dog', timeout=10)

# Get cgminer API data (port 4028 with --api-listen)
for label, cmd in [
    ('cgminer summary', 'echo -n \'{"command":"summary"}\' | nc -w 2 127.0.0.1 4028 2>/dev/null'),
    ('cgminer pools', 'echo -n \'{"command":"pools"}\' | nc -w 2 127.0.0.1 4028 2>/dev/null'),
    ('cgminer devs', 'echo -n \'{"command":"devs"}\' | nc -w 2 127.0.0.1 4028 2>/dev/null'),
    ('cgminer stats', 'echo -n \'{"command":"stats"}\' | nc -w 2 127.0.0.1 4028 2>/dev/null'),
    ('network drops', 'cat /proc/net/dev | tail -1'),
    ('netstat', 'netstat -an 2>/dev/null | head -20'),
    ('dmesg errors', 'dmesg | grep -i "error\|fail\|drop\|reset\|link\|down" | tail -20'),
    ('cgminer conf', 'cat /config/cgminer.conf'),
    ('chain logs - last restart', 'strings /fpgabit/logs/log_current.txt | grep -i "error\|fail\|reset\|timeout\|pool\|stratum\|disconnect\|reconnect\|dead\|alive" | tail -40'),
    ('log_current tail 100', 'tail -100 /fpgabit/logs/log_current.txt'),
    ('processes', 'ps'),
]:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    print(f'\n--- {label} ---')
    if out: print(out[:1200])
    if err: print('ERR:', err[:200])

ssh.close()

print()
print("=" * 60)
print("MONITOR SIDE (192.168.3.8) - Watchdog Log")
print("=" * 60)

ssh2 = paramiko.SSHClient()
ssh2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh2.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

for label, cmd in [
    ('watchdog log tail', 'powershell -Command "Get-Content C:\\Users\\sydrro_ssh\\Desktop\\miner308\\watchdog.log -Tail 80"'),
    ('gpu events log', 'powershell -Command "Get-Content C:\\Users\\sydrro_ssh\\Desktop\\miner308\\gpu_events.log -Tail 30 -ErrorAction SilentlyContinue"'),
    ('log files list', 'dir C:\\Users\\sydrro_ssh\\Desktop\\miner308\\*.log 2>nul'),
]:
    stdin, stdout, stderr = ssh2.exec_command(cmd)
    out = stdout.read().decode('gbk', errors='replace').strip()
    err = stderr.read().decode('gbk', errors='replace').strip()
    print(f'\n--- {label} ---')
    if out: print(out[:1500])
    if err: print('ERR:', err[:200])

ssh2.close()
