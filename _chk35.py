import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.5', username='root', password='ltc@dog', timeout=10)

# Check miner status via local API (VolcMiner API)
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1/cgi-bin/miner_status.cgi 2>/dev/null')
out = stdout.read().decode().strip()
print(f'=== miner_status.cgi ===\n{out[:1000]}')

# Check main status
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1/cgi-bin/status.cgi 2>/dev/null')
out = stdout.read().decode().strip()
print(f'\n=== status.cgi ===\n{out[:1000]}')

# Check miner info
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1/cgi-bin/miner_info.cgi 2>/dev/null')
out = stdout.read().decode().strip()
print(f'\n=== miner_info.cgi ===\n{out[:1000]}')

# Check pools
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1/cgi-bin/pools.cgi 2>/dev/null')
out = stdout.read().decode().strip()
print(f'\n=== pools.cgi ===\n{out[:1000]}')

# Check if web pages exist
stdin, stdout, stderr = ssh.exec_command('ls /www/cgi-bin/ 2>/dev/null')
out = stdout.read().decode().strip()
print(f'\n=== /www/cgi-bin ===\n{out[:500]}')

# Check config
stdin, stdout, stderr = ssh.exec_command('cat /config/config.yaml 2>/dev/null | head -50')
out = stdout.read().decode().strip()
print(f'\n=== Config ===\n{out[:1000]}')

ssh.close()
