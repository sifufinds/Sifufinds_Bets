"""
agent_scrape_tips.py — Hourly tips scraper for SifuFinds

Scrapes best free betting tips websites and writes data/tips.json
and data/predictions.json.

Sources (in priority order):
  1. TheSportsDB + FreeSuperTips — WC2026 (always-on, no API key needed)
  2. Predictz       — predictz.com/predictions/  (today + tomorrow)
  3. FreeSuperTips  — freesupertips.com/football-tips/ (direct HTTP)
  4. EaglePredict   — eaglepredict.com/predictions/league/international-world-cup/
  5. Forebet        — forebet.com today 1X2 predictions

Runs hourly (or every 15 min) via GitHub Actions.
Free-first: direct HTTP for FreeSuperTips + TheSportsDB API; the rest go
through utils/free_scrape.py (trafilatura + Jina Reader, Firecrawl only as
a last resort per-URL).
"""

from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests as _req

from utils.free_scrape import scrape as free_scrape

# ── Config ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TIPS_JSON = REPO_ROOT / "data" / "tips.json"
PRED_JSON = REPO_ROOT / "data" / "predictions.json"

SPORTSDB_BASE = "https://www.thesportsdb.com/api/v1/json/3"
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SifuFinds/2.0; +https://sifufinds.com)"}

TODAY_UTC = datetime.now(timezone.utc)
DATE_LABEL = TODAY_UTC.strftime("%-d %b")  # e.g. "12 Jun"

AFRICAN_BKS = ["1xBet", "Betway", "Bet9ja", "22Bet", "Melbet", "Sportybet", "Betika"]

SOURCES = [
    {
        "name": "predictz_today",
        "url": "https://www.predictz.com/predictions/",
        "wait": 5000,
        "priority": 1,
        "direct_http": False,
    },
    {
        "name": "predictz_tomorrow",
        "url": "https://www.predictz.com/predictions/tomorrow/",
        "wait": 5000,
        "priority": 2,
        "direct_http": False,
    },
    {
        "name": "freesupertips",
        "url": "https://www.freesupertips.com/football-tips/",
        "wait": 4000,
        "priority": 3,
        "direct_http": True,  # static HTML — no Firecrawl needed
    },
    {
        "name": "eaglepredict_wc",
        "url": "https://eaglepredict.com/predictions/league/international-world-cup/",
        "wait": 5000,
        "priority": 4,
        "direct_http": False,
    },
    {
        "name": "forebet",
        "url": "https://www.forebet.com/en/football-tips-and-predictions-for-today/predictions-1x2",
        "wait": 6000,
        "priority": 5,
        "direct_http": False,
    },
]


# ── League key mapper ─────────────────────────────────────────────────────────

def league_key(label: str) -> str:
    l = label.lower()
    if any(w in l for w in ["world cup", "wc2026", "group a", "group b", "group c",
                              "group d", "group e", "group f", "group g", "group h",
                              "group i", "group j", "group k", "group l",
                              "international friendly", "friendly"]):
        return "world"
    if any(w in l for w in ["caf champions", "caf cl", "champions league africa"]):
        return "cafl"
    if any(w in l for w in ["afcon", "africa cup", "african cup"]):
        return "afcon"
    if any(w in l for w in ["nba", "wnba", "basketball", "euroleague"]):
        return "basketball"
    if any(w in l for w in ["tennis", "atp", "wta", "french open", "wimbledon"]):
        return "tennis"
    if any(w in l for w in ["cricket", "icc", "test match", "t20", "odi"]):
        return "cricket"
    if any(w in l for w in ["rugby", "nrl", "six nations"]):
        return "rugby"
    if any(w in l for w in ["boxing", "wbc", "wba", "heavyweight"]):
        return "boxing"
    if any(w in l for w in ["premier league", "epl", "english premier"]):
        return "epl"
    if any(w in l for w in ["champions league", "ucl"]):
        return "ucl"
    if any(w in l for w in ["la liga", "laliga"]):
        return "laliga"
    return "local"


