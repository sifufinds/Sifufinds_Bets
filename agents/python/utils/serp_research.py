"""
serp_research.py — Automatic SERP + competitor research before every blog post.

Free-first pipeline (no login, no API key, no credits burned):
  - DuckDuckGo search (`ddgs`) for SERP results
  - trafilatura direct-fetch for competitor page content
  - Jina AI Reader (r.jina.ai) as a free fallback for JS-heavy/blocked pages
  - PAA/related-question hints derived from the free search snippets

Firecrawl (search + scrape) and Apify (RAG web browser) are kept only as an
explicit opt-in fallback — set SIFU_ALLOW_PAID_CRAWL=1 to re-enable them when
free sources come back empty. They never fire by default, so a normal blog
run costs zero Firecrawl/Apify credits.

Returns a formatted research block ready to inject into an LLM prompt.
Fails silently so a network issue never blocks content generation.
"""
import os
import re
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
ALLOW_PAID_CRAWL = os.getenv("SIFU_ALLOW_PAID_CRAWL", "").lower() in ("1", "true", "yes")

_FC_BASE = "https://api.firecrawl.dev/v1"
_APIFY_BASE = "https://api.apify.com/v2"
_TIMEOUT = 25  # seconds per request
_JINA_READER = "https://r.jina.ai/"
_MIN_SCRAPE_CHARS = 300  # below this, trafilatura likely hit a JS-only/blocked page
_UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _fc_headers() -> dict:
    return {"Authorization": f"Bearer {FIRECRAWL_API_KEY}", "Content-Type": "application/json"}


def _word_count(text: str) -> int:
    return len(text.split())


def _extract_headings(markdown: str) -> list[str]:
    return [line.strip() for line in markdown.splitlines() if re.match(r"^#{1,3} ", line)][:12]


def _has_table(markdown: str) -> bool:
    return "|" in markdown and "---" in markdown


# ── Free: DuckDuckGo search (no key, no login) — two engines combined ───────
#    1) ddgs library — richer results but has a known intermittent SSL bug on
#       some Python/LibreSSL builds (randomises TLS context, ~40% fail rate
#       on macOS system Python 3.9). Never fatal, just skipped on failure.
#    2) html.duckduckgo.com/html — plain requests + BeautifulSoup, no flaky
#       SSL context juggling, so it's the reliable backbone of the pipeline.

def _ddg_lib_search(query: str, limit: int = 8) -> list[dict]:
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=limit))
        return [
            {
                "url": r.get("href", ""),
                "title": r.get("title", ""),
                "description": r.get("body", ""),
                "markdown": "",
            }
            for r in raw
            if r.get("href")
        ]
    except Exception as e:
        print(f"[serp_research] ddgs library search failed (non-fatal): {e}")
        return []


def _ddg_html_search(query: str, limit: int = 8) -> list[dict]:
    try:
        from bs4 import BeautifulSoup
        from urllib.parse import urlparse, parse_qs, unquote

        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=_UA,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        for body in soup.select(".result__body"):
            a = body.select_one(".result__a")
            snippet_el = body.select_one(".result__snippet")
            if not a or not a.get("href"):
                continue
            href = a["href"]
            qs = parse_qs(urlparse(href).query)
            real_url = unquote(qs["uddg"][0]) if "uddg" in qs else href
            if not real_url or urlparse(real_url).netloc.endswith("duckduckgo.com"):
                continue  # skip sponsored ad-click redirects, keep organic results only
            results.append({
                "url": real_url,
                "title": a.get_text(strip=True),
                "description": snippet_el.get_text(strip=True) if snippet_el else "",
                "markdown": "",
            })
        return results[:limit]
    except Exception as e:
        print(f"[serp_research] DuckDuckGo HTML search failed: {e}")
        return []


def _ddg_search(query: str, limit: int = 8) -> list[dict]:
    """Combined free search: merge ddgs library + DuckDuckGo HTML endpoint,
    deduplicated by URL. Either source failing independently is fine."""
    combined = _ddg_html_search(query, limit) + _ddg_lib_search(query, limit)
    seen = set()
    deduped = []
    for r in combined:
        url = r.get("url", "")
        if url and url not in seen:
            seen.add(url)
            deduped.append(r)
    return deduped[:limit]


# ── Free: trafilatura direct fetch, Jina Reader fallback ────────────────────

def _trafilatura_scrape(url: str) -> str:
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return ""
        return trafilatura.extract(downloaded, include_tables=True, include_links=False) or ""
    except Exception as e:
        print(f"[serp_research] trafilatura failed ({url}): {e}")
        return ""


