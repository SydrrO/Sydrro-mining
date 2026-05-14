#!/usr/bin/env python3
"""VolcMiner D1 MINI real-time monitor."""

import requests
from requests.auth import HTTPDigestAuth
import time
import json
import re
import csv
from datetime import datetime

BASE_URL = "http://192.168.3.5"
USER = "root"
PWD = "ltc@dog"


def extract_inner(raw_text):
    """Extract the inner JSON object from the malformed API response."""
    m = re.search(r'"data"\s*:\s*"', raw_text)
    if not m:
        return None
    pos = m.end()
    while pos < len(raw_text) and raw_text[pos] in ' \t\n\r':
        pos += 1
    if pos >= len(raw_text):
        return None
    open_ch = raw_text[pos]
    close_ch = '}' if open_ch == '{' else ']' if open_ch == '[' else None
    if close_ch is None:
        return None
    depth = 0
    for i in range(pos, len(raw_text)):
        c = raw_text[i]
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return raw_text[pos:i + 1]
    return None


def extract_simple(key, text):
    """Extract a simple string value: "key": "value" """
    m = re.search(r'"' + re.escape(key) + r'"\s*:\s*"([^"]*)"', text)
    return m.group(1) if m else None


def extract_bracket_string(key, text):
    """Extract a string value that contains an unescaped JSON object/array.
    The API returns these as: "key": "[...]" or "key": "{...}"
    where the inner brackets and their contents are NOT escaped.
    """
    m = re.search(r'"' + re.escape(key) + r'"\s*:\s*"', text)
    if not m:
        return None
    pos = m.end()
    while pos < len(text) and text[pos] not in '[{':
        pos += 1
    if pos >= len(text):
        return None
    open_ch = text[pos]
    close_ch = ']' if open_ch == '[' else '}'
    val_start = pos
    depth = 0
    for i in range(pos, len(text)):
        c = text[i]
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return text[val_start:i + 1]
    return None


