"""Shared <title> / meta-description length enforcement for every page generator.

Every generator in this repo used to hand-roll its own title/description
truncation (or none at all) — gen_blog_post_pages.py and gen_bk_reviews.py
each carried their own slightly different copy of seo_title(), and the other
~11 generators (gen_best_betting_pages.py, generate_country_pages.py,
gen_bookmaker_country_pages.py, gen_payment_country_pages.py,
gen_sport_country_pages.py, gen_guide_pages.py, gen_bonus_pages.py,
gen_all_cities.py, gen_city_pages.py, gen_payment_pages.py,
gen_wc2026_teams.py) built meta descriptions by unbounded f-string
concatenation with no length check at all. That gap let 313 pages across
every one of those generators ship a meta description over Google's 155-char
display limit — found only when scripts/seo_check.py's title/meta-desc check
was extended from blog-only to every deployed HTML file (technical SEO
audit, 2026-08-11). scripts/seo_check.py is the permanent guard that catches
a regression here; this module is the one place the fix itself lives, so
every current and future generator imports the same behaviour instead of
re-implementing (and re-breaking) it.

Usage:
    from seo_meta import seo_title, seo_meta_description
    title = seo_title(f"{name} Review 2026")
    desc = seo_meta_description(f"Full description of {name}...")
"""

from __future__ import annotations

from datetime import datetime, timezone


def current_month_year() -> str:
    """Return e.g. 'August 2026' — always the real date at call time.

    Single source of truth for every "Updated <Month Year>" / "Reviewed
    <Month Year>" freshness string across generators, so none of them can
    drift back into a hardcoded month that goes stale (found 2026-08-16:
    'June 2026' was still hardcoded in 6 generators, 238 deployed pages,
    two months after it was first written).
    """
    return datetime.now(timezone.utc).strftime("%B %Y")


def current_year() -> str:
    """Return e.g. '2026' — always the real year at call time."""
    return str(datetime.now(timezone.utc).year)


