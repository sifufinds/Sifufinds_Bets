#!/usr/bin/env python3
"""
SifuFinds IndexNow Submitter
Submits recently changed or new URLs to IndexNow (Bing/Yandex).
Bing feeds ChatGPT Browse + Perplexity — this directly boosts AI readiness.
Run on every deploy via GitHub Actions.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEXNOW_KEY = "ed3656512e7456003ee2a5c4f3139c55"
SITE_URL = "https://sifufinds.com"
MAX_URLS_PER_BATCH = 10000

# IndexNow endpoints — submit to Bing (covers Bing, DuckDuckGo, Yandex, and via Bing → ChatGPT/Perplexity)
INDEXNOW_ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
]

def get_changed_urls():
    """Get URLs for files changed in the last git push."""
    try:
        # Files changed in last commit
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            cwd=str(ROOT), capture_output=True, text=True
        )
        changed = result.stdout.strip().split('\n') if result.stdout.strip() else []
    except Exception:
        changed = []

    urls = set()
    for f in changed:
        if not f.endswith('.html'):
            continue
        # Convert file path to URL
        path = f.replace('index.html', '').rstrip('/')
        url = f"{SITE_URL}/{path}/" if path else f"{SITE_URL}/"
        url = re.sub(r'/+', '/', url.replace(SITE_URL + '/', SITE_URL + '/'))
        urls.add(url)

    return list(urls)

def get_sitemap_urls():
    """Fallback: get all URLs from sitemap for a full resubmission."""
    urls = []
    for sm_file in ROOT.glob('sitemap-*.xml'):
        content = sm_file.read_text()
        found = re.findall(r'<loc>(https://[^<]+)</loc>', content)
        urls.extend(found)
    return list(set(urls))[:MAX_URLS_PER_BATCH]

def submit_to_indexnow(urls, endpoint):
    """POST a batch of URLs to IndexNow endpoint."""
    if not urls:
        return False, "No URLs to submit"

    payload = json.dumps({
        "host": "sifufinds.com",
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": urls
    }).encode('utf-8')

    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "SifuFinds-IndexNow/1.0"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.getcode()
            return status in (200, 202), f"HTTP {status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return False, str(e)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "incremental"

    if mode == "full":
        urls = get_sitemap_urls()
        print(f"Full submission: {len(urls)} URLs from sitemaps")
    else:
        urls = get_changed_urls()
        if not urls:
            # Fall back to submitting key pages on every deploy
            urls = [
                f"{SITE_URL}/",
                f"{SITE_URL}/blog/",
                f"{SITE_URL}/tips/",
                f"{SITE_URL}/odds/",
                f"{SITE_URL}/countries/",
            ]
        print(f"Incremental submission: {len(urls)} changed/key URLs")

    print(f"URLs to submit: {urls[:10]}{'...' if len(urls)>10 else ''}")

    success_count = 0
    for endpoint in INDEXNOW_ENDPOINTS:
        ok, msg = submit_to_indexnow(urls, endpoint)
        status = "✅" if ok else "⚠️"
        print(f"  {status} {endpoint}: {msg}")
        if ok:
            success_count += 1

    # Log result
    log_path = ROOT / "data" / "indexnow_log.json"
    log_path.parent.mkdir(exist_ok=True)
    log = []
    if log_path.exists():
        try:
            log = json.loads(log_path.read_text())[-49:]  # keep last 50
        except Exception:
            log = []
    log.append({
        "date": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "urls_submitted": len(urls),
        "endpoints_ok": success_count,
    })
    log_path.write_text(json.dumps(log, indent=2))

    print(f"\nIndexNow submission complete: {success_count}/{len(INDEXNOW_ENDPOINTS)} endpoints OK")
    sys.exit(0)

if __name__ == "__main__":
    main()