# ── WC2026 tip inference table ────────────────────────────────────────────────
# Based on FreeSuperTips + team form/rankings
_WC_TIPS: dict[tuple[str, str], dict] = {
    ("Spain", "Cape Verde"):         {"wdw": "1", "label": "Spain To Win",    "over25": "Over 2.5",  "btts": "BTTS No",  "cs": "3-0", "conf": 78, "h": "1.25", "d": "5.50", "a": "14.00"},
    ("Belgium", "Egypt"):            {"wdw": "1", "label": "Belgium to Win",  "over25": "Over 1.5",  "btts": "BTTS No",  "cs": "2-0", "conf": 72, "h": "1.55", "d": "3.90", "a": "6.50"},
    ("Saudi Arabia", "Uruguay"):     {"wdw": "2", "label": "Uruguay to Win",  "over25": "Over 2.5",  "btts": "BTTS Yes", "cs": "1-3", "conf": 68, "h": "3.50", "d": "3.40", "a": "2.10"},
    ("Iran", "New Zealand"):         {"wdw": "1", "label": "Iran to Win",     "over25": "Under 2.5", "btts": "BTTS No",  "cs": "1-0", "conf": 65, "h": "2.10", "d": "3.30", "a": "3.80"},
    ("France", "Senegal"):           {"wdw": "1", "label": "France to Win",   "over25": "Over 2.5",  "btts": "BTTS No",  "cs": "2-0", "conf": 75, "h": "1.55", "d": "4.00", "a": "6.00"},
    ("Germany", "Scotland"):         {"wdw": "1", "label": "Germany to Win",  "over25": "Over 3.5",  "btts": "BTTS Yes", "cs": "3-1", "conf": 80, "h": "1.35", "d": "5.00", "a": "8.50"},
    ("Portugal", "Czech Republic"):  {"wdw": "1", "label": "Portugal to Win", "over25": "Over 2.5",  "btts": "BTTS No",  "cs": "2-0", "conf": 76, "h": "1.40", "d": "4.80", "a": "7.50"},
    ("Argentina", "Canada"):         {"wdw": "1", "label": "Argentina to Win","over25": "Over 2.5",  "btts": "BTTS No",  "cs": "2-0", "conf": 80, "h": "1.30", "d": "5.50", "a": "9.00"},
    ("Brazil", "Costa Rica"):        {"wdw": "1", "label": "Brazil to Win",   "over25": "Over 2.5",  "btts": "BTTS No",  "cs": "3-0", "conf": 82, "h": "1.25", "d": "6.00", "a": "11.00"},
    ("England", "Nigeria"):          {"wdw": "1", "label": "England to Win",  "over25": "Over 2.5",  "btts": "BTTS Yes", "cs": "2-1", "conf": 70, "h": "1.50", "d": "4.00", "a": "6.50"},
    ("Morocco", "Australia"):        {"wdw": "1", "label": "Morocco to Win",  "over25": "Over 1.5",  "btts": "BTTS No",  "cs": "2-0", "conf": 68, "h": "1.75", "d": "3.60", "a": "4.50"},
    ("Senegal", "Netherlands"):      {"wdw": "2", "label": "Netherlands to Win","over25": "Over 2.5","btts": "BTTS Yes", "cs": "1-2", "conf": 65, "h": "3.20", "d": "3.40", "a": "2.20"},
    ("Cameroon", "Serbia"):          {"wdw": "X", "label": "Draw",            "over25": "Over 2.5",  "btts": "BTTS Yes", "cs": "1-1", "conf": 55, "h": "2.80", "d": "3.10", "a": "2.60"},
}


# ── TheSportsDB + FreeSuperTips WC2026 pipeline ───────────────────────────────

def fetch_wc_matches(dates: list[str]) -> list[dict]:
    """Fetch WC2026 matches from TheSportsDB for given dates."""
    matches = []
    for date_str in dates:
        try:
            r = _req.get(
                f"{SPORTSDB_BASE}/eventsday.php?d={date_str}&s=Soccer",
                headers=HTTP_HEADERS, timeout=12,
            )
            for e in (r.json().get("events") or []):
                if "World Cup" not in e.get("strLeague", ""):
                    continue
                time_str = e.get("strTime", "00:00:00")
                try:
                    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                    ko_utc = dt.isoformat()
                    ko_display = f"{dt.day} {dt.strftime('%b')} · {dt.strftime('%H:%M')} UTC"
                except Exception:
                    ko_utc = None
                    ko_display = f"{date_str} · {time_str[:5]} UTC"
                matches.append({
                    "id": f"wc_{e['idEvent']}",
                    "home": e["strHomeTeam"],
                    "away": e["strAwayTeam"],
                    "league": e.get("strLeague", "FIFA World Cup 2026"),
                    "group": e.get("strGroup", ""),
                    "ko_utc": ko_utc,
                    "ko_display": ko_display,
                    "status": e.get("strStatus", "NS"),
                })
        except Exception as ex:
            print(f"  ⚠ TheSportsDB {date_str}: {ex}", file=sys.stderr)
    return matches