def current_iso_date() -> str:
    """Return e.g. '2026-08-16' — for dateModified fields with no real edit tracking."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# Words that read as an incomplete sentence fragment when they land as the
# very last word of a truncated title/excerpt — "...Man Utd's Rebuild, and"
# is a valid word-boundary cut (no word split in half) but still an obviously
# dangling, ungrammatical ending. Found live 2026-08-21 across ~190 blog
# posts, all produced by truncation code that only ever checked the former.
# Covers English (primary — this is what every editorial title/excerpt is
# authored in) plus the short function words most likely to end a truncated
# fr/de/es/pt translated title, since translations are truncated through
# this same seo_title() call.
DANGLING_TRAILING_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "nor", "so", "yet",
    "to", "of", "in", "on", "at", "by", "for", "with", "from", "as",
    "is", "are", "was", "were", "be", "been", "being",
    "that", "this", "these", "those", "its", "it's", "his", "her", "their",
    "our", "your", "my", "what's", "who's", "there's", "which", "who",
    "whom", "whose", "when", "where", "while",
    "de", "du", "des", "la", "le", "les", "et", "un", "une", "au", "aux", "en", "dans",
    "der", "die", "das", "und", "ein", "eine", "im", "mit", "von", "zu", "für",
    "el", "los", "las", "y", "con", "para", "por",
    "o", "os", "as", "e", "um", "uma", "com",
})

# Two-word endings that LOOK like a dangling preposition/particle but are
# actually complete phrasal verbs in this site's own transfer-news headline
# style ("Savinho Talks On", "Rodri Saga Rolls On") — checked before the
# single-word rule above so these don't get trimmed into "Savinho Talks",
# which reads just as incomplete as the bug this function exists to fix.
_SAFE_TRAILING_PHRASES = frozenset({
    "talks on", "rolls on", "moves on", "carries on", "goes on",
    "reads on", "presses on", "battles on", "drags on", "lives on",
})


def _is_dangling_last_word(words: list[str]) -> bool:
    """A trailing word counts as dangling if it's a known function word, or
    if it's ANY possessive ("Nigeria's", "Man Utd's") — a possessive with
    nothing after it always implies the noun that got cut off, regardless of
    whether the specific word is on a hardcoded list. Exempts the small set
    of complete phrasal-verb endings in _SAFE_TRAILING_PHRASES.
    """
    if len(words) >= 2:
        bigram = " ".join(w.strip(" ,.;:!?’‘'“”\"").lower() for w in words[-2:])
        if bigram in _SAFE_TRAILING_PHRASES:
            return False
    word = words[-1]
    bare = word.strip(" ,.;:!?—–-&’‘'“”\"").lower()
    # A "word" that's pure punctuation once stripped (a trailing standalone
    # em/en dash left over from "...ACCA — with the" after "with"/"the" are
    # popped, or a bare "&" implying an uncompleted "X & Y" list) is exactly
    # as dangling-looking as a bare stopword.
    if not bare:
        return True
    if bare in DANGLING_TRAILING_WORDS:
        return True
    return word.rstrip(" ,.;:!?\"").endswith(("'s", "’s", "s'", "s’"))


def strip_dangling_words(text: str, max_trims: int = 4) -> str:
    """Drop a trailing run of conjunctions/articles/prepositions/possessives
    so truncated text never ends mid-thought.

    Word-boundary truncation ("never split a word in half") is a different
    guarantee than "reads as a complete phrase" — this closes that gap.
    Capped at `max_trims` so a title that is coincidentally almost all
    function words (effectively never happens in practice) can't be trimmed
    down to nothing; `len(words) > 3` is the same safety net from the other
    direction.
    """
    words = text.split(" ")
    trims = 0
    while len(words) > 3 and trims < max_trims and _is_dangling_last_word(words):
        words.pop()
        trims += 1
    return " ".join(words).rstrip(" ,;:—–-&")


def ends_with_dangling_word(text: str) -> bool:
    """True if `text` ends on a bare conjunction/article/preposition/possessive
    fragment (ignoring a trailing ellipsis) — the detection half of
    strip_dangling_words(), for use in audits that need to flag this without
    necessarily rewriting the text themselves.
    """
    words = text.strip().rstrip(".…").split(" ")
    if not words or not words[-1]:
        return False
    return _is_dangling_last_word(words)


def seo_title(title: str, max_len: int = 60, suffix: str = "| SifuFinds") -> str:
    """Return a <= max_len char <title> string with a '| SifuFinds'-style suffix.

    Plain word-boundary truncation from the tail, then strip_dangling_words()
    to avoid ending on a dangling function word. An earlier version of this
    function special-cased truncating at a ' — '/' - '/': '/' | ' separator
    and keeping only the text *before* it, on the theory that a short generic
    lead-in ("World Cup 2026:") swallowing the whole truncation was the risk
    to guard against (GEO/technical audit 2026-07-26). That shortcut is
    removed: for the very common "Tournament Year: specific match detail"
    title shape, the distinguishing text sits *after* the separator, so
    keeping only the prefix reintroduced the exact collapse it was meant to
    prevent — confirmed live 2026-08-21 on translated World Cup posts, where
    two different French match reports both truncated to the identical
    "Coupe du Monde 2026 | SifuFinds" and tripped scripts/audit_titles.py's
    duplicate-<title> gate. Tail-based truncation can't collapse two
    different titles onto one shared generic prefix the same way, since each
    title is cut at a point determined by its own full length, not by the
    position of its first separator.
    """
    full = f"{title} {suffix}"
    if len(full) <= max_len:
        return full
    available = max_len - len(suffix) - 1
    truncated = strip_dangling_words(title[:available].rsplit(" ", 1)[0])
    return f"{truncated} {suffix}"


def seo_meta_description(text: str, max_len: int = 155) -> str:
    """Clean word-boundary truncation to <= max_len chars, no ellipsis.

    Meant for meta descriptions (default 155, Google's display limit) and
    Open Graph descriptions (pass max_len=200-300, which social platforms
    tolerate before truncating themselves). Also runs strip_dangling_words()
    so a truncated description never ends on a dangling function word — see
    that function's docstring for why word-boundary truncation alone isn't
    enough.
    """
    if len(text) <= max_len:
        return text
    truncated = text[:max_len].rsplit(" ", 1)[0].rstrip(".,;:—- ")
    return strip_dangling_words(truncated)
