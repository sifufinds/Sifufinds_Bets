"""live_json_store.py — Shared read/merge/write helpers for data/live.json.

Used by agent_multi_scrape.py and agent_firecrawl_odds.py so a match found
by one job (e.g. a fixture from Sofascore) and enriched by another (e.g.
real odds from OddsPortal) both land on the same event instead of each job
keeping its own, non-merging copy.
"""
from __future__ import annotations

import json
from pathlib import Path

LIVE_JSON = Path(__file__).resolve().parent.parent.parent.parent / "data" / "live.json"


def load_live_json(path: Path = LIVE_JSON) -> dict:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"  Could not read {path}: {exc}")
    return {"events": [], "updated": ""}


def save_live_json(data: dict, path: Path = LIVE_JSON) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def match_key(e: dict) -> str:
    return f"{(e.get('home') or '').lower()}|{(e.get('away') or '').lower()}"


def enrich_existing(existing_events: list[dict], new_events: list[dict]) -> list[dict]:
    """Merge new_events into existing_events by (home, away).

    Updates live/score status when the new source has it, backfills odds
    onto an existing zero-odds entry, and appends genuinely new matches.
    Never overwrites odds that are already present.
    """
    existing_map: dict[str, dict] = {match_key(e): e for e in existing_events}

    for new in new_events:
        k = match_key(new)
        if k not in existing_map:
            existing_map[k] = new
            continue

        ex = existing_map[k]
        if new.get("live") and new.get("hScore") is not None:
            ex["live"] = True
            ex["hScore"] = new["hScore"]
            ex["aScore"] = new["aScore"]
            ex["time"] = new["time"]
        elif new.get("complete") and not ex.get("complete"):
            ex["complete"] = True
            ex["hScore"] = new.get("hScore")
            ex["aScore"] = new.get("aScore")
            ex["time"] = "FT"

        if ex.get("h", 0) == 0 and new.get("h", 0) > 0:
            ex["h"] = new["h"]
            ex["d"] = new["d"]
            ex["a"] = new["a"]
            ex["hBk"] = new.get("hBk", "")
            ex["dBk"] = new.get("dBk", "")
            ex["aBk"] = new.get("aBk", "")

    return list(existing_map.values())