def _jina_scrape(url: str) -> str:
    """Free reader proxy — no API key/login. Best for JS-rendered or blocked pages."""
    try:
        resp = requests.get(f"{_JINA_READER}{url}", headers=_UA, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[serp_research] Jina Reader failed ({url}): {e}")
        return ""


def _free_scrape(url: str) -> str:
    """Combined free scrape: trafilatura first, Jina Reader fallback if too thin."""
    text = _trafilatura_scrape(url)
    if len(text) >= _MIN_SCRAPE_CHARS:
        return text
    jina_text = _jina_scrape(url)
    return jina_text if len(jina_text) > len(text) else text


# ── Firecrawl: search (paid, opt-in fallback only) ──────────────────────────

def _fc_search(query: str, limit: int = 8) -> list[dict]:
    """Return list of {url, title, description, markdown} from Firecrawl search."""
    if not FIRECRAWL_API_KEY or not ALLOW_PAID_CRAWL:
        return []
    try:
        resp = requests.post(
            f"{_FC_BASE}/search",
            headers=_fc_headers(),
            json={"query": query, "limit": limit, "scrapeOptions": {"formats": ["markdown"]}},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])
    except Exception as e:
        print(f"[serp_research] Firecrawl search failed: {e}")
        return []


# ── Firecrawl: scrape individual URL (paid, opt-in fallback only) ───────────