def extract_json_obj(key, text):
    """Extract a proper JSON object value: "key": { ... } """
    m = re.search(r'"' + re.escape(key) + r'"\s*:\s*', text)
    if not m:
        return None
    pos = m.end()
    while pos < len(text) and text[pos] in ' \t\n\r':
        pos += 1
    if pos >= len(text) or text[pos] != '{':
        return None
    depth = 0
    for i in range(pos, len(text)):
        c = text[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return text[pos:i + 1]
    return None


def parse_status(raw_text):
    """Parse miner status response."""
    inner = extract_inner(raw_text)
    if not inner:
        return None

    result = {}

    # Simple string fields
    for key in ['elapsed', 'ghs5s', 'ghsav', 'localwork', 'utility', 'wu', 'bestshare']:
        v = extract_simple(key, inner)
        if v is not None:
            result[key] = v

    # chains: string-embedded JSON array
    chains_raw = extract_bracket_string('chains', inner)
    if chains_raw:
        try:
            result['chains'] = json.loads(chains_raw)
        except:
            result['chains'] = []

    # fan: regular nested JSON object
    fan_raw = extract_json_obj('fan', inner)
    if fan_raw:
        try:
            result['fan'] = json.loads(fan_raw)
        except:
            result['fan'] = {}

    # pools: regular nested JSON object
    pools_raw = extract_json_obj('pools', inner)
    pools_obj = {}
    if pools_raw:
        try:
            pools_obj = json.loads(pools_raw)
        except:
            pools_obj = {}

    # pool_dtls: string-embedded JSON array inside pools
    pool_dtls_raw = extract_bracket_string('pool_dtls', inner)
    if pool_dtls_raw:
        try:
            result['pool_dtls'] = json.loads(pool_dtls_raw)
        except:
            result['pool_dtls'] = []
    else:
        result['pool_dtls'] = []

    # Also extract hw and total from pools
    for sub in ['hw', 'total']:
        sub_raw = extract_json_obj(sub, inner)
        if sub_raw:
            try:
                result[sub] = json.loads(sub_raw)
            except:
                pass

    return result


def parse_system(raw_text):
    """Parse system info response."""
    inner = extract_inner(raw_text)
    if not inner:
        return None
    # The system info inner is valid JSON
    try:
        return json.loads(inner)
    except:
        pass
    # Fallback: regex extraction
    result = {}
    for key in ['minertype', 'macaddr', 'hostname', 'ipaddress',
                'uptime', 'mem_total', 'mem_used', 'mem_free',
                'system_filesystem_version', 'cgminer_version',
                'bb_hwv', 'loadaverage', 'machine_time']:
        v = extract_simple(key, inner)
        if v is not None:
            result[key] = v
    return result


def num(s):
    if isinstance(s, (int, float)):
        return float(s)
    return float(str(s).replace(",", ""))


def ghs(v):
    if v >= 1000:
        return f"{v / 1000:.2f} TH/s"
    return f"{v:.2f} GH/s"


def main():
    auth = HTTPDigestAuth(USER, PWD)
    interval = 3

    # Fetch system info once
    sys_info = None
    try:
        r = requests.get(f"{BASE_URL}/cgi-bin/get_system_infoV1.cgi", auth=auth, timeout=5)
        sys_info = parse_system(r.text)
    except:
        pass

    import sys
    print("=" * 70, flush=True)
    print("  VolcMiner D1 MINI Real-time Monitor", flush=True)
    if sys_info:
        print(f"  Model: {sys_info.get('minertype', '?')}  |  FW: {sys_info.get('system_filesystem_version', '?')}", flush=True)
        print(f"  Uptime: {sys_info.get('uptime', '?')} days  |  cgminer: {sys_info.get('cgminer_version', '?')}", flush=True)
    print("=" * 70, flush=True)

    # CSV log
    log_file = f"miner_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(log_file, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "ghs5s", "ghsav", "temp1", "temp2", "hw_total", "fan2", "fan3", "elapsed", "accepted", "rejected"])

    header = f"  {'Time':>8}  {'Hash(5s)':>10}  {'Hash(avg)':>10}  T1   T2  HW  {'Fan2/Fan3':>12}  {'Pool':>16}"
    print(header, flush=True)
    print("  " + "-" * (len(header) - 2), flush=True)

    count = 0
    try:
        while True:
            try:
                r = requests.get(f"{BASE_URL}/cgi-bin/get_miner_statusV1.cgi", auth=auth, timeout=5)
                data = parse_status(r.text)
            except:
                time.sleep(interval)
                continue

            if not data:
                time.sleep(interval)
                continue

            ghs5s = num(data.get('ghs5s', '0'))
            ghsav = num(data.get('ghsav', '0'))
            elapsed = data.get('elapsed', '?')

            chains = data.get('chains', [])
            t1 = chains[0].get('temp', '?') if isinstance(chains, list) and len(chains) > 0 else '?'
            t2 = chains[1].get('temp', '?') if isinstance(chains, list) and len(chains) > 1 else '?'
            hw_total = sum(int(c.get('hw', 0)) for c in chains) if isinstance(chains, list) else 0

            fan = data.get('fan', {})
            fan2 = fan.get('fan2', '?') if isinstance(fan, dict) else '?'
            fan3 = fan.get('fan3', '?') if isinstance(fan, dict) else '?'

            pools = data.get('pool_dtls', [])
            if isinstance(pools, str):
                try:
                    pools = json.loads(pools)
                except:
                    pools = []
            pool_alive = next((p for p in pools if p.get('status') == 'Alive'), None)
            pool_str = f"acc:{pool_alive.get('accepted','?')}" if pool_alive else "?"

            ts = datetime.now().strftime('%H:%M:%S')
            print(f"  {ts:>8}  {ghs(ghs5s):>10}  {ghs(ghsav):>10}  "
                  f"{t1:>3}C {t2:>3}C {hw_total:>3}  "
                  f"{fan2:>5}/{fan3:<5}  {pool_str:>16}  [{elapsed}]", flush=True)

            # CSV logging
            try:
                with open(log_file, "a", encoding="utf-8", newline="") as f:
                    acc = pool_alive.get('accepted', '0') if pool_alive else '0'
                    rej = pool_alive.get('rejected', '0') if pool_alive else '0'
                    w = csv.writer(f)
                    w.writerow([datetime.now().isoformat(), ghs5s, ghsav, t1, t2, hw_total, fan2, fan3, elapsed, acc, rej])
            except:
                pass

            count += 1
            time.sleep(interval)

    except KeyboardInterrupt:
        print()
        print(f"  Stopped. {count} samples logged to: {log_file}")


if __name__ == "__main__":
    main()
