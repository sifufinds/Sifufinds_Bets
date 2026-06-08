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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    """Split CamelCase-concatenated team names by finding the boundary closest to mid."""
    boundaries = [m.start() + 1 for m in re.finditer(r'(?<=[a-z\d])(?=[A-Z])', text)]
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

def load_cache() -> list[dict]:
    try:
        data = json.loads(OUT_PATH.read_text())
        return data.get("predictions", [])
    except Exception:
        return []

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
            if m.get("source") == "predictz.com":
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

    # Merge: predictz takes precedence over forebet for same match
    all_matches: dict[str, dict] = {**fb_matches, **matches}

    predictions = sorted(
        all_matches.values(),
        key=lambda p: (p.get("ko_utc") or "zzz", p["home"]),
    )

    sources = list({p["source"] for p in predictions})
    OUT_PATH.write_text(json.dumps({
        "updated":     now_str,
        "source":      ", ".join(sources),
        "count":       len(predictions),
        "scrape_log":  log,
        "predictions": predictions,
    }, ensure_ascii=False, indent=2))

    print(f"[done] {len(predictions)} predictions ({len(matches)} predictz + {len(fb_matches)} forebet) → {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
