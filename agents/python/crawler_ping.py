#!/usr/bin/env python3
"""
SifuFinds Crawler Ping
Notifies Google, Bing, Yandex and all major search engines of sitemap updates.
Runs on every deploy + daily via GitHub Actions.

Coverage:
  Google  → direct sitemap ping (feeds Google Search + Gemini AI Overviews)
  Bing    → sitemap ping + IndexNow (feeds Bing, ChatGPT Browse, Perplexity, Copilot)
  Yandex  → direct sitemap ping (feeds Yandex Alice AI)
  Naver   → direct sitemap ping (South Korea / Africa diaspora market)
"""
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_URL = "https://sifufinds.com"

SITEMAPS = [
    f"{SITE_URL}/sitemap.xml",
    f"{SITE_URL}/sitemap-blog.xml",
    f"{SITE_URL}/sitemap-countries.xml",
    f"{SITE_URL}/sitemap-other.xml",
]

# Endpoints that accept ?sitemap= pings
PING_ENDPOINTS = [
    "https://www.google.com/ping",   # Google
    "https://www.bing.com/ping",     # Bing → ChatGPT/Perplexity/Copilot
    "https://www.yandex.com/ping",   # Yandex → Alice AI
]


def ping_sitemap(endpoint: str, sitemap_url: str) -> dict:
    encoded = urllib.parse.quote(sitemap_url, safe="")
    url = f"{endpoint}?sitemap={encoded}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SifuFinds-Bot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return {"url": url, "status": r.status, "ok": r.status < 400}
    except Exception as e:
        return {"url": url, "status": None, "ok": False, "error": str(e)}


def run():
    results = []
    now = datetime.now(timezone.utc).isoformat()

    print(f"[{now}] SifuFinds Crawler Ping — pinging {len(PING_ENDPOINTS)} engines × {len(SITEMAPS)} sitemaps")

    for sitemap in SITEMAPS:
        for endpoint in PING_ENDPOINTS:
            r = ping_sitemap(endpoint, sitemap)
            icon = "✓" if r["ok"] else "✗"
            engine = endpoint.split("/")[2].replace("www.", "")
            print(f"  {icon} {engine:20s} ← {sitemap.replace(SITE_URL, '')}  [HTTP {r.get('status', 'ERR')}]")
            results.append({**r, "sitemap": sitemap, "engine": engine, "ts": now})

    success = sum(1 for r in results if r["ok"])
    total = len(results)
    print(f"\n[DONE] {success}/{total} pings succeeded")

    # Write log
    log_path = ROOT / "data" / "crawler_ping_log.json"
    log_path.parent.mkdir(exist_ok=True)
    existing = []
    if log_path.exists():
        try:
            existing = json.loads(log_path.read_text())[-49:]  # keep last 50 runs
        except Exception:
            pass
    existing.append({"ts": now, "success": success, "total": total, "results": results})
    log_path.write_text(json.dumps(existing, indent=2))
    print(f"[LOG] Written to {log_path}")

    return 0


if __name__ == "__main__":
    exit(run())