def _fc_scrape(url: str) -> str:
    """Return markdown content of a URL, empty string on failure."""
    if not FIRECRAWL_API_KEY or not ALLOW_PAID_CRAWL:
        return ""
    try:
        resp = requests.post(
            f"{_FC_BASE}/scrape",
            headers=_fc_headers(),
            json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("data", {}).get("markdown", "")
    except Exception as e:
        print(f"[serp_research] Firecrawl scrape failed ({url}): {e}")
        return ""


# ── Apify: RAG web browser (paid, opt-in fallback only) ─────────────────────

def _apify_rag(query: str, max_results: int = 5) -> list[dict]:
    """Run Apify RAG web browser, return list of {url, title, description, text}."""
    if not APIFY_TOKEN or not ALLOW_PAID_CRAWL:
        return []
    try:
        resp = requests.post(
            f"{_APIFY_BASE}/acts/apify~rag-web-browser/run-sync-get-dataset-items",
            params={"token": APIFY_TOKEN},
            json={"query": query, "maxResults": max_results},
            timeout=90,
        )
        resp.raise_for_status()
        return resp.json() if isinstance(resp.json(), list) else []
    except Exception as e:
        print(f"[serp_research] Apify RAG failed: {e}")
        return []


def _paa_from_snippets(snippets: list[str]) -> list[str]:
    """Derive PAA-style question hints from free search result snippets (no Apify needed)."""
    hints = []
    for desc in snippets:
        questions = [
            s.strip() for s in re.split(r"[.?]", desc)
            if "?" in s or s.strip().lower().startswith(
                ("how", "what", "which", "is ", "are ", "can ", "do ", "does ", "why", "when")
            )
        ]
        hints.extend(questions[:2])
    return hints


# ── Derive keyword from agent1 slot + country ────────────────────────────────

SLOT_KEYWORD_TEMPLATES = {
    "Today's Best Betting Odds":     "best betting odds {country} today",
    "Best Welcome Bonus":            "best betting bonus {country} 2026",
    "Match Prediction":              "{country} football match prediction tips",
    "Casino Jackpot":                "best casino sites {country} 2026",
    "Betting education":             "how to bet online {country} beginners guide",
    "Weekend Accumulator":           "weekend accumulator tips {country}",
    "Best Bookmaker":                "best bookmakers {country} 2026",
    "Live Betting Guide":            "live betting guide {country}",
    "Breaking news":                 "football betting news {country} 2026",
}


def build_keyword(topic: str, country_name: str) -> str:
    """Map a content slot description + country to a concrete search keyword."""
    for fragment, template in SLOT_KEYWORD_TEMPLATES.items():
        if fragment.lower() in topic.lower():
            return template.format(country=country_name)
    return f"betting tips {country_name} 2026"


_CATEGORY_KEYWORDS = {
    "football":     "football betting tips Africa today",
    "sportnews":    "sports betting news Africa 2026",
    "betting":      "accumulator betting tips Africa 2026",
    "igaming":      "best igaming betting sites Africa 2026",
    "basketball":   "NBA basketball betting tips Africa 2026",
    "tennis":       "tennis betting predictions 2026",
    "cricket":      "cricket betting tips Africa 2026",
    "rugby":        "rugby betting predictions 2026",
    "boxing":       "boxing betting odds 2026",
    "f1":           "Formula 1 F1 betting tips 2026",
    "worldcup2026": "World Cup 2026 betting guide Africa",
}


def build_keyword_from_category(category: str) -> str:
    """Map an agent_sports_blog category name to a SERP search keyword."""
    return _CATEGORY_KEYWORDS.get(category, f"{category} betting tips Africa 2026")


# ── Public wrappers (for agents that need raw search/scrape, not the full
#    research() block — e.g. agent_brand_discovery.py's legitimacy checks) ──
#    Free-first: DuckDuckGo + trafilatura/Jina try first; Firecrawl only fires
#    if free sources come back empty AND SIFU_ALLOW_PAID_CRAWL=1 is set.

def fc_search(query: str, limit: int = 8) -> list[dict]:
    """Free-first search. Falls back to Firecrawl only if free search is empty
    and paid crawl is explicitly allowed. See _ddg_search for return shape."""
    results = _ddg_search(query, limit)
    if results:
        return results
    return _fc_search(query, limit)


def fc_scrape(url: str) -> str:
    """Free-first scrape (trafilatura + Jina Reader). Falls back to Firecrawl
    only if free scrape is empty and paid crawl is explicitly allowed."""
    text = _free_scrape(url)
    if text:
        return text
    return _fc_scrape(url)


# ── Main entry point ─────────────────────────────────────────────────────────

def research(keyword: str, country_name: str = "") -> str:
    """
    Run full SERP + competitor research for a keyword using free sources
    (DuckDuckGo search + trafilatura/Jina Reader scrape) combined together.
    Firecrawl/Apify only engage as an opt-in fallback (SIFU_ALLOW_PAID_CRAWL=1)
    when the free pipeline comes back empty, so a normal run costs zero credits.
    Returns a formatted string block to inject into the agent1 LLM prompt.
    Returns empty string if no source produced any data.
    """
    print(f"[serp_research] Researching: '{keyword}' (free pipeline: DuckDuckGo + trafilatura/Jina)")

    # --- Phase 1: free SERP search (DuckDuckGo), Firecrawl only if that's empty ---
    search_results = _ddg_search(keyword, limit=8)
    used_paid_search = False
    if not search_results:
        search_results = _fc_search(keyword, limit=8)
        used_paid_search = bool(search_results)

    top_urls = []
    serp_titles = []
    inline_content = []  # results that already came with markdown from search
    snippets = []

    for r in search_results:
        url = r.get("url", "")
        title = r.get("title", "")
        description = r.get("description", "")
        md = r.get("markdown", "") or r.get("content", "")

        if url:
            top_urls.append(url)
        if title:
            serp_titles.append(f"• {title} ({url})")
        if description:
            snippets.append(description)
        if md:
            inline_content.append((url, md))

    # --- Phase 2: scrape top 3 competitor pages (free: trafilatura + Jina) ---
    scraped = []
    scrape_targets = top_urls[:3] if len(inline_content) < 2 else []
    for url in scrape_targets:
        md = _free_scrape(url) or (_fc_scrape(url) if not used_paid_search else "")
        if md:
            scraped.append((url, md))

    all_content = inline_content + scraped

    # Analyse competitor signals
    word_counts = []
    all_headings = []
    table_count = 0
    for url, md in all_content[:5]:
        wc = _word_count(md)
        if wc > 100:
            word_counts.append(wc)
        headings = _extract_headings(md)
        all_headings.extend(headings)
        if _has_table(md):
            table_count += 1

    avg_wc = int(sum(word_counts) / len(word_counts)) if word_counts else 900
    target_wc = int(avg_wc * 1.25)

    # Deduplicate headings
    seen = set()
    unique_headings = []
    for h in all_headings:
        key = re.sub(r"^#+\s*", "", h).lower()
        if key not in seen:
            seen.add(key)
            unique_headings.append(h)

    # --- Phase 3: PAA hints derived from free search snippets (no Apify needed) ---
    paa_hints = _paa_from_snippets(snippets)
    if not paa_hints:
        # Apify only fires if explicitly allowed and free snippets gave nothing
        apify_results = _apify_rag(keyword, max_results=4)
        for item in apify_results:
            desc = item.get("description", "") or item.get("text", "")[:300]
            paa_hints.extend(_paa_from_snippets([desc]))

    # --- Build research block ---
    if not search_results:
        print("[serp_research] No data from any source — skipping research injection")
        return ""

    lines = [
        "=" * 60,
        f"SERP RESEARCH: \"{keyword}\"",
        "=" * 60,
        "",
    ]

    if serp_titles:
        lines.append("TOP RANKING PAGES (beat all of these):")
        lines.extend(serp_titles[:8])
        lines.append("")

    if word_counts:
        lines.append(f"COMPETITOR CONTENT SIGNALS:")
        lines.append(f"  • Avg word count of top pages: ~{avg_wc} words")
        lines.append(f"  • YOUR TARGET: >{target_wc} words minimum")
        lines.append(f"  • Pages with tables: {table_count}/{len(all_content[:5])}")
        lines.append("")

    if unique_headings:
        lines.append("COMMON H2/H3 HEADINGS IN TOP PAGES (use or improve on these):")
        for h in unique_headings[:10]:
            lines.append(f"  {h}")
        lines.append("")

    paa_clean = list(dict.fromkeys(q.strip() for q in paa_hints if len(q.strip()) > 15))[:5]
    if paa_clean:
        lines.append("PEOPLE ALSO ASK / FAQ TARGETS (answer all of these):")
        for i, q in enumerate(paa_clean, 1):
            lines.append(f"  {i}. {q}?")
        lines.append("")

    lines += [
        "INSTRUCTIONS FROM RESEARCH:",
        f"  1. Write >{target_wc} words (top pages average {avg_wc})",
        "  2. Mirror or improve the H2 structure above",
        "  3. Include at least one odds/comparison table",
        "  4. Add an FAQ section answering the PAA questions",
        "  5. 3–5 internal links to sifufinds.com pages",
        "=" * 60,
        "",
    ]

    return "\n".join(lines)
