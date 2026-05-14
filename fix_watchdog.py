import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)

base = r'D:\Donwlaods\rigel-1.23.1-win'

# Build watchdog script line by line
lines = []
lines.append('$miner = "rigel.exe"')
lines.append('$path = "D:\\Donwlaods\\rigel-1.23.1-win"')
lines.append('$checkInterval = 15')
lines.append('$paused = $false')
lines.append('')
lines.append('while($true) {')
lines.append('    $rigel = Get-Process $miner -ErrorAction SilentlyContinue')
lines.append('    $gpu = nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>$null')
lines.append('    $gpuUtil = if($gpu) { [int]($gpu.Trim() -replace " .*","") } else { 0 }')
lines.append('')
lines.append('    # Check if non-rigel processes are using GPU')
lines.append('    $gpuProcs = nvidia-smi --query-compute-apps=process_name --format=csv,noheader 2>$null')
lines.append('    $otherOnGPU = $false')
lines.append('    if ($gpuProcs) {')
lines.append('        foreach ($p in $gpuProcs) {')
lines.append('            $pn = $p.Trim().ToLower()')
lines.append('            if ($pn -and $pn -ne $miner.ToLower()) {')
lines.append('                $otherOnGPU = $true')
lines.append('                break')
lines.append('            }')
lines.append('        }')
lines.append('    }')
lines.append('')
lines.append('    if (-not $paused) {')
lines.append('        if ($otherOnGPU) {')
lines.append('            Stop-Process $miner -Force -ErrorAction SilentlyContinue')
lines.append('            $paused = $true')
lines.append('        }')
lines.append('    } else {')
lines.append('        if (-not $otherOnGPU -and $gpuUtil -lt 10) {')
lines.append('            $args = "-a octopus -o stratum+tcp://cfx.f2pool.com:6800 -u sydrro.5070ti --proxy 192.168.3.8:17890 --api-bind 0.0.0.0:5002 --log-file logs/miner.log"')
lines.append('            Start-Process -FilePath "$path\\rigel.exe" -ArgumentList $args -WorkingDirectory $path -WindowStyle Hidden')
lines.append('            $paused = $false')
lines.append('        }')
lines.append('    }')
lines.append('    Start-Sleep $checkInterval')
lines.append('}')

content = '\r\n'.join(lines)

sftp = ssh.open_sftp()
f = sftp.open(base + '/watchdog.ps1', 'w')
f.write(content)
f.close()
sftp.close()

# Verify
stdin, stdout, stderr = ssh.exec_command('cmd /c "type ' + base + '\\watchdog.ps1"')
out = stdout.read().decode('gbk', errors='replace')
print('Lines written:', len(out.split('\n')))

# Restart task
ssh.exec_command('schtasks /end /tn MinerWatchdog002 /f 2>nul')
time.sleep(1)
ssh.exec_command('schtasks /run /tn MinerWatchdog002')

print('Watchdog deployed and running!')
ssh.close()
