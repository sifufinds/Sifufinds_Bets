#!/usr/bin/env python3
"""
update_football_data.py — SifuFinds Football Data Updater
Uses SportAPI7 (sportapi7.p.rapidapi.com) — SofaScore-based API.

Key design: GET /api/v1/sport/football/scheduled-events/{date} returns ALL
matches for the day in one call, including live scores.  Live data therefore
costs exactly 1 API call per 15-min refresh rather than one per match.

Usage:
  python3 update_football_data.py             # full (live + standings)
  python3 update_football_data.py --live-only # live scores only (1 call)
  python3 update_football_data.py --standings # standings only

Env vars:
  FOOTBALL_API_KEY  — RapidAPI key for sportapi7.p.rapidapi.com
                      Add as GitHub Actions secret: FOOTBALL_API_KEY
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    sys.exit("ERROR: requests not installed — pip install requests")

# ── Paths ───────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).parent
DATA_DIR     = ROOT / "data" / "football"
STANDINGS_DIR = DATA_DIR / "standings"
MAP_FILE     = DATA_DIR / "tournament_map.json"   # persisted tournament → season IDs

# ── API config ───────────────────────────────────────────────────────────────
API_KEY   = os.getenv("FOOTBALL_API_KEY", "")
BASE_URL  = "https://sportapi7.p.rapidapi.com"
HOST      = "sportapi7.p.rapidapi.com"

# ── Slug → (uniqueTournament ID, seed season ID) ────────────────────────────
# IDs are SportAPI7 / SofaScore uniqueTournament IDs.
# The script auto-discovers real season IDs from today's events and persists
# them in data/football/tournament_map.json for future runs.
PRIORITY_COMPS: dict[str, tuple[int, int | None]] = {
    # slug:                  (uniqueTournament_id, seed_season_id_or_None)
    "world-cup-2026":        (16,   None),
    "champions-league":      (7,    None),
    "europa-league":         (679,  None),
    "conference-league":     (17015, None),
    "premier-league":        (17,   None),
    "championship":          (18,   None),
    "fa-cup":                (19,   None),
    "laliga":                (8,    None),
    "bundesliga":            (35,   None),
    "serie-a":               (23,   None),
    "ligue-1":               (34,   None),
    "eredivisie":            (37,   None),
    "primeira-liga":         (238,  None),
    "pro-league":            (38,   None),
    "super-lig":             (52,   None),
    "scottish-pl":           (36,   None),
    "afcon":                 (180,  None),
    "caf-champions-league":  (182,  None),
    "caf-confederation-cup": (183,  None),
    "copa-libertadores":     (384,  None),
    "copa-sudamericana":     (480,  None),
    "mls":                   (242,  None),
    "liga-mx":               (9,    None),
    "brasileirao":           (325,  None),
    "liga-profesional":      (155,  None),
    "psl":                   (383,  None),
    "npfl":                  (1627, None),
    "gpl":                   (1628, None),
    "botola":                (229,  None),
    "kpl":                   (1644, None),
    "wsl":                   (50,   None),
    "liga-f":                (386,  None),
    "wwc-2023":              (290,  None),
    "wafcon":                (181,  None),
    "j-league":              (196,  None),
    "k-league":              (55,   None),
    "saudi-pl":              (955,  None),
}

# Status normalisation: SportAPI7 type → our format
_STATUS_MAP = {
    "notstarted":  "NS",
    "inprogress":  "LIVE",
    "finished":    "FT",
    "cancelled":   "CANC",
    "postponed":   "PPD",
    "interrupted": "INT",
    "overtime":    "ET",
    "penalties":   "PEN",
    "awarded":     "AWD",
    "halftime":    "HT",
}

# Flags for common countries (extend as needed)
_FLAGS: dict[str, str] = {
    "england": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "nigeria": "🇳🇬", "kenya": "🇰🇪", "ghana": "🇬🇭", "south africa": "🇿🇦",
    "morocco": "🇲🇦", "egypt": "🇪🇬", "senegal": "🇸🇳", "algeria": "🇩🇿",
    "cameroon": "🇨🇲", "ivory coast": "🇨🇮", "côte d'ivoire": "🇨🇮",
    "tanzania": "🇹🇿", "uganda": "🇺🇬", "zambia": "🇿🇲", "zimbabwe": "🇿🇼",
    "ethiopia": "🇪🇹", "rwanda": "🇷🇼", "angola": "🇦🇴", "dr congo": "🇨🇩",
    "botswana": "🇧🇼", "namibia": "🇳🇦", "malawi": "🇲🇼", "mozambique": "🇲🇿",
    "spain": "🇪🇸", "germany": "🇩🇪", "france": "🇫🇷", "italy": "🇮🇹",
    "netherlands": "🇳🇱", "portugal": "🇵🇹", "belgium": "🇧🇪", "turkey": "🇹🇷",
    "brazil": "🇧🇷", "argentina": "🇦🇷", "colombia": "🇨🇴", "uruguay": "🇺🇾",
    "mexico": "🇲🇽", "usa": "🇺🇸", "united states": "🇺🇸", "canada": "🇨🇦",
    "japan": "🇯🇵", "south korea": "🇰🇷", "australia": "🇦🇺", "saudi arabia": "🇸🇦",
    "iran": "🇮🇷", "iraq": "🇮🇶", "qatar": "🇶🇦", "indonesia": "🇮🇩",
    "croatia": "🇭🇷", "serbia": "🇷🇸", "switzerland": "🇨🇭", "denmark": "🇩🇰",
    "sweden": "🇸🇪", "norway": "🇳🇴", "poland": "🇵🇱", "austria": "🇦🇹",
    "ukraine": "🇺🇦", "new zealand": "🇳🇿", "paraguay": "🇵🇾", "ecuador": "🇪🇨",
    "venezuela": "🇻🇪", "chile": "🇨🇱", "peru": "🇵🇪", "bolivia": "🇧🇴",
    "panama": "🇵🇦", "costa rica": "🇨🇷", "honduras": "🇭🇳", "jamaica": "🇯🇲",
    "slovenia": "🇸🇮", "slovakia": "🇸🇰", "czech republic": "🇨🇿",
    "hungary": "🇭🇺", "romania": "🇷🇴", "greece": "🇬🇷", "uzbekistan": "🇺🇿",
    "ghana": "🇬🇭", "tunisia": "🇹🇳", "mali": "🇲🇱", "guinea": "🇬🇳",
    "dr congo": "🇨🇩", "congo": "🇨🇬", "gabon": "🇬🇦",
    "bosnia-herzegovina": "🇧🇦", "bosnia": "🇧🇦",
    "scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
}


def _flag(country_name: str) -> str:
    return _FLAGS.get(country_name.lower().strip(), "")


# ── HTTP ─────────────────────────────────────────────────────────────────────
def _headers() -> dict[str, str]:
    return {
        "X-RapidAPI-Key":  API_KEY,
        "X-RapidAPI-Host": HOST,
        "Accept":          "application/json",
    }


def _get(path: str, params: dict[str, Any] | None = None) -> dict | None:
    if not API_KEY:
        return None
    url = f"{BASE_URL}{path}"
    try:
        r = requests.get(url, headers=_headers(), params=params or {}, timeout=20)
        r.raise_for_status()
        remaining = r.headers.get("X-RateLimit-Requests-Remaining", "?")
        reset_in  = r.headers.get("X-RateLimit-Requests-Reset", "?")
        print(f"  GET {path} → {r.status_code}  remaining={remaining}  reset={reset_in}s")
        return r.json()
    except Exception as exc:
        print(f"  ERROR {path}: {exc}", file=sys.stderr)
        return None


# ── Atomic file write ─────────────────────────────────────────────────────────
def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    print(f"  ✓ {path.relative_to(ROOT)}")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ts_to_dt(ts: int | None) -> datetime | None:
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)


# ── Tournament map (persisted slug → ids) ─────────────────────────────────────
def _load_map() -> dict[str, dict]:
    if MAP_FILE.exists():
        try:
            return json.loads(MAP_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_map(m: dict[str, dict]) -> None:
    _write(MAP_FILE, m)


# ── Normalise a SportAPI7 event into our common format ────────────────────────
def _norm_event(ev: dict) -> dict:
    home    = ev.get("homeTeam", {})
    away    = ev.get("awayTeam", {})
    hs      = ev.get("homeScore", {})
    as_     = ev.get("awayScore", {})
    st      = ev.get("status", {})
    tourn   = ev.get("tournament", {})
    unique  = tourn.get("uniqueTournament", {})
    season  = ev.get("season", {})

    status_type = st.get("type", "notstarted")
    status_desc = st.get("description", "")
    status_out  = _STATUS_MAP.get(status_type, status_type.upper()[:4])

    # Derive match minute from status description or elapsed calculation
    minute: int | None = None
    ts_start = ev.get("time", {}).get("currentPeriodStartTimestamp")
    if status_type == "inprogress" and ts_start:
        elapsed_s = int(datetime.now(timezone.utc).timestamp()) - ts_start
        period    = status_desc.lower()
        base      = 45 if "2nd" in period else 0
        minute    = min(base + max(0, elapsed_s // 60), 120)

    ko_dt = _ts_to_dt(ev.get("startTimestamp"))

    home_name = home.get("name", "")
    away_name = away.get("name", "")
    home_country = home.get("country", {}).get("name", "") or home.get("slug", "")
    away_country = away.get("country", {}).get("name", "") or away.get("slug", "")

    return {
        "id":             ev.get("id"),
        "competition":    unique.get("name") or tourn.get("name", ""),
        "uniqueTournamentId": unique.get("id"),
        "seasonId":       season.get("id"),
        "round":          ev.get("roundInfo", {}).get("name", ""),
        "home":           home_name,
        "hFlag":          _flag(home_country) or _flag(home_name),
        "away":           away_name,
        "aFlag":          _flag(away_country) or _flag(away_name),
        "hScore":         hs.get("current"),
        "aScore":         as_.get("current"),
        "status":         status_out,
        "statusDesc":     status_desc,
        "minute":         minute,
        "date":           ko_dt.strftime("%-d %b") if ko_dt else "",
        "time":           ko_dt.strftime("%H:%M UTC") if ko_dt else "",
        "venue":          ev.get("venue", {}).get("name", ""),
    }


# ── Fetch ALL today's matches (1 API call) ────────────────────────────────────
def fetch_today_all(today: str, tmap: dict[str, dict]) -> list[dict]:
    """
    One call returns every football match scheduled today with live scores.
    We also harvest tournament IDs from the events to fill gaps in tmap.
    """
    print(f"→ Fetching all football matches for {today}…")
    data = _get(f"/api/v1/sport/football/scheduled-events/{today}")
    if data is None:
        return []

    events_raw = data.get("events", [])
    events     = [_norm_event(e) for e in events_raw]

    # Harvest tournament → season IDs we haven't seen before
    for ev_raw, ev in zip(events_raw, events):
        uid = ev.get("uniqueTournamentId")
        sid = ev.get("seasonId")
        if not uid or not sid:
            continue
        name_lc = ev.get("competition", "").lower()
        # Check if any of our slugs matches this tournament ID
        for slug, (known_uid, _) in PRIORITY_COMPS.items():
            if known_uid == uid and slug not in tmap:
                tmap[slug] = {"uniqueTournamentId": uid, "seasonId": sid}
                print(f"  discovered: {slug} → uid={uid} sid={sid}")

    return events


def write_live_json(events: list[dict]) -> None:
    live_statuses = {"LIVE", "ET", "PEN", "HT"}
    live_events   = [e for e in events if e["status"] in live_statuses]
    out = {
        "updated":   _now_iso(),
        "liveCount": len(live_events),
        "matches":   events,          # all today's matches; page filters by status
    }
    _write(DATA_DIR / "live.json", out)


def write_today_json(events: list[dict], today: str) -> None:
    _write(DATA_DIR / "today.json", {
        "updated":  _now_iso(),
        "date":     today,
        "count":    len(events),
        "fixtures": events,
    })


# ── Fetch standings for one competition ───────────────────────────────────────
def fetch_standings(slug: str, uid: int, sid: int) -> None:
    print(f"→ Standings: {slug}  (uid={uid} sid={sid})…")
    data = _get(
        f"/api/v1/unique-tournament/{uid}/season/{sid}/standings/total"
    )
    if not data:
        return

    standings_list = data.get("standings", [])
    if not standings_list:
        print(f"  No standings rows for {slug}")
        return

    comp_name = standings_list[0].get("name") or slug
    is_groups = len(standings_list) > 1 or (
        standings_list[0].get("name", "").lower().startswith("group")
    )

    if is_groups:
        _write_group_standings(slug, comp_name, standings_list)
    else:
        _write_league_standings(slug, comp_name, standings_list[0].get("rows", []))


def _write_group_standings(slug: str, comp_name: str, standings_list: list) -> None:
    groups = []
    for group in standings_list:
        group_name = group.get("name", f"Group {len(groups)+1}")
        rows       = group.get("rows", [])
        teams      = [_norm_standing_row(r, i + 1) for i, r in enumerate(rows)]
        groups.append({"name": group_name, "teams": teams, "fixtures": []})

    _write(STANDINGS_DIR / f"{slug}.json", {
        "updated":     _now_iso(),
        "competition": comp_name,
        "stage":       "Group Stage",
        "type":        "groups",
        "groups":      groups,
    })


def _write_league_standings(slug: str, comp_name: str, rows: list) -> None:
    standings = [_norm_standing_row(r, r.get("position", i + 1)) for i, r in enumerate(rows)]
    _write(STANDINGS_DIR / f"{slug}.json", {
        "updated":     _now_iso(),
        "competition": comp_name,
        "stage":       "League Table",
        "type":        "league",
        "standings":   standings,
        "fixtures":    [],
        "results":     [],
    })


def _norm_standing_row(r: dict, pos: int) -> dict:
    team   = r.get("team", {})
    name   = team.get("name", "")
    ctry   = team.get("country", {}).get("name", "") or team.get("slug", "")

    return {
        "pos":     r.get("position", pos),
        "team":    name,
        "flag":    _flag(ctry) or _flag(name),
        "played":  r.get("matches", 0),
        "won":     r.get("wins", 0),
        "drawn":   r.get("draws", 0),
        "lost":    r.get("losses", 0),
        "gf":      r.get("scoresFor", 0),
        "ga":      r.get("scoresAgainst", 0),
        "gd":      r.get("scoresFor", 0) - r.get("scoresAgainst", 0),
        "points":  r.get("points", 0),
        "form":    [],   # SportAPI7 doesn't return form strings in standings
        "qualified": False,
    }


# ── No-key fallback ────────────────────────────────────────────────────────────
def _write_live_empty() -> None:
    _write(DATA_DIR / "live.json", {
        "updated":   _now_iso(),
        "liveCount": 0,
        "matches":   [],
        "note":      "No API key — set FOOTBALL_API_KEY in .env or GitHub Secrets",
    })


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    args         = set(sys.argv[1:])
    live_only    = "--live-only" in args
    standings_only = "--standings" in args

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STANDINGS_DIR.mkdir(parents=True, exist_ok=True)

    if not API_KEY:
        print("⚠  FOOTBALL_API_KEY not set — writing empty live.json")
        _write_live_empty()
        return

    print(f"🟢 Football update — {_now_iso()}")
    print(f"   Key: {API_KEY[:6]}…{API_KEY[-4:]}")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tmap  = _load_map()

    # ── Live / today ─────────────────────────────────────────────────────────
    if not standings_only:
        events = fetch_today_all(today, tmap)
        write_live_json(events)
        if not live_only:
            write_today_json(events, today)
        _save_map(tmap)

    # ── Standings ─────────────────────────────────────────────────────────────
    if not live_only:
        # Merge hardcoded IDs with anything discovered from today's events
        resolved: dict[str, tuple[int, int]] = {}
        for slug, (uid, seed_sid) in PRIORITY_COMPS.items():
            if slug in tmap:
                resolved[slug] = (tmap[slug]["uniqueTournamentId"], tmap[slug]["seasonId"])
            elif seed_sid is not None:
                resolved[slug] = (uid, seed_sid)
            # else: uid known but season unknown — skip until discovered

        for slug, (uid, sid) in resolved.items():
            fetch_standings(slug, uid, sid)
            time.sleep(2)          # stay well within rate limits

        _save_map(tmap)

    print(f"\n✅ Done — {_now_iso()}")


if __name__ == "__main__":
    main()
