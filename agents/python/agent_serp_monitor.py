"""
SERP Monitoring Agent — tracks SifuFinds' rank position over time for a
watchlist of keywords tied to content that already exists (bookmaker
reviews, evergreen comparisons, core tools), so a real ranking regression
gets caught rather than only discovering it anecdotally from a traffic drop.

Distinct from agent_keyword_research.py: that agent hunts for NEW keyword
opportunities SifuFinds may not rank for yet; this one watches a small,
stable set of keywords SifuFinds SHOULD already rank for and flags when a
position gets meaningfully worse. No historical rank-tracking storage
existed anywhere in this repo before this agent.

Usage:
    python agent_serp_monitor.py                # next batch of the watchlist
    python agent_serp_monitor.py --batch-size 12  # check the whole watchlist in one run
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from utils.logger import log
from utils.serp_research import fc_search, find_site_position

HISTORY_PATH = Path(__file__).parent / "serp_rank_history.json"
REGRESSIONS_PATH = Path(__file__).parent / "serp_regressions.json"
BOOKMAKER_LINKS_PATH = Path(__file__).parent.parent.parent / "data" / "bookmaker_links.json"

BATCH_SIZE = 6
MAX_HISTORY_PER_KEYWORD = 90  # roughly a quarter of daily-ish checks
# A position getting this many places worse (or dropping out of the top 10
# entirely, tracked separately below) is worth a human looking at, not just
# ordinary week-to-week SERP noise.
REGRESSION_THRESHOLD = 5

EVERGREEN_WATCHLIST = [
    "odds calculator",
    "accumulator calculator africa",
    "bet9ja vs sportybet",
    "1xbet vs betway africa",
]


def _bookmaker_watchlist() -> list[str]:
    if not BOOKMAKER_LINKS_PATH.exists():
        return []
    try:
        data = json.loads(BOOKMAKER_LINKS_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    return [
        f"{e['keyword']} review 2026"
        for e in data.get("bookmakers", [])
        if e.get("status") == "active"
    ]


def _watchlist() -> list[str]:
    return EVERGREEN_WATCHLIST + _bookmaker_watchlist()


def _load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return default


def _save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _pick_batch(watchlist: list[str], history: dict, batch_size: int) -> list[str]:
    never_checked = [k for k in watchlist if k not in history or not history[k]]
    if len(never_checked) >= batch_size:
        return never_checked[:batch_size]
    stale_first = sorted(
        (k for k in watchlist if k in history and history[k]),
        key=lambda k: history[k][-1].get("date", ""),
    )
    return never_checked + stale_first[: batch_size - len(never_checked)]


def check_keyword(keyword: str) -> int | None:
    results = fc_search(keyword, limit=10)
    return find_site_position(results)


def run(batch_size: int = BATCH_SIZE) -> int:
    watchlist = _watchlist()
    history = _load_json(HISTORY_PATH, {})
    regressions = _load_json(REGRESSIONS_PATH, [])

    batch = _pick_batch(watchlist, history, batch_size)
    print(f"SERP Monitoring Agent — {len(watchlist)} keyword(s) on watchlist, checking {len(batch)} this run")

    flagged = 0
    today = datetime.now(timezone.utc).date().isoformat()
    for keyword in batch:
        print(f"  → {keyword}")
        try:
            position = check_keyword(keyword)
        except Exception as e:
            log("serp_monitor", "check_keyword", "error", f"{keyword}: {e}")
            print(f"    ✗ error: {e}")
            continue

        prior = history.get(keyword, [])
        prior_position = prior[-1]["position"] if prior else None

        history.setdefault(keyword, []).append({"date": today, "position": position})
        history[keyword] = history[keyword][-MAX_HISTORY_PER_KEYWORD:]

        regressed = (
            prior_position is not None
            and (position is None or (position - prior_position) >= REGRESSION_THRESHOLD)
        )
        if regressed:
            flagged += 1
            regressions.append({
                "keyword": keyword,
                "prior_position": prior_position,
                "new_position": position,
                "detected_at": datetime.now(timezone.utc).isoformat(),
            })
            print(f"    ⚠ REGRESSION — was #{prior_position}, now {'unranked (outside top 10)' if position is None else f'#{position}'}")
            log("serp_monitor", "check_keyword", "regression",
                f"{keyword}: #{prior_position} -> {position}")
        else:
            print(f"    ✓ position: {position if position is not None else 'unranked (outside top 10)'}"
                  f"{f' (was #{prior_position})' if prior_position is not None else ''}")

    _save_json(HISTORY_PATH, history)
    _save_json(REGRESSIONS_PATH, regressions[-200:])
    log("serp_monitor", "run", "ok", f"checked {len(batch)}, {flagged} regression(s) flagged")
    print(f"\n✅ {len(batch)} keyword(s) checked, {flagged} regression(s) flagged this run.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()
    return run(batch_size=args.batch_size)


if __name__ == "__main__":
    sys.exit(main())
