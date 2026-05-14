import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.6', username='sydrro_ssh', password='061021', timeout=10)

# Step 1: Generate key on 001
cmds = [
    'mkdir C:\\Users\\sydrro_ssh\\.ssh 2>nul',
    'ssh-keygen -t ed25519 -f C:\\Users\\sydrro_ssh\\.ssh\\id_ed25519 -N "" -q 2>&1',
    'type C:\\Users\\sydrro_ssh\\.ssh\\id_ed25519.pub'
]
pubkey = ""
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('gbk', errors='replace').strip()
    err = stderr.read().decode('gbk', errors='replace').strip()
    if cmd.startswith('type'):
        pubkey = out
    print(f'[{cmd[:40]}]: {out[:80]} {err[:80]}')

print(f'\nPubkey: {pubkey[:60]}...')

# Step 2: From 001, ssh to server and add key using password
add_key_script = f'''
ssh -o StrictHostKeyChecking=no root@47.111.182.166 "mkdir -p ~/.ssh && echo '{pubkey}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo KEY_ADDED" 2>&1
'''
# We need to use sshpass or pipe password. Since sshpass might not be available,
# let's create a temp script and use plink or native ssh with a workaround
# Actually, let's write a Python script on 001 to do the key addition

# Simpler: use paramiko from here to connect 001 -> server via SSH command with password input
# Create a script on 001 that uses plink or ssh with expect-like behavior

# Actually simplest: write the pubkey to a file, then from 001 use scp/ssh
add_cmd = f'ssh -o StrictHostKeyChecking=no root@47.111.182.166 "mkdir -p ~/.ssh && echo \\"{pubkey}\\" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo KEY_ADDED"'
print('\nRunning:', add_cmd[:100] + '...')

# This will prompt for password. Let's use a different approach -
# write a batch file that does it with ssh -W (askpass) or use the fact that
# we can pass password via a file descriptor

# Let's try using ssh with SSH_ASKPASS
# Write a helper vbs/bat that provides password
pw_provider = '@echo off\r\necho Dymc12138\r\n'
sftp = ssh.open_sftp()
f = sftp.open('C:/Users/sydrro_ssh/pw.bat', 'w')
f.write(pw_provider)
f.close()
sftp.close()

add_script = f'''
set SSH_ASKPASS=C:\\Users\\sydrro_ssh\\pw.bat
set DISPLAY=1
ssh -o StrictHostKeyChecking=no root@47.111.182.166 "mkdir -p ~/.ssh && echo "{pubkey}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo KEY_ADDED"
'''

# Actually SSH_ASKPASS is tricky on Windows. Let's use a simpler approach:
# just add the key through the ssh command with password on stdin via Python
# by writing a temporary Python script on 001

# Wait - 001 might not have Python. Let me just try running ssh directly
# and see what happens (maybe passwordless already works, or we can use another method)

# Easiest reliable approach: create a one-time key pair, and add the pubkey manually
# Or: use the fact that from 001 we can run ssh with password via paramiko from HERE
# by connecting to server through 001 as a jump host.

# Actually, the SIMPLEST approach that definitely works:
# I already have the pubkey. Let me use paramiko to connect from my machine
# through the proxy (which might work if 001 can reach the server)

# But I tested and my local machine can't reach the server directly.
# So let me try another way: create a Python script ON 001 that uses paramiko
# to add the key.

# Actually 001 doesn't have Python installed (we checked earlier).
# Let me just write a simple VBS script that spawns ssh with password.

# The truly simplest approach: copy the pubkey to the server manually
# from my local machine using 001 as a jumphost.

print('\nAttempting to add key via jumphost approach...')
# Use paramiko to connect: local -> 001 -> server
# Transport chain: open channel on 001 to server

try:
    # Get 001's transport
    transport_001 = ssh.get_transport()
    if transport_001:
        # Open a direct-tcpip channel from 001 to server:22
        dest_addr = ('47.111.182.166', 22)
        src_addr = ('127.0.0.1', 0)
        channel = transport_001.open_channel('direct-tcpip', dest_addr, src_addr)

        # Use this channel to connect paramiko
        ssh_srv = paramiko.SSHClient()
        ssh_srv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_srv.connect('47.111.182.166', username='root', password='Dymc12138', sock=channel, timeout=15)

        add_cmd = f'mkdir -p ~/.ssh && echo "{pubkey}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo KEY_ADDED'
        stdin, stdout, stderr = ssh_srv.exec_command(add_cmd)
        print('Server says:', stdout.read().decode().strip())
        ssh_srv.close()

        # Test passwordless
        print('\nTesting passwordless SSH from 001...')
        test_cmd = 'ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 root@47.111.182.166 echo TEST_OK'
        stdin, stdout, stderr = ssh.exec_command(test_cmd)
        print('Test:', stdout.read().decode('gbk', errors='replace').strip(), stderr.read().decode('gbk', errors='replace').strip()[:100])

        # Setup tunnel
        print('\nSetting up reverse tunnel...')
        tunnel_cmd = 'ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -fN -R 0.0.0.0:2222:localhost:22 root@47.111.182.166'
        stdin, stdout, stderr = ssh.exec_command(tunnel_cmd)
        print('Tunnel cmd result:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

        time.sleep(2)

        # Verify from server
        ssh_srv2 = paramiko.SSHClient()
        ssh_srv2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        channel2 = transport_001.open_channel('direct-tcpip', dest_addr, src_addr)
        ssh_srv2.connect('47.111.182.166', username='root', password='Dymc12138', sock=channel2, timeout=15)
        stdin, stdout, stderr = ssh_srv2.exec_command('ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 -p 2222 sydrro_ssh@localhost whoami')
        print('Tunnel verification:', stdout.read().decode().strip(), stderr.read().decode().strip())
        ssh_srv2.close()

        # Schedule persistent tunnel
        tunnel_bat = '@echo off\r\nssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes -NT -R 0.0.0.0:2222:localhost:22 root@47.111.182.166\r\n'
        sftp = ssh.open_sftp()
        f = sftp.open('C:/Users/sydrro_ssh/tunnel.bat', 'w')
        f.write(tunnel_bat)
        f.close()
        sftp.close()

        ssh.exec_command('schtasks /delete /tn SSHTunnel /f 2>nul')
        time.sleep(1)
        tr = '"C:\\Users\\sydrro_ssh\\tunnel.bat"'
        task_cmd = f'schtasks /create /tn SSHTunnel /tr {tr} /sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
        stdin, stdout, stderr = ssh.exec_command(task_cmd)
        print('Task:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

        ssh.exec_command('schtasks /run /tn SSHTunnel')
        print('\n=== DONE ===')
        print('Access 001 from anywhere: ssh sydrro_ssh@47.111.182.166 -p 2222')

except Exception as e:
    print(f'Error: {e}')

ssh.close()
