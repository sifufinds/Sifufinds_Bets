"""
Trending Keywords Agent — researches each of SifuFinds' 28 African markets'
OWN genuinely trending stories (not a shared pool reused across countries)
and pairs them with country intent modifiers to surface time-sensitive
keyword opportunities, for direct use by blog/news/guide writers.

Distinct from agent_keyword_research.py: that agent tracks a fixed backlog
of evergreen money keywords ("best betting sites {country} 2026") that
barely change month to month. This agent re-seeds itself from real,
freshness-checked, COUNTRY-SCOPED news every run (utils/news_fetcher.py's
fetch_country_trending() — a live DuckDuckGo search with the country's own
name embedded in the query, plus that country's dedicated local-outlet feed
where one exists), so the keyword ideas it produces are genuinely trending
IN that specific market — a live fixture, a transfer story, a tournament
headline a Kenyan or Ghanaian bettor is actually searching for right now —
rather than a global headline arbitrarily paired with a country name.

Fixed 2026-08-08: the previous version fetched ONE shared pool of global
topics via fetch_category() and assigned them to whichever countries were
due for a check via topics[i % len(topics)] — the exact same handful of
headlines got round-robined across every country in the batch, so "trending
in Nigeria" and "trending in Kenya" were frequently the identical story.
fetch_country_trending() replaces that as the primary source per country;
the old shared-pool fetch is kept only as a fallback for the (rare) case a
specific country's own search comes up empty this run.

Free-first, no LLM calls: news comes from utils/news_fetcher.py (DuckDuckGo
+ site feeds, no API key) and SERP checks come from utils/serp_research.py's
fc_search()/find_site_position() (DuckDuckGo only — Firecrawl is hard-disabled
in serp_research.py, scoped exclusively to the tips/odds/leagues pipelines) —
the same free pipeline every other keyword/SERP agent in this repo already
uses.

Usage:
    python agent_trending_keywords.py                # next batch of countries
    python agent_trending_keywords.py --batch-size 15
"""
import argparse
import json
import os
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))

from utils.countries import AFRICAN_COUNTRIES
from utils.logger import log
from utils.news_fetcher import fetch_category, fetch_country_trending
from utils.serp_research import fc_search, find_site_position

STATE_PATH = Path(__file__).parent / "trending_keywords.json"
# All 28 countries every run, not a handful — this research step makes no
# LLM calls (free DuckDuckGo/RSS only, see module docstring), so there's no
# per-run cost pressure to ration coverage the way agent_keyword_research.py
# rations its LLM-adjacent SERP checks. "Each country" genuinely means each
# country every day, not a slow multi-day rotation.
BATCH_SIZE = 23
MAX_ENTRIES = 400

# Categories most relevant to betting content — mirrors the "premier focus"
# ordering in CLAUDE.md's Content Focus section (football first).
TREND_CATEGORIES = ["football", "betting", "worldcup2026", "basketball"]
TOPICS_PER_CATEGORY = 5

_SOURCE_SUFFIX_RE = re.compile(
    r"\s*[\|\-–—:]\s*(goal\.com|bbc sport|espn|sky sports|the guardian|"
    r"90min|talksport|mirror football|independent|yahoo).*$",
    re.IGNORECASE,
)
_VS_RE = re.compile(r"([A-Z][\w .'-]{1,30}\s+(?:vs\.?|v)\s+[A-Z][\w .'-]{1,30})")
_GENERIC_WORDS = {
    "predictions", "prediction", "tips", "tip", "news", "today", "latest",
    "breaking", "preview", "update", "updates", "live", "recap", "highlights",
    "results", "result", "and", "the", "a", "an",
    "for", "in", "of", "to", "on", "with", "at", "vs",
    # Stripped so the topic doesn't collide/repeat with the "betting tips" /
    # "odds" intent modifiers the keyword templates already append below.
    "betting", "bet", "bets", "odds",
}

