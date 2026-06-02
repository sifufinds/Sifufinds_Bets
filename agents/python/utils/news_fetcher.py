"""
Live news research module — three-layer search for maximum freshness.

Layer 1 — DuckDuckGo News Search (live web, last 24h, no API key)
Layer 2 — Google News RSS search (Google's index, per keyword, no API key)
Layer 3 — Site RSS feeds (BBC, ESPN, Guardian, Sky — reliable fallback)

Freshness rules:
  - Items with no parseable pubDate are DISCARDED (never faked as "now")
  - Each category has a MAX_AGE_HOURS window; stale items are filtered out
  - If < MIN_FRESH_ITEMS pass the filter the agent skips generation
"""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import TypedDict, Optional
import re

# ── FRESHNESS CONFIG ──────────────────────────────────────────────────────────
MAX_AGE_HOURS: dict[str, int] = {
    "football":   48,
    "sportnews":  48,
    "basketball": 48,
    "betting":    72,
    "tennis":     72,
    "cricket":    72,
    "rugby":      72,
    "boxing":     168,
    "f1":         168,
    "igaming":    168,
}
DEFAULT_MAX_AGE_HOURS = 72
MIN_FRESH_ITEMS = 3


class NewsItem(TypedDict):
    title: str
    description: str
    url: str
    source: str
    category: str
    published_at: str
    age_hours: float


# ── SEARCH QUERIES ────────────────────────────────────────────────────────────
# Per-category queries used for both DuckDuckGo and Google News RSS
SEARCH_QUERIES: dict[str, list[str]] = {
    "football":   [
        "premier league football news today",
        "champions league europa league news",
        "african football transfer news today",
    ],
    "sportnews":  [
        "trending sports news today",
        "world sport breaking news",
        "sports transfer signing news today",
    ],
    "basketball": [
        "NBA basketball news today",
        "basketball africa league BAL news",
    ],
    "tennis":     [
        "tennis ATP WTA news today",
        "grand slam tennis tournament news",
    ],
    "cricket":    [
        "cricket test match ODI news today",
        "IPL cricket news today",
    ],
    "rugby":      [
        "rugby union news today",
        "springboks six nations rugby",
    ],
    "boxing":     [
        "boxing fight news today",
        "heavyweight boxing world championship",
    ],
    "f1":         [
        "formula 1 grand prix news today",
        "F1 race results qualifying news",
    ],
    "igaming":    [
        "online gambling regulation africa news",
        "igaming sports betting industry news",
    ],
    "betting":    [
        "sports betting tips odds today africa",
        "best betting predictions accumulator today",
        "african bookmaker odds value bets today",
    ],
}

# ── FALLBACK RSS FEEDS ────────────────────────────────────────────────────────
FEEDS: list[tuple[str, str, str]] = [
    # Football
    ("BBC Sport",         "https://feeds.bbci.co.uk/sport/football/rss.xml",            "football"),
    ("ESPN Soccer",       "https://www.espn.com/espn/rss/soccer/news",                  "football"),
    ("Guardian Football", "https://www.theguardian.com/football/rss",                   "football"),
    ("Sky Football",      "https://www.skysports.com/rss/11095",                        "football"),
    ("BBC Africa Sport",  "https://feeds.bbci.co.uk/sport/africa/rss.xml",              "football"),
    # Sport News
    ("Sky Sports News",   "https://www.skysports.com/rss/12040",                        "sportnews"),
    ("Sky Sport All",     "https://www.skysports.com/rss/12",                           "sportnews"),
    ("BBC Sport All",     "https://feeds.bbci.co.uk/sport/rss.xml",                     "sportnews"),
    ("BBC Transfers",     "https://feeds.bbci.co.uk/sport/football/transfers/rss.xml",  "sportnews"),
    ("ESPN All",          "https://www.espn.com/espn/rss/news",                         "sportnews"),
    ("Guardian Sport",    "https://www.theguardian.com/sport/rss",                      "sportnews"),
    # Basketball
    ("BBC Basketball",    "https://feeds.bbci.co.uk/sport/basketball/rss.xml",          "basketball"),
    ("ESPN NBA",          "https://www.espn.com/espn/rss/nba/news",                     "basketball"),
    ("Guardian NBA",      "https://www.theguardian.com/sport/nba/rss",                  "basketball"),
    # Tennis
    ("BBC Tennis",        "https://feeds.bbci.co.uk/sport/tennis/rss.xml",              "tennis"),
    ("ESPN Tennis",       "https://www.espn.com/espn/rss/tennis/news",                  "tennis"),
    ("Guardian Tennis",   "https://www.theguardian.com/sport/tennis/rss",               "tennis"),
    # Cricket
    ("BBC Cricket",       "https://feeds.bbci.co.uk/sport/cricket/rss.xml",             "cricket"),
    ("ESPN Cricket",      "https://www.espn.com/espn/rss/cricket/news",                 "cricket"),
    ("Guardian Cricket",  "https://www.theguardian.com/sport/cricket/rss",              "cricket"),
    # Rugby
    ("BBC Rugby",         "https://feeds.bbci.co.uk/sport/rugby-union/rss.xml",         "rugby"),
    ("ESPN Rugby",        "https://www.espn.com/espn/rss/rugby/news",                   "rugby"),
    ("Guardian Rugby",    "https://www.theguardian.com/sport/rugby-union/rss",          "rugby"),
    # Boxing
    ("BBC Boxing",        "https://feeds.bbci.co.uk/sport/boxing/rss.xml",              "boxing"),
    ("ESPN Boxing",       "https://www.espn.com/espn/rss/boxing/news",                  "boxing"),
    ("Guardian Boxing",   "https://www.theguardian.com/sport/boxing/rss",               "boxing"),
    # Formula 1
    ("BBC F1",            "https://feeds.bbci.co.uk/sport/formula1/rss.xml",            "f1"),
    ("ESPN F1",           "https://www.espn.com/espn/rss/f1/news",                      "f1"),
    ("Guardian F1",       "https://www.theguardian.com/sport/formulaone/rss",           "f1"),
    # iGaming
    ("iGaming Business",  "https://igamingbusiness.com/feed/",                          "igaming"),
    ("Calvinayre",        "https://calvinayre.com/feed/",                               "igaming"),
    # Betting Tips & Odds
    ("Guardian Betting",  "https://www.theguardian.com/sport/betting/rss",              "betting"),
    ("BBC Sport Betting", "https://feeds.bbci.co.uk/sport/rss.xml",                     "betting"),
]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

_CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"


# ── DATE PARSING ──────────────────────────────────────────────────────────────

def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse any date string → aware UTC datetime.
    Returns None if unparseable — NEVER falls back to now().
    """
    if not date_str:
        return None
    s = date_str.strip()
    # Normalise timezone abbreviations
    s = re.sub(r'\s+(EST|EDT)$', ' -0500', s)
    s = re.sub(r'\s+(CST|CDT)$', ' -0600', s)
    s = re.sub(r'\s+(MST|MDT)$', ' -0700', s)
    s = re.sub(r'\s+(PST|PDT)$', ' -0800', s)
    s = re.sub(r'\s+(GMT|UTC)$',  ' +0000', s)
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M %z",
        "%d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def _strip_html(text: Optional[str]) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _text(el: Optional[ET.Element]) -> str:
    return (el.text or "").strip() if el is not None else ""


def _make_item(title: str, description: str, url: str, source: str,
               category: str, pub_dt: datetime) -> NewsItem:
    now = datetime.now(timezone.utc)
    age = (now - pub_dt).total_seconds() / 3600
    return NewsItem(
        title=title,
        description=description[:300],
        url=url,
        source=source,
        category=category,
        published_at=pub_dt.isoformat(),
        age_hours=round(age, 1),
    )


# ── LAYER 1: DUCKDUCKGO NEWS SEARCH ──────────────────────────────────────────

def _ddg_search(query: str, category: str, max_age_hours: int,
                max_results: int = 8) -> list[NewsItem]:
    """Search DuckDuckGo News — live web results, last 24h."""
    try:
        try:
            from ddgs import DDGS          # new package name
        except ImportError:
            from duckduckgo_search import DDGS  # legacy fallback
        with DDGS() as ddgs:
            raw = list(ddgs.news(query, max_results=max_results, timelimit="d"))
    except Exception:
        return []

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=max_age_hours)
    items: list[NewsItem] = []

    for r in raw:
        title = (r.get("title") or "").strip()
        if not title or len(title) < 5:
            continue
        pub_dt = _parse_date(r.get("date") or r.get("published"))
        if pub_dt is None or pub_dt < cutoff:
            continue
        items.append(_make_item(
            title=title,
            description=_strip_html(r.get("body") or r.get("excerpt") or ""),
            url=r.get("url") or r.get("link") or "",
            source=r.get("source") or "DuckDuckGo",
            category=category,
            pub_dt=pub_dt,
        ))

    return items


# ── LAYER 2: GOOGLE NEWS RSS SEARCH ──────────────────────────────────────────

def _fetch_url(url: str, timeout: int = 12) -> Optional[bytes]:
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception:
        return None


def _google_news_search(query: str, category: str,
                        max_age_hours: int) -> list[NewsItem]:
    """Fetch Google News RSS for a search query."""
    encoded = urllib.parse.quote(query)
    url = (
        f"https://news.google.com/rss/search"
        f"?q={encoded}&hl=en&gl=US&ceid=US:en"
    )
    data = _fetch_url(url)
    if not data:
        return []
    return _parse_rss(data, "Google News", category, max_age_hours)


# ── LAYER 3: SITE RSS FEEDS ───────────────────────────────────────────────────

def _parse_rss(xml_bytes: bytes, source: str, category: str,
               max_age_hours: int) -> list[NewsItem]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=max_age_hours)
    items: list[NewsItem] = []

    for item in root.findall(".//item"):
        title = _text(item.find("title"))
        if not title or len(title) < 5:
            continue
        pub_dt = _parse_date(_text(item.find("pubDate")))
        if pub_dt is None or pub_dt < cutoff:
            continue
        desc_raw = (
            _text(item.find(f"{{{_CONTENT_NS}}}encoded"))
            or _text(item.find("description"))
        )
        link = _text(item.find("link")) or _text(item.find("guid"))
        items.append(_make_item(
            title=title,
            description=_strip_html(desc_raw),
            url=link,
            source=source,
            category=category,
            pub_dt=pub_dt,
        ))

    return items


def _fetch_site_feeds(feed_list: list[tuple[str, str, str]], category: str,
                      max_age_hours: int, max_per_feed: int = 6) -> list[NewsItem]:
    items: list[NewsItem] = []
    for source, url, _ in feed_list:
        data = _fetch_url(url)
        if not data:
            continue
        parsed = _parse_rss(data, source, category, max_age_hours)
        parsed.sort(key=lambda x: x["age_hours"])
        items.extend(parsed[:max_per_feed])
    return items


# ── DEDUPLICATION & SORTING ───────────────────────────────────────────────────

def _dedupe_sort(items: list[NewsItem]) -> list[NewsItem]:
    seen: set[str] = set()
    unique: list[NewsItem] = []
    for item in items:
        key = re.sub(r"[^a-z0-9]", "", item["title"].lower())[:40]
        if key not in seen:
            seen.add(key)
            unique.append(item)
    unique.sort(key=lambda x: x["age_hours"])
    return unique


# ── PUBLIC API ────────────────────────────────────────────────────────────────

def fetch_category(category: str, max_per_feed: int = 6) -> list[NewsItem]:
    """
    Fetch fresh headlines for a category using three layers:
    1. DuckDuckGo live web search (freshest)
    2. Google News RSS per keyword
    3. Site-specific RSS feeds (BBC/ESPN/Guardian/Sky)

    Returns [] if fewer than MIN_FRESH_ITEMS pass the freshness window,
    so the agent skips generation rather than writing about stale news.
    """
    max_age = MAX_AGE_HOURS.get(category, DEFAULT_MAX_AGE_HOURS)
    queries = SEARCH_QUERIES.get(category, [f"{category} sports news today"])
    all_items: list[NewsItem] = []

    # Layer 1: DuckDuckGo
    for q in queries:
        all_items.extend(_ddg_search(q, category, max_age, max_results=6))

    # Layer 2: Google News RSS
    for q in queries:
        all_items.extend(_google_news_search(q, category, max_age))

    # Layer 3: Site RSS fallback
    site_feeds = [(s, u, c) for s, u, c in FEEDS if c == category]
    all_items.extend(_fetch_site_feeds(site_feeds, category, max_age, max_per_feed))

    result = _dedupe_sort(all_items)
    return result if len(result) >= MIN_FRESH_ITEMS else []


def fetch_all_categories(max_per_category: int = 8) -> dict[str, list[NewsItem]]:
    categories = [
        "football", "sportnews", "basketball", "tennis",
        "cricket", "rugby", "boxing", "f1", "igaming",
    ]
    return {cat: fetch_category(cat, max_per_feed=max_per_category // 2)
            for cat in categories}


def build_ticker_items(max_items: int = 20) -> list[dict]:
    """Build live ticker — freshest stories across all categories."""
    categories = [
        "football", "sportnews", "basketball", "tennis",
        "cricket", "rugby", "boxing", "f1", "igaming",
    ]
    seen_global: set[str] = set()
    ticker: list[dict] = []
    per_cat = max(2, max_items // len(categories))

    for cat in categories:
        items = fetch_category(cat, max_per_feed=4)
        added = 0
        for item in items:
            if added >= per_cat:
                break
            key = re.sub(r"[^a-z0-9]", "", item["title"].lower())[:40]
            if key in seen_global:
                continue
            seen_global.add(key)
            ticker.append({
                "category": cat,
                "text": item["title"],
                "source": item["source"],
                "url": item["url"],
                "published_at": item["published_at"],
                "age_hours": item["age_hours"],
            })
            added += 1

    ticker.sort(key=lambda x: x.get("age_hours", 999))
    return ticker[:max_items]


def format_for_prompt(items: list[NewsItem], limit: int = 10) -> str:
    """Format news for the LLM — shows exact age so it knows how current each story is."""
    if not items:
        return "⚠ NO FRESH NEWS AVAILABLE — do not generate an article."

    lines = []
    for i, item in enumerate(items[:limit], 1):
        age = item.get("age_hours", 0)
        age_label = (
            f"{int(age * 60)}m ago" if age < 1
            else f"{age:.1f}h ago" if age < 24
            else f"{age / 24:.1f}d ago"
        )
        lines.append(
            f"{i}. [{item['source']} · {age_label}] {item['title']}"
            + (f"\n   {item['description'][:160]}" if item["description"] else "")
        )

    oldest = max(i.get("age_hours", 0) for i in items[:limit])
    freshest = items[0].get("age_hours", 0)
    lines.append(
        f"\n⏰ News window: {freshest:.1f}h – {oldest:.1f}h old. "
        f"Write ONLY about these actual named stories — do not invent events."
    )
    return "\n".join(lines)
