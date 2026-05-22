"""
SifuFinds bookmaker review generator.

Usage:
    python scripts/generate_review.py --brand "Bet9ja"
    python scripts/generate_review.py --brand "Sportybet" --country Nigeria
    python scripts/generate_review.py --list-brands
    python scripts/generate_review.py --batch  # writes all pending brands
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
BLOG_POSTS = REPO_ROOT.parent / "blog" / "posts.json"
BRAND_KB = REPO_ROOT / "knowledge" / "brand" / "brand-knowledge-base.json"
ARTICLES_DIR = REPO_ROOT / "knowledge" / "articles"
ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Brand catalogue — add new bookmakers here to queue them
# ---------------------------------------------------------------------------
BOOKMAKER_CATALOGUE: dict[str, dict] = {
    "Bet9ja": {
        "tagline": "Nigeria's Biggest Bookmaker – Est. 2013",
        "countries": ["Nigeria"],
        "welcome_offer": "100% first deposit bonus up to ₦100,000",
        "promo_code": "None required",
        "min_deposit": "₦100",
        "min_stake": "₦50",
        "sports_count": "25+",
        "key_sports": ["Football", "Basketball", "Tennis", "Virtual Sports"],
        "payment_methods": ["OPay", "PalmPay", "Bank Transfer", "Visa", "Mastercard", "USSD"],
        "withdrawal_speed": "Instant to 24 hours",
        "live_betting": True,
        "live_streaming": False,
        "cash_out": True,
        "mobile_app": True,
        "ussd": True,
        "customer_support": ["Live chat", "Email", "Phone"],
        "support_24_7": True,
        "local_languages": ["Pidgin", "Yoruba", "Igbo", "Hausa"],
        "stars": 4,
        "image_color": "#006600",
        "image_icon": "⭐",
        "verdict_audience": "Nigerian football fans, accumulator punters, and virtual sports bettors",
        "pros": [
            "Nigeria's most trusted bookmaker with 10+ years of history",
            "Extensive local football coverage including NPFL",
            "USSD access for non-smartphone users",
            "Multiple local payment methods including OPay and PalmPay",
            "24/7 customer support in local languages",
        ],
        "cons": [
            "No live streaming",
            "Website can feel cluttered during peak hours",
            "Odds not always the best for international events",
            "Welcome bonus wagering requirements can be steep",
        ],
    },
    "Sportybet": {
        "tagline": "Fast Payouts – Pan-African Operator",
        "countries": ["Nigeria", "Kenya", "Ghana", "Uganda", "Tanzania", "Zambia"],
        "welcome_offer": "Free bet on first deposit",
        "promo_code": "None required",
        "min_deposit": "₦100",
        "min_stake": "₦50",
        "sports_count": "20+",
        "key_sports": ["Football", "Basketball", "Tennis", "Esports"],
        "payment_methods": ["OPay", "PalmPay", "MTN MoMo", "M-Pesa", "Bank Transfer", "Visa"],
        "withdrawal_speed": "Instant",
        "live_betting": True,
        "live_streaming": False,
        "cash_out": True,
        "mobile_app": True,
        "ussd": False,
        "customer_support": ["Live chat", "Email"],
        "support_24_7": True,
        "local_languages": ["Pidgin", "Swahili"],
        "stars": 4,
        "image_color": "#ff6600",
        "image_icon": "⭐",
        "verdict_audience": "Multi-country African bettors who want instant withdrawals and a clean mobile experience",
        "pros": [
            "Truly instant withdrawals across all major African payment methods",
            "Clean, fast mobile app loved across Africa",
            "Pan-African — works in Nigeria, Kenya, Ghana, Uganda, and more",
            "Competitive football odds, especially for African leagues",
            "Cash-out available on most markets",
        ],
        "cons": [
            "No live streaming",
            "No USSD for feature phone users",
            "Welcome offer is modest compared to competitors",
            "Smaller sports catalogue than Melbet or 1xBet",
        ],
    },
    "Betway": {
        "tagline": "Global Brand, Local Heart – Sports Betting Leader",
        "countries": ["Nigeria", "Kenya", "Ghana", "South Africa", "Zambia"],
        "welcome_offer": "100% first deposit bonus up to ₦50,000",
        "promo_code": "None required",
        "min_deposit": "₦100",
        "min_stake": "₦50",
        "sports_count": "30+",
        "key_sports": ["Football", "Basketball", "Tennis", "Cricket", "Rugby"],
        "payment_methods": ["Bank Transfer", "Visa", "Mastercard", "M-Pesa", "MTN MoMo", "OPay"],
        "withdrawal_speed": "Instant to 48 hours depending on method",
        "live_betting": True,
        "live_streaming": True,
        "cash_out": True,
        "mobile_app": True,
        "ussd": False,
        "customer_support": ["Live chat", "Email", "Phone"],
        "support_24_7": True,
        "local_languages": ["English"],
        "stars": 4,
        "image_color": "#00a6e0",
        "image_icon": "⭐",
        "verdict_audience": "African bettors who want a globally trusted brand with live streaming and a wide sports range",
        "pros": [
            "One of the few African bookmakers offering live streaming",
            "Globally trusted brand operating since 2006",
            "Wide sports range including cricket and rugby",
            "Cash-out available on live and pre-match markets",
            "Strong responsible gambling tools",
        ],
        "cons": [
            "Withdrawal times can be slower than Sportybet or Bet9ja",
            "Support not available in local African languages",
            "Some promotions are region-specific and not always available",
        ],
    },
    "BetKing": {
        "tagline": "Nigeria's Fastest Growing Bookmaker",
        "countries": ["Nigeria", "Kenya", "Sierra Leone"],
        "welcome_offer": "200% first deposit bonus up to ₦100,000",
        "promo_code": "KING",
        "min_deposit": "₦100",
        "min_stake": "₦50",
        "sports_count": "20+",
        "key_sports": ["Football", "Basketball", "Tennis", "Virtual Sports"],
        "payment_methods": ["OPay", "PalmPay", "Bank Transfer", "Visa"],
        "withdrawal_speed": "Instant to 24 hours",
        "live_betting": True,
        "live_streaming": False,
        "cash_out": True,
        "mobile_app": True,
        "ussd": True,
        "customer_support": ["Live chat", "Email"],
        "support_24_7": False,
        "local_languages": ["Pidgin"],
        "stars": 4,
        "image_color": "#c8102e",
        "image_icon": "⭐",
        "verdict_audience": "Nigerian bettors looking for a generous welcome bonus and fast payouts",
        "pros": [
            "Very generous 200% welcome bonus",
            "Fast-growing platform with strong Nigerian football focus",
            "USSD access for feature phone users",
            "OPay and PalmPay supported for instant deposits",
        ],
        "cons": [
            "No live streaming",
            "Customer support not 24/7",
            "Smaller market presence outside Nigeria",
            "Promo wagering requirements should be read carefully",
        ],
    },
    "Hollywoodbets": {
        "tagline": "South Africa's Biggest Bookmaker – Now Across Africa",
        "countries": ["South Africa", "Nigeria", "Kenya", "Ghana", "Zimbabwe", "Mozambique"],
        "welcome_offer": "₦50 free bet on registration",
        "promo_code": "None required",
        "min_deposit": "₦50",
        "min_stake": "₦10",
        "sports_count": "25+",
        "key_sports": ["Football", "Horse Racing", "Rugby", "Cricket", "Tennis"],
        "payment_methods": ["Bank Transfer", "Visa", "Mastercard", "OPay", "M-Pesa"],
        "withdrawal_speed": "Instant to 24 hours",
        "live_betting": True,
        "live_streaming": True,
        "cash_out": True,
        "mobile_app": True,
        "ussd": False,
        "customer_support": ["Live chat", "Email", "Phone"],
        "support_24_7": True,
        "local_languages": ["English", "Zulu"],
        "stars": 4,
        "image_color": "#9b1b30",
        "image_icon": "⭐",
        "verdict_audience": "South African bettors and African racing fans who want live streaming and horse racing markets",
        "pros": [
            "Excellent horse racing coverage — unmatched on the continent",
            "Live streaming available for select events",
            "30+ years of experience in Africa — most established brand on the list",
            "Ultra-low minimum deposit of ₦50",
            "Strong responsible gambling culture",
        ],
        "cons": [
            "Football odds can lag behind specialists like Bet9ja or Sportybet",
            "Not as strong in Nigeria compared to South Africa",
            "No USSD support",
        ],
    },
    "Betika": {
        "tagline": "Kenya's Home-Grown Betting Champion",
        "countries": ["Kenya", "Tanzania", "Uganda"],
        "welcome_offer": "KSh 50 free bet on first deposit",
        "promo_code": "None required",
        "min_deposit": "KSh 10",
        "min_stake": "KSh 1",
        "sports_count": "15+",
        "key_sports": ["Football", "Basketball", "Tennis", "Virtual Sports"],
        "payment_methods": ["M-Pesa", "Airtel Money"],
        "withdrawal_speed": "Instant",
        "live_betting": True,
        "live_streaming": False,
        "cash_out": True,
        "mobile_app": True,
        "ussd": True,
        "customer_support": ["Live chat", "WhatsApp", "Email"],
        "support_24_7": False,
        "local_languages": ["Swahili", "English"],
        "stars": 4,
        "image_color": "#1a237e",
        "image_icon": "⭐",
        "verdict_audience": "Kenyan bettors who want a local brand with instant M-Pesa payouts and a jackpot programme",
        "pros": [
            "Kenya's most popular local bookmaker",
            "Instant M-Pesa withdrawals",
            "Weekly jackpot with attractive prize pools",
            "Ultra-low minimum stake of KSh 1",
            "USSD available for non-smartphone users",
        ],
        "cons": [
            "No live streaming",
            "Payment options limited to M-Pesa and Airtel Money",
            "Available mainly in East Africa only",
            "Customer support not 24/7",
        ],
    },
    "PariMatch": {
        "tagline": "European Precision, African Markets – Live Streaming Leader",
        "countries": ["Nigeria", "Kenya", "Ghana"],
        "welcome_offer": "100% first deposit bonus up to ₦50,000",
        "promo_code": "PMATCH",
        "min_deposit": "₦500",
        "min_stake": "₦50",
        "sports_count": "30+",
        "key_sports": ["Football", "Basketball", "Tennis", "MMA", "Hockey"],
        "payment_methods": ["Bank Transfer", "Visa", "Mastercard", "OPay"],
        "withdrawal_speed": "Instant to 24 hours",
        "live_betting": True,
        "live_streaming": True,
        "cash_out": True,
        "mobile_app": True,
        "ussd": False,
        "customer_support": ["Live chat", "Email"],
        "support_24_7": True,
        "local_languages": ["English"],
        "stars": 4,
        "image_color": "#0057a8",
        "image_icon": "⭐",
        "verdict_audience": "African bettors who value live streaming, European odds precision, and a wide selection beyond football",
        "pros": [
            "Live streaming available on thousands of events annually",
            "European pedigree with sharp odds across all major sports",
            "Clean, fast platform — excellent desktop and mobile experience",
            "Cash-out on live and pre-match markets",
            "24/7 customer support",
        ],
        "cons": [
            "Higher minimum deposit (₦500) than most local rivals",
            "No USSD support — smartphone required",
            "Limited local language support",
            "Smaller African market footprint than Bet9ja or 1xBet",
        ],
    },
    "Bangbet": {
        "tagline": "Nigeria's Rising Bookmaker – Big Bonuses, Fast Payouts",
        "countries": ["Nigeria"],
        "welcome_offer": "200% first deposit bonus up to ₦200,000",
        "promo_code": "BANGBET",
        "min_deposit": "₦100",
        "min_stake": "₦50",
        "sports_count": "20+",
        "key_sports": ["Football", "Basketball", "Tennis", "Virtual Sports", "Aviator"],
        "payment_methods": ["OPay", "PalmPay", "Bank Transfer", "Visa", "Mastercard"],
        "withdrawal_speed": "Instant",
        "live_betting": True,
        "live_streaming": False,
        "cash_out": True,
        "mobile_app": True,
        "ussd": False,
        "customer_support": ["Live chat", "WhatsApp", "Email"],
        "support_24_7": False,
        "local_languages": ["Pidgin", "English"],
        "stars": 3,
        "image_color": "#e60000",
        "image_icon": "⭐",
        "verdict_audience": "Nigerian bettors looking for a big welcome bonus and Aviator fans wanting more crash game markets",
        "pros": [
            "Very generous 200% welcome bonus — one of the highest in Nigeria",
            "Instant withdrawals via OPay and PalmPay",
            "Strong Aviator and virtual sports section",
            "Clean mobile app with a modern interface",
        ],
        "cons": [
            "Newer brand — less proven track record than Bet9ja or Sportybet",
            "No live streaming",
            "Support not available 24/7",
            "Sports range smaller than established competitors",
            "Bonus terms should be read carefully — high wagering requirements reported",
        ],
    },
    "MSport": {
        "tagline": "Nigeria's Fastest-Paying Bookmaker – Instant Withdrawals Guaranteed",
        "countries": ["Nigeria"],
        "welcome_offer": "100% first deposit bonus up to ₦100,000",
        "promo_code": "MSPORT",
        "min_deposit": "₦100",
        "min_stake": "₦50",
        "sports_count": "25+",
        "key_sports": ["Football", "Basketball", "Tennis", "Virtual Sports", "E-Sports"],
        "payment_methods": ["OPay", "PalmPay", "Moniepoint", "Bank Transfer", "Visa"],
        "withdrawal_speed": "Instant",
        "live_betting": True,
        "live_streaming": False,
        "cash_out": True,
        "mobile_app": True,
        "ussd": True,
        "customer_support": ["Live chat", "WhatsApp", "Email", "Phone"],
        "support_24_7": True,
        "local_languages": ["Pidgin", "Yoruba", "Igbo", "Hausa"],
        "stars": 4,
        "image_color": "#006b3c",
        "image_icon": "⭐",
        "verdict_audience": "Nigerian bettors who demand instant payouts and strong local football coverage with USSD access",
        "pros": [
            "Guaranteed instant withdrawals — a key differentiator in Nigeria",
            "USSD support for non-smartphone users",
            "Strong local language customer support — Yoruba, Igbo, Hausa, Pidgin",
            "Moniepoint integration — fast and widely used in Nigeria",
            "24/7 support across multiple channels",
        ],
        "cons": [
            "No live streaming",
            "Limited international brand recognition",
            "E-sports offering still developing",
            "Promotional offers less generous than 1xBet or Melbet",
        ],
    },
}


# ---------------------------------------------------------------------------
# Article generator
# ---------------------------------------------------------------------------

def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _post_id(brand: str) -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"review-{_slug(brand)}-review-{date_str}"


def generate_review(brand: str, country: str | None = None) -> dict:
    """Generate a full bookmaker review post dict for posts.json."""
    info = BOOKMAKER_CATALOGUE.get(brand)
    if not info:
        raise ValueError(f"Brand '{brand}' not in catalogue. Add it first.")

    with open(BRAND_KB) as f:
        kb = json.load(f)

    site_url = kb["site_url"]
    footer = kb["required_footer"]
    primary_country = country or info["countries"][0]
    currency = "KSh" if primary_country == "Kenya" else "₦"

    countries_str = ", ".join(info["countries"])
    payment_str = ", ".join(f"**{p}**" for p in info["payment_methods"])
    pros_md = "\n".join(f"  + {p}" for p in info["pros"])
    cons_md = "\n".join(f"  + {c}" for c in info["cons"])

    live_streaming_note = (
        "live streaming on select events" if info["live_streaming"]
        else "live betting without live streaming"
    )
    cash_out_note = "Cash-out is available" if info["cash_out"] else "Cash-out is not currently offered"
    ussd_note = (
        "USSD is supported for non-smartphone users, which is a major advantage across Africa."
        if info["ussd"]
        else "USSD is not currently supported, so a smartphone is required."
    )
    support_hours = "24/7" if info["support_24_7"] else "during business hours"
    languages_str = " and ".join(info["local_languages"])

    body = f"""## Introduction
{brand} — {info['tagline']} — has built a strong reputation among {primary_country}n bettors. Operating across {countries_str}, the bookmaker covers {info['sports_count']} sports and offers {info['welcome_offer']}. In this review, we put {brand} through its paces across every dimension that matters to African bettors: bonuses, sports markets, mobile experience, payments, live betting, customer support, and responsible gambling.

