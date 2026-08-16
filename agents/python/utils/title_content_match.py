"""Detects blog posts whose title/slug frames a transfer/football story as
African ("Transfer Frenzy in Africa", "Africa's Top Transfer Stories") when
the body never actually names a real African country, league, or
competition — i.e. the story is really about European/global clubs and the
"Africa" framing is a false claim about the content, not just marketing
flavour like "for African bettors".

Found 2026-08-16: a live post titled "Transfer Frenzy in Africa: Breaking
Down the Latest Deals and Their Impact on Odds" was entirely about West Ham,
Sunderland, Chelsea and Newcastle (English clubs) with zero African clubs,
players, or leagues mentioned anywhere in the body. A repo-wide audit the
same day found this same pattern recurring across multiple posts generated
by agent_sports_blog.py's "transfers" category — see CLAUDE.md's SEO
self-healing table and AGENT-KNOWLEDGE.md's 2026-08-16 entry for the full
incident. This module is the permanent, deterministic guard against it:
called both at generation time (agent_sports_blog.generate_post(), to hold
a bad draft back before it's ever published) and by scripts/seo_check.py
(as a regression tripwire scanning every existing post before deploy).

Deliberately regex/word-list based, not LLM based — the failure mode is a
concrete, checkable fact ("does the body name any real African place or
competition?"), not a judgement call, so a deterministic check is both
cheaper and more reliable than another LLM pass that could itself
hallucinate a pass/fail.
"""
import re

# Broader than utils/countries.py's 28 "promotable" markets on purpose — this
# is a detection list ("does the body mention a real African place?"), not a
# content-targeting list, so it deliberately also recognises the 5 countries
# that list excludes (Algeria, Libya, Mauritania, Somalia, Tunisia).
AFRICAN_COUNTRIES = [
    "Nigeria", "Kenya", "Ghana", "South Africa", "Tanzania", "Uganda", "Zambia",
    "Ethiopia", "Ivory Coast", "Cote d'Ivoire", "Côte d'Ivoire", "Cameroon",
    "Senegal", "Rwanda", "Zimbabwe", "Malawi", "Mozambique", "Angola",
    "DR Congo", "Botswana", "Namibia", "Egypt", "Morocco", "Sierra Leone",
    "Liberia", "Benin", "Burkina Faso", "Gambia", "Togo", "Congo-Brazzaville",
    "Algeria", "Tunisia", "Libya", "Mauritania", "Somalia",
]

# Demonym/adjectival forms ("Nigerian striker", "Ghanaian winger") — a body
# that names a player's nationality this way is a genuine African reference
# even though the country noun itself ("Nigeria") never appears. Found
# 2026-08-16: "Latest Transfer News: African Stars on the Move" named a real
# "Nigerian striker" (Tolu Arokodare to Ajax) but the plain country-name
# check missed it, since \bnigeria\b doesn't match inside "Nigerian".
AFRICAN_DEMONYMS = [
    "Nigerian", "Kenyan", "Ghanaian", "South African", "Tanzanian", "Ugandan",
    "Zambian", "Ethiopian", "Ivorian", "Cameroonian", "Senegalese", "Rwandan",
    "Zimbabwean", "Malawian", "Mozambican", "Angolan", "Congolese",
    "Motswana", "Namibian", "Egyptian", "Moroccan", "Sierra Leonean",
    "Liberian", "Beninese", "Burkinabe", "Gambian", "Togolese", "Algerian",
    "Tunisian", "Libyan", "Mauritanian", "Somali",
]

_AFRICAN_LEAGUES_RE = re.compile(
    r"\b(NPFL|KPL|PSL|GPL|CAF|AFCON|BAL|COSAFA|WAFCON|"
    r"Premier Soccer League|Kenyan Premier League|Ghana Premier League|"
    r"Basketball Africa League)\b",
    re.IGNORECASE,
)

