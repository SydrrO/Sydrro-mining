import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)

dir_path = r'D:\Donwlaods\rigel-1.23.1-win'
base = r'D:\Donwlaods\rigel-1.23.1-win'

# 1. cfx.bat — full config
cfx = '''@echo off
:: CFX / Conflux / Octopus — F2Pool
cd /d "%~dp0"
rigel.exe -a octopus -o stratum+tcp://cfx.f2pool.com:6800 -u sydrro.5070ti --api-bind 0.0.0.0:5002 --log-file logs/miner.log
'''

sftp = ssh.open_sftp()
f = sftp.open(base + '/cfx.bat', 'w')
f.write(cfx)
f.close()

# 2. silent_start.vbs — 完全隐藏窗口静默启动
vbs = '''Set ws = CreateObject("WScript.Shell")
ws.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
ws.Run "rigel.exe -a octopus -o stratum+tcp://cfx.f2pool.com:6800 -u sydrro.5070ti --api-bind 0.0.0.0:5002 --log-file logs/miner.log", 0, False
'''

f = sftp.open(base + '/silent_start.vbs', 'w')
f.write(vbs)
f.close()
sftp.close()

# Verify
stdin, stdout, stderr = ssh.exec_command('cmd /c "dir /b ' + base + '"')
print('Files:')
print(stdout.read().decode('gbk', errors='replace'))

ssh.close()
print('Done!')
print()
print('cfx.bat         — 配置：CFX/F2Pool/sydrro.5070ti')
print('silent_start.vbs — 双击完全静默启动，无窗口')