Whether you're a casual football fan or a serious accumulator punter, this guide will tell you exactly what to expect.

## Welcome Bonus & Promotions
{brand}'s welcome offer gives new customers {info['welcome_offer']}{"." if not info['welcome_offer'].endswith('.') else ""} {"No promo code is required — simply register and make your first deposit." if info['promo_code'] == "None required" else f"Use promo code **{info['promo_code']}** when registering to claim the offer."} The minimum deposit to qualify is {info['min_deposit']}.

Compared to other bookmakers in the African market, {brand}'s welcome offer is {"generous and competitive" if info['stars'] >= 4 else "modest but straightforward"}. Always read the terms and conditions — wagering requirements apply before any bonus funds can be withdrawn.

## Sports Markets & Odds
{brand} covers {info['sports_count']} sports, including {", ".join(info['key_sports'][:-1])} and {info['key_sports'][-1]}. The platform provides strong coverage of African football leagues alongside international competitions like the Premier League, La Liga, Champions League, and AFCON.

Odds are competitive {"across the board" if info['stars'] >= 4 else "for major markets"}, particularly for football. The minimum stake is {info['min_stake']}, keeping betting accessible for all budgets.

## Mobile App & User Experience
{brand}'s mobile app is available for Android and iOS, offering a clean and intuitive interface. {ussd_note}