# Some RSS sources tagged "football"/"betting"/etc. in news_fetcher.py's
# FEEDS list are general-news feeds under the hood, not sport-only — found
# 2026-08-01: Punch Sports (Nigeria)'s feed (category="football") was
# serving plain Nigerian political/legal headlines ("Criminals have no
# tribe, religion, says Shettima", "Presidency rebukes Catholic bishops")
# alongside genuine football stories. Rather than trust category tagging
# alone, require an actual sports/competition/betting signal word in the
# headline before it becomes a keyword topic.
_SPORTS_SIGNAL_WORDS = {
    "match", "matches", "fixture", "fixtures", "league", "cup", "champions",
    "championship", "coach", "manager", "goal", "goals", "score", "scores",
    "beat", "beats", "win", "wins", "won", "loss", "loses", "draw", "squad",
    "kickoff", "kick-off", "derby", "final", "friendly", "tournament",
    "striker", "midfielder", "defender", "keeper", "goalkeeper", "transfer",
    "transfers", "signing", "signs", "wafcon", "afcon", "caf", "fifa",
    "uefa", "premier league", "nba", "basketball", "world cup", "playoffs",
    "odds", "bet", "bets", "betting", "wager", "bookmaker", "punter",
}


def _looks_sports_related(title: str) -> bool:
    lowered = title.lower()
    return any(word in lowered for word in _SPORTS_SIGNAL_WORDS) or bool(_VS_RE.search(title))


def _extract_topic(title: str) -> str:
    """Best-effort trending subject from a headline: prefer a "X vs Y"
    fixture (a clean, betting-relevant subject on its own), otherwise the
    headline with source suffixes and filler words stripped."""
    cleaned = _SOURCE_SUFFIX_RE.sub("", title).strip()
    vs_match = _VS_RE.search(cleaned)
    if vs_match:
        return vs_match.group(1).strip()
    cleaned = cleaned.replace(":", " ")
    words = [w for w in cleaned.split() if w.lower().strip(",.;") not in _GENERIC_WORDS]
    topic = " ".join(words[:8]).strip(" -:|")
    return topic or cleaned[:40]


def _suggest_content_type(topic: str, keyword: str) -> str:
    lowered = keyword.lower()
    if "how to bet" in lowered or "beginner" in lowered:
        return "guide"
    if " vs " in topic.lower() or re.search(r"\bv\b", topic.lower()):
        return "news"
    return "blog"


def _fresh_topics() -> list[dict]:
    """Pull today's fresh headlines across betting-relevant categories and
    reduce each to a short trending subject + source metadata, deduped by
    subject so the same story doesn't dominate every country pairing.

    This is now only the FALLBACK pool — used when a specific country's own
    fetch_country_trending() search comes up empty this run — not the
    primary source. See _topics_for_country() and the module docstring."""
    topics: list[dict] = []
    seen: set[str] = set()
    for category in TREND_CATEGORIES:
        try:
            items = fetch_category(category, max_per_feed=6)
        except Exception as e:
            log("trending_keywords", "_fresh_topics", "error", f"{category}: {e}")
            continue
        relevant_items = [i for i in items if _looks_sports_related(i["title"])]
        for item in relevant_items[:TOPICS_PER_CATEGORY]:
            topic = _extract_topic(item["title"])
            key = topic.lower()
            if not topic or key in seen:
                continue
            seen.add(key)
            topics.append({
                "topic": topic,
                "source_headline": item["title"],
                "source_description": item.get("description", ""),
                "source_url": item["url"],
                "source_category": category,
            })
    return topics


def _topics_for_country(country_name: str) -> list[dict]:
    """Genuinely country-scoped trending topics — the primary source for
    each country's batch entry. See fetch_country_trending()'s docstring
    (utils/news_fetcher.py) and this module's docstring for why this
    replaced the old shared/global pool cycled by round-robin."""
    try:
        items = fetch_country_trending(country_name, max_results=10)
    except Exception as e:
        log("trending_keywords", "_topics_for_country", "error", f"{country_name}: {e}")
        return []

    topics: list[dict] = []
    seen: set[str] = set()
    relevant_items = [i for i in items if _looks_sports_related(i["title"])]
    for item in relevant_items[:TOPICS_PER_CATEGORY]:
        topic = _extract_topic(item["title"])
        key = topic.lower()
        if not topic or key in seen:
            continue
        seen.add(key)
        topics.append({
            "topic": topic,
            "source_headline": item["title"],
            "source_description": item.get("description", ""),
            "source_url": item["url"],
            "source_category": "country_trending",
        })
    return topics


