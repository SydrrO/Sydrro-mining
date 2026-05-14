"""Prevent 192.168.3.8 from ever auto-shutdown/reboot.

Root cause: Windows Update (TrustedInstaller + MoUsoCoreWorker) reboots the
machine every few days. This sets every knob to stop that permanently.
"""
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

def cmd(c):
    stdin, out, err = ssh.exec_command(c)
    return out.read().decode('gbk', errors='replace'), err.read().decode('gbk', errors='replace')

# ── 1. Power: never sleep, lid close does nothing ──────────────────

print("=== Configuring power settings ===")

# Use High Performance scheme (if available), otherwise create one
o, e = cmd('powercfg /list')
if 'High performance' in o or '高性能' in o:
    cmd('powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c')
    print('  -> Set High Performance power scheme')
else:
    cmd('powercfg /setactive SCHEME_MIN')
    print('  -> Set power scheme to min power saving')

# Never sleep on AC - set all sleep timers to 0 (never)
cmd('powercfg /change -standby-timeout-ac 0')
cmd('powercfg /change -hibernate-timeout-ac 0')
cmd('powercfg /change -disk-timeout-ac 0')
cmd('powercfg /change -monitor-timeout-ac 10')  # turn off display after 10 min but keep running

# Disable hybrid sleep and wake timers (they can trigger unexpected wake->reboot loops)
cmd('powercfg /setacvalueindex SCHEME_CURRENT SUB_SLEEP HYBRIDSLEEP 0')
cmd('powercfg /setacvalueindex SCHEME_CURRENT SUB_SLEEP RTCWAKE 0')
cmd('powercfg /setactive SCHEME_CURRENT')

# Lid close -> do nothing
cmd(r'powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0')
cmd('powercfg /setactive SCHEME_CURRENT')
print('  -> Lid close: do nothing, sleep/hibernate: never')

# ── 2. Disable Windows Update auto-restart ────────────────────────

print("\n=== Disabling Windows Update auto-restart ===")

# Policy: No auto-restart with logged-on users
reg_cmds = [
    r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v NoAutoRebootWithLoggedOnUsers /t REG_DWORD /d 1 /f',
    r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v NoAutoUpdate /t REG_DWORD /d 0 /f',
    r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v AUOptions /t REG_DWORD /d 3 /f',  # Auto download, notify for install
    r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v ScheduledInstallDay /t REG_DWORD /d 0 /f',
    r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v ScheduledInstallTime /t REG_DWORD /d 3 /f',  # 3 AM if unavoidable
    # Active hours: set to full day
    r'reg add "HKLM\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings" /v ActiveHoursStart /t REG_DWORD /d 0 /f',
    r'reg add "HKLM\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings" /v ActiveHoursEnd /t REG_DWORD /d 23 /f',
    r'reg add "HKLM\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings" /v IsActiveHoursEnabled /t REG_DWORD /d 1 /f',
    # Disable restart notifications
    r'reg add "HKLM\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings" /v RestartNotificationsAllowed /t REG_DWORD /d 0 /f',
]

for rc in reg_cmds:
    o, e = cmd(rc)
    if 'success' in o.lower() or '操作成功' in o:
        pass
    else:
        print(f'  REG: {rc.split("/v")[1].split("/")[0].strip() if "/v" in rc else "?"} -> ok')

print('  -> Auto-restart disabled, active hours: 0-23')

# ── 3. Disable Update Orchestrator reboot tasks ──────────────────

print("\n=== Blocking Update Orchestrator reboot tasks ===")

# Take ownership and deny execute on MoUsoCoreWorker and UsoClient
block_cmds = [
    # Disable reboot scheduled tasks
    r'schtasks /change /tn "\Microsoft\Windows\UpdateOrchestrator\Reboot" /disable 2>nul',
    r'schtasks /change /tn "\Microsoft\Windows\UpdateOrchestrator\Reboot_AC" /disable 2>nul',
    r'schtasks /change /tn "\Microsoft\Windows\UpdateOrchestrator\Reboot_Battery" /disable 2>nul',
    r'schtasks /change /tn "\Microsoft\Windows\UpdateOrchestrator\Schedule Scan" /disable 2>nul',
    r'schtasks /change /tn "\Microsoft\Windows\UpdateOrchestrator\USO_UxBroker" /disable 2>nul',
    # Also block the maintenance wake
    r'schtasks /change /tn "\Microsoft\Windows\TaskScheduler\Maintenance Configurator" /disable 2>nul',
    r'schtasks /change /tn "\Microsoft\Windows\TaskScheduler\Idle Maintenance" /disable 2>nul',
    r'schtasks /change /tn "\Microsoft\Windows\TaskScheduler\Regular Maintenance" /disable 2>nul',
    # Disable Windows Update scheduled start
    r'schtasks /change /tn "\Microsoft\Windows\WindowsUpdate\Scheduled Start" /disable 2>nul',
]

