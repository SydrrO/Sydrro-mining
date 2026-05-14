import paramiko, time, base64, socket, json

# Efficient TCP relay using embedded C# via PowerShell Add-Type
# This runs in-process with proper async IO, much faster than netsh
relay_cs = '''
using System;
using System.Net;
using System.Net.Sockets;
using System.Threading;

public class TcpRelay {
    static void Pipe(NetworkStream from, NetworkStream to) {
        byte[] buf = new byte[65536];
        try { int n; while ((n = from.Read(buf, 0, buf.Length)) > 0) to.Write(buf, 0, n); }
        catch {}
    }
    public static void Start(int listenPort, string targetHost, int targetPort) {
        var listener = new TcpListener(IPAddress.Any, listenPort);
        listener.Start();
        while (true) {
            var client = listener.AcceptTcpClient();
            ThreadPool.QueueUserWorkItem(_ => {
                try {
                    var target = new TcpClient(targetHost, targetPort);
                    var t1 = new Thread(() => { Pipe(client.GetStream(), target.GetStream()); });
                    var t2 = new Thread(() => { Pipe(target.GetStream(), client.GetStream()); });
                    t1.Start(); t2.Start();
                    t1.Join(); t2.Join();
                    target.Close(); client.Close();
                } catch {}
            });
        }
    }
}
'''

# Base64 encode and send to 3.8
ps_b64 = base64.b64encode(relay_cs.encode('utf-8')).decode()

ssh38 = paramiko.SSHClient()
ssh38.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh38.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# Remove old netsh portproxy
ssh38.exec_command('netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=16800 2>nul')
time.sleep(1)

# Write relay script via base64
ps_script = '[System.IO.File]::WriteAllText("C:\\Users\\sydrro_ssh\\fast_relay.cs", [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("' + ps_b64 + '")))'
ssh38.exec_command('powershell -Command "' + ps_script + '"')
time.sleep(1)

# Start relay via scheduled task (runs continuously in background)
run_cmd = 'powershell -Command "Add-Type -Path C:\\Users\\sydrro_ssh\\fast_relay.cs; [TcpRelay]::Start(16800, \"cfx.f2pool.com\", 6800)"'

ssh38.exec_command('schtasks /delete /tn FastRelay38 /f 2>nul')
time.sleep(1)
task = 'schtasks /create /tn FastRelay38 /tr "' + run_cmd + '" /sc onstart /ru sydrro_ssh /rp 061021 /rl HIGHEST /f'
ssh38.exec_command(task)
time.sleep(1)
ssh38.exec_command('schtasks /run /tn FastRelay38')
time.sleep(8)
ssh38.close()

# Test relay
s = socket.socket(); s.settimeout(5)
try:
    s.connect(('192.168.3.8', 16800))
    print('Fast relay 16800: OPEN!')
    s.close()
except Exception as e:
    print(f'CLOSED: {e}')

# Monitor 002 for improvements
ssh002 = paramiko.SSHClient()
ssh002.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh002.connect('192.168.3.7', username='sydrro_ssh', password='061021', timeout=10)

# Current stats
stdin, stdout, stderr = ssh002.exec_command('curl -s http://127.0.0.1:5002')
d = json.loads(stdout.read().decode())
dev = d['devices'][0]['solution_stat']['octopus']
total = dev['accepted'] + dev['rejected']
rr = dev['rejected'] / total * 100 if total > 0 else 0
pool = d['pools']['octopus'][0]
print(f'Before: {d["hashrate"]["octopus"]/1e6:.0f} MH/s | {pool["average_latency_ms"]:.0f}ms | {dev["accepted"]}/{dev["rejected"]} ({rr:.1f}%)')
print('Waiting 30s for latency to update...')

# Wait and recheck
time.sleep(30)
stdin, stdout, stderr = ssh002.exec_command('curl -s http://127.0.0.1:5002')
d2 = json.loads(stdout.read().decode())
pool2 = d2['pools']['octopus'][0]
dev2 = d2['devices'][0]['solution_stat']['octopus']
total2 = dev2['accepted'] + dev2['rejected']
rr2 = dev2['rejected'] / total2 * 100 if total2 > 0 else 0
print(f'After:  {d2["hashrate"]["octopus"]/1e6:.0f} MH/s | {pool2["average_latency_ms"]:.0f}ms | {dev2["accepted"]}/{dev2["rejected"]} ({rr2:.1f}%)')

ssh002.close()
print('\nDone!')
