"""
Brand Review Writer Agent — SifuFinds
Generates 1500-2000 word professional bookmaker reviews for each brand listed on
the SifuFinds site. Reviews are written in the voice of a senior iGaming journalist.

Usage:
  python agent_brand_reviews.py                  # all brands, one review each
  python agent_brand_reviews.py --brand Bet9ja   # specific brand
  python agent_brand_reviews.py --limit 5        # first N brands only
"""
import argparse
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))

from llm import ask_long
from config import SITE_URL, BRAND_NAME

# ── BRAND DATABASE ─────────────────────────────────────────────────────────────
# Distilled from assets/shared.js — all data is accurate as per the site.

BRANDS: list[dict] = [
    {
        "name": "Bet9ja",
        "slug": "bet9ja-review",
        "abbr": "B9",
        "bg": "#00875A",
        "tc": "#fff",
        "tag": "Nigeria's No.1 Licensed Bookmaker",
        "welcome": "Get ₦2,500 Free Bet on Signup + 170% ACCA Boost",
        "bonus_top": "₦2,500 Free Bet (no deposit required)",
        "acca_boost": "170% Accumulator Boost on 3+ leg multi-bets",
        "promo_code": "9BONUS",
        "stars": 5,
        "min_deposit": "₦100",
        "min_stake": "₦50",
        "instant_withdrawal": True,
        "cashout": True,
        "live_streaming": True,
        "sports_count": 30,
        "licence": "NLRC (National Lottery Regulatory Commission)",
        "countries": ["Nigeria"],
        "payment_methods": ["OPay", "PalmPay", "Bank Transfer", "Visa", "Mastercard", "USSD"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": True,
        "founded": "2013",
        "hq": "Lagos, Nigeria",
        "key_sports": ["Football", "Basketball", "Tennis", "Virtual Sports", "Horse Racing"],
        "standout": "NLRC-licensed, largest sportsbook in Nigeria, ACCA Boost up to 170%",
    },
    {
        "name": "Sportybet",
        "slug": "sportybet-review",
        "abbr": "SB",
        "bg": "#00C851",
        "tc": "#fff",
        "tag": "Africa's Most Downloaded Betting App",
        "welcome": "150% Welcome Bonus – Up to ₦30,000 Free Bet",
        "bonus_top": "150% Free Bet Gifts on qualifying deposits",
        "acca_boost": None,
        "promo_code": None,
        "stars": 4,
        "min_deposit": "₦100",
        "min_stake": "₦50",
        "instant_withdrawal": True,
        "cashout": True,
        "live_streaming": False,
        "sports_count": 30,
        "licence": "NLRC Licensed (Nigeria), BCLB Licensed (Kenya)",
        "countries": ["Nigeria", "Kenya", "Ghana", "Uganda", "Tanzania", "Ethiopia"],
        "payment_methods": ["OPay", "Quickteller", "Bank Transfer", "Visa", "Mastercard", "M-Pesa"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": True,
        "founded": "2015",
        "hq": "Accra, Ghana",
        "key_sports": ["Football", "Basketball", "Tennis", "Handball", "E-Sports"],
        "standout": "Africa's #1 downloaded betting app, 6 African countries, ultra-fast mobile experience",
    },
    {
        "name": "BetKing",
        "slug": "betking-review",
        "abbr": "BK",
        "bg": "#1C3D5A",
        "tc": "#fff",
        "tag": "No Deposit – KingMakers-Backed Nigerian Brand",
        "welcome": "₦100 Free Bets + 10 Aviator Flights – No Deposit Required",
        "bonus_top": "₦50 Sports + ₦50 Virtual Free Bets + 10 Aviator flights",
        "acca_boost": None,
        "promo_code": "BONUSKG",
        "stars": 5,
        "min_deposit": "₦0",
        "min_stake": "₦50",
        "instant_withdrawal": True,
        "cashout": True,
        "live_streaming": True,
        "sports_count": 25,
        "licence": "NLRC Licensed",
        "countries": ["Nigeria"],
        "payment_methods": ["OPay", "PalmPay", "Bank Transfer", "Visa", "Mastercard", "USSD"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": True,
        "founded": "2018",
        "hq": "Lagos, Nigeria",
        "key_sports": ["Football", "Basketball", "Tennis", "Aviator", "Virtual Sports"],
        "standout": "Backed by KingMakers investment group, no-deposit welcome bonus, strong Nigerian football coverage",
    },
    {
        "name": "1xBet",
        "slug": "1xbet-review",
        "abbr": "1X",
        "bg": "#E60000",
        "tc": "#fff",
        "tag": "Highest Welcome Bonus in Africa",
        "welcome": "300% First Deposit Bonus – Up to ₦1,200,000 (Nigeria) / 200% up to KSh 20,000 (Kenya)",
        "bonus_top": "300% first deposit match (Nigeria)",
        "acca_boost": None,
        "promo_code": "1BONUSNG",
        "stars": 4,
        "min_deposit": "₦100",
        "min_stake": "₦20",
        "instant_withdrawal": True,
        "cashout": True,
        "live_streaming": True,
        "sports_count": 50,
        "licence": "NLRC Licensed (Nigeria), BCLB Licensed (Kenya), Curaçao (international)",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania", "Uganda", "Zambia", "Ethiopia", "Ivory Coast", "Cameroon"],
        "payment_methods": ["OPay", "PalmPay", "Bank Transfer", "Visa", "Mastercard", "MTN MoMo", "M-Pesa", "Airtel Money"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": True,
        "founded": "2007",
        "hq": "Limassol, Cyprus",
        "key_sports": ["Football", "Basketball", "Tennis", "Cricket", "MMA", "E-Sports", "Table Tennis", "Darts"],
        "standout": "50+ sports markets, widest odds range in Africa, live streaming for thousands of events",
    },
    {
        "name": "Betway",
        "slug": "betway-review",
        "abbr": "BW",
        "bg": "#00aeef",
        "tc": "#000",
        "tag": "International Brand – Fast Payouts Across 12 African Countries",
        "welcome": "Up to ₦100,000 in Free Bets – First 7 Days (Nigeria)",
        "bonus_top": "10% of settled stakes up to ₦100,000/day for first 7 days",
        "acca_boost": None,
        "promo_code": "WAYBON",
        "stars": 4,
        "min_deposit": "₦1,000",
        "min_stake": "₦100",
        "instant_withdrawal": True,
        "cashout": True,
        "live_streaming": True,
        "sports_count": 28,
        "licence": "NLRC (Nigeria), BCLB (Kenya), NGBB (SA), Gaming Commission of Ghana",
        "countries": ["Nigeria", "Kenya", "South Africa", "Ghana", "Tanzania", "Uganda", "Zambia", "Zimbabwe", "Mozambique", "Rwanda", "Namibia", "Botswana", "Ethiopia"],
        "payment_methods": ["OPay", "Bank Transfer", "Visa", "Mastercard", "M-Pesa", "MTN MoMo", "EFT", "Capitec"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": True,
        "founded": "2006",
        "hq": "Malta / Johannesburg",
        "key_sports": ["Football", "Basketball", "Tennis", "Rugby", "Cricket", "Golf", "Horse Racing"],
        "standout": "Most trusted international brand in Africa, 12+ African countries, Premier League & CAF partnerships",
    },
    {
        "name": "Hollywoodbets",
        "slug": "hollywoodbets-review",
        "abbr": "HW",
        "bg": "#3B1EA5",
        "tc": "#fff",
        "tag": "South Africa's Biggest Homegrown Bookmaker",
        "welcome": "R25 Free Bet on Registration (no deposit required)",
        "bonus_top": "R25 free bet on signup + ongoing daily promotions",
        "acca_boost": None,
        "promo_code": "HOLLYWOODBETS",
        "stars": 5,
        "min_deposit": "R5",
        "min_stake": "R1",
        "instant_withdrawal": True,
        "cashout": True,
        "live_streaming": True,
        "sports_count": 30,
        "licence": "Western Cape Gambling and Racing Board (South Africa)",
        "countries": ["South Africa", "Kenya", "Uganda", "Tanzania", "Mozambique", "Zambia", "Zimbabwe", "Namibia"],
        "payment_methods": ["Instant EFT", "Visa", "Mastercard", "Capitec", "Nedbank", "FNB", "Standard Bank", "Blue Voucher", "M-Pesa"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": True,
        "founded": "1999",
        "hq": "Durban, South Africa",
        "key_sports": ["Football", "Rugby", "Cricket", "Horse Racing", "Basketball", "Tennis", "Golf"],
        "standout": "25+ years in SA betting, NSFAS-excluded banking, Purple Trust responsible gambling programme",
    },
    {
        "name": "Betika",
        "slug": "betika-review",
        "abbr": "BT",
        "bg": "#007A4D",
        "tc": "#fff",
        "tag": "Operator of the Year 2025 – 8M+ Users Across East Africa",
        "welcome": "Free Bet Gifts + Aviator Free Bets on Signup",
        "bonus_top": "Registration free bet + regular Aviator drops (KSh 30–500)",
        "acca_boost": None,
        "promo_code": None,
        "stars": 5,
        "min_deposit": "KSh 10",
        "min_stake": "KSh 1",
        "instant_withdrawal": True,
        "cashout": True,
        "live_streaming": False,
        "sports_count": 20,
        "licence": "BCLB Licence No. BK0000679",
        "countries": ["Kenya", "Tanzania", "Uganda", "Malawi", "Ghana"],
        "payment_methods": ["M-Pesa", "Airtel Money", "Equitel", "USSD *644#", "Betika USSD"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": True,
        "founded": "2016",
        "hq": "Nairobi, Kenya",
        "key_sports": ["Football", "Basketball", "Tennis", "Rugby", "Virtual Sports", "Aviator"],
        "standout": "Operator of the Year 2025, 8M+ users, USSD *644# for non-smartphone users, Kenya Premier League data",
    },
    {
        "name": "SportPesa",
        "slug": "sportpesa-review",
        "abbr": "SP",
        "bg": "#00BF5C",
        "tc": "#fff",
        "tag": "Official Sponsor of the SportPesa Premier League (Kenya)",
        "welcome": "300% Welcome Karibu Gift on First Deposit",
        "bonus_top": "300% match as free bets",
        "acca_boost": None,
        "promo_code": None,
        "stars": 5,
        "min_deposit": "KSh 10",
        "min_stake": "KSh 1",
        "instant_withdrawal": True,
        "cashout": True,
        "live_streaming": True,
        "sports_count": 30,
        "licence": "BCLB Licensed",
        "countries": ["Kenya", "Tanzania", "Uganda", "Rwanda"],
        "payment_methods": ["M-Pesa", "Airtel Money", "Bank Transfer", "Visa", "Mastercard"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": True,
        "founded": "2014",
        "hq": "Nairobi, Kenya",
        "key_sports": ["Football", "Rugby", "Cricket", "Basketball", "Tennis", "Esports"],
        "standout": "Named Kenya Premier League sponsor, jackpots from KSh 10, Mega Jackpot weekly prize pool",
    },
    {
        "name": "Melbet",
        "slug": "melbet-review",
        "abbr": "MB",
        "bg": "#FD1B26",
        "tc": "#fff",
        "tag": "200%–300% Bonus – 150+ Sports Markets",
        "welcome": "200% First Deposit Bonus – Up to ₦480,000 (Nigeria) / 300% up to KSh 1,500 (Kenya)",
        "bonus_top": "200% first deposit match (Nigeria)",
        "acca_boost": None,
        "promo_code": "MBMAX",
        "stars": 4,
        "min_deposit": "₦100",
        "min_stake": "₦20",
        "instant_withdrawal": False,
        "cashout": False,
        "live_streaming": True,
        "sports_count": 150,
        "licence": "NLRC Licensed (Nigeria), BCLB Licensed (Kenya), Curaçao (international)",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania", "Ethiopia", "Ivory Coast", "Cameroon"],
        "payment_methods": ["OPay", "Bank Transfer", "Visa", "Mastercard", "MTN MoMo", "M-Pesa", "Airtel Money"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": True,
        "founded": "2012",
        "hq": "Limassol, Cyprus",
        "key_sports": ["Football", "Basketball", "Tennis", "Cricket", "MMA", "E-Sports", "Darts", "Badminton", "Futsal", "Beach Volleyball"],
        "standout": "150+ sports, widest range of niche markets, live betting on 1,000+ daily events",
    },
    {
        "name": "MozzartBet",
        "slug": "mozzartbet-review",
        "abbr": "MZ",
        "bg": "#280071",
        "tc": "#FFD700",
        "tag": "100% Bonus + 500 Aviator Free Bets",
        "welcome": "100% Bonus Up to ₦50,000 + 500 Aviator Free Bets",
        "bonus_top": "100% match deposit up to ₦50,000 + 500 Aviator bets",
        "acca_boost": None,
        "promo_code": None,
        "stars": 4,
        "min_deposit": "₦100",
        "min_stake": "₦50",
        "instant_withdrawal": True,
        "cashout": True,
        "live_streaming": False,
        "sports_count": 20,
        "licence": "NLRC Licensed (Nigeria), BCLB Licensed (Kenya)",
        "countries": ["Nigeria", "Kenya", "Zimbabwe"],
        "payment_methods": ["OPay", "Bank Transfer", "Visa", "Mastercard", "M-Pesa", "Airtel Money"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": True,
        "founded": "1998",
        "hq": "Belgrade, Serbia",
        "key_sports": ["Football", "Basketball", "Tennis", "Aviator", "Virtual Sports"],
        "standout": "European heritage brand, strong Aviator crash game following, 25+ years of betting experience",
    },
    {
        "name": "NairaBet",
        "slug": "nairabet-review",
        "abbr": "NB",
        "bg": "#1B5E20",
        "tc": "#fff",
        "tag": "Nigeria's Pioneer Bookmaker – Est. 2009",
        "welcome": "Free Bet on First Deposit + Daily Free Bets for Active Players",
        "bonus_top": "Welcome free bet + daily loyalty free bets",
        "acca_boost": None,
        "promo_code": None,
        "stars": 4,
        "min_deposit": "₦100",
        "min_stake": "₦50",
        "instant_withdrawal": True,
        "cashout": True,
        "live_streaming": False,
        "sports_count": 25,
        "licence": "NLRC Licensed",
        "countries": ["Nigeria"],
        "payment_methods": ["OPay", "PalmPay", "Bank Transfer", "Visa", "Mastercard"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": True,
        "founded": "2009",
        "hq": "Lagos, Nigeria",
        "key_sports": ["Football", "Basketball", "Tennis", "Virtual Sports", "Horse Racing"],
        "standout": "Nigeria's first online bookmaker, 15+ years of trust, daily free bets programme for active bettors",
    },
    {
        "name": "22Bet",
        "slug": "22bet-review",
        "abbr": "22",
        "bg": "#FF6B00",
        "tc": "#fff",
        "tag": "100% Bonus – Reliable Fast Payouts",
        "welcome": "100% First Deposit Bonus – Up to ₦207,500 (Nigeria) / KSh 19,000 (Kenya)",
        "bonus_top": "100% first deposit match",
        "acca_boost": None,
        "promo_code": "BNSNG",
        "stars": 4,
        "min_deposit": "₦100",
        "min_stake": "₦20",
        "instant_withdrawal": True,
        "cashout": True,
        "live_streaming": False,
        "sports_count": 35,
        "licence": "NLRC Licensed (Nigeria), BCLB Licensed (Kenya), Curaçao (international)",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania", "Ethiopia"],
        "payment_methods": ["OPay", "Bank Transfer", "Visa", "Mastercard", "MTN MoMo", "M-Pesa"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": True,
        "founded": "2018",
        "hq": "Limassol, Cyprus",
        "key_sports": ["Football", "Basketball", "Tennis", "Cricket", "Boxing", "E-Sports"],
        "standout": "35 sports, competitive odds, straightforward 5x wagering on bonus, proven fast payout track record",
    },
    {
        "name": "Betpawa",
        "slug": "betpawa-review",
        "abbr": "BPW",
        "bg": "#388E3C",
        "tc": "#fff",
        "tag": "Jackpot from Just ₦50 – Pan-African Operator",
        "welcome": "Weekly Jackpot – Win Millions from ₦50 Stake",
        "bonus_top": "Weekly jackpot from ₦50 stake",
        "acca_boost": None,
        "promo_code": None,
        "stars": 4,
        "min_deposit": "₦50",
        "min_stake": "₦1",
        "instant_withdrawal": True,
        "cashout": False,
        "live_streaming": False,
        "sports_count": 15,
        "licence": "NLRC Licensed (Nigeria), BCLB Licensed (Kenya), Gambling Commission (Ghana)",
        "countries": ["Nigeria", "Kenya", "Ghana", "Uganda", "Tanzania", "Zambia"],
        "payment_methods": ["OPay", "MTN MoMo", "Bank Transfer", "Visa", "M-Pesa", "Airtel Money"],
        "mobile_app": True,
        "virtual_sports": False,
        "casino": False,
        "founded": "2016",
        "hq": "Nairobi, Kenya",
        "key_sports": ["Football", "Basketball", "Tennis"],
        "standout": "Ultra-low minimum stake (₦1), weekly jackpot accessible for as little as ₦50, 6 African countries",
    },
    {
        "name": "BetWinner",
        "slug": "betwinner-review",
        "abbr": "BN",
        "bg": "#0055A4",
        "tc": "#fff",
        "tag": "200% Bonus – Easy 5x Wagering on 40+ Sports",
        "welcome": "200% First Deposit Bonus – Up to ₦130,000 (Nigeria) / KSh 16,250 (Kenya)",
        "bonus_top": "200% first deposit match",
        "acca_boost": None,
        "promo_code": "WBONUS1",
        "stars": 3,
        "min_deposit": "₦400",
        "min_stake": "₦20",
        "instant_withdrawal": False,
        "cashout": True,
        "live_streaming": True,
        "sports_count": 40,
        "licence": "NLRC Licensed (Nigeria), BCLB Licensed (Kenya), Curaçao",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania", "Uganda"],
        "payment_methods": ["Bank Transfer", "Visa", "Mastercard", "MTN MoMo", "OPay", "M-Pesa", "Airtel Money"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": True,
        "founded": "2018",
        "hq": "Limassol, Cyprus",
        "key_sports": ["Football", "Basketball", "Tennis", "Cricket", "MMA", "E-Sports", "Volleyball", "Table Tennis"],
        "standout": "40+ sports, 200% bonus with achievable 5x wagering, live streaming on major events",
    },
    {
        "name": "Odibets",
        "slug": "odibets-review",
        "abbr": "OD",
        "bg": "#8BC34A",
        "tc": "#111",
        "tag": "Bet from KSh 10 – Kenya's Low-Stake Champion",
        "welcome": "KSh 30 Free Bet on Registration – No Deposit Needed",
        "bonus_top": "KSh 30 registration free bet",
        "acca_boost": None,
        "promo_code": None,
        "stars": 4,
        "min_deposit": "KSh 10",
        "min_stake": "KSh 1",
        "instant_withdrawal": True,
        "cashout": True,
        "live_streaming": False,
        "sports_count": 20,
        "licence": "BCLB Licensed",
        "countries": ["Kenya"],
        "payment_methods": ["M-Pesa", "Airtel Money"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": False,
        "founded": "2017",
        "hq": "Nairobi, Kenya",
        "key_sports": ["Football", "Basketball", "Tennis", "Rugby", "Virtual Sports"],
        "standout": "Ultra-affordable entry point (KSh 1 min stake), M-Pesa instant, strong Kenyan football coverage",
    },
    {
        "name": "Supabets",
        "slug": "supabets-review",
        "abbr": "SU",
        "bg": "#D50000",
        "tc": "#fff",
        "tag": "South Africa's Homegrown Underdog – Massive Jackpots",
        "welcome": "R10 Free Bet on Registration",
        "bonus_top": "R10 registration free bet + SuperBanker weekly bonus",
        "acca_boost": None,
        "promo_code": None,
        "stars": 4,
        "min_deposit": "R5",
        "min_stake": "R0",
        "instant_withdrawal": True,
        "cashout": True,
        "live_streaming": False,
        "sports_count": 20,
        "licence": "Western Cape Gambling and Racing Board",
        "countries": ["South Africa", "Zimbabwe", "Zambia"],
        "payment_methods": ["Instant EFT", "Visa", "Mastercard", "Capitec", "FNB", "Standard Bank"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": True,
        "founded": "2008",
        "hq": "Cape Town, South Africa",
        "key_sports": ["Football", "Rugby", "Cricket", "Basketball", "Tennis", "Horse Racing"],
        "standout": "SA-born and operated, PSL focus, SuperBanker weekly cash bonuses, low-cost entry",
    },
    {
        "name": "Bangbet",
        "slug": "bangbet-review",
        "abbr": "BB",
        "bg": "#1C1E24",
        "tc": "#f9c633",
        "tag": "Low Minimum Stake – Great for New Bettors",
        "welcome": "Deposit ₦50, Get ₦200 in Free Bets (Nigeria) / Deposit KSh 10, Get KSh 50 (Kenya)",
        "bonus_top": "₦200 in free bets after first deposit",
        "acca_boost": None,
        "promo_code": None,
        "stars": 3,
        "min_deposit": "₦50",
        "min_stake": "₦10",
        "instant_withdrawal": True,
        "cashout": False,
        "live_streaming": False,
        "sports_count": 20,
        "licence": "NLRC Licensed (Nigeria), BCLB Licensed (Kenya)",
        "countries": ["Nigeria", "Kenya"],
        "payment_methods": ["OPay", "Bank Transfer", "Visa", "Mastercard", "M-Pesa", "Airtel Money"],
        "mobile_app": True,
        "virtual_sports": False,
        "casino": False,
        "founded": "2020",
        "hq": "Lagos, Nigeria",
        "key_sports": ["Football", "Basketball", "Tennis"],
        "standout": "Beginner-friendly low stakes, dual Nigeria-Kenya presence, clean mobile interface",
    },
    {
        "name": "HelaBet",
        "slug": "helabet-review",
        "abbr": "HB",
        "bg": "#1565C0",
        "tc": "#fff",
        "tag": "Licensed Kenyan Brand – Instant M-Pesa Payouts",
        "welcome": "100% Welcome Bonus – Up to KSh 5,000",
        "bonus_top": "100% match on first deposit up to KSh 5,000",
        "acca_boost": None,
        "promo_code": None,
        "stars": 4,
        "min_deposit": "KSh 10",
        "min_stake": "KSh 1",
        "instant_withdrawal": True,
        "cashout": True,
        "live_streaming": False,
        "sports_count": 25,
        "licence": "BCLB Licensed",
        "countries": ["Kenya"],
        "payment_methods": ["M-Pesa", "Airtel Money", "Bank Transfer"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": False,
        "founded": "2019",
        "hq": "Nairobi, Kenya",
        "key_sports": ["Football", "Basketball", "Tennis", "Rugby", "Volleyball"],
        "standout": "Kenya-focused, instant M-Pesa, strong KPL and EPL coverage, clean local app",
    },
    {
        "name": "Paripesa",
        "slug": "paripesa-review",
        "abbr": "PP",
        "bg": "#2E7D32",
        "tc": "#fff",
        "tag": "200% Bonus – 50+ Sports Markets Rising Fast in Africa",
        "welcome": "200% First Deposit Bonus – Up to ₦200,000 (Nigeria) / KSh 20,000 (Kenya)",
        "bonus_top": "200% first deposit match",
        "acca_boost": None,
        "promo_code": None,
        "stars": 4,
        "min_deposit": "₦100",
        "min_stake": "₦20",
        "instant_withdrawal": True,
        "cashout": True,
        "live_streaming": True,
        "sports_count": 50,
        "licence": "NLRC Licensed (Nigeria), BCLB Licensed (Kenya), Curaçao",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania"],
        "payment_methods": ["OPay", "PalmPay", "Bank Transfer", "Visa", "Mastercard", "M-Pesa", "Airtel Money"],
        "mobile_app": True,
        "virtual_sports": True,
        "casino": True,
        "founded": "2020",
        "hq": "Limassol, Cyprus",
        "key_sports": ["Football", "Basketball", "Tennis", "Cricket", "E-Sports", "MMA"],
        "standout": "50+ sports, fast-growing African presence, competitive 200% bonus with live streaming",
    },
]

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""You are a senior iGaming journalist and professional copywriter for SifuFinds ({SITE_URL}), Africa's #1 sports betting comparison platform, covering 19 African countries.

Your task is to write authoritative, long-form bookmaker reviews in the style of a respected iGaming publication — think iGaming Business or Gambling.com, but written for the African betting market.

WRITING STANDARDS:
- Voice: Authoritative, analytical, insider knowledge — like a journalist who has personally tested the platform
- Tone: Honest, balanced, and professional — praise genuine strengths, flag real weaknesses
- Depth: Cover every aspect a bettor needs before depositing — bonus mechanics, odds quality, payment speed, mobile experience
- African context: Reference local payment methods, currencies, mobile usage habits, football leagues (NPFL, KPL, PSL, GPL, CAF), local operators

REVIEW STRUCTURE — write EACH section in full. Do not abbreviate or rush any section.
1. **Introduction** (180-220 words) — Start with a compelling hook. Place the bookmaker in context: how long have they been in the African market, what makes them notable, who is their primary audience, what sets them apart from the competition. Paint a picture that makes the reader want to keep reading.
2. **Welcome Bonus & Promotions** (220-280 words) — Explain the welcome offer in complete detail: the exact amount or percentage, what qualifies, the wagering requirements step-by-step, time limits, minimum odds restrictions, promo code if applicable. Assess: is this genuinely good value for an African bettor? Compare briefly to rival offers. Mention any ongoing promotions beyond the welcome offer.
3. **Sports Markets & Odds** (220-280 words) — Detail the breadth of sports available, naming specific leagues covered. Discuss the depth of markets within each sport (pre-match, specials, player props). Assess odds competitiveness — are they tighter or looser than Betway/1xBet/Bet9ja? Which sport has the best market depth here?
4. **Mobile App & User Experience** (180-220 words) — Describe the Android and iOS app experience in detail. How does it load? Is the interface cluttered or clean? Does it support USSD for non-smartphone users? How does the desktop experience compare? Specific design observations that help the reader visualise the platform.
5. **Payment Methods & Withdrawal Speed** (180-220 words) — List all accepted payment methods with their specific limits. How long does a deposit take? How long does a typical withdrawal take? Any limits or fees? Discuss the experience for each major African payment method: OPay, M-Pesa, MTN MoMo, bank transfer. Are there complaints about slow payouts?
6. **Live Betting & Streaming** (150-180 words) — How deep is the in-play offering? Which sports have live betting? Is cash-out available and on which markets? If streaming is available, which events? If not, how does this compare to rivals who do offer it?
7. **Customer Support** (130-160 words) — What support channels exist: live chat, WhatsApp, email, phone? What are the operating hours? Is support available in local languages (Pidgin, Swahili, Zulu, etc.)? Share any typical response time expectations. Is the support quality good based on available information?
8. **Responsible Gambling** (130-160 words) — What responsible gambling tools does the operator provide? Deposit limits, self-exclusion, cool-off periods, reality checks. Does the operator support GamCare, BeGambleAware or local African equivalents? Is the messaging around responsible gambling visible and accessible in their app/website?
9. **Pros & Cons** — Bullet list: 5-6 distinct pros, 4-5 distinct cons. Each point should be specific, not generic.
10. **SifuFinds Verdict** (180-220 words) — Give a clear, decisive verdict. State the star rating (X/5) explicitly and explain it. Recommend who this bookmaker is best suited for (e.g., casual Nigerian football fan, serious accumulator punter, new bettors, high-stakes players). Give a clear bottom-line recommendation.

OUTPUT FORMAT — return EXACTLY this structure:

===META===
{{
  "category": "review",
  "icon": "⭐",
  "title": "Brand Name Review [Year]: Is It Worth It for African Bettors?",
  "slug": "brand-slug-review",
  "excerpt": "150-200 char excerpt — summarise verdict and top feature",
  "image_color": "#hexcolor",
  "tags": ["Review", "Brand Name", "Bookmaker", "Country"],
  "featured": false,
  "bookmaker_featured": "Brand Name",
  "read_time": 8,
  "stars": 4,
  "brand_name": "Brand Name"
}}
===BLOG===
[Full review in markdown — 1500-2000 words]
[Use ## for section headings]
[Use **bold** for key terms and bonus amounts]
[Include a pros/cons bullet list]
[End with CTA: Compare {SITE_URL} for today's best odds and bonuses]
[Final line: *18+ | Bet Responsibly | T&Cs Apply | {SITE_URL}*]
===END==="""


# ── REVIEW GENERATION ─────────────────────────────────────────────────────────

def generate_review(brand: dict) -> Optional[dict]:
    today = datetime.now(timezone.utc).strftime("%B %Y")

    user_message = f"""Write a comprehensive, professional review for {brand['name']} — a bookmaker operating in {', '.join(brand['countries'])}.

BRAND DATA (use this as your source of truth — do not invent facts):
- Full name: {brand['name']}
- Tagline: {brand['tag']}
- Welcome offer: {brand['welcome']}
- Bonus top-line: {brand['bonus_top']}
- Promo code: {brand.get('promo_code') or 'None published'}
- Star rating: {brand['stars']}/5
- Minimum deposit: {brand['min_deposit']}
- Minimum stake: {brand['min_stake']}
- Instant withdrawals: {'Yes' if brand['instant_withdrawal'] else 'No'}
- Cash-out feature: {'Yes' if brand['cashout'] else 'No'}
- Live streaming: {'Yes' if brand['live_streaming'] else 'No'}
- Sports markets: {brand['sports_count']}+ sports
- Licence: {brand['licence']}
- Operating countries: {', '.join(brand['countries'])}
- Payment methods: {', '.join(brand['payment_methods'])}
- Mobile app: {'Yes' if brand['mobile_app'] else 'No'}
- Virtual sports: {'Yes' if brand['virtual_sports'] else 'No'}
- Casino: {'Yes' if brand['casino'] else 'No'}
- Founded: {brand.get('founded', 'N/A')}
- Headquarters: {brand.get('hq', 'N/A')}
- Key sports: {', '.join(brand['key_sports'])}
- What makes them stand out: {brand['standout']}

CONTEXT: This review is for {today} on SifuFinds, Africa's #1 betting comparison.

Write the full review now. ABSOLUTE LENGTH REQUIREMENT: The ===BLOG=== section MUST contain at minimum 1500 words and ideally 1800-2000 words. Each numbered section must reach its stated word count — do not truncate or summarise any section. If you find yourself under 1500 words total, go back and expand each section with more specific analysis, examples, and context. Quality and length are both required. Stay strictly within the facts provided above — do not invent bonus amounts, odd values, or features not listed."""

    try:
        print(f"  🤖 Generating review for {brand['name']}...")
        raw = ask_long(SYSTEM_PROMPT, user_message)

        meta_raw = _extract(raw, "===META===", "===BLOG===")
        blog_body = _extract(raw, "===BLOG===", "===END===")

        if not meta_raw or not blog_body:
            print(f"  ✗ LLM response missing required sections for {brand['name']}")
            return None

        meta = json.loads(_clean_json(meta_raw))

        return {
            "id": f"review-{brand['slug']}-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            "category": "review",
            "title": meta.get("title", f"{brand['name']} Review 2026"),
            "slug": meta.get("slug", brand["slug"]),
            "excerpt": meta.get("excerpt", ""),
            "body": blog_body.strip(),
            "author": "SifuFinds Editorial Team",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "image_color": meta.get("image_color", brand["bg"]),
            "image_icon": meta.get("icon", "⭐"),
            "tags": meta.get("tags", ["Review", brand["name"]]),
            "featured": False,
            "bookmaker_featured": brand["name"],
            "read_time": meta.get("read_time", 8),
            "stars": meta.get("stars", brand["stars"]),
            "brand_name": brand["name"],
        }

    except json.JSONDecodeError as e:
        print(f"  ✗ JSON parse error for {brand['name']}: {e}")
        return None
    except Exception as e:
        print(f"  ✗ Error generating {brand['name']} review: {e}")
        return None


def _extract(text: str, start: str, end: str) -> str:
    try:
        s = text.index(start) + len(start)
        e = text.index(end, s)
        return text[s:e].strip()
    except ValueError:
        return ""


def _clean_json(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("```")[1]
        if s.startswith("json"):
            s = s[4:]
    return s.strip()


# ── POSTS STORAGE ─────────────────────────────────────────────────────────────

POSTS_PATH = Path(__file__).parent.parent.parent / "blog" / "posts.json"


def load_posts() -> list:
    if POSTS_PATH.exists():
        try:
            with open(POSTS_PATH) as f:
                return json.load(f).get("posts", [])
        except Exception:
            return []
    return []


def save_posts(posts: list) -> None:
    POSTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"posts": posts}
    with open(POSTS_PATH, "w") as f:
        json.dump(payload, f, indent=2)
    js_path = POSTS_PATH.parent / "posts-data.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(f"window.POSTS_DATA={json.dumps(payload, ensure_ascii=False)};\n")


# ── MAIN RUNNER ───────────────────────────────────────────────────────────────

def run(brand_name: Optional[str] = None, limit: Optional[int] = None) -> None:
    targets = BRANDS
    if brand_name:
        targets = [b for b in BRANDS if b["name"].lower() == brand_name.lower()]
        if not targets:
            print(f"✗ Brand '{brand_name}' not found. Available: {', '.join(b['name'] for b in BRANDS)}")
            return
    if limit:
        targets = targets[:limit]

    print(f"📝 Generating {len(targets)} brand review(s)...")

    existing = load_posts()
    reviewed_slugs = {p["slug"] for p in existing if p.get("category") == "review"}
    new_reviews: list[dict] = []

    for brand in targets:
        if brand["slug"] in reviewed_slugs:
            print(f"  ↳ {brand['name']}: review already exists — skipping (delete to regenerate)")
            continue
        print(f"\n⭐ Reviewing: {brand['name']}")
        review = generate_review(brand)
        if review:
            new_reviews.append(review)
            reviewed_slugs.add(brand["slug"])
            print(f"  ✓ '{review['title'][:60]}...' ({len(review['body'].split())} words)")
        else:
            print(f"  ✗ Failed — skipping {brand['name']}")

    if new_reviews:
        all_posts = new_reviews + existing
        all_posts = all_posts[:100]  # cap at 100 total posts
        save_posts(all_posts)
        print(f"\n✅ Added {len(new_reviews)} review(s). Total posts: {len(all_posts)}")
    else:
        print("\n⚠ No new reviews generated.")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Brand Review Writer")
    parser.add_argument("--brand", type=str, default=None, help="Single brand name to review")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of brands to process")
    args = parser.parse_args()

    run(brand_name=args.brand, limit=args.limit)
