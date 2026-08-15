"""
Telegram Brand Offers Agent — SifuFinds
Posts one brand offer per run to @sifufinds, rotating through all 27 bookmakers.
Uses the existing Bot Token (no Telethon needed for own channel).

Also posts a Facebook Page photo post for the same brand (image generated
locally, link prefers a real bonus-flavoured blog post over the bookmaker's
own review page). Skips Facebook cleanly if FACEBOOK_PAGE_ID/
FACEBOOK_PAGE_ACCESS_TOKEN aren't configured yet.

Usage:
  python agent_telegram_offers.py            # next brand in rotation
  python agent_telegram_offers.py --brand Bet9ja  # specific brand
  python agent_telegram_offers.py --force    # ignore cooldown, post anyway
  python agent_telegram_offers.py --no-facebook   # Telegram only
  python agent_telegram_offers.py --dry-run       # preview only, post nothing
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
import requests

load_dotenv(Path(__file__).parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))
from utils.logger import log
from utils.blog_match import find_matching_post, mark_used, bookmaker_review_url
from utils.social_image import build_social_image, brand_color
from utils.affiliate_links import masked_url, pick_cta, cta_html, cta_plain, promo_code_line
from agent3_social import post_facebook

# ── CONFIG ────────────────────────────────────────────────────────────────────

CHANNEL    = os.getenv("TELEGRAM_CHANNEL_USERNAME", "@sifufinds")
BOT_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
SITE_URL   = "https://sifufinds.com"
STATE_FILE = Path(__file__).parent / "offers_state.json"

# Minimum hours between posts of the SAME brand
BRAND_COOLDOWN_HOURS = 48

# ── BRANDS ────────────────────────────────────────────────────────────────────
# RULE: Only post brands where affiliate=True (affiliate link exists).
#       Brands with affiliate=False are kept for reference — add their affiliate
#       link and flip to True when ready. Never post without an affiliate link.
# No promo codes — do not add unless instructed.

BRANDS = [
    {
        "name": "Bet9ja",
        "flag": "🇳🇬",
        "countries": ["Nigeria"],
        "welcome": "₦2,500 Free Bet on Signup + 170% ACCA Boost",
        "bonus_highlight": "No deposit needed",
        "url": "https://www.bet9ja.com",
        "affiliate": False,
        "min_deposit": "₦100",
        "stars": 5,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC Licensed",
        "tag": "Nigeria's No.1 Licensed Bookmaker",
        "hashtags": "#Bet9ja #Nigeria #FreeBet #NLRC #NigerianBetting",
    },
    {
        "name": "Sportybet",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Uganda", "Tanzania"],
        "welcome": "150% Welcome Bonus – Up to ₦30,000",
        "bonus_highlight": "150% free bet gifts on qualifying deposits",
        "url": "https://www.sportybet.com/ng/",
        "affiliate": False,
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC + BCLB Licensed",
        "tag": "Africa's Most Downloaded Betting App",
        "hashtags": "#Sportybet #Africa #BettingApp #FreeBet #SportsBetting",
    },
    {
        "name": "BetKing",
        "flag": "🇳🇬",
        "countries": ["Nigeria"],
        "welcome": "₦100 Free Bets + 10 Aviator Flights — No Deposit",
        "bonus_highlight": "Zero deposit required to claim",
        "url": "https://www.betking.com",
        "affiliate": False,
        "min_deposit": "₦0",
        "stars": 5,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC Licensed",
        "tag": "KingMakers-Backed, No Deposit Bonus",
        "hashtags": "#BetKing #Nigeria #Aviator #NoDeposit #FreeBet",
    },
    {
        "name": "1xBet",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania", "Uganda", "Zambia"],
        "welcome": "300% First Deposit Bonus – Up to ₦1,200,000",
        "bonus_highlight": "Highest welcome bonus in Africa",
        "url": "https://reffpa.com/L?tag=d_5969542m_1599c_&site=5969542&ad=1599",
        "affiliate": True,
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC + BCLB + Curaçao Licensed",
        "tag": "50+ Sports — Highest Bonus in Africa",
        "hashtags": "#1xBet #Africa #SportsBetting #300Bonus #FreeBet",
    },
    {
        "name": "Betway",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "South Africa", "Ghana", "Tanzania"],
        "welcome": "Up to ₦100,000 in Free Bets — First 7 Days",
        "bonus_highlight": "Free bets on every settled stake for 7 days",
        "url": "https://www.betway.com/en-ng/",
        "affiliate": False,
        "min_deposit": "₦1,000",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC + BCLB + NGBB Licensed",
        "tag": "International Brand Trusted Across 12 African Countries",
        "hashtags": "#Betway #Africa #FreeBets #Trusted #SportsBetting",
    },
    {
        "name": "Hollywoodbets",
        "flag": "🇿🇦",
        "countries": ["South Africa", "Kenya", "Uganda", "Tanzania"],
        "welcome": "R25 Free Bet on Registration — No Deposit",
        "bonus_highlight": "25 years of trust in South Africa",
        "url": "https://www.hollywoodbets.net/",
        "affiliate": False,
        "min_deposit": "R5",
        "stars": 5,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "Western Cape Gambling Board",
        "tag": "South Africa's Biggest Homegrown Bookmaker",
        "hashtags": "#Hollywoodbets #SouthAfrica #PSL #FreeBet #ZABetting",
    },
    {
        "name": "Betika",
        "flag": "🇰🇪",
        "countries": ["Kenya", "Tanzania", "Uganda", "Malawi", "Ghana"],
        "welcome": "Free Bet + Aviator Free Bets on Signup",
        "bonus_highlight": "Operator of the Year 2025 — 8M+ users",
        "url": "https://www.betika.com/en-ke/",
        "affiliate": False,
        "min_deposit": "KSh 10",
        "stars": 5,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "BCLB Licensed (No. BK0000679)",
        "tag": "Operator of the Year 2025 — 8M Users",
        "hashtags": "#Betika #Kenya #KPL #Aviator #EastAfrica",
    },
    {
        "name": "SportPesa",
        "flag": "🇰🇪",
        "countries": ["Kenya", "Tanzania", "Uganda", "Rwanda"],
        "welcome": "300% Welcome Karibu Gift on First Deposit",
        "bonus_highlight": "Triple your first deposit as free bets",
        "url": "https://www.sportpesa.co.ke",
        "affiliate": False,
        "min_deposit": "KSh 10",
        "stars": 5,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "BCLB Licensed",
        "tag": "Official Sponsor of the Kenya Premier League",
        "hashtags": "#SportPesa #Kenya #KPL #300Bonus #MegaJackpot",
    },
    {
        "name": "Melbet",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania", "Ethiopia"],
        "welcome": "200% First Deposit Bonus – Up to ₦480,000",
        "bonus_highlight": "150+ sports markets — most in Africa",
        "url": "https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559",
        "affiliate": True,
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": False,
        "cashout": False,
        "licence": "NLRC + BCLB + Curaçao Licensed",
        "tag": "150+ Sports — Widest Market Range",
        "hashtags": "#Melbet #Africa #200Bonus #SportsBetting #Esports",
    },
    # "Mebet" is a second, separately-tracked affiliate ID for this same Melbet
    # platform (its masked link 301s to melbet.org's own registration page —
    # confirmed by resolving the redirect, same brand/logo/bonus as above), not
    # a distinct operator. Facts intentionally mirror the Melbet entry above
    # since they describe the same real platform; only the tracked url/tag/
    # hashtags differ.
    {
        "name": "Mebet",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania", "Ethiopia"],
        "welcome": "200% First Deposit Bonus – Up to ₦480,000",
        "bonus_highlight": "150+ sports markets — most in Africa",
        "url": "https://refpa3665.com/L?tag=d_5833716m_66335c_sifufinds&site=5833716&ad=66335",
        "affiliate": True,
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": False,
        "cashout": False,
        "licence": "NLRC + BCLB + Curaçao Licensed",
        "tag": "150+ Sports — Widest Market Range",
        "hashtags": "#Mebet #Africa #200Bonus #SportsBetting #Esports",
    },
    {
        "name": "MozzartBet",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Zimbabwe"],
        "welcome": "100% Bonus Up to ₦50,000 + 500 Aviator Free Bets",
        "bonus_highlight": "500 Aviator free bets included",
        "url": "https://www.mozzartbet.com/en/",
        "affiliate": False,
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC + BCLB Licensed",
        "tag": "100% Bonus + 500 Aviator Free Bets",
        "hashtags": "#MozzartBet #Aviator #Nigeria #Kenya #100Bonus",
    },
    {
        "name": "NairaBet",
        "flag": "🇳🇬",
        "countries": ["Nigeria"],
        "welcome": "Free Bet on First Deposit + Daily Free Bets",
        "bonus_highlight": "Nigeria's pioneer bookmaker since 2009",
        "url": "https://www.nairabet.com",
        "affiliate": False,
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC Licensed",
        "tag": "Nigeria's Pioneer Bookmaker — Est. 2009",
        "hashtags": "#NairaBet #Nigeria #NLRC #FreeBet #DailyBonus",
    },
    {
        "name": "22Bet",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania"],
        "welcome": "100% First Deposit Bonus – Up to ₦207,500",
        "bonus_highlight": "Proven fast payouts, 35 sports",
        "url": "https://22bet.com",
        "affiliate": False,
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC + BCLB + Curaçao Licensed",
        "tag": "100% Bonus — Reliable Fast Payouts",
        "hashtags": "#22Bet #Africa #FastPayout #100Bonus #SportsBetting",
    },
    {
        "name": "Betpawa",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Uganda", "Tanzania"],
        "welcome": "Weekly Jackpot — Win Millions from ₦50 Stake",
        "bonus_highlight": "Jackpot entry from just ₦50 / KSh 1 min stake",
        "url": "https://www.betpawa.ng",
        "affiliate": False,
        "min_deposit": "₦50",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": False,
        "licence": "NLRC + BCLB + Ghana GC Licensed",
        "tag": "Jackpot from ₦50 — Pan-African Operator",
        "hashtags": "#Betpawa #Jackpot #Africa #LowStake #WinBig",
    },
    {
        "name": "BetWinner",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania"],
        "welcome": "200% First Deposit Bonus – Up to ₦130,000",
        "bonus_highlight": "Easy 5x wagering requirement",
        "url": "https://bwredir.com/1Lvf?p=%2Fregistration%2F",
        "affiliate": True,
        "min_deposit": "₦400",
        "stars": 3,
        "instant_withdrawal": False,
        "cashout": True,
        "licence": "NLRC + BCLB + Curaçao Licensed",
        "tag": "200% Bonus — Easy 5x Wagering on 40+ Sports",
        "hashtags": "#BetWinner #200Bonus #Africa #SportsBetting #LiveBetting",
    },
    {
        "name": "Odibets",
        "flag": "🇰🇪",
        "countries": ["Kenya"],
        "welcome": "KSh 30 Free Bet on Registration — No Deposit",
        "bonus_highlight": "Min stake KSh 1 — most affordable in Kenya",
        "url": "https://odibets.com/",
        "affiliate": False,
        "min_deposit": "KSh 10",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "BCLB Licensed",
        "tag": "Bet from KSh 10 — Kenya's Low-Stake Champion",
        "hashtags": "#Odibets #Kenya #MPesa #LowStake #KPL",
    },
    {
        "name": "Supabets",
        "flag": "🇿🇦",
        "countries": ["South Africa", "Zimbabwe", "Zambia"],
        "welcome": "R10 Free Bet on Registration",
        "bonus_highlight": "SuperBanker weekly cash bonuses",
        "url": "https://www.supabets.com/",
        "affiliate": False,
        "min_deposit": "R5",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "Western Cape Gambling Board",
        "tag": "South Africa's Homegrown Underdog — Massive Jackpots",
        "hashtags": "#Supabets #SouthAfrica #PSL #Jackpot #Rugby",
    },
    {
        "name": "Bangbet",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya"],
        "welcome": "Deposit ₦50, Get ₦200 in Free Bets",
        "bonus_highlight": "Beginner-friendly low minimum stake",
        "url": "https://www.bangbet.com",
        "affiliate": False,
        "min_deposit": "₦50",
        "stars": 3,
        "instant_withdrawal": True,
        "cashout": False,
        "licence": "NLRC + BCLB Licensed",
        "tag": "Low Minimum Stake — Great for New Bettors",
        "hashtags": "#Bangbet #Nigeria #Kenya #LowStake #FreeBet",
    },
    {
        "name": "HelaBet",
        "flag": "🇰🇪",
        "countries": ["Kenya"],
        "welcome": "100% Welcome Bonus – Up to KSh 5,000",
        "bonus_highlight": "Instant M-Pesa payouts",
        "url": "https://1212fghnna.com/L?tag=d_2204817m_52235c_&site=2204817&ad=52235",
        "affiliate": True,
        "min_deposit": "KSh 10",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "BCLB Licensed",
        "tag": "Licensed Kenyan Brand — Instant M-Pesa Payouts",
        "hashtags": "#HelaBet #Kenya #MPesa #KPL #FreeBet",
    },
    {
        "name": "Paripesa",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania"],
        "welcome": "200% First Deposit Bonus – Up to ₦200,000",
        "bonus_highlight": "50+ sports markets, live streaming",
        "url": "https://combodef.com/L?tag=d_2350859m_45569c_&site=2350859&ad=45569",
        "affiliate": True,
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC + BCLB + Curaçao Licensed",
        "tag": "200% Bonus — 50+ Sports, Rising Fast in Africa",
        "hashtags": "#Paripesa #200Bonus #Africa #LiveBetting #SportsBetting",
    },
    # Facts below mirror the same brand's existing verified BOOKS entry in
    # assets/shared.js (already live on the relevant country pages) rather
    # than being re-researched from scratch — see that file for the source.
    {
        "name": "Rasbet",
        "flag": "🇪🇹",
        "countries": ["Ethiopia"],
        "welcome": "Welcome Bonus on First Deposit",
        "bonus_highlight": "Rising sportsbook built for the Ethiopian market",
        "url": "https://rasbet.goaffnk.com/t/MTRfMQ==/",
        "affiliate": True,
        "min_deposit": "Br 50",
        "stars": 3,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "Licensed",
        "tag": "Rising Sportsbook for the Ethiopian Market",
        "hashtags": "#Rasbet #Ethiopia #SportsBetting #FreeBet #AfricanBetting",
    },
    {
        "name": "TicTacBets",
        "flag": "🇿🇦",
        "countries": ["South Africa"],
        "welcome": "25 Free Spins + 100% Match Up to R5,000 + 50 Spins",
        "bonus_highlight": "25 free spins on registration, no deposit needed",
        "url": "https://trackrt.tictacbets.co.za/o/zdY0CA?site_id=1023",
        "affiliate": True,
        "min_deposit": "R5",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NCGLB Licensed",
        "tag": "SA-Owned Since 2015 — 25 Free Spins No Deposit",
        "hashtags": "#TicTacBets #SouthAfrica #FreeSpins #NoDeposit #SportsBetting",
    },
    {
        "name": "BetXchange",
        "flag": "🇿🇦",
        "countries": ["South Africa"],
        "welcome": "R200 Free Bet on First Deposit",
        "bonus_highlight": "Betting exchange with competitive odds",
        "url": "https://track.trkbxa.click/o/yDSAGh?lpage=m0gk2w&site_id=1226",
        "affiliate": True,
        "min_deposit": "R10",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "WCGRB Licensed",
        "tag": "SA Betting Exchange — Competitive Odds",
        "hashtags": "#BetXchange #SouthAfrica #FreeBet #SportsBetting #AfricanBetting",
    },
    {
        "name": "Bettabets",
        "flag": "🇿🇦",
        "countries": ["South Africa"],
        "welcome": "R200 Free Bet on First Deposit",
        "bonus_highlight": "Local South African brand focused on PSL and cricket",
        "url": "https://track.bettapartners.co.za/o/zNV2Pk?lpage=AjB-aC&site_id=777",
        "affiliate": True,
        "min_deposit": "R10",
        "stars": 3,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NGB Licensed",
        "tag": "SA Local Brand — PSL & Cricket",
        "hashtags": "#Bettabets #SouthAfrica #FreeBet #PSL #SportsBetting",
    },
    {
        "name": "Playbet",
        "flag": "🇿🇦",
        "countries": ["South Africa"],
        "welcome": "100% Deposit Bonus – Up to R2,000",
        "bonus_highlight": "Sports and casino in one platform",
        "url": "https://trk.playbet.net/o/5tgJzp?site_id=284",
        "affiliate": True,
        "min_deposit": "R10",
        "stars": 3,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "WCGRB Licensed",
        "tag": "SA Bookmaker — Sports & Casino",
        "hashtags": "#Playbet #SouthAfrica #DepositBonus #SportsBetting #AfricanBetting",
    },
    {
        # Real per-country data mirrored from assets/shared.js's BOOKS entries
        # (added 2026-08-14 — see AGENT-KNOWLEDGE.md's "Linebet added to BOOKS"
        # entry for the research/verification trail). Welcome figure uses the
        # Nigeria entry, the one with the highest verified bonus amount, same
        # convention every other multi-country brand in this list follows.
        "name": "Linebet",
        "flag": "🌍",
        "countries": [
            "Nigeria", "Kenya", "Ghana", "South Africa", "Tanzania", "Uganda",
            "Zambia", "Ethiopia", "Ivory Coast", "Cameroon", "Senegal", "Rwanda",
            "Zimbabwe", "Malawi", "Mozambique", "Angola", "DR Congo", "Botswana",
            "Egypt", "Morocco", "Namibia", "Sierra Leone", "Liberia",
        ],
        "welcome": "100% First Deposit Bonus – Up to ₦180,000",
        "bonus_highlight": "100% match on first deposit, wager x5 accumulators at min odds 1.40",
        "url": "https://lb-aff.com/L?tag=d_5966746m_22611c_sifufinds&site=5966746&ad=22611",
        "affiliate": True,
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "Curaçao Licensed",
        "tag": "International Brand – 1,000+ Daily Events",
        "hashtags": "#Linebet #Africa #Curacao #SportsBetting #AfricanBetting",
    },
    {
        # Real per-country data mirrored from assets/shared.js's BOOKS entries.
        # No Nigeria/Kenya presence found there, unlike most other multi-country
        # brands in this list — min_deposit varies by market since the bonus
        # itself is denominated in EUR uniformly rather than local currency.
        "name": "FairPari",
        "flag": "🌍",
        "countries": [
            "Ghana", "South Africa", "Tanzania", "Uganda", "Zambia", "Ethiopia",
            "Ivory Coast", "Cameroon", "Senegal", "Rwanda", "Zimbabwe", "Malawi",
            "Mozambique", "Angola", "DR Congo", "Botswana", "Egypt", "Morocco",
            "Namibia", "Sierra Leone", "Liberia",
        ],
        "welcome": "100% First Deposit Bonus – Up to €100",
        "bonus_highlight": "63+ sports, 4,000+ casino games, wide payment options",
        "url": "https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration",
        "affiliate": True,
        "min_deposit": "Varies by country",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "Locally licensed per market",
        "tag": "63+ Sports – 4,000+ Casino Games",
        "hashtags": "#FairPari #Africa #SportsBetting #AfricanBetting #CasinoGames",
    },
]

# Only brands with affiliate links are eligible for posting
AFFILIATE_BRANDS = [b for b in BRANDS if b.get("affiliate")]
BRAND_NAMES = [b["name"] for b in AFFILIATE_BRANDS]


# ── STATE MANAGEMENT ──────────────────────────────────────────────────────────

def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_index": -1, "brand_last_posted": {}}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _next_brand(state: dict, force_name: str | None = None, force: bool = False) -> dict | None:
    now = datetime.now(timezone.utc)
    brand_last = state.get("brand_last_posted", {})

    if force_name:
        candidates = [b for b in AFFILIATE_BRANDS if b["name"].lower() == force_name.lower()]
        if not candidates:
            print(f"✗ Brand '{force_name}' not found or has no affiliate link. Options: {', '.join(BRAND_NAMES)}")
            return None
        return candidates[0]

    # Round-robin across affiliate brands only, respecting cooldown
    n = len(AFFILIATE_BRANDS)
    start = (state.get("last_index", -1) + 1) % n
    for offset in range(n):
        idx = (start + offset) % n
        brand = AFFILIATE_BRANDS[idx]
        last_str = brand_last.get(brand["name"])
        if force or not last_str:
            state["last_index"] = idx
            return brand
        last_dt = datetime.fromisoformat(last_str)
        if (now - last_dt) >= timedelta(hours=BRAND_COOLDOWN_HOURS):
            state["last_index"] = idx
            return brand

    # All on cooldown — pick the affiliate brand with the oldest post
    oldest = min(AFFILIATE_BRANDS, key=lambda b: brand_last.get(b["name"], "2000-01-01T00:00:00+00:00"))
    state["last_index"] = AFFILIATE_BRANDS.index(oldest)
    return oldest


# ── MESSAGE FORMATTER ─────────────────────────────────────────────────────────

def _stars(n: int) -> str:
    return "⭐" * n + "☆" * (5 - n)


def _yes_no(v: bool) -> str:
    return "✅" if v else "❌"


def _country_flags(countries: list[str]) -> str:
    flag_map = {
        "Nigeria": "🇳🇬", "Kenya": "🇰🇪", "South Africa": "🇿🇦",
        "Ghana": "🇬🇭", "Tanzania": "🇹🇿", "Uganda": "🇺🇬",
        "Zambia": "🇿🇲", "Zimbabwe": "🇿🇼", "Rwanda": "🇷🇼",
        "Malawi": "🇲🇼", "Ethiopia": "🇪🇹", "Namibia": "🇳🇦",
        "Mozambique": "🇲🇿", "Botswana": "🇧🇼", "Ivory Coast": "🇨🇮",
        "Cameroon": "🇨🇲",
    }
    return " ".join(flag_map.get(c, "🌍") for c in countries[:6])


def build_offer_message(brand: dict) -> str:
    flags = _country_flags(brand["countries"])
    countries_str = " · ".join(brand["countries"][:5])
    if len(brand["countries"]) > 5:
        countries_str += f" +{len(brand['countries']) - 5} more"

    promo_line = promo_code_line(brand["name"])
    promo_bit = f"🎁 {promo_line}\n" if promo_line else ""

    msg = (
        f"🔥 <b>TODAY'S TOP DEAL</b> — {brand['name']} {flags}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>{brand['welcome']}</b>\n"
        f"✨ {brand['bonus_highlight']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{_stars(brand['stars'])}  {brand['tag']}\n\n"
        f"💳 Min Deposit: {brand['min_deposit']}\n"
        f"⚡ Instant Withdrawal: {_yes_no(brand['instant_withdrawal'])}\n"
        f"💸 Cash-Out: {_yes_no(brand['cashout'])}\n"
        f"🛡 {brand['licence']}\n\n"
        f"🌍 Available in: {countries_str}\n\n"
        f"{promo_bit}"
        f"👉 {cta_html(brand)}\n"
        f"📊 Compare all bonuses → <a href=\"{SITE_URL}\">{SITE_URL}</a>\n"
        f"📲 Join our channel → @sifufinds\n\n"
        f"{brand['hashtags']} #SifuFinds #BettingBonus #AfricanBetting\n\n"
        f"<i>18+ | Bet Responsibly | T&Cs Apply</i>"
    )
    return msg


def build_facebook_offer_message(brand: dict, link: str) -> str:
    """
    Plain-text Facebook Page caption (Graph API captions don't render HTML tags,
    so the CTA phrase sits in front of the link rather than as anchor text).
    Two purposeful links, never more: the content link first (drives organic
    traffic to a real SifuFinds review/blog post) and a masked, CTA'd affiliate
    link second — sifufinds.com/<brand>, never the raw tracking URL, per the
    site-wide affiliate link masking rule in utils/affiliate_links.py.
    Hashtags are always included — never a Facebook post without them.
    """
    flags = _country_flags(brand["countries"])
    countries_str = " · ".join(brand["countries"][:5])
    if len(brand["countries"]) > 5:
        countries_str += f" +{len(brand['countries']) - 5} more"
    top_hashtags = " ".join(brand["hashtags"].split()[:5])

    promo_line = promo_code_line(brand["name"])
    promo_bit = f"{promo_line}\n" if promo_line else ""

    return (
        f"🔥 Today's Top Deal — {brand['name']} {flags}\n\n"
        f"{brand['welcome']}\n"
        f"{brand['bonus_highlight']}\n\n"
        f"{_stars(brand['stars'])} {brand['tag']}\n"
        f"Min deposit {brand['min_deposit']} · {brand['licence']}\n"
        f"Available in: {countries_str}\n\n"
        f"Read the full review → {link}\n"
        f"{promo_bit}"
        f"{cta_plain(brand)}\n\n"
        f"{top_hashtags} #SifuFinds #BettingBonus\n\n"
        f"18+ | Bet Responsibly | BeGambleAware.org"
    )


# ── TELEGRAM SENDER ───────────────────────────────────────────────────────────

async def _send_telethon(message: str) -> bool:
    """Primary sender — uses Telethon user session (same creds as all other agents)."""
    api_id_str = os.getenv("TELEGRAM_API_ID", "").strip()
    api_hash   = os.getenv("TELEGRAM_API_HASH", "").strip()
    session    = os.getenv("TELEGRAM_SESSION_STRING", "").strip()

    if not api_id_str or not api_hash or not session:
        return False

    try:
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        async with TelegramClient(StringSession(session), int(api_id_str), api_hash) as client:
            await client.send_message(CHANNEL, message, parse_mode="html")
        return True
    except Exception as e:
        print(f"✗ Telethon error: {e}")
        return False


def _send_bot_token(message: str) -> bool:
    """Fallback sender — uses Bot Token if Telethon creds not available."""
    if not BOT_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": CHANNEL,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }, timeout=15)
    ok = resp.status_code == 200
    if not ok:
        print(f"✗ Bot token error: {resp.json().get('description', resp.text[:200])}")
    return ok


def send_to_channel(message: str) -> bool:
    """Try Telethon first, fall back to bot token."""
    if asyncio.run(_send_telethon(message)):
        return True
    print("Telethon unavailable — trying bot token fallback...")
    return _send_bot_token(message)


async def _send_telethon_photo(photo, caption: str) -> bool:
    """`photo` can be a remote URL or a local file path — Telethon's
    send_file() handles both transparently."""
    api_id_str = os.getenv("TELEGRAM_API_ID", "").strip()
    api_hash   = os.getenv("TELEGRAM_API_HASH", "").strip()
    session    = os.getenv("TELEGRAM_SESSION_STRING", "").strip()

    if not api_id_str or not api_hash or not session:
        return False

    try:
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        async with TelegramClient(StringSession(session), int(api_id_str), api_hash) as client:
            await client.send_file(CHANNEL, str(photo), caption=caption, parse_mode="html")
        return True
    except Exception as e:
        print(f"✗ Telethon photo error: {e}")
        return False


def _send_bot_token_photo(photo, caption: str) -> bool:
    """`photo` can be a remote URL (sent as JSON) or a local file path
    (multipart-uploaded) — the Bot API needs a different request shape
    for each, unlike Telethon which handles both the same way."""
    if not BOT_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    is_remote = str(photo).startswith(("http://", "https://"))
    if is_remote:
        resp = requests.post(url, json={
            "chat_id": CHANNEL, "photo": photo, "caption": caption, "parse_mode": "HTML",
        }, timeout=15)
    else:
        with open(photo, "rb") as f:
            resp = requests.post(url, data={
                "chat_id": CHANNEL, "caption": caption, "parse_mode": "HTML",
            }, files={"photo": f}, timeout=30)
    ok = resp.status_code == 200
    if not ok:
        print(f"✗ Bot token photo error: {resp.json().get('description', resp.text[:200])}")
    return ok


def send_photo_to_channel(photo, caption: str) -> bool:
    """Send a photo + HTML caption. `photo` may be a remote URL (e.g. a
    Wikimedia player photo) or a local file path (e.g. the freshly
    generated per-post branded graphic) — both are supported end to end.
    Tries Telethon first, falls back to bot token, and falls back further
    to a text-only message if the photo send fails for any reason (e.g.
    Telegram rejects the source) rather than losing the post entirely."""
    if asyncio.run(_send_telethon_photo(photo, caption)):
        return True
    print("Telethon photo send unavailable — trying bot token fallback...")
    if _send_bot_token_photo(photo, caption):
        return True
    print("Photo send failed — falling back to text-only message...")
    return send_to_channel(caption)


def _bonus_link_and_post(brand: dict) -> tuple[str, dict | None]:
    """Prefer a real bonus-flavoured blog post, then the bookmaker's own
    review page, then the homepage — never the raw affiliate URL, so organic
    Page traffic funnels through SifuFinds' own content."""
    post = find_matching_post("bonus")
    if post:
        return post["url"], post
    review_url = bookmaker_review_url(brand["name"])
    if review_url:
        return review_url, None
    return SITE_URL, None


