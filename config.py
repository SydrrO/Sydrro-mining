"""Mining Dashboard configuration."""

import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError(f"config.json not found at {CONFIG_PATH}")


def create_default():
    """Create a default config.json if it doesn't exist."""
    default = {
        "asic": {
            "ip": "192.168.3.5",
            "user": "root",
            "password": "ltc@dog"
        },
        "gpu_miners": [
            {"host": "192.168.3.6", "port": 5002, "name": "GPU #1"},
            {"host": "192.168.3.2", "port": 5002, "name": "GPU #2"}
        ],
        "database": {
            "path": "miner_data.db"
        },
        "server": {
            "host": "0.0.0.0",
            "port": 5000
        }
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(default, f, indent=2, ensure_ascii=False)
    print(f"Created default config: {CONFIG_PATH}")
    return default
