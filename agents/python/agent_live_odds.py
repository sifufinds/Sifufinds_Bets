"""
agent_live_odds.py — Live Sports Odds Agent for SifuFinds
Fetches ESPN public API for non-football sports and openfootball's WC2026 schedule
for football (TheSportsDB's free tier does not carry World Cup 2026 fixtures).
Converts American moneyline odds to decimal and writes data/live.json.

Run by GitHub Actions every 5 minutes. No API keys required.
"""

import json
import re
import sys
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

from utils.live_data_helpers import american_to_decimal

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
OPENFOOTBALL_WC_URL = "https://raw.githubusercontent.com/openfootball/world-cup.json/master/2026/worldcup.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (SifuFinds/2.0; live-odds-agent)"}
TIMEOUT = 12

ENDPOINTS = [
    # Soccer — African leagues return HTTP 400 from ESPN; WC2026 (concluded July
    # 2026) handled by openfootball below. The top-5 European leagues are back
    # in season as of Aug 2026 (see AGENT-KNOWLEDGE.md 2026-08-22) — they used
    # to be omitted here as "off-season", which left this endpoint list with no
    # football at all once the World Cup ended and data/live.json permanently
    # empty for the odds page's football rows.
    {"url": f"{ESPN_BASE}/soccer/eng.1/scoreboard",                    "key": "epl",        "label": "Premier League"},
    {"url": f"{ESPN_BASE}/soccer/esp.1/scoreboard",                    "key": "laliga",     "label": "La Liga"},
    {"url": f"{ESPN_BASE}/soccer/ger.1/scoreboard",                    "key": "bundesliga", "label": "Bundesliga"},
    {"url": f"{ESPN_BASE}/soccer/ita.1/scoreboard",                    "key": "seriea",     "label": "Serie A"},
    {"url": f"{ESPN_BASE}/soccer/fra.1/scoreboard",                    "key": "ligue1",     "label": "Ligue 1"},
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
            day_mon_year = f"{dt.day} {dt.strftime('%b %Y')}"
            return f"{day_mon_year} · {time_part}"
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

    # ESPN's soccer scoreboard can return `"odds": [null]` (no odds panel for
    # that match) rather than omitting the key or using an empty list — crashed
    # every event in a scoreboard the moment one match had no odds panel,
    # which silently zeroed out entire leagues (verified 2026-08-22: eng.1,
    # esp.1, fra.1 all failed this way on every single request).
    odds_list = [o for o in (comp.get("odds") or []) if o]
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
        # No custom User-Agent — ESPN's edge (site.api.espn.com) returns HTTP
        # 403 for ANY explicitly-set User-Agent header (verified 2026-08-22,
        # same issue already documented and fixed in update_leagues.py on
        # 2026-08-09, but never propagated here) while the default
        # python-requests UA gets HTTP 200. This was silently zeroing out
        # every ESPN-sourced sport in data/live.json.
        r = requests.get(endpoint["url"], timeout=TIMEOUT)
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


_OF_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})\s*UTC([+-]\d+)?")
_PLACEHOLDER_TEAM_RE = re.compile(r"^[WL]\d+$")


