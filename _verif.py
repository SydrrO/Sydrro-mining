import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

def run(cmd):
    stdin, out, err = ssh.exec_command(cmd)
    return out.read().decode('gbk', errors='replace') + err.read().decode('gbk', errors='replace')

# Test stratum handshake - connect and recv
code = r"""import socket
s = socket.socket(); s.settimeout(10)
s.connect(('202.173.11.130', 6800))
# Send stratum subscribe
s.sendall(b'{"id":1,"method":"mining.subscribe","params":["rigel/1.23.1"]}\n')
data = s.recv(4096)
print('RECV:', data[:500])
# Also see if pool sends greeting first
# Try again without sending
s2 = socket.socket(); s2.settimeout(10)
s2.connect(('202.173.11.130', 6800))
import time; time.sleep(2)
try:
    greeting = s2.recv(4096)
    print('GREETING:', greeting[:500])
except:
    print('No greeting (waiting for client to send first)')
s2.close()
s.close()
"""
py = r'C:\Users\sydrro_ssh\Desktop\miner308\python312\python.exe'
o = run(py + ' -c "' + code + '"')
print(o[:1000])

# Also test if the proxy is actually forwarding correctly
print('\n=== Proxy forward test ===')
code2 = r"""import socket
s = socket.socket(); s.settimeout(10)
s.connect(('127.0.0.1', 16900))
s.sendall(b'{"id":1,"method":"mining.subscribe","params":["rigel/1.23.1"]}\n')
import time; time.sleep(3)
s.settimeout(5)
try:
    data = s.recv(4096)
    print('PROXY RECV:', data[:500])
except Exception as e:
    print('PROXY: no response -', e)
s.close()
"""
o2 = run(py + ' -c "' + code2 + '"')
print(o2[:500])

ssh.close()
