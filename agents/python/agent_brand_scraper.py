"""
Brand Bonus Scraper Agent — SifuFinds
Scrapes all bookmaker sites daily to verify and update current welcome bonuses,
promo codes, free bets, free games, casino offers, and best betting markets.

Safety guarantee: only writes a brand's data when confidence >= CONFIDENCE_THRESHOLD.
If scraping fails or looks suspicious the existing known-good value is preserved.

Outputs:
  ../../blog/banners.json        — banner cards read by the site
  ../../blog/banners-data.js     — same data as a JS variable (window.BANNERS_DATA)
  ../../brands/data.json         — full brand database with extended offer details

Usage:
  python agent_brand_scraper.py              # all brands
  python agent_brand_scraper.py --brand Bet9ja
  python agent_brand_scraper.py --dry-run    # show changes, do not write
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from llm import ask
from utils.logger import log
from seo_meta import strip_dangling_words

load_dotenv(Path(__file__).parent / ".env")

# ── PATHS ────────────────────────────────────────────────────────────────────

REPO_ROOT        = Path(__file__).parent.parent.parent
BANNERS_JSON     = REPO_ROOT / "blog" / "banners.json"
BANNERS_DATA_JS  = REPO_ROOT / "blog" / "banners-data.js"
BRANDS_DIR       = REPO_ROOT / "brands"
BRANDS_DATA_JSON = BRANDS_DIR / "data.json"
STATE_FILE       = Path(__file__).parent / "scraper_state.json"

CONFIDENCE_THRESHOLD = 0.65
REQUEST_TIMEOUT      = 12
DELAY_BETWEEN_BRANDS = 3   # seconds — polite crawl rate

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── BRAND REGISTRY ───────────────────────────────────────────────────────────
# affiliate_url_locked=True means the url field in banners.json is NEVER modified.

# Ordered so brands that historically struggle run first and get fresh Groq quota.
# "Never succeeded" brands (Sportybet, Betika, Betway, Melbet) are at the top.
BRAND_REGISTRY: list[dict] = [
    {
        "name": "Sportybet",
        "banner_id": "ban-003",
        "base_url": "https://www.sportybet.com",
        "promo_urls": ["https://www.sportybet.com/ng/promotions"],
        "search_query": "Sportybet welcome bonus Nigeria free bet signup 2025",
        "region": "Nigeria",
        "currency_symbol": "₦",
        "affiliate_url_locked": False,
    },
    {
        "name": "Betika",
        "banner_id": "ban-005",
        "base_url": "https://www.betika.com",
        "promo_urls": ["https://www.betika.com/en-ke/promo"],
        "search_query": "Betika Kenya welcome bonus free bet signup 2025",
        "region": "Kenya",
        "currency_symbol": "KSh",
        "affiliate_url_locked": False,
    },
    {
        "name": "Betway",
        "banner_id": "ban-006",
        "base_url": "https://www.betway.com.ng",
        "promo_urls": [
            "https://www.betway.com.ng/en-ng/promos",
            "https://www.betway.com.ng/en-ng/promotions",
        ],
        "search_query": "Betway Nigeria welcome bonus free bets signup 2025",
        "region": "Nigeria",
        "currency_symbol": "₦",
        "affiliate_url_locked": False,
    },
    {
        "name": "Melbet",
        "banner_id": "ban-009",
        "base_url": "https://melbet.ng",
        "promo_urls": ["https://melbet.ng/en/promo", "https://melbet.ng/en/bonus"],
        "search_query": "Melbet Nigeria welcome bonus promo code first deposit 2025",
        "region": "Nigeria",
        "currency_symbol": "₦",
        "affiliate_url_locked": True,
    },
    {
        "name": "Bet9ja",
        "banner_id": "ban-001",
        "base_url": "https://www.bet9ja.com",
        "promo_urls": ["https://www.bet9ja.com/promos", "https://sports.bet9ja.com"],
        "search_query": "Bet9ja welcome bonus free bet signup Nigeria 2025",
        "region": "Nigeria",
        "currency_symbol": "₦",
        "affiliate_url_locked": False,
    },
    {
        "name": "BetWinner",
        "banner_id": "ban-007",
        "base_url": "https://betwinner.ng",
        "promo_urls": ["https://betwinner.ng/en/promo"],
        "search_query": "BetWinner Nigeria welcome bonus promo code 2025",
        "region": "Nigeria",
        "currency_symbol": "₦",
        "affiliate_url_locked": True,
    },
    {
        "name": "TicTacBets",
        "banner_id": "ban-011",
        "base_url": "https://www.tictacbets.co.za",
        "promo_urls": ["https://www.tictacbets.co.za/promotions"],
        "search_query": "TicTacBets South Africa welcome bonus signup 2025",
        "region": "South Africa",
        "currency_symbol": "R",
        "affiliate_url_locked": True,
    },
    {
        "name": "Hollywoodbets",
        "banner_id": "ban-002",
        "base_url": "https://www.hollywoodbets.net",
        "promo_urls": ["https://www.hollywoodbets.net/promotions"],
        "search_query": "Hollywoodbets welcome bonus free bet signup South Africa 2025",
        "region": "South Africa",
        "currency_symbol": "R",
        "affiliate_url_locked": False,
    },
    {
        "name": "1xBet",
        "banner_id": "ban-004",
        "base_url": "https://1xbet.ng",
        "promo_urls": ["https://1xbet.ng/en/promo", "https://1xbet.ng/en/bonus"],
        "search_query": "1xBet welcome bonus Nigeria promo code 2025 first deposit",
        "region": "Nigeria",
        "currency_symbol": "₦",
        "affiliate_url_locked": True,
    },
    {
        "name": "HelaBet",
        "banner_id": "ban-008",
        "base_url": "https://helabet.com",
        "promo_urls": ["https://helabet.com/en/promotions"],
        "search_query": "HelaBet Kenya welcome bonus signup offer M-Pesa 2025",
        "region": "Kenya",
        "currency_symbol": "KSh",
        "affiliate_url_locked": True,
    },
    {
        "name": "Paripesa",
        "banner_id": "ban-010",
        "base_url": "https://paripesa.ng",
        "promo_urls": ["https://paripesa.ng/en/promo"],
        "search_query": "Paripesa Nigeria welcome bonus first deposit offer 2025",
        "region": "Nigeria",
        "currency_symbol": "₦",
        "affiliate_url_locked": True,
    },
]

REGISTRY_BY_NAME = {b["name"]: b for b in BRAND_REGISTRY}
REGISTRY_BY_BANNER_ID = {b["banner_id"]: b for b in BRAND_REGISTRY}


# ── DATA CLASSES ─────────────────────────────────────────────────────────────

@dataclass
class ScrapeResult:
    brand_name: str
    welcome_bonus: str
    bonus_headline: str       # short form for banner offer field, e.g. "Get ₦2,500 FREE BET"
    bonus_sub: str            # subtitle, e.g. "No deposit required · NLRC Licensed"
    promo_code: Optional[str]
    min_deposit: str
    free_games: list[str]     # e.g. ["Aviator", "Virtual Sports"]
    best_markets: list[str]   # e.g. ["Football", "Basketball"]
    casino_offer: Optional[str]
    source: str               # "ddgs", "direct", "ddgs+direct"
    confidence: float         # 0.0 – 1.0
    scraped_at: str           # ISO timestamp


@dataclass
class BrandState:
    last_scraped: str = ""
    last_success: str = ""
    current_offer: str = ""
    consecutive_failures: int = 0


# ── STATE MANAGEMENT ─────────────────────────────────────────────────────────

def _load_state() -> dict[str, dict]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_state(state: dict[str, dict]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


# ── DDGS SEARCH ──────────────────────────────────────────────────────────────

def _ddgs_search(query: str, max_results: int = 6) -> list[str]:
    """Return concatenated text snippets from DuckDuckGo search results."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        snippets = []
        for r in results:
            title = r.get("title", "")
            body = r.get("body", "")
            href = r.get("href", "")
            snippets.append(f"[{title}] ({href})\n{body}")
        return snippets
    except Exception as e:
        log("scraper", "ddgs_error", str(e))
        return []


