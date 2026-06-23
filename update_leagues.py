#!/usr/bin/env python3
"""
update_leagues.py — Fetch football match data for leagues/index.html

Modes (CLI flag):
  (none)        full — FD 7-day schedule + ESPN African/WC live patch + WC standings
  --espn-only   ESPN live patch only — no FD quota used, patches today+tomorrow
  --force-fd    force FD fetch even if within the 25-min throttle window

Writes:
  data/matches_live.json   — byDate map, liveCount, wcLive, updated timestamp
  data/wc_standings.json   — WC 2026 group tables (full runs only)

FD throttle: skip FD if matches_live.json was written < 25 min ago (saves quota).
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("ERROR: requests not installed — pip install requests")

ROOT      = Path(__file__).parent
OUT_MATCH = ROOT / "data" / "matches_live.json"
OUT_WC    = ROOT / "data" / "wc_standings.json"

FD_TOKEN         = os.getenv("FD_TOKEN", "")
FD_BASE          = "https://api.football-data.org/v4"
FD_THROTTLE_MINS = 25

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

# Competition priority — lower = displayed first on the page
COMP_PRIORITY: dict = {
    2000:             1,   # FIFA World Cup 2026
    2001:             2,   # UEFA Champions League
    2021:             3,   # Premier League
    2014:             4,   # La Liga
    2002:             5,   # Bundesliga
    2019:             6,   # Serie A
    2015:             7,   # Ligue 1
    2017:             8,   # Primeira Liga
    2003:             9,   # Eredivisie
    2016:            10,   # Championship
    2013:            11,   # Brasileirao
    2018:            12,   # EURO
    2152:            13,   # Copa Libertadores
    "espn:caf.afcon": 14,
    "espn:caf.cl":    15,
    "espn:caf.cc":    16,
    "espn:rsa.1":     17,
    "espn:nig.1":     18,
    "espn:gha.1":     19,
    "espn:ken.1":     20,
    "espn:uga.1":     21,
    "espn:tan.1":     22,
    "espn:zim.1":     23,
    "espn:zam.1":     24,
    "espn:eth.1":     25,
    "espn:mar.1":     26,
    "espn:egy.1":     27,
}

# ESPN league slugs for African competitions (plus WC for live-score patching)
ESPN_LEAGUES = [
    # (compId used internally, ESPN slug, display name)
    (2000,             "fifa.world",    "FIFA World Cup 2026"),
    ("espn:caf.afcon", "caf.nations",  "AFCON 2025"),
    ("espn:caf.cl",    "caf.champions","CAF Champions League"),
    ("espn:caf.cc",    "caf.confed",   "CAF Confederation Cup"),
    ("espn:rsa.1",     "rsa.1",        "PSL"),
    ("espn:nig.1",     "nig.1",        "NPFL"),
    ("espn:gha.1",     "gha.1",        "Ghana Premier League"),
    ("espn:ken.1",     "ken.1",        "FKF Premier League"),
    ("espn:uga.1",     "uga.1",        "Uganda Premier League"),
    ("espn:tan.1",     "tan.1",        "Tanzania Premier League"),
    ("espn:zim.1",     "zim.1",        "Zimbabwe PSL"),
    ("espn:zam.1",     "zam.1",        "Zambia Super League"),
    ("espn:eth.1",     "eth.1",        "Ethiopia Premier League"),
    ("espn:mar.1",     "mar.1",        "Botola Pro"),
    ("espn:egy.1",     "egy.1",        "Egyptian Premier League"),
]

LIVE_STATUSES = {"IN_PLAY", "PAUSED", "EXTRA_TIME", "PENALTY_SHOOTOUT"}

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "SifuFinds/2.0 leaguesbot@sifufinds.com"})


# ── FD helpers ────────────────────────────────────────────────────────────────

def _fd_fetch_matches(date_from: str, date_to: str) -> list[dict]:
    try:
        r = SESSION.get(
            f"{FD_BASE}/matches",
            headers={"X-Auth-Token": FD_TOKEN},
            params={"dateFrom": date_from, "dateTo": date_to},
            timeout=25,
        )
        print(f"  FD /matches {date_from}→{date_to} → HTTP {r.status_code}")
        if r.status_code == 429:
            print("  ⚠ FD rate limited — skipping")
            return []
        r.raise_for_status()
        return r.json().get("matches", [])
    except Exception as exc:
        print(f"  FD ERROR: {exc}", file=sys.stderr)
        return []


def _fd_fetch_standings() -> dict | None:
    try:
        r = SESSION.get(
            f"{FD_BASE}/competitions/2000/standings",
            headers={"X-Auth-Token": FD_TOKEN},
            timeout=25,
        )
        print(f"  FD /competitions/2000/standings → HTTP {r.status_code}")
        return r.json() if r.status_code == 200 else None
    except Exception as exc:
        print(f"  FD standings ERROR: {exc}", file=sys.stderr)
        return None


def _fd_normalise(m: dict) -> dict:
    comp  = m.get("competition", {})
    home  = m.get("homeTeam", {})
    away  = m.get("awayTeam", {})
    score = m.get("score", {})
    ft    = score.get("fullTime", {})
    ht    = score.get("halfTime", {})
    utc   = m.get("utcDate", "")
    try:
        ko       = datetime.fromisoformat(utc.replace("Z", "+00:00"))
        time_str = ko.strftime("%H:%M UTC")
        date_str = ko.strftime("%-d %b")
    except Exception:
        time_str = date_str = ""
    return {
        "id":        m.get("id"),
        "source":    "fd",
        "compId":    comp.get("id"),
        "compName":  comp.get("name", ""),
        "compCode":  comp.get("code", ""),
        "emblem":    comp.get("emblem", ""),
        "matchday":  m.get("matchday"),
        "stage":     m.get("stage", ""),
        "group":     m.get("group"),
        "utcDate":   utc,
        "date":      date_str,
        "time":      time_str,
        "status":    m.get("status", "SCHEDULED"),
        "minute":    m.get("minute"),
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


# ── ESPN helpers ──────────────────────────────────────────────────────────────

_ESPN_STATUS: dict[str, str] = {
    "STATUS_SCHEDULED":   "SCHEDULED",
    "STATUS_IN_PROGRESS": "IN_PLAY",
    "STATUS_HALFTIME":    "PAUSED",
    "STATUS_FINAL":       "FINISHED",
    "STATUS_POSTPONED":   "POSTPONED",
    "STATUS_CANCELED":    "CANCELLED",
    "STATUS_SUSPENDED":   "SUSPENDED",
    "STATUS_DELAYED":     "POSTPONED",
    "STATUS_ABANDONED":   "CANCELLED",
    "STATUS_EXTRA_TIME":  "EXTRA_TIME",
    "STATUS_PENALTY":     "PENALTY_SHOOTOUT",
}


def _espn_fetch_day(slug: str, yyyymmdd: str) -> list[dict]:
    try:
        r = SESSION.get(f"{ESPN_BASE}/{slug}/scoreboard", params={"dates": yyyymmdd}, timeout=15)
        return r.json().get("events", []) if r.status_code == 200 else []
    except Exception:
        return []


def _espn_normalise(event: dict, comp_id: str | int, comp_name: str) -> dict | None:
    comps = event.get("competitions", [])
    if not comps:
        return None
    c = comps[0]
    competitors = c.get("competitors", [])
    home = next((x for x in competitors if x.get("homeAway") == "home"), None)
    away = next((x for x in competitors if x.get("homeAway") == "away"), None)
    if not home or not away:
        return None

    stype  = c.get("status", {}).get("type", {})
    status = _ESPN_STATUS.get(stype.get("name", ""), "SCHEDULED")
    detail = stype.get("shortDetail", "")
    minute: int | None = None
    if status == "IN_PLAY" and "'" in detail:
        try:
            minute = int(detail.replace("'", "").strip())
        except ValueError:
            pass

    utc = event.get("date", "")
    try:
        ko       = datetime.fromisoformat(utc.replace("Z", "+00:00"))
        time_str = ko.strftime("%H:%M UTC")
        date_str = ko.strftime("%-d %b")
    except Exception:
        time_str = date_str = ""

    def name(t: dict) -> str:
        tm = t.get("team", {})
        return tm.get("shortDisplayName") or tm.get("abbreviation") or tm.get("displayName") or "TBD"

    def crest(t: dict) -> str:
        logos = t.get("team", {}).get("logos", [])
        return logos[0].get("href", "") if logos else ""

    h_score = a_score = None
    if status in LIVE_STATUSES | {"FINISHED"}:
        try:
            h_score = int(home.get("score", "0"))
            a_score = int(away.get("score", "0"))
        except (ValueError, TypeError):
            pass

    return {
        "id":        f"espn:{event.get('id', '')}",
        "source":    "espn",
        "compId":    comp_id,
        "compName":  comp_name,
        "compCode":  "",
        "emblem":    "",
        "matchday":  None,
        "stage":     "",
        "group":     None,
        "utcDate":   utc,
        "date":      date_str,
        "time":      time_str,
        "status":    status,
        "minute":    minute,
        "home":      name(home),
        "homeFull":  home.get("team", {}).get("displayName", ""),
        "homeCrest": crest(home),
        "away":      name(away),
        "awayFull":  away.get("team", {}).get("displayName", ""),
        "awayCrest": crest(away),
        "hScore":    h_score,
        "aScore":    a_score,
        "hHT":       None,
        "aHT":       None,
    }


def _fetch_espn_leagues(days: int) -> list[dict]:
    now = datetime.now(timezone.utc)
    results: list[dict] = []
    for comp_id, slug, comp_name in ESPN_LEAGUES:
        count = 0
        for i in range(days):
            events = _espn_fetch_day(slug, (now + timedelta(days=i)).strftime("%Y%m%d"))
            for ev in events:
                m = _espn_normalise(ev, comp_id, comp_name)
                if m:
                    results.append(m)
                    count += 1
            time.sleep(0.08)
        if count:
            print(f"  ESPN {slug}: {count} matches")
    return results


# ── WC standings ──────────────────────────────────────────────────────────────

def _write_wc_standings(raw: dict) -> None:
    now    = datetime.now(timezone.utc)
    groups: list[dict] = []
    for s in raw.get("standings", []):
        if s.get("type") != "TOTAL":
            continue
        gname = s.get("group", "")
        if not gname:
            continue
        display = gname.replace("GROUP_", "Group ").replace("_", " ").title()
        table = []
        for row in s.get("table", []):
            team     = row.get("team", {})
            form_raw = row.get("form") or ""
            form     = "".join(f for f in form_raw.replace(",", "") if f in "WDL")[-5:]
            table.append({
                "pos":    row.get("position", 0),
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
                "form":   form,
            })
        if table:
            groups.append({"group": display, "table": table})

    if not groups:
        print("  WC standings: no group data returned")
        return

    OUT_WC.write_text(
        json.dumps({"updated": now.isoformat(), "groups": groups},
                   ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"  ✓ wc_standings.json ({len(groups)} groups)")


# ── Throttle check ────────────────────────────────────────────────────────────

def _fd_is_throttled(force: bool) -> bool:
    if force or not OUT_MATCH.exists():
        return False
    try:
        upd = json.loads(OUT_MATCH.read_text()).get("updated", "")
        if not upd:
            return False
        last     = datetime.fromisoformat(upd)
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        age_mins = (datetime.now(timezone.utc) - last).total_seconds() / 60
        if age_mins < FD_THROTTLE_MINS:
            print(f"  FD throttled — last fetch {age_mins:.1f} min ago (< {FD_THROTTLE_MINS} min)")
            return True
    except Exception:
        pass
    return False


# ── Build and write output ────────────────────────────────────────────────────

def _write_matches(matches: list[dict], now: datetime) -> None:
    by_date: dict[str, list[dict]] = {}
    cutoff  = (now - timedelta(hours=2)).strftime("%Y-%m-%d")

    for m in matches:
        day = m["utcDate"][:10] if m.get("utcDate") else ""
        if not day or day < cutoff:
            continue
        by_date.setdefault(day, []).append(m)

    for day in by_date:
        by_date[day].sort(key=lambda m: (COMP_PRIORITY.get(m["compId"], 50), m["utcDate"]))

    # Deduplicate by id
    seen: set[str] = set()
    for day in by_date:
        deduped = []
        for m in by_date[day]:
            k = str(m["id"])
            if k not in seen:
                seen.add(k)
                deduped.append(m)
        by_date[day] = deduped

    total      = sum(len(v) for v in by_date.values())
    live_count = sum(1 for v in by_date.values() for m in v if m["status"] in LIVE_STATUSES)
    wc_live    = any(m["compId"] == 2000 and m["status"] in LIVE_STATUSES
                     for v in by_date.values() for m in v)

    out = {
        "updated":   now.isoformat(),
        "dateFrom":  now.strftime("%Y-%m-%d"),
        "dateTo":    (now + timedelta(days=6)).strftime("%Y-%m-%d"),
        "total":     total,
        "liveCount": live_count,
        "wcLive":    wc_live,
        "byDate":    by_date,
    }
    OUT_MATCH.parent.mkdir(parents=True, exist_ok=True)
    OUT_MATCH.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  ✓ matches_live.json  {total} matches  {live_count} live  wcLive={wc_live}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args      = set(sys.argv[1:])
    espn_only = "--espn-only" in args
    force_fd  = "--force-fd"  in args
    now       = datetime.now(timezone.utc)
    mode_str  = "espn-only" if espn_only else ("force-fd" if force_fd else "full")
    print(f"🟢 update_leagues.py  mode={mode_str}  {now:%Y-%m-%d %H:%M UTC}")

    matches: list[dict] = []

    if espn_only:
        # Load previous FD matches as the base, then patch with ESPN live data
        if OUT_MATCH.exists():
            try:
                prev = json.loads(OUT_MATCH.read_text())
                for day_list in prev.get("byDate", {}).values():
                    matches.extend(day_list)
                print(f"  Loaded {len(matches)} cached matches from previous run")
            except Exception as exc:
                print(f"  Could not load previous data: {exc}", file=sys.stderr)

        espn_matches = _fetch_espn_leagues(days=2)

        # Build index of existing matches for live-score patching
        fd_index: dict[str, dict] = {}   # "YYYY-MM-DD:home:away" → match
        for m in matches:
            if m.get("source") == "fd":
                day = m["utcDate"][:10]
                key = f"{day}:{m['home'].lower()}:{m['away'].lower()}"
                fd_index[key] = m

        for em in espn_matches:
            if em["compId"] == 2000:
                # Patch WC match live status/score back into the FD match
                day = em["utcDate"][:10]
                key = f"{day}:{em['home'].lower()}:{em['away'].lower()}"
                if key in fd_index:
                    fd_m = fd_index[key]
                    if em["status"] in LIVE_STATUSES or (
                        em["status"] == "FINISHED" and fd_m["status"] not in ("FINISHED", "AWARDED")
                    ):
                        fd_m["status"] = em["status"]
                        fd_m["minute"] = em["minute"]
                        if em["hScore"] is not None:
                            fd_m["hScore"] = em["hScore"]
                            fd_m["aScore"] = em["aScore"]
                    continue
            # Non-WC ESPN match — add if not already present from FD
            matches.append(em)

    else:
        # Full run: fetch FD + ESPN
        throttled = _fd_is_throttled(force_fd)
        if not throttled:
            date_from = now.strftime("%Y-%m-%d")
            date_to   = (now + timedelta(days=6)).strftime("%Y-%m-%d")
            print(f"  Fetching FD matches {date_from}→{date_to} …")
            raw = _fd_fetch_matches(date_from, date_to)
            matches = [_fd_normalise(m) for m in raw]
            print(f"  FD: {len(matches)} matches")

            print("  Fetching WC 2026 standings …")
            raw_st = _fd_fetch_standings()
            if raw_st and raw_st.get("standings"):
                _write_wc_standings(raw_st)
        else:
            # FD throttled — load previous FD data
            if OUT_MATCH.exists():
                try:
                    prev = json.loads(OUT_MATCH.read_text())
                    for day_list in prev.get("byDate", {}).values():
                        matches.extend(day_list)
                    print(f"  FD throttled — using {len(matches)} cached matches")
                except Exception:
                    pass

        # Always complement with ESPN (African leagues not in FD)
        espn_matches = _fetch_espn_leagues(days=7)
        fd_comp_ids  = {m["compId"] for m in matches}
        added = 0
        for em in espn_matches:
            if em["compId"] not in fd_comp_ids:
                matches.append(em)
                added += 1
        if added:
            print(f"  ESPN added {added} African/WC matches")

    _write_matches(matches, now)
    print(f"✅ Done — {now.isoformat()}")


if __name__ == "__main__":
    main()
