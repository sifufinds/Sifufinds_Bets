#!/usr/bin/env python3
"""
SifuFinds — Real-time countries page data updater.

Uses Firecrawl CLI + Apify REST API to scrape live bonus offers and bookmaker
availability, then writes data/countries_live.json for the frontend to consume.

Run:     python3 update_countries.py
Schedule: every 4–6 hours via cron or GitHub Actions
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FC_DIR = BASE_DIR / ".firecrawl"
SCRAPER_STATE = BASE_DIR / "agents" / "python" / "scraper_state.json"
LIVE_OUT = DATA_DIR / "countries_live.json"

NOW = datetime.now(timezone.utc).isoformat()

# ── Bookmaker promo pages to scrape ───────────────────────────────────────────
BOOKMAKER_PAGES = [
    # Nigeria — use promotions / registration pages where bonus text appears
    ("Bet9ja",            "https://www.bet9ja.com/register"),
    ("1xBet Nigeria",     "https://1xbet.com/en/promo"),
    ("Betway Nigeria",    "https://www.betway.com/en-ng/promotions/sports/"),
    ("Sportybet Nigeria", "https://www.sportybet.com/ng/promotion/"),
    ("Melbet Nigeria",    "https://melbet.com/en/promo/"),
    ("BetWinner Nigeria", "https://betwinner.com/en/promo/"),
    # Kenya
    ("Betika Kenya",      "https://www.betika.com/en-ke/promotions"),
    ("SportPesa Kenya",   "https://www.sportpesa.co.ke/promotions"),
    ("Betway Kenya",      "https://www.betway.com/en-ke/promotions/sports/"),
    ("Odibets Kenya",     "https://odibets.com/promotions"),
    # South Africa
    ("Hollywoodbets",     "https://www.hollywoodbets.net/promotions/"),
    ("Supabets",          "https://www.supabets.com/promotions"),
    ("TicTacBets",        "https://www.tictacbets.co.za/promotions"),
    ("Betway South Africa", "https://www.betway.com/en-za/promotions/sports/"),
    # Pan-Africa
    ("Paripesa",          "https://paripesa.bet/en/promo/"),
    ("HelaBet",           "https://www.helabet.com/promotions"),
]

# ── Apify Google Search queries (one per priority country) ────────────────────
APIFY_QUERIES = [
    ("NG", "best betting sites Nigeria 2026 bonus"),
    ("KE", "best betting sites Kenya 2026 bonus"),
    ("ZA", "best betting sites South Africa 2026 bonus"),
    ("GH", "best betting sites Ghana 2026 bonus"),
    ("TZ", "best betting sites Tanzania 2026 bonus"),
    ("UG", "best betting sites Uganda 2026 bonus"),
    ("ZM", "best betting sites Zambia 2026"),
    ("RW", "best betting sites Rwanda 2026"),
    ("CM", "best betting sites Cameroon 2026"),
    ("SN", "best betting sites Senegal 2026"),
]

# ── Regex patterns for extracting bonus amounts ───────────────────────────────
BONUS_PATTERNS = [
    # Currency-first patterns: ₦1,200,000 / R25 / KSh 50,000 / GH₵500
    r"(?:up to|get|earn|claim|win|receive)\s*[^\n]{0,30}?(₦[\d,]+(?:\.\d+)?(?:,\d+)*)",
    r"(?:up to|get|earn|claim|win|receive)\s*[^\n]{0,30}?(R[\d,]+(?:\.\d+)?(?:,\d+)*)",
    r"(?:up to|get|earn|claim|win|receive)\s*[^\n]{0,30}?(KSh\s*[\d,]+)",
    r"(?:up to|get|earn|claim|win|receive)\s*[^\n]{0,30}?(GH₵[\d,]+)",
    r"(?:up to|get|earn|claim|win|receive)\s*[^\n]{0,30}?(TSh\s*[\d,]+)",
    # Percentage patterns
    r"(\d{2,3}%\s*(?:first\s*deposit|welcome|match|bonus))",
    # Freebet patterns
    r"([\w₦R$£€]+\s*[\d,]+\s*free\s*bet)",
    r"(free\s*bet\s*of\s*[\w₦R$£€]+\s*[\d,]+)",
]


def fc_scrape(url: str, out_name: str) -> str | None:
    """Scrape a URL with Firecrawl CLI; return content or None."""
    out = FC_DIR / f"live-{out_name}.md"
    try:
        r = subprocess.run(
            ["firecrawl", "scrape", url, "--only-main-content", "-o", str(out)],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode == 0 and out.exists():
            return out.read_text(encoding="utf-8", errors="ignore")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def extract_bonus(content: str) -> str | None:
    """Extract a bonus string from scraped page content."""
    if not content:
        return None
    for pattern in BONUS_PATTERNS:
        m = re.search(pattern, content, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            # Normalise whitespace and cap length
            return re.sub(r"\s+", " ", raw)[:80]
    return None


def apify_google_search(query: str, token: str, max_results: int = 5) -> list[dict]:
    """Run Apify google-search-scraper and return results. Returns [] on error."""
    api_url = "https://api.apify.com/v2/acts/apify~google-search-scraper/run-sync-get-dataset-items"
    payload = json.dumps({
        "queries": query,
        "maxPagesPerQuery": 1,
        "resultsPerPage": max_results,
    }).encode()
    req = urllib.request.Request(
        f"{api_url}?token={token}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return []


def apify_rag_browser(query: str, token: str) -> str:
    """Run apify/rag-web-browser for a query and return text. Returns '' on error."""
    api_url = "https://api.apify.com/v2/acts/apify~rag-web-browser/run-sync-get-dataset-items"
    payload = json.dumps({"query": query, "maxResults": 3}).encode()
    req = urllib.request.Request(
        f"{api_url}?token={token}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            items = json.loads(resp.read().decode())
            return " ".join(
                i.get("text", "") or i.get("markdown", "") for i in items
            )
    except Exception:
        return ""


def load_live() -> dict:
    """Load existing countries_live.json or scaffold empty structure."""
    if LIVE_OUT.exists():
        try:
            return json.loads(LIVE_OUT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"updated": NOW, "v": 2, "bookmakers": {}, "countries": {}}


def save_live(data: dict) -> None:
    data["updated"] = NOW
    DATA_DIR.mkdir(exist_ok=True)
    LIVE_OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"  💾  Saved → {LIVE_OUT}")


def merge_scraper_state(live: dict) -> None:
    """Pull current_offer from agents/python/scraper_state.json."""
    if not SCRAPER_STATE.exists():
        return
    try:
        state = json.loads(SCRAPER_STATE.read_text(encoding="utf-8"))
        for name, info in state.items():
            if "current_offer" in info and info["current_offer"]:
                bk = live["bookmakers"].setdefault(name, {})
                bk["top"] = info["current_offer"]
                bk["last_verified"] = info.get("last_success", NOW)
        print(f"  ✓  Merged {len(state)} entries from scraper_state.json")
    except Exception as e:
        print(f"  ✗  scraper_state merge error: {e}")


# ── Static bookmaker counts from shared.js (source of truth until Apify updates) ─
STATIC_COUNTS = {
    "NG": 34, "KE": 51, "GH": 26, "ZA": 58, "TZ": 22, "UG": 21,
    "ZM": 13, "ET": 1,  "CI": 4,  "CM": 8,  "SN": 6,  "RW": 8,
    "ZW": 14, "MW": 10, "MZ": 16, "AO": 9,  "CD": 2,  "BW": 11,
    "NA": 15, "EG": 5,  "MA": 4,  "SL": 3,  "LR": 8,
}


def main() -> None:
    print(f"\n🔄  SifuFinds Live Data Updater")
    print(f"    {NOW}\n")

    FC_DIR.mkdir(exist_ok=True)
    live = load_live()

    apify_token = os.getenv("APIFY_API_TOKEN") or os.getenv("APIFY_TOKEN", "")

    # ── Phase 1 · Firecrawl bookmaker pages ───────────────────────────────────
    print("📡  Phase 1 · Firecrawl bookmaker promo pages")
    for name, url in BOOKMAKER_PAGES:
        slug = re.sub(r"[^\w]", "-", name.lower())
        print(f"    Scraping {name} …", end=" ", flush=True)
        content = fc_scrape(url, slug)
        bk = live["bookmakers"].setdefault(name, {})
        bk["url"] = url
        if content:
            bonus = extract_bonus(content)
            bk["status"] = "live"
            bk["last_verified"] = NOW
            if bonus:
                bk["top"] = bonus
                print(f"✓  ({bonus[:50]})")
            else:
                print("✓  (no bonus extracted)")
        else:
            bk["status"] = "error"
            bk["last_attempt"] = NOW
            print("✗  scrape failed")
        time.sleep(1)  # be polite

    # ── Phase 2 · Merge scraper_state.json (free bonus lookup) ────────────────
    print("\n🔗  Phase 2 · Merge existing scraper_state data")
    merge_scraper_state(live)

    # ── Phase 3 · Apify Google Search (if token available) ────────────────────
    if apify_token:
        print("\n🔍  Phase 3 · Apify Google Search — country keyword intelligence")
        for code, query in APIFY_QUERIES:
            print(f"    [{code}] {query} …", end=" ", flush=True)
            try:
                # Use RAG browser for richer content extraction
                text = apify_rag_browser(query, apify_token)
                if text:
                    country = live["countries"].setdefault(code, {})
                    country["last_verified"] = NOW
                    # Try to extract bonus from SERP content
                    bonus = extract_bonus(text)
                    if bonus:
                        country["serp_top_offer"] = bonus
                    print(f"✓  ({len(text)} chars)")
                else:
                    print("✗  no content")
            except Exception as e:
                print(f"✗  {e}")
            time.sleep(2)
    else:
        print("\n⚠️   Phase 3 · Apify skipped — set APIFY_API_TOKEN to enable")
        print("     Add to .env: APIFY_API_TOKEN=your_token_here")

    # ── Phase 4 · Seed country stats from static counts + live offers ─────────
    print("\n🌍  Phase 4 · Country stats")
    for code, count in STATIC_COUNTS.items():
        c = live["countries"].setdefault(code, {})
        c.setdefault("count", count)  # preserve any Apify-discovered count
        c.setdefault("last_verified", NOW)

    # Map top bookmakers per country with live offers
    COUNTRY_TOP = {
        "NG": "1xBet Nigeria", "KE": "SportPesa Kenya", "GH": "Sportybet Ghana",
        "ZA": "Hollywoodbets", "TZ": "1xBet Nigeria",   "UG": "1xBet Nigeria",
        "ZM": "Paripesa",      "RW": "Betway Kenya",    "ZW": "Betway Nigeria",
        "ET": "Betway Nigeria","CI": "Melbet Nigeria",   "CM": "Melbet Nigeria",
        "SN": "Paripesa",      "MW": "Betway Nigeria",  "MZ": "Hollywoodbets",
        "AO": "Melbet Nigeria","CD": "Melbet Nigeria",   "BW": "Hollywoodbets",
        "NA": "Hollywoodbets", "EG": "1xBet Nigeria",   "MA": "1xBet Nigeria",
        "SL": "Betway Nigeria","LR": "Betway Nigeria",
    }
    for code, bk_name in COUNTRY_TOP.items():
        c = live["countries"].setdefault(code, {})
        c["top_bookmaker"] = bk_name
        top_offer = live["bookmakers"].get(bk_name, {}).get("top", "")
        if top_offer:
            c["top_offer"] = top_offer

    # ── Save ──────────────────────────────────────────────────────────────────
    print()
    save_live(live)

    bk_count = len(live["bookmakers"])
    ct_count = len(live["countries"])
    verified = sum(1 for b in live["bookmakers"].values() if b.get("status") == "live")
    print(f"\n✅  Done — {verified}/{bk_count} bookmakers verified, {ct_count} countries updated\n")


if __name__ == "__main__":
    main()