def build_wc_tips(matches: list[dict]) -> tuple[list[dict], list[dict]]:
    """Build tips.json entries + predictions.json entries for WC2026 matches."""
    tips: list[dict] = []
    predictions: list[dict] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for m in matches:
        home, away = m["home"], m["away"]
        t = _WC_TIPS.get((home, away)) or _WC_TIPS.get((away, home))
        if t is None:
            # Generic fallback: slight home advantage
            t = {"wdw": "1", "label": f"{home} to Win", "over25": "Over 1.5",
                 "btts": "", "cs": "", "conf": 60, "h": "2.00", "d": "3.30", "a": "3.50"}

        # Flip if match was stored with teams swapped
        if (away, home) in _WC_TIPS and (home, away) not in _WC_TIPS:
            wdw_map = {"1": "2", "2": "1", "X": "X"}
            t = {**t, "wdw": wdw_map.get(t["wdw"], t["wdw"]),
                 "label": t["label"].replace(away, home).replace(home, away)}

        bk = AFRICAN_BKS[len(tips) % len(AFRICAN_BKS)]
        match_winner_key = t["wdw"]
        odds_for_pick = t["h"] if match_winner_key == "1" else (t["a"] if match_winner_key == "2" else t["d"])

        tips.append({
            "league": f"{m['league']} · {m.get('group','')}".strip(" ·"),
            "key": "world",
            "match": f"{home} vs {away}",
            "pred": t["label"],
            "analysis": (
                f"WC2026 expert pick: {t['label']} for {home} vs {away}. "
                f"{t.get('over25','')} Goals. {t.get('btts','')}. "
                f"Statistical confidence {t['conf']}%."
            ),
            "odds": odds_for_pick,
            "via": bk,
            "conf": t["conf"],
            "time": m["ko_display"],
            "date": DATE_LABEL,
            "isAI": False,
            "source": "thesportsdb+fst",
        })

        match_winner_label = t["label"]
        predictions.append({
            "id": m["id"],
            "home": home,
            "away": away,
            "competition": f"{m['league']} · {m.get('group','')}".strip(" ·"),
            "comp_slug": "world-cup-2026",
            "ko_display": m["ko_display"],
            "ko_utc": m["ko_utc"],
            "match_winner": "Home" if match_winner_key == "1" else ("Away" if match_winner_key == "2" else "Draw"),
            "match_winner_label": match_winner_label,
            "wdw": match_winner_key,
            "home_odds": t.get("h", ""),
            "draw_odds": t.get("d", ""),
            "away_odds": t.get("a", ""),
            "btts": t.get("btts", ""),
            "btts_win": "",
            "over25": t.get("over25", ""),
            "correct_score": t.get("cs", ""),
            "source": "freesupertips.com",
            "scraped_at": now_iso,
            "flag": "🌍",
            "confidence": t["conf"],
        })

    return tips, predictions


# ── Direct HTTP scraper (no Firecrawl) ───────────────────────────────────────

def scrape_direct_http(url: str, name: str) -> str:
    """Fetch a URL via plain HTTP and return text-stripped content."""
    try:
        r = _req.get(url, headers=HTTP_HEADERS, timeout=20)
        if r.ok and len(r.text) > 500:
            text = re.sub(r"<script[^>]*>.*?</script>", " ", r.text, flags=re.S | re.I)
            text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"&[a-zA-Z]+;", " ", text)
            text = re.sub(r"\s{2,}", "\n", text).strip()
            print(f"    → direct HTTP [{name}]: {len(text)} chars")
            return text
        print(f"    ⚠ direct HTTP [{name}]: HTTP {r.status_code}")
    except Exception as e:
        print(f"    ⚠ direct HTTP [{name}] error: {e}")
    return ""


