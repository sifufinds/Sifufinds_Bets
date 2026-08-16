"""
agent_firecrawl_odds.py — Daily scrape of OddsPortal for real 1X2 odds
Supplements the ESPN/Sofascore/Flashscore-based live.json with real prices
from OddsPortal (utils/oddsportal_parser.py). Free-first (trafilatura +
Jina Reader via utils/free_scrape.py); Firecrawl only fires as a last
resort per-URL. Runs once daily via GitHub Actions, alongside the every-15-
minute agent_multi_scrape.py which covers the same source more frequently —
this job is a supplementary daily pass, not the primary one.
"""
from datetime import datetime, timedelta, timezone

from utils.free_scrape import scrape as free_scrape
from utils.live_data_helpers import fmt_time, league_key
from utils.live_json_store import enrich_existing, load_live_json, match_key, save_live_json
from utils.oddsportal_parser import parse_oddsportal

TODAY = datetime.now(timezone.utc).strftime("%Y%m%d")
TOMORROW = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y%m%d")

TARGETS = [
    f"https://www.oddsportal.com/matches/football/{TODAY}/",
    f"https://www.oddsportal.com/matches/football/{TOMORROW}/",
    "https://www.oddsportal.com/football/world/friendly-international/",
]


def scrape_url(url: str) -> str:
    """Free-first scrape (trafilatura + Jina Reader), Firecrawl last resort."""
    # 1500 char floor: OddsPortal's boilerplate-only trafilatura fetch tops
    # out around ~1200 chars, so a lower floor risks accepting junk instead
    # of escalating to Jina Reader/Firecrawl.
    return free_scrape(url, wait_ms=4000, min_chars=1500)


def main() -> None:
    from utils.free_scrape import FIRECRAWL_API_KEY
    if not FIRECRAWL_API_KEY:
        print("ℹ FIRECRAWL_API_KEY not set — running free-only (trafilatura + Jina Reader)")

    print(f"OddsPortal odds agent — {datetime.now(timezone.utc).isoformat()}")

    existing = load_live_json()
    events: list[dict] = existing.get("events", [])
    print(f"  Existing events in live.json: {len(events)}")

    all_new: list[dict] = []
    for url in TARGETS:
        print(f"  Scraping {url}")
        text = scrape_url(url)
        found = parse_oddsportal(text, league_key, fmt_time)
        print(f"    Found {len(found)} matches with real odds")
        all_new.extend(found)

    merged = enrich_existing(events, all_new)
    for e in merged:
        e.pop("_src", None)

    if all_new:
        output = {
            "updated": datetime.now(timezone.utc).isoformat(),
            "count": len(merged),
            "events": merged,
        }
        save_live_json(output)
        new_count = len(merged) - len(events)
        print(f"✅ live.json updated: {len(merged)} total events ({new_count} new, {len(all_new)} OddsPortal matches with real odds)")
    else:
        print("No new data to add")


if __name__ == "__main__":
    main()
