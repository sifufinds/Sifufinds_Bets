"""Generate bookmakers/winwinbet/index.html (WinWinBet review/profile page).

Added 2026-11-09 when WinWinBet was onboarded for Nigeria, Kenya, Ghana, South Africa,
Tanzania, Zambia, Ethiopia, Côte d'Ivoire, Cameroon, Senegal, Egypt, Morocco, Benin and Congo. Reuses the shared bookmaker page template
(agents/python/utils/bookmaker_page_template.py) so the page matches every
other bookmaker profile, then post-processes the few spots that template
hard-codes for a brand with NO commercial relationship (disclosure wording,
"Not an affiliate link", plain-text CTA) because WinWinBet is a promoted partner
with the SIFUKAI promo code.

Only facts the owner supplied are asserted (headline welcome offer, promo
code, the seven target countries). Licensing, payment methods, minimum deposit
and wagering terms are deliberately NOT stated: the page says they are
unverified. Re-run after changing WINWINBET_CTA_URL or the facts below:

    python3 scripts/gen_winwinbet_page.py

WINWINBET_CTA_URL is the masked link (.htaccess "AFFILIATE LINK MASKING" block);
swap the real affiliate URL in .htaccess, never here.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agents" / "python"))

from utils.bookmaker_page_template import render_bookmaker_page  # noqa: E402

WINWINBET_CTA_URL = "https://sifufinds.com/winwinbet"
PROMO_CODE = "SIFUKAI"
CTA_LABEL = "CLAIM BONUS NOW"
ASSET_DIR = "../../assets/banners/winwinbet"

COUNTRY_PAGES = [
    ("Nigeria", "best-betting-in-nigeria"),
    ("Kenya", "best-betting-in-kenya"),
    ("Ghana", "best-betting-in-ghana"),
    ("South Africa", "best-betting-in-south-africa"),
    ("Tanzania", "best-betting-in-tanzania"),
    ("Zambia", "best-betting-in-zambia"),
    ("Ethiopia", "best-betting-in-ethiopia"),
    ("Côte d'Ivoire", "best-betting-in-ivory-coast"),
    ("Cameroon", "best-betting-in-cameroon"),
    ("Senegal", "best-betting-in-senegal"),
    ("Egypt", "best-betting-in-egypt"),
    ("Morocco", "best-betting-in-morocco"),
    ("Benin", "best-betting-in-benin"),
    ("Congo-Brazzaville", "best-betting-in-congo-brazzaville"),
]

FACTS = {
    "slug": "winwinbet",
    "brand_name": "WinWinBet",
    "primary_country": "Nigeria",
    "official_url": "https://winwin.bet/",
    "rating": 3.0,
    "welcome_bonus_summary": (
        f"Sports and casino welcome offer with promo code {PROMO_CODE}. "
        "The bonus amount and wagering terms vary by country, so confirm them on the official site before depositing."
    ),
    "licensing_status": (
        "Third-party reviews describe a Curaçao licence; SifuFinds has not independently verified it "
        "or local licensing in each market."
    ),
    "payment_methods": [],
    "pros": [
        "Sportsbook and casino under one account",
        f"SifuFinds promo code {PROMO_CODE} shown on every WinWinBet offer",
    ],
    "cons": [
        "Availability, licensing and payment methods differ by country and have not yet been independently verified by SifuFinds",
        "Bonus amount, wagering requirements, minimum deposit and expiry are not confirmed here, and third-party sources disagree on them, so check the official site first",
        "A Curaçao licence, if held, is an offshore licence and does not replace local regulation in markets that license operators themselves",
    ],
    "faqs": [
        {
            "q": "What is the WinWinBet welcome bonus?",
            "a": f"WinWinBet promotes a sports and casino welcome offer for new players who register with promo code {PROMO_CODE}. SifuFinds has not confirmed the exact deposit match, wagering requirements or expiry, and review sites quote different figures, so read the terms on WinWinBet's official site for your country before you deposit.",
        },
        {
            "q": "Which countries does SifuFinds list WinWinBet for?",
            "a": "SifuFinds lists WinWinBet for Nigeria, Kenya, Ghana, South Africa, Tanzania, Zambia, Ethiopia, Côte d'Ivoire, Cameroon, Senegal, Egypt, Morocco, Benin and Congo-Brazzaville. Availability and licensing in each market have not been independently verified yet, so check that WinWinBet accepts players in your country before registering.",
        },
        {
            "q": "Is there a WinWinBet promo code?",
            "a": f"Yes. SifuFinds' WinWinBet promo code is {PROMO_CODE}. Enter it at registration to be eligible for the welcome offer, subject to WinWinBet's own terms and conditions.",
        },
    ],
    "verdict_paragraph": (
        "WinWinBet is a new SifuFinds listing, so this page makes no claims about its licensing, payout speed, "
        "customer service or payment methods beyond what has been verified. What is confirmed is that it offers "
        f"sports betting and casino play and that SifuFinds' promo code is {PROMO_CODE}. Treat it as an "
        "operator to check carefully: confirm it is available in your country, read the full bonus terms, "
        "and only gamble what you can afford to lose. 18+ only."
    ),
}


def _banner_block() -> str:
    return (
        f'<a href="{WINWINBET_CTA_URL}" target="_blank" rel="noopener noreferrer sponsored" '
        'style="display:block;text-align:center;margin:12px 0">'
        f'<img src="{ASSET_DIR}/winwinbet-728x90.png" width="728" height="89" loading="lazy" '
        'style="max-width:100%;height:auto;border-radius:8px" '
        f'alt="WinWinBet sports and casino, promo code {PROMO_CODE}"></a>'
    )


def _logo_block() -> str:
    return (
        f'<img src="{ASSET_DIR}/winwinbet-logo-on-black.png" width="300" height="45" '
        'style="max-width:100%;height:auto;border-radius:8px;display:block;margin:0 0 10px" '
        'alt="WinWinBet logo">'
    )


def _country_links_block() -> str:
    items = "".join(f'<li><a href="../../{slug}/">Best betting sites in {name}</a></li>' for name, slug in COUNTRY_PAGES)
    return (
        '<div class="cbox2"><h2>Where SifuFinds lists WinWinBet</h2>'
        "<p>WinWinBet appears in the bookmaker comparisons for these countries. Availability has not been "
        "independently verified in each market, so confirm it on WinWinBet's official site.</p>"
        f'<ul style="line-height:1.9;padding-left:18px">{items}</ul></div>'
    )


META_DESCRIPTION = (
    f"WinWinBet review by SifuFinds: sports and casino with promo code {PROMO_CODE}. "
    "Licensing and terms vary by country."
)


def _short_meta(html: str) -> str:
    """The shared template concatenates bonus + licensing + disclaimer into one 266-char
    description (limit 155). Replace the description/og/twitter copies with a short one."""
    import re
    for attr, key in (("name", "description"), ("property", "og:description"), ("name", "twitter:description")):
        html = re.sub(
            rf'(<meta\s+{attr}="{re.escape(key)}"\s+content=")[^"]*(")',
            lambda m: m.group(1) + META_DESCRIPTION + m.group(2),
            html,
        )
    return html


def build() -> str:
    html = _short_meta(render_bookmaker_page(FACTS))
    official = FACTS["official_url"]

    old_adv_start = html.index('<div class="adv">')
    old_adv_end = html.index("</div>", old_adv_start) + len("</div>")
    html = (
        html[:old_adv_start]
        + '<div class="adv">📢 <strong>Advertiser Disclosure:</strong> SifuFinds may earn commission if you sign up '
        "via our links. This does not affect our ratings. Always check WinWinBet's official site for current T&amp;Cs.</div>"
        + html[old_adv_end:]
    )

    html = html.replace(
        f'href="{official}" target="_blank" rel="noopener noreferrer">Visit WinWinBet Official Site →</a>',
        f'href="{WINWINBET_CTA_URL}" target="_blank" rel="noopener noreferrer sponsored">{CTA_LABEL} →</a>',
    )
    html = html.replace("Not an affiliate link · T&amp;Cs apply · 18+ only", "Advertising link · T&amp;Cs apply · 18+ only")
    html = html.replace(
        "<h3>ℹ️ WinWinBet — Welcome Offer</h3>",
        "<h3>🎁 WinWinBet — Welcome Offer</h3>" + _logo_block(),
    )
    claim_end = html.index('<div class="cbox2">')
    html = html[:claim_end] + _banner_block() + _country_links_block() + html[claim_end:]
    return html


def main() -> None:
    out = ROOT / "bookmakers" / "winwinbet" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    html = build()
    assert WINWINBET_CTA_URL in html and "Not an affiliate link" not in html
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