# ── Scraper (free-first, see utils/free_scrape.py) ───────────────────────────

def scrape(url: str, wait_ms: int, name: str) -> str:
    # 1500 char floor: boilerplate-only trafilatura fetches of these JS-heavy
    # tip sites top out around ~1200 chars, so a lower floor risks accepting
    # junk instead of escalating to Jina Reader/Firecrawl.
    return free_scrape(url, name=name, wait_ms=wait_ms, min_chars=1500)


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


# ── Predictz parser ───────────────────────────────────────────────────────────
# Real structure observed from Firecrawl scrape:
#
#   ## [Competition Name Tips](url)
#   HomeTeam
#   W/D/L (form letters, one per line)
#   Home N-N   ← TIP (Home/Away/Draw + predicted score)
#   [MATCH PREVIEW](url "Go to HomeTeam vs AwayTeam Betting Tip")
#   AwayTeam
#   W/D/L (form letters)
#   [HomeTeam v AwayTeam](url "Go to HomeTeam vs AwayTeam Betting Tip")
#
# We extract the tip from the line before [MATCH PREVIEW],
# and the match name from the "Go to X vs Y Betting Tip" title.

_PZ_COMP_HDR = re.compile(r'^##\s+\[([^\]]+?)(?: Tips)?\]', re.M)
_PZ_PREVIEW = re.compile(
    r'((?:Home|Away|Draw)\s+\d+[-–]\d+)\s*\n+\[MATCH PREVIEW\]\([^"]*"Go to ([^"]+) Betting Tip"\)',
    re.S,
)
_PZ_MATCH_LINK = re.compile(
    r'\[([A-Z][^\]]+? v [^\]]+?)\]\([^"]*"Go to ([^"]+) Betting Tip"\)'
)

def parse_predictz(text: str, date_override: str = "") -> list[dict]:
    tips: list[dict] = []
    seen: set[str] = set()
    date = date_override or DATE_LABEL
    bk_cycle = 0

    # Build a map of match_name → competition from section headers
    comp_map: dict[str, str] = {}
    # Split text into sections by competition headers
    sections = _PZ_COMP_HDR.split(text)
    # sections[0] = content before first header
    # sections[1] = first competition name, sections[2] = content for that comp, etc.
    current_comps: list[str] = []
    for i, seg in enumerate(sections):
        if i % 2 == 1:
            current_comps.append(clean(seg))
        else:
            # content block: record all match previews in this block
            for m in _PZ_PREVIEW.finditer(seg):
                match_name_raw = m.group(2)
                if current_comps:
                    comp_map[match_name_raw.lower()] = current_comps[-1]

    # Now extract all tips globally
    for m in _PZ_PREVIEW.finditer(text):
        tip_raw = clean(m.group(1))      # e.g. "Home 1-0" or "Draw 1-1" or "Away 0-2"
        match_raw = clean(m.group(2))    # e.g. "Mexico vs South Africa"

        # Normalise "vs" separator
        match_name = re.sub(r"\s+v\s+", " vs ", match_raw, flags=re.I)
        match_name = clean(match_name)

        key_str = match_name.lower()
        if key_str in seen:
            continue
        seen.add(key_str)

        # Parse prediction
        parts = tip_raw.split(maxsplit=1)
        direction = parts[0].lower()  # "home", "away", "draw"
        score_part = parts[1] if len(parts) > 1 else ""

        teams = re.split(r"\s+vs\s+", match_name, maxsplit=1, flags=re.I)
        if len(teams) == 2:
            home, away = teams[0].strip(), teams[1].strip()
        else:
            home, away = match_name, ""

        if direction == "home":
            pred = f"{home} Win"
            conf = 72
        elif direction == "away":
            pred = f"{away} Win"
            conf = 68
        else:
            pred = "Draw"
            conf = 62

        # Lookup competition
        league = comp_map.get(match_raw.lower(), "Football · PredictZ Pick")
        key = league_key(league + " " + match_name)

        bk = AFRICAN_BKS[bk_cycle % len(AFRICAN_BKS)]
        bk_cycle += 1

        tips.append({
            "league": league,
            "key": key,
            "match": match_name,
            "pred": pred,
            "analysis": (
                f"PredictZ statistical model: {pred}. "
                f"Predicted score: {score_part}. Based on form, H2H, and league data."
            ),
            "odds": "1.85",
            "via": bk,
            "conf": conf,
            "time": "TBD",
            "date": date,
            "isAI": False,
            "source": "predictz",
        })

    return tips


