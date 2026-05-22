"""Simple file-based logger — no database needed."""
import json
import os
from datetime import datetime, timezone


LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "agent_log.json")


def log(agent: str, action: str, status: str, detail: str = ""):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "action": action,
        "status": status,
        "detail": detail,
    }
    records = _read()
    records.append(entry)
    # Keep last 500 entries only
    records = records[-500:]
    with open(LOG_FILE, "w") as f:
        json.dump(records, f, indent=2)
    print(f"[{entry['ts']}] [{agent}] {action} → {status}")


def _read() -> list:
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def get_last_n(n: int = 50) -> list:
    return _read()[-n:]
