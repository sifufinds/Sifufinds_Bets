"""
Player/club photo lookup — sports news & social image search first, with a
Wikipedia REST/Search API fallback.

Product decision (explicit user direction, 2026-07-26): source images from
the wider football media ecosystem — sports news outlets (BBC/Sky/Guardian/
Mirror/TeamTalk/etc.) and public social platforms — via DuckDuckGo image
search (search_news_photo/find_player_image), not just Wikimedia Commons.
This carries real copyright exposure that Wikimedia hotlinking doesn't:
those outlets' photos are typically syndicated agency photos (Getty/PA/
Reuters) licensed for the outlet's own site, not necessarily free for
SifuFinds to repost. Flagged that tradeoff to the user before building this;
recorded here so a future reader doesn't mistake it for an oversight.

Wikipedia's page-summary endpoint (fetch_player_photo/fetch_entity_photo)
remains as the fallback tier: its lead image is always hosted on Wikimedia
Commons under a licence that permits reuse (CC BY-SA or public domain), so
it's the safe net for whatever the news/social search misses.

Never invents a photo: if nothing is found at either tier, returns None and
the caller falls back to SifuFinds' own generic branded card.
"""
import re
import urllib.parse
import urllib.request
import json
from typing import Optional

_HEADERS = {
    # Wikimedia's API etiquette policy requires a descriptive User-Agent with
    # contact info for any automated client — see https://meta.wikimedia.org/wiki/User-Agent_policy
    "User-Agent": "SifuFindsBot/1.0 (https://sifufinds.com; contact: kai.s.manyeh@gmail.com)",
    "Accept": "application/json",
}

_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
_SEARCH_URL = "https://en.wikipedia.org/w/api.php"

_FOOTBALL_HINTS = (
    "footballer", "football player", "association football",
    "midfielder", "defender", "forward", "goalkeeper", "winger", "striker",
)

# Broader than _FOOTBALL_HINTS — covers clubs/national teams and the other
# sports SifuFinds writes about (basketball, cricket, tennis, rugby, boxing,
# F1), so blog feature-image lookups (see scripts/generate_blog_feature_image.py)
# can find a real photo for a team or a non-footballer subject too, not just
# individual footballers.
_ENTITY_HINTS = _FOOTBALL_HINTS + (
    "football club", "national football team", "soccer club",
    "basketball player", "basketball team", "point guard", "shooting guard",
    "small forward", "power forward", "national basketball association",
    "cricketer", "cricket team",
    "tennis player",
    "rugby union", "rugby league",
    "boxer",
    "racing driver", "formula one",
    "head coach", "football manager", "manager (association football)",
)


_WOMEN_HINTS = ("women's", "women", "womens", "female")


def _mentions_women(text: str) -> bool:
    text_l = (text or "").lower()
    return any(hint in text_l for hint in _WOMEN_HINTS)


def _gender_mismatch(query: str, candidate_text: str) -> bool:
    """True when a candidate's own text disagrees with the query on men's vs
    women's football — in either direction, so this also protects a genuine
    women's-football query from picking up a men's photo, not just the
    reported direction.

    Root cause of a live incident (2026-07-27): a bare country tag like
    'Morocco' on a post specifically about the Men's FIFA World Ranking
    resolved, via both the Wikipedia search fallback and the news/social
    image search, to Morocco's WOMEN's national team celebrating their 2023
    World Cup run — a completely different, unrelated story that happened to
    share the word 'Morocco'. Neither tier's existing checks (entity-context
    keyword match, or "every word of the query appears in the title") catch
    this, because both texts are legitimately about association football —
    they just aren't about the same team. Blocking the org/competition tags
    that started this (see generate_blog_feature_image._ORG_AND_COMPETITION_WORDS)
    closes the most direct path, but a bare team/country name can still
    surface the wrong-gender side, so this check runs wherever a candidate
    is accepted regardless of which tag reached it."""
    return _mentions_women(candidate_text) != _mentions_women(query)


def _fetch_json(url: str, timeout: int = 8) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _thumbnail_from_summary(data: dict) -> Optional[str]:
    thumb = data.get("originalimage") or data.get("thumbnail")
    if not thumb or not thumb.get("source"):
        return None
    url = thumb["source"]
    # Only trust Wikimedia-hosted images — never follow a redirect to some
    # other third-party host the summary API might otherwise point at.
    return url if "upload.wikimedia.org" in url else None


def _get_summary(title: str) -> Optional[dict]:
    return _fetch_json(_SUMMARY_URL.format(title=urllib.parse.quote(title.replace(" ", "_"))))


