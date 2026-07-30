"""
Live news research module — three-layer search for maximum freshness.

Layer 1 — DuckDuckGo News Search (live web, last 24h, no API key)
Layer 2 — Google News RSS search (Google's index, per keyword, no API key)
Layer 3 — Site RSS feeds: 45 verified-live feeds spanning BBC, Guardian, TalkSport,
          Independent, 90min, Yahoo, Sporting News, CBS Sports, Sportskeeda,
          ESPN Cricinfo, Autosport, France24, iGaming Business/SBC News/EGR
          Global/Vegas Slots Online, plus nine African outlets (AllAfrica,
          Punch/Vanguard/Complete Sports/Premium Times for Nigeria, Standard
          Sports for Kenya, Graphic Sports for Ghana, KickOff for South Africa,
          Africa Top Sports pan-African)

Freshness rules:
  - Items with no parseable pubDate are DISCARDED (never faked as "now")
  - Each category has a MAX_AGE_HOURS window; stale items are filtered out
  - If < MIN_FRESH_ITEMS pass the filter the agent skips generation
"""
import html
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import TypedDict, Optional
import re

# ── FRESHNESS CONFIG ──────────────────────────────────────────────────────────
MAX_AGE_HOURS: dict[str, int] = {
    "football":      48,
    "sportnews":     48,
    "transfers":     24,   # transfer news moves fast — stale rumours aren't worth posting
    "basketball":    48,
    "betting":       72,
    "tennis":        72,
    "cricket":       72,
    "rugby":         72,
    "boxing":        168,
    "f1":            168,
    "igaming":       168,
    "worldcup2026":  24,   # daily freshness — tournament runs June–July 2026
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
    image: str


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
        "Nigeria Kenya Ghana South Africa sports news today",
    ],
    "transfers":  [
        "football transfer news today deal agreed",
        "premier league transfer rumours today",
        "european club transfer window news today",
        "african player transfer news today",
        "Fabrizio Romano here we go transfer",
        "David Ornstein Athletic transfer exclusive",
        "Sky Sports News transfer deadline day",
        "ESPN FC transfer news today",
        "BBC Sport transfer news today",
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
    "worldcup2026": [
        "FIFA World Cup 2026 match results today",
        "World Cup 2026 group stage scores news",
        "World Cup 2026 African teams Nigeria Morocco Senegal news",
        "World Cup 2026 betting odds predictions today",
    ],
}

# ── TRANSFER NEWS SOURCE ALLOWLIST ────────────────────────────────────────────
# Added 2026-07-28 by explicit product decision: transfer news must only ever
# be attributed to Sky Sports, BBC Sport, ESPN, TalkSport, David Ornstein (The
# Athletic), or Fabrizio Romano — never Google or Yahoo. All three fetch
# layers (DuckDuckGo, Google News RSS, site RSS feeds) are used for
# "transfers" — Google News RSS is no longer skipped as of the same date:
# it turned out to carry a real per-item <source> element (e.g. "Sky
# Sports", "BBC", "talkSPORT"), so _parse_rss(use_item_source=True) reads
# the genuine outlet instead of the generic "Google News" label an earlier
# version of this fix hardcoded. Every item from every layer is still
# filtered through _is_allowed_transfer_source() before it can be posted —
# this allowlist is what actually enforces the restriction now, not which
# layer an item came from.
TRANSFER_ALLOWED_SOURCE_TERMS = (
    "bbc",
    "sky sports",
    "espn",
    "talksport",
    "athletic",    # David Ornstein writes for The Athletic
    "ornstein",
    "romano",      # Fabrizio Romano
)


def _is_allowed_transfer_source(source: str) -> bool:
    s = (source or "").lower()
    return any(term in s for term in TRANSFER_ALLOWED_SOURCE_TERMS)


