"""live_data_helpers.py — Shared primitives for the tips/odds/leagues scrapers
(agent_live_odds.py, agent_multi_scrape.py, agent_firecrawl_odds.py).

Kept small and dependency-free so any of those scripts can import it without
pulling in the rest of another script's module-level state.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone


def american_to_decimal(odds: str | int | float) -> float:
    """Convert American moneyline odds (+164, -198) to decimal odds.

    Returns 0.0 on unparseable input rather than raising — callers treat 0.0
    as "no odds available" throughout the live-data pipeline.
    """
    try:
        o = int(str(odds).replace("+", "").strip())
        return round((100 / abs(o) + 1) if o < 0 else (o / 100 + 1), 2)
    except (ValueError, TypeError):
        return 0.0


def fmt_time(raw_time: str, is_live: bool = False) -> str:
    """Format a HH:MM string into a SifuFinds-compatible time label."""
    now = datetime.now(timezone.utc)
    t = raw_time.strip()
    if is_live:
        return t
    try:
        h, m = map(int, t.split(":"))
        match_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if match_dt < now:
            match_dt = match_dt + timedelta(days=1)
        day_mon_year = f"{match_dt.day} {match_dt.strftime('%b %Y')}"
        return f"{day_mon_year} · {t} UTC"
    except Exception:
        day_mon_year = f"{now.day} {now.strftime('%b %Y')}"
        return f"{day_mon_year} · {t} UTC"


# Sport/league label → internal `key` used across live.json, TIPS, ODDS_DATA.
# Order matters — first match wins. Default (no match) is "world", never
# "local": "local" specifically means an African domestic league on this
# site (see odds/index.html's "🏟️ Local Football" filter) and must not be
# the silent catch-all for every unrecognised league worldwide.
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
]


def league_key(label: str) -> str:
    for pattern, key in LEAGUE_KEY_MAP:
        if pattern.search(label):
            return key
    return "world"
