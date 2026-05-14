import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.5', username='root', password='ltc@dog', timeout=10)

# Use channel-level timeout for each command
def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    return out, err

# Check key config files
for fname in ['final_0.conf', 'final_1.conf', 'run_mode.conf', 'network.conf', 'cgminer.conf']:
    out, err = run(f'cat /config/{fname}')
    print(f'=== /config/{fname} ===')
    print(out[:500] if out else '(empty/nonexistent)')
    if err: print(f'stderr: {err[:200]}')
    print()

# Check if cgminer is running via pidof
out, err = run('pidof cgminer')
print(f'cgminer pid: {out if out else "NOT RUNNING"}')
print()

# Check recent logs
out, err = run('cat /var/log/messages 2>/dev/null | tail -20')
print(f'=== /var/log/messages tail ===')
print(out[:1000] if out else '(none)')
print()

# Check /tmp
out, err = run('ls -la /tmp/ 2>/dev/null | head -20')
print(f'=== /tmp ===')
print(out[:500])
print()

# What scripts run cgminer?
out, err = run('cat /config/start_miner_fixed.sh')
print(f'=== start_miner_fixed.sh ===')
print(out[:1000] if out else '(empty)')
print()

ssh.close()
