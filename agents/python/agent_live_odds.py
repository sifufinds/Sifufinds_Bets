"""
agent_live_odds.py — Live Sports Odds Agent for SifuFinds
Fetches ESPN public API for 15+ sport endpoints, converts American moneyline
odds to decimal, and writes data/live.json for the site to consume.

Run by GitHub Actions every 5 minutes. No API keys required.
"""

import json
import sys
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
HEADERS = {"User-Agent": "Mozilla/5.0 (SifuFinds/2.0; live-odds-agent)"}
TIMEOUT = 12

ENDPOINTS = [
    # Football / Soccer
    {"url": f"{ESPN_BASE}/soccer/fifa.worldcup/scoreboard",        "key": "world",      "label": "World Cup 2026"},
    {"url": f"{ESPN_BASE}/soccer/caf.champions_league/scoreboard", "key": "cafl",       "label": "CAF Champions League"},
    {"url": f"{ESPN_BASE}/soccer/fifa.worldq.caf/scoreboard",      "key": "afcon",      "label": "AFCON 2027 Qualifier"},
    {"url": f"{ESPN_BASE}/soccer/ng.1/scoreboard",                 "key": "local",      "label": "NPFL Nigeria"},
    {"url": f"{ESPN_BASE}/soccer/ke.1/scoreboard",                 "key": "local",      "label": "Kenya Premier League"},
    {"url": f"{ESPN_BASE}/soccer/za.1/scoreboard",                 "key": "local",      "label": "PSL South Africa"},
    {"url": f"{ESPN_BASE}/soccer/gh.1/scoreboard",                 "key": "local",      "label": "Ghana Premier League"},
    {"url": f"{ESPN_BASE}/soccer/eng.1/scoreboard",                "key": "epl",        "label": "Premier League"},
    {"url": f"{ESPN_BASE}/soccer/esp.1/scoreboard",                "key": "laliga",     "label": "La Liga"},
    {"url": f"{ESPN_BASE}/soccer/uefa.champions/scoreboard",       "key": "ucl",        "label": "UEFA Champions League"},
    # Basketball
    {"url": f"{ESPN_BASE}/basketball/nba/scoreboard",              "key": "basketball", "label": "NBA"},
    {"url": f"{ESPN_BASE}/basketball/wnba/scoreboard",             "key": "basketball", "label": "WNBA"},
    # Baseball
    {"url": f"{ESPN_BASE}/baseball/mlb/scoreboard",                "key": "baseball",   "label": "MLB"},
    # Tennis
    {"url": f"{ESPN_BASE}/tennis/tennis_atp/scoreboard",           "key": "tennis",     "label": "Tennis · ATP"},
    {"url": f"{ESPN_BASE}/tennis/tennis_wta/scoreboard",           "key": "tennis",     "label": "Tennis · WTA"},
    # Cricket
    {"url": f"{ESPN_BASE}/cricket/cricket/scoreboard",             "key": "cricket",    "label": "Cricket"},
    # Rugby
    {"url": f"{ESPN_BASE}/rugby-league/nrl/scoreboard",            "key": "rugby",      "label": "Rugby · NRL"},
]

NO_DRAW_SPORTS = {"basketball", "tennis", "cricket", "rugby", "boxing", "baseball"}


def american_to_decimal(odds_str: str) -> float:
    """Convert American odds string (+164, -198) to decimal odds."""
    try:
        o = int(str(odds_str).replace("+", "").strip())
        return round((100 / abs(o) + 1) if o < 0 else (o / 100 + 1), 2)
    except Exception:
        return 0.0


def format_time(event: dict, is_live: bool, is_complete: bool) -> str:
    """Return a clean, date-aware time string.
    Live:     '67'' or 'Q3 2:15'
    Complete: 'FT'
    Upcoming: '3 Jun · 20:30 UTC' / 'Today · 20:30 UTC' / 'Tomorrow · 20:30 UTC'
    """
    status = event.get("status", {})
    if is_live:
        clock = status.get("displayClock", "")
        return clock if clock and clock not in ("0:00", "0.0") else "LIVE"
    if is_complete:
        return "FT"

    date_str = event.get("date", "")
    if date_str:
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            today = now.date()
            tomorrow = today + timedelta(days=1)
            time_part = dt.strftime("%H:%M UTC")
            if dt.date() == today:
                return f"Today · {time_part}"
            elif dt.date() == tomorrow:
                return f"Tomorrow · {time_part}"
            else:
                day_mon = dt.strftime("%-d %b")
                return f"{day_mon} · {time_part}"
        except Exception:
            pass

    # Fallback to ESPN's own string (still better than nothing)
    short = status.get("type", {}).get("shortDetail", "")
    return short or "TBD"


