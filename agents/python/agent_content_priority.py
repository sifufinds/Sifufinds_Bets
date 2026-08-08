"""
Content Priority Agent — ranks keyword gaps by country tier, content type,
and actionability into one queue, so it's clear exactly what to write next
to close the "0 of 51 keywords ranking" gap found 2026-08-01.

Reads both keyword backlogs (agent_keyword_research.py's evergreen gaps,
agent_trending_keywords.py's country-scoped trending gaps) and produces one
ranked queue at content_priority_queue.json.

Trending gaps are writer-actionable UNLESS the same real-world story is
already covered by agent_sports_blog.py's existing 3x/day pan-African news
schedule — checked against utils/story_dedup.py's shared covered-story
registry (the same registry agent_sports_blog.py itself writes to), so a
second post is only ever written when it's a genuinely different,
country-specific angle agent_sports_blog.py's pan-African pipeline wouldn't
otherwise produce. This closes the gap found 2026-08-08: since
agent_trending_keywords.py now researches each country's OWN trending
stories (not a shared pool cycled by country name, see that module's
docstring), most trending gaps are about stories agent_sports_blog.py never
touches at all, so unconditionally marking every trending gap
non-actionable was leaving real country-specific ranking opportunities on
the table. agent_country_trending_writer.py is the writer that closes this
gap, the trending-content equivalent of agent_priority_writer.py.

The genuinely uncovered evergreen ground is commercial content — "best
betting sites/bonus/apps", "how to bet online" — which has no existing
writer at all; agent_priority_writer.py closes that.

Usage:
    python agent_content_priority.py
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from utils.countries import AFRICAN_COUNTRIES
from utils.logger import log
from utils.story_dedup import headline_key, load_covered_keys

KEYWORD_OPPS_PATH = Path(__file__).parent / "keyword_opportunities.json"
TRENDING_PATH = Path(__file__).parent / "trending_keywords.json"
QUEUE_PATH = Path(__file__).parent / "content_priority_queue.json"

# Mirrors update_countries.py's existing "top 5 priority countries" pattern
# (NG/KE/ZA/GH/TZ) extended with a second tier of markets that already carry
# a meaningfully large real bookmaker presence (see utils/site_data.py).
COUNTRY_TIER = {
    "Nigeria": 3, "Kenya": 3, "Ghana": 3, "South Africa": 3, "Tanzania": 3,
    "Uganda": 2, "Zambia": 2, "Ivory Coast": 2, "Cameroon": 2, "Senegal": 2,
    "Egypt": 2, "Morocco": 2, "Ethiopia": 2, "Zimbabwe": 2, "Mozambique": 2,
}
DEFAULT_TIER = 1

# (substring in an evergreen keyword, content_type, guide_angle, writer_actionable)
# "guide" keywords have zero existing writer — closing that gap is the point
# of agent_priority_writer.py. "football betting tips today" and "best live
# odds" are already structurally served by agent_sports_blog.py's scheduled
# news pipeline and the /tips /odds tool pages respectively, so they're
# tracked for visibility but excluded from the write queue.
EVERGREEN_CONTENT_TYPES = [
    ("best betting sites", "guide", "best_sites", True),
    ("best betting bonus", "guide", "best_bonus", True),
    ("how to bet online", "guide", "how_to_bet", True),
    ("safest betting apps", "guide", "safest_apps", True),
    ("football betting tips today", "blog", "", False),
    ("best live odds", "tool", "", False),
]

_COUNTRY_NAMES = [c["name"] for c in AFRICAN_COUNTRIES]


def _country_in_keyword(keyword: str) -> str | None:
    for name in _COUNTRY_NAMES:
        if re.search(r"\b" + re.escape(name) + r"\b", keyword):
            return name
    return None


def _classify_evergreen(keyword: str) -> tuple[str, str, bool]:
    lowered = keyword.lower()
    for substring, content_type, guide_angle, actionable in EVERGREEN_CONTENT_TYPES:
        if substring in lowered:
            return content_type, guide_angle, actionable
    return "blog", "", False


def _score(country_name: str, actionable: bool, source: str, checked_at: str) -> float:
    tier = COUNTRY_TIER.get(country_name, DEFAULT_TIER)
    score = tier * 10
    if actionable:
        score += 5
    if source == "trending":
        # Trending value decays fast — a same-day story is worth chasing,
        # a week-old one no longer is.
        try:
            age_hours = (datetime.now(timezone.utc) - datetime.fromisoformat(checked_at)).total_seconds() / 3600
            score += max(0, 5 - age_hours / 24)
        except (ValueError, TypeError):
            pass
    return round(score, 2)


def build_queue() -> dict:
    opps = {}
    if KEYWORD_OPPS_PATH.exists():
        opps = json.loads(KEYWORD_OPPS_PATH.read_text()).get("opportunities", {})
    trending = {}
    if TRENDING_PATH.exists():
        trending = json.loads(TRENDING_PATH.read_text()).get("trending", {})

    items = []
    for keyword, data in opps.items():
        if data.get("sifufinds_ranks"):
            continue
        country = _country_in_keyword(keyword)
        if not country:
            continue
        content_type, guide_angle, actionable = _classify_evergreen(keyword)
        items.append({
            "keyword": keyword,
            "country": country,
            "content_type": content_type,
            "guide_angle": guide_angle,
            "writer_actionable": actionable,
            "source": "evergreen",
            "top_competitors": data.get("top_competitors", []),
            "checked_at": data.get("checked_at", ""),
            "score": _score(country, actionable, "evergreen", data.get("checked_at", "")),
        })

    covered_keys = load_covered_keys()
    for key, data in trending.items():
        if data.get("sifufinds_ranks"):
            continue
        source_headline = data.get("source_headline", "")
        # Only skip writer-actionable when the same real-world story is
        # already covered by agent_sports_blog.py's pan-African pipeline
        # (shared registry, see module docstring) — a country-specific
        # trending story that pipeline never touched at all is exactly the
        # gap agent_country_trending_writer.py exists to close.
        already_covered = bool(source_headline) and headline_key(source_headline) in covered_keys
        actionable = not already_covered
        items.append({
            "keyword": data.get("primary_keyword", key),
            "country": data.get("country", ""),
            "content_type": data.get("content_type_suggestion", "blog"),
            "guide_angle": "",
            "writer_actionable": actionable,
            "source": "trending",
            "top_competitors": data.get("top_competitors", []),
            "source_headline": source_headline,
            "source_description": data.get("source_description", ""),
            "source_url": data.get("source_url", ""),
            "checked_at": data.get("checked_at", ""),
            "score": _score(data.get("country", ""), actionable, "trending", data.get("checked_at", "")),
        })

    items.sort(key=lambda i: i["score"], reverse=True)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_gaps": len(items),
        "writer_actionable_count": sum(1 for i in items if i["writer_actionable"]),
        "items": items,
    }


def run() -> int:
    queue = build_queue()
    QUEUE_PATH.write_text(json.dumps(queue, indent=2, ensure_ascii=False))
    print(f"Content Priority Agent — {queue['total_gaps']} tracked gap(s), {queue['writer_actionable_count']} writer-actionable")
    if queue["items"]:
        print("\nTop 15 priorities:")
        for item in queue["items"][:15]:
            flag = "✉ " if item["writer_actionable"] else "   "
            print(f"  {flag}[{item['score']:>5}] {item['country']:<15} {item['content_type']:<6} {item['keyword']}")
    log("content_priority", "run", "ok", f"{queue['total_gaps']} gaps, {queue['writer_actionable_count']} actionable")
    return 0


if __name__ == "__main__":
    sys.exit(run())
