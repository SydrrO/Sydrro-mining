import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.8', username='sydrro_ssh', password='061021', timeout=10)

# Write proxy relay script to 3.8
relay = r'''import socket, threading

SRC = ('0.0.0.0', 17890)
DST = ('127.0.0.1', 7892)

def relay(client, addr):
    try:
        backend = socket.socket(); backend.settimeout(30)
        backend.connect(DST)
        def pipe(a, b):
            while True:
                d = a.recv(4096)
                if not d: break
                b.sendall(d)
        t1 = threading.Thread(target=pipe, args=(client, backend), daemon=True)
        t2 = threading.Thread(target=pipe, args=(backend, client), daemon=True)
        t1.start(); t2.start()
        t1.join(); t2.join()
    except: pass
    finally:
        try: client.close()
        except: pass
        try: backend.close()
        except: pass

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(SRC); s.listen(50)
while True:
    c, a = s.accept()
    threading.Thread(target=relay, args=(c, a), daemon=True).start()
'''

sftp = ssh.open_sftp()
f = sftp.open('C:/Users/sydrro_ssh/proxy_relay.py', 'w')
f.write(relay)
f.close()
sftp.close()

# Start relay in background
ssh.exec_command('pythonw C:\\Users\\sydrro_ssh\\proxy_relay.py')
time.sleep(3)

# Test from local machine
import socket
s = socket.socket()
s.settimeout(3)
try:
    s.connect(('192.168.3.8', 17890))
    print('Port 17890 OPEN on 3.8 - relay working!')
    s.close()
except Exception as e:
    print(f'Port 17890 CLOSED: {e}')

ssh.close()