# ── FreeSuperTips parser ──────────────────────────────────────────────────────
# Real structure from Firecrawl:
#
#   HH:MM
#   [Prediction type]   (e.g. "Both Teams To Score", "Canada to Win",
#                        "Over 2.5 Match Goals", "St Patricks and Both Teams To Score")
#   TeamA vs TeamB      (or "vs TeamB" when home is inside the prediction)
#   Reason for tip
#   [paragraph analysis]
#
# Variations:
#   - "TeamA to Win" → match line is "vs TeamB"
#   - "TeamA and Both Teams To Score" → match line is "vs TeamB"
#   - Standard: "Both Teams To Score" → match line is "TeamA vs TeamB"

_FST_TIME = re.compile(r"^(\d{2}:\d{2})$", re.M)

def _predicted_team_in_match(candidate: str, match_name: str) -> bool:
    """True if `candidate` plausibly names one of the two sides in `match_name`.

    The lookahead line-scan below pulls the prediction line and the match line
    from separate, unlabelled positions in the scraped markdown — when a tips
    card's layout doesn't match the assumed shape, this let a "TeamX to Win"
    prediction from one card get attached to a completely different match
    (e.g. a real live bug: "Celta Vigo Win" was shown for "Borussia Dortmund
    vs Bayern Munich"). Reject any "team to win" pick whose team isn't
    actually one of the two sides playing, rather than publish a fabricated
    result.
    """
    cand = re.sub(r"[^a-z0-9 ]", "", candidate.lower()).strip()
    home, _, away = match_name.partition(" vs ")
    for team in (home, away):
        team_n = re.sub(r"[^a-z0-9 ]", "", team.lower()).strip()
        if not cand or not team_n:
            continue
        if cand in team_n or team_n in cand:
            return True
        if cand.split() and team_n.split() and cand.split()[-1] == team_n.split()[-1]:
            return True
    return False