# ── MAIN ──────────────────────────────────────────────────────────────────────

def run(brand_name: str | None = None, force: bool = False, facebook: bool = True, dry_run: bool = False) -> None:
    log("offers", "start", "running")
    state = _load_state()

    brand = _next_brand(state, force_name=brand_name, force=force)
    if not brand:
        sys.exit(1)

    print(f"📣 Posting offer for: {brand['name']}")
    message = build_offer_message(brand)
    link, matched_post = _bonus_link_and_post(brand)
    fb_message = build_facebook_offer_message(brand, link)

    if dry_run:
        print("\n" + "─" * 60 + "\nTELEGRAM\n" + "─" * 60)
        print(message)
        print("\n" + "─" * 60 + f"\nFACEBOOK (link: {link})\n" + "─" * 60)
        print(fb_message)
        print("\nDry run — nothing sent.")
        return

    results: dict[str, bool] = {}
    results["telegram"] = send_to_channel(message)
    if results["telegram"]:
        now_iso = datetime.now(timezone.utc).isoformat()
        state.setdefault("brand_last_posted", {})[brand["name"]] = now_iso
        _save_state(state)
        print(f"✓ Offer posted for {brand['name']}")
    log("offers", "telegram", "success" if results["telegram"] else "failed", brand["name"])

    if facebook:
        image_path = build_social_image(
            headline=f"{brand['name']}: {brand['welcome']}",
            tag="Best Bonus Today",
            color_hex=brand_color(brand["name"]),
            subtext=brand["tag"],
            out_name="bonus_card.png",
        )
        results["facebook"] = post_facebook(fb_message, image_path=image_path)
        if results["facebook"] and matched_post:
            mark_used("bonus", matched_post["slug"])
        log("offers", "facebook", "success" if results["facebook"] else "failed", brand["name"])
        print("✓ Posted to Facebook." if results["facebook"] else "✗ Facebook post failed or not configured (see agents/python/FB_SETUP_SIMPLE.md).")

    if not any(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Telegram Brand Offers")
    parser.add_argument("--brand", type=str, default=None, help="Post a specific brand offer")
    parser.add_argument("--force", action="store_true", help="Ignore cooldown and post anyway")
    parser.add_argument("--no-facebook", dest="facebook", action="store_false", help="Don't auto-post to Facebook")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, post nothing")
    args = parser.parse_args()
    run(brand_name=args.brand, force=args.force, facebook=args.facebook, dry_run=args.dry_run)
