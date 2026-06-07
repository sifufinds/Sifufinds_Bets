"""
serp_research.py — Automatic SERP + competitor research before every blog post.

Uses Firecrawl (search + scrape) and Apify (RAG web browser) to gather:
  - Top 10 ranking URLs for the keyword
  - Competitor content signals (word count, headings, tables)
  - People Also Ask / related questions

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

_FC_BASE = "https://api.firecrawl.dev/v1"
_APIFY_BASE = "https://api.apify.com/v2"
_TIMEOUT = 25  # seconds per request


# ── Helpers ──────────────────────────────────────────────────────────────────

def _fc_headers() -> dict:
    return {"Authorization": f"Bearer {FIRECRAWL_API_KEY}", "Content-Type": "application/json"}


def _word_count(text: str) -> int:
    return len(text.split())


def _extract_headings(markdown: str) -> list[str]:
    return [line.strip() for line in markdown.splitlines() if re.match(r"^#{1,3} ", line)][:12]


def _has_table(markdown: str) -> bool:
    return "|" in markdown and "---" in markdown


# ── Firecrawl: search ────────────────────────────────────────────────────────

def _fc_search(query: str, limit: int = 8) -> list[dict]:
    """Return list of {url, title, description, markdown} from Firecrawl search."""
    if not FIRECRAWL_API_KEY:
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


# ── Firecrawl: scrape individual URL ────────────────────────────────────────

def _fc_scrape(url: str) -> str:
    """Return markdown content of a URL, empty string on failure."""
    if not FIRECRAWL_API_KEY:
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


# ── Apify: RAG web browser for PAA + related questions ──────────────────────

def _apify_rag(query: str, max_results: int = 5) -> list[dict]:
    """Run Apify RAG web browser, return list of {url, title, description, text}."""
    if not APIFY_TOKEN:
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


# ── Main entry point ─────────────────────────────────────────────────────────

def research(keyword: str, country_name: str = "") -> str:
    """
    Run full SERP + competitor research for a keyword.
    Returns a formatted string block to inject into the agent1 LLM prompt.
    Returns empty string if both APIs are unavailable.
    """
    print(f"[serp_research] Researching: '{keyword}'")

    # --- Phase 1: Firecrawl SERP search ---
    search_results = _fc_search(keyword, limit=8)

    top_urls = []
    serp_titles = []
    inline_content = []  # results that already came with markdown from search

    for r in search_results:
        url = r.get("url", "")
        title = r.get("title", "")
        description = r.get("description", "")
        md = r.get("markdown", "") or r.get("content", "")

        if url:
            top_urls.append(url)
        if title:
            serp_titles.append(f"• {title} ({url})")
        if md:
            inline_content.append((url, md))

    # --- Phase 2: Scrape top 3 competitor pages (if search didn't return content) ---
    scraped = []
    scrape_targets = top_urls[:3] if len(inline_content) < 2 else []
    for url in scrape_targets:
        md = _fc_scrape(url)
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

    # --- Phase 3: Apify for additional context + PAA ---
    apify_results = _apify_rag(keyword, max_results=4)
    paa_hints = []
    apify_urls = []
    for item in apify_results:
        if item.get("url"):
            apify_urls.append(item["url"])
        # Extract question-like sentences from description
        desc = item.get("description", "") or item.get("text", "")[:300]
        questions = [s.strip() for s in re.split(r"[.?]", desc) if "?" in s or s.strip().lower().startswith(("how", "what", "which", "is ", "are ", "can ", "do ", "does "))]
        paa_hints.extend(questions[:2])

    # --- Build research block ---
    if not search_results and not apify_results:
        print("[serp_research] No data from either API — skipping research injection")
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