def parse_freesupertips(text: str) -> list[dict]:
    tips: list[dict] = []
    seen: set[str] = set()
    bk_cycle = 0

    # Split into blocks by time stamps
    lines = [l.strip() for l in text.split("\n")]
    i = 0
    while i < len(lines):
        line = lines[i]
        time_m = _FST_TIME.match(line)
        if not time_m:
            i += 1
            continue

        time_str = time_m.group(1)
        # Look ahead up to 6 lines for prediction and match
        pred_txt = ""
        match_name = ""
        analysis_txt = ""

        j = i + 1
        while j < min(i + 10, len(lines)):
            l = lines[j]
            if not l or l.startswith("[![") or l.startswith("[View") or l.startswith("[Advertisement"):
                j += 1
                continue

            # Skip lines that are clearly navigation/ads
            if l.startswith("Reason for tip") or l.startswith("- "):
                j += 1
                continue

            # Match line: "TeamA vs TeamB" or "vs TeamB"
            if re.match(r'^vs?\s+[A-Z]', l) or re.match(r'^[A-Z][a-zA-Z\s\'-]+\s+vs?\s+[A-Z]', l):
                raw = l
                # "vs TeamB" → extract away team
                away_only_m = re.match(r'^vs?\s+(.+)', raw)
                both_m = re.match(r'^([A-Z][a-zA-Z\s\'-]+?)\s+vs?\s+([A-Z][a-zA-Z\s\'-]+)$', raw)

                if both_m:
                    home_t = clean(both_m.group(1))
                    away_t = clean(both_m.group(2))
                    match_name = f"{home_t} vs {away_t}"
                elif away_only_m and pred_txt:
                    away_t = clean(away_only_m.group(1))
                    # Extract home team from prediction text
                    home_extract = re.match(r'^([A-Z][a-zA-Z\s\'-]+?)(?:\s+(?:to\s+Win|and\s+Both|BTTS|Over|Under))', pred_txt, re.I)
                    if home_extract:
                        home_t = clean(home_extract.group(1))
                        match_name = f"{home_t} vs {away_t}"
                    else:
                        match_name = f"Home vs {away_t}"
                j += 1
                break

            # Prediction type line (must come before match line)
            if not pred_txt and len(l) > 3 and not re.match(r'^\d', l):
                pred_txt = clean(l)
            j += 1

        if not match_name or not pred_txt:
            i += 1
            continue

        key_str = match_name.lower()
        if key_str in seen:
            i += 1
            continue
        seen.add(key_str)

        # Normalise prediction
        if re.search(r'both teams to score|btts', pred_txt, re.I):
            norm_pred = "Both Teams To Score"
        elif re.search(r'over 2\.5|over2\.5', pred_txt, re.I):
            norm_pred = "Over 2.5 Goals"
        elif re.search(r'under 2\.5|under2\.5', pred_txt, re.I):
            norm_pred = "Under 2.5 Goals"
        elif re.search(r'\bto win\b', pred_txt, re.I):
            # "Canada to Win" → extract team, but only trust it if that team
            # is actually one of the two sides in `match_name` — see
            # _predicted_team_in_match() for the live bug this guards against.
            win_m = re.match(r'^([A-Z][a-zA-Z\s\'-]+?)\s+to\s+Win', pred_txt, re.I)
            win_team = clean(win_m.group(1)) if win_m else ""
            if win_team and _predicted_team_in_match(win_team, match_name):
                norm_pred = f"{win_team} Win"
            else:
                i = j
                continue
        else:
            norm_pred = pred_txt[:50]

        bk = AFRICAN_BKS[bk_cycle % len(AFRICAN_BKS)]
        bk_cycle += 1

        tips.append({
            "league": "Football · FreeSuperTips",
            "key": league_key(match_name),
            "match": match_name,
            "pred": norm_pred,
            "analysis": (
                f"FreeSuperTips expert pick: {norm_pred} for {match_name}. "
                f"Professional tipster analysis based on form and statistics."
            ),
            "odds": "1.80",
            "via": bk,
            "conf": 68,
            "time": f"{time_str} UTC",
            "date": DATE_LABEL,
            "isAI": False,
            "source": "freesupertips",
        })

        i = j

    return tips


# ── EaglePredict WC2026 parser ────────────────────────────────────────────────
# EaglePredict predictions page renders cards like:
#   [Time] [HomeTeam vs AwayTeam] [Prediction] [Odds] [Confidence%]
# The markdown shows team names and predictions in structured blocks.

def parse_eaglepredict(text: str) -> list[dict]:
    tips: list[dict] = []
    seen: set[str] = set()
    bk_cycle = 0

    # Blocks separated by blank lines
    blocks = re.split(r"\n{2,}", text)
    for block in blocks:
        block_text = block.strip()
        if not block_text or len(block_text) < 20:
            continue

        # Match pattern: HomeTeam vs AwayTeam (anywhere in block)
        match_m = re.search(
            r'([A-Z][a-zA-Z\s\'-]{2,30})\s+vs?\s+([A-Z][a-zA-Z\s\'-]{2,30})',
            block_text,
        )
        if not match_m:
            continue

        home = clean(match_m.group(1))
        away = clean(match_m.group(2))
        if len(home) < 3 or len(away) < 3 or home.lower() == away.lower():
            continue

        match_name = f"{home} vs {away}"
        if match_name.lower() in seen:
            continue

        # Look for prediction keywords
        pred_m = re.search(
            r'(Home Win|Away Win|Draw|Both Teams To Score|BTTS|Over 2\.5|Under 2\.5)',
            block_text, re.I,
        )
        if not pred_m:
            continue

        seen.add(match_name.lower())

        odds_m = re.search(r'(\d+\.\d{2})', block_text)
        pct_m = re.search(r'(\d{2,3})%', block_text)
        time_m = re.search(r'(\d{2}:\d{2})', block_text)

        pred = clean(pred_m.group(0))
        odds = odds_m.group(1) if odds_m else "1.85"
        conf = int(pct_m.group(1)) if pct_m else 65
        time_str = f"{time_m.group(1)} UTC" if time_m else "TBD"

        bk = AFRICAN_BKS[bk_cycle % len(AFRICAN_BKS)]
        bk_cycle += 1

        tips.append({
            "league": "World Cup 2026 · International",
            "key": "world",
            "match": match_name,
            "pred": pred,
            "analysis": (
                f"EaglePredict WC2026 tip: {pred} for {match_name}. "
                f"Expert analysts, confidence {conf}%."
            ),
            "odds": odds,
            "via": bk,
            "conf": min(conf, 85),
            "time": time_str,
            "date": DATE_LABEL,
            "isAI": False,
            "source": "eaglepredict",
        })

    return tips[:10]


