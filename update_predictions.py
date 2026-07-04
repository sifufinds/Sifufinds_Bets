#!/usr/bin/env python3
"""
SifuKaii Predicts — multi-source football prediction scraper.

Sources:
  1. predictz.com  — primary (match winner, BTTS, O/U 2.5, correct score)
  2. forebet.com   — supplementary (60+ leagues inc. African competitions)

Firecrawl (REST API or CLI) and Apify run in parallel per page.
Whichever returns a valid result first wins; the other is discarded.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import requests as _req

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

URLS: dict[str, str] = {
    "main":  "https://www.predictz.com/predictions/",
    "btts":  "https://www.predictz.com/predictions/today/both-teams-to-score/",
    "ou25":  "https://www.predictz.com/predictions/today/over-under-25-goals/",
    "bw":    "https://www.predictz.com/predictions/today/both-teams-to-score-and-win/",
    "score": "https://www.predictz.com/predictions/today/correct-score/",
    # Forebet — mathematical predictions for 60+ leagues
    "forebet_1x2":  "https://www.forebet.com/en/football-tips-and-predictions-for-today/predictions-1x2",
    "forebet_btts": "https://www.forebet.com/en/football-tips-and-predictions-for-today/predictions-both-to-score",
    "forebet_ou":   "https://www.forebet.com/en/football-tips-and-predictions-for-today/predictions-under-over-goals",
}

OUT_PATH = Path(__file__).parent / "data" / "predictions.json"

# ---------------------------------------------------------------------------
# Forebet: country-code → readable competition name
# ---------------------------------------------------------------------------

FOREBET_COMP: dict[str, str] = {
    "ng": "Nigeria NPFL",
    "ke": "Kenya Premier League",
    "za": "South Africa PSL",
    "gh": "Ghana Premier League",
    "eg": "Egypt Premier League",
    "ma": "Morocco Botola Pro",
    "tz": "Tanzania Ligi Kuu",
    "cm": "Cameroon Elite One",
    "sn": "Senegal Premier League",
    "ug": "Uganda Premier League",
    "zw": "Zimbabwe PSL",
    "tn": "Tunisia Ligue 1",
    "dz": "Algeria Ligue 1",
    "et": "Ethiopia Premier League",
    "rw": "Rwanda Premier League",
    "zm": "Zambia Super League",
    "mz": "Mozambique Moçambola",
    "ao": "Angola GiraFC",
    "cd": "DR Congo Linafoot",
    "ci": "Ivory Coast Ligue 1",
    "bw": "Botswana Premier League",
    "na": "Namibia Premier League",
    "en": "England Premier League",
    "es": "Spain La Liga",
    "de": "Germany Bundesliga",
    "it": "Italy Serie A",
    "fr": "France Ligue 1",
    "pt": "Portugal Primeira Liga",
    "nl": "Netherlands Eredivisie",
    "be": "Belgium Pro League",
    "tr": "Turkey Super Lig",
    "br": "Brazil Serie A",
    "ar": "Argentina Primera Division",
    "mx": "Mexico Liga MX",
    "us": "USA MLS",
    "jp": "Japan J1 League",
    "sa": "Saudi Arabia Pro League",
    "kr": "South Korea K League",
    "au": "Australia A-League",
    "sc": "Scotland Premiership",
    "wl": "Wales Premier League",
    "ie": "Ireland Premier Division",
    "ru": "Russia Premier League",
    "ua": "Ukraine Premier League",
    "pl": "Poland Ekstraklasa",
    "cz": "Czech Republic HET Liga",
    "sk": "Slovakia Super Liga",
    "hu": "Hungary OTP Bank Liga",
    "ro": "Romania Liga 1",
    "bg": "Bulgaria First League",
    "rs": "Serbia Super Liga",
    "hr": "Croatia HNL",
    "si": "Slovenia PrvaLiga",
    "ba": "Bosnia Premier League",
    "sl": "Slovenia PrvaLiga",
    "uy": "Uruguay Primera Division",
    "ca": "Canada Premier League",
    "co": "Colombia Primera A",
    "py": "Paraguay Division Professional",
    "cl": "Chile Primera Division",
    "lt": "Lithuania A Lyga",
    "ve": "Venezuela Primera",
    "pe": "Peru Liga 1",
    "ec": "Ecuador LigaPro",
    "bo": "Bolivia Liga",
    "cr": "Costa Rica Primera",
    "pa": "Panama LPF",
    "hn": "Honduras Liga Nacional",
    "sv": "El Salvador Primera",
    "gt": "Guatemala Liga Nacional",
    "al": "Albania Superliga",
    "gr": "Greece Super League",
    "cy": "Cyprus First Division",
    "at": "Austria Bundesliga",
    "ch": "Switzerland Super League",
    "dk": "Denmark Superliga",
    "se": "Sweden Allsvenskan",
    "no": "Norway Eliteserien",
    "fi": "Finland Veikkausliiga",
    "int": "International Friendly",
    "wc": "World Cup 2026",
    "eu": "UEFA Champions League",
    "uel": "UEFA Europa League",
    "cafl": "CAF Champions League",
    "afcon": "AFCON",
}

# ---------------------------------------------------------------------------
# Regex patterns — predictz
# ---------------------------------------------------------------------------

MATCH_LINK = re.compile(
    r"\[(.+?)\s+v\s+(.+?)\]\(https://www\.predictz\.com/predictions/(.+?)/(\d+)/",
    re.I,
)
MATCH_PREVIEW = re.compile(
    r"\[MATCH PREVIEW\]\(https://www\.predictz\.com/predictions/[^)]+/(\d+)/",
    re.I,
)
COMP_HEAD  = re.compile(r"^##\s*\[([^\]]+?)\s*Tips\]", re.I)
PRED_MAIN  = re.compile(r"^(Home|Away|Draw)\s+(\d+[-:]\d+(?:\s*\(\w+\))?)", re.I)
BTTS_PRED  = re.compile(r"^BTTS (Yes|No)$", re.I)
OU_PRED    = re.compile(r"^(Over|Under) 2\.5$", re.I)
BW_PRED    = re.compile(r"^(BTTS And Win|Did Not Win)", re.I)
SCORE_PRED = re.compile(r"^(\d+-\d+) Correct Score Odds$", re.I)
FANDUEL    = re.compile(r"^\[(\d+\.\d+)\]\(https://www\.predictz\.com/fanduel/", re.I)

# ---------------------------------------------------------------------------
# Regex patterns — forebet
# ---------------------------------------------------------------------------

FB_FLAG  = re.compile(r'!\[\]\(https://www\.forebet\.com/images/fc/(\w+)\.png\)(\w+)', re.I)
FB_MATCH = re.compile(
    r'\[(.+?)(\d{2}/\d{2}/\d{4}\s+\d{1,2}:\d{2}\s+[AP]M)\]'
    r'\(https://www\.forebet\.com/en/football/matches/[^)]*?-(\d{4,})\)',
    re.I,
)
FB_PROBS = re.compile(r'^(\d{2})(\d{2})(\d{2})$')
FB_PRED  = re.compile(r'^([12X]{1,2})(\d+)-(\d+)$')
FB_BTTS  = re.compile(r'^(Yes|No)(\d+)-(\d+)$', re.I)       # BTTS page format
FB_OU    = re.compile(r'^(Over|Under)(\d+)-(\d+)$', re.I)   # OU page format
FB_LIVE  = re.compile(r'^\+\d+\'$|^HT$|^FT$')
FB_SCORE = re.compile(r'^\*\*\d+\s*-\s*\d+\*\*')

# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------

def _scrape_firecrawl_rest(url: str, api_key: str) -> str:
    payload = json.dumps({
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,
    }).encode()
    req = urllib.request.Request(
        "https://api.firecrawl.dev/v1/scrape",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
    if not result.get("success"):
        raise RuntimeError(f"Firecrawl API error: {result}")
    return result.get("data", {}).get("markdown", "")


def _scrape_firecrawl_cli(url: str) -> str:
    candidates = [
        "firecrawl",
        os.path.expanduser("~/.nvm/versions/node/v24.15.0/bin/firecrawl"),
        os.path.expanduser("~/.nvm/versions/node/v22.0.0/bin/firecrawl"),
    ]
    bin_path = next(
        (c for c in candidates
         if os.path.isfile(c) or subprocess.run(
             ["which", c], capture_output=True
         ).returncode == 0),
        None,
    )
    if not bin_path:
        raise RuntimeError("firecrawl CLI not found")

    r = subprocess.run(
        [bin_path, "scrape", url, "--only-main-content"],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        raise RuntimeError(f"firecrawl CLI ({r.returncode}): {r.stderr[:200]}")
    return r.stdout


def _scrape_apify(url: str, token: str) -> str:
    payload = json.dumps({"query": url, "maxResults": 1}).encode()
    req = urllib.request.Request(
        f"https://api.apify.com/v2/acts/apify~rag-web-browser/runs?token={token}&waitSecs=90",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        run = json.loads(resp.read())

    dataset_id = (
        run.get("data", {}).get("defaultDatasetId")
        or run.get("defaultDatasetId")
    )
    if not dataset_id:
        raise RuntimeError(f"Apify: no dataset ID: {run}")

    items_url = (
        f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        f"?token={token}&clean=true"
    )
    with urllib.request.urlopen(items_url, timeout=30) as resp:
        items = json.loads(resp.read())

    if not items:
        raise RuntimeError("Apify: empty dataset")
    return items[0].get("markdown") or items[0].get("text") or ""


def _apify_token() -> str:
    return (
        os.environ.get("APIFY_API_TOKEN")
        or os.environ.get("APIFY_TOKEN")
        or ""
    ).strip()


def _firecrawl_scraper(url: str):
    """Return a callable for whichever Firecrawl variant is available."""
    api_key = os.environ.get("FIRECRAWL_API_KEY", "").strip()
    if api_key:
        return lambda: _scrape_firecrawl_rest(url, api_key)
    return lambda: _scrape_firecrawl_cli(url)


def scrape(url: str) -> str:
    """
    Run Firecrawl and Apify in parallel.
    Return whichever produces a non-empty result first.
    Fall back to the slower one if the fast one fails.
    """
    apify_tok = _apify_token()
    tasks: dict = {}

    with ThreadPoolExecutor(max_workers=2) as pool:
        tasks[pool.submit(_firecrawl_scraper(url))] = "firecrawl"
        if apify_tok:
            tasks[pool.submit(_scrape_apify, url, apify_tok)] = "apify"

        errors: list[str] = []
        remaining = set(tasks.keys())

        while remaining:
            done, remaining = wait(remaining, return_when=FIRST_COMPLETED, timeout=130)
            for future in done:
                name = tasks[future]
                try:
                    result = future.result()
                    if result:
                        # Cancel whatever is still running
                        for f in remaining:
                            f.cancel()
                        print(f"  [ok/{name}] {len(result)} chars", file=sys.stderr)
                        return result
                except Exception as exc:
                    errors.append(f"{name}: {exc}")
                    print(f"  [warn/{name}] {exc}", file=sys.stderr)

    raise RuntimeError(f"All scrapers failed for {url}: {'; '.join(errors)}")

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _lines(text: str) -> list[str]:
    return [l.strip() for l in text.splitlines()]


def _pred_map_before_preview(
    lines: list[str],
    pred_re: re.Pattern,
) -> dict[str, str]:
    """
    For pages where the prediction label appears before [MATCH PREVIEW].
    Scans back from each MATCH PREVIEW anchor to find the prediction.
    Returns {match_id: prediction_text}.
    """
    result: dict[str, str] = {}
    for i, line in enumerate(lines):
        mp_m = MATCH_PREVIEW.search(line)
        if not mp_m:
            continue
        match_id = mp_m.group(1)
        for j in range(i - 1, max(i - 20, -1), -1):
            prev = lines[j]
            if not prev:
                continue
            if COMP_HEAD.match(prev):
                break
            if pred_re.match(prev):
                result[match_id] = prev
                break
    return result

# ---------------------------------------------------------------------------
# Page parsers
# ---------------------------------------------------------------------------

def parse_main(text: str) -> dict[str, dict]:
    lines = _lines(text)
    pred_map = _pred_map_before_preview(lines, PRED_MAIN)

    results: dict[str, dict] = {}
    current_comp = ""

    for i, line in enumerate(lines):
        comp_m = COMP_HEAD.match(line)
        if comp_m:
            current_comp = comp_m.group(1).strip()
            continue

        ml = MATCH_LINK.match(line)
        if not ml:
            continue
        home, away, comp_slug, match_id = ml.groups()

        pred_raw = pred_map.get(match_id, "")
        pred_m = PRED_MAIN.match(pred_raw)
        outcome = score = wdw = ""
        if pred_m:
            side  = pred_m.group(1).capitalize()
            score = pred_m.group(2).strip()
            outcome = side
            wdw = {"home": "1", "away": "2", "draw": "X"}.get(side.lower(), "")

        # Forward scan for home / draw / away odds (FanDuel links)
        found: list[str] = []
        for j in range(i + 1, min(i + 40, len(lines))):
            fm = FANDUEL.match(lines[j])
            if fm:
                found.append(fm.group(1))
                if len(found) == 3:
                    break
            nxt = lines[j]
            if nxt and (
                MATCH_LINK.match(nxt)
                or MATCH_PREVIEW.search(nxt)
                or COMP_HEAD.match(nxt)
            ):
                break
        home_odds, draw_odds, away_odds = (found + ["", "", ""])[:3]

        results[match_id] = {
            "id":                match_id,
            "home":              home.strip(),
            "away":              away.strip(),
            "competition":       current_comp,
            "comp_slug":         comp_slug.strip("/"),
            "ko_display":        "Today",
            "ko_utc":            None,
            "match_winner":      outcome,
            "match_winner_label": f"{outcome} {score}".strip(),
            "wdw":               wdw,
            "home_odds":         home_odds,
            "draw_odds":         draw_odds,
            "away_odds":         away_odds,
            "btts":              "",
            "btts_win":          "",
            "over25":            "",
            "correct_score":     "",
            "source":            "predictz.com",
            "scraped_at":        datetime.now(timezone.utc).isoformat(),
        }

    return results


def parse_btts(text: str) -> dict[str, str]:
    lines = _lines(text)
    pred_map = _pred_map_before_preview(lines, BTTS_PRED)
    out: dict[str, str] = {}
    for line in lines:
        ml = MATCH_LINK.match(line)
        if not ml:
            continue
        match_id = ml.group(4)
        raw = pred_map.get(match_id, "")
        m = BTTS_PRED.match(raw)
        if m:
            out[match_id] = f"BTTS {m.group(1)}"
    return out


def parse_ou(text: str) -> dict[str, str]:
    lines = _lines(text)
    pred_map = _pred_map_before_preview(lines, OU_PRED)
    out: dict[str, str] = {}
    for line in lines:
        ml = MATCH_LINK.match(line)
        if not ml:
            continue
        match_id = ml.group(4)
        raw = pred_map.get(match_id, "")
        m = OU_PRED.match(raw)
        if m:
            out[match_id] = f"{m.group(1)} 2.5"
    return out


def parse_btts_win(text: str) -> dict[str, str]:
    lines = _lines(text)
    pred_map = _pred_map_before_preview(lines, BW_PRED)
    out: dict[str, str] = {}
    for line in lines:
        ml = MATCH_LINK.match(line)
        if not ml:
            continue
        match_id = ml.group(4)
        raw = pred_map.get(match_id, "")
        if raw:
            out[match_id] = raw
    return out


def parse_score(text: str) -> dict[str, str]:
    """Correct score appears AFTER [Team1 v Team2] on the correct score page."""
    lines = _lines(text)
    out: dict[str, str] = {}
    for i, line in enumerate(lines):
        ml = MATCH_LINK.match(line)
        if not ml:
            continue
        match_id = ml.group(4)
        for j in range(i + 1, min(i + 30, len(lines))):
            if not lines[j]:
                continue
            sm = SCORE_PRED.match(lines[j])
            if sm:
                out[match_id] = sm.group(1)
                break
            if (
                MATCH_LINK.match(lines[j])
                or MATCH_PREVIEW.search(lines[j])
                or COMP_HEAD.match(lines[j])
            ):
                break
    return out

# ---------------------------------------------------------------------------
# Forebet parsers
# ---------------------------------------------------------------------------

def _fb_split_teams(text: str) -> tuple[str, str]:
    """Split CamelCase/period-concatenated team names at the boundary closest to mid."""
    # Match position where lowercase/digit/period is followed by uppercase
    boundaries = [m.start() for m in re.finditer(r'(?<=[a-z\d.])(?=[A-Z])', text)]
    if not boundaries:
        return text.strip(), ""
    mid = len(text) // 2
    split_at = min(boundaries, key=lambda x: abs(x - mid))
    return text[:split_at].strip(), text[split_at:].strip()


def _fb_ko_utc(date_str: str) -> str | None:
    try:
        dt = datetime.strptime(date_str.strip(), "%m/%d/%Y %I:%M %p")
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except Exception:
        return None


def _fb_comp_name(cc: str, league_code: str) -> str:
    base = FOREBET_COMP.get(cc.lower())
    if base:
        level_m = re.search(r"\d", league_code)
        if level_m and int(level_m.group()) > 1:
            return f"{base} Div {level_m.group()}"
        return base
    return f"{league_code} League"


def parse_forebet_1x2(text: str) -> dict[str, dict]:
    """Parse Forebet 1X2 today page → match winner predictions for 40+ leagues."""
    lines = _lines(text)
    results: dict[str, dict] = {}

    current_cc = ""
    current_comp = ""
    now_utc = datetime.now(timezone.utc)

    i = 0
    while i < len(lines):
        line = lines[i]

        # Competition flag line
        flag_m = FB_FLAG.search(line)
        if flag_m:
            current_cc = flag_m.group(1).lower()
            if current_cc.isdigit():   # skip Forebet internal numeric codes
                i += 1
                continue
            current_comp = _fb_comp_name(current_cc, flag_m.group(2))
            i += 1
            continue

        # Match link
        match_m = FB_MATCH.search(line)
        if not match_m:
            i += 1
            continue

        teams_text = match_m.group(1)
        date_time_str = match_m.group(2)
        match_id = f"fb_{match_m.group(3)}"

        home, away = _fb_split_teams(teams_text)
        if not home or not away:
            i += 1
            continue

        ko_utc = _fb_ko_utc(date_time_str)

        pred_label = home_goals = away_goals = ""
        is_live = False

        for j in range(i + 1, min(i + 18, len(lines))):
            l = lines[j]
            if FB_LIVE.match(l) or FB_SCORE.match(l):
                is_live = True
                break
            pred_m = FB_PRED.match(l)
            if pred_m:
                pred_label = pred_m.group(1)
                home_goals = pred_m.group(2)
                away_goals = pred_m.group(3)
                break
            # Stop scanning at next match block
            if FB_FLAG.search(l) or FB_MATCH.search(l):
                break

        if is_live or not pred_label:
            i += 1
            continue

        wdw = pred_label if pred_label in ("1", "2", "X") else ""

        results[match_id] = {
            "id":                match_id,
            "home":              home,
            "away":              away,
            "competition":       current_comp,
            "comp_slug":         current_cc,
            "ko_display":        "Today",
            "ko_utc":            ko_utc,
            "match_winner":      pred_label,
            "match_winner_label": f"{pred_label} {home_goals}-{away_goals}",
            "wdw":               wdw,
            "home_odds":         "",
            "draw_odds":         "",
            "away_odds":         "",
            "btts":              "",
            "btts_win":          "",
            "over25":            "",
            "correct_score":     f"{home_goals}-{away_goals}",
            "source":            "forebet.com",
            "scraped_at":        now_utc.isoformat(),
        }
        i += 1

    return results


def parse_forebet_btts(text: str, existing: dict[str, dict]) -> None:
    """Enrich existing forebet matches with BTTS prediction from the BTTS page."""
    lines = _lines(text)
    i = 0
    while i < len(lines):
        match_m = FB_MATCH.search(lines[i])
        if match_m:
            mid = f"fb_{match_m.group(3)}"
            for j in range(i + 1, min(i + 12, len(lines))):
                l = lines[j]
                if FB_LIVE.match(l) or FB_SCORE.match(l):
                    break
                m = re.match(r'^(Yes|No)\d+-\d+$', l, re.I)
                if not m:
                    m = re.match(r'^(Yes|No)$', l, re.I)
                if m and mid in existing:
                    existing[mid]["btts"] = f"BTTS {m.group(1).capitalize()}"
                    break
                if FB_FLAG.search(l) or FB_MATCH.search(l):
                    break
        i += 1


def parse_forebet_ou(text: str, existing: dict[str, dict]) -> None:
    """Enrich existing forebet matches with Over/Under 2.5 from the OU page."""
    lines = _lines(text)
    i = 0
    while i < len(lines):
        match_m = FB_MATCH.search(lines[i])
        if match_m:
            mid = f"fb_{match_m.group(3)}"
            for j in range(i + 1, min(i + 12, len(lines))):
                l = lines[j]
                if FB_LIVE.match(l) or FB_SCORE.match(l):
                    break
                m = re.match(r'^(Over|Under)\d+-\d+$', l, re.I)
                if not m:
                    m = re.match(r'^(Over|Under) 2\.5$', l, re.I)
                if m and mid in existing:
                    existing[mid]["over25"] = f"{m.group(1).capitalize()} 2.5"
                    break
                if FB_FLAG.search(l) or FB_MATCH.search(l):
                    break
        i += 1


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# WC2026 baseline — always-on, no Firecrawl needed
# ---------------------------------------------------------------------------

# TheSportsDB's free tier carries no World Cup 2026 fixtures at all (verified:
# eventsday.php returns only minor US leagues for WC2026 match dates), so the
# schedule comes from openfootball instead — it ships the full fixture list
# with date/time/round and is updated with live scores as the tournament progresses.
OPENFOOTBALL_WC_URL = "https://raw.githubusercontent.com/openfootball/world-cup.json/master/2026/worldcup.json"
_HTTP_HDR  = {"User-Agent": "Mozilla/5.0 (compatible; SifuFinds/2.0)"}
_OF_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})\s*UTC([+-]\d+)?")
_PLACEHOLDER_TEAM_RE = re.compile(r"^[WL]\d+$")


def _parse_openfootball_kickoff(date_str: str, time_str: str) -> datetime | None:
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

_WC_TIPS: dict[tuple[str, str], dict] = {
    ("Spain", "Cape Verde"):         {"wdw": "1", "label": "Spain To Win",      "over25": "Over 2.5",  "btts": "BTTS No",  "cs": "3-0",  "conf": 78, "h": "1.25", "d": "5.50", "a": "14.00"},
    ("Belgium", "Egypt"):            {"wdw": "1", "label": "Belgium to Win",    "over25": "Over 1.5",  "btts": "BTTS No",  "cs": "2-0",  "conf": 72, "h": "1.55", "d": "3.90", "a": "6.50"},
    ("Saudi Arabia", "Uruguay"):     {"wdw": "2", "label": "Uruguay to Win",    "over25": "Over 2.5",  "btts": "BTTS Yes", "cs": "1-3",  "conf": 68, "h": "3.50", "d": "3.40", "a": "2.10"},
    ("Iran", "New Zealand"):         {"wdw": "1", "label": "Iran to Win",       "over25": "Under 2.5", "btts": "BTTS No",  "cs": "1-0",  "conf": 65, "h": "2.10", "d": "3.30", "a": "3.80"},
    ("France", "Senegal"):           {"wdw": "1", "label": "France to Win",     "over25": "Over 2.5",  "btts": "BTTS No",  "cs": "2-0",  "conf": 75, "h": "1.55", "d": "4.00", "a": "6.00"},
    ("Argentina", "Algeria"):        {"wdw": "1", "label": "Argentina to Win",  "over25": "Over 2.5",  "btts": "BTTS No",  "cs": "2-0",  "conf": 80, "h": "1.30", "d": "5.50", "a": "9.00"},
    ("Austria", "Jordan"):           {"wdw": "1", "label": "Austria to Win",    "over25": "Over 2.5",  "btts": "BTTS No",  "cs": "3-0",  "conf": 74, "h": "1.45", "d": "4.50", "a": "7.00"},
    ("England", "Croatia"):          {"wdw": "1", "label": "England to Win",    "over25": "Over 2.5",  "btts": "BTTS Yes", "cs": "2-1",  "conf": 72, "h": "1.50", "d": "4.00", "a": "6.50"},
    ("Uzbekistan", "Colombia"):      {"wdw": "2", "label": "Colombia to Win",   "over25": "Over 2.5",  "btts": "BTTS Yes", "cs": "0-2",  "conf": 68, "h": "4.00", "d": "3.50", "a": "1.95"},
    ("Canada", "Qatar"):             {"wdw": "1", "label": "Canada to Win",     "over25": "Over 2.5",  "btts": "BTTS No",  "cs": "2-0",  "conf": 67, "h": "1.75", "d": "3.50", "a": "5.00"},
    ("Germany", "Scotland"):         {"wdw": "1", "label": "Germany to Win",    "over25": "Over 3.5",  "btts": "BTTS Yes", "cs": "3-1",  "conf": 82, "h": "1.35", "d": "5.00", "a": "8.50"},
    ("Portugal", "Czech Republic"):  {"wdw": "1", "label": "Portugal to Win",   "over25": "Over 2.5",  "btts": "BTTS No",  "cs": "2-0",  "conf": 76, "h": "1.40", "d": "4.80", "a": "7.50"},
    ("Brazil", "Costa Rica"):        {"wdw": "1", "label": "Brazil to Win",     "over25": "Over 2.5",  "btts": "BTTS No",  "cs": "3-0",  "conf": 82, "h": "1.25", "d": "6.00", "a": "11.00"},
    ("Morocco", "Australia"):        {"wdw": "1", "label": "Morocco to Win",    "over25": "Over 1.5",  "btts": "BTTS No",  "cs": "2-0",  "conf": 68, "h": "1.75", "d": "3.60", "a": "4.50"},
    ("USA", "Jamaica"):              {"wdw": "1", "label": "USA to Win",        "over25": "Over 2.5",  "btts": "BTTS No",  "cs": "3-0",  "conf": 74, "h": "1.40", "d": "4.50", "a": "8.00"},
    ("Mexico", "South Africa"):      {"wdw": "1", "label": "Mexico to Win",     "over25": "Over 1.5",  "btts": "BTTS No",  "cs": "2-0",  "conf": 66, "h": "1.80", "d": "3.40", "a": "4.50"},
}


def fetch_wc_predictions(now_utc: datetime) -> list[dict]:
    """Build verified WC2026 prediction records from the openfootball fixture schedule."""
    ts = now_utc.isoformat()
    window_start = now_utc - timedelta(minutes=90)
    window_end = now_utc + timedelta(days=8)
    predictions: list[dict] = []

    try:
        r = _req.get(OPENFOOTBALL_WC_URL, headers=_HTTP_HDR, timeout=12)
        matches = r.json().get("matches", [])
    except Exception as ex:
        print(f"[warn] open-football: {ex}", file=sys.stderr)
        return predictions

    for m in matches:
        home = m.get("team1", "")
        away = m.get("team2", "")
        if not home or not away:
            continue
        if _PLACEHOLDER_TEAM_RE.match(home) or _PLACEHOLDER_TEAM_RE.match(away):
            continue  # bracket slot not yet resolved (e.g. "W89 vs W90")

        kickoff = _parse_openfootball_kickoff(m.get("date", ""), m.get("time", ""))
        if kickoff is None or not (window_start <= kickoff <= window_end):
            continue  # already played or too far out

        score = m.get("score") or {}
        if score.get("p") or score.get("et") or score.get("ft"):
            continue  # final result already in — nothing left to predict

        ko_display = f"{kickoff.day} {kickoff.strftime('%b')} · {kickoff.strftime('%H:%M')} UTC"
        round_name = m.get("round") or ""
        comp_label = f"FIFA World Cup 2026 · {round_name}" if round_name else "FIFA World Cup 2026"

        t = _WC_TIPS.get((home, away), {
            "wdw": "1", "label": f"{home} to Win", "over25": "Over 1.5",
            "btts": "", "cs": "", "conf": 60, "h": "2.00", "d": "3.30", "a": "3.50",
        })
        mw = "Home" if t["wdw"] == "1" else ("Away" if t["wdw"] == "2" else "Draw")

        predictions.append({
            "id": f"wc_{m.get('num')}",
            "home": home,
            "away": away,
            "competition": comp_label,
            "comp_slug": "world-cup-2026",
            "ko_display": ko_display,
            "ko_utc": kickoff.isoformat(),
            "match_winner": mw,
            "match_winner_label": t["label"],
            "wdw": t["wdw"],
            "home_odds": t.get("h", ""),
            "draw_odds": t.get("d", ""),
            "away_odds": t.get("a", ""),
            "btts": t.get("btts", ""),
            "btts_win": "",
            "over25": t.get("over25", ""),
            "correct_score": t.get("cs", ""),
            "source": "openfootball+fst",
            "scraped_at": ts,
            "flag": "🌍",
            "confidence": t["conf"],
        })

    return predictions


def load_cache() -> list[dict]:
    try:
        data = json.loads(OUT_PATH.read_text())
        return data.get("predictions", [])
    except Exception:
        return []


_MAX_CACHE_AGE = timedelta(hours=6)


def _is_recent(scraped_at: str) -> bool:
    """Guard against resurrecting week-old cached picks when a scrape fails.

    predictz.com never exposes a real kickoff time (ko_utc is always None for its
    matches), so isUpcoming() on the frontend can't filter stale predictz entries by
    itself — without this cap, a single successful scrape's matches get replayed as
    "current" tips indefinitely every time predictz.com scraping fails afterward.
    """
    try:
        scraped = datetime.fromisoformat(scraped_at)
    except (TypeError, ValueError):
        return False
    return datetime.now(timezone.utc) - scraped < _MAX_CACHE_AGE

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    now_str = datetime.now(timezone.utc).isoformat()
    log: list[dict[str, Any]] = []

    raw: dict[str, str] = {}
    for page, url in URLS.items():
        try:
            print(f"[scraping] {page} …", file=sys.stderr)
            raw[page] = scrape(url)
            log.append({"page": page, "status": "ok", "ts": now_str})
            print(f"  [ok] {page} — {len(raw[page])} chars", file=sys.stderr)
        except Exception as exc:
            log.append({"page": page, "status": "error", "error": str(exc)[:200], "ts": now_str})
            print(f"  [fail] {page}: {exc}", file=sys.stderr)

    # ── Predictz: base match records ──────────────────────────────────────────
    matches: dict[str, dict] = {}

    if "main" in raw:
        matches = parse_main(raw["main"])
        print(f"[parse] predictz main → {len(matches)} matches", file=sys.stderr)

        for page_key, parser_fn, field in [
            ("btts",  parse_btts,     "btts"),
            ("ou25",  parse_ou,       "over25"),
            ("bw",    parse_btts_win, "btts_win"),
            ("score", parse_score,    "correct_score"),
        ]:
            if page_key not in raw:
                continue
            n = 0
            for mid, val in parser_fn(raw[page_key]).items():
                if mid in matches:
                    matches[mid][field] = val
                    n += 1
            print(f"[parse] predictz {page_key} → {n} enriched", file=sys.stderr)
    else:
        print("[warn] predictz main scrape failed — using cache for predictz matches", file=sys.stderr)
        for m in load_cache():
            if m.get("source") == "predictz.com" and _is_recent(m.get("scraped_at", "")):
                matches[m["id"]] = m

    # ── Forebet: supplementary matches from 60+ leagues ───────────────────────
    fb_matches: dict[str, dict] = {}

    if "forebet_1x2" in raw:
        fb_matches = parse_forebet_1x2(raw["forebet_1x2"])
        print(f"[parse] forebet 1x2 → {len(fb_matches)} matches", file=sys.stderr)

        if "forebet_btts" in raw:
            parse_forebet_btts(raw["forebet_btts"], fb_matches)
            print(f"[parse] forebet btts enrichment done", file=sys.stderr)

        if "forebet_ou" in raw:
            parse_forebet_ou(raw["forebet_ou"], fb_matches)
            print(f"[parse] forebet ou enrichment done", file=sys.stderr)
    else:
        print("[warn] forebet scrape failed — supplementary leagues unavailable", file=sys.stderr)

    # ── Always-on: WC2026 baseline from TheSportsDB (no Firecrawl needed) ────────
    now_utc = datetime.now(timezone.utc)
    wc_preds = fetch_wc_predictions(now_utc)
    print(f"[wc2026] {len(wc_preds)} verified matches from openfootball", file=sys.stderr)

    # Merge: predictz takes precedence over forebet for same match
    all_matches: dict[str, dict] = {**fb_matches, **matches}

    scraped = sorted(
        all_matches.values(),
        key=lambda p: (p.get("ko_utc") or "zzz", p["home"]),
    )

    # WC2026 first, then scraped (deduped by id)
    seen_ids: set[str] = {p["id"] for p in wc_preds}
    scraped_extra = [p for p in scraped if p.get("id") not in seen_ids]
    predictions = wc_preds + scraped_extra

    # Never overwrite good cached data with an empty result
    if not predictions:
        cached = load_cache()
        if cached:
            print("[warn] all scrapers returned 0 results — keeping existing predictions.json", file=sys.stderr)
            return
        print("[warn] 0 predictions and no cache — writing empty file", file=sys.stderr)

    sources = list({p.get("source", "") for p in predictions if p.get("source")})
    OUT_PATH.write_text(json.dumps({
        "updated":     now_str,
        "source":      ", ".join(sources),
        "count":       len(predictions),
        "scrape_log":  log,
        "predictions": predictions,
    }, ensure_ascii=False, indent=2))

    print(f"[done] {len(predictions)} predictions ({len(wc_preds)} wc2026 + {len(matches)} predictz + {len(fb_matches)} forebet) → {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