_COUNTRY_DESC_HINTS = (
    "country in", "sovereign state in", "island nation", "island country",
    "country located in", "country on the",
)


def _looks_like_bare_country(name: str) -> bool:
    """True when `name` resolves on Wikipedia to a country/place page rather
    than a sports subject. A bare country name is exactly the ambiguous
    shape that caused a live incident (2026-07-27): 'Morocco' alone gives
    neither Wikipedia's search fallback nor the news-image search any way to
    tell the men's national team from the women's, so either could come
    back for a query that was never about gender in the first place. This
    check drives qualify_entity_query() below rather than hardcoding a
    country list, so it keeps working for any country tag the content
    pipeline produces."""
    data = _get_summary(name)
    if not data:
        return False
    desc = (data.get("description") or "").lower()
    return any(hint in desc for hint in _COUNTRY_DESC_HINTS)


def qualify_entity_query(name: str) -> str:
    """Rewrites a bare country name to its unambiguous men's-side Wikipedia
    title before either photo tier ever runs a query. '<Country> national
    football team' is the long-standing Wikipedia convention for the men's
    side; the women's side is always titled '<Country> women's national
    football team' explicitly. Any other name — a player, a club, a name
    that's already qualified — is returned unchanged."""
    name = (name or "").strip()
    if name and _looks_like_bare_country(name):
        return f"{name} national football team"
    return name


def _is_football_context(data: dict) -> bool:
    haystack = f"{data.get('description', '')} {data.get('extract', '')}".lower()
    return any(hint in haystack for hint in _FOOTBALL_HINTS)


def _matches_club(data: dict, context_clubs: list[str]) -> bool:
    haystack = f"{data.get('description', '')} {data.get('extract', '')}".lower()
    return any(club.lower() in haystack for club in context_clubs if club)


def _search_candidates(query: str, limit: int = 5) -> list[str]:
    params = urllib.parse.urlencode({
        "action": "query", "list": "search", "srsearch": query,
        "format": "json", "srlimit": limit,
    })
    data = _fetch_json(f"{_SEARCH_URL}?{params}")
    if not data:
        return []
    return [r["title"] for r in data.get("query", {}).get("search", [])]


def fetch_player_photo(name: str, context_clubs: Optional[list[str]] = None) -> Optional[str]:
    """Return a public HTTPS photo URL for the named person, or None.

    Two-stage lookup:
    1. Direct summary lookup against the exact name — fast path for
       unambiguous names ('Yan Diomande', 'Vinicius Junior').
    2. If that misses or lands on a disambiguation page (e.g. 'Marcos
       Alonso', shared by a father and son who both played professionally),
       search Wikipedia for '<name> footballer' and vet every candidate that
       Wikipedia's own description/extract identifies as a footballer.
       Among those, a candidate whose page already mentions one of the
       known clubs (from_club/to_club, if extracted from the real article)
       is preferred — but a transfer story is inherently about the club a
       player is *joining*, which by definition won't be on their Wikipedia
       page yet, so club context is a confidence boost, not a hard filter;
       falling back to Wikipedia's own search-relevance order among
       football-context candidates still reliably picks the active,
       notable player over a same-named historical figure. Never falls
       back to a non-football candidate — a wrong photo is a worse
       failure than no photo.
    """
    name = (name or "").strip()
    if not name or len(name) < 3:
        return None
    context_clubs = [c for c in (context_clubs or []) if c]

    data = _get_summary(name)
    if data and data.get("type") not in ("disambiguation", "no-extract"):
        photo = _thumbnail_from_summary(data)
        if photo:
            return photo

    # Fast path missed or hit a disambiguation page — search, keep only
    # football-context candidates, and prefer a club match when one exists.
    football_candidates = []
    for candidate_title in _search_candidates(f"{name} footballer"):
        candidate = _get_summary(candidate_title)
        if not candidate or candidate.get("type") == "disambiguation":
            continue
        if not _is_football_context(candidate):
            continue
        football_candidates.append(candidate)

    football_candidates.sort(key=lambda c: not _matches_club(c, context_clubs))
    for candidate in football_candidates:
        photo = _thumbnail_from_summary(candidate)
        if photo:
            return photo

    return None


def _is_entity_context(data: dict) -> bool:
    haystack = f"{data.get('description', '')} {data.get('extract', '')}".lower()
    return any(hint in haystack for hint in _ENTITY_HINTS)


