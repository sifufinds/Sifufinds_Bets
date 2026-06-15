"""
agent_live_odds.py — Live Sports Odds Agent for SifuFinds
Fetches ESPN public API for non-football sports and TheSportsDB for WC2026/football.
Converts American moneyline odds to decimal and writes data/live.json.

Run by GitHub Actions every 5 minutes. No API keys required.
"""

import json
import sys
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
SPORTSDB_BASE = "https://www.thesportsdb.com/api/v1/json/3"
OPENFOOTBALL_WC_URL = "https://raw.githubusercontent.com/openfootball/world-cup.json/master/2026/worldcup.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (SifuFinds/2.0; live-odds-agent)"}
TIMEOUT = 12

ENDPOINTS = [
    # Football / Soccer — ESPN endpoints kept for reference; WC2026 uses TheSportsDB instead
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


def _build_football_fallbacks() -> list:
    """Build fallback events for missing football keys using TheSportsDB + open-football WC2026 data."""
    fallbacks = []
    now_utc = datetime.now(timezone.utc)
    today = now_utc.strftime("%Y-%m-%d")
    tomorrow = (now_utc + timedelta(days=1)).strftime("%Y-%m-%d")
    window_end = (now_utc + timedelta(days=2)).strftime("%Y-%m-%d")

    # ── TheSportsDB: fetch WC2026 matches for today + tomorrow ─────────────────
    wc_events = []
    for date_str in [today, tomorrow]:
        try:
            url = f"{SPORTSDB_BASE}/eventsday.php?d={date_str}&s=Soccer"
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code == 200:
                events = r.json().get("events") or []
                for e in events:
                    if "World Cup" in (e.get("strLeague") or ""):
                        wc_events.append(e)
        except Exception as ex:
            print(f"  ⚠ TheSportsDB {date_str}: {ex}", file=sys.stderr)

    # ── Open Football: get recent results as context ────────────────────────────
    wc_results: dict[str, dict] = {}
    try:
        r = requests.get(OPENFOOTBALL_WC_URL, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200:
            matches = r.json().get("matches", [])
            for m in matches:
                key = f"{m['team1']}:{m['team2']}"
                score = m.get("score", {})
                ft = score.get("ft")
                if ft and ft[0] is not None:
                    wc_results[key] = {"hScore": ft[0], "aScore": ft[1], "complete": True}
    except Exception as ex:
        print(f"  ⚠ open-football: {ex}", file=sys.stderr)

    for e in wc_events:
        home = e.get("strHomeTeam", "")
        away = e.get("strAwayTeam", "")
        if not home or not away:
            continue
        date_event = e.get("dateEvent", today)
        time_str = e.get("strTime", "")
        group = e.get("strGroup") or ""
        status = e.get("strStatus", "NS")
        home_score = e.get("intHomeScore")
        away_score = e.get("intAwayScore")
        is_complete = status in ("FT", "AET", "PEN")
        is_live = status in ("1H", "HT", "2H", "ET", "P")

        result = wc_results.get(f"{home}:{away}", {})
        if result:
            home_score = result["hScore"]
            away_score = result["aScore"]
            is_complete = result["complete"]

        try:
            dt = datetime.strptime(f"{date_event} {time_str}", "%Y-%m-%d %H:%M:%S")
            dt = dt.replace(tzinfo=timezone.utc)
            label_day = dt.strftime("%-d %b %Y")
            time_label = f"{label_day} · {dt.strftime('%H:%M')} UTC"
        except Exception:
            time_label = f"{date_event} · {time_str[:5]} UTC"

        comp_label = f"FIFA World Cup 2026 · Group {group}" if group else "FIFA World Cup 2026"
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
        # Absolute last-resort static fallbacks (always upcoming)
        fallbacks = [
            {"league": "FIFA World Cup 2026 · Group G", "key": "world", "live": False, "complete": False,
             "home": "Spain", "away": "Cape Verde", "hScore": None, "aScore": None,
             "time": "15 Jun 2026 · 16:00 UTC", "h": 1.22, "d": 6.00, "a": 13.00, "hBk": "1xBet", "dBk": "Betway", "aBk": "Bet9ja"},
            {"league": "FIFA World Cup 2026 · Group H", "key": "world", "live": False, "complete": False,
             "home": "Belgium", "away": "Egypt", "hScore": None, "aScore": None,
             "time": "15 Jun 2026 · 19:00 UTC", "h": 1.55, "d": 4.00, "a": 6.50, "hBk": "Betway", "dBk": "1xBet", "aBk": "Bet9ja"},
            {"league": "FIFA World Cup 2026 · Group H", "key": "world", "live": False, "complete": False,
             "home": "Saudi Arabia", "away": "Uruguay", "hScore": None, "aScore": None,
             "time": "15 Jun 2026 · 22:00 UTC", "h": 3.20, "d": 3.30, "a": 2.30, "hBk": "Bet9ja", "dBk": "SportyBet", "aBk": "1xBet"},
            {"league": "FIFA World Cup 2026 · Group I", "key": "world", "live": False, "complete": False,
             "home": "France", "away": "Senegal", "hScore": None, "aScore": None,
             "time": "16 Jun 2026 · 22:00 UTC", "h": 1.60, "d": 3.80, "a": 6.00, "hBk": "1xBet", "dBk": "22Bet", "aBk": "Betway"},
            {"league": "FIFA World Cup 2026 · Group J", "key": "world", "live": False, "complete": False,
             "home": "Argentina", "away": "Algeria", "hScore": None, "aScore": None,
             "time": "16 Jun 2026 · 19:00 UTC", "h": 1.30, "d": 5.50, "a": 10.00, "hBk": "Betway", "dBk": "1xBet", "aBk": "Bet9ja"},
        ]

    return fallbacks


FOOTBALL_FALLBACKS_STATIC = [
    {"league": "AFCON 2027 Qualifier", "key": "afcon", "live": False, "complete": False,
     "home": "Nigeria", "away": "DR Congo", "hScore": None, "aScore": None,
     "time": "16 Jun 2026 · 17:00 UTC", "h": 1.65, "d": 3.90, "a": 5.50, "hBk": "Bet9ja", "dBk": "SportPesa", "aBk": "1xBet"},
    {"league": "AFCON 2027 Qualifier", "key": "afcon", "live": False, "complete": False,
     "home": "Senegal", "away": "Algeria", "hScore": None, "aScore": None,
     "time": "17 Jun 2026 · 19:00 UTC", "h": 1.70, "d": 3.30, "a": 5.00, "hBk": "1xBet", "dBk": "22Bet", "aBk": "Melbet"},
    {"league": "NPFL · Super 8", "key": "local", "live": False, "complete": False,
     "home": "Enyimba FC", "away": "Remo Stars", "hScore": None, "aScore": None,
     "time": "16 Jun 2026 · 15:00 UTC", "h": 2.00, "d": 3.20, "a": 3.80, "hBk": "Bet9ja", "dBk": "Sportybet", "aBk": "BetKing"},
    {"league": "Kenya Premier League · Playoff", "key": "local", "live": False, "complete": False,
     "home": "Gor Mahia", "away": "AFC Leopards", "hScore": None, "aScore": None,
     "time": "17 Jun 2026 · 13:00 UTC", "h": 2.10, "d": 3.00, "a": 3.60, "hBk": "Betika", "dBk": "SportPesa", "aBk": "Betway"},
]

FOOTBALL_KEYS = {"world", "cafl", "afcon", "local", "epl", "ucl", "laliga"}


def inject_football_fallbacks(events: list) -> list:
    """Add dynamic WC2026 events from TheSportsDB + static fallbacks for missing football keys."""
    covered = {e["key"] for e in events}
    missing = FOOTBALL_KEYS - covered

    if "world" in missing:
        wc_events = _build_football_fallbacks()
        if wc_events:
            print(f"  → WC2026: injected {len(wc_events)} matches from TheSportsDB/open-football")
        events = events + wc_events
        if wc_events:
            missing -= {"world"}

    if missing:
        injected = [e for e in FOOTBALL_FALLBACKS_STATIC if e["key"] in missing]
        if injected:
            print(f"  → Static fallback for: {', '.join(sorted(missing))}")
        events = events + injected

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
