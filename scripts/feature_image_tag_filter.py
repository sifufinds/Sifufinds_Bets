#!/usr/bin/env python3
"""Pure-stdlib tag-candidate filter for blog feature-image generation.

Split out of generate_blog_feature_image.py (2026-07-27) purely so
scripts/validate_site.py — the pre-deploy gate, which must run with zero
third-party dependencies since the deploy workflow never installs any pip
packages before running it — can import the actual filtering logic for its
CHECK 4 regression guard without dragging in Pillow. generate_blog_feature_image.py
needs Pillow for the image compositing itself; this module needs nothing
but `re`, so it must never gain a dependency beyond the standard library.

See generate_blog_feature_image.py's module docstring and the 2026-07-27
AGENT-KNOWLEDGE.md entry for the incident this filter exists to prevent.
"""
from __future__ import annotations

import re

# Words that show up in tags but never identify a specific player, team, or
# person on their own — a tag consisting entirely of these (e.g. "Transfers",
# "Value Bets", "World Cup 2026") must never reach an image search: a loose
# query on a word like "Transfers" returns some plausible-but-wrong football
# photo (verified during testing — it surfaced an unrelated player illustrating
# the general concept of a transfer), which is a worse failure than no photo.
_GENERIC_TAG_WORDS = {
    "transfer", "transfers", "betting", "bet", "bets", "tips", "tip", "odds",
    "preview", "previews", "review", "reviews", "news", "update", "updates",
    "latest", "value", "bonus", "bonuses", "guide", "guides", "best", "top",
    "market", "markets", "africa", "african", "football", "soccer",
    "basketball", "cricket", "tennis", "rugby", "boxing", "sport", "sports",
    "match", "matches", "live", "score", "scores", "game", "games", "week",
    "today", "stage", "group", "world", "cup", "final", "finals", "season",
    "league", "fan", "fans", "analysis", "prediction", "predictions",
    "result", "results", "comparison", "deposit", "withdrawal", "welcome",
    "free", "app", "apps", "site", "sites", "",
}

# Governing bodies, confederations, and competition/ranking brand names are a
# *different* hazard from the generic descriptive words above: these are real,
# specific proper nouns, so the generic-word check alone lets them straight
# through as "entity" candidates. But unlike a player or club, none of them
# corresponds to a single stable photo — the same acronym or brand spans many
# unrelated tournaments, editions, and genders (FIFA alone governs the Men's
# World Cup, the Women's World Cup, U-20s, futsal, and more). Both photo tiers
# are also too permissive for a bare acronym like this: fetch_entity_photo()'s
# Wikipedia description check treats "governing body of association football"
# as a football-context match, and search_news_photo()'s title-matching only
# requires the literal word to appear somewhere in a result's title — which is
# true of nearly any football article ever written. That combination is
# exactly how a live post went out with a "FIFA WOMEN'S WORLD CUP AU NZ 2023"
# tournament graphic as the feature image for a Men's World Ranking article
# (caught 2026-07-27, /blog/fifa-world-ranking-2026-spain-top-morocco-lead-africa/,
# tags included the bare "FIFA" and "World Ranking"). Blocking these names at
# the source — before either photo tier ever runs a query — is far cheaper and
# more reliable than trying to make the search itself edition/gender-aware.
_ORG_AND_COMPETITION_WORDS = {
    "fifa", "uefa", "caf", "concacaf", "conmebol", "afc", "ofc",
    "afcon", "can", "chan", "nba", "nfl", "nhl", "mlb", "mls",
    "icc", "atp", "wta", "itf", "fia", "ioc", "fifpro",
    "premier", "championship", "championships", "ranking", "rankings",
    "qualifier", "qualifiers", "qualifying", "playoff", "playoffs",
    "confederation", "federation", "association", "governing", "body",
    "olympics", "olympic", "champions", "europa", "bundesliga",
    "eredivisie", "seria", "serie", "liga", "ligue", "la",
}

_BLOCKED_TAG_WORDS = _GENERIC_TAG_WORDS | _ORG_AND_COMPETITION_WORDS

# _BLOCKED_TAG_WORDS above only rejects a tag when EVERY word in it is
# generic (AND-logic) — deliberately, since a real entity tag can legitimately
# contain one clean word ('Chelsea'). That AND-based rule still let tournament
# names straight through the moment they carried one incidental proper-noun-
# shaped word alongside a competition word: 'African Cup of Nations' has
# 'African' and 'Cup' blocked, but 'of' and 'Nations' weren't, so the tag as a
# whole wasn't "every word generic" and passed; same story for 'T20 World Cup'
# ('t20' unblocked) and 'Queen's Club Championship' ('queen's'/'club'
# unblocked). Caught via a full scan of every tag actually in posts.json
# (2026-07-27) after the FIFA/Morocco incident — this is a distinct, stronger
# rule: ANY of these words appearing ANYWHERE in a tag disqualifies the whole
# tag as a photo-search candidate, regardless of what else rides along with
# it, because every word here names a tournament *format*, never a specific
# team/player/country. 'super' is deliberately excluded even though it names
# competitions ('Super League') — Nigeria's own 'Super Eagles' nickname would
# also die under an OR-rule on that word, and that's a real, frequently-used,
# perfectly safe tag; 'Super League' is still caught because 'league' alone
# is enough.
_COMPETITION_STRUCTURE_WORDS = {
    "cup", "league", "championship", "championships", "trophy", "trophies",
    "open", "masters", "prix", "bowl", "slam", "slams", "playoffs", "playoff",
    "qualifier", "qualifiers", "qualifying", "nations", "finals", "final",
    "conference", "division", "t20", "odi", "series", "invitational",
    "classic", "tour", "grand", "games",
}


def _tokenize(name: str) -> list[str]:
    """Splits a tag into words on whitespace AND hyphens — a hyphenated tag
    like 'world-cup-2026' previously came through as a single glued token
    ('worldcup2026') that matched nothing in any blocklist, silently
    bypassing every word-level check below."""
    return [w for w in re.split(r"[\s\-]+", name.strip()) if w]


def _is_competition_reference(name: str) -> bool:
    words = {re.sub(r"[^a-z0-9]", "", w.lower()) for w in _tokenize(name)}
    return bool(words & _COMPETITION_STRUCTURE_WORDS)


def _looks_like_entity_candidate(name: str) -> bool:
    """False for a purely generic, governing-body, or competition-brand tag;
    true otherwise — i.e. the tag has at least one word that could plausibly
    be part of a proper name for a specific player, club, or country ('Real
    Madrid', 'Marc Cucurella', 'Chelsea', 'Morocco').

    Two independent rejection rules: every word is generic/org-level (see
    _GENERIC_TAG_WORDS / _ORG_AND_COMPETITION_WORDS — AND-logic, tolerates
    one clean proper-noun word), or the tag references a tournament format
    at all (see _COMPETITION_STRUCTURE_WORDS — OR-logic, stricter, added
    after real tournament tags still slipped past the first rule alone)."""
    words = _tokenize(name)
    if not words:
        return False
    if _is_competition_reference(name):
        return False
    normalized = {re.sub(r"[^a-z]", "", w.lower()) for w in words}
    return not normalized <= _BLOCKED_TAG_WORDS
