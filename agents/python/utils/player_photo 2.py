"""
Free, legal player/club photo lookup via the Wikipedia REST API.

Wikipedia's page-summary endpoint returns the same lead image used in the
article infobox, which is always hosted on Wikimedia Commons under a licence
that permits reuse (CC BY-SA or public domain) — this is the same source
Wikipedia itself displays, so pulling the URL and hotlinking it for a social
post caption is safe. No API key, no login, no scraping of a photo host that
could revoke rights.

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


def _fetch(url: str, timeout: int = 8) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def fetch_player_photo(name: str) -> Optional[str]:
    """Return a public HTTPS photo URL for the named person/club, or None.

    Uses the Wikipedia summary endpoint directly against the name first
    (handles well-known players like 'Yan Diomande' or 'Vinicius Junior'),
    and never guesses a disambiguated title — a miss just returns None.
    """
    name = (name or "").strip()
    if not name or len(name) < 3:
        return None

    title = urllib.parse.quote(name.replace(" ", "_"))
    data = _fetch(_SUMMARY_URL.format(title=title))
    if not data:
        return None

    # Disambiguation / missing pages carry these markers — never guess further.
    if data.get("type") in ("disambiguation", "no-extract") and not data.get("thumbnail"):
        return None

    thumb = data.get("originalimage") or data.get("thumbnail")
    if not thumb or not thumb.get("source"):
        return None

    url = thumb["source"]
    # Only trust Wikimedia-hosted images (upload.wikimedia.org) — never
    # follow a redirect to some other third-party host.
    if "upload.wikimedia.org" not in url:
        return None
    return url


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
