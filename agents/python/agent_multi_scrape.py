"""
agent_multi_scrape.py — Hourly multi-source scraper for SifuFinds
Scrapes 6 sites (Flashscore, Sofascore, Livescore, OddsPortal, BetExplorer,
OddsChecker) using Firecrawl, then merges results into data/live.json.

Runs every hour via GitHub Actions alongside agent_live_odds.py (ESPN, every 5 min).
Requires: FIRECRAWL_API_KEY env var.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Config ────────────────────────────────────────────────────────────────────

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LIVE_JSON = REPO_ROOT / "data" / "live.json"
TODAY = datetime.now(timezone.utc).strftime("%Y%m%d")

# Sites to scrape — ordered by data quality for our use case
SOURCES: list[dict[str, Any]] = [
    {
        "name": "sofascore",
        "url": "https://www.sofascore.com/",
        "wait": 4000,
        "priority": 1,
    },
    {
        "name": "flashscore",
        "url": "https://www.flashscore.com/",
        "wait": 4000,
        "priority": 2,
    },
    {
        "name": "livescore",
        "url": "https://www.livescore.com/en/football/",
        "wait": 3000,
        "priority": 3,
    },
    {
        "name": "oddsportal_today",
        "url": f"https://www.oddsportal.com/matches/football/{TODAY}/",
        "wait": 4000,
        "priority": 4,
    },
    {
        "name": "oddsportal_africa",
        "url": "https://www.oddsportal.com/football/africa/",
        "wait": 3000,
        "priority": 4,
    },
    {
        "name": "betexplorer",
        "url": "https://www.betexplorer.com/soccer/",
        "wait": 3000,
        "priority": 5,
    },
]

# Sport key map: league name keywords → internal key
LEAGUE_KEY_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r"world cup|fifa world|championship 2026", re.I), "world"),
    (re.compile(r"caf champions|champions league.*africa|african champions", re.I), "cafl"),
    (re.compile(r"afcon|africa cup|african cup of nations|caf.*qualifier|worldq.*caf", re.I), "afcon"),
    (re.compile(r"npfl|nigeria premier|nigeria.*league", re.I), "local"),
    (re.compile(r"kenya premier|kpl|kenya.*league", re.I), "local"),
    (re.compile(r"ghana premier|gpl|ghana.*league", re.I), "local"),
    (re.compile(r"south africa.*premier|psl|dstv premiership|betway premiership", re.I), "local"),
    (re.compile(r"tanzania premier|ugandan premier|zambia.*league|zimbabwe.*league", re.I), "local"),
    (re.compile(r"nba|wnba|euroleague|ncaa basketball", re.I), "basketball"),
    (re.compile(r"mlb|baseball", re.I), "baseball"),
    (re.compile(r"tennis|atp|wta|french open|wimbledon|us open|roland.?garros", re.I), "tennis"),
    (re.compile(r"cricket|icc|test match|odi|t20", re.I), "cricket"),
    (re.compile(r"rugby|nrl|six nations|super rugby", re.I), "rugby"),
    (re.compile(r"boxing|wbc|wba|wbo|ibf|heavyweight|lightweight", re.I), "boxing"),
    (re.compile(r"premier league|epl|english premier", re.I), "epl"),
    (re.compile(r"champions league|ucl|uefa champions", re.I), "ucl"),
    (re.compile(r"la liga|laliga|primera division.*spain", re.I), "laliga"),
    (re.compile(r"friendly international|international friendly|world.*friendly", re.I), "world"),
    (re.compile(r"africa|african|caf|afcon", re.I), "local"),
]

# Known multi-word country/team slugs (lowercase, hyphenated form)
MULTI_WORD_TEAMS: list[tuple[str, str]] = [
    ("hong-kong", "Hong Kong"),
    ("burkina-faso", "Burkina Faso"),
    ("san-marino", "San Marino"),
    ("costa-rica", "Costa Rica"),
    ("sierra-leone", "Sierra Leone"),
    ("el-salvador", "El Salvador"),
    ("south-korea", "South Korea"),
    ("north-korea", "North Korea"),
    ("south-africa", "South Africa"),
    ("new-zealand", "New Zealand"),
    ("saudi-arabia", "Saudi Arabia"),
    ("ivory-coast", "Ivory Coast"),
    ("central-africa", "Central Africa"),
    ("dr-congo", "DR Congo"),
    ("papua-new-guinea", "Papua New Guinea"),
    ("equatorial-guinea", "Equatorial Guinea"),
    ("sao-tome", "Sao Tome"),
    ("trinidad-tobago", "Trinidad & Tobago"),
    ("cape-verde", "Cape Verde"),
    ("new-caledonia", "New Caledonia"),
    ("american-samoa", "American Samoa"),
    ("united-states", "USA"),
    ("czech-republic", "Czech Republic"),
    ("northern-ireland", "Northern Ireland"),
    ("faroe-islands", "Faroe Islands"),
    ("antigua-barbuda", "Antigua & Barbuda"),
    ("bosnia-and-herzegovina", "Bosnia"),
    ("bosnia-herzegovina", "Bosnia"),
    ("new-zealand", "New Zealand"),
    ("united-arab-emirates", "UAE"),
    ("central-african", "Central Africa"),
]

# ── Firecrawl scraper ─────────────────────────────────────────────────────────


def scrape_url(url: str, wait_ms: int = 3000, name: str = "") -> str:
    """Scrape a URL via Firecrawl CLI (or Python SDK fallback)."""
    env = dict(os.environ)
    if FIRECRAWL_API_KEY and len(FIRECRAWL_API_KEY) > 20:
        env["FIRECRAWL_API_KEY"] = FIRECRAWL_API_KEY
    try:
        result = subprocess.run(
            [
                "firecrawl",
                "scrape",
                url,
                "--wait-for",
                str(wait_ms),
                "--only-main-content",
            ],
            capture_output=True,
            text=True,
            timeout=90,
            env=env,
        )
        if result.stdout and len(result.stdout) > 200:
            return result.stdout
        if result.stderr:
            print(f"    firecrawl cli stderr [{name}]: {result.stderr[:150]}")
    except FileNotFoundError:
        pass  # CLI not installed, fall through to SDK
    except Exception as exc:
        print(f"    cli error [{name}]: {exc}")

    # SDK fallback
    return _sdk_scrape(url, wait_ms, name)


def _sdk_scrape(url: str, wait_ms: int, name: str) -> str:
    try:
        from firecrawl import FirecrawlApp  # type: ignore

        app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
        result = app.scrape_url(
            url,
            params={
                "formats": ["markdown"],
                "waitFor": wait_ms,
                "onlyMainContent": True,
            },
        )
        return result.get("markdown", "")
    except Exception as exc:
        print(f"    sdk error [{name}]: {exc}")
        return ""


# ── Parsers ───────────────────────────────────────────────────────────────────


def league_key(label: str) -> str:
    for pattern, key in LEAGUE_KEY_MAP:
        if pattern.search(label):
            return key
    return "local"


def slug_to_teams(slug: str) -> tuple[str, str]:
    """
    Convert a Sofascore/OddsPortal URL slug like 'china-singapore' or
    'burkina-faso-russia' into (Home, Away) team names.
    """
    # Try known multi-word teams at the start or end of slug
    lower = slug.lower()

    # Check if slug ends with a known multi-word team (away)
    for mw_slug, mw_name in sorted(MULTI_WORD_TEAMS, key=lambda x: -len(x[0])):
        if lower.endswith("-" + mw_slug):
            home_slug = slug[: -(len(mw_slug) + 1)]
            home = slug_to_single_team(home_slug)
            return home, mw_name
        if lower.startswith(mw_slug + "-"):
            away_slug = slug[len(mw_slug) + 1:]
            away = slug_to_single_team(away_slug)
            return mw_name, away

    # Fall back: split roughly in half
    parts = slug.split("-")
    if len(parts) >= 2:
        mid = max(1, len(parts) // 2)
        home = " ".join(p.capitalize() for p in parts[:mid])
        away = " ".join(p.capitalize() for p in parts[mid:])
        return home, away

    name = slug.replace("-", " ").title()
    return name, "Unknown"


def slug_to_single_team(slug: str) -> str:
    for mw_slug, mw_name in MULTI_WORD_TEAMS:
        if slug.lower() == mw_slug:
            return mw_name
    return slug.replace("-", " ").title()


def fmt_time(raw_time: str, is_live: bool = False) -> str:
    """Format a HH:MM string into a SifuFinds-compatible time label."""
    now = datetime.now(timezone.utc)
    t = raw_time.strip()
    if is_live:
        return t
    # If we can't parse it, default to "Today · HH:MM UTC"
    try:
        h, m = map(int, t.split(":"))
        match_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if match_dt < now.replace(hour=0, minute=0, second=0):
            match_dt = match_dt.replace(day=match_dt.day + 1)
        label = "Today" if match_dt.date() == now.date() else "Tomorrow"
        return f"{label} · {t} UTC"
    except Exception:
        return f"Today · {t} UTC"


# ── Sofascore parser ──────────────────────────────────────────────────────────

_SOFA_MATCH_RE = re.compile(
    r"\[([^\]]+?)\]\(https://www\.sofascore\.com/football/match/([a-z0-9-]+)/[^\)]+\)",
    re.I,
)
_SOFA_TIME_RE = re.compile(r"^(\d{2}:\d{2})$")


def parse_sofascore(text: str) -> list[dict]:
    matches_out: list[dict] = []
    seen: set[str] = set()

    current_league = "World / Friendly International"
    current_key = "world"

    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect competition headers from /tournament/ or /category/ links only
        league_link = re.search(
            r"\[([A-Z][^\]]{3,60})\]\(https://www\.sofascore\.com/football/(?:tournament|category)/([^/]+)/([^/]+)/",
            line,
        )
        if league_link:
            candidate = league_link.group(1).strip()
            # Skip page titles (contain multiple leagues), match names, or year suffixes
            bad = (
                " - " in candidate
                or " vs " in candidate.lower()
                or "," in candidate
                or "Premier League, Champions" in candidate
                or re.search(r"\d{4}$", candidate)
                or len(candidate) < 4
                or len(candidate) > 60
            )
            if not bad:
                current_league = candidate
                current_key = league_key(candidate)

        # Find match links: [TIME\nEXTRA](https://www.sofascore.com/football/match/SLUG/...)
        for m in _SOFA_MATCH_RE.finditer(line):
            link_text = m.group(1).strip()
            slug = m.group(2).lower()

            # Require at least two parts separated by hyphen
            parts = slug.split("-")
            if len(parts) < 2 or "/" in slug:
                continue

            # Extract time from link text (format: "07:30\n..." or just "07:30")
            time_match = re.match(r"(\d{2}:\d{2})", link_text)
            time_raw = time_match.group(1) if time_match else ""

            # Score detection
            score_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", link_text)
            h_score = int(score_match.group(1)) if score_match else None
            a_score = int(score_match.group(2)) if score_match else None
            is_complete = bool(re.search(r"FT|Final|Finished", link_text, re.I))
            is_live = bool(score_match and not is_complete)

            home, away = slug_to_teams(slug)

            # Skip obviously bad parses (same team twice or single-char names)
            if home == away or len(home) < 2 or len(away) < 2:
                continue

            key_str = f"{home.lower()}|{away.lower()}"
            if key_str in seen:
                continue
            seen.add(key_str)

            # Infer league from teams if current_league is still default
            inferred_league = current_league
            inferred_key = current_key
            if current_league == "World / Friendly International":
                # World Cup teams hint
                wc_teams = {"nigeria","ghana","senegal","morocco","cameroon","egypt","algeria","tunisia","south africa","mali","ivory coast","democratic republic of congo"}
                if home.lower() in wc_teams or away.lower() in wc_teams:
                    inferred_league = "World Cup 2026 · Group Stage"
                    inferred_key = "world"

            time_display = fmt_time(time_raw) if time_raw else "Today · TBD"

            matches_out.append(
                {
                    "league": inferred_league,
                    "key": inferred_key,
                    "live": is_live,
                    "complete": is_complete,
                    "home": home,
                    "away": away,
                    "hScore": h_score,
                    "aScore": a_score,
                    "time": time_display,
                    "h": 0.0, "d": 0.0, "a": 0.0,
                    "hBk": "", "dBk": "", "aBk": "",
                    "_src": "sofascore",
                }
            )

        i += 1

    return matches_out


# ── Flashscore parser ─────────────────────────────────────────────────────────

_FS_TEAM_RE = re.compile(r"!\[([^\]]+?)\]\(https://static\.flashscore\.com/[^\)]+\)([A-Za-z].*)")
_FS_COMP_RE = re.compile(r"\[([A-Z][^\]]{3,60})\]\(https://www\.flashscore\.com/football/[^\)]+\)")
_FS_SCORE_RE = re.compile(r"^(\d+)\s*[-–]\s*(\d+)$")
_FS_TIME_RE = re.compile(r"^(\d{2}:\d{2})$")


def parse_flashscore(text: str) -> list[dict]:
    matches_out: list[dict] = []
    seen: set[str] = set()
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    current_league = "World / Friendly International"
    current_key = "world"
    pending_time: str = ""
    pending_home: str = ""
    pending_h_score: int | None = None
    pending_a_score: int | None = None
    is_live = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect competition header
        comp_match = _FS_COMP_RE.search(line)
        if comp_match and not _FS_TEAM_RE.search(line):
            candidate = comp_match.group(1).strip()
            if 4 < len(candidate) < 60 and not re.search(r"^\d", candidate):
                current_league = candidate
                current_key = league_key(candidate)
            i += 1
            continue

        # Detect LIVE marker
        if re.search(r"\bLIVE\b", line, re.I) and len(line) < 10:
            is_live = True
            i += 1
            continue

        # Detect time HH:MM on its own line
        time_match = _FS_TIME_RE.match(line)
        if time_match:
            pending_time = time_match.group(1)
            is_live = False
            i += 1
            continue

        # Detect score like "1 - 0" on its own line
        score_match = _FS_SCORE_RE.match(line)
        if score_match and pending_home:
            pending_h_score = int(score_match.group(1))
            pending_a_score = int(score_match.group(2))
            i += 1
            continue

        # Detect team name via image+name pattern
        team_match = _FS_TEAM_RE.search(line)
        if team_match:
            team_name = team_match.group(2).strip()
            # Remove trailing markdown artifacts
            team_name = re.sub(r"\s*\[.*", "", team_name).strip()
            if not team_name or len(team_name) < 2:
                i += 1
                continue

            if not pending_home:
                pending_home = team_name
            else:
                # We have both teams
                away = team_name
                key_str = f"{pending_home}|{away}"
                if key_str not in seen:
                    seen.add(key_str)
                    time_display = fmt_time(pending_time, is_live) if pending_time else "Today · TBD"
                    matches_out.append(
                        {
                            "league": current_league,
                            "key": current_key,
                            "live": is_live and pending_h_score is not None,
                            "complete": False,
                            "home": pending_home,
                            "away": away,
                            "hScore": pending_h_score,
                            "aScore": pending_a_score,
                            "time": time_display,
                            "h": 0.0,
                            "d": 0.0,
                            "a": 0.0,
                            "hBk": "",
                            "dBk": "",
                            "aBk": "",
                            "_src": "flashscore",
                        }
                    )
                # Reset
                pending_home = ""
                pending_time = ""
                pending_h_score = None
                pending_a_score = None
                is_live = False

        i += 1

    return matches_out


# ── Livescore parser ──────────────────────────────────────────────────────────

_LS_TEAM_RE = re.compile(r"!\[([^\]]+?)\]\(https://storage\.livescore\.com/[^\)]+\)\s*\\?\s*([A-Za-z][^\n\\]{1,40})")
_LS_COMP_RE = re.compile(r"##\s+(.+)")


def parse_livescore(text: str) -> list[dict]:
    matches_out: list[dict] = []
    seen: set[str] = set()
    current_league = "World / Friendly International"
    current_key = "world"
    pending_home: str = ""
    pending_time: str = ""
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    i = 0
    while i < len(lines):
        line = lines[i]

        comp_m = _LS_COMP_RE.match(line)
        if comp_m:
            candidate = comp_m.group(1).strip()
            if 3 < len(candidate) < 60:
                current_league = candidate
                current_key = league_key(candidate)
            i += 1
            continue

        time_m = re.match(r"^(\d{2}:\d{2})$", line)
        if time_m:
            pending_time = time_m.group(1)
            i += 1
            continue

        team_m = _LS_TEAM_RE.search(line)
        if team_m:
            team_name = team_m.group(2).strip()
            team_name = re.sub(r"[\\\[\]|].*", "", team_name).strip()
            if not team_name or len(team_name) < 2:
                i += 1
                continue

            if not pending_home:
                pending_home = team_name
            else:
                key_str = f"{pending_home}|{team_name}"
                if key_str not in seen:
                    seen.add(key_str)
                    time_display = fmt_time(pending_time) if pending_time else "Today · TBD"
                    matches_out.append(
                        {
                            "league": current_league,
                            "key": current_key,
                            "live": False,
                            "complete": False,
                            "home": pending_home,
                            "away": team_name,
                            "hScore": None,
                            "aScore": None,
                            "time": time_display,
                            "h": 0.0,
                            "d": 0.0,
                            "a": 0.0,
                            "hBk": "",
                            "dBk": "",
                            "aBk": "",
                            "_src": "livescore",
                        }
                    )
                pending_home = ""
                pending_time = ""

        i += 1

    return matches_out


# ── OddsPortal parser ─────────────────────────────────────────────────────────

_OP_TIME_RE = re.compile(r"^(\d{2}:\d{2})$")
_OP_ODDS_RE = re.compile(r"^(\d+\.\d{2})$")


def parse_oddsportal(text: str, label_hint: str = "All Football") -> list[dict]:
    matches_out: list[dict] = []
    seen: set[str] = set()
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    current_league = "World / Friendly International"
    current_key = "world"
    pending_time: str = ""
    teams: list[str] = []
    odds_buf: list[float] = []

    AFRICAN_BKS = ["Bet9ja", "Betway", "1xBet", "Sportybet", "Betika", "22Bet", "Melbet"]

    for line in lines:
        # Competition header from link text
        comp_m = re.search(r"\[([A-Z][^\]]{5,55})\]\(https://www\.oddsportal\.com/football/", line)
        if comp_m and not _OP_TIME_RE.match(line):
            candidate = comp_m.group(1).strip()
            if not re.search(r"^\d|\d{4}$", candidate):
                current_league = candidate
                current_key = league_key(candidate)
            teams = []
            odds_buf = []
            pending_time = ""
            continue

        if _OP_TIME_RE.match(line):
            pending_time = line
            teams = []
            odds_buf = []
            continue

        odds_m = _OP_ODDS_RE.match(line)
        if odds_m and pending_time and len(teams) >= 2:
            odds_buf.append(float(odds_m.group(1)))
            if len(odds_buf) == 3:
                key_str = f"{teams[0]}|{teams[1]}"
                if key_str not in seen:
                    seen.add(key_str)
                    h, d, a = odds_buf[0], odds_buf[1], odds_buf[2]
                    bk = AFRICAN_BKS[len(seen) % len(AFRICAN_BKS)]
                    matches_out.append(
                        {
                            "league": current_league,
                            "key": current_key,
                            "live": False,
                            "complete": False,
                            "home": teams[0],
                            "away": teams[1],
                            "hScore": None,
                            "aScore": None,
                            "time": fmt_time(pending_time),
                            "h": h,
                            "d": d,
                            "a": a,
                            "hBk": bk,
                            "dBk": bk,
                            "aBk": bk,
                            "_src": "oddsportal",
                        }
                    )
                pending_time = ""
                teams = []
                odds_buf = []
            continue

        # Team names: non-empty lines between time and odds
        if (
            pending_time
            and len(teams) < 2
            and line
            and not line.startswith("!")
            and not line.startswith("[")
            and not line.startswith("|")
            and not re.match(r"^\d+\.?\d*$", line)
            and 2 < len(line) < 55
        ):
            teams.append(line)

    return matches_out


# ── BetExplorer parser ────────────────────────────────────────────────────────


def parse_betexplorer(text: str) -> list[dict]:
    """BetExplorer has a table-like structure — extract what we can."""
    matches_out: list[dict] = []
    seen: set[str] = set()
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    current_league = "World / Friendly International"
    current_key = "world"
    pending_time: str = ""
    teams: list[str] = []

    for line in lines:
        comp_m = re.search(r"\[([A-Z][^\]]{5,55})\]\(https://www\.betexplorer\.com/soccer/", line)
        if comp_m:
            candidate = comp_m.group(1).strip()
            if not re.search(r"^\d", candidate):
                current_league = candidate
                current_key = league_key(candidate)
            teams = []
            pending_time = ""
            continue

        time_m = re.match(r"^(\d{2}:\d{2})$", line)
        if time_m:
            pending_time = time_m.group(1)
            teams = []
            continue

        if (
            pending_time
            and line
            and not line.startswith("!")
            and not line.startswith("[")
            and not re.match(r"^\d", line)
            and 2 < len(line) < 55
        ):
            teams.append(line)
            if len(teams) == 2:
                key_str = f"{teams[0]}|{teams[1]}"
                if key_str not in seen:
                    seen.add(key_str)
                    matches_out.append(
                        {
                            "league": current_league,
                            "key": current_key,
                            "live": False,
                            "complete": False,
                            "home": teams[0],
                            "away": teams[1],
                            "hScore": None,
                            "aScore": None,
                            "time": fmt_time(pending_time),
                            "h": 0.0,
                            "d": 0.0,
                            "a": 0.0,
                            "hBk": "",
                            "dBk": "",
                            "aBk": "",
                            "_src": "betexplorer",
                        }
                    )
                teams = []
                pending_time = ""

    return matches_out


# ── Parser dispatch ───────────────────────────────────────────────────────────

PARSERS: dict[str, Any] = {
    "sofascore": parse_sofascore,
    "flashscore": parse_flashscore,
    "livescore": parse_livescore,
    "oddsportal_today": lambda t: parse_oddsportal(t, "All Football"),
    "oddsportal_africa": lambda t: parse_oddsportal(t, "Africa"),
    "betexplorer": parse_betexplorer,
}


# ── live.json helpers ─────────────────────────────────────────────────────────


def load_live_json() -> dict:
    try:
        if LIVE_JSON.exists():
            return json.loads(LIVE_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"  Could not read live.json: {exc}")
    return {"events": [], "updated": ""}


def save_live_json(data: dict) -> None:
    LIVE_JSON.parent.mkdir(parents=True, exist_ok=True)
    LIVE_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def match_key(e: dict) -> str:
    return f"{(e.get('home') or '').lower()}|{(e.get('away') or '').lower()}"


def enrich_existing(existing_events: list[dict], new_events: list[dict]) -> list[dict]:
    """
    Update existing events with live score info from new_events.
    For new matches not in existing, append them.
    Preserves ESPN odds (h/d/a > 0) and only overwrites scores/live status.
    """
    existing_map: dict[str, dict] = {match_key(e): e for e in existing_events}

    for new in new_events:
        k = match_key(new)
        if k in existing_map:
            ex = existing_map[k]
            # Only update live/score if the new source has score data
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
            # Enrich odds only if existing has none
            if ex.get("h", 0) == 0 and new.get("h", 0) > 0:
                ex["h"] = new["h"]
                ex["d"] = new["d"]
                ex["a"] = new["a"]
                ex["hBk"] = new.get("hBk", "")
                ex["dBk"] = new.get("dBk", "")
                ex["aBk"] = new.get("aBk", "")
        else:
            # New match not seen before
            existing_map[k] = new

    return list(existing_map.values())


# ── Main ──────────────────────────────────────────────────────────────────────


def scrape_source(source: dict) -> tuple[str, list[dict]]:
    """Scrape one source and return (name, parsed_matches)."""
    name = source["name"]
    print(f"  → Scraping {name} ({source['url'][:50]}...)")
    text = scrape_url(source["url"], source["wait"], name)
    if not text or len(text) < 300:
        print(f"    ⚠ {name}: too little content ({len(text)} chars) — skipping")
        return name, []

    parser = PARSERS.get(name)
    if not parser:
        print(f"    ⚠ {name}: no parser defined")
        return name, []

    matches = parser(text)
    print(f"    ✓ {name}: {len(matches)} matches parsed")
    return name, matches


def main() -> None:
    if not FIRECRAWL_API_KEY:
        print("ℹ FIRECRAWL_API_KEY not set — using CLI stored credentials")

    ts = datetime.now(timezone.utc).isoformat()
    print(f"\n[{ts}] Multi-source scrape starting...")
    print(f"  Sources: {', '.join(s['name'] for s in SOURCES)}")

    # Load current live.json
    existing = load_live_json()
    events: list[dict] = existing.get("events", [])
    print(f"  Existing events in live.json: {len(events)}")

    # Scrape all sources concurrently
    all_new: list[dict] = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(scrape_source, src): src for src in SOURCES}
        for future in as_completed(futures):
            name, matches = future.result()
            all_new.extend(matches)

    print(f"\n  Total raw matches from all sources: {len(all_new)}")

    # Deduplicate across sources (higher-priority sources win)
    seen_keys: set[str] = set()
    deduped: list[dict] = []
    for src_name in [s["name"] for s in sorted(SOURCES, key=lambda x: x["priority"])]:
        for m in all_new:
            if m.get("_src") != src_name:
                continue
            k = match_key(m)
            if k not in seen_keys:
                seen_keys.add(k)
                deduped.append(m)

    print(f"  Deduped new matches: {len(deduped)}")

    # Merge: update existing events and add new ones
    merged = enrich_existing(events, deduped)

    # Remove _src metadata field before saving
    for e in merged:
        e.pop("_src", None)

    # Sort: live first, then upcoming, then finished
    def sort_key(e: dict) -> tuple:
        live = 0 if e.get("live") else (2 if e.get("complete") else 1)
        key_order = ["world", "cafl", "afcon", "local", "basketball", "tennis", "cricket", "rugby", "epl", "ucl", "laliga", "baseball"]
        k = key_order.index(e.get("key", "")) if e.get("key") in key_order else 99
        return (live, k)

    merged.sort(key=sort_key)

    output = {
        "updated": ts,
        "count": len(merged),
        "events": merged,
    }

    save_live_json(output)
    live_count = sum(1 for e in merged if e.get("live"))
    new_count = sum(1 for e in merged if match_key(e) not in {match_key(x) for x in events})
    print(f"\n  ✅ live.json updated:")
    print(f"     Total events: {len(merged)}")
    print(f"     Live now:     {live_count}")
    print(f"     New matches:  {new_count}")
    print(f"     Written to:   {LIVE_JSON}")


if __name__ == "__main__":
    main()
