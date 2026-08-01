"""
Trending Keywords Agent — pairs today's fresh news headlines with country
intent modifiers to surface time-sensitive keyword opportunities across all
23 African markets SifuFinds serves, for direct use by blog/news/guide
writers.

Distinct from agent_keyword_research.py: that agent tracks a fixed backlog
of evergreen money keywords ("best betting sites {country} 2026") that
barely change month to month. This agent re-seeds itself from real,
freshness-checked news every run (reusing utils/news_fetcher.py, the same
free multi-source feed agent_sports_blog.py already writes from), so the
keyword ideas it produces are genuinely trending — a live fixture, a
transfer story, a tournament headline — rather than a static template.

Free-first, no LLM calls: news comes from utils/news_fetcher.py (DuckDuckGo
+ Google News RSS + site feeds, no API key) and SERP checks come from
utils/serp_research.py's fc_search()/find_site_position() (DuckDuckGo,
Firecrawl only as an opt-in last resort) — the same free pipeline every
other keyword/SERP agent in this repo already uses.

Usage:
    python agent_trending_keywords.py                # next batch of countries
    python agent_trending_keywords.py --batch-size 15
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from utils.countries import AFRICAN_COUNTRIES
from utils.logger import log
from utils.news_fetcher import fetch_category
from utils.serp_research import fc_search, find_site_position

STATE_PATH = Path(__file__).parent / "trending_keywords.json"
BATCH_SIZE = 10
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
    subject so the same story doesn't dominate every country pairing."""
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
                "source_url": item["url"],
                "source_category": category,
            })
    return topics


def _pick_countries(last_checked: dict, batch_size: int) -> list[dict]:
    """Oldest-checked-first rotation across all 23 countries, mirroring
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

    topics = _fresh_topics()
    if not topics:
        print("No fresh trending topics found this run (all sources below freshness window) — skipping")
        log("trending_keywords", "run", "skipped", "no fresh topics")
        _save_state(state)
        return 0

    countries = _pick_countries(last_checked, batch_size)
    print(f"Trending Keywords Agent — {len(topics)} fresh topic(s), pairing with {len(countries)} countr{'y' if len(countries) == 1 else 'ies'} this run")

    today = datetime.now(timezone.utc).isoformat()
    gaps_found = 0
    for i, country in enumerate(countries):
        topic_data = topics[i % len(topics)]
        topic = topic_data["topic"]
        print(f"  → [{country['name']}] {topic}")
        try:
            result = research_trending_pair(topic, country["name"])
        except Exception as e:
            log("trending_keywords", "research_trending_pair", "error", f"{topic}/{country['name']}: {e}")
            print(f"    ✗ error: {e}")
            continue

        key = f"{country['code']}:{topic.lower()[:60]}"
        trending[key] = {
            "country": country["name"],
            "country_code": country["code"],
            "topic": topic,
            "source_headline": topic_data["source_headline"],
            "source_url": topic_data["source_url"],
            "source_category": topic_data["source_category"],
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
    log("trending_keywords", "run", "ok", f"{len(countries)} countr(y/ies), {gaps_found} gap(s)")
    print(f"\n✅ {len(countries)} countr{'y' if len(countries) == 1 else 'ies'} checked against fresh trending topics, {gaps_found} gap(s) with no current SifuFinds ranking.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()
    return run(batch_size=args.batch_size)


if __name__ == "__main__":
    sys.exit(main())
