#!/usr/bin/env python3
"""
update_football_data.py — SifuFinds Football Data Updater
Fetches live scores, standings and fixtures from api-sports.io (API-Football v3).
Writes results to data/football/ for the Tables page to consume.

Usage:
  python3 update_football_data.py             # full update (standings + live)
  python3 update_football_data.py --live-only # only refresh live scores
  python3 update_football_data.py --standings # only refresh standings

Env vars required:
  FOOTBALL_API_KEY  — api-sports.io key (set in .env or GitHub Actions secrets)

Rate limits (free tier): 100 calls/day, 10 calls/min.
This script budgets calls carefully: live data uses 1 call, standings use ~1 each.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

# ── Config ─────────────────────────────────────────────────────────────────
API_KEY = os.getenv("FOOTBALL_API_KEY", "")
BASE_URL = "https://v3.football.api-sports.io"
DATA_DIR = Path(__file__).parent / "data" / "football"
STANDINGS_DIR = DATA_DIR / "standings"

# Competition IDs on api-sports.io  →  our local slug
COMPETITION_MAP = {
    1:   "world-cup-2026",        # FIFA World Cup (current season = 2026)
    2:   "champions-league",      # UEFA Champions League
    3:   "europa-league",
    5:   "euro-nations-league",
    6:   "afcon",                 # AFCON
    7:   "copa-america",
    8:   "wwc-2023",              # FIFA Women's World Cup
    9:   "gold-cup",
    10:  "fifa-club-world-cup",
    12:  "caf-champions-league",
    13:  "copa-libertadores",
    39:  "premier-league",
    45:  "fa-cup",
    46:  "efl-cup",
    61:  "ligue-1",
    65:  "wsl",
    78:  "bundesliga",
    81:  "dfb-pokal",
    88:  "eredivisie",
    94:  "primeira-liga",
    135: "serie-a",
    140: "laliga",
    143: "copa-del-rey",
    144: "pro-league",
    203: "super-lig",
    253: "mls",
    262: "liga-mx",
    283: "brasileirao",
    288: "psl",                   # DStv Premiership (South Africa)
    363: "npfl",                  # Nigeria Professional Football League
    # African leagues
    169: "gpl",                   # Ghana Premier League
    200: "botola",                # Botola Pro (Morocco)
    704: "kpl",                   # Kenya PL (varies by API)
}

# Competitions to refresh in the daily standings run (conserve API calls)
DAILY_STANDINGS = [
    (1, 2026),    # World Cup 2026
    (2, 2025),    # UCL 2025-26
    (6, 2025),    # AFCON 2025
    (12, 2026),   # CAF CL 2026
    (13, 2026),   # Copa Libertadores 2026
    (39, 2025),   # Premier League 2025-26
    (140, 2025),  # LaLiga 2025-26
    (78, 2025),   # Bundesliga 2025-26
    (135, 2025),  # Serie A 2025-26
    (61, 2025),   # Ligue 1 2025-26
    (253, 2026),  # MLS 2026
    (283, 2026),  # Brasileirão 2026
    (288, 2026),  # PSL 2026
    (363, 2025),  # NPFL 2025-26
]


def _headers():
    return {"X-apisports-key": API_KEY, "Accept": "application/json"}


def _get(endpoint: str, params: dict = None) -> dict | None:
    if not API_KEY:
        return None
    url = f"{BASE_URL}{endpoint}"
    try:
        r = requests.get(url, headers=_headers(), params=params or {}, timeout=15)
        r.raise_for_status()
        data = r.json()
        remaining = r.headers.get("X-RateLimit-Requests-Remaining", "?")
        print(f"  GET {endpoint} → {r.status_code} | remaining calls: {remaining}")
        return data
    except Exception as e:
        print(f"  ERROR {endpoint}: {e}", file=sys.stderr)
        return None


def _write(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    print(f"  ✓ wrote {path.relative_to(Path(__file__).parent)}")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Live matches ────────────────────────────────────────────────────────────
def fetch_live():
    print("→ Fetching live matches…")
    data = _get("/fixtures", {"live": "all"})
    if data is None:
        _write_live_empty()
        return

    fixtures = data.get("response", [])
    matches = [_normalise_fixture(f) for f in fixtures]
    live_count = len([m for m in matches if m["status"] in ("LIVE", "1H", "2H", "HT", "ET", "P")])

    out = {
        "updated": _now_iso(),
        "liveCount": live_count,
        "matches": matches,
    }
    _write(DATA_DIR / "live.json", out)


def _write_live_empty():
    _write(DATA_DIR / "live.json", {
        "updated": _now_iso(),
        "liveCount": 0,
        "matches": [],
        "note": "No API key configured — set FOOTBALL_API_KEY in .env",
    })


def _normalise_fixture(f: dict) -> dict:
    fix = f.get("fixture", {})
    teams = f.get("teams", {})
    goals = f.get("goals", {})
    league = f.get("league", {})
    score = f.get("score", {})

    ko = fix.get("date", "")
    ko_dt = None
    if ko:
        try:
            ko_dt = datetime.fromisoformat(ko.replace("Z", "+00:00"))
        except Exception:
            pass

    status_short = fix.get("status", {}).get("short", "NS")
    elapsed = fix.get("status", {}).get("elapsed")

    return {
        "id": fix.get("id"),
        "competition": league.get("name", ""),
        "competitionId": league.get("id"),
        "round": league.get("round", ""),
        "home": teams.get("home", {}).get("name", ""),
        "away": teams.get("away", {}).get("name", ""),
        "hScore": goals.get("home"),
        "aScore": goals.get("away"),
        "status": status_short,
        "minute": elapsed,
        "date": ko_dt.strftime("%-d %b") if ko_dt else "",
        "time": ko_dt.strftime("%H:%M UTC") if ko_dt else "",
        "venue": fix.get("venue", {}).get("name", ""),
    }


# ── Today's fixtures ────────────────────────────────────────────────────────
def fetch_today():
    print("→ Fetching today's fixtures…")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # fetch top competitions for today
    all_fixtures = []
    for league_id, season in DAILY_STANDINGS[:6]:
        time.sleep(0.5)
        data = _get("/fixtures", {"league": league_id, "season": season, "date": today})
        if data:
            all_fixtures.extend([_normalise_fixture(f) for f in data.get("response", [])])

    out = {
        "updated": _now_iso(),
        "date": today,
        "count": len(all_fixtures),
        "fixtures": all_fixtures,
    }
    _write(DATA_DIR / "today.json", out)


# ── Standings ───────────────────────────────────────────────────────────────
def fetch_standings(league_id: int, season: int, slug: str):
    print(f"→ Standings: {slug} (league {league_id}, season {season})…")
    data = _get("/standings", {"league": league_id, "season": season})
    if data is None:
        return

    resp = data.get("response", [])
    if not resp:
        print(f"  No standings data for {slug}")
        return

    league_info = resp[0].get("league", {})
    standings_raw = league_info.get("standings", [])

    # World Cup / group-stage competitions have multiple standing arrays (one per group)
    is_groups = len(standings_raw) > 1

    if is_groups:
        _write_group_standings(slug, league_info, standings_raw)
    else:
        _write_league_standings(slug, league_info, standings_raw[0] if standings_raw else [])


def _write_group_standings(slug: str, league_info: dict, standings_raw: list):
    groups = []
    for group_teams in standings_raw:
        if not group_teams:
            continue
        group_name = group_teams[0].get("group", f"Group {len(groups)+1}")
        teams = [_normalise_team(t) for t in group_teams]
        groups.append({"name": group_name, "teams": teams, "fixtures": []})

    out = {
        "updated": _now_iso(),
        "competition": league_info.get("name", slug),
        "stage": "Group Stage",
        "type": "groups",
        "season": league_info.get("season"),
        "groups": groups,
    }
    _write(STANDINGS_DIR / f"{slug}.json", out)


def _write_league_standings(slug: str, league_info: dict, teams_raw: list):
    standings = [_normalise_team(t, rank_field="rank") for t in teams_raw]
    out = {
        "updated": _now_iso(),
        "competition": league_info.get("name", slug),
        "stage": "League Table",
        "type": "league",
        "season": league_info.get("season"),
        "standings": standings,
        "fixtures": [],
        "results": [],
    }
    _write(STANDINGS_DIR / f"{slug}.json", out)


def _normalise_team(t: dict, rank_field: str = "rank") -> dict:
    team = t.get("team", {})
    all_stats = t.get("all", {})
    goals = all_stats.get("goals", {})
    form_str = t.get("form", "") or ""

    return {
        "pos": t.get(rank_field, 0),
        "team": team.get("name", ""),
        "flag": "",  # flags are added manually or via team lookup
        "played": all_stats.get("played", 0),
        "won": all_stats.get("win", 0),
        "drawn": all_stats.get("draw", 0),
        "lost": all_stats.get("lose", 0),
        "gf": goals.get("for", 0),
        "ga": goals.get("against", 0),
        "gd": t.get("goalsDiff", 0),
        "points": t.get("points", 0),
        "form": list(form_str[-5:].upper()),
        "qualified": False,
    }


# ── Fixtures for a competition ──────────────────────────────────────────────
def fetch_fixtures(league_id: int, season: int, slug: str, next_n: int = 10):
    print(f"→ Upcoming fixtures: {slug}…")
    data = _get("/fixtures", {"league": league_id, "season": season, "next": next_n})
    if data is None:
        return []
    return [_normalise_fixture(f) for f in data.get("response", [])]


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    args = set(sys.argv[1:])
    live_only = "--live-only" in args
    standings_only = "--standings" in args

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STANDINGS_DIR.mkdir(parents=True, exist_ok=True)

    if not API_KEY:
        print("⚠  FOOTBALL_API_KEY not set — writing empty live.json only")
        _write_live_empty()
        return

    print(f"🟢 Football data update — {_now_iso()}")
    print(f"   API key: {API_KEY[:6]}…{API_KEY[-4:]}")

    if not standings_only:
        fetch_live()
        time.sleep(2)

    if not live_only:
        for league_id, season in DAILY_STANDINGS:
            slug = COMPETITION_MAP.get(league_id, f"comp-{league_id}")
            fetch_standings(league_id, season, slug)
            time.sleep(6)  # respect 10 calls/min rate limit

    print(f"\n✅ Done — {_now_iso()}")


if __name__ == "__main__":
    main()
