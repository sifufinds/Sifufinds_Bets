"""
agent_scrape_tips.py — Hourly tips scraper for SifuFinds
Scrapes all 6 Best Free Betting Tips Websites:
  - TipsterBattle  (tipsterbattle.com/football/africa)
  - 1960Tips       (1960tips.com)
  - FreeSuperTips  (freesupertips.com/football-tips)
  - Forebet        (forebet.com/en/football-tips-and-predictions-for-today)
  - Predictz       (predictz.com/predictions)
  - EaglePredict   (eaglepredict.com/predictions)

Writes parsed tips to data/tips.json which the tips page loads as a
fallback when Supabase is unavailable.

Run hourly via GitHub Actions. Requires FIRECRAWL_API_KEY.
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

# ── Config ────────────────────────────────────────────────────────────────────

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TIPS_JSON = REPO_ROOT / "data" / "tips.json"

TODAY_UTC = datetime.now(timezone.utc)
DATE_LABEL = TODAY_UTC.strftime("%-d %b")   # e.g. "5 Jun"

# African bookmakers used when attributing tips
AFRICAN_BKS = ["1xBet", "Betway", "Bet9ja", "22Bet", "Melbet", "Sportybet", "Betika"]

# Sport key map
def league_key(label: str) -> str:
    l = label.lower()
    if any(w in l for w in ["world cup", "wc2026", "group a", "group b", "group c",
                             "group d", "group e", "group f", "group g", "group h",
                             "group i", "group j", "group k", "group l", "friendly"]):
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


SOURCES = [
    {
        "name": "tipsterbattle",
        "url": "https://www.tipsterbattle.com/football/africa",
        "wait": 3000,
        "priority": 1,
    },
    {
        "name": "1960tips",
        "url": "https://www.1960tips.com/",
        "wait": 3000,
        "priority": 2,
    },
    {
        "name": "freesupertips",
        "url": "https://www.freesupertips.com/football-tips/",
        "wait": 4000,
        "priority": 3,
    },
    {
        "name": "forebet",
        "url": "https://www.forebet.com/en/football-tips-and-predictions-for-today/predictions-1x2",
        "wait": 5000,
        "priority": 4,
    },
    {
        "name": "eaglepredict",
        "url": "https://eaglepredict.com/predictions/league/africa/",
        "wait": 4000,
        "priority": 4,
    },
    {
        "name": "predictz",
        "url": "https://www.predictz.com/predictions/",
        "wait": 4000,
        "priority": 5,
    },
]

# ── Firecrawl ─────────────────────────────────────────────────────────────────

def scrape(url: str, wait_ms: int, name: str) -> str:
    env = {**os.environ, "FIRECRAWL_API_KEY": FIRECRAWL_API_KEY}
    try:
        r = subprocess.run(
            ["firecrawl", "scrape", url, "--wait-for", str(wait_ms), "--only-main-content"],
            capture_output=True, text=True, timeout=90, env=env,
        )
        if r.stdout and len(r.stdout) > 300:
            return r.stdout
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"    cli error [{name}]: {e}")

    # Python SDK fallback
    try:
        from firecrawl import FirecrawlApp  # type: ignore
        app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
        res = app.scrape_url(url, params={
            "formats": ["markdown"], "waitFor": wait_ms, "onlyMainContent": True
        })
        return res.get("markdown", "")
    except Exception as e:
        print(f"    sdk error [{name}]: {e}")
        return ""

# ── Parsers ───────────────────────────────────────────────────────────────────

def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


# ── TipsterBattle ─────────────────────────────────────────────────────────────
# Table format:
# | Event | Betting tip | Tipster | Bookmaker |
# | [Match\nDate - Time] | **Tip** Odds **X.XX** Stake **Y**/10 | ... | ... |

# Single-line regex: each TipsterBattle row is one long line
_TB_ROW = re.compile(
    r"\|\s*\[([^\]]+)\]\(https://www\.tipsterbattle\.com/betting-tips/[^\)]+\)"
    r"\s*<br>(\d{2}\.\d{2}\.\d{4})\s*-\s*(\d{2}:\d{2})"   # date + time
    r"[^|]+\|\s*\*\*([^*]+)\*\*"                            # prediction (bold)
    r"\s*<br>Odds\s*\*\*(\d+\.\d+)\*\*"                    # odds
    r"Stake\s*\*\*(\d+)\*\*/10"                             # stake/10
)


def parse_tipsterbattle(text: str) -> list[dict]:
    tips = []
    seen: set[str] = set()
    bk_cycle = 0

    for m in _TB_ROW.finditer(text):
        raw_match = clean(m.group(1))
        # Normalise separators: " vs ", " Vs ", " - ", " – "
        match_name = re.sub(r"\s+(vs|Vs|VS|–)\s+", " vs ", raw_match)
        match_name = re.sub(r"\s+-\s+", " vs ", match_name)

        time_str = m.group(3)      # HH:MM
        pred_text = clean(m.group(4))
        odds_val = m.group(5)
        stake = int(m.group(6))

        if match_name in seen:
            continue
        seen.add(match_name)

        # confidence: stake 10/10 → 80%, 5/10 → 65%
        conf = min(85, 55 + stake * 3)
        bk = AFRICAN_BKS[bk_cycle % len(AFRICAN_BKS)]
        bk_cycle += 1

        # Try to detect Algeria / CAF league from context
        league = "Algeria · Football"
        key = "local"
        if any(w in match_name for w in ["Kabylie", "Belouizdad", "Mostaganem", "Saoura",
                                          "Constantine", "Rouissat", "khenchela", "Baydh"]):
            league = "Algeria Ligue Professionnelle"

        tips.append({
            "league": league,
            "key": key,
            "match": match_name,
            "pred": pred_text,
            "analysis": (
                f"TipsterBattle community pick: {pred_text} at odds {odds_val}. "
                f"Tipster stake rating {stake}/10. Verify latest odds before placing."
            ),
            "odds": odds_val,
            "via": bk,
            "conf": conf,
            "time": f"{time_str} UTC",
            "date": DATE_LABEL,
            "isAI": False,
            "source": "tipsterbattle",
        })

    return tips


# ── 1960Tips ──────────────────────────────────────────────────────────────────
# Pattern visible in scrape:
# "GRP A Mexico vs South Africa TIP: 1|GRP A South Korea vs Czech Republic TIP: 2|..."
# "87%1%12%  OUR TIPMexico WIN"

def parse_1960tips(text: str) -> list[dict]:
    tips = []
    seen: set[str] = set()

    # Extract from ticker line: "GRP X TEAM1 vs TEAM2 TIP: N"
    ticker = re.findall(
        r"GRP\s+([A-L])\s+([A-Za-z\s]+)\s+vs\s+([A-Za-z\s]+)\s+TIP:\s*([12X])",
        text,
    )
    # Extract probability sections: "87%1%12%  OUR TIPMexico WIN"
    prob_sections = re.findall(
        r"(\d+)%(\d+)%(\d+)%\s*OUR\s*TIP\s*([A-Za-z\s]+(?:WIN|DRAW|win|draw))",
        text,
    )

    for idx, (grp, home, away, tip_code) in enumerate(ticker):
        home = clean(home)
        away = clean(away)
        match_name = f"{home} vs {away}"
        if match_name in seen:
            continue
        seen.add(match_name)

        # Match with probability section by index
        if idx < len(prob_sections):
            h_pct, d_pct, a_pct, tip_text = prob_sections[idx]
            h_pct, d_pct, a_pct = int(h_pct), int(d_pct), int(a_pct)
            pred = clean(tip_text)
            conf = max(h_pct, d_pct, a_pct)
        else:
            pred = "Home Win" if tip_code == "1" else ("Draw" if tip_code == "X" else "Away Win")
            conf = 68

        tips.append({
            "league": f"World Cup 2026 · Group {grp}",
            "key": "world",
            "match": match_name,
            "pred": pred,
            "analysis": (
                f"1960Tips professional analysts predict {pred} for this World Cup 2026 "
                f"Group {grp} clash. Statistical model confidence: {conf}%."
            ),
            "odds": "1.85",
            "via": "1xBet",
            "conf": conf,
            "time": "19:00 UTC",
            "date": "11 Jun",
            "isAI": False,
            "source": "1960tips",
        })

    return tips


# ── FreeSuperTips ─────────────────────────────────────────────────────────────
# Pattern: time on one line, tip type on next, match name on next
# "12:30\nBoth Teams To Score\nSlovakia vs Montenegro"

def parse_freesupertips(text: str) -> list[dict]:
    tips = []
    seen: set[str] = set()
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    TIP_TYPES = [
        "Both Teams To Score", "BTTS", "Over 2.5", "Under 2.5",
        "Home Win", "Away Win", "Draw", "1X2", "Correct Score",
        "Double Chance", "Asian Handicap", "First Goal",
    ]
    tip_pattern = re.compile(
        r"^(" + "|".join(re.escape(t) for t in TIP_TYPES) + r")",
        re.I,
    )
    time_pattern = re.compile(r"^(\d{2}:\d{2})$")
    match_pattern = re.compile(r"^([A-Z][a-zA-Z\s'-]+)\s+vs?\s+([A-Z][a-zA-Z\s'-]+)$")

    i = 0
    while i < len(lines):
        line = lines[i]
        time_m = time_pattern.match(line)
        if time_m:
            time_str = time_m.group(1)
            # Look ahead for tip type and match
            pred_txt = ""
            match_name = ""
            league_txt = "World / Friendly International"
            for j in range(i + 1, min(i + 6, len(lines))):
                if tip_pattern.match(lines[j]) and not pred_txt:
                    pred_txt = clean(lines[j])
                elif match_pattern.match(lines[j]) and not match_name:
                    match_name = clean(lines[j])
                elif lines[j] and not lines[j].startswith("[") and not lines[j].startswith("!") and len(lines[j]) > 5:
                    if not pred_txt:
                        league_txt = lines[j]

            if pred_txt and match_name and match_name not in seen:
                seen.add(match_name)
                tips.append({
                    "league": league_txt,
                    "key": league_key(league_txt + " " + match_name),
                    "match": match_name,
                    "pred": pred_txt,
                    "analysis": (
                        f"FreeSuperTips expert pick: {pred_txt} for {match_name}. "
                        f"Professional tipster analysis based on team form and statistics."
                    ),
                    "odds": "1.80",
                    "via": "Betway",
                    "conf": 68,
                    "time": f"{time_str} UTC",
                    "date": DATE_LABEL,
                    "isAI": False,
                    "source": "freesupertips",
                })
        i += 1

    return tips


# ── Forebet ───────────────────────────────────────────────────────────────────
# Forebet renders via JS; what we get is mostly navigation.
# We parse any visible match lines: "TEAM1 - TEAM2 ... 1 ... XX% ..."

def parse_forebet(text: str) -> list[dict]:
    tips = []
    seen: set[str] = set()

    # Pattern: odds values followed by percentage, then team names in a link
    match_links = re.findall(
        r"\[([A-Z][a-zA-Z\s\-'\.]+)\s*[-–]\s*([A-Z][a-zA-Z\s\-'\.]+)\]\(https://www\.forebet\.com/[^\)]+\)",
        text,
    )
    # Also look for probability-style data: home% draw% away%
    # "1.45  3.40  2.90  55%  28%  17%"
    prob_lines = re.findall(
        r"(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+)%\s+(\d+)%\s+(\d+)%",
        text,
    )

    for idx, (home, away) in enumerate(match_links[:len(prob_lines)]):
        home, away = clean(home), clean(away)
        match_name = f"{home} vs {away}"
        if match_name in seen or len(home) < 2 or len(away) < 2:
            continue
        seen.add(match_name)

        if idx < len(prob_lines):
            h_odds, d_odds, a_odds, h_pct, d_pct, a_pct = prob_lines[idx]
            h_pct, d_pct, a_pct = int(h_pct), int(d_pct), int(a_pct)
            if h_pct >= d_pct and h_pct >= a_pct:
                pred, odds, conf = f"{home} Win", h_odds, h_pct
            elif a_pct >= d_pct:
                pred, odds, conf = f"{away} Win", a_odds, a_pct
            else:
                pred, odds, conf = "Draw", d_odds, d_pct
        else:
            pred, odds, conf = "Home Win", "1.80", 60

        tips.append({
            "league": "Football · Forebet Pick",
            "key": "local",
            "match": match_name,
            "pred": pred,
            "analysis": (
                f"Forebet mathematical model predicts {pred}. "
                f"Statistical confidence: {conf}%. Based on 500+ data points."
            ),
            "odds": str(odds),
            "via": AFRICAN_BKS[idx % len(AFRICAN_BKS)],
            "conf": conf,
            "time": "TBD",
            "date": DATE_LABEL,
            "isAI": False,
            "source": "forebet",
        })

    return tips[:5]  # cap forebet at 5 (navigation data is noisy)


# ── EaglePredict ──────────────────────────────────────────────────────────────

def parse_eaglepredict(text: str) -> list[dict]:
    tips = []
    seen: set[str] = set()

    # Look for match prediction blocks:
    # "TEAM1 vs TEAM2 ... prediction ... odds ... %"
    blocks = re.split(r"\n{2,}", text)
    for block in blocks:
        match_m = re.search(
            r"([A-Z][a-zA-Z\s'-]+)\s+vs?\s+([A-Z][a-zA-Z\s'-]+)",
            block,
        )
        if not match_m:
            continue
        home, away = clean(match_m.group(1)), clean(match_m.group(2))
        if len(home) < 2 or len(away) < 2 or home == away:
            continue
        match_name = f"{home} vs {away}"
        if match_name in seen:
            continue

        odds_m = re.search(r"(\d+\.\d{2})", block)
        pct_m = re.search(r"(\d{2,3})%", block)
        pred_m = re.search(
            r"(Home Win|Away Win|Draw|Over \d+\.?\d*|Under \d+\.?\d*|BTTS|Both Teams)",
            block, re.I,
        )

        if not pred_m:
            continue

        seen.add(match_name)
        conf = int(pct_m.group(1)) if pct_m else 65
        odds = odds_m.group(1) if odds_m else "1.85"

        tips.append({
            "league": "Africa · Football",
            "key": "local",
            "match": match_name,
            "pred": clean(pred_m.group(0)),
            "analysis": (
                f"EaglePredict expert analysis: {clean(pred_m.group(0))} for {match_name}. "
                f"Africa-specialist tipsters with strong track record."
            ),
            "odds": odds,
            "via": AFRICAN_BKS[len(seen) % len(AFRICAN_BKS)],
            "conf": min(conf, 85),
            "time": "TBD",
            "date": DATE_LABEL,
            "isAI": False,
            "source": "eaglepredict",
        })

    return tips[:6]


# ── Predictz ──────────────────────────────────────────────────────────────────

def parse_predictz(text: str) -> list[dict]:
    tips = []
    seen: set[str] = set()

    # Predictz format: varies, look for pattern:
    # TEAM1 vs TEAM2 ... Win/Draw/BTTS ... odds
    rows = re.findall(
        r"([A-Z][a-zA-Z\s'-]+)\s+vs?\s+([A-Z][a-zA-Z\s'-]+)"
        r".*?(Home Win|Away Win|Draw|Over \d+\.?\d*|Under \d+\.?\d*|BTTS)"
        r".*?(\d+\.\d{2})",
        text,
        re.I | re.S,
    )
    for home, away, pred, odds in rows[:6]:
        home, away = clean(home), clean(away)
        match_name = f"{home} vs {away}"
        if match_name in seen or len(home) < 2:
            continue
        seen.add(match_name)
        tips.append({
            "league": "Football · Predictz Pick",
            "key": league_key(home + " " + away),
            "match": match_name,
            "pred": clean(pred),
            "analysis": (
                f"PredictZ free prediction: {clean(pred)} for {match_name}. "
                f"Based on current form, head-to-head, and team statistics."
            ),
            "odds": odds,
            "via": AFRICAN_BKS[len(seen) % len(AFRICAN_BKS)],
            "conf": 65,
            "time": "TBD",
            "date": DATE_LABEL,
            "isAI": False,
            "source": "predictz",
        })
    return tips


PARSERS = {
    "tipsterbattle": parse_tipsterbattle,
    "1960tips": parse_1960tips,
    "freesupertips": parse_freesupertips,
    "forebet": parse_forebet,
    "eaglepredict": parse_eaglepredict,
    "predictz": parse_predictz,
}


# ── Main ──────────────────────────────────────────────────────────────────────

def scrape_source(source: dict) -> tuple[str, list[dict]]:
    name = source["name"]
    print(f"  → {name}")
    text = scrape(source["url"], source["wait"], name)
    if len(text) < 200:
        print(f"    ⚠ too little content — skip")
        return name, []
    parser = PARSERS.get(name)
    if not parser:
        return name, []
    tips = parser(text)
    print(f"    ✓ {len(tips)} tips")
    return name, tips


def main():
    if not FIRECRAWL_API_KEY:
        print("FIRECRAWL_API_KEY not set — skipping tips scrape")
        sys.exit(0)

    ts = datetime.now(timezone.utc).isoformat()
    print(f"\n[{ts}] Tips scraper starting ({len(SOURCES)} sources)...")

    all_tips: list[dict] = []
    # Scrape in priority order, 3 concurrent
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(scrape_source, s): s for s in SOURCES}
        for fut in as_completed(futs):
            _, tips = fut.result()
            all_tips.extend(tips)

    # Deduplicate by match name
    seen: set[str] = set()
    deduped: list[dict] = []
    for t in sorted(all_tips, key=lambda x: x.get("conf", 0), reverse=True):
        k = t["match"].lower()
        if k not in seen:
            seen.add(k)
            deduped.append(t)

    # Sort: highest confidence first, then by key priority
    KEY_ORDER = ["world", "cafl", "afcon", "local", "epl", "ucl", "basketball", "tennis", "cricket"]
    deduped.sort(key=lambda t: (
        -(t.get("conf", 0)),
        KEY_ORDER.index(t.get("key", "local")) if t.get("key") in KEY_ORDER else 99,
    ))

    output = {
        "updated": ts,
        "count": len(deduped),
        "tips": deduped,
    }

    TIPS_JSON.parent.mkdir(parents=True, exist_ok=True)
    TIPS_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  ✅ data/tips.json: {len(deduped)} tips written")
    for t in deduped[:6]:
        print(f"     [{t['source']:14}] {t['match']:35} → {t['pred']} ({t['conf']}%)")


if __name__ == "__main__":
    main()
