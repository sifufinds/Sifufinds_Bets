"""
Free, legal player/club photo lookup via the Wikipedia REST + Search APIs.

Wikipedia's page-summary endpoint returns the same lead image used in the
article infobox, which is always hosted on Wikimedia Commons under a licence
that permits reuse (CC BY-SA or public domain) — this is the same source
Wikipedia itself displays, so pulling the URL and hotlinking it for a social
post caption is safe. No API key, no login, no scraping of a photo host that
could revoke rights.

Deliberately does NOT scrape photos from news outlets (BBC/Sky/Guardian/etc.)
even though those articles almost always carry a current picture of the
player — those are near-always syndicated agency photos (Getty/PA/Reuters)
licensed only for that outlet's own site, and reposting them to our own
channels would be real copyright exposure, not a grey area. Wikimedia Commons
is the one large, genuinely free-to-reuse source of footballer photos, so the
lookup here is deliberately made smarter (search + disambiguation handling)
rather than widening the source list to include copyrighted press photos.

Never invents a photo: if the named person has no Wikipedia page, or the page
has no lead image, returns None and the caller falls back to SifuFinds' own
generic branded card.
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


def looks_like_person_name(name: str) -> bool:
    """Light heuristic: two or more capitalised words, no digits — filters out
    junk like 'Unknown Player' or club names accidentally passed in."""
    name = (name or "").strip()
    if not name:
        return False
    if re.search(r"\d", name):
        return False
    words = [w for w in name.split() if w]
    return len(words) >= 2 and all(w[0].isupper() for w in words if w[0].isalpha())
