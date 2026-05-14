"""Check DNS and fix: use IP that works through Clash."""
import paramiko, time, base64, urllib.request, json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=15)

def run(cmd, timeout=10):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('gbk', errors='replace').strip()
    err = stderr.read().decode('gbk', errors='replace').strip()
    return out, err

# Quick DNS check for CFX
print("=== DNS test (quick) ===")
stdin, stdout, stderr = ssh.exec_command('C:\\Users\\sydrro_ssh\\Desktop\\miner308\\python312\\python.exe -c "import socket; print(socket.gethostbyname(\'cfx.f2pool.com\'))" 2>&1', timeout=10)
out = stdout.read().decode('gbk', errors='replace')
err = stderr.read().decode('gbk', errors='replace')
print(f'cfx.f2pool.com: {out.strip() or err.strip()[:200]}')

# The FUNDAMENTAL fix: use IP directly in proxy
# The GPU proxy connects to 172.65.190.98:6800 (Cloudflare) and it WORKS through Clash
# For LTC, we need the Cloudflare IP. Let me resolve ltc.f2pool.com from my side and use it

# From MY machine: ltc.f2pool.com -> 202.173.11.130 (direct origin IP)
# But from 3.8 via Clash, the Cloudflare IPs work. Let me check what IPs work

# Strategy: Try known-working f2pool IPs for port 3335
# 1. 172.65.249.114 - Cloudflare (was reachable before)
# 2. 202.173.11.130 - Origin (timed out before)
# 3. Find through Clash: test what IP the GPU proxy actually uses

print("\n=== What IP does GPU proxy use? ===")
out, err = run('netstat -ano 2>nul | findstr "35664" | findstr "ESTABLISHED"')
print(out[:500])

print("\n=== Test: connect to known Cloudflare IPs for LTC ===")
# Test TCP connectivity from 3.8
for ip, port in [('172.65.249.114', 3335), ('172.65.190.98', 3335)]:
    cmd = f'powershell -Command "Test-NetConnection -ComputerName {ip} -Port {port} -WarningAction SilentlyContinue | Select-Object TcpTestSucceeded,RemoteAddress"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    out = stdout.read().decode('gbk', errors='replace')
    print(f'{ip}:{port}: {out.strip()[:150]}')

# Let's try a totally different approach: use the GPU proxy's pattern
# GPU proxy works by connecting through Clash. The key insight from comment:
# "Use domain - FlClash will route correctly"
# This means Clash intercepts DNS and returns fake IPs, then proxies the connection
# So the DOMAIN NAME matters for Clash rules!

# Maybe "ltc.f2pool.com" simply isn't in Clash's rules.
# Let me check Clash config to see what domains are proxied

print("\n=== Clash config search ===")
for path in [
    'C:\\Users\\sydrro_ssh\\.config\\clash-verge',
    'C:\\Users\\sydrro_ssh\\AppData\\Roaming\\clash-verge',
    'C:\\Users\\sydrro_ssh\\AppData\\Local\\clash-verge',
]:
    out, err = run(f'dir /s /b "{path}\\*.yaml" "{path}\\*.yml" 2>nul | findstr /i "profile rule config"')
    if out:
        print(f'{path}:')
        for line in out.split('\n')[:5]:
            print(f'  {line.strip()[:150]}')

# Check for clash profile in common locations
out, err = run('dir /s /b C:\\Users\\sydrro_ssh\\.config 2>nul | findstr /i "clash"')
print(f'\n.config clash: {out[:300] if out else "NONE"}')

# Check all of C:\\Users\\sydrro_ssh for clash configs (limited depth)
out, err = run('powershell -Command "Get-ChildItem C:\\Users\\sydrro_ssh -Recurse -Depth 3 -Name clash*.yaml,clash*.yml,profile*.yaml -ErrorAction SilentlyContinue"')
print(f'\nClash yaml: {out[:500]}')

ssh.close()