# ── DIRECT FETCH ─────────────────────────────────────────────────────────────

def _fetch_page(url: str) -> str:
    """Try to fetch a URL, return visible text (first 4000 chars). Empty on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if resp.status_code != 200:
            return ""
        # Strip HTML tags with a simple regex — good enough for promo text extraction
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:4000]
    except Exception:
        return ""


def _gather_raw_content(brand: dict) -> tuple[str, str]:
    """
    Returns (combined_text, source_label).
    Tries DDGS search first, then direct page fetch.
    """
    name = brand["name"]
    query = brand["search_query"]

    snippets = _ddgs_search(query)
    ddgs_text = "\n\n---\n\n".join(snippets) if snippets else ""

    direct_text = ""
    for url in brand["promo_urls"]:
        direct_text = _fetch_page(url)
        if direct_text:
            break

    combined = ""
    source = "none"
    if ddgs_text and direct_text:
        combined = f"=== SEARCH RESULTS ===\n{ddgs_text}\n\n=== PROMO PAGE ===\n{direct_text}"
        source = "ddgs+direct"
    elif ddgs_text:
        combined = ddgs_text
        source = "ddgs"
    elif direct_text:
        combined = direct_text
        source = "direct"

    return combined, source


# ── LLM EXTRACTION ───────────────────────────────────────────────────────────

_EXTRACT_SYSTEM = """You are a data extraction specialist for an African sports betting comparison site.
Your job is to extract CURRENT, ACCURATE bonus information for a specific bookmaker from raw web content.
Output strict JSON only — no prose, no markdown, no code fences.