The desktop site mirrors the app experience, with clear navigation and fast load times. Overall, the platform prioritises ease of use — a must for markets where mobile is the primary access point.

## Payment Methods & Withdrawal Speed
{brand} supports a range of payment methods including {payment_str}. The minimum deposit is {info['min_deposit']}, and withdrawals are typically processed {info['withdrawal_speed']}.

Deposits are processed instantly for most methods. No fees are charged on standard transactions, though individual payment providers may have their own charges. Local payment methods are well-integrated, which is essential for African bettors.

## Live Betting & Streaming
{brand} offers {live_streaming_note}. The live betting interface is well-designed with real-time odds updates and a broad selection of in-play markets. {cash_out_note} on selected markets, giving bettors flexibility to lock in profits or limit losses.

## Customer Support
The support team is available {support_hours} via {", ".join(info['customer_support'])}. Support is offered in {languages_str}, which is a significant advantage for local bettors.

Response times are generally quick, and agents are knowledgeable about the platform's products and promotions.

## Responsible Gambling
{brand} provides deposit limits, self-exclusion, and cool-off periods to help bettors manage their activity. Responsible gambling information is clearly signposted throughout the site and app.

Always bet within your means. Set a budget before you start and never chase losses.

## Pros & Cons
* Pros:
{pros_md}
* Cons:
{cons_md}

