#!/usr/bin/env python3
"""Notify Bing/Yandex/Seznam/Naver via the shared IndexNow protocol whenever
content changes, instead of waiting for their crawlers to rediscover it.

Why this exists: found 2026-08-21 during an SEO/GEO audit — this site
publishes at high frequency (multiple posts/day via automated agents, per
the daily/2-hourly content agent schedules elsewhere in this repo) but had
no IndexNow integration, so Bing/Yandex only learn about new or changed
pages on their own crawl schedule. Google is unaffected (it doesn't
participate in IndexNow; Search Console/the Indexing API is the equivalent
there and is a separate integration).

Protocol: https://www.indexnow.org/ — a single HTTP POST naming the changed
URLs plus a key, verified by fetching https://<host>/<key>.txt (that file
must contain exactly the key and be deployed at the site root — see
99f774fee94b3f7a1cd2ade69cdcefb6.txt, and note it's on the explicit
top-level-file allow-list in .github/workflows/deploy_hostinger.yml's
"Build deployment archive" step, since that step doesn't deploy top-level
files by default the way it does top-level directories).

Usage:
    python3 scripts/submit_indexnow.py <url> [<url> ...]   # specific URLs
    python3 scripts/submit_indexnow.py --sitemap            # every URL in every sitemap-*.xml

Never raises on network/API failure — IndexNow is a best-effort indexing
signal, not a build-blocking requirement, so a submission failure must
never fail whatever pipeline called this (e.g. the post-deploy step in
deploy_hostinger.yml).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "sifufinds.com"
KEY = "99f774fee94b3f7a1cd2ade69cdcefb6"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"

# IndexNow allows up to 10,000 URLs per submission; well below that keeps
# each call small and fast, and a full-sitemap submission is a rare/manual
# operation, not something run on every single page change.
MAX_URLS_PER_CALL = 500


def _sitemap_urls() -> list[str]:
    urls: list[str] = []
    for sitemap_path in sorted(ROOT.glob("sitemap*.xml")):
        try:
            tree = ET.parse(sitemap_path)
        except ET.ParseError:
            continue
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        # Both a sitemap index (<sitemap><loc>) and a URL set (<url><loc>)
        # use the same tag name once the namespace prefix is stripped.
        for loc in tree.getroot().iter(f"{ns}loc"):
            if loc.text and loc.text.startswith("https://sifufinds.com/"):
                urls.append(loc.text.strip())
    return urls


def submit(urls: list[str]) -> bool:
    """POST `urls` to IndexNow. Returns True on a 200/202 response, False
    on any failure — never raises."""
    urls = [u for u in urls if u.startswith(f"https://{HOST}/")]
    if not urls:
        print("IndexNow: no sifufinds.com URLs to submit — skipping.")
        return True

    ok = True
    for i in range(0, len(urls), MAX_URLS_PER_CALL):
        batch = urls[i : i + MAX_URLS_PER_CALL]
        payload = json.dumps(
            {"host": HOST, "key": KEY, "keyLocation": KEY_LOCATION, "urlList": batch}
        ).encode("utf-8")
        req = urllib.request.Request(
            ENDPOINT, data=payload, headers={"Content-Type": "application/json; charset=utf-8"}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = resp.status
        except urllib.error.HTTPError as e:
            status = e.code
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"IndexNow: submission failed for batch of {len(batch)} URLs — {e}")
            ok = False
            continue

        if status in (200, 202):
            print(f"IndexNow: submitted {len(batch)} URL(s) — HTTP {status}")
        else:
            print(f"IndexNow: unexpected response for batch of {len(batch)} URLs — HTTP {status}")
            ok = False
    return ok


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    if args == ["--sitemap"]:
        urls = _sitemap_urls()
        print(f"IndexNow: submitting {len(urls)} URL(s) discovered from sitemap*.xml")
    else:
        urls = args

    ok = submit(urls)
    # Always exit 0: see module docstring — never fail a caller over a
    # best-effort indexing signal.
    if not ok:
        print("IndexNow: one or more batches failed — not treated as a fatal error.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
