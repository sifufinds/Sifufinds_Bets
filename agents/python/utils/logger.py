"""File-based logger that also mirrors entries to Supabase agent_logs."""
import json
import os
from datetime import datetime, timezone


LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "agent_log.json")


def log(agent: str, action: str, status: str, detail: str = "", meta: dict | None = None):
    ts = datetime.now(timezone.utc).isoformat()
    entry = {"ts": ts, "agent": agent, "action": action, "status": status, "detail": detail}

    # Write to local JSON (always, as fallback)
    records = _read()
    records.append(entry)
    records = records[-500:]
    with open(LOG_FILE, "w") as f:
        json.dump(records, f, indent=2)

    # Mirror to Supabase (best-effort, never raises)
    try:
        from utils.supabase_client import sb_log  # type: ignore
        sb_log(agent, action, status, detail, meta)
    except Exception:
        pass

    print(f"[{ts}] [{agent}] {action} → {status}")


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