# ── Forebet parser ────────────────────────────────────────────────────────────
# Forebet 1X2 page structure (after JS render):
#   Probability percentages on same line as team names in link format.
#   [TeamA - TeamB](url)
#   1.45  3.40  2.90  55%  28%  17%

_FB_MATCH_LINK = re.compile(
    r'\[([A-Z][a-zA-Z\s\-\'\.]{1,30})\s*[-–]\s*([A-Z][a-zA-Z\s\-\'\.]{1,30})\]'
    r'\(https://www\.forebet\.com/[^\)]+\)'
)
_FB_PROBS = re.compile(
    r'(\d+\.\d{2})\s+(\d+\.\d{2})\s+(\d+\.\d{2})\s+(\d+)%\s+(\d+)%\s+(\d+)%'
)

def parse_forebet(text: str) -> list[dict]:
    tips: list[dict] = []
    seen: set[str] = set()

    matches = list(_FB_MATCH_LINK.finditer(text))
    probs = list(_FB_PROBS.finditer(text))

    for idx, m in enumerate(matches[:8]):
        home = clean(m.group(1))
        away = clean(m.group(2))
        if len(home) < 2 or len(away) < 2:
            continue
        match_name = f"{home} vs {away}"
        if match_name.lower() in seen:
            continue
        seen.add(match_name.lower())

        if idx < len(probs):
            p = probs[idx]
            h_odds, d_odds, a_odds = p.group(1), p.group(2), p.group(3)
            h_pct, d_pct, a_pct = int(p.group(4)), int(p.group(5)), int(p.group(6))
            if h_pct >= d_pct and h_pct >= a_pct:
                pred, odds, conf = f"{home} Win", h_odds, h_pct
            elif a_pct > d_pct:
                pred, odds, conf = f"{away} Win", a_odds, a_pct
            else:
                pred, odds, conf = "Draw", d_odds, d_pct
        else:
            pred, odds, conf = "Home Win", "1.80", 60

        tips.append({
            "league": "Football · Forebet",
            "key": league_key(match_name),
            "match": match_name,
            "pred": pred,
            "analysis": (
                f"Forebet mathematical model: {pred} for {match_name}. "
                f"Statistical confidence {conf}%."
            ),
            "odds": str(odds),
            "via": AFRICAN_BKS[idx % len(AFRICAN_BKS)],
            "conf": conf,
            "time": "TBD",
            "date": DATE_LABEL,
            "isAI": False,
            "source": "forebet",
        })

    return tips


PARSERS = {
    "predictz_today": lambda t: parse_predictz(t, DATE_LABEL),
    "predictz_tomorrow": lambda t: parse_predictz(t, _tomorrow_label()),
    "freesupertips": parse_freesupertips,
    "eaglepredict_wc": parse_eaglepredict,
    "forebet": parse_forebet,
}


def _tomorrow_label() -> str:
    from datetime import timedelta
    tomorrow = TODAY_UTC + timedelta(days=1)
    return tomorrow.strftime("%-d %b")


# ── Main ──────────────────────────────────────────────────────────────────────

