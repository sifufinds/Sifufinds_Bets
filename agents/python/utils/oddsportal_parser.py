"""oddsportal_parser.py — Extract real 1X2 odds from OddsPortal match pages.

Shared by agent_multi_scrape.py (every 15 min) and agent_firecrawl_odds.py
(daily) so both jobs use the same, correct extraction instead of two
diverging copies.

OddsPortal match rows on pages like /matches/football/today/ look like
(after markdown scraping, one element per line):

    [12:00](https://www.oddsportal.com/football/h2h/el-bayadh-.../mostaganem-.../#...)
    ![Mostaganem](img)
    Mostaganem
    –
    ![El Bayadh](img)
    El Bayadh
    +160          <- 1  (home win)
    +200          <- X  (draw)
    +165          <- 2  (away win)

preceded, once per country/league block, by a header of the form:

    [Ligue 1](https://www.oddsportal.com/football/algeria/ligue-1/)

Odds appear in American moneyline format when scraped from a US-based
runner (GitHub Actions), decimal format otherwise — both are handled.
Rows with no odds ("-") are skipped: other sources (Sofascore, Flashscore)
already cover fixture-only data, so OddsPortal only needs to contribute
what it uniquely offers — real prices.
"""
from __future__ import annotations

import re
from typing import Callable

from utils.live_data_helpers import american_to_decimal

_OP_H2H_RE = re.compile(
    r"\[(\d{1,2}:\d{2})\]\(https://www\.oddsportal\.com/football/h2h/[^\)]+\)"
)
# Two-segment football link = a genuine country/league page, e.g.
# .../football/algeria/ligue-1/ — the country slug is reliable (from the
# URL), the league name (link text) is the human-readable label.
_OP_LEAGUE_RE = re.compile(
    r"\[([^\[\]]{2,80})\]\(https://www\.oddsportal\.com/football/"
    r"([a-z0-9]+(?:-[a-z0-9]+)*)/[a-z0-9]+(?:-[a-z0-9]+)*/\)"
)
_OP_AMERICAN_ODDS_RE = re.compile(r"^([+-]\d{2,5})$")
_OP_DECIMAL_ODDS_RE = re.compile(r"^(\d{1,3}\.\d{2})$")

# OddsPortal displays the country's own name as link text next to its flag;
# the URL slug is just that name lower-cased/hyphenated, so comparing the
# slug (with hyphens turned to spaces) against these names is reliable
# without having to hardcode OddsPortal's exact slug spelling separately.
AFRICAN_COUNTRY_NAMES = {
    "algeria", "angola", "benin", "botswana", "burkina faso", "burundi",
    "cameroon", "cape verde", "central african republic", "chad", "comoros",
    "congo", "dr congo", "democratic republic of congo", "djibouti", "egypt",
    "equatorial guinea", "eritrea", "eswatini", "ethiopia", "gabon",
    "gambia", "ghana", "guinea", "guinea bissau", "ivory coast",
    "cote d'ivoire", "kenya", "lesotho", "liberia", "libya", "madagascar",
    "malawi", "mali", "mauritania", "mauritius", "morocco", "mozambique",
    "namibia", "niger", "nigeria", "rwanda", "sao tome and principe",
    "senegal", "seychelles", "sierra leone", "somalia", "south africa",
    "south sudan", "sudan", "tanzania", "togo", "tunisia", "uganda",
    "zambia", "zimbabwe",
}


def _to_decimal_odds(raw: str) -> float:
    m = _OP_AMERICAN_ODDS_RE.match(raw)
    if m:
        return american_to_decimal(m.group(1))
    m = _OP_DECIMAL_ODDS_RE.match(raw)
    if m:
        return float(m.group(1))
    return 0.0


def _is_odds_line(line: str) -> bool:
    return bool(_OP_AMERICAN_ODDS_RE.match(line) or _OP_DECIMAL_ODDS_RE.match(line))


def parse_oddsportal(
    text: str,
    league_key_fn: Callable[[str], str],
    fmt_time_fn: Callable[[str], str],
    label_hint: str = "All Football",
) -> list[dict]:
    matches_out: list[dict] = []
    seen: set[str] = set()

    checkpoints: list[tuple[int, str, str]] = []
    for m in _OP_LEAGUE_RE.finditer(text):
        league_name = m.group(1).strip()
        country_slug = m.group(2).strip()
        if re.search(r"^\d|\d{4}$", league_name):
            continue
        country_name = country_slug.replace("-", " ")
        if country_name in AFRICAN_COUNTRY_NAMES:
            key = "local"
        else:
            key = league_key_fn(league_name)
            # league_key_fn's generic "premier league"/"la liga" patterns
            # also match e.g. "Canadian Premier League" — gate them by the
            # one country each label is actually specific to, since here
            # (unlike Sofascore/Flashscore) real country context exists.
            if key == "epl" and country_name != "england":
                key = "world"
            elif key == "laliga" and country_name != "spain":
                key = "world"
        checkpoints.append((m.start(), f"{country_name.title()} · {league_name}", key))

    def context_at(pos: int) -> tuple[str, str]:
        label, key = label_hint, "world"
        for cp_pos, cp_label, cp_key in checkpoints:
            if cp_pos > pos:
                break
            label, key = cp_label, cp_key
        return label, key

    anchors = list(_OP_H2H_RE.finditer(text))
    for idx, anchor in enumerate(anchors):
        kickoff = anchor.group(1)
        window_end = anchors[idx + 1].start() if idx + 1 < len(anchors) else min(anchor.end() + 800, len(text))
        window = text[anchor.end():window_end]
        # Normalise Firecrawl/Jina's backslash-newline row continuations.
        normalised = re.sub(r"\\\s*\n?\s*", "\n", window)
        lines = [l.strip() for l in normalised.split("\n") if l.strip()]

        teams: list[str] = []
        odds_raw: list[str] = []
        for line in lines:
            if line.startswith("![") or line.startswith("[") or line.startswith("|"):
                continue
            if line in ("-", "–", "—"):
                continue
            if len(teams) < 2 and 2 < len(line) < 55 and not _is_odds_line(line):
                teams.append(line)
                continue
            if len(teams) >= 2 and len(odds_raw) < 3 and _is_odds_line(line):
                odds_raw.append(line)
                if len(odds_raw) == 3:
                    break

        if len(teams) < 2 or len(odds_raw) < 3:
            continue  # fixture without full odds — other sources cover the fixture itself

        h, d, a = (_to_decimal_odds(o) for o in odds_raw)
        if h <= 0 or d <= 0 or a <= 0:
            continue

        home, away = teams[0], teams[1]
        key_str = f"{home.lower()}|{away.lower()}"
        if key_str in seen:
            continue
        seen.add(key_str)

        league_label, key = context_at(anchor.start())

        matches_out.append({
            "league": league_label,
            "key": key,
            "live": False,
            "complete": False,
            "home": home,
            "away": away,
            "hScore": None,
            "aScore": None,
            "time": fmt_time_fn(kickoff),
            "h": h,
            "d": d,
            "a": a,
            "hBk": "OddsPortal",
            "dBk": "OddsPortal",
            "aBk": "OddsPortal",
            "_src": "oddsportal",
        })

    return matches_out