def _shares_significant_word(name: str, candidate_title: str) -> bool:
    """Guards the search-fallback tier below: Wikipedia's search API happily
    returns tangentially-related sport pages for a generic query (e.g.
    "odds comparison sport" surfaced "Rugby football" and "Set piece
    (football)" — both pass _is_entity_context since they genuinely are
    sports pages, but have zero relation to "odds comparison"). Caught this
    by actually rendering a feature image for a generic non-player betting
    post and seeing an unrelated 19th-century engraving come back. Requiring
    at least one non-trivial word in common with the original query keeps
    real name-variant matches (disambiguation pages, "F.C." suffixes) while
    rejecting genuinely unrelated sport pages a loose query happened to hit."""
    name_words = {w.lower() for w in re.findall(r"[A-Za-z]{3,}", name)}
    candidate_words = {w.lower() for w in re.findall(r"[A-Za-z]{3,}", candidate_title)}
    return bool(name_words & candidate_words)


def fetch_entity_photo(name: str) -> Optional[str]:
    """Like fetch_player_photo, but for any sports subject — a player, a
    club/national team, or a coach — used to source a real featured image
    for blog posts (see scripts/generate_blog_feature_image.py) instead of
    always falling back to the generic branded card.

    Same guarantee as fetch_player_photo: only returns a photo when
    Wikipedia's own description/extract for the matched page identifies it
    as a sports subject, so a same-named unrelated Wikipedia page (a place,
    a film, an unrelated person) never gets picked up. Returns None rather
    than guess when nothing qualifies.
    """
    name = (name or "").strip()
    if not name or len(name) < 3:
        return None

    data = _get_summary(name)
    if data and data.get("type") not in ("disambiguation", "no-extract") and _is_entity_context(data):
        haystack = f"{data.get('title', '')} {data.get('description', '')} {data.get('extract', '')}"
        if not _gender_mismatch(name, haystack):
            photo = _thumbnail_from_summary(data)
            if photo:
                return photo

    for candidate_title in _search_candidates(f"{name} sport"):
        if not _shares_significant_word(name, candidate_title):
            continue
        candidate = _get_summary(candidate_title)
        if not candidate or candidate.get("type") == "disambiguation":
            continue
        if not _is_entity_context(candidate):
            continue
        haystack = f"{candidate_title} {candidate.get('description', '')} {candidate.get('extract', '')}"
        if _gender_mismatch(name, haystack):
            continue
        photo = _thumbnail_from_summary(candidate)
        if photo:
            return photo

    return None


# Outlets explicitly named by the user (2026-07-26) plus the other
# free/open sports-news sources this codebase already treats as reliable
# for text (see utils/news_fetcher.py FEEDS) — searched via `site:` first so
# a result is an actual editorial photo from a named newsroom, not whatever
# an unrestricted query happens to surface (verified during testing: a bare
# open-web image search for "Real Madrid" and "Chelsea" returned wallpaper-
# aggregator sites and a photo-agency CDN, not a newsroom or social source
# and a worse copyright/quality bet than the site-restricted tier below).
_TRUSTED_NEWS_DOMAINS = (
    "skysports.com", "bbc.co.uk", "bbc.com", "espn.com",
    "theguardian.com", "90min.com", "talksport.com",
    "independent.co.uk", "mirror.co.uk", "goal.com",
)
# Public social platforms, tried after the newsroom tier — image search
# engines rarely surface individual social posts reliably, so this is a
# lighter-weight second pass rather than the primary source.
_SOCIAL_DOMAINS = ("twitter.com", "x.com", "instagram.com", "facebook.com")


def _ddgs_image_search(query: str, max_results: int = 6) -> list[dict]:
    try:
        from ddgs import DDGS
    except ImportError:
        return []
    try:
        with DDGS() as ddgs:
            return list(ddgs.images(query, max_results=max_results))
    except Exception:
        return []