def map_event(event: dict, key: str, label: str):
    comp = (event.get("competitions") or [{}])[0]
    competitors = comp.get("competitors") or []
    if len(competitors) < 2:
        return None

    home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
    away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

    status_type = event.get("status", {}).get("type", {})
    state = status_type.get("state", "pre")
    is_live = state == "in"
    is_complete = status_type.get("completed", False) or status_type.get("name") == "STATUS_FINAL"

    def name_of(c):
        t = c.get("team") or c.get("athlete") or {}
        return t.get("displayName") or t.get("name") or "TBC"

    home_score = home.get("score") if (is_live or is_complete) else None
    away_score = away.get("score") if (is_live or is_complete) else None

    # Parse DraftKings moneyline odds
    h_odds = a_odds = d_odds = 0.0
    h_bk = a_bk = d_bk = ""

    odds_list = comp.get("odds") or []
    if odds_list:
        od = odds_list[0]
        provider = od.get("provider", {}).get("name", "DraftKings")
        ml = od.get("moneyline") or {}
        home_ml = (ml.get("home") or {}).get("close", {}).get("odds", "")
        away_ml = (ml.get("away") or {}).get("close", {}).get("odds", "")
        if home_ml:
            h_odds = american_to_decimal(home_ml)
            h_bk = provider
        if away_ml:
            a_odds = american_to_decimal(away_ml)
            a_bk = provider

    notes = event.get("notes") or []
    note_headline = notes[0].get("headline", "") if notes else ""
    full_label = f"{label} · {note_headline}" if note_headline else label

    return {
        "league":    full_label,
        "key":       key,
        "live":      is_live,
        "complete":  is_complete,
        "home":      name_of(home),
        "away":      name_of(away),
        "hScore":    home_score,
        "aScore":    away_score,
        "time":      format_time(event, is_live, is_complete),
        "h":         h_odds,
        "d":         d_odds,
        "a":         a_odds,
        "hBk":       h_bk,
        "dBk":       d_bk,
        "aBk":       a_bk,
    }


def fetch_endpoint(endpoint: dict):
    try:
        r = requests.get(endpoint["url"], headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        data = r.json()
        results = []
        for ev in (data.get("events") or [])[:10]:
            m = map_event(ev, endpoint["key"], endpoint["label"])
            if m:
                results.append(m)
        return results
    except Exception as e:
        print(f"  ⚠ {endpoint['label']}: {e}", file=sys.stderr)
        return []


def main():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] Fetching live sports data...")

    all_events = []
    for ep in ENDPOINTS:
        events = fetch_endpoint(ep)
        if events:
            print(f"  ✓ {ep['label']}: {len(events)} events")
        all_events.extend(events)

    # Sort: live first, then by key priority
    KEY_ORDER = ["world", "cafl", "afcon", "local", "basketball", "tennis", "cricket", "rugby", "epl", "ucl", "laliga", "baseball"]
    def sort_key(e):
        live_score = 0 if e["live"] else (2 if e["complete"] else 1)
        key_score = KEY_ORDER.index(e["key"]) if e["key"] in KEY_ORDER else 99
        return (live_score, key_score)

    all_events.sort(key=sort_key)

    output = {
        "updated": ts,
        "count": len(all_events),
        "events": all_events,
    }

    # Write to data/live.json at the repo root
    repo_root = Path(__file__).parent.parent.parent
    data_dir = repo_root / "data"
    data_dir.mkdir(exist_ok=True)
    out_path = data_dir / "live.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"  → Written {len(all_events)} events to {out_path}")


if __name__ == "__main__":
    main()
