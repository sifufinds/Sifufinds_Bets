"""
Affiliate link masking + CTA helpers — shared by every social posting agent.

Raw affiliate tracking URLs (e.g. https://reffpa.com/L?tag=d_3805082m_97c_&site=...)
look spammy and untrustworthy when pasted into a tweet or Facebook caption, and
readers rightly hesitate to click them. Every bookmaker gets a clean masked URL
instead — https://sifufinds.com/<brand-slug> — that 301-redirects to the real
affiliate link via the "AFFILIATE LINK MASKING" block in .htaccess.

Rule: whenever an affiliate link is shared on any social platform, it must be
the masked sifufinds.com/<brand> URL, never the raw tracking URL, and it must
be presented as a CTA ("BET NOW" / "CLAIM BONUS NOW" / "FREE BETS"), not a
generic "click here" or the bare brand name.

If you add a new brand or change which URL an existing masked slug points to,
add/update the matching RewriteRule in .htaccess in the same change — the two
must stay in sync or the masked link 404s.
"""
import re

SITE_URL = "https://sifufinds.com"

# Explicit slug per brand (not auto-derived) so the masked URL always matches
# the .htaccess RewriteRule exactly, even if a display name ever changes.
BRAND_SLUGS: dict[str, str] = {
    "fairpari": "fairpari",
    "1xbet": "1xbet",
    "linebet": "linebet",
    "melbet": "melbet",
    "betwinner": "betwinner",
    "helabet": "helabet",
    "paripesa": "paripesa",
    "bet9ja": "bet9ja",
    "sportybet": "sportybet",
    "betking": "betking",
    "betway": "betway",
    "hollywoodbets": "hollywoodbets",
    "betika": "betika",
    "sportpesa": "sportpesa",
    "mozzartbet": "mozzartbet",
    "nairabet": "nairabet",
    "22bet": "22bet",
    "betpawa": "betpawa",
    "odibets": "odibets",
    "supabets": "supabets",
    "bangbet": "bangbet",
    "rasbet": "rasbet",
    "mebet": "mebet",
    "tictacbet": "tictacbet",
    "tictacbets": "tictacbet",
    "betxchange": "betxchange",
    "bettabets": "bettabets",
    "bettabet": "bettabets",
    "playbet": "playbet",
}

CTA_FREE_BETS = "FREE BETS"
CTA_CLAIM_BONUS = "CLAIM BONUS NOW"
CTA_BET_NOW = "BET NOW"


def _brand_key(brand_name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", brand_name.lower())


def brand_slug(brand_name: str) -> str:
    key = _brand_key(brand_name)
    return BRAND_SLUGS.get(key, key)


def masked_url(brand_name: str) -> str:
    """Clean, friendly link for sharing — sifufinds.com/<brand> — never the
    raw affiliate tracking URL. Must have a matching RewriteRule in .htaccess."""
    return f"{SITE_URL}/{brand_slug(brand_name)}"


def pick_cta(brand: dict) -> str:
    """Choose the CTA phrase that actually matches the offer, never a label
    that overstates or misdescribes it."""
    text = f"{brand.get('welcome', '')} {brand.get('bonus_highlight', brand.get('highlight', ''))}".lower()
    if "no deposit" in text or "free bet" in text:
        return CTA_FREE_BETS
    if "bonus" in text or "deposit" in text:
        return CTA_CLAIM_BONUS
    return CTA_BET_NOW


def cta_html(brand: dict, label: str | None = None) -> str:
    """Real clickable hyperlink for platforms that render HTML (Telegram
    parse_mode=HTML) — the CTA phrase itself is the anchor text."""
    cta = label or pick_cta(brand)
    return f'<a href="{masked_url(brand["name"])}">{cta}</a>'


def cta_plain(brand: dict, label: str | None = None) -> str:
    """Plain-text platforms (Facebook captions, X, Instagram) can't render
    custom anchor text, so the CTA phrase precedes the masked link instead."""
    cta = label or pick_cta(brand)
    return f"{cta} → {masked_url(brand['name'])}"
