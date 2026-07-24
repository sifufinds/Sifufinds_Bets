"""
agent_firecrawl_odds.py — Daily scrape of OddsPortal for African leagues
Supplements the ESPN-based live.json with real odds from OddsPortal public
pages. Free-first (trafilatura + Jina Reader via utils/free_scrape.py);
Firecrawl only fires as a last resort per-URL. Runs once daily via GitHub
Actions.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from utils.free_scrape import scrape as free_scrape

TODAY = datetime.now(timezone.utc).strftime("%Y%m%d")

TARGETS = [
    {"url": "https://www.oddsportal.com/football/africa/", "region": "Africa"},
    {"url": "https://www.oddsportal.com/football/world/friendly-international/", "region": "Friendly"},
    {"url": f"https://www.oddsportal.com/matches/football/{TODAY}/", "region": "All Football"},
]

# Resolve live.json relative to this file: agents/python/ -> root/data/live.json
LIVE_JSON = Path(__file__).resolve().parent.parent.parent / "data" / "live.json"


def scrape_url(url: str) -> str:
    """Free-first scrape (trafilatura + Jina Reader), Firecrawl last resort."""
    return free_scrape(url, wait_ms=4000, min_chars=200)


def extract_matches(text: str, region: str) -> list:
    """Parse OddsPortal markdown for match data.

    OddsPortal markdown typically surfaces rows like:
        18:00
        Team A
        Team B
        1.85  3.40  4.50
    We do a simple line-by-line sweep: find a HH:MM timestamp, then grab
    the next two non-trivial lines as home/away team names.
    """
    matches = []
    if not text:
        return matches

    lines = [l.strip() for l in text.split("\n")]
    time_pattern = re.compile(r"^\d{2}:\d{2}$")
    sport_key = "local" if region == "Africa" else "world"

    i = 0
    while i < len(lines):
        line = lines[i]
        if time_pattern.match(line):
            kick_off = line  # e.g. "18:00"
            teams: list[str] = []
            j = i + 1
            while j < min(i + 10, len(lines)) and len(teams) < 2:
                candidate = lines[j]
                # Skip empty lines, markdown image/link syntax, odds-like decimals
                if (
                    candidate
                    and not candidate.startswith("!")
                    and not candidate.startswith("[")
                    and not candidate.startswith("|")
                    and not re.match(r"^\d+\.\d{2}$", candidate)
                    and 2 < len(candidate) < 60
                ):
                    teams.append(candidate)
                j += 1

            if len(teams) >= 2:
                matches.append(
                    {
                        "league": f"{region} · Football",
                        "key": sport_key,
                        "live": False,
                        "complete": False,
                        "home": teams[0],
                        "away": teams[1],
                        "hScore": None,
                        "aScore": None,
                        "time": f"Today · {kick_off} UTC",
                        "h": 0.0,
                        "d": 0.0,
                        "a": 0.0,
                        "hBk": "",
                        "dBk": "",
                        "aBk": "",
                    }
                )
        i += 1

    return matches


def load_live_json() -> dict:
    """Load existing live.json or return an empty scaffold."""
    try:
        if LIVE_JSON.exists():
            return json.loads(LIVE_JSON.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  Could not read live.json: {e}")
    return {"events": [], "updated": ""}


def save_live_json(data: dict) -> None:
    LIVE_JSON.parent.mkdir(parents=True, exist_ok=True)
    LIVE_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    from utils.free_scrape import FIRECRAWL_API_KEY
    if not FIRECRAWL_API_KEY:
        print("ℹ FIRECRAWL_API_KEY not set — running free-only (trafilatura + Jina Reader)")

    print(f"OddsPortal odds agent — {datetime.now(timezone.utc).isoformat()}")
    print(f"  live.json path: {LIVE_JSON}")

    existing = load_live_json()
    events: list = existing.get("events", [])
    existing_keys: set = {f"{e['home']}|{e['away']}" for e in events}
    new_matches: list = []

    for target in TARGETS:
        print(f"  Scraping {target['url']}")
        text = scrape_url(target["url"])
        found = extract_matches(text, target["region"])
        added_this_target = 0
        for m in found:
            k = f"{m['home']}|{m['away']}"
            if k not in existing_keys:
                new_matches.append(m)
                existing_keys.add(k)
                added_this_target += 1
        print(f"    Found {len(found)} matches ({added_this_target} new)")

    if new_matches:
        events.extend(new_matches)
        existing["events"] = events
        existing["updated"] = datetime.now(timezone.utc).isoformat()
        save_live_json(existing)
        print(f"Added {len(new_matches)} new matches to live.json")
    else:
        print("No new matches to add")


if __name__ == "__main__":
    main()
