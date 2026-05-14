"""Check all tunnels and proxy routing on 3.8."""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

def run(cmd, timeout=10):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('gbk', errors='replace').strip()
    err = stderr.read().decode('gbk', errors='replace').strip()
    return out, err

# Check frp config
print("="*50)
print("FRP CONFIG")
out, err = run('type C:\\Users\\sydrro_ssh\\frpc.ini 2>nul')
print(out[:1500] if out else 'NOT FOUND')
if err: print(f'err: {err[:200]}')

# Check natapp config
print("\n" + "="*50)
print("NATAPP CONFIG")
out, err = run('type C:\\Users\\sydrro_ssh\\natapp_config.ini 2>nul')
print(out[:500] if out else 'NOT FOUND')

out, err = run('type C:\\Users\\sydrro_ssh\\config.ini 2>nul')
print(f'config.ini: {out[:500] if out else "NOT FOUND"}')

# Check SSH tunnel config
print("\n" + "="*50)
print("SSH TUNNEL TASK")
out, err = run('schtasks /query /tn SshTunnel /fo csv /v 2>nul')
print(out[:500])

# Check NatappTunnel task
print("\nNATAPP TUNNEL TASK")
out, err = run('schtasks /query /tn NatappTunnel /fo csv /v 2>nul')
print(out[:500])

# Check FrpTunnel task
print("\nFRP TUNNEL TASK")
out, err = run('schtasks /query /tn FrpTunnel /fo csv /v 2>nul')
print(out[:500])

# Check if there's a SOCKS proxy or HTTP proxy running
print("\n" + "="*50)
print("PROXY PORTS CHECK")
for port in ['1080', '10808', '7890', '7891', '8118', '9053', '10000']:
    out, err = run(f'netstat -ano 2>nul | findstr LISTENING | findstr ":{port}"')
    if out:
        print(f'Port {port}: {out[:200]}')

# Check current proxy_fixed.py - does it use a proxy?
print("\n" + "="*50)
print("CURRENT PROXY SCRIPT")
out, err = run('type C:\\Users\\sydrro_ssh\\Desktop\\proxy_fixed.py 2>nul')
print(out[:1000])

# Check old stratum_proxy config
print("\n" + "="*50)
print("GPU PROXY CONFIG")
out, err = run('type C:\\Users\\sydrro_ssh\\gpu_stratum_proxy.py 2>nul | findstr /v "^$"')
print(out[:1000])

# Check natapp tunnels - what ports are forwarded
print("\n" + "="*50)
print("NATAPP PROCESS INFO")
out, err = run('wmic process where "name=\'natapp.exe\'" get ProcessId,CommandLine /format:csv 2>nul')
print(out[:500])

# Check frpc process info
print("\n" + "="*50)
print("FRPC PROCESS INFO")
out, err = run('wmic process where "name=\'frpc.exe\'" get ProcessId,CommandLine /format:csv 2>nul')
print(out[:500])

# Check if there's a FlClash or clash running
out, err = run('tasklist 2>nul | findstr /i "clash flclash v2ray xray hysteria sing"')
print(f'\nVPN/Proxy tools: {out if out else "NONE"}')

# Check listening on 127.0.0.1 ports (local proxies)
print("\n" + "="*50)
print("LOCALHOST LISTENING PORTS")
out, err = run('netstat -ano 2>nul | findstr "127.0.0.1" | findstr LISTENING')
print(out[:1000])

ssh.close()
