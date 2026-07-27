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
#
# "wafcon"/"wsl"/"nwsl"/"uwcl" were added after a second, distinct incident
# the same day: a WAFCON (Women's Africa Cup of Nations) post shipped with a
# men's Nigeria squad photo, because "wafcon" itself wasn't blocked here AND
# — the deeper bug — a bare country tag alongside it ('Nigeria') silently
# defaulted to the men's team with no way to know the post was about a
# women's tournament (fixed separately in player_photo.qualify_entity_query /
# generate_blog_feature_image._post_is_womens_context). These acronyms don't
# literally contain "women" so the plain word-hint check elsewhere in the
# pipeline can't catch them; they belong here for the same reason FIFA/AFCON
# do — one acronym spans many editions/genders with no single stable photo.
_ORG_AND_COMPETITION_WORDS = {
    "fifa", "uefa", "caf", "concacaf", "conmebol", "afc", "ofc",
    "afcon", "can", "chan", "wafcon", "wsl", "nwsl", "uwcl",
    "nba", "nfl", "nhl", "mlb", "mls",
    "icc", "atp", "wta", "itf", "fia", "ioc", "fifpro",
    "premier", "championship", "championships", "ranking", "rankings",
    "qualifier", "qualifiers", "qualifying", "playoff", "playoffs",
    "confederation", "federation", "association", "governing", "body",
    "olympics", "olympic", "champions", "europa", "bundesliga",
    "eredivisie", "seria", "serie", "liga", "ligue", "la",
}

# News-outlet attribution tags (the content pipeline cites its own sources
# as tags, e.g. ['World Cup 2026', 'USA', 'Sky Sports', 'Guardian Sport']) —
# these name the outlet a fact was sourced from, never the article's actual
# subject, so a query for one would only ever return a broadcaster/publisher
# logo or an unrelated page, not a photo relevant to the post. None of these
# currently reach a search as any post's *first* candidate (verified via
# audit 2026-07-27), but blocking them outright removes the risk entirely
# for any post where every more-specific tag fails to resolve.
_NEWS_OUTLET_WORDS = {
    "sky", "guardian", "bbc", "espn", "talksport", "mirror", "90min",
    "goal", "independent", "teamtalk", "standard", "telegraph", "times",
}

# Sponsor/brand names the content pipeline sometimes tags a post with (kit
# manufacturers, game/console tie-ins) even though the brand is never the
# post's actual subject. Real incident (2026-07-27): an NBA/basketball post
# tagged ['NBA', 'Nike', 'Basketball Africa League', 'BAL', 'Nigeria', ...]
# tried 'Nike' as a photo-search candidate and got back an unrelated
# football photo (Nike sponsors far more football content than basketball),
# a wrong-sport mismatch on a basketball article.
_BRAND_SPONSOR_WORDS = {
    "nike", "adidas", "puma", "castore", "umbro", "reebok",
    "playstation", "xbox", "nvidia",
}

_BLOCKED_TAG_WORDS = (
    _GENERIC_TAG_WORDS | _ORG_AND_COMPETITION_WORDS | _NEWS_OUTLET_WORDS | _BRAND_SPONSOR_WORDS
)

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
# is enough. 'test' (cricket's Test-match format, alongside 't20'/'odi'
# already here) was added 2026-07-27 after the same-day WAFCON audit also
# turned up 'Test matches' ('matches' blocked, 'test' wasn't) resolving to
# an unrelated men's Test cricket photo on a Women's T20 World Cup post.
_COMPETITION_STRUCTURE_WORDS = {
    "cup", "league", "championship", "championships", "trophy", "trophies",
    "open", "masters", "prix", "bowl", "slam", "slams", "playoffs", "playoff",
    "qualifier", "qualifiers", "qualifying", "nations", "finals", "final",
    "conference", "division", "t20", "odi", "test", "series", "invitational",
    "classic", "tour", "grand", "games",
}


# Acronyms/short names for women's-only competitions that don't literally
# contain the word "women" (WAFCON = Women's Africa Cup of Nations, WSL =
# Women's Super League, NWSL/UWCL likewise) — plain substring matching on
# "women" misses these, and they're exactly the kind of tag that establishes
# a post's women's-football context without any individual country/team tag
# alongside them carrying that signal on its own. See
# _looks_like_womens_context's docstring for the incident this closes.
_WOMENS_ONLY_COMPETITION_ACRONYMS = ("wafcon", "wsl", "nwsl", "uwcl")

_WOMENS_CONTEXT_PATTERN = re.compile(
    r"\b(women'?s|womens|female|" + "|".join(_WOMENS_ONLY_COMPETITION_ACRONYMS) + r")\b",
    re.IGNORECASE,
)


def _looks_like_womens_context(*texts: str) -> bool:
    """True when the combined post text (title, excerpt, tags — any mix of
    strings the caller has on hand) is clearly about women's football, even
    though the individual candidate tag being resolved (a bare country name
    like 'Nigeria') carries no gender signal by itself.

    Root cause of a live incident (2026-07-27): a WAFCON (Women's Africa Cup
    of Nations) post tagged ['WAFCON', 'Nigeria', 'Morocco'] shipped with a
    men's Nigeria squad photo. Blocking 'wafcon' as a photo-search candidate
    (see _ORG_AND_COMPETITION_WORDS above) stops that acronym from being
    tried directly, but the very next candidate, 'Nigeria', is a bare
    country tag that agents/python/utils/player_photo.qualify_entity_query()
    has always defaulted to the men's national football team — and nothing
    upstream told it the post itself was about the women's tournament.
    generate_blog_feature_image.find_subject_photo() calls this once per
    post (scanning title + excerpt + every tag together, since the signal is
    often carried by a *different* tag than the one being qualified) and
    threads the result through to qualify_entity_query() as `womens_context`
    so the country resolves to the correct side."""
    return bool(_WOMENS_CONTEXT_PATTERN.search(" ".join(t or "" for t in texts)))


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