def search_news_photo(name: str, context_clubs: Optional[list[str]] = None) -> Optional[str]:
    """Search sports news outlets and social platforms for a real, current
    photo of the named subject, via DuckDuckGo image search (free, no key —
    the `ddgs` package already used elsewhere in this codebase). This is a
    deliberate product decision to source images from the wider football
    media ecosystem (BBC/Sky/ESPN/Guardian/etc. and public social posts),
    not just Wikimedia Commons — those outlets' photos are typically
    syndicated agency photos (Getty/PA/Reuters) licensed for the outlet's
    own site, so this carries real copyright exposure that plain Wikimedia
    hotlinking doesn't. Made that tradeoff explicitly at the user's
    direction rather than silently choosing either side.

    Tries the named outlets first (site: restricted, one query per domain
    tier — see _TRUSTED_NEWS_DOMAINS), then social platforms, then an open
    query as a last resort before the caller falls through to Wikipedia.
    Every tier requires every word of the name to appear in the result
    title before trusting an image — general image-search relevance is much
    noisier than Wikipedia's structured data (a bare "Alonso Chelsea" query
    mixed in results for Xabi Alonso, Chelsea's manager, alongside Marcos
    Alonso, the player) — a wrong photo is a worse failure than none.
    """
    name = (name or "").strip()
    if not name:
        return None
    name_parts = [p.lower() for p in name.split() if len(p) > 2]
    if not name_parts:
        return None

    club_hint = next((c for c in (context_clubs or []) if c), "")
    base_query = f'"{name}" {club_hint}'.strip()

    def _first_match(results: list[dict]) -> Optional[str]:
        for r in results:
            image_url = r.get("image") or ""
            title = (r.get("title") or "").lower()
            if not image_url.startswith("https://"):
                continue
            # lookaside.instagram.com is a live SEO-preview crawler proxy, not
            # a stable direct photo URL — it can return a generic Instagram
            # placeholder, a different post's cached preview, or nothing
            # decodable at all depending on what Instagram's crawler feels
            # like serving that moment. Real post images live on
            # scontent*.cdninstagram.com / *.fbcdn.net.
            if "lookaside.instagram.com" in image_url:
                continue
            if not all(part in title for part in name_parts):
                continue
            # "every word of the name appears in the title" is trivially true
            # for a bare team/country query ("Morocco") on any article about
            # that name — including a completely unrelated women's-side story
            # (the actual 2026-07-27 incident: a Men's FIFA ranking post's
            # "Morocco" tag surfaced Morocco WOMEN's 2023 World Cup
            # celebration photos, since both texts legitimately say
            # "Morocco"). Reject a men's/women's mismatch in either
            # direction — see _gender_mismatch's docstring.
            if _gender_mismatch(name, title):
                continue
            return image_url
        return None

    for domain in _TRUSTED_NEWS_DOMAINS:
        photo = _first_match(_ddgs_image_search(f"{base_query} site:{domain}", max_results=3))
        if photo:
            return photo

    for domain in _SOCIAL_DOMAINS:
        photo = _first_match(_ddgs_image_search(f"{base_query} site:{domain}", max_results=3))
        if photo:
            return photo

    return _first_match(_ddgs_image_search(base_query, max_results=8))


def find_player_image(name: str, context_clubs: Optional[list[str]] = None) -> Optional[str]:
    """Best-effort real photo lookup for a transfer-news subject: sports
    news/social image search first (see search_news_photo — the current
    product policy), then Wikipedia as a safe, always-free-to-reuse
    fallback for whatever the search misses. Returns None only if both
    tiers come up empty, in which case the caller falls back further to
    SifuFinds' own branded graphic."""
    return search_news_photo(name, context_clubs) or fetch_player_photo(name, context_clubs)


def find_entity_image(name: str, context: Optional[list[str]] = None) -> Optional[str]:
    """Same news/social-first, Wikipedia-fallback policy as find_player_image,
    but for any sports subject a blog post's feature image might need — a
    player, a club, or a national team (see scripts/generate_blog_feature_image.py).
    Falls back to fetch_entity_photo (not fetch_player_photo) so a team name
    still resolves to its crest/photo on the Wikipedia safety-net tier."""
    query = qualify_entity_query(name)
    return search_news_photo(query, context) or fetch_entity_photo(query)


_NAME_PLACEHOLDERS = {"unknown", "player", "n/a", "tbd", "none", "unnamed", "club"}


def looks_like_person_name(name: str) -> bool:
    """Light heuristic filtering out junk like 'Unknown Player' or a club
    name accidentally passed in, while still accepting single-word football
    mononyms (Rodri, Casemiro, Neymar, Militão) — very common in transfer
    news and previously excluded entirely by a hard "2+ words" rule, which
    meant single-name players never got a real photo lookup at all."""
    name = (name or "").strip()
    if not name:
        return False
    if re.search(r"\d", name):
        return False
    if name.lower() in _NAME_PLACEHOLDERS:
        return False
    words = [w for w in name.split() if w]
    if not words:
        return False
    if len(words) >= 2:
        return all(w[0].isupper() for w in words if w[0].isalpha())
    # Single word: require proper case (First-letter-upper, rest lower) and
    # a plausible length — excludes all-caps abbreviations like "TBD" or
    # "NBA" (their rest-of-word isn't lowercase) while still accepting a
    # real mononym.
    w = words[0]
    return len(w) >= 4 and w[0].isupper() and w[1:].islower()