# ── FALLBACK RSS FEEDS ────────────────────────────────────────────────────────
# Full liveness audit run 2026-07-25 (fetched every URL, parsed the XML, and
# counted <item>s) turned up a large dead-weight problem: every espn.com/espn/rss/*
# feed (soccer, all, NBA, tennis, cricket, rugby, boxing, F1 — 8 entries), every
# skysports.com/rss/* feed (11095, 12040, 12 — all returned an empty <channel>
# with zero items), every mirror.co.uk RSS (football/sport/transfers), Calvinayre,
# and the Guardian betting feed were all silently dead or empty — non-fatal by
# design (fetch_category just gets less), but it means a large chunk of the
# "three-layer" coverage this file's docstring promises had quietly rotted away.
# Reuters, Football365, and Goal.com remain dead too (verified again this pass).
# Removed all of the above and replaced them with a wider, verified-live set —
# including nine African outlets (AllAfrica, Punch/Vanguard/Complete Sports/
# Premium Times for Nigeria, Standard Sports for Kenya, Graphic Sports for Ghana,
# KickOff for South Africa, Africa Top Sports pan-African) so African football
# and betting content is actually grounded in African reporting, not just UK/US
# outlets covering Africa from the outside. Re-run the liveness check in
# scripts/check_news_feeds.py before trusting any future edit to this list —
# RSS feeds rot silently and non-fatally, so a stale entry never raises an error,
# it just quietly stops contributing sources.
FEEDS: list[tuple[str, str, str]] = [
    # Football — international
    ("BBC Sport",         "https://feeds.bbci.co.uk/sport/football/rss.xml",            "football"),
    ("Guardian Football", "https://www.theguardian.com/football/rss",                   "football"),
    ("BBC Africa Sport",  "https://feeds.bbci.co.uk/sport/africa/rss.xml",              "football"),
    ("90min",             "https://www.90min.com/posts.rss",                            "football"),
    ("TalkSport",         "https://talksport.com/feed/",                                "football"),
    ("Independent Football", "https://www.independent.co.uk/sport/football/rss",        "football"),
    ("Yahoo Soccer",      "https://sports.yahoo.com/soccer/rss.xml",                     "football"),
    ("France24 Sport",    "https://www.france24.com/en/sport/rss",                       "football"),
    # Football — African outlets (grounds African coverage in African reporting)
    ("AllAfrica Sports",  "https://allafrica.com/tools/headlines/rdf/sport/headlines.rdf", "football"),
    ("Punch Sports (Nigeria)",    "https://punchng.com/topics/sports/feed/",             "football"),
    ("Vanguard Sports (Nigeria)", "https://www.vanguardngr.com/category/sports/feed/",   "football"),
    ("Complete Sports (Nigeria)", "https://www.completesports.com/feed/",                "football"),
    ("Standard Sports (Kenya)",   "https://www.standardmedia.co.ke/rss/sports.php",      "football"),
    ("Graphic Sports (Ghana)",    "https://www.graphic.com.gh/sports.feed",              "football"),
    ("KickOff (South Africa)",    "https://www.kickoff.com/rss",                         "football"),
    ("Africa Top Sports",         "https://africatopsports.com/feed/",                   "football"),
    # World Cup 2026
    ("BBC Football WC",   "https://feeds.bbci.co.uk/sport/football/rss.xml",            "worldcup2026"),
    ("Guardian Football WC", "https://www.theguardian.com/football/rss",               "worldcup2026"),
    ("BBC Africa WC",     "https://feeds.bbci.co.uk/sport/africa/rss.xml",              "worldcup2026"),
    ("90min WC",          "https://www.90min.com/posts.rss",                            "worldcup2026"),
    ("AllAfrica Sports WC", "https://allafrica.com/tools/headlines/rdf/sport/headlines.rdf", "worldcup2026"),
    ("KickOff WC",        "https://www.kickoff.com/rss",                                 "worldcup2026"),
    # Sport News
    ("BBC Sport All",     "https://feeds.bbci.co.uk/sport/rss.xml",                     "sportnews"),
    ("BBC Transfers",     "https://feeds.bbci.co.uk/sport/football/transfers/rss.xml",  "sportnews"),
    ("Guardian Sport",    "https://www.theguardian.com/sport/rss",                      "sportnews"),
    ("TalkSport News",    "https://talksport.com/feed/",                                "sportnews"),
    ("Independent Sport", "https://www.independent.co.uk/sport/rss",                    "sportnews"),
    ("Sky News Sport",    "https://feeds.skynews.com/feeds/rss/sports.xml",              "sportnews"),
    ("Sporting News",     "https://www.sportingnews.com/us/rss",                         "sportnews"),
    ("CBS Sports",        "https://www.cbssports.com/rss/headlines/",                    "sportnews"),
    ("Yahoo Sports",      "https://sports.yahoo.com/rss/",                               "sportnews"),
    ("Sportskeeda",       "https://www.sportskeeda.com/feed",                            "sportnews"),
    ("Premium Times Sports (Nigeria)", "https://www.premiumtimesng.com/category/sports/feed", "sportnews"),
    # Transfers (dedicated feeds) — restricted to Sky Sports/BBC/ESPN/
    # TalkSport/David Ornstein/Fabrizio Romano only (2026-07-28); Guardian and
    # Yahoo dropped. No dedicated TalkSport RSS feed here: talksport.com/feed/
    # is a general all-sports feed (confirmed 2026-07-28 to carry NFL/other
    # non-football stories), so TalkSport coverage for "transfers" comes only
    # through the DuckDuckGo layer, whose queries are already football/
    # transfer-specific (see SEARCH_QUERIES["transfers"]) and still passes
    # through _is_allowed_transfer_source() like every other item.
    ("BBC Transfers Dedicated", "https://feeds.bbci.co.uk/sport/football/transfers/rss.xml", "transfers"),
    # Basketball
    ("BBC Basketball",    "https://feeds.bbci.co.uk/sport/basketball/rss.xml",          "basketball"),
    ("Guardian NBA",      "https://www.theguardian.com/sport/nba/rss",                  "basketball"),
    ("Sporting News NBA", "https://www.sportingnews.com/us/rss",                        "basketball"),
    ("CBS Sports NBA",    "https://www.cbssports.com/rss/headlines/",                   "basketball"),
    # Tennis
    ("BBC Tennis",        "https://feeds.bbci.co.uk/sport/tennis/rss.xml",              "tennis"),
    ("Guardian Tennis",   "https://www.theguardian.com/sport/tennis/rss",               "tennis"),
    # Cricket
    ("BBC Cricket",       "https://feeds.bbci.co.uk/sport/cricket/rss.xml",             "cricket"),
    ("Guardian Cricket",  "https://www.theguardian.com/sport/cricket/rss",              "cricket"),
    ("ESPN Cricinfo",     "https://www.espncricinfo.com/rss/content/story/feeds/0.xml", "cricket"),
    # Rugby
    ("BBC Rugby",         "https://feeds.bbci.co.uk/sport/rugby-union/rss.xml",         "rugby"),
    ("Guardian Rugby",    "https://www.theguardian.com/sport/rugby-union/rss",          "rugby"),
    # Boxing
    ("BBC Boxing",        "https://feeds.bbci.co.uk/sport/boxing/rss.xml",              "boxing"),
    ("Guardian Boxing",   "https://www.theguardian.com/sport/boxing/rss",               "boxing"),
    # Formula 1
    ("BBC F1",            "https://feeds.bbci.co.uk/sport/formula1/rss.xml",            "f1"),
    ("Guardian F1",       "https://www.theguardian.com/sport/formulaone/rss",           "f1"),
    ("Autosport F1",      "https://www.autosport.com/rss/f1/news/",                     "f1"),
    # iGaming
    ("iGaming Business",  "https://igamingbusiness.com/feed/",                          "igaming"),
    ("SBC News",          "https://sbcnews.co.uk/feed/",                                 "igaming"),
    ("EGR Global",        "https://egr.global/feed/",                                    "igaming"),
    ("Vegas Slots Online", "https://www.vegasslotsonline.com/news/feed/",               "igaming"),
    # Betting Tips & Odds
    ("BBC Sport Betting", "https://feeds.bbci.co.uk/sport/rss.xml",                     "betting"),
    ("Sportskeeda Betting", "https://www.sportskeeda.com/feed",                          "betting"),
    ("SBC News Betting",  "https://sbcnews.co.uk/feed/",                                 "betting"),
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
_MEDIA_NS = "http://search.yahoo.com/mrss/"


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


def _valid_image_url(url: str) -> str:
    """Only trust a well-formed http(s) URL as a real source image — never a
    relative path or garbage string a feed occasionally includes."""
    url = (url or "").strip()
    return url if url.startswith(("http://", "https://")) else ""


def _make_item(title: str, description: str, url: str, source: str,
               category: str, pub_dt: datetime, image: str = "") -> NewsItem:
    now = datetime.now(timezone.utc)
    age = (now - pub_dt).total_seconds() / 3600
    # RSS/search titles and descriptions routinely carry HTML entities
    # (&#8217; for a right single quote, &#8211; for an en dash, etc.) — every
    # caller used to hand this straight to an LLM, which paraphrased over the
    # mess without anyone noticing. Now that agent_transfer_post.py's raw-AI-
    # outage fallback (added 2026-07-27) can post a title/description
    # verbatim with no LLM in between, unescape here once so nothing ever
    # ships "&#8217;" literally in a live post again.
    return NewsItem(
        title=html.unescape(title),
        description=html.unescape(description)[:300],
        url=url,
        source=source,
        category=category,
        published_at=pub_dt.isoformat(),
        age_hours=round(age, 1),
        image=_valid_image_url(image),
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
            image=r.get("image") or "",
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
    return _parse_rss(data, "Google News", category, max_age_hours, use_item_source=True)


# ── LAYER 3: SITE RSS FEEDS ───────────────────────────────────────────────────

def _rss_item_image(item: ET.Element) -> str:
    """Real, article-specific image straight from the source feed (e.g. BBC's
    <media:thumbnail url="https://ichef.bbci.co.uk/..."> — confirmed live
    2026-07-28) — never a speculative name-based photo search. Checks the
    common RSS image patterns in order of how specific/reliable they are:
    media:content (usually full-size), media:thumbnail, then a plain
    <enclosure> with an image MIME type."""
    media_content = item.find(f"{{{_MEDIA_NS}}}content")
    if media_content is not None and media_content.get("url"):
        return media_content.get("url", "")
    thumbnail = item.find(f"{{{_MEDIA_NS}}}thumbnail")
    if thumbnail is not None and thumbnail.get("url"):
        return thumbnail.get("url", "")
    enclosure = item.find("enclosure")
    if enclosure is not None and enclosure.get("url") and "image" in enclosure.get("type", ""):
        return enclosure.get("url", "")
    return ""


def _parse_rss(xml_bytes: bytes, source: str, category: str,
               max_age_hours: int, use_item_source: bool = False) -> list[NewsItem]:
    """use_item_source=True reads each item's own <source> element (Google
    News RSS aggregates many outlets per feed and tags every item with the
    real publication, e.g. "Sky Sports"/"BBC"/"talkSPORT" — confirmed live
    2026-07-28) instead of the single fixed `source` string, which is what
    every other RSS feed here uses since they're already single-outlet
    feeds. Without this, Google News items were hardcoded to the literal
    string "Google News" and had to be excluded entirely from the
    "transfers" category's strict named-outlet allowlist — see
    TRANSFER_ALLOWED_SOURCE_TERMS above — even when the underlying item was
    genuinely from Sky Sports/BBC/ESPN/talkSPORT."""
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
        item_source = source
        if use_item_source:
            item_source = _text(item.find("source")) or source
        items.append(_make_item(
            title=title,
            description=_strip_html(desc_raw),
            url=link,
            source=item_source,
            category=category,
            pub_dt=pub_dt,
            image=_rss_item_image(item),
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

    # Layer 2: Google News RSS. Previously skipped entirely for "transfers"
    # on the theory that every item would be hardcoded to the unattributable
    # literal "Google News" — fixed 2026-07-28 by reading each item's real
    # <source> element instead (see _parse_rss's use_item_source), so this
    # layer now genuinely surfaces Sky Sports/BBC/ESPN/talkSPORT items
    # (confirmed live) and is included for every category, "transfers"
    # included; _is_allowed_transfer_source() below still filters out
    # anything that isn't one of the allowlisted outlets.
    for q in queries:
        all_items.extend(_google_news_search(q, category, max_age))

    # Layer 3: Site RSS fallback
    site_feeds = [(s, u, c) for s, u, c in FEEDS if c == category]
    all_items.extend(_fetch_site_feeds(site_feeds, category, max_age, max_per_feed))

    # Transfer news is restricted to a named-outlet allowlist regardless of
    # which layer surfaced it (Yahoo/Guardian/other outlets can still show up
    # via DuckDuckGo search results, not just the site-feed layer).
    if category == "transfers":
        all_items = [i for i in all_items if _is_allowed_transfer_source(i["source"])]

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