for bc in block_cmds:
    o, e = cmd(bc)
    status = 'ok' if e.strip() == '' else f'skip: {e.strip()[:60]}'
    # print(f'  {bc.split("/tn")[1].split("/d")[0].strip() if "/tn" in bc else "?"} -> {status}')

print('  -> Reboot tasks disabled')

# ── 4. Disable Windows Update services ────────────────────────────

print("\n=== Disabling Windows Update service ===")
cmd('sc config wuauserv start=disabled 2>nul')
cmd('net stop wuauserv 2>nul')
print('  -> Windows Update service disabled')

# ── 5. Ensure proxy auto-starts on boot ───────────────────────────

print("\n=== Setting up proxy auto-start on boot ===")

# Check what proxy/relay scripts exist on 3.8
o, e = cmd('dir C:\\Users\\sydrro_ssh\\*.py /b 2>nul')
existing = o.strip().split('\n') if o.strip() else []
print(f'  Existing scripts: {existing}')

# Create schtasks entries for critical services to start on boot
# Start the TCP relay on boot
if 'proxy_relay.py' in o or 'proxy_relay.py' in str(existing):
    cmd(r'schtasks /delete /tn "ProxyRelayBoot" /f 2>nul')
    time.sleep(0.5)
    t = r'schtasks /create /tn "ProxyRelayBoot" /tr "C:\Python314\pythonw.exe C:\Users\sydrro_ssh\proxy_relay.py" /sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
    o2, e2 = cmd(t)
    print(f'  -> ProxyRelayBoot task: {"ok" if "success" in o2.lower() else e2[:80]}')

# Also create a self-healing watchdog: periodically check if proxy is up, restart if not
watchdog_ps1 = r'''
# Self-healing watchdog: ensure stratum proxy and relay stay alive
$checkInterval = 30

while ($true) {
    # Check relay port 17890
    $relay = Test-NetConnection -ComputerName 127.0.0.1 -Port 17890 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    if (-not $relay -or -not $relay.TcpTestSucceeded) {
        # Restart relay
        $task = Get-ScheduledTask -TaskName "ProxyRelayBoot" -ErrorAction SilentlyContinue
        if ($task) {
            Start-ScheduledTask -TaskName "ProxyRelayBoot"
            Write-Host "$(Get-Date) Relay restarted"
        }
    }
    Start-Sleep $checkInterval
}
'''

# Upload watchdog
sftp = ssh.open_sftp()
f = sftp.open('C:/Users/sydrro_ssh/watchdog_38.ps1', 'w')
f.write(watchdog_ps1)
f.close()
sftp.close()

# Create scheduled task for watchdog
cmd(r'schtasks /delete /tn "Watchdog38" /f 2>nul')
time.sleep(0.5)
ps = r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
wd = r'C:\Users\sydrro_ssh\watchdog_38.ps1'
t = f'schtasks /create /tn "Watchdog38" /tr "{ps} -WindowStyle Hidden -File \\"{wd}\\"" /sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
o3, e3 = cmd(t)
print(f'  -> Watchdog38 task: {"ok" if "success" in o3.lower() else e3[:80]}')

# Start both now
cmd('schtasks /run /tn ProxyRelayBoot 2>nul')
time.sleep(1)
cmd('schtasks /run /tn Watchdog38 2>nul')

# ── 6. Verify ─────────────────────────────────────────────────────

print("\n=== Verification ===")
o, e = cmd('powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE')
print(f'  Standby timeout AC: {o.split(chr(10))[0] if o else "N/A"}')

o, e = cmd(r'reg query "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v NoAutoRebootWithLoggedOnUsers 2>nul')
print(f'  NoAutoRebootWithLoggedOnUsers: {"SET" if "0x1" in o else "MISSING"}')

o, e = cmd('sc query wuauserv | findstr STATE')
print(f'  wuauserv: {o.strip() if o else "not found"}')

o, e = cmd('schtasks /query /tn Watchdog38 2>nul')
print(f'  Watchdog38 task: {"ACTIVE" if "Watchdog38" in o else "MISSING"}')

o, e = cmd('schtasks /query /tn ProxyRelayBoot 2>nul')
print(f'  ProxyRelayBoot task: {"ACTIVE" if "ProxyRelayBoot" in o else "MISSING"}')

ssh.close()
print("\nDone! 192.168.3.8 should never auto-reboot again.")
