import paramiko
import time

# Connect to 001
ssh_001 = paramiko.SSHClient()
ssh_001.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_001.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

# Generate key
cmds = [
    'mkdir C:\\Users\\sydrro_ssh\\.ssh 2>nul',
    'ssh-keygen -t ed25519 -f C:\\Users\\sydrro_ssh\\.ssh\\id_ed25519 -N "" -q',
    'type C:\\Users\\sydrro_ssh\\.ssh\\id_ed25519.pub'
]

for cmd in cmds:
    stdin, stdout, stderr = ssh_001.exec_command(cmd)
    out = stdout.read().decode('gbk', errors='replace').strip()
    err = stderr.read().decode('gbk', errors='replace').strip()
    if out:
        print(out)
    if err and 'already exists' not in err.lower() and 'exist' not in err.lower():
        print('ERR:', err[:200])

pubkey = out  # last output is the public key
print('Public key:', pubkey[:80] + '...')

# Add public key to remote server
ssh_srv = paramiko.SSHClient()
ssh_srv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_srv.connect('47.111.182.166', username='root', password='Dymc12138', timeout=10)

# Add key to authorized_keys
add_cmd = f'mkdir -p ~/.ssh && echo "{pubkey}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo OK'
stdin, stdout, stderr = ssh_srv.exec_command(add_cmd)
print('Server:', stdout.read().decode().strip())

# Test passwordless SSH from 001 to server
test_cmd = 'ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 root@47.111.182.166 echo TEST_OK'
stdin, stdout, stderr = ssh_001.exec_command(test_cmd)
result = stdout.read().decode('gbk', errors='replace').strip()
err = stderr.read().decode('gbk', errors='replace').strip()
print('Test connect:', result, err)

if 'TEST_OK' in result:
    print('Passwordless SSH working!')

    # Set up reverse tunnel: server:2222 -> 001:22
    tunnel_cmd = 'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -fN -R 0.0.0.0:2222:localhost:22 root@47.111.182.166'
    stdin, stdout, stderr = ssh_001.exec_command(tunnel_cmd)
    out = stdout.read().decode('gbk', errors='replace')
    err = stderr.read().decode('gbk', errors='replace')
    print('Tunnel:', out, err)

    time.sleep(2)

    # Test: from server, try to SSH back to 001 via the tunnel
    test_tunnel = 'ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 -p 2222 sydrro_ssh@localhost echo TUNNEL_OK'
    stdin, stdout, stderr = ssh_srv.exec_command(test_tunnel)
    result2 = stdout.read().decode().strip()
    err2 = stderr.read().decode().strip()
    print('Tunnel test:', result2, err2)

    if 'TUNNEL_OK' in result2:
        print('\nSUCCESS! Reverse tunnel active.')
        print('Access 001 from anywhere: ssh sydrro_ssh@47.111.182.166 -p 2222')

        # Create scheduled task on 001 to maintain tunnel persistently
        tunnel_bat = '@echo off\r\nssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes -NT -R 0.0.0.0:2222:localhost:22 root@47.111.182.166\r\n'
        sftp = ssh_001.open_sftp()
        f = sftp.open('C:/Users/sydrro_ssh/tunnel.bat', 'w')
        f.write(tunnel_bat)
        f.close()
        sftp.close()

        ssh_001.exec_command('schtasks /delete /tn SSHTunnel /f 2>nul')
        time.sleep(1)
        tr = '"C:\\Users\\sydrro_ssh\\tunnel.bat"'
        task_cmd = f'schtasks /create /tn SSHTunnel /tr {tr} /sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
        stdin, stdout, stderr = ssh_001.exec_command(task_cmd)
        print('Task:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

        # Run now
        ssh_001.exec_command('schtasks /run /tn SSHTunnel')
        print('Tunnel scheduled for auto-start on boot.')
    else:
        print('Tunnel test failed. Manual check needed.')
else:
    print('Passwordless SSH NOT working. Check key setup.')

ssh_001.close()
ssh_srv.close()
