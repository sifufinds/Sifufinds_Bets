#!/usr/bin/env python3
"""Liveness check for every RSS feed the content pipeline depends on.

agent_sports_blog.py (via agents/python/utils/news_fetcher.py) needs fresh,
real headlines before it's allowed to write a post — fetch_category() returns
[] and the agent skips generation if too few live items come back. A feed
going dead is non-fatal by design (the other layers pick up the slack), but
it's silent: nothing errors, a source just quietly stops contributing. A full
audit on 2026-07-25 found 15 of ~40 configured feeds (every espn.com/espn/rss/*
url, every skysports.com/rss/* url, all of mirror.co.uk, Calvinayre, and the
Guardian betting feed) had rotted dead or empty without anyone noticing.

Run this periodically (see .github/workflows/check_news_feeds.yml) to catch
the next round of rot before it silently erodes coverage again.

Usage:
  python3 scripts/check_news_feeds.py            # human-readable report
  python3 scripts/check_news_feeds.py --exit-code # also exit 1 if any feed is dead/empty
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents" / "python"))

from utils.news_fetcher import FEEDS, _fetch_url, _parse_rss  # noqa: E402


def main() -> None:
    strict = "--exit-code" in sys.argv
    seen: set[str] = set()
    dead: list[str] = []
    empty: list[str] = []
    ok = 0

    for source, url, category in FEEDS:
        if url in seen:
            continue
        seen.add(url)
        data = _fetch_url(url)
        if not data:
            print(f"DEAD    {source:32s} [{category:12s}] {url}")
            dead.append(source)
            continue
        items = _parse_rss(data, source, category, max_age_hours=24 * 365)
        if not items:
            print(f"EMPTY   {source:32s} [{category:12s}] {url}")
            empty.append(source)
            continue
        ok += 1
        print(f"OK      {source:32s} [{category:12s}] {len(items):3d} items")

    total = len(seen)
    print(f"\n{ok}/{total} feeds live, {len(dead)} dead, {len(empty)} empty (0 items)")
    if dead or empty:
        print("Dead/empty feeds still return [] safely (non-fatal), but should be")
        print("replaced or removed from FEEDS in agents/python/utils/news_fetcher.py.")

    if strict and (dead or empty):
        sys.exit(1)


if __name__ == "__main__":
    main()
