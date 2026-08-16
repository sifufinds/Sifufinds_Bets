"""
agent_multi_scrape.py — 15-min multi-source scraper for SifuFinds
Scrapes 6 sites (Flashscore, Sofascore, Livescore, OddsPortal, BetExplorer,
OddsChecker) free-first (trafilatura + Jina Reader, see utils/free_scrape.py),
then merges results into data/live.json. Firecrawl only fires as a last
resort per-URL when both free layers return too little content.

Runs every 15 minutes via GitHub Actions alongside agent_live_odds.py (ESPN,
every 5 min). FIRECRAWL_API_KEY is optional — the free pipeline needs no key.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from utils.free_scrape import scrape as free_scrape
from utils.live_data_helpers import fmt_time, league_key
from utils.live_json_store import enrich_existing, load_live_json, match_key, save_live_json
from utils.oddsportal_parser import parse_oddsportal as _parse_oddsportal

# ── Config ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LIVE_JSON = REPO_ROOT / "data" / "live.json"
TODAY = datetime.now(timezone.utc).strftime("%Y%m%d")
TOMORROW = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y%m%d")

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
        "name": "oddsportal_tomorrow",
        "url": f"https://www.oddsportal.com/matches/football/{TOMORROW}/",
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

# ── Scraper (free-first, see utils/free_scrape.py) ───────────────────────────


def scrape_url(url: str, wait_ms: int = 3000, name: str = "") -> str:
    """Free-first scrape (trafilatura + Jina Reader), Firecrawl last resort."""
    # 1500 char floor: observed boilerplate-only trafilatura fetches of these
    # SPA shells (cookie/legal disclaimers) top out around ~1200 chars, so a
    # lower floor would accept junk instead of escalating to Jina/Firecrawl.
    return free_scrape(url, name=name, wait_ms=wait_ms, min_chars=1500)


# ── Parsers ───────────────────────────────────────────────────────────────────


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


# ── Sofascore parser ──────────────────────────────────────────────────────────
# Real Firecrawl format observed from live scrape:
#
#   [League](tournament_url) [Country](country_url)
#   N   ← number of matches
#   [HH:MM\
#   \
#   FT/LIVE/N'\
#   \
#   ![Team1](img)\
#   \
#   Team1\
#   \
#   ![Team2](img)\
#   \
#   Team2\
#   \
#   HScore\
#   \
#   AScore](match_url)
#
# Each match is a single multi-line link with `\` as row separators.
# Team names appear after their badge image link, separated by `\` + newline.

# Match link: captures full content inside [...](sofascore_match_url)
_SOFA_MATCH_LINK = re.compile(
    r'\[([\s\S]{30,600}?)\]\(https://www\.sofascore\.com/football/match/[^\)]+\)',
    re.S,
)
# Competition header link
_SOFA_COMP_RE = re.compile(
    r'\[([A-Z][^\]]{3,60})\]\(https://www\.sofascore\.com/football/(?:tournament|category)/[^\)]+\)',
)
# Team name after image: ![...](img_url)\<newline>\<newline>TeamName
_SOFA_TEAM_RE = re.compile(r'!\[[^\]]*\]\([^\)]+\)\\?\s*\\?\s*([A-Za-z][^\n\\]{1,50}?)\\?\s*(?=\\|$|\n)', re.M)


def _parse_sofa_link(content: str) -> tuple[str, str, str, int | None, int | None, bool, bool]:
    """Parse the inside of a Sofascore match link.

    Returns (time, home, away, h_score, a_score, is_live, is_complete).
    Firecrawl renders each row separated by backslash + newline sequences.
    """
    # Normalise: replace `\\\n\\` sequences (backslash-newline-backslash) to a delimiter
    normalised = re.sub(r'\\\s*\\\s*', '|', content)
    # Also handle single `\` followed by whitespace
    normalised = re.sub(r'\\\s+', '|', normalised)
    parts = [p.strip() for p in normalised.split('|') if p.strip()]

    time_str = ""
    status = ""
    teams: list[str] = []
    raw_scores: list[str] = []

    for part in parts:
        # Time: HH:MM
        if re.match(r'^\d{2}:\d{2}$', part) and not time_str:
            time_str = part
        # Status: FT, LIVE, N' (minute)
        elif re.match(r'^(?:FT|Final|Finished|LIVE|\d+\'?)$', part, re.I):
            status = part
        # Image link — skip
        elif part.startswith('!['):
            continue
        # Score string: digits only (e.g. "33" = 3-3, "10" = 1-0, "21" = 2-1)
        elif re.match(r'^\d{1,2}$', part) and len(teams) >= 2:
            raw_scores.append(part)
        # Team name: not starting with [ or ! or digit, length 2-50
        elif (not part.startswith('[') and not part.startswith('!')
              and not re.match(r'^\d', part)
              and 2 <= len(part) <= 50 and len(teams) < 2):
            teams.append(part)

    home = teams[0] if len(teams) > 0 else ""
    away = teams[1] if len(teams) > 1 else ""

    # Scores: raw_scores may be ["33", "22"] meaning [3, 3] then [2, 2]
    # Sofascore concatenates home+away digits: "33" = 3-3, "10" = 1-0
    h_score: int | None = None
    a_score: int | None = None
    if raw_scores:
        s = raw_scores[0]
        if len(s) == 2:
            try:
                h_score = int(s[0])
                a_score = int(s[1])
            except ValueError:
                pass

    is_complete = bool(re.match(r'^(?:FT|Final|Finished)$', status, re.I))
    is_live = bool(status and not is_complete and status != "")

    return time_str, home, away, h_score, a_score, is_live, is_complete


def parse_sofascore(text: str) -> list[dict]:
    matches_out: list[dict] = []
    seen: set[str] = set()

    current_league = "World / Friendly International"
    current_key = "world"

    # Process line by line to track competition context
    # Competition headers appear as: [League Name](tournament_url) [Country](country_url)
    lines = text.split("\n")
    # Build a position→league map so match links inherit the most recent header
    comp_positions: list[tuple[int, str, str]] = []  # (char_offset, league, key)

    # Find all competition headers in the full text
    for m in _SOFA_COMP_RE.finditer(text):
        candidate = m.group(1).strip()
        # Filter out page-level navigation titles (contain multiple league names separated by comma+space)
        bad = (
            " - " in candidate or " vs " in candidate.lower()
            or (", " in candidate and re.search(r"League.*League|Cup.*League", candidate))
            or len(candidate) < 4 or len(candidate) > 70
            or re.search(r"\d{4}$", candidate)
        )
        if not bad:
            k = league_key(candidate)
            comp_positions.append((m.start(), candidate, k))

    def comp_at(pos: int) -> tuple[str, str]:
        league, key = "World / Friendly International", "world"
        for cp_pos, cp_league, cp_key in comp_positions:
            if cp_pos <= pos:
                league, key = cp_league, cp_key
            else:
                break
        return league, key

    for m in _SOFA_MATCH_LINK.finditer(text):
        content = m.group(1)
        match_pos = m.start()

        time_raw, home, away, h_score, a_score, is_live, is_complete = _parse_sofa_link(content)

        if not home or not away or len(home) < 2 or len(away) < 2:
            continue
        if home.lower() == away.lower():
            continue

        key_str = f"{home.lower()}|{away.lower()}"
        if key_str in seen:
            continue
        seen.add(key_str)

        league, key = comp_at(match_pos)

        # Infer WC2026 teams
        if league == "World / Friendly International":
            wc_teams = {
                "nigeria", "ghana", "senegal", "morocco", "cameroon", "egypt",
                "algeria", "tunisia", "south africa", "mali", "ivory coast",
                "democratic republic of congo", "dr congo", "mexico", "usa",
                "canada", "brazil", "argentina", "france", "spain", "england",
            }
            if home.lower() in wc_teams or away.lower() in wc_teams:
                league = "World Cup 2026 · Group Stage"
                key = "world"

        time_display = fmt_time(time_raw, is_live) if time_raw else "Today · TBD"

        matches_out.append({
            "league": league,
            "key": key,
            "live": is_live and h_score is not None,
            "complete": is_complete,
            "home": home,
            "away": away,
            "hScore": h_score,
            "aScore": a_score,
            "time": time_display,
            "h": 0.0, "d": 0.0, "a": 0.0,
            "hBk": "", "dBk": "", "aBk": "",
            "_src": "sofascore",
        })

    return matches_out


# ── Flashscore parser ─────────────────────────────────────────────────────────

_FS_TEAM_RE = re.compile(r"!\[([^\]]+?)\]\(https://static\.flashscore\.com/[^\)]+\)([A-Za-z].*)")
_FS_COMP_RE = re.compile(r"\[([A-Z][^\]]{3,60})\]\(https://www\.flashscore\.com/football/[^\)]+\)")
_FS_SCORE_RE = re.compile(r"^(\d+)\s*[-–]\s*(\d+)$")
_FS_CONCAT_SCORE_RE = re.compile(r"^(\d)(\d)$")  # Flashscore concatenates: "40" = 4-0
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

        # Detect LIVE or Finished status
        if re.match(r"^(?:LIVE|Finished|FT)$", line, re.I):
            is_live = line.upper() == "LIVE"
            i += 1
            continue

        # Detect time HH:MM on its own line
        time_match = _FS_TIME_RE.match(line)
        if time_match:
            pending_time = time_match.group(1)
            is_live = False
            i += 1
            continue

        # Detect score: "N - M" format
        score_match = _FS_SCORE_RE.match(line)
        if score_match and pending_home:
            pending_h_score = int(score_match.group(1))
            pending_a_score = int(score_match.group(2))
            i += 1
            continue

        # Detect concatenated score: "40" = 4-0, "11" = 1-1 (Flashscore format)
        concat_m = _FS_CONCAT_SCORE_RE.match(line)
        if concat_m and pending_home:
            pending_h_score = int(concat_m.group(1))
            pending_a_score = int(concat_m.group(2))
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


# ── OddsPortal parser (utils/oddsportal_parser.py — extracts real 1X2 odds) ────


def parse_oddsportal(text: str, label_hint: str = "All Football") -> list[dict]:
    return _parse_oddsportal(text, league_key, fmt_time, label_hint)


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
    "oddsportal_tomorrow": lambda t: parse_oddsportal(t, "All Football"),
    "betexplorer": parse_betexplorer,
}


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
    from utils.free_scrape import FIRECRAWL_API_KEY
    if not FIRECRAWL_API_KEY:
        print("ℹ FIRECRAWL_API_KEY not set — running free-only (trafilatura + Jina Reader)")

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

    # Deduplicate across sources (higher-priority source's fixture data wins,
    # but a lower-priority duplicate's odds are still backfilled onto it —
    # e.g. Sofascore usually wins the fixture, OddsPortal still contributes
    # its real 1X2 prices onto that same match instead of being dropped).
    dedup_map: dict[str, dict] = {}
    for src_name in [s["name"] for s in sorted(SOURCES, key=lambda x: x["priority"])]:
        for m in all_new:
            if m.get("_src") != src_name:
                continue
            k = match_key(m)
            if k not in dedup_map:
                dedup_map[k] = m
            elif dedup_map[k].get("h", 0) == 0 and m.get("h", 0) > 0:
                kept = dedup_map[k]
                kept["h"], kept["d"], kept["a"] = m["h"], m["d"], m["a"]
                kept["hBk"], kept["dBk"], kept["aBk"] = m.get("hBk", ""), m.get("dBk", ""), m.get("aBk", "")

    deduped = list(dedup_map.values())
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
