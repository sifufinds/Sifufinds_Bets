#!/usr/bin/env python3
"""
update_leagues.py — Multi-source football aggregator for SifuFinds

Sources:
  1. football-data.org v4  (primary — World Cup + UCL + top 5 EU + Copa Lib + Brasileirao)
  2. ESPN unofficial API   (secondary — African leagues + live-minute enrichment, no auth needed)

Modes:
  python3 update_leagues.py               # full: FD + ESPN (respects FD 25-min throttle)
  python3 update_leagues.py --espn-only   # live patch: ESPN only, merges into existing JSON
  python3 update_leagues.py --force-fd    # force FD call even if < 25 min since last call

Output: data/matches_live.json

Env:
  FD_TOKEN  — football-data.org API token (free tier, 100 req/day)
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("ERROR: requests not installed — pip install requests")

ROOT           = Path(__file__).parent
OUT_FILE       = ROOT / "data" / "matches_live.json"
STANDINGS_FILE = ROOT / "data" / "wc_standings.json"
NOW            = datetime.now(timezone.utc)
TODAY          = NOW.strftime("%Y-%m-%d")

# ── football-data.org ─────────────────────────────────────────────────────────
FD_TOKEN   = os.getenv("FD_TOKEN", "530624f0ac724d53ad5ef067d9739ef5")
FD_BASE    = "https://api.football-data.org/v4"
FD_HEADERS = {"X-Auth-Token": FD_TOKEN}

# FD is throttled to 100 req/day free — only call it when last call was > 25 min ago
FD_THROTTLE_SECS = 1500  # 25 min

# ── Competition display priority (lower number = shown first on page) ─────────
COMP_PRIORITY: dict[str | int, int] = {
    # football-data.org IDs
    2000:               1,   # FIFA World Cup 2026
    2001:               2,   # UEFA Champions League
    2021:               3,   # Premier League
    2014:               4,   # La Liga
    2002:               5,   # Bundesliga
    2019:               6,   # Serie A
    2015:               7,   # Ligue 1
    2017:               8,   # Primeira Liga
    2003:               9,   # Eredivisie
    2016:               10,  # Championship
    2013:               11,  # Brasileirao Série A
    2018:               12,  # European Championship
    2152:               13,  # Copa Libertadores
    # ESPN virtual IDs (espn:<slug>)
    "espn:caf.afcon":   14,
    "espn:caf.cl":      15,
    "espn:caf.cc":      16,
    "espn:rsa.1":       17,
    "espn:nig.1":       18,
    "espn:gha.1":       19,
    "espn:ken.1":       20,
    "espn:uga.1":       21,
    "espn:tan.1":       22,
    "espn:zim.1":       23,
    "espn:zam.1":       24,
    "espn:eth.1":       25,
    "espn:mar.1":       26,
    "espn:egy.1":       27,
}

# ── ESPN leagues to fetch (slug, display name, fd_comp_id_if_overlap) ─────────
# fd_comp_id: if set, this ESPN league overlaps with an FD competition — only
# fetch from ESPN today (for live-minute enrichment), not the full window.
ESPN_LEAGUES: list[tuple[str, str, int | None]] = [
    # African national leagues
    ("rsa.1",    "Premier Soccer League",       None),
    ("nig.1",    "NPFL",                        None),
    ("gha.1",    "Ghana Premier League",        None),
    ("ken.1",    "Kenyan Premier League",       None),
    ("uga.1",    "Uganda Premier League",       None),
    ("tan.1",    "Tanzania Premier League",     None),
    ("zim.1",    "Zimbabwe PSL",                None),
    ("zam.1",    "Zambia Super League",         None),
    ("eth.1",    "Ethiopian Premier League",    None),
    ("mar.1",    "Botola Pro",                  None),
    ("egy.1",    "Egyptian Premier League",     None),
    # African international competitions
    ("caf.afcon","AFCON 2025",                  None),
    ("caf.cl",   "CAF Champions League",        None),
    ("caf.cc",   "CAF Confederation Cup",       None),
    # World Cup — ESPN for live-minute data to enrich FD results
    ("fifa.world","FIFA World Cup 2026",        2000),
]

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

# ESPN status → our normalised status string (same as football-data.org style)
ESPN_STATUS_MAP: dict[str, str] = {
    "STATUS_SCHEDULED":          "SCHEDULED",
    "STATUS_IN_PROGRESS":        "IN_PLAY",
    "STATUS_HALFTIME":           "PAUSED",
    "STATUS_HALF_TIME":          "PAUSED",
    "STATUS_FULL_TIME":          "FINISHED",
    "STATUS_FINAL":              "FINISHED",
    "STATUS_END_PERIOD":         "FINISHED",
    "STATUS_EXTRA_TIME":         "EXTRA_TIME",
    "STATUS_PENALTY":            "PENALTY_SHOOTOUT",
    "STATUS_SUSPENDED":          "SUSPENDED",
    "STATUS_POSTPONED":          "POSTPONED",
    "STATUS_CANCELLED":          "CANCELLED",
    "STATUS_ABANDONED":          "CANCELLED",
    "STATUS_DELAYED":            "SCHEDULED",
    "STATUS_TBD":                "TIMED",
    "STATUS_RAIN_DELAY":         "SUSPENDED",
}

LIVE_STATUSES = {"IN_PLAY", "PAUSED", "EXTRA_TIME", "PENALTY_SHOOTOUT"}


# ── Utilities ─────────────────────────────────────────────────────────────────
def _log(msg: str) -> None:
    print(msg, flush=True)


def _priority(comp_id: int | str) -> int:
    return COMP_PRIORITY.get(comp_id, 50)


def _norm_name(name: str) -> str:
    """Collapse team name to alphanum for fuzzy deduplication."""
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _ko_fields(utc_dt: str) -> tuple[str, str, str]:
    """Return (date YYYY-MM-DD, time HH:MM UTC, date label d Mon)."""
    try:
        ko = datetime.fromisoformat(utc_dt.replace("Z", "+00:00"))
        return ko.strftime("%Y-%m-%d"), ko.strftime("%H:%M UTC"), ko.strftime("%-d %b")
    except Exception:
        return "", "", ""


# ── football-data.org fetch ───────────────────────────────────────────────────
def _fd_should_call(force: bool) -> bool:
    if force:
        return True
    if not OUT_FILE.exists():
        return True
    try:
        data = json.loads(OUT_FILE.read_text(encoding="utf-8"))
        last_fd = data.get("lastFdUpdate", "")
        if not last_fd:
            return True
        last = datetime.fromisoformat(last_fd)
        age  = (NOW - last.replace(tzinfo=timezone.utc) if last.tzinfo is None
                else NOW - last)
        return age.total_seconds() > FD_THROTTLE_SECS
    except Exception:
        return True


def _fd_fetch(date_from: str, date_to: str) -> list[dict]:
    url = f"{FD_BASE}/matches"
    try:
        r = requests.get(
            url, headers=FD_HEADERS,
            params={"dateFrom": date_from, "dateTo": date_to},
            timeout=25,
        )
        _log(f"  FD /matches {date_from}→{date_to} → HTTP {r.status_code}")
        if r.status_code == 429:
            _log("  ⚠ FD rate-limited — skipping this call")
            return []
        r.raise_for_status()
        return r.json().get("matches", [])
    except Exception as exc:
        _log(f"  FD ERROR: {exc}")
        return []


def _fd_norm(m: dict) -> dict:
    comp  = m.get("competition", {})
    home  = m.get("homeTeam", {})
    away  = m.get("awayTeam", {})
    score = m.get("score", {})
    ft    = score.get("fullTime", {})
    ht    = score.get("halfTime", {})

    utc_dt              = m.get("utcDate", "")
    date_s, time_s, dl = _ko_fields(utc_dt)

    return {
        "id":        f"fd:{m.get('id')}",
        "source":    "fd",
        "compId":    comp.get("id"),
        "compName":  comp.get("name", ""),
        "compCode":  comp.get("code", ""),
        "emblem":    comp.get("emblem", ""),
        "matchday":  m.get("matchday"),
        "stage":     m.get("stage", ""),
        "group":     m.get("group"),
        "utcDate":   utc_dt,
        "date":      date_s,
        "dateLabel": dl,
        "time":      time_s,
        "status":    m.get("status", "SCHEDULED"),
        "minute":    m.get("minute"),
        "home":      home.get("shortName") or home.get("name") or "TBD",
        "homeFull":  home.get("name", ""),
        "homeCrest": home.get("crest", ""),
        "homeNorm":  _norm_name(home.get("name") or ""),
        "away":      away.get("shortName") or away.get("name") or "TBD",
        "awayFull":  away.get("name", ""),
        "awayCrest": away.get("crest", ""),
        "awayNorm":  _norm_name(away.get("name") or ""),
        "hScore":    ft.get("home"),
        "aScore":    ft.get("away"),
        "hHT":       ht.get("home"),
        "aHT":       ht.get("away"),
    }


# ── ESPN unofficial API fetch ─────────────────────────────────────────────────
def _espn_fetch_day(slug: str, date_str: str) -> list[dict]:
    date_key = date_str.replace("-", "")
    url = f"{ESPN_BASE}/{slug}/scoreboard"
    try:
        r = requests.get(
            url,
            params={"dates": date_key, "limit": 200},
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        _log(f"  ESPN /{slug} {date_str} → HTTP {r.status_code}")
        if r.status_code in (404, 400):
            return []  # league not available — silent skip
        r.raise_for_status()
        return r.json().get("events", [])
    except Exception as exc:
        _log(f"  ESPN ERROR ({slug} {date_str}): {exc}")
        return []


def _espn_norm(ev: dict, slug: str, comp_name: str) -> dict | None:
    comps = ev.get("competitions", [])
    if not comps:
        return None
    c = comps[0]

    competitors = c.get("competitors", [])
    home = next((x for x in competitors if x.get("homeAway") == "home"), None)
    away = next((x for x in competitors if x.get("homeAway") == "away"), None)
    if not home or not away:
        return None

    status_obj  = c.get("status", {})
    status_type = status_obj.get("type", {})
    status_name = status_type.get("name", "STATUS_SCHEDULED")
    our_status  = ESPN_STATUS_MAP.get(status_name, "SCHEDULED")

    # Live minute from clock or shortDetail (e.g. "45'")
    minute: int | None = None
    if our_status in LIVE_STATUSES:
        clock = status_obj.get("clock")
        if clock is not None:
            try:
                minute = int(float(clock) // 60) if float(clock) >= 60 else int(float(clock))
            except Exception:
                pass
        if minute is None:
            detail = status_type.get("shortDetail", "")
            m_match = re.match(r"(\d+)'", detail)
            if m_match:
                minute = int(m_match.group(1))

    utc_dt              = c.get("date") or ev.get("date", "")
    date_s, time_s, dl = _ko_fields(utc_dt)

    ht  = home.get("team", {})
    at  = away.get("team", {})
    hs  = home.get("score")
    as_ = away.get("score")
    if our_status == "SCHEDULED":
        hs = as_ = None

    return {
        "id":        f"espn:{ev.get('id')}",
        "source":    "espn",
        "compId":    f"espn:{slug}",
        "compName":  comp_name,
        "compCode":  slug.upper().replace(".", "_"),
        "emblem":    "",
        "matchday":  None,
        "stage":     "",
        "group":     None,
        "utcDate":   utc_dt,
        "date":      date_s,
        "dateLabel": dl,
        "time":      time_s,
        "status":    our_status,
        "minute":    minute,
        "home":      ht.get("abbreviation") or ht.get("displayName") or "TBD",
        "homeFull":  ht.get("displayName", ""),
        "homeCrest": ht.get("logo", ""),
        "homeNorm":  _norm_name(ht.get("displayName") or ""),
        "away":      at.get("abbreviation") or at.get("displayName") or "TBD",
        "awayFull":  at.get("displayName", ""),
        "awayCrest": at.get("logo", ""),
        "awayNorm":  _norm_name(at.get("displayName") or ""),
        "hScore":    int(hs)  if hs  is not None else None,
        "aScore":    int(as_) if as_ is not None else None,
        "hHT":       None,
        "aHT":       None,
    }


# ── Merge FD (primary) + ESPN (supplement) ────────────────────────────────────
def _merge(fd_matches: list[dict], espn_matches: list[dict]) -> list[dict]:
    """
    FD is authoritative for competitions it covers.
    ESPN supplements:
      - Adds African league matches not in FD.
      - Enriches FD WC/UCL matches with live `minute` where FD lags.
    Handles existing-JSON entries that predate the homeNorm/awayNorm fields.
    """
    # Ensure every FD match has dedup keys (existing JSON may lack them)
    for m in fd_matches:
        if "homeNorm" not in m:
            m["homeNorm"] = _norm_name(m.get("homeFull") or m.get("home") or "")
        if "awayNorm" not in m:
            m["awayNorm"] = _norm_name(m.get("awayFull") or m.get("away") or "")
        if "date" not in m:
            m["date"] = (m.get("utcDate") or "")[:10]

    # Index FD by dedup key
    fd_idx: dict[tuple, int] = {}
    for i, m in enumerate(fd_matches):
        key = (m["homeNorm"], m["awayNorm"], m["date"])
        fd_idx[key] = i

    for em in espn_matches:
        if not em:
            continue
        key = (em["homeNorm"], em["awayNorm"], em["date"])
        if key in fd_idx:
            fd_m = fd_matches[fd_idx[key]]
            # Enrich live minute if FD doesn't have it yet
            if fd_m.get("minute") is None and em.get("minute") is not None:
                fd_m["minute"] = em["minute"]
            # Enrich score if FD hasn't updated yet (live lag)
            if em.get("hScore") is not None:
                fd_m["hScore"] = em["hScore"]
                fd_m["aScore"] = em["aScore"]
            # Sync status: upgrade SCHEDULED→LIVE or demote stale LIVE→FINISHED
            if fd_m["status"] == "SCHEDULED" and em["status"] in LIVE_STATUSES:
                fd_m["status"] = em["status"]
            elif fd_m["status"] in LIVE_STATUSES and em["status"] in ("FINISHED", "AWARDED"):
                fd_m["status"] = em["status"]
        else:
            fd_matches.append(em)

    return fd_matches


# ── WC2026 group standings ────────────────────────────────────────────────────
def _fetch_wc_standings() -> None:
    """Fetch WC2026 group standings from football-data.org and write to wc_standings.json."""
    _log("→ Fetching WC2026 group standings…")
    try:
        r = requests.get(
            f"{FD_BASE}/competitions/2000/standings",
            headers=FD_HEADERS,
            timeout=20,
        )
        _log(f"  FD /competitions/2000/standings → HTTP {r.status_code}")
        if r.status_code == 429:
            _log("  ⚠ FD rate-limited — skipping standings")
            return
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        _log(f"  FD standings ERROR: {exc}")
        return

    comp   = data.get("competition", {})
    season = data.get("season", {})
    raw_groups = data.get("standings", [])

    groups: list[dict] = []
    for sg in raw_groups:
        rows: list[dict] = []
        for row in sg.get("table", []):
            team = row.get("team", {})
            rows.append({
                "pos":    row.get("position", 0),
                "id":     team.get("id"),
                "team":   team.get("shortName") or team.get("name", ""),
                "tla":    team.get("tla", ""),
                "crest":  team.get("crest", ""),
                "played": row.get("playedGames", 0),
                "won":    row.get("won", 0),
                "draw":   row.get("draw", 0),
                "lost":   row.get("lost", 0),
                "gf":     row.get("goalsFor", 0),
                "ga":     row.get("goalsAgainst", 0),
                "gd":     row.get("goalDifference", 0),
                "points": row.get("points", 0),
                "form":   row.get("form") or "",
            })
        if rows:
            groups.append({
                "group":  sg.get("group", ""),
                "stage":  sg.get("stage", ""),
                "table":  rows,
            })

    out = {
        "updated":     NOW.isoformat(),
        "competition": comp.get("name", "FIFA World Cup 2026"),
        "season":      season.get("currentMatchday"),
        "stage":       raw_groups[0].get("stage", "") if raw_groups else "",
        "groups":      groups,
    }
    STANDINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STANDINGS_FILE.write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    _log(f"  ✓ {STANDINGS_FILE.relative_to(ROOT)} ({len(groups)} groups)")


# ── Build output structure ────────────────────────────────────────────────────
def _build_output(
    matches: list[dict],
    date_from: str,
    date_to: str,
    last_fd_update: str,
) -> dict:
    # Group by date
    by_date: dict[str, list[dict]] = {}
    for m in matches:
        day = (m.get("date") or "")[:10]
        if day:
            by_date.setdefault(day, []).append(m)

    # Group by competition
    comp_map: dict[str | int, dict] = {}
    for m in matches:
        cid = m["compId"]
        if cid not in comp_map:
            comp_map[cid] = {
                "id":       cid,
                "name":     m["compName"],
                "code":     m["compCode"],
                "emblem":   m.get("emblem", ""),
                "priority": _priority(cid),
                "matches":  [],
            }
        comp_map[cid]["matches"].append(m)

    competitions = sorted(comp_map.values(), key=lambda c: (c["priority"], c["name"]))

    live_count = sum(1 for m in matches if m["status"] in LIVE_STATUSES)
    wc_live    = any(
        m["status"] in LIVE_STATUSES
        and m.get("compId") in (2000, "espn:fifa.world")
        for m in matches
    )

    return {
        "updated":       NOW.isoformat(),
        "lastFdUpdate":  last_fd_update,
        "dateFrom":      date_from,
        "dateTo":        date_to,
        "total":         len(matches),
        "liveCount":     live_count,
        "wcLive":        wc_live,
        "competitions":  competitions,
        "byDate":        by_date,
    }


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    args      = set(sys.argv[1:])
    espn_only = "--espn-only" in args
    force_fd  = "--force-fd" in args

    date_from = TODAY
    date_to   = (NOW + timedelta(days=6)).strftime("%Y-%m-%d")

    _log(f"🟢 Leagues update — {NOW.isoformat()}")
    _log(f"   Mode: {'espn-only (live patch)' if espn_only else 'full (FD + ESPN)'}")

    # ── Load existing JSON as base (for espn-only live-patch mode) ────────────
    existing: dict = {}
    last_fd_update = ""
    if OUT_FILE.exists():
        try:
            existing = json.loads(OUT_FILE.read_text(encoding="utf-8"))
            last_fd_update = existing.get("lastFdUpdate", "")
        except Exception:
            pass

    # ── football-data.org (primary) ───────────────────────────────────────────
    fd_matches: list[dict] = []
    if not espn_only:
        if _fd_should_call(force_fd):
            raw = _fd_fetch(date_from, date_to)
            _log(f"   FD: {len(raw)} matches returned")
            fd_matches     = [_fd_norm(m) for m in raw]
            last_fd_update = NOW.isoformat()
            # Fetch WC group standings on every full FD call
            _fetch_wc_standings()
        else:
            # Re-use FD data from last full run, just patch live scores via ESPN
            _log(f"   FD: skipped (last call {last_fd_update or 'unknown'} — throttled)")
            # Flatten existing byDate into fd_matches as base
            for day_matches in existing.get("byDate", {}).values():
                for m in day_matches:
                    if m.get("source") == "fd":
                        fd_matches.append(m)
    else:
        # espn-only: start from the existing FD + African data
        for day_matches in existing.get("byDate", {}).values():
            fd_matches.extend(day_matches)

    # ── ESPN (secondary — African leagues + WC live enrichment) ──────────────
    espn_matches: list[dict] = []

    # For espn-only / live patch: fetch today + tomorrow; for full: same window
    espn_window = [TODAY, (NOW + timedelta(days=1)).strftime("%Y-%m-%d")]

    for slug, name, fd_comp_id in ESPN_LEAGUES:
        # Overlap competitions (e.g. World Cup): today only for enrichment
        days = [TODAY] if fd_comp_id is not None else espn_window
        for day in days:
            events = _espn_fetch_day(slug, day)
            for ev in events:
                norm = _espn_norm(ev, slug, name)
                if norm and norm["date"]:
                    espn_matches.append(norm)
            time.sleep(0.12)

    _log(f"   ESPN: {len(espn_matches)} matches from {len(ESPN_LEAGUES)} leagues")

    # ── Merge ─────────────────────────────────────────────────────────────────
    merged = _merge(fd_matches, espn_matches)
    _log(f"   Merged: {len(merged)} total matches")

    # ── Build and write output ─────────────────────────────────────────────────
    out = _build_output(merged, date_from, date_to, last_fd_update)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    _log(f"   ✓ {OUT_FILE.relative_to(ROOT)}")
    _log(f"   {out['total']} matches · {out['liveCount']} live · {len(out['competitions'])} competitions")
    _log(f"   WC2026 live: {out['wcLive']}")
    _log(f"✅ Done — {NOW.isoformat()}")


if __name__ == "__main__":
    main()
