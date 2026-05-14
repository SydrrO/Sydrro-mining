import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# Query tasks with CSV format
for task in ['MinerWatchdog', 'Watchdog38', 'MinerDashboard', 'GpuStratumProxy', 'FrpTunnel', 'NatappTunnel', 'SshTunnel', 'StratumProxy', 'ProxyAutoStart']:
    stdin, stdout, stderr = ssh.exec_command(f'schtasks /query /tn {task} /fo csv /v 2>&1')
    raw = stdout.read()
    for enc in ['utf-8', 'gbk', 'latin-1']:
        try:
            out = raw.decode(enc).strip()
            if out: break
        except:
            continue
    print(f'=== {task} ===')
    if out and 'ERROR' not in out and out != '""':
        # Split CSV - fields: HostName,TaskName,NextRunTime,Status,LogonMode,LastRunTime,LastResult,Author,TaskToRun,StartIn,Comment,ScheduledTaskState,IdleTime,PowerManagement,RunAsUser,DeleteTaskIfNotRescheduled,StopTaskIfRunsXHoursXMinutes,Schedule,...
        fields = out.split('","')
        cmd = fields[8] if len(fields) > 8 else '?'
        status = fields[3] if len(fields) > 3 else '?'
        schedule = fields[17] if len(fields) > 17 else '?'
        print(f'  Status: {status}')
        print(f'  Command: {cmd[:200]}')
        print(f'  Schedule: {schedule[:100]}')
    else:
        print(f'  (empty or error)')
    print()

# Check running services on 3.8
stdin, stdout, stderr = ssh.exec_command('netstat -ano 2>nul | findstr LISTENING | findstr "5000 17890 3389 22"')
out = stdout.read().decode('gbk', errors='replace').strip()
print(f'Listening ports:\n{out[:500]}')

# Check python and other running processes
stdin, stdout, stderr = ssh.exec_command('tasklist 2>nul | findstr /i "python proxy frp natapp powershell"')
out = stdout.read().decode('gbk', errors='replace').strip()
print(f'\nKey processes:\n{out[:500]}')

ssh.close()
