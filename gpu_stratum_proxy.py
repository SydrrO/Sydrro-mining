import socket, threading

LOCAL_HOST = "0.0.0.0"
LOCAL_PORT = 16900
REMOTE_HOST = "172.65.190.98"  # cfx.f2pool.com
REMOTE_PORT = 6800

def pipe(src, dst):
    try:
        while True:
            data = src.recv(65536)
            if not data: break
            dst.sendall(data)
    except: pass

def handle(client_sock, addr):
    remote = None
    try:
        remote = socket.socket(); remote.settimeout(10)
        remote.connect((REMOTE_HOST, REMOTE_PORT))
        remote.settimeout(None); client_sock.settimeout(None)
        print(f"[gpu-proxy] {addr[0]}:{addr[1]} -> {REMOTE_HOST}:{REMOTE_PORT}")
        t1 = threading.Thread(target=pipe, args=(client_sock, remote), daemon=True)
        t2 = threading.Thread(target=pipe, args=(remote, client_sock), daemon=True)
        t1.start(); t2.start()
        t1.join(); t2.join()
    except Exception as e:
        print(f"[gpu-proxy] error: {e}")
    finally:
        try: client_sock.close()
        except: pass
        if remote:
            try: remote.close()
            except: pass

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((LOCAL_HOST, LOCAL_PORT)); s.listen(50)
print(f"[gpu-proxy] {LOCAL_HOST}:{LOCAL_PORT} -> {REMOTE_HOST}:{REMOTE_PORT}")
while True:
    try:
        c, a = s.accept()
        threading.Thread(target=handle, args=(c, a), daemon=True).start()
    except KeyboardInterrupt: break
s.close()