# Matches a phrase that claims the STORY itself is African (clubs, players,
# the transfer window, etc.) — not phrases like "for African bettors"/
# "African punters" which describe the audience, not the subject, and are
# legitimate on every post regardless of which clubs are actually involved.
#
# Allows AT MOST ONE filler word between "africa(n)/africa's" and the
# subject noun (e.g. "African TOP clubs", "Africa's BIGGEST transfer", or
# "transfer FRENZY in Africa") in either direction. This one-word tolerance
# is deliberately narrow: an earlier version allowed a wide 20-30 char gap,
# which correctly caught headline phrasing ("Transfer Frenzy in Africa")
# but also false-matched real sentences like "African bettors follow the
# transfer market closely" — the gap didn't care that "bettors" (an
# audience noun, not a subject noun) was the actual word connecting them.
# Tightening to a single-word gap keeps every known headline case matching
# (there's rarely more than one filler word — "Frenzy"/"Top"/"Biggest" —
# between the claim and its subject) while rejecting sentences where an
# audience phrase ("bettors", "punters", "for African fans") sits in
# between. Verified against a 21-case suite spanning both title/slug
# phrasing and full body sentences — see AGENT-KNOWLEDGE.md's 2026-08-16
# entries for the false positives this replaced.
# Deliberately excludes "team"/"league" — those words are too broad for
# general sports content: "African teams" is routine, TRUE commentary on
# World Cup/AFCON coverage ("African teams have exited the tournament" is
# real, not a false claim), unlike "club"/"transfer"/"window" which rarely
# appear in a genuine collective-Africa sentence outside the exact false-
# claim pattern this module exists to catch. Found 2026-08-16: adding
# "team"/"league" (to catch one real violation's "African teams and
# leagues" phrasing, already fixed by hand) immediately false-flagged
# several legitimate World Cup recap posts once the check started scanning
# body sentences, not just titles.
#
# Also excludes "player" for the same reason, but a subtler collision: in
# betting copy "player" routinely means "bettor/gambler" ("African players
# often look for value in the 1.20-1.35 range"), not "footballer" — the
# word is genuinely ambiguous between the two senses and this module has no
# way to disambiguate them. "footballer" (unambiguous) stays in the list.
_SUBJECT_NOUNS = r"(transfer|club|star|footballer|squad|deal|window)s?"
_GAP = r"(\s+\S+)?"
_FALSE_AFRICA_CLAIM_RE = re.compile(
    rf"\b{_SUBJECT_NOUNS}{_GAP}\s+in africa\b"
    rf"|\bafrica'?s{_GAP}\s+{_SUBJECT_NOUNS}\b"
    rf"|\bafrican{_GAP}\s+{_SUBJECT_NOUNS}\b"
    # Bare "africa" (no possessive 's) directly/near a subject noun — e.g.
    # slug form "africa-transfer-window-2026" (-> "africa transfer window
    # 2026"), which has no apostrophe to match the "africa's" alternative.
    rf"|\bafrica{_GAP}\s+{_SUBJECT_NOUNS}\b",
    re.IGNORECASE,
)


def mentions_real_africa_entity(body: str) -> bool:
    """True if the body names an actual African country, league, or
    competition — i.e. the "African" framing in the title would be earned."""
    body_lower = body.lower()
    for name in AFRICAN_COUNTRIES + AFRICAN_DEMONYMS:
        if re.search(r"\b" + re.escape(name.lower()) + r"\b", body_lower):
            return True
    return bool(_AFRICAN_LEAGUES_RE.search(body))


def _first_body_claim(body: str) -> str | None:
    """Return the first body sentence that itself claims the story is
    African (e.g. "the transfer window in Africa is heating up", "African
    clubs are making some exciting moves"), or None.

    Found 2026-08-16, same day as the original incident: two posts whose
    TITLE had already been corrected still opened or closed with this exact
    claim baked into the prose — a title-only check never sees it. Split
    into sentences (rather than running the gap-based regex against the
    whole multi-paragraph body) so the `.{0,30}` proximity windows in
    _FALSE_AFRICA_CLAIM_RE can't accidentally bridge two unrelated
    sentences that happen to sit close together.
    """
    for sentence in re.split(r"(?<=[.!?])\s+", body):
        if _FALSE_AFRICA_CLAIM_RE.search(sentence):
            return sentence.strip()
    return None


def check_africa_framing(title: str, slug: str, body: str) -> str | None:
    """Return a violation message if the title, slug, or the body's own
    prose falsely claims an African transfer/club story, or None if the
    post is fine.

    A post is only flagged when BOTH: (1) the title, slug, or a body
    sentence makes an explicit claim the story/clubs/window/team/league are
    African, AND (2) the body genuinely names no real African country,
    league, or competition anywhere. Posts that only mention "African
    bettors"/"African punters" as the audience never match (1), so this
    cannot false-positive on ordinary betting-angle copy — see
    BETTING_ANGLES/AFRICAN CONTEXT in agent_sports_blog.py, which every post
    legitimately carries regardless of which clubs are involved.
    """
    # Checked separately, never concatenated — concatenating "...African
    # Bettors" (end of title) with "transfer window..." (start of slug)
    # created a false cross-boundary match ("African Bettors transfer
    # window") for a title that never actually made an Africa claim.
    slug_as_words = slug.replace('-', ' ')
    title_or_slug_claim = (
        _FALSE_AFRICA_CLAIM_RE.search(title) is not None
        or _FALSE_AFRICA_CLAIM_RE.search(slug_as_words) is not None
    )
    body_claim = _first_body_claim(body) if not title_or_slug_claim else None
    if not title_or_slug_claim and not body_claim:
        return None
    if mentions_real_africa_entity(body):
        return None
    if title_or_slug_claim:
        return (
            f"Title/URL claims an African transfer/club story ({title!r}) but "
            f"the body names no real African country, league, or competition — "
            f"this looks like European/global transfer news mislabelled as "
            f"African. See CLAUDE.md's SEO self-healing table, 'Title/URL "
            f"claims a topic the content never delivers' row."
        )
    return (
        f"Body claims an African transfer/club story ({body_claim!r}) but "
        f"names no real African country, league, or competition anywhere — "
        f"this looks like European/global transfer news mislabelled as "
        f"African. See CLAUDE.md's SEO self-healing table, 'Title/URL "
        f"claims a topic the content never delivers' row."
    )
