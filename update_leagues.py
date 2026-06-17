#!/usr/bin/env python3
"""
update_leagues.py — Fetch 7-day match schedule from football-data.org
and write to data/matches_live.json for the leagues page.

Usage:
  python3 update_leagues.py

Env vars:
  FD_TOKEN  — football-data.org API token (or set directly below)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("ERROR: requests not installed — pip install requests")

ROOT      = Path(__file__).parent
OUT_FILE  = ROOT / "data" / "matches_live.json"

FD_TOKEN  = os.getenv("FD_TOKEN", "530624f0ac724d53ad5ef067d9739ef5")
FD_BASE   = "https://api.football-data.org/v4"

# Competition display priority (lower = shown first)
COMP_PRIORITY: dict[int, int] = {
    2000: 1,   # FIFA World Cup
    2001: 2,   # UEFA Champions League
    2021: 3,   # Premier League
    2014: 4,   # La Liga
    2002: 5,   # Bundesliga
    2019: 6,   # Serie A
    2015: 7,   # Ligue 1
    2017: 8,   # Primeira Liga
    2003: 9,   # Eredivisie
    2016: 10,  # Championship
}


def _headers() -> dict[str, str]:
    return {"X-Auth-Token": FD_TOKEN}


def _fetch_matches(date_from: str, date_to: str) -> list[dict]:
    url = f"{FD_BASE}/matches"
    try:
        r = requests.get(
            url,
            headers=_headers(),
            params={"dateFrom": date_from, "dateTo": date_to},
            timeout=20,
        )
        print(f"  GET /matches {date_from}→{date_to} → HTTP {r.status_code}")
        if r.status_code == 429:
            print("  ⚠ Rate limited — writing empty file")
            return []
        r.raise_for_status()
        return r.json().get("matches", [])
    except Exception as exc:
        print(f"  ERROR: {exc}", file=sys.stderr)
        return []


def _normalise(match: dict) -> dict:
    comp  = match.get("competition", {})
    home  = match.get("homeTeam", {})
    away  = match.get("awayTeam", {})
    score = match.get("score", {})
    ft    = score.get("fullTime", {})
    ht    = score.get("halfTime", {})

    utc_date = match.get("utcDate", "")
    try:
        ko = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
        time_str = ko.strftime("%H:%M UTC")
        date_str = ko.strftime("%-d %b")
    except Exception:
        time_str = ""
        date_str = ""

    return {
        "id":        match.get("id"),
        "compId":    comp.get("id"),
        "compName":  comp.get("name", ""),
        "compCode":  comp.get("code", ""),
        "emblem":    comp.get("emblem", ""),
        "matchday":  match.get("matchday"),
        "stage":     match.get("stage", ""),
        "group":     match.get("group"),
        "utcDate":   utc_date,
        "date":      date_str,
        "time":      time_str,
        "status":    match.get("status", "SCHEDULED"),
        "minute":    match.get("minute"),
        "home":      home.get("shortName") or home.get("name") or "TBD",
        "homeFull":  home.get("name", ""),
        "homeCrest": home.get("crest", ""),
        "away":      away.get("shortName") or away.get("name") or "TBD",
        "awayFull":  away.get("name", ""),
        "awayCrest": away.get("crest", ""),
        "hScore":    ft.get("home"),
        "aScore":    ft.get("away"),
        "hHT":       ht.get("home"),
        "aHT":       ht.get("away"),
    }


def _priority(comp_id: int) -> int:
    return COMP_PRIORITY.get(comp_id, 50)


def main() -> None:
    now       = datetime.now(timezone.utc)
    date_from = now.strftime("%Y-%m-%d")
    date_to   = (now + timedelta(days=6)).strftime("%Y-%m-%d")

    print(f"🟢 Fetching leagues data {date_from} → {date_to}")

    raw_matches = _fetch_matches(date_from, date_to)
    print(f"   {len(raw_matches)} matches returned")

    matches = [_normalise(m) for m in raw_matches]

    # Group by competition
    comp_map: dict[int, dict] = {}
    for m in matches:
        cid = m["compId"]
        if cid not in comp_map:
            comp_map[cid] = {
                "id":       cid,
                "name":     m["compName"],
                "code":     m["compCode"],
                "emblem":   m["emblem"],
                "priority": _priority(cid),
                "matches":  [],
            }
        comp_map[cid]["matches"].append(m)

    competitions = sorted(comp_map.values(), key=lambda c: (c["priority"], c["name"]))

    # Also build a flat date-indexed list for the date tabs
    dates: dict[str, list[dict]] = {}
    for m in matches:
        day = m["utcDate"][:10]  # YYYY-MM-DD
        dates.setdefault(day, []).append(m)

    out = {
        "updated":      now.isoformat(),
        "dateFrom":     date_from,
        "dateTo":       date_to,
        "total":        len(matches),
        "competitions": competitions,
        "byDate":       dates,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"   ✓ {OUT_FILE.relative_to(ROOT)} ({len(matches)} matches, {len(competitions)} competitions)")
    print(f"✅ Done — {now.isoformat()}")


if __name__ == "__main__":
    main()