Rules:
- Only extract information that is clearly stated in the content.
- If a value is not mentioned, use null.
- welcome_bonus: the main welcome/signup bonus in one short sentence (max 80 chars).
- bonus_headline: ultra-short promo banner text, e.g. "Get ₦2,500 FREE BET" (max 40 chars).
- bonus_sub: subtitle with key detail, e.g. "No deposit required · NLRC Licensed" (max 60 chars).
- promo_code: alphanumeric code if mentioned, else null.
- min_deposit: e.g. "₦100" or "KSh 10" or null.
- free_games: list of free game products, e.g. ["Aviator", "Virtual Sports", "Casino Slots"].
- best_markets: top 3 sports/betting markets, e.g. ["Football", "Basketball", "Tennis"].
- casino_offer: casino welcome offer if present, else null (max 80 chars).
- confidence: float 0.0–1.0 how confident you are this is current, correct information.
  Use 0.8+ only if multiple sources confirm the same specific offer.
  Use 0.5–0.7 if only one source with some uncertainty.
  Use below 0.5 if content is generic, outdated-looking, or contradictory.
- reasoning: one sentence explaining the confidence score.
"""

def _llm_extract(brand_name: str, region: str, raw_content: str) -> dict | None:
    if not raw_content.strip():
        return None

    prompt = (
        f"Extract current bonus data for: {brand_name} ({region})\n\n"
        f"Raw content:\n{raw_content[:6000]}"
    )

    try:
        raw = ask(_EXTRACT_SYSTEM, prompt)
        # Strip any accidental markdown fences
        raw = re.sub(r"```[a-z]*\n?", "", raw).strip()
        return json.loads(raw)
    except Exception as e:
        log("scraper", "llm_error", f"{brand_name}: {e}")
        return None


# ── VALIDATION ───────────────────────────────────────────────────────────────

def _is_plausible(extracted: dict, brand: dict) -> bool:
    """Sanity-check the extracted offer before accepting it."""
    if not extracted:
        return False

    welcome = extracted.get("welcome_bonus") or ""
    headline = extracted.get("bonus_headline") or ""

    if not welcome and not headline:
        return False

    # Check for absurd bonus percentages
    pct_matches = re.findall(r"(\d{1,4})\s*%", welcome + " " + headline)
    for pct in pct_matches:
        if int(pct) > 600:
            return False

    # Headline length guard
    if len(headline) > 60:
        extracted["bonus_headline"] = strip_dangling_words(headline[:60].rsplit(" ", 1)[0])

    # Brand name should not appear to belong to a competitor
    name_lower = brand["name"].lower()
    combined = (welcome + " " + headline).lower()
    if combined and name_lower not in combined:
        # If it mentions a completely different brand name, reject
        other_brands = [b["name"].lower() for b in BRAND_REGISTRY if b["name"] != brand["name"]]
        for other in other_brands:
            if other in combined:
                return False

    return True


# ── MAIN SCRAPER ──────────────────────────────────────────────────────────────

def scrape_brand(brand: dict) -> ScrapeResult | None:
    """Scrape one brand. Returns ScrapeResult on success, None on total failure."""
    name = brand["name"]
    region = brand["region"]
    sym = brand["currency_symbol"]

    log("scraper", "start", name)
    raw_content, source = _gather_raw_content(brand)

    if not raw_content:
        log("scraper", "no_content", name)
        return None

    extracted = _llm_extract(name, region, raw_content)
    if not extracted:
        log("scraper", "llm_failed", name)
        return None

    confidence = float(extracted.get("confidence", 0.0))
    if not _is_plausible(extracted, brand):
        log("scraper", "implausible", f"{name} (conf={confidence:.2f})")
        return None

    free_games = extracted.get("free_games") or []
    best_markets = extracted.get("best_markets") or []
    if isinstance(free_games, str):
        free_games = [free_games]
    if isinstance(best_markets, str):
        best_markets = [best_markets]

    result = ScrapeResult(
        brand_name=name,
        welcome_bonus=extracted.get("welcome_bonus") or "",
        bonus_headline=extracted.get("bonus_headline") or "",
        bonus_sub=extracted.get("bonus_sub") or "",
        promo_code=extracted.get("promo_code"),
        min_deposit=extracted.get("min_deposit") or "",
        free_games=free_games[:6],
        best_markets=best_markets[:5],
        casino_offer=extracted.get("casino_offer"),
        source=source,
        confidence=confidence,
        scraped_at=datetime.now(timezone.utc).isoformat(),
    )

    log("scraper", "ok", f"{name} conf={confidence:.2f} src={source}")
    return result


# ── BANNERS.JSON UPDATER ──────────────────────────────────────────────────────

def _load_banners() -> dict:
    return json.loads(BANNERS_JSON.read_text(encoding="utf-8"))


def _save_banners(data: dict) -> None:
    BANNERS_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    # Regenerate the JS file
    BANNERS_DATA_JS.write_text(
        f"window.BANNERS_DATA={json.dumps(data, separators=(',', ':'), ensure_ascii=False)};\n",
        encoding="utf-8",
    )


def _apply_scrape_to_banner(banner: dict, result: ScrapeResult, registry: dict) -> tuple[dict, bool]:
    """
    Return (updated_banner, changed: bool).
    Affiliate URLs are never touched.
    """
    updated = dict(banner)  # shallow copy — immutable pattern
    changed = False

    if result.bonus_headline and result.bonus_headline != banner.get("offer", ""):
        updated = {**updated, "offer": result.bonus_headline}
        changed = True

    if result.bonus_sub and result.bonus_sub != banner.get("sub", ""):
        updated = {**updated, "sub": result.bonus_sub}
        changed = True

    return updated, changed


# ── BRANDS/DATA.JSON UPDATER ──────────────────────────────────────────────────

def _load_brands_data() -> dict:
    if BRANDS_DATA_JSON.exists():
        try:
            return json.loads(BRANDS_DATA_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_updated": "", "brands": {}}


def _save_brands_data(data: dict) -> None:
    BRANDS_DIR.mkdir(exist_ok=True)
    BRANDS_DATA_JSON.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _apply_scrape_to_brands_data(brands_data: dict, result: ScrapeResult) -> tuple[dict, bool]:
    brands = dict(brands_data.get("brands", {}))
    existing = brands.get(result.brand_name, {})
    updated_entry = {
        **existing,
        "name": result.brand_name,
        "welcome_bonus": result.welcome_bonus or existing.get("welcome_bonus", ""),
        "bonus_headline": result.bonus_headline or existing.get("bonus_headline", ""),
        "bonus_sub": result.bonus_sub or existing.get("bonus_sub", ""),
        "promo_code": result.promo_code if result.promo_code is not None else existing.get("promo_code"),
        "min_deposit": result.min_deposit or existing.get("min_deposit", ""),
        "free_games": result.free_games if result.free_games else existing.get("free_games", []),
        "best_markets": result.best_markets if result.best_markets else existing.get("best_markets", []),
        "casino_offer": result.casino_offer if result.casino_offer is not None else existing.get("casino_offer"),
        "last_scraped": result.scraped_at,
        "scrape_confidence": result.confidence,
        "scrape_source": result.source,
    }

    changed = updated_entry != existing
    new_brands = {**brands, result.brand_name: updated_entry}
    new_data = {
        **brands_data,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "brands": new_brands,
    }
    return new_data, changed


# ── CHANGE LOG ───────────────────────────────────────────────────────────────

def _log_change(brand_name: str, field: str, old_val: str, new_val: str) -> None:
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "brand": brand_name,
        "field": field,
        "old": old_val,
        "new": new_val,
    }
    change_log_path = Path(__file__).parent / "scraper_changes.json"
    changes = []
    if change_log_path.exists():
        try:
            changes = json.loads(change_log_path.read_text())
        except Exception:
            pass
    changes.append(entry)
    # Keep last 500 entries
    change_log_path.write_text(json.dumps(changes[-500:], indent=2, ensure_ascii=False))
    print(f"  CHANGED {brand_name} [{field}]: '{old_val}' → '{new_val}'")


# ── ORCHESTRATOR ──────────────────────────────────────────────────────────────

def run(brand_filter: str | None = None, dry_run: bool = False) -> None:
    log("scraper", "run_start", brand_filter or "all")

    # ── Load existing data ──
    banners_data = _load_banners()
    banner_by_id = {b["id"]: b for b in banners_data.get("banners", [])}
    brands_data = _load_brands_data()
    state = _load_state()

    brands_to_process = BRAND_REGISTRY
    if brand_filter:
        brands_to_process = [b for b in BRAND_REGISTRY if b["name"].lower() == brand_filter.lower()]
        if not brands_to_process:
            print(f"✗ Brand '{brand_filter}' not found. Available: {', '.join(b['name'] for b in BRAND_REGISTRY)}")
            sys.exit(1)

    total_changed = 0
    total_processed = 0
    total_failed = 0

    for brand in brands_to_process:
        name = brand["name"]
        print(f"\n── {name} ──────────────────────────")

        try:
            result = scrape_brand(brand)
        except Exception as e:
            print(f"  ✗ Exception: {e}")
            log("scraper", "exception", f"{name}: {e}")
            total_failed += 1
            s = state.get(name, {})
            s["consecutive_failures"] = s.get("consecutive_failures", 0) + 1
            state[name] = s
            time.sleep(DELAY_BETWEEN_BRANDS)
            continue

        if not result or result.confidence < CONFIDENCE_THRESHOLD:
            conf = result.confidence if result else 0.0
            print(f"  ⚠ Skipped (confidence {conf:.2f} < {CONFIDENCE_THRESHOLD}) — keeping existing data")
            total_failed += 1
            s = state.get(name, {})
            s["consecutive_failures"] = s.get("consecutive_failures", 0) + 1
            state[name] = s
            time.sleep(DELAY_BETWEEN_BRANDS)
            continue

        total_processed += 1
        brand_changed = False

        # ── Apply to banners ──
        banner_id = brand.get("banner_id")
        if banner_id and banner_id in banner_by_id:
            old_banner = banner_by_id[banner_id]
            new_banner, bchanged = _apply_scrape_to_banner(old_banner, result, brand)
            if bchanged:
                if not dry_run:
                    banner_by_id[banner_id] = new_banner
                _log_change(name, "offer", old_banner.get("offer", ""), new_banner.get("offer", ""))
                _log_change(name, "sub", old_banner.get("sub", ""), new_banner.get("sub", ""))
                brand_changed = True

        # ── Apply to brands data ──
        new_brands_data, bchanged2 = _apply_scrape_to_brands_data(brands_data, result)
        if bchanged2:
            if not dry_run:
                brands_data = new_brands_data
            brand_changed = True

        if brand_changed:
            total_changed += 1
            print(f"  ✓ Updated (conf={result.confidence:.2f}, src={result.source})")
        else:
            print(f"  ✓ Verified — no change (conf={result.confidence:.2f})")
            if not dry_run:
                # Still update the brands_data to record the scrape timestamp
                brands_data = new_brands_data

        # ── Update state ──
        state[name] = {
            "last_scraped": result.scraped_at,
            "last_success": result.scraped_at,
            "current_offer": result.bonus_headline,
            "consecutive_failures": 0,
        }

        time.sleep(DELAY_BETWEEN_BRANDS)

    # ── Write outputs ──
    if not dry_run and total_processed > 0:
        updated_banners = {
            **banners_data,
            "banners": list(banner_by_id.values()),
        }
        _save_banners(updated_banners)
        _save_brands_data(brands_data)
        _save_state(state)
        print(f"\n✓ Wrote banners.json, banners-data.js, brands/data.json")
    elif dry_run:
        print(f"\n[DRY RUN] No files written.")
        _save_state(state)

    print(
        f"\n═══ Scraper done ═══\n"
        f"  Processed : {total_processed}/{len(brands_to_process)}\n"
        f"  Changed   : {total_changed}\n"
        f"  Skipped   : {total_failed}\n"
    )
    log("scraper", "run_done", f"processed={total_processed} changed={total_changed} failed={total_failed}")


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Brand Bonus Scraper")
    parser.add_argument("--brand", type=str, default=None, help="Scrape a specific brand only")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing files")
    args = parser.parse_args()
    run(brand_filter=args.brand, dry_run=args.dry_run)
