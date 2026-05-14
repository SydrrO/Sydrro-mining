"""SysLog v2 — structured event logger for mining operations.

Categories:
  pool       — pool connection/disconnection, latency spikes
  hashrate   — hashrate drops, DAG generation, recovery
  hardware   — GPU temperature warnings, fan issues, HW errors
  network    — proxy restarts, connection timeouts
  system     — dashboard restarts, config reloads

Severity:
  0  OK      — normal events (DAG done, miner started)
  1  INFO    — informational
  2  WARN    — needs attention (hashrate drop, high latency)
  3  ERROR   — critical (miner offline, pool dead)
"""

import json
import os
import time
from datetime import datetime, timedelta
from collections import deque
from threading import Lock

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SEVERITY_MAP = {"OK": 0, "INFO": 1, "WARN": 2, "ERROR": 3}
SEVERITY_ICONS = {0: "✓", 1: "ℹ", 2: "⚠", 3: "✗"}
SEVERITY_COLORS = {0: "log-ok", 1: "log-info", 2: "log-warning", 3: "log-danger"}

CATEGORY_LABELS = {
    "pool": "Pool",
    "hashrate": "Hashrate",
    "hardware": "Hardware",
    "network": "Network",
    "system": "System",
}


class SysLog:
    def __init__(self, config=None):
        self._lock = Lock()
        self._events = deque(maxlen=500)
        self._counters = {
            "disconnects": 0,
            "restarts": 0,
            "unreachable": 0,
            "hash_drops": 0,
            "hw_spikes": 0,
        }
        self._log_path = config.get("log_path", os.path.join(BASE_DIR, "mining_events.log")) if config else os.path.join(BASE_DIR, "mining_events.log")
        self._last_hw = {}  # Track HW errors for per-minute rate calculation

    def log(self, category, severity, message, detail=None):
        """Record an event."""
        ts = datetime.now()
        with self._lock:
            event = {
                "ts": ts.isoformat(),
                "ts_display": ts.strftime("%m/%d %H:%M:%S"),
                "category": category,
                "severity": severity,
                "severity_level": SEVERITY_MAP.get(severity, 1),
                "message": message,
                "detail": detail or "",
            }
            self._events.append(event)

            # Update counters
            if category == "pool" and severity in ("WARN", "ERROR"):
                self._counters["disconnects"] += 1
            elif category == "system" and "restart" in message.lower():
                self._counters["restarts"] += 1
            elif category == "network" and "unreachable" in message.lower():
                self._counters["unreachable"] += 1
            elif category == "hashrate" and "drop" in message.lower():
                self._counters["hash_drops"] += 1
            elif category == "hardware" and severity in ("WARN", "ERROR"):
                self._counters["hw_spikes"] += 1

            self._write_to_file(event)

    def ok(self, category, message, detail=None):
        self.log(category, "OK", message, detail)

    def info(self, category, message, detail=None):
        self.log(category, "INFO", message, detail)

    def warn(self, category, message, detail=None):
        self.log(category, "WARN", message, detail)

    def error(self, category, message, detail=None):
        self.log(category, "ERROR", message, detail)

    def get_recent(self, limit=100, min_severity=0, categories=None):
        """Get recent events with filtering."""
        with self._lock:
            events = list(self._events)
            if categories:
                events = [e for e in events if e["category"] in categories]
            events = [e for e in events if SEVERITY_MAP.get(e["severity"], 1) >= min_severity]
            return events[-limit:]

    def get_summary(self):
        """Get 24h summary counts."""
        cutoff = datetime.now() - timedelta(hours=24)
        with self._lock:
            recent = [e for e in self._events if datetime.fromisoformat(e["ts"]) > cutoff]
            summary = dict(self._counters)
            summary["total_events_24h"] = len(recent)
            summary["warnings_24h"] = sum(1 for e in recent if e["severity"] == "WARN")
            summary["errors_24h"] = sum(1 for e in recent if e["severity"] == "ERROR")
        return summary

    def get_timeline(self, limit=50):
        """Get timeline for dashboard display."""
        with self._lock:
            events = list(self._events)[-limit:]
        return [
            {
                "time": e["ts_display"],
                "cat": CATEGORY_LABELS.get(e["category"], e["category"]),
                "sev": e["severity"],
                "level": e["severity_level"],
                "icon": SEVERITY_ICONS.get(e["severity_level"], "?"),
                "color": SEVERITY_COLORS.get(e["severity_level"], ""),
                "msg": e["message"],
                "detail": e["detail"],
            }
            for e in reversed(events)
        ]

    def _write_to_file(self, event):
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(
                    f"[{event['ts_display']}] [{event['severity']}] [{event['category']}] "
                    f"{event['message']}"
                )
                if event.get("detail"):
                    f.write(f" | {event['detail']}")
                f.write("\n")
        except Exception:
            pass


# ---- Singleton ----
_instance = None


def get_syslog(config=None):
    global _instance
    if _instance is None:
        _instance = SysLog(config)
    return _instance
