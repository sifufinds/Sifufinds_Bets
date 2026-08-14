"""
free_scrape.py — Shared free-first scrape helper for the live-data agents
(agent_multi_scrape.py, agent_scrape_tips.py, agent_firecrawl_odds.py) that
feed sifufinds.com/tips/, /odds/, and /leagues/.

Priority order:
  1. trafilatura direct fetch (free, no key, no login)
  2. Jina AI Reader r.jina.ai (free, no key, renders JS — covers most SPA
     sites like Sofascore/Flashscore/OddsPortal/Predictz)
  3. Firecrawl REST API — genuine last resort, only fires when both free
     layers return too little content AND FIRECRAWL_API_KEY is set.

This fallback is intentionally NOT gated behind SIFU_ALLOW_PAID_CRAWL the
way utils/serp_research.py gates blog research (that pipeline guarantees
zero Firecrawl cost per run by design). These three agents feed live
odds/tips/scores data that must stay fresh, and two of them run on a
15-minute cron — a hard opt-in flag would mean Firecrawl effectively never
fires even when free sources genuinely fail, silently degrading live data.
Free sources still handle the large majority of calls (trafilatura + Jina
cover most public sports pages), so real Firecrawl usage drops drastically
compared to the old Firecrawl-only implementation without disappearing
entirely when it's genuinely needed.

Standing policy (added 2026-08-09): Firecrawl usage sitewide is scoped
exclusively to the tips/odds/leagues pipelines above. Any OTHER caller of
scrape() — e.g. update_countries.py, which feeds countries_live.json for
the homepage, all country pages, and other non-tips/odds/leagues
surfaces — MUST pass allow_firecrawl=False so this module still gives it
trafilatura + Jina Reader but never falls through to Firecrawl.
"""
import os

import requests

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
_FC_SCRAPE_URL = "https://api.firecrawl.dev/v1/scrape"
_JINA_READER = "https://r.jina.ai/"
_MIN_CHARS = 300
_TIMEOUT = 25
_UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _trafilatura_scrape(url: str) -> str:
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return ""
        return trafilatura.extract(downloaded, include_tables=True, include_links=True) or ""
    except Exception as e:
        print(f"    trafilatura failed [{url}]: {e}")
        return ""


def _jina_scrape(url: str) -> str:
    try:
        resp = requests.get(f"{_JINA_READER}{url}", headers=_UA, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"    Jina Reader failed [{url}]: {e}")
        return ""


def _firecrawl_scrape(url: str, wait_ms: int = 4000) -> str:
    if not FIRECRAWL_API_KEY or len(FIRECRAWL_API_KEY) < 20:
        return ""
    try:
        resp = requests.post(
            _FC_SCRAPE_URL,
            headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}", "Content-Type": "application/json"},
            json={"url": url, "formats": ["markdown"], "waitFor": wait_ms, "onlyMainContent": True},
            timeout=90,
        )
        if resp.ok:
            data = resp.json()
            return (data.get("data") or data).get("markdown", "")
        print(f"    Firecrawl HTTP {resp.status_code} [{url}]: {resp.text[:120]}")
    except Exception as e:
        print(f"    Firecrawl failed [{url}]: {e}")
    return ""


def scrape(
    url: str,
    name: str = "",
    wait_ms: int = 4000,
    min_chars: int = _MIN_CHARS,
    allow_firecrawl: bool = True,
) -> str:
    """Free-first scrape: trafilatura -> Jina Reader -> Firecrawl (last resort).

    Both free layers are always tried and the larger result is kept — a
    static trafilatura fetch of a JS-heavy SPA (Flashscore, Sofascore, ...)
    can return a few hundred characters of cookie/legal boilerplate that
    would otherwise clear a naive length gate while missing the actual
    rendered content Jina Reader provides, so we never skip Jina based on
    trafilatura alone clearing min_chars.

    allow_firecrawl must be explicitly False for any caller that isn't one
    of the tips/odds/leagues pipelines (see module docstring) — the free
    layers still run either way.

    Returns markdown/text content, or the empty string if every layer fails.
    """
    label = name or url

    text = _trafilatura_scrape(url)
    jina_text = _jina_scrape(url)
    best_free = jina_text if len(jina_text) > len(text) else text

    if len(best_free) >= min_chars:
        source = "Jina Reader" if best_free is jina_text else "trafilatura"
        print(f"    {source} [{label}]: {len(best_free)} chars")
        return best_free

    if not allow_firecrawl:
        return best_free

    fc_text = _firecrawl_scrape(url, wait_ms)
    if len(fc_text) > len(best_free):
        print(f"    Firecrawl fallback [{label}]: {len(fc_text)} chars")
        return fc_text

    return best_free
