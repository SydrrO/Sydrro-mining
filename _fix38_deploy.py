"""Start proxy via cmd start command (more reliable)."""
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

def run(cmd, timeout=10):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('gbk', errors='replace').strip()
    err = stderr.read().decode('gbk', errors='replace').strip()
    return out, err

# Check if port 3335 is free now
out, err = run('netstat -ano 2>nul | findstr ":3335" | findstr LISTENING')
print(f'Port 3335 before: {out if out else "FREE"}')

# Kill any remaining python on port 3335
out, err = run('netstat -ano 2>nul | findstr ":3335" | findstr LISTENING')
if out:
    for line in out.split('\n'):
        parts = line.strip().split()
        pid = parts[-1]
        if pid.isdigit():
            run(f'taskkill /f /pid {pid} 2>nul')
            print(f'Killed PID {pid}')
            time.sleep(1)

# Verify port is free
out, err = run('netstat -ano 2>nul | findstr ":3335" | findstr LISTENING')
print(f'Port 3335 after kill: {out if out else "FREE"}')

# Start proxy - try multiple approaches
print("\n=== Starting proxy ===")

# Method 1: cmd /c start with title (most reliable for background)
py_path = r'C:\Users\sydrro_ssh\Desktop\miner308\python312\pythonw.exe'
script_path = r'C:\Users\sydrro_ssh\Desktop\proxy_fixed.py'
work_dir = r'C:\Users\sydrro_ssh\Desktop'

# Use start command with window title for proper process group
cmd = f'start "Proxy3335" /b /min "{py_path}" "{script_path}"'
out, err = run(f'cmd /c "{cmd}"')
print(f'Method 1 result: out={out[:100]}, err={err[:100]}')
time.sleep(3)

out, err = run('netstat -ano 2>nul | findstr ":3335" | findstr LISTENING')
if out:
    print(f'Port 3335: {out}')
else:
    print('Port 3335: NOT LISTENING')

    # Method 2: direct execution via batch file
    print('\n=== Method 2: via batch file ===')
    # Create batch
    batch_lines = [
        '@echo off',
        f'cd /d "{work_dir}"',
        f'start "" /b "{py_path}" "{script_path}" > proxy_fixed.log 2>&1',
    ]
    batch_content = '\r\n'.join(batch_lines)

    sftp = None
    try:
        sftp = ssh.open_sftp()
        f = sftp.open('C:\\Users\\sydrro_ssh\\Desktop\\start_proxy_fixed.bat', 'w')
        f.write(batch_content)
        f.close()
        sftp.close()
        print('Batch file created')
    except Exception as e:
        print(f'Batch upload: {e}')
        if sftp:
            sftp.close()
        # Write via echo
        for line in batch_lines:
            run(f'echo {line} >> C:\\Users\\sydrro_ssh\\Desktop\\start_proxy_fixed.bat 2>nul')
        print('Batch via echo')
    time.sleep(1)

    # Run batch
    run('C:\\Users\\sydrro_ssh\\Desktop\\start_proxy_fixed.bat')
    time.sleep(5)

    out, err = run('netstat -ano 2>nul | findstr ":3335" | findstr LISTENING')
    if out:
        print(f'Port 3335 after batch: {out}')
    else:
        print('Port 3335 after batch: NOT LISTENING')

        # Method 3: Run with python.exe (not pythonw) to see errors
        print('\n=== Method 3: python.exe (capture error) ===')
        test_cmd = f'cmd /c ""{py_path.replace("pythonw.exe", "python.exe")}" "{script_path}" 2>&1"'
        stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=8)
        time.sleep(3)
        try:
            out = stdout.read().decode('gbk', errors='replace')
            err = stderr.read().decode('gbk', errors='replace')
            print(f'stdout: {out[:500]}')
            print(f'stderr: {err[:500]}')
        except Exception as e:
            print(f'Read error: {e}')

# Final status
out, err = run('netstat -ano 2>nul | findstr ":3335" | findstr LISTENING')
print(f'\nFinal port 3335: {out if out else "NOT LISTENING"}')

out, err = run('tasklist 2>nul | findstr /i "python proxy"')
print(f'Processes:\n{out[:500]}')

ssh.close()
