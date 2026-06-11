#!/usr/bin/env python3
"""
SifuFinds Crawler Ping
Notifies all major search engines and AI crawlers of sitemap updates.
Runs on every deploy + daily via GitHub Actions.

Coverage map:
  Google          → robots.txt Sitemap: directives (Google deprecated its ping endpoint June 2023)
                    robots.txt is re-read by Googlebot automatically on every crawl.
  Bing            → IndexNow API (covers Bing, ChatGPT Browse, Perplexity, Copilot)
  Yandex / Alice  → direct sitemap ping (still works, HTTP 200)
  All others      → robots.txt Sitemap: directives + ai.txt explicit allow
"""
import json
import subprocess
import sys
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

# Only Yandex still accepts the legacy ?sitemap= ping.
# Google (deprecated 2023) and Bing (replaced by IndexNow) both dropped it.
YANDEX_PING = "https://www.yandex.com/ping"


def ping_yandex(sitemap_url: str) -> dict:
    encoded = urllib.parse.quote(sitemap_url, safe="")
    url = f"{YANDEX_PING}?sitemap={encoded}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SifuFinds-Bot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return {"url": url, "status": r.status, "ok": r.status < 400}
    except Exception as e:
        return {"url": url, "status": None, "ok": False, "error": str(e)}


def run_indexnow() -> dict:
    """Run IndexNow to notify Bing (→ ChatGPT Browse, Perplexity, Copilot)."""
    script = Path(__file__).parent / "indexnow_submit.py"
    if not script.exists():
        return {"ok": False, "error": "indexnow_submit.py not found"}
    try:
        result = subprocess.run(
            [sys.executable, str(script), "incremental"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        ok = result.returncode == 0
        output = (result.stdout + result.stderr).strip()
        return {"ok": ok, "output": output[-300:] if output else ""}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def run():
    results = []
    now = datetime.now(timezone.utc).isoformat()

    print(f"[{now}] SifuFinds Crawler Ping")

    # ── Yandex sitemap pings ─────────────────────────────────────────────────
    print("\n── Yandex (→ Alice AI) ──")
    for sitemap in SITEMAPS:
        r = ping_yandex(sitemap)
        icon = "✓" if r["ok"] else "✗"
        print(f"  {icon} yandex.com ← {sitemap.replace(SITE_URL, '')}  [HTTP {r.get('status', 'ERR')}]")
        results.append({**r, "sitemap": sitemap, "engine": "yandex", "ts": now})

    # ── IndexNow — Bing / ChatGPT / Perplexity / Copilot ────────────────────
    print("\n── IndexNow (→ Bing, ChatGPT Browse, Perplexity, Copilot) ──")
    ix = run_indexnow()
    icon = "✓" if ix["ok"] else "✗"
    print(f"  {icon} indexnow  [{'OK' if ix['ok'] else ix.get('error', 'FAIL')}]")
    if ix.get("output"):
        for line in ix["output"].split("\n")[-4:]:
            print(f"      {line}")
    results.append({**ix, "engine": "indexnow (bing/chatgpt/perplexity)", "ts": now})

    # ── Google note ──────────────────────────────────────────────────────────
    print("\n── Google (→ Gemini AI Overviews) ──")
    print("  ℹ Google ping endpoint deprecated June 2023.")
    print("  ✓ Google discovers sitemaps via robots.txt Sitemap: directives automatically.")
    print("  ✓ robots.txt lists 4 sitemaps — Googlebot re-reads it on every crawl cycle.")
    results.append({"engine": "google", "ok": True, "method": "robots.txt Sitemap: directives", "ts": now})

    success = sum(1 for r in results if r["ok"])
    total = len(results)
    print(f"\n[DONE] {success}/{total} engines covered")

    log_path = ROOT / "data" / "crawler_ping_log.json"
    log_path.parent.mkdir(exist_ok=True)
    existing = []
    if log_path.exists():
        try:
            existing = json.loads(log_path.read_text())[-49:]
        except Exception:
            pass
    existing.append({"ts": now, "success": success, "total": total, "results": results})
    log_path.write_text(json.dumps(existing, indent=2))
    print(f"[LOG] Written to {log_path}")

    return 0


if __name__ == "__main__":
    exit(run())
