import threading
import time
import os
import json

_lock = threading.Lock()
_counters = {
    'total_requests': 0,
    'ai_calls': 0,
    'ai_call_failures': 0
}

# Persist counters to disk so metrics survive restarts.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
TELEMETRY_FILE = os.path.join(DATA_DIR, 'telemetry.json')

def _load_counters():
    try:
        if os.path.exists(TELEMETRY_FILE):
            with open(TELEMETRY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
    except Exception:
        pass
    return None

_loaded = _load_counters()
if _loaded and isinstance(_loaded, dict):
    with _lock:
        for k, v in _loaded.items():
            _counters[k] = int(v)

def increment(name: str, by: int = 1):
    with _lock:
        _counters[name] = _counters.get(name, 0) + by
        # persist on change
        try:
            with open(TELEMETRY_FILE, 'w', encoding='utf-8') as f:
                json.dump(_counters, f)
        except Exception:
            pass

def get_metrics_text() -> str:
    # Return Prometheus-compatible metrics exposition
    lines = []
    with _lock:
        for k, v in _counters.items():
            # sanitize metric name
            name = k.replace('.', '_')
            lines.append(f"# HELP {name} Simple counter for {name}")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {int(v)}")
    # add timestamp
    lines.append(f"# Generated at {int(time.time())}")
    return "\n".join(lines) + "\n"


def get_metrics_json() -> dict:
    with _lock:
        return dict(_counters)
