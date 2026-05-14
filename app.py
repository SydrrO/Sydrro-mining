#!/usr/bin/env python3
"""Mining Dashboard v3 — unified monitoring with syslog, structured APIs."""

import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from requests.auth import HTTPDigestAuth
from flask import Flask, g, jsonify, render_template, request

from config import load as load_config, create_default
from monitor_miner import parse_status, parse_system, num, ghs
from syslog import get_syslog

# ---- Init ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    _cfg = load_config()
except Exception:
    create_default()
    _cfg = load_config()

_asic = _cfg["asic"]
BASE_URL = f"http://{_asic['ip']}"
USER = _asic["user"]
PWD = _asic["password"]

_db_cfg = _cfg.get("database", {})
DB_PATH = os.path.join(BASE_DIR, _db_cfg.get("path", "miner_data.db"))

GPU_MINERS = _cfg.get("gpu_miners", [])

app = Flask(__name__)
_syslog = get_syslog(_cfg.get("syslog", {}))

# ---- Database ----
_db_lock = threading.Lock()
_local = threading.local()


def get_db():
    db = getattr(_local, "db", None)
    if db is None:
        db = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA busy_timeout=5000")
        _local.db = db
    return db


@app.teardown_appcontext
def close_db(exception):
    db = getattr(_local, "db", None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass
        _local.db = None


def init_db():
    with _db_lock:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS miner_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    ghs5s REAL, ghsav REAL,
                    temp1 REAL, temp2 REAL,
                    hw_total INTEGER,
                    fan2 TEXT, fan3 TEXT,
                    elapsed TEXT,
                    accepted INTEGER, rejected INTEGER
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ts ON miner_status(timestamp)")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS gpu_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    idx INTEGER,
                    mhs REAL, temp INTEGER, power REAL, fan INTEGER,
                    acc INTEGER, rej INTEGER, eff REAL, latency_ms REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_gpu_ts ON gpu_log(timestamp)")


def cleanup_old_data():
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    with _db_lock:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM miner_status WHERE timestamp < ?", (cutoff,))
            conn.execute("DELETE FROM gpu_log WHERE timestamp < ?", (cutoff,))
            conn.commit()
            conn.execute("VACUUM")


# ---- GPU helpers ----
def _gpu_get(idx):
    if idx >= len(GPU_MINERS):
        return {"success": False, "error": "not configured"}
    g = GPU_MINERS[idx]
    host = g["host"]
    agent_port = g.get("port", 5002)
    rigel_port = g.get("rigel_port", 5000)

    # Try GPU agent first
    try:
        r = requests.get(f"http://{host}:{agent_port}/status", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("success"):
                data["host"] = host
                data["gpu_name"] = g.get("name", f"GPU #{idx+1}")
                return data
    except Exception:
        pass

    # Fallback: Rigel API directly
    try:
        r = requests.get(f"http://{host}:{rigel_port}", timeout=8)
        if r.status_code == 200:
            data = r.json()
            data["success"] = True
            data["host"] = host
            data["gpu_name"] = g.get("name", f"GPU #{idx+1}")
            return data
    except Exception:
        pass

    return {"success": False, "error": f"{host} unreachable", "host": host}


def _gpu_action(idx, action):
    if idx >= len(GPU_MINERS):
        return {"success": False, "error": "not configured"}
    g = GPU_MINERS[idx]
    host = g["host"]
    agent_port = g.get("port", 5002)

    # Try GPU agent first
    try:
        r = requests.post(f"http://{host}:{agent_port}/{action}", timeout=8)
        if r.status_code == 200:
            result = r.json()
            _syslog.info("system", f"GPU{idx+1} {action}: {result.get('message', 'ok')}")
            return result
    except Exception:
        pass

    # Fallback: remote schtasks
    ssh_user = g.get("ssh_user", "")
    ssh_pwd = g.get("ssh_password", "")
    task_name = g.get("task_name", "RigelMiner")

    if ssh_user:
        try:
            if action == "start":
                cmd = f'schtasks /run /s {host} /u {ssh_user} /p {ssh_pwd} /tn "{task_name}"'
            else:
                cmd = f'schtasks /end /s {host} /u {ssh_user} /p {ssh_pwd} /tn "{task_name}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=15)
            ok = result.returncode == 0
            msg = f"GPU{idx+1} {action} via schtasks: {'ok' if ok else 'failed'}"
            _syslog.info("system", msg)
            return {"success": ok, "message": msg}
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "no control method available"}


# ---- Routes ----
@app.route("/")
def index():
    auth = HTTPDigestAuth(USER, PWD)
    sys_info = None
    try:
        r = requests.get(f"{BASE_URL}/cgi-bin/get_system_infoV1.cgi", auth=auth, timeout=5)
        sys_info = parse_system(r.text)
    except Exception:
        pass
    return render_template("index.html", sys_info=sys_info)


@app.route("/api/status")
def api_status():
    auth = HTTPDigestAuth(USER, PWD)
    try:
        r = requests.get(f"{BASE_URL}/cgi-bin/get_miner_statusV1.cgi", auth=auth, timeout=5)
        data = parse_status(r.text)
    except Exception:
        _syslog.warn("network", "ASIC miner unreachable", f"host={_asic['ip']}")
        return jsonify({"error": "miner offline"}), 502

    if not data:
        return jsonify({"error": "parse failed"}), 502

    ghs5s = num(data.get("ghs5s", "0"))
    ghsav = num(data.get("ghsav", "0"))
    elapsed = data.get("elapsed", "?")

    chains = data.get("chains", [])
    t1 = num(chains[0].get("temp", 0)) if isinstance(chains, list) and len(chains) > 0 else None
    t2 = num(chains[1].get("temp", 0)) if isinstance(chains, list) and len(chains) > 1 else None
    hw_total = sum(int(num(c.get("hw", 0))) for c in chains) if isinstance(chains, list) else 0

    fan = data.get("fan", {})
    fan2 = str(fan.get("fan2", "")) if isinstance(fan, dict) else ""
    fan3 = str(fan.get("fan3", "")) if isinstance(fan, dict) else ""

    pools = data.get("pool_dtls", [])
    if isinstance(pools, str):
        try:
            pools = json.loads(pools)
        except Exception:
            pools = []
    pool_alive = next((p for p in pools if p.get("status") == "Alive"), None)
    accepted = int(num(pool_alive.get("accepted", 0))) if pool_alive else 0
    rejected = int(num(pool_alive.get("rejected", 0))) if pool_alive else 0

    now = datetime.now().isoformat()

    try:
        db = get_db()
        with _db_lock:
            db.execute("""
                INSERT INTO miner_status (timestamp, ghs5s, ghsav, temp1, temp2, hw_total, fan2, fan3, elapsed, accepted, rejected)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, ghs5s, ghsav, t1, t2, hw_total, fan2, fan3, elapsed, accepted, rejected))
            db.commit()
    except Exception:
        pass

    # Syslog checks
    if ghsav < 100:
        _syslog.warn("hashrate", "ASIC hashrate very low", f"{ghsav:.0f} GH/s")
    if hw_total > 0 and elapsed and "m" in elapsed:
        _syslog.info("hardware", f"ASIC HW errors: {hw_total}", f"uptime={elapsed}")

    return jsonify({
        "timestamp": now,
        "ghs5s": ghs5s, "ghsav": ghsav,
        "ghs5s_display": ghs(ghs5s), "ghsav_display": ghs(ghsav),
        "temp1": t1, "temp2": t2, "hw_total": hw_total,
        "fan2": fan2, "fan3": fan3, "elapsed": elapsed,
        "accepted": accepted, "rejected": rejected,
    })


@app.route("/api/gpu/status")
def api_gpu_status():
    results = []
    for i in range(len(GPU_MINERS)):
        g = _gpu_get(i)
        results.append(g)

        if not g.get("success"):
            _syslog.warn("network", f"GPU{i+1} unreachable",
                         f"host={GPU_MINERS[i]['host']}")

    return jsonify(results)


@app.route("/api/gpu/start/<int:idx>", methods=["POST"])
def api_gpu_start(idx):
    return jsonify(_gpu_action(idx, "start"))


@app.route("/api/gpu/stop/<int:idx>", methods=["POST"])
def api_gpu_stop(idx):
    return jsonify(_gpu_action(idx, "stop"))


@app.route("/api/history")
def api_history():
    hours = request.args.get("hours", 0.5, type=float)
    cap = min(hours, 720)
    since = (datetime.now() - timedelta(hours=cap)).isoformat()

    db = get_db()
    rows = db.execute(
        "SELECT * FROM miner_status WHERE timestamp >= ? ORDER BY id ASC",
        (since,)
    ).fetchall()

    total = len(rows)
    MAX_POINTS = 2000
    if total > MAX_POINTS:
        step = total // MAX_POINTS
        rows = rows[::step]

    data = [{
        "timestamp": r["timestamp"],
        "ghs5s": r["ghs5s"], "ghsav": r["ghsav"],
        "temp1": r["temp1"], "temp2": r["temp2"],
        "hw_total": r["hw_total"],
        "fan2": r["fan2"], "fan3": r["fan3"],
        "elapsed": r["elapsed"],
        "accepted": r["accepted"], "rejected": r["rejected"],
    } for r in rows]

    return jsonify({"data": data, "total": total, "hours": cap})


@app.route("/api/syslog")
def api_syslog():
    try:
        timeline = _syslog.get_timeline(60)
        summary = _syslog.get_summary()
        return jsonify({"timeline": timeline, "summary": summary})
    except Exception as e:
        return jsonify({"timeline": [], "summary": {}, "error": str(e)})


@app.route("/api/health")
def api_health():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT COUNT(*) as cnt, MAX(timestamp) as last_ts, AVG(ghsav) as avg_hash FROM miner_status"
        ).fetchone()
        db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
        conn.close()
        return jsonify({
            "status": "ok",
            "db_records": row["cnt"],
            "db_size_mb": round(db_size / 1048576, 2),
            "last_record": row["last_ts"],
            "avg_ghsav": round(row["avg_hash"] or 0, 2),
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


# ---- GPU data collector ----
def gpu_collector_loop():
    """Periodically collect GPU data into gpu_log."""
    while True:
        for i in range(len(GPU_MINERS)):
            try:
                g = _gpu_get(i)
                if not g.get("success"):
                    continue

                dev = (g.get("devices") or [{}])[0] or {}
                hr = dev.get("hashrate", {})
                alg = list(hr.keys())[0] if hr else ""
                mhs = hr.get(alg, 0) / 1e6 if alg else 0
                mon = dev.get("monitoring_info", {})
                sol = (g.get("solution_stat") or {}).get(alg, {})

                pools = g.get("pools", {})
                pool_list = pools.get(alg, [])
                latency = pool_list[0].get("average_latency_ms") if pool_list else None

                with _db_lock:
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("""
                        INSERT INTO gpu_log (timestamp, idx, mhs, temp, power, fan, acc, rej, eff, latency_ms)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        datetime.now().isoformat(), i, round(mhs, 2),
                        mon.get("core_temperature"),
                        mon.get("power_usage"),
                        mon.get("fan_speed"),
                        sol.get("accepted", 0), sol.get("rejected", 0),
                        round(mhs / mon.get("power_usage", 1) * 1000, 1) if mon.get("power_usage", 0) > 0 else 0,
                        latency
                    ))
                    conn.commit()
                    conn.close()

                # Syslog checks
                if latency and latency > 500:
                    _syslog.warn("pool", f"GPU{i+1} high latency: {latency:.0f}ms")
                if g.get("miner_running") is False and dev.get("state") != "mining":
                    pass  # normal during DAG gen
            except Exception:
                pass
        time.sleep(30)


# ---- Main ----
if __name__ == "__main__":
    init_db()
    cleanup_old_data()

    srv = _cfg.get("server", {})
    port = srv.get("port", 5000)
    host = srv.get("host", "0.0.0.0")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((_asic["ip"], 80))
        lan_ip = s.getsockname()[0]
        s.close()
    except Exception:
        lan_ip = "0.0.0.0"

    print("=" * 55)
    print("  Mining Dashboard v3")
    print(f"  Local:   http://localhost:{port}")
    print(f"  Network: http://{lan_ip}:{port}")
    for i, g in enumerate(GPU_MINERS):
        print(f"  GPU{i+1}: {g['host']} ({g.get('name', 'unknown')})")
    print(f"  SysLog:  {_syslog._log_path}")
    print("=" * 55)

    _syslog.info("system", "Dashboard starting", f"v3.0 port={port}")

    collector = threading.Thread(target=gpu_collector_loop, daemon=True)
    collector.start()

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        webbrowser.open(f"http://localhost:{port}")

    try:
        from waitress import serve
        print("Running with waitress")
        serve(app, host=host, port=port)
    except ImportError:
        print("WARNING: waitress not installed")
        app.run(host=host, port=port, debug=False)