## SifuFinds Verdict
{brand} earns a **{info['stars']}/5 stars** from SifuFinds. It is an excellent choice for {info['verdict_audience']}.

If you're looking for a reliable bookmaker with strong African football coverage, solid payment options, and responsive support, {brand} is well worth considering.

Compare {brand} with other top bookmakers on [{site_url}]({site_url}) for today's best odds and bonuses.
{footer}"""

    tags = ["Review", brand, "Bookmaker"] + info["countries"][:3]

    return {
        "id": _post_id(brand),
        "category": "review",
        "title": f"{brand} Review 2026: Is It Worth It for {primary_country}n Bettors?",
        "slug": f"{_slug(brand)}-review",
        "excerpt": (
            f"{brand} offers {info['welcome_offer']}. With {info['sports_count']} sports markets, "
            f"{info['withdrawal_speed'].lower()} withdrawals, and coverage across {countries_str}. "
            f"Read our in-depth review to find out if it's the right bookmaker for you."
        ),
        "body": body,
        "author": "SifuFinds Editorial Team",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "image_color": info["image_color"],
        "image_icon": info["image_icon"],
        "tags": tags,
        "featured": False,
        "bookmaker_featured": brand,
        "read_time": 8,
        "stars": info["stars"],
        "brand_name": brand,
    }


def load_posts() -> list:
    if BLOG_POSTS.exists():
        with open(BLOG_POSTS) as f:
            data = json.load(f)
        return data.get("posts", [])
    return []


def save_posts(posts: list) -> None:
    with open(BLOG_POSTS, "w") as f:
        json.dump({"posts": posts}, f, indent=2, ensure_ascii=False)
    print(f"  Saved {len(posts)} posts to {BLOG_POSTS}")


def publish(brand: str, country: str | None = None, dry_run: bool = False) -> dict:
    post = generate_review(brand, country)
    posts = load_posts()

    # Check for existing review of this brand
    existing_ids = {p["id"] for p in posts}
    existing_brands = {p.get("brand_name", "").lower() for p in posts if p.get("category") == "review"}

    if brand.lower() in existing_brands:
        print(f"  SKIP: review for '{brand}' already exists in posts.json")
        return post

    if dry_run:
        print(f"  DRY RUN — would publish: {post['title']}")
        article_path = ARTICLES_DIR / f"{_slug(brand)}-review.md"
        article_path.write_text(post["body"])
        print(f"  Article draft saved to {article_path}")
        return post

    # Prepend so newest appears first
    posts.insert(0, post)
    save_posts(posts)

    article_path = ARTICLES_DIR / f"{_slug(brand)}-review.md"
    article_path.write_text(post["body"])
    print(f"  Published: {post['title']}")
    print(f"  Article saved to {article_path}")
    return post


def main() -> None:
    parser = argparse.ArgumentParser(description="SifuFinds bookmaker review generator")
    parser.add_argument("--brand", help="Bookmaker name (e.g. 'Bet9ja')")
    parser.add_argument("--country", help="Primary country for the review (e.g. 'Nigeria')")
    parser.add_argument("--list-brands", action="store_true", help="List all available brands")
    parser.add_argument("--batch", action="store_true", help="Generate reviews for all brands not yet in posts.json")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to posts.json")
    args = parser.parse_args()

    if args.list_brands:
        print("Available brands:")
        for b in BOOKMAKER_CATALOGUE:
            print(f"  - {b}")
        return

    if args.batch:
        posts = load_posts()
        existing_brands = {p.get("brand_name", "").lower() for p in posts if p.get("category") == "review"}
        pending = [b for b in BOOKMAKER_CATALOGUE if b.lower() not in existing_brands]
        if not pending:
            print("All brands already have reviews in posts.json.")
            return
        print(f"Generating {len(pending)} new review(s)...")
        for brand in pending:
            print(f"\n→ {brand}")
            publish(brand, dry_run=args.dry_run)
        return

    if not args.brand:
        parser.print_help()
        sys.exit(1)

    if args.brand not in BOOKMAKER_CATALOGUE:
        print(f"Error: '{args.brand}' not in catalogue. Available: {list(BOOKMAKER_CATALOGUE.keys())}")
        sys.exit(1)

    print(f"\n→ Generating review for {args.brand}...")
    post = publish(args.brand, args.country, dry_run=args.dry_run)
    print(f"\nDone. Title: {post['title']}")


if __name__ == "__main__":
    main()
