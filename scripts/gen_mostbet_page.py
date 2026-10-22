"""Generate bookmakers/mostbet/index.html (MostBet review/profile page).

Added 2026-10-21 when MostBet was onboarded for Kenya, Ghana, Tanzania, Egypt,
Morocco, Côte d'Ivoire and Benin. Reuses the shared bookmaker page template
(agents/python/utils/bookmaker_page_template.py) so the page matches every
other bookmaker profile, then post-processes the few spots that template
hard-codes for a brand with NO commercial relationship (disclosure wording,
"Not an affiliate link", plain-text CTA) because MostBet is a promoted partner
with the SIFUKAI promo code.

Only facts the owner supplied are asserted (headline welcome offer, promo
code, the seven target countries). Licensing, payment methods, minimum deposit
and wagering terms are deliberately NOT stated: the page says they are
unverified. Re-run after changing MOSTBET_CTA_URL or the facts below:

    python3 scripts/gen_mostbet_page.py

MOSTBET_CTA_URL is the masked link (.htaccess "AFFILIATE LINK MASKING" block);
swap the real affiliate URL in .htaccess, never here.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agents" / "python"))

from utils.bookmaker_page_template import render_bookmaker_page  # noqa: E402

MOSTBET_CTA_URL = "https://sifufinds.com/mostbet"
PROMO_CODE = "SIFUKAI"
CTA_LABEL = "CLAIM BONUS NOW"
ASSET_DIR = "../../assets/banners/mostbet"

COUNTRY_PAGES = [
    ("Kenya", "best-betting-in-kenya"),
    ("Ghana", "best-betting-in-ghana"),
    ("Tanzania", "best-betting-in-tanzania"),
    ("Egypt", "best-betting-in-egypt"),
    ("Morocco", "best-betting-in-morocco"),
    ("Côte d'Ivoire", "best-betting-in-ivory-coast"),
    ("Benin", "best-betting-in-benin"),
]

FACTS = {
    "slug": "mostbet",
    "brand_name": "MostBet",
    "primary_country": "Kenya",
    "official_url": "https://mostbet.com/",
    "rating": 3.0,
    "welcome_bonus_summary": (
        f"Welcome bonus up to 150% + 250 free spins with promo code {PROMO_CODE}. "
        "Confirm the current terms for your country before depositing."
    ),
    "licensing_status": "Licensing not yet independently verified in each market.",
    "payment_methods": [],
    "pros": [
        "Welcome offer of up to 150% plus 250 free spins",
        f"SifuFinds promo code {PROMO_CODE} shown on every MostBet offer",
    ],
    "cons": [
        "Availability, licensing and payment methods differ by country and have not yet been independently verified by SifuFinds",
        "Wagering requirements, minimum deposit and bonus expiry are not confirmed here, so check them on the official site first",
    ],
    "faqs": [
        {
            "q": "What is the MostBet welcome bonus?",
            "a": f"MostBet advertises a welcome bonus of up to 150% plus 250 free spins for new players who register with promo code {PROMO_CODE}. The exact deposit match, wagering requirements and expiry can differ by country, so confirm the terms on MostBet's official site before you deposit.",
        },
        {
            "q": "Which countries does SifuFinds list MostBet for?",
            "a": "SifuFinds lists MostBet for Kenya, Ghana, Tanzania, Egypt, Morocco, Côte d'Ivoire and Benin. Availability and licensing in each market have not been independently verified yet, so check that MostBet accepts players in your country before registering.",
        },
        {
            "q": "Is there a MostBet promo code?",
            "a": f"Yes. SifuFinds' MostBet promo code is {PROMO_CODE}. Enter it at registration to be eligible for the welcome offer, subject to MostBet's own terms and conditions.",
        },
    ],
    "verdict_paragraph": (
        "MostBet is a new SifuFinds listing, so this page makes no claims about its licensing, payout speed, "
        "customer service or payment methods beyond what has been verified. What is confirmed is the welcome "
        f"offer headline (up to 150% plus 250 free spins) and the promo code {PROMO_CODE}. Treat it as an "
        "operator to check carefully: confirm it is available in your country, read the full bonus terms, "
        "and only gamble what you can afford to lose. 18+ only."
    ),
}


def _banner_block() -> str:
    return (
        f'<a href="{MOSTBET_CTA_URL}" target="_blank" rel="noopener noreferrer sponsored" '
        'style="display:block;text-align:center;margin:12px 0">'
        f'<img src="{ASSET_DIR}/mostbet-welcome-728x90.png" width="728" height="90" loading="lazy" '
        'style="max-width:100%;height:auto;border-radius:8px" '
        f'alt="MostBet welcome bonus up to 150% plus 250 free spins, promo code {PROMO_CODE}"></a>'
    )


def _logo_block() -> str:
    return (
        f'<img src="{ASSET_DIR}/mostbet-logo-on-white-1200x400.png" width="300" height="100" '
        'style="max-width:100%;height:auto;border-radius:8px;display:block;margin:0 0 10px" '
        'alt="MostBet logo">'
    )


def _country_links_block() -> str:
    items = "".join(f'<li><a href="../../{slug}/">Best betting sites in {name}</a></li>' for name, slug in COUNTRY_PAGES)
    return (
        '<div class="cbox2"><h2>Where SifuFinds lists MostBet</h2>'
        "<p>MostBet appears in the bookmaker comparisons for these countries. Availability has not been "
        "independently verified in each market, so confirm it on MostBet's official site.</p>"
        f'<ul style="line-height:1.9;padding-left:18px">{items}</ul></div>'
    )


def build() -> str:
    html = render_bookmaker_page(FACTS)
    official = FACTS["official_url"]

    old_adv_start = html.index('<div class="adv">')
    old_adv_end = html.index("</div>", old_adv_start) + len("</div>")
    html = (
        html[:old_adv_start]
        + '<div class="adv">📢 <strong>Advertiser Disclosure:</strong> SifuFinds may earn commission if you sign up '
        "via our links. This does not affect our ratings. Always check MostBet's official site for current T&amp;Cs.</div>"
        + html[old_adv_end:]
    )

    html = html.replace(
        f'href="{official}" target="_blank" rel="noopener noreferrer">Visit MostBet Official Site →</a>',
        f'href="{MOSTBET_CTA_URL}" target="_blank" rel="noopener noreferrer sponsored">{CTA_LABEL} →</a>',
    )
    html = html.replace("Not an affiliate link · T&amp;Cs apply · 18+ only", "Advertising link · T&amp;Cs apply · 18+ only")
    html = html.replace(
        "<h3>ℹ️ MostBet — Welcome Offer</h3>",
        "<h3>🎁 MostBet — Welcome Offer</h3>" + _logo_block(),
    )
    claim_end = html.index('<div class="cbox2">')
    html = html[:claim_end] + _banner_block() + _country_links_block() + html[claim_end:]
    return html


def main() -> None:
    out = ROOT / "bookmakers" / "mostbet" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    html = build()
    assert MOSTBET_CTA_URL in html and "Not an affiliate link" not in html
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
