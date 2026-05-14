import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)

base = r'D:\Donwlaods\rigel-1.23.1-win'

# Watchdog script: monitors GPU usage by non-rigel processes
# If another app takes >30% GPU, pause mining; resume when idle
watchdog_ps1 = r'''
$minerExe = "rigel.exe"
$minerPath = "D:\Donwlaods\rigel-1.23.1-win"
$threshold = 20  # GPU% threshold to trigger pause
$checkInterval = 10  # seconds between checks

$miningActive = $true

while ($true) {
    # Get GPU utilization
    $gpuInfo = nvidia-smi --query-gpu=utilization.gpu,name --format=csv,noheader,nounits 2>$null
    if (-not $gpuInfo) { Start-Sleep $checkInterval; continue }

    $gpuUtil = [int]($gpuInfo -replace ' .*', '')

    # Check if rigel is running
    $rigelRunning = Get-Process -Name $minerExe -ErrorAction SilentlyContinue

    # If GPU busy but rigel NOT running -> user app is using GPU
    $userAppOnGPU = ($gpuUtil -gt $threshold) -and (-not $rigelRunning)

    # If rigel running but GPU near idle -> rigel failed, restart
    $rigelIdle = $rigelRunning -and ($gpuUtil -lt 5) -and $miningActive

    if ($miningActive) {
        if ($userAppOnGPU) {
            # User opened a heavy app - stop mining
            Stop-Process -Name $minerExe -Force -ErrorAction SilentlyContinue
            $miningActive = $false
            Write-Host "$(Get-Date) Paused: user app detected (GPU:$gpuUtil%)"
        }
    } else {
        # Mining is paused, check if we can resume
        if (-not $userAppOnGPU -and $gpuUtil -lt 5) {
            # GPU idle - resume mining
            $args = "-a octopus -o stratum+tcp://cfx.f2pool.com:6800 -u sydrro.5070ti --proxy 192.168.3.8:17890 --api-bind 0.0.0.0:5002 --log-file logs/miner.log --no-tui"
            Start-Process -FilePath "$minerPath\rigel.exe" -ArgumentList $args -WorkingDirectory $minerPath -WindowStyle Hidden
            $miningActive = $true
            Write-Host "$(Get-Date) Resumed: GPU idle ($gpuUtil%)"
        }
    }

    Start-Sleep $checkInterval
}
'''

sftp = ssh.open_sftp()
f = sftp.open(base + '/watchdog.ps1', 'w')
f.write(watchdog_ps1)
f.close()
sftp.close()

# Start watchdog in background via scheduled task
ssh.exec_command('schtasks /delete /tn MinerWatchdog002 /f 2>nul')
time.sleep(1)

wd_path = base + '\\watchdog.ps1'
# OpenSSH path might differ, find powershell
ps_path = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe'
task = f'schtasks /create /tn MinerWatchdog002 /tr "{ps_path} -WindowStyle Hidden -File \\"{wd_path}\\"" /sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
stdin, stdout, stderr = ssh.exec_command(task)
print('Task:', stdout.read().decode('gbk', errors='replace'), stderr.read().decode('gbk', errors='replace'))

# Start now
ssh.exec_command('schtasks /run /tn MinerWatchdog002')
time.sleep(2)

print('Watchdog started!')
print('Logic: GPU>20% by non-rigel app -> pause mining')
print('       GPU<5% idle -> resume mining')
print('Check interval: 10s')

ssh.close()
