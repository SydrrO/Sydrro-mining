#!/usr/bin/env python3
"""Unified GPU Miner Deployment — standardized setup for any Windows GPU miner.

Usage:
  python deploy_gpu.py                    # deploy all GPUs from config.json
  python deploy_gpu.py --host 192.168.3.6 # deploy single GPU
  python deploy_gpu.py --dry-run          # show what would be done

Creates on each GPU miner:
  D:\\miner\\rigel.exe                 # miner binary
  D:\\miner\\gpu_agent.py             # monitoring agent (HTTP :5002)
  D:\\miner\\start_rigel.bat          # launch script
  Scheduled tasks: RigelMiner, GpuAgent
  Firewall rules: port 5000 (API), 5002 (agent)
"""

import json
import os
import subprocess
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
RIGEL_VERSION = "1.23.2"
RIGEL_URL = f"https://github.com/rigelminer/rigel/releases/download/{RIGEL_VERSION}/rigel-{RIGEL_VERSION}-win.zip"
RIGEL_MIRROR = f"https://ghproxy.com/{RIGEL_URL}"  # China mirror fallback

GPU_AGENT_TEMPLATE = os.path.join(BASE_DIR, "gpu_agent.py")

# ---- Default miner config ----
DEFAULT_CONFIG = {
    "algorithm": "octopus",
    "pool_url": "stratum+tcp://192.168.3.8:16900",
    "worker_template": "sydrro.{gpu_name}",
    "api_port": 5000,
    "agent_port": 5002,
    "max_power_w": None,  # auto-detect
    "core_offset": 0,
    "mem_offset": 0,
}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def deploy_gpu(host, ssh_user, ssh_password, gpu_config):
    """Deploy mining stack to a single GPU machine via SSH."""
    name = gpu_config.get("name", "unknown")
    algo = gpu_config.get("algorithm", "octopus")
    pool = gpu_config.get("pool_url", "stratum+tcp://192.168.3.8:16900")
    worker = gpu_config.get("worker_template", "sydrro.{gpu_name}").format(
        gpu_name=name.lower().replace(" ", "_").replace("#", "")
    )
    api_port = gpu_config.get("api_port", 5000)
    agent_port = gpu_config.get("agent_port", 5002)

    print(f"\n{'='*60}")
    print(f"  Deploying {name} @ {host}")
    print(f"  Worker: {worker} | Algo: {algo}")
    print(f"  Pool: {pool}")

    if not ssh_password:
        print(f"  [SKIP] No SSH password configured for {host}")
        return False

    def ssh(cmd):
        """Run command on remote via SSH."""
        result = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", f"{ssh_user}@{host}", cmd],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "SSHPASS": ssh_password}
        )
        return result.returncode == 0

    def scp_upload(local, remote):
        """Upload file via SCP."""
        result = subprocess.run(
            ["scp", "-o", "StrictHostKeyChecking=no", local, f"{ssh_user}@{host}:{remote}"],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "SSHPASS": ssh_password}
        )
        return result.returncode == 0

    # 1. Create directory
    ssh('powershell -Command "New-Item -ItemType Directory -Force -Path D:\\miner"')
    print("  [OK] Directory created")

    # 2. Copy GPU agent
    if os.path.exists(GPU_AGENT_TEMPLATE):
        scp_upload(GPU_AGENT_TEMPLATE, "D:/miner/gpu_agent.py")
        print("  [OK] GPU agent uploaded")

    # 3. Create start script
    start_bat = (
        f"@echo off\r\n"
        f"cd /d D:\\miner\r\n"
        f'start "" /b rigel.exe'
        f" -a {algo}"
        f" -o {pool}"
        f" -u {worker}"
        f" -w 002"
        f" --no-tui"
        f" --api-bind 0.0.0.0:{api_port}"
    )
    bat_b64 = __import__('base64').b64encode(start_bat.encode()).decode()
    ssh(f'echo {bat_b64} > D:\\miner\\start.b64 && certutil -decode D:\\miner\\start.b64 D:\\miner\\start_rigel.bat > nul && del D:\\miner\\start.b64')
    print("  [OK] Start script created")

    # 4. Create scheduled tasks
    ssh(f'schtasks /create /tn "RigelMiner" /tr "D:\\miner\\start_rigel.bat" /sc ONSTART /ru SYSTEM /f')
    ssh(f'schtasks /create /tn "GpuAgent" /tr "C:\\Windows\\py.exe D:\\miner\\gpu_agent.py" /sc ONSTART /ru SYSTEM /f')
    print("  [OK] Scheduled tasks created")

    # 5. Firewall rules
    ssh(f'netsh advfirewall firewall add rule name="Rigel API {name}" dir=in action=allow protocol=TCP localport={api_port} 2>nul')
    ssh(f'netsh advfirewall firewall add rule name="GPU Agent {name}" dir=in action=allow protocol=TCP localport={agent_port} 2>nul')
    print("  [OK] Firewall rules added")

    # 6. Start services
    ssh('schtasks /run /tn "RigelMiner"')
    time.sleep(2)
    ssh('schtasks /run /tn "GpuAgent"')
    print("  [OK] Services started")

    print(f"  [DONE] {name} deployed!")
    return True


def main():
    cfg = load_config()
    gpu_miners = cfg.get("gpu_miners", [])
    dry_run = "--dry-run" in sys.argv
    target_host = None

    for arg in sys.argv:
        if arg.startswith("--host="):
            target_host = arg.split("=", 1)[1]

    for gpu in gpu_miners:
        host = gpu.get("host", "")
        if target_host and host != target_host:
            continue

        merged = {**DEFAULT_CONFIG, **gpu}
        ssh_user = merged.get("ssh_user", "25030")
        ssh_pwd = merged.get("ssh_password", "")

        if dry_run:
            print(f"[DRY-RUN] Would deploy to {host} ({merged.get('name')})")
            continue

        try:
            deploy_gpu(host, ssh_user, ssh_pwd, merged)
        except Exception as e:
            print(f"  [ERROR] {host}: {e}")


if __name__ == "__main__":
    main()