def _pick_countries(last_checked: dict, batch_size: int) -> list[dict]:
    """Oldest-checked-first rotation across all 28 countries, mirroring
    agent_keyword_research.py, so trending coverage reaches every market
    instead of always refreshing the same first few."""
    ordered = sorted(AFRICAN_COUNTRIES, key=lambda c: last_checked.get(c["code"], ""))
    return ordered[:batch_size]


def _load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return {"trending": {}, "country_last_checked": {}, "runs": 0}


def _save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def research_trending_pair(topic: str, country_name: str) -> dict:
    primary_keyword = f"{topic} betting tips {country_name}"
    variants = [
        primary_keyword,
        f"{topic} odds {country_name} today",
        f"how to bet on {topic} in {country_name}",
    ]
    results = fc_search(primary_keyword, limit=10)
    position = find_site_position(results)
    top_competitors = [
        {"title": r.get("title", ""), "url": r.get("url", "")}
        for r in results[:5]
        if "sifufinds.com" not in (r.get("url") or "")
    ]
    return {
        "primary_keyword": primary_keyword,
        "keyword_variants": variants,
        "sifufinds_ranks": position is not None,
        "sifufinds_position": position,
        "top_competitors": top_competitors,
        "content_type_suggestion": _suggest_content_type(topic, primary_keyword),
    }


def run(batch_size: int = BATCH_SIZE) -> int:
    state = _load_state()
    state["runs"] = state.get("runs", 0) + 1
    trending = state.setdefault("trending", {})
    last_checked = state.setdefault("country_last_checked", {})

    countries = _pick_countries(last_checked, batch_size)
    print(f"Trending Keywords Agent — researching each of {len(countries)} countr{'y' if len(countries) == 1 else 'ies'}' own trending topics this run")

    # Lazy, computed at most once, only if some country's own search comes
    # up empty this run — see _fresh_topics()'s docstring.
    fallback_topics: Optional[list[dict]] = None

    today = datetime.now(timezone.utc).isoformat()
    gaps_found = 0
    countries_checked = 0
    for country in countries:
        country_topics = _topics_for_country(country["name"])
        source_scope = "country_specific"
        if country_topics:
            topic_data = country_topics[0]
        else:
            if fallback_topics is None:
                fallback_topics = _fresh_topics()
            if not fallback_topics:
                print(f"  → [{country['name']}] no fresh topics found (country-specific or fallback) — skipping this run")
                continue
            topic_data = random.choice(fallback_topics)
            source_scope = "fallback_global"

        topic = topic_data["topic"]
        scope_note = "" if source_scope == "country_specific" else " (fallback — no country-specific trend found)"
        print(f"  → [{country['name']}] {topic}{scope_note}")
        try:
            result = research_trending_pair(topic, country["name"])
        except Exception as e:
            log("trending_keywords", "research_trending_pair", "error", f"{topic}/{country['name']}: {e}")
            print(f"    ✗ error: {e}")
            continue

        countries_checked += 1
        key = f"{country['code']}:{topic.lower()[:60]}"
        trending[key] = {
            "country": country["name"],
            "country_code": country["code"],
            "topic": topic,
            "source_headline": topic_data["source_headline"],
            "source_description": topic_data.get("source_description", ""),
            "source_url": topic_data["source_url"],
            "source_category": topic_data["source_category"],
            "source_scope": source_scope,
            "checked_at": today,
            **result,
        }
        last_checked[country["code"]] = today

        if not result["sifufinds_ranks"]:
            gaps_found += 1
            print(f"    ⚠ gap — SifuFinds not in top 10, {len(result['top_competitors'])} competitor(s) found")
        else:
            print(f"    ✓ ranking at position {result['sifufinds_position']}")

    # Cap total tracked entries, keeping the most recently checked.
    if len(trending) > MAX_ENTRIES:
        newest = sorted(trending.items(), key=lambda kv: kv[1]["checked_at"], reverse=True)[:MAX_ENTRIES]
        state["trending"] = dict(newest)

    state["generated_at"] = today
    _save_state(state)
    log("trending_keywords", "run", "ok", f"{countries_checked} countr(y/ies), {gaps_found} gap(s)")
    print(f"\n✅ {countries_checked} countr{'y' if countries_checked == 1 else 'ies'} checked against fresh trending topics, {gaps_found} gap(s) with no current SifuFinds ranking.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()
    return run(batch_size=args.batch_size)


if __name__ == "__main__":
    sys.exit(main())
