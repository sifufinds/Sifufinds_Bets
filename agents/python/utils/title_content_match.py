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
# Deliberately does NOT include a generic "africa...transfer" proximity
# fallback — an earlier version of this regex had one, and it false-matched
# legitimate audience framing like "transfer news for African bettors"
# (fine) as if it were "Transfer Frenzy in Africa" (not fine). Only these
# three explicit shapes are treated as a claim about the subject.
_FALSE_AFRICA_CLAIM_RE = re.compile(
    r"\b(transfer|club|star|footballer|player|squad|deal|window)s?\b.{0,25}\bin africa\b"
    r"|\bafrica'?s\b.{0,30}\b(transfer|club|star|footballer|player|window|deal)"
    r"|\bafrican\b.{0,20}\b(transfer|club|footballer|window|star)s?\b"
    # Bare "africa" directly adjacent to a subject noun (no word in between)
    # — e.g. "africa transfer window". Deliberately requires direct
    # adjacency rather than a proximity gap: a gap version previously
    # false-matched legitimate audience framing like "transfer news for
    # African bettors", where a word (bettors/punters) sits between
    # "africa" and any subject noun.
    r"|\bafrica\s+(transfer|club|star|footballer|player|window|deal)s?\b",
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


def check_africa_framing(title: str, slug: str, body: str) -> str | None:
    """Return a violation message if title/slug falsely claim an African
    transfer/club story, or None if the post is fine.

    A post is only flagged when BOTH: (1) the title or slug makes an
    explicit claim the story/clubs/window are African, AND (2) the body
    genuinely names no real African country, league, or competition. Posts
    that only mention "African bettors"/"African punters" as the audience
    never match (1), so this cannot false-positive on ordinary betting-angle
    copy — see BETTING_ANGLES/AFRICAN CONTEXT in agent_sports_blog.py, which
    every post legitimately carries regardless of which clubs are involved.
    """
    # Checked separately, never concatenated — concatenating "...African
    # Bettors" (end of title) with "transfer window..." (start of slug)
    # created a false cross-boundary match ("African Bettors transfer
    # window") for a title that never actually made an Africa claim.
    slug_as_words = slug.replace('-', ' ')
    if not _FALSE_AFRICA_CLAIM_RE.search(title) and not _FALSE_AFRICA_CLAIM_RE.search(slug_as_words):
        return None
    if mentions_real_africa_entity(body):
        return None
    return (
        f"Title/URL claims an African transfer/club story ({title!r}) but "
        f"the body names no real African country, league, or competition — "
        f"this looks like European/global transfer news mislabelled as "
        f"African. See CLAUDE.md's SEO self-healing table, 'Title/URL "
        f"claims a topic the content never delivers' row."
    )