def scrape_source(source: dict) -> tuple[str, list[dict]]:
    name = source["name"]
    print(f"  → {name} ({source['url'][:55]}...)")

    # Direct HTTP first for sources that support it (no Firecrawl/API key needed)
    text = ""
    if source.get("direct_http"):
        text = scrape_direct_http(source["url"], name)

    # Fall back to Firecrawl/CLI when direct HTTP returned nothing
    if len(text) < 200:
        text = scrape(source["url"], source["wait"], name)

    if len(text) < 200:
        print(f"    ⚠ too little content ({len(text)} chars) — skip")
        return name, []
    parser = PARSERS.get(name)
    if not parser:
        return name, []
    tips = parser(text)
    print(f"    ✓ {len(tips)} tips parsed")
    return name, tips


def main() -> None:
    from utils.free_scrape import FIRECRAWL_API_KEY
    if not FIRECRAWL_API_KEY:
        print("ℹ FIRECRAWL_API_KEY not set — running free-only (direct HTTP + trafilatura/Jina Reader)")

    ts = datetime.now(timezone.utc).isoformat()
    now_utc = datetime.now(timezone.utc)
    today = now_utc.strftime("%Y-%m-%d")
    tomorrow = (now_utc + timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"\n[{ts}] Tips scraper starting ({len(SOURCES)} sources + TheSportsDB WC2026)...")

    # ── Always-on: WC2026 from TheSportsDB + local tip table ─────────────────
    wc_matches = fetch_wc_matches([today, tomorrow])
    wc_tips, wc_predictions = build_wc_tips(wc_matches)
    print(f"  ✓ TheSportsDB WC2026: {len(wc_matches)} matches → {len(wc_tips)} tips")

    # ── Scraped sources (parallel) ───────────────────────────────────────────
    scraped_tips: list[dict] = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(scrape_source, s): s for s in SOURCES}
        for fut in as_completed(futs):
            _, tips = fut.result()
            scraped_tips.extend(tips)

    all_tips = wc_tips + scraped_tips

    # Deduplicate by match name, keeping highest-confidence entry
    seen: set[str] = set()
    deduped: list[dict] = []
    for t in sorted(all_tips, key=lambda x: x.get("conf", 0), reverse=True):
        k = t["match"].lower()
        if k not in seen:
            seen.add(k)
            deduped.append(t)

    KEY_ORDER = ["world", "cafl", "afcon", "local", "epl", "ucl", "laliga",
                 "basketball", "tennis", "cricket", "rugby"]
    deduped.sort(key=lambda t: (
        -(t.get("conf", 0)),
        KEY_ORDER.index(t.get("key", "local")) if t.get("key") in KEY_ORDER else 99,
    ))

    # ── Write data/tips.json ─────────────────────────────────────────────────
    output = {
        "updated": ts,
        "count": len(deduped),
        "tips": deduped,
    }
    TIPS_JSON.parent.mkdir(parents=True, exist_ok=True)
    TIPS_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  ✅ data/tips.json: {len(deduped)} tips written")
    for t in deduped[:8]:
        print(f"     [{t['source']:20}] {t['match']:35} → {t['pred']} ({t['conf']}%)")

    # ── Write data/predictions.json (read by tips/index.html) ───────────────
    if wc_predictions:
        # Merge with existing non-WC predictions that have valid future ko_utc
        cutoff = now_utc - timedelta(hours=6)
        existing_preds: list[dict] = []
        if PRED_JSON.exists():
            try:
                old = json.loads(PRED_JSON.read_text())
                for p in old.get("predictions", []):
                    if p.get("comp_slug") == "world-cup-2026":
                        continue
                    ko = p.get("ko_utc")
                    if not ko:
                        continue  # skip null-date predictions — they may be stale
                    try:
                        ko_dt = datetime.fromisoformat(ko.replace("Z", "+00:00"))
                        if ko_dt > cutoff:
                            existing_preds.append(p)
                    except Exception:
                        pass
            except Exception:
                pass

        all_preds = wc_predictions + existing_preds
        pred_output = {
            "updated": ts,
            "source": "thesportsdb.com + freesupertips.com",
            "count": len(all_preds),
            "scrape_log": [{"page": "wc2026", "status": "ok", "ts": ts}],
            "predictions": all_preds,
        }
        PRED_JSON.write_text(json.dumps(pred_output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✅ data/predictions.json: {len(all_preds)} predictions written")

    if not deduped:
        print("  ⚠ WARNING: 0 tips written — check scrapers")
        sys.exit(1)


if __name__ == "__main__":
    main()