def _parse_openfootball_kickoff(date_str: str, time_str: str):
    """Parse openfootball's 'HH:MM UTC±N' local kickoff time into a UTC datetime."""
    m = _OF_TIME_RE.match(time_str or "")
    if not m:
        return None
    hh, mm, offset = m.groups()
    offset_hours = int(offset) if offset else 0
    try:
        local_dt = datetime.strptime(f"{date_str} {hh}:{mm}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None
    # "UTC-4" means local = UTC - 4h, so UTC = local + 4h
    return (local_dt - timedelta(hours=offset_hours)).replace(tzinfo=timezone.utc)


def _build_football_fallbacks() -> list:
    """Build verified WC2026 fixtures/results directly from the openfootball schedule.

    TheSportsDB's free tier does not carry World Cup 2026 fixtures (verified: eventsday.php
    returns only minor US leagues for WC2026 match dates), so it cannot be used as the
    schedule source. openfootball/world-cup.json ships the full fixture list with
    date/time/round and is updated with live scores as the tournament progresses.
    Never injects fabricated data — if the feed returns nothing, returns an empty list.
    """
    now_utc = datetime.now(timezone.utc)
    window_start = now_utc - timedelta(hours=3)
    window_end = now_utc + timedelta(days=8)

    try:
        r = requests.get(OPENFOOTBALL_WC_URL, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            print(f"  ⚠ open-football: HTTP {r.status_code}", file=sys.stderr)
            return []
        matches = r.json().get("matches", [])
    except Exception as ex:
        print(f"  ⚠ open-football: {ex}", file=sys.stderr)
        return []

    fallbacks = []
    for m in matches:
        home = m.get("team1", "")
        away = m.get("team2", "")
        if not home or not away:
            continue
        if _PLACEHOLDER_TEAM_RE.match(home) or _PLACEHOLDER_TEAM_RE.match(away):
            continue  # bracket slot not yet resolved (e.g. "W89 vs W90")

        kickoff = _parse_openfootball_kickoff(m.get("date", ""), m.get("time", ""))
        if kickoff is None or not (window_start <= kickoff <= window_end):
            continue

        score = m.get("score") or {}
        final = score.get("p") or score.get("et") or score.get("ft")
        is_complete = final is not None
        home_score = final[0] if final else None
        away_score = final[1] if final else None
        is_live = not is_complete and kickoff <= now_utc <= kickoff + timedelta(minutes=130)

        if is_live or is_complete:
            time_label = "FT" if is_complete else "LIVE"
        else:
            label_day = kickoff.strftime("%-d %b %Y")
            time_label = f"{label_day} · {kickoff.strftime('%H:%M')} UTC"

        round_name = m.get("round") or ""
        comp_label = f"FIFA World Cup 2026 · {round_name}" if round_name else "FIFA World Cup 2026"
        fallbacks.append({
            "league":    comp_label,
            "key":       "world",
            "live":      is_live,
            "complete":  is_complete,
            "home":      home,
            "away":      away,
            "hScore":    home_score,
            "aScore":    away_score,
            "time":      time_label,
            "h": 0.0, "d": 0.0, "a": 0.0,
            "hBk": "1xBet", "dBk": "Betway", "aBk": "Bet9ja",
        })

    if not fallbacks:
        print("  ⚠ open-football returned no WC2026 matches in window — live.json will have no football", file=sys.stderr)

    return fallbacks


def inject_football_fallbacks(events: list) -> list:
    """Add verified WC2026 events from openfootball. Never injects fabricated data."""
    has_football = any(e["key"] == "world" for e in events)
    if not has_football:
        wc_events = _build_football_fallbacks()
        if wc_events:
            print(f"  → WC2026: injected {len(wc_events)} verified matches from openfootball")
        events = events + wc_events
    return events


def _event_key(e: dict) -> str:
    """Deterministic primary key: home:away:sport_key (lowercased)."""
    return f"{e['home'].lower()}:{e['away'].lower()}:{e['key']}"


def upsert_to_supabase(events: list, ts: str) -> bool:
    """Push live_events rows to Supabase.  Returns True on success."""
    try:
        import sys as _sys
        sys_path_backup = _sys.path[:]
        _sys.path.insert(0, str(Path(__file__).parent))
        from utils.supabase_client import sb_upsert  # type: ignore
        _sys.path = sys_path_backup
    except ImportError:
        return False

    rows = [
        {
            "event_key":    _event_key(e),
            "league":       e["league"],
            "sport_key":    e["key"],
            "live":         e["live"],
            "complete":     e["complete"],
            "home":         e["home"],
            "away":         e["away"],
            "h_score":      str(e["hScore"]) if e.get("hScore") is not None else None,
            "a_score":      str(e["aScore"]) if e.get("aScore") is not None else None,
            "time_disp":    e["time"],
            "h_odds":       float(e.get("h", 0) or 0),
            "d_odds":       float(e.get("d", 0) or 0),
            "a_odds":       float(e.get("a", 0) or 0),
            "h_bk":         e.get("hBk", ""),
            "d_bk":         e.get("dBk", ""),
            "a_bk":         e.get("aBk", ""),
            "refreshed_at": ts,
        }
        for e in events
    ]
    ok = sb_upsert("live_events", rows)
    if ok:
        print(f"  → Supabase: upserted {len(rows)} events to live_events")
    else:
        print("  ⚠ Supabase: upsert skipped (not configured or failed)", file=sys.stderr)
    return ok


def main():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] Fetching live sports data...")

    all_events = []
    for ep in ENDPOINTS:
        events = fetch_endpoint(ep)
        if events:
            print(f"  ✓ {ep['label']}: {len(events)} events")
        all_events.extend(events)

    all_events = inject_football_fallbacks(all_events)

    # Drop non-live events whose kickoff was more than 3 hours ago
    # (catches ESPN returning yesterday's games not yet marked complete)
    now_utc = datetime.now(timezone.utc)
    stale_cutoff = now_utc - timedelta(hours=3)

    def _parse_event_time(e: dict):
        """Parse an event's time string to UTC datetime, or None if unparseable."""
        t = e.get("time", "")
        for fmt in ("%d %b %Y · %H:%M UTC", "%d %b · %H:%M UTC"):
            try:
                raw = datetime.strptime(t, fmt)
                if raw.year == 1900:
                    raw = raw.replace(year=now_utc.year)
                return raw.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return None

    def _keep_event(e: dict) -> bool:
        if e.get("live") or e.get("complete"):
            return True
        dt = _parse_event_time(e)
        if dt and dt < stale_cutoff:
            return False
        return True

    before = len(all_events)
    all_events = [e for e in all_events if _keep_event(e)]
    dropped = before - len(all_events)
    if dropped:
        print(f"  → Dropped {dropped} stale non-live events (kickoff >3h ago)")

    # Sort: live first, then by key priority
    KEY_ORDER = ["world", "cafl", "afcon", "local", "epl", "laliga", "bundesliga", "seriea", "ligue1", "ucl", "basketball", "tennis", "cricket", "rugby", "baseball"]
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

    # 1. Push to Supabase (primary)
    upsert_to_supabase(all_events, ts)

    # 2. Write data/live.json (fallback for frontend if Supabase is unreachable)
    repo_root = Path(__file__).parent.parent.parent
    data_dir = repo_root / "data"
    data_dir.mkdir(exist_ok=True)
    out_path = data_dir / "live.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"  → Written {len(all_events)} events to {out_path}")


if __name__ == "__main__":
    main()
