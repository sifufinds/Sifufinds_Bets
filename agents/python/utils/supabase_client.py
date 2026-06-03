"""Shared Supabase client for all SifuFinds agents.

Usage:
    from utils.supabase_client import sb, sb_upsert, sb_set_state, sb_get_state

Requires SUPABASE_URL and SUPABASE_SERVICE_KEY env vars (set as GitHub secrets
and in .env locally).  Falls back to no-op silently so agents still work without
Supabase configured.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import Any

_client = None
_enabled = False


def _init():
    global _client, _enabled
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    if not url or not key:
        return
    try:
        from supabase import create_client  # type: ignore
        _client = create_client(url, key)
        _enabled = True
    except Exception as exc:
        print(f"[supabase] init failed: {exc}", file=sys.stderr)


_init()


def sb():
    """Return the Supabase client, or None if not configured."""
    return _client


def sb_upsert(table: str, rows: list[dict], on_conflict: str = "") -> bool:
    """Upsert rows into a table.  Returns True on success."""
    if not _enabled or not rows:
        return False
    try:
        q = _client.table(table).upsert(rows)
        if on_conflict:
            q = q.on_conflict(on_conflict)
        q.execute()
        return True
    except Exception as exc:
        print(f"[supabase] upsert {table} failed: {exc}", file=sys.stderr)
        return False


def sb_insert(table: str, rows: list[dict]) -> bool:
    """Insert rows; silently skip duplicates."""
    if not _enabled or not rows:
        return False
    try:
        _client.table(table).insert(rows).execute()
        return True
    except Exception as exc:
        print(f"[supabase] insert {table} failed: {exc}", file=sys.stderr)
        return False


def sb_set_state(key: str, value: Any) -> bool:
    """Upsert a key→jsonb value in agent_state (replaces JSON file on disk)."""
    return sb_upsert("agent_state", [{"key": key, "value": value, "updated_at": _now()}])


def sb_get_state(key: str) -> Any | None:
    """Fetch a state value from agent_state.  Returns None if not found."""
    if not _enabled:
        return None
    try:
        r = _client.table("agent_state").select("value").eq("key", key).single().execute()
        return r.data.get("value") if r.data else None
    except Exception:
        return None


def sb_log(agent: str, action: str, status: str, detail: str = "", meta: dict | None = None) -> bool:
    """Append a row to agent_logs."""
    row = {
        "logged_at": _now(),
        "agent": agent,
        "action": action,
        "status": status,
        "detail": detail or "",
        "meta": meta or {},
    }
    return sb_insert("agent_logs", [row])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
