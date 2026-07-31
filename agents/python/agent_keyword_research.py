"""
Keyword Research Agent — discovers keyword opportunities for SifuFinds'
core topics x countries, persisting a standing backlog other content agents
can draw from (agent_sports_blog.py, agent_content_backfill.py) instead of
each doing one-off, un-persisted research per article.

Previously the only keyword research in this repo happened per-article
inside agent_sports_blog.generate_post() via utils/serp_research.research()
— useful in the moment, but nothing about it was ever saved for reuse or
prioritisation. This agent runs independently, on a batch of seed keywords
per run (mirrors agent_content_backfill.py's resumable pattern), and writes
findings to keyword_opportunities.json: whether SifuFinds already ranks for
each keyword, who the top competitors are, and PAA-style question gaps.

Usage:
    python agent_keyword_research.py                # next batch of seed keywords
    python agent_keyword_research.py --batch-size 8
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from config import COUNTRIES
from utils.logger import log
from utils.serp_research import fc_search, find_site_position, paa_hints_from_results

STATE_PATH = Path(__file__).parent / "keyword_opportunities.json"
BATCH_SIZE = 6

# Core money-keyword templates — the topics SifuFinds actually needs to rank
# for, not a random keyword list. Mirrors utils/serp_research.py's
# SLOT_KEYWORD_TEMPLATES/_CATEGORY_KEYWORDS shape but broader, since this
# agent's job is discovering gaps, not just picking one keyword per post.
KEYWORD_TEMPLATES = [
    "best betting sites {country} 2026",
    "best betting bonus {country} 2026",
    "{country} football betting tips today",
    "how to bet online {country} beginners guide",
    "best live odds {country} 2026",
    "safest betting apps {country}",
]


def _seed_keywords() -> list[str]:
    keywords = []
    for country in COUNTRIES:
        name = country["name"]
        for template in KEYWORD_TEMPLATES:
            keywords.append(template.format(country=name))
    return keywords


def _load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return {"opportunities": {}, "runs": 0}


def _save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def _pick_batch(seed_keywords: list[str], state: dict, batch_size: int) -> list[str]:
    """Oldest-checked-first rotation so every seed keyword gets refreshed
    eventually rather than always re-checking the same first few."""
    checked = state["opportunities"]
    never_checked = [k for k in seed_keywords if k not in checked]
    if len(never_checked) >= batch_size:
        return never_checked[:batch_size]
    stale_first = sorted(
        (k for k in seed_keywords if k in checked),
        key=lambda k: checked[k].get("checked_at", ""),
    )
    return never_checked + stale_first[: batch_size - len(never_checked)]


def research_keyword(keyword: str) -> dict:
    results = fc_search(keyword, limit=10)
    position = find_site_position(results)
    top_competitors = [
        {"title": r.get("title", ""), "url": r.get("url", "")}
        for r in results[:5]
        if "sifufinds.com" not in (r.get("url") or "")
    ]
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "sifufinds_ranks": position is not None,
        "sifufinds_position": position,
        "top_competitors": top_competitors,
        "paa_questions": paa_hints_from_results(results),
    }


def run(batch_size: int = BATCH_SIZE) -> int:
    seed_keywords = _seed_keywords()
    state = _load_state()
    state["runs"] = state.get("runs", 0) + 1

    batch = _pick_batch(seed_keywords, state, batch_size)
    print(f"Keyword Research Agent — {len(seed_keywords)} tracked keyword(s), researching {len(batch)} this run")

    gaps_found = 0
    for keyword in batch:
        print(f"  → {keyword}")
        try:
            result = research_keyword(keyword)
        except Exception as e:
            log("keyword_research", "research_keyword", "error", f"{keyword}: {e}")
            print(f"    ✗ error: {e}")
            continue

        state["opportunities"][keyword] = result
        if not result["sifufinds_ranks"]:
            gaps_found += 1
            print(f"    ⚠ gap — SifuFinds not in top 10, {len(result['top_competitors'])} competitor(s) found")
        else:
            print(f"    ✓ ranking at position {result['sifufinds_position']}")

    _save_state(state)
    log("keyword_research", "run", "ok", f"researched {len(batch)}, {gaps_found} gap(s) found")
    print(f"\n✅ {len(batch)} keyword(s) researched, {gaps_found} gap(s) with no current SifuFinds ranking.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()
    return run(batch_size=args.batch_size)


if __name__ == "__main__":
    sys.exit(main())
