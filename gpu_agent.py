"""GPU Agent v2 — standardized HTTP API for any GPU miner.

Runs on every GPU miner machine. Provides:
  GET  /status    — GPU info + miner status + hashrate from Rigel API
  GET  /health    — liveness check
  POST /start     — start miner via scheduled task
  POST /stop      — stop miner via taskkill

Uses Rigel API (port 5000) as primary data source for hashrate/shares/latency.
Falls back to nvidia-smi for GPU hardware info.
"""

import json
import os
import re
import subprocess
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from urllib.request import urlopen, Request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 5002
RIGEL_API = f"http://127.0.0.1:5000"


def run(cmd, timeout=8):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout)
        out = p.stdout + p.stderr
        for enc in ['gbk', 'utf-8', 'latin-1']:
            try:
                return out.decode(enc)
            except Exception:
                continue
        return str(out[:1000])
    except Exception as e:
        return f"Error: {e}"


def get_gpu_info():
    """Get GPU hardware info via nvidia-smi."""
    smi = run(
        'C:\\Windows\\System32\\nvidia-smi.exe '
        '--query-gpu=name,temperature.gpu,utilization.gpu,'
        'clocks.sm,clocks.mem,power.draw,power.limit,fan.speed '
        '--format=csv,noheader'
    )
    if not smi.strip() or "Error" in smi:
        return {}
    parts = [p.strip() for p in smi.strip().split(',')]
    if len(parts) < 8:
        return {}
    return {
        "name": parts[0],
        "temp": int(parts[1]),
        "util": int(parts[2].replace('%', '')),
        "core_mhz": int(parts[3].replace('MHz', '').strip()),
        "mem_mhz": int(parts[4].replace('MHz', '').strip()),
        "power_w": float(parts[5].replace('W', '').strip()),
        "power_limit_w": float(parts[6].replace('W', '').strip()),
        "fan_pct": int(parts[7].replace('%', '').strip()),
    }


def get_rigel_status():
    """Query Rigel miner API for detailed status."""
    try:
        req = Request(RIGEL_API, headers={"User-Agent": "GpuAgent/2.0"})
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def get_status():
    """Build comprehensive status response."""
    result = {
        "success": False,
        "miner_running": False,
        "hostname": os.environ.get("COMPUTERNAME", "unknown"),
    }

    # Check if rigel process exists
    proc = run('tasklist /FI "IMAGENAME eq rigel.exe" 2>&1')
    result["miner_running"] = "rigel.exe" in proc.lower()

    # Try Rigel API first (richest data)
    rigel = get_rigel_status()
    if rigel:
        result.update(rigel)
        result["success"] = True
        result["source"] = "rigel_api"
        return result

    # Fallback: nvidia-smi only
    gpu = get_gpu_info()
    if gpu:
        result["gpu"] = gpu
        result["success"] = True
        result["source"] = "nvidia-smi"
    else:
        result["error"] = "No GPU detected"

    return result


def start_miner():
    try:
        s = get_status()
        if s.get("miner_running"):
            return {"success": True, "message": "Miner already running"}
        run('schtasks /run /tn "RigelMiner"', timeout=5)
        return {"success": True, "message": "Miner scheduled task started"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def stop_miner():
    try:
        run('taskkill /F /IM rigel.exe 2>&1', timeout=5)
        run('schtasks /end /tn "RigelMiner" 2>&1', timeout=5)
        return {"success": True, "message": "Miner stopped"}
    except Exception as e:
        return {"success": False, "error": str(e)}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/status':
            self._send(get_status())
        elif path == '/health':
            self._send({"status": "ok"})
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == '/start':
            self._send(start_miner())
        elif path == '/stop':
            self._send(stop_miner())
        else:
            self._send({"error": "not found"}, 404)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        print(json.dumps(get_status(), indent=2, ensure_ascii=False))
    else:
        print(f"GPU Agent v2 on port {PORT}")
        print(f"  Miner API: {RIGEL_API}")
        HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
