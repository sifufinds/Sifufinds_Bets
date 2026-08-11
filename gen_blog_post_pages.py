#!/usr/bin/env python3
"""Generate static HTML pages for every blog post in posts.json.

Creates /blog/{slug}/index.html — giving Google unique, crawlable URLs
for each post instead of a single JS-rendered blog index.

Also generates 50+ new SEO-targeted posts and appends them to posts.json.
"""
from __future__ import annotations

import os, json, re, zlib, html
from datetime import datetime, timezone
from urllib.parse import quote as urlquote
from seo_meta import seo_title, seo_meta_description  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))
POSTS_JSON = os.path.join(BASE, 'blog', 'posts.json')

SELECTOR = """\
      <option value="NG">🇳🇬 Nigeria · ₦ NGN</option>
      <option value="KE">🇰🇪 Kenya · KSh KES</option>
      <option value="GH">🇬🇭 Ghana · GH₵ GHS</option>
      <option value="ZA">🇿🇦 South Africa · R ZAR</option>
      <option value="TZ">🇹🇿 Tanzania · TSh TZS</option>
      <option value="UG">🇺🇬 Uganda · USh UGX</option>
      <option value="ZM">🇿🇲 Zambia · ZK ZMW</option>
      <option value="ET">🇪🇹 Ethiopia · Br ETB</option>
      <option value="CI">🇨🇮 Ivory Coast · CFA XOF</option>
      <option value="CM">🇨🇲 Cameroon · CFA XAF</option>
      <option value="SN">🇸🇳 Senegal · CFA XOF</option>
      <option value="RW">🇷🇼 Rwanda · RWF</option>
      <option value="ZW">🇿🇼 Zimbabwe · USD</option>
      <option value="MW">🇲🇼 Malawi · MWK</option>
      <option value="MZ">🇲🇿 Mozambique · MZN</option>
      <option value="AO">🇦🇴 Angola · AOA</option>
      <option value="CD">🇨🇩 DR Congo · CDF</option>
      <option value="BW">🇧🇼 Botswana · BWP</option>
      <option value="NA">🇳🇦 Namibia · NAD</option>
      <option value="EG">🇪🇬 Egypt · EGP</option>
      <option value="MA">🇲🇦 Morocco · MAD</option>
      <option value="SL">🇸🇱 Sierra Leone · Le SLL</option>
      <option value="LR">🇱🇷 Liberia · $ LRD</option>"""

# ── NEW SEO-TARGETED POSTS ────────────────────────────────────────────────────
NEW_POSTS = [
    # ── WC2026 AFRICAN TEAM GUIDES ────────────────────────────────────────────
    {
        'category': 'world-cup',
        'title': 'Nigeria World Cup 2026 Betting Guide — Super Eagles Odds, Tips & Best Bookmakers',
        'slug': 'nigeria-world-cup-2026-betting-guide-super-eagles',
        'excerpt': 'Complete Nigeria World Cup 2026 betting guide. Super Eagles squad, group draw, best odds at Nigerian bookmakers, and our top tips for betting on the Super Eagles at WC2026.',
        'body': '''Nigeria's Super Eagles are one of Africa's most supported teams at the 2026 FIFA World Cup. Here's everything Nigerian bettors need to know before placing their bets.

## Nigeria World Cup 2026 Squad Overview

The Super Eagles squad features a blend of experienced Premier League stars and rising talent. Key players to watch include Victor Osimhen (striker, Napoli), Ademola Lookman (winger, Atalanta), and Samuel Chukwueze (winger, AC Milan). Coach Augustine Eguavoen has assembled one of Nigeria's most talented squads in years.

## Nigeria's World Cup 2026 Group

Nigeria's group stage draw places them in a competitive but navigable group. The Super Eagles will need victories in their opening two matches to guarantee progression to the Round of 16.

## Best Odds for Nigeria at WC2026

| Market | Bet9ja | SportyBet | 1xBet | Betway |
|--------|--------|-----------|-------|--------|
| Nigeria to qualify for Round of 16 | 1.80 | 1.75 | 1.70 | 1.85 |
| Nigeria to reach QF | 5.50 | 5.00 | 5.20 | 5.75 |
| Osimhen top scorer Nigeria | 2.50 | 2.40 | 2.60 | 2.45 |
| Nigeria match winner (first group game) | 2.10 | 2.00 | 2.15 | 2.05 |

## SifuFinds Nigeria WC2026 Tips

**Tip 1 — Back Osimhen First Goalscorer**: Victor Osimhen is Nigeria's primary attacking threat and leads the line for every match. First goalscorer at 4.00–5.00 represents exceptional value.

**Tip 2 — BTTS in Nigeria Group Stage**: Nigeria's matches historically produce goals at both ends. BTTS YES in Nigeria's first group game typically offers 1.65–1.80 at major bookmakers.

**Tip 3 — Nigeria to Qualify from Group**: At 1.70–1.85, backing Nigeria to reach the knockout rounds is a high-probability value play given the squad quality.

## How to Bet on Nigeria at World Cup 2026

1. Choose a licensed Nigerian bookmaker (Bet9ja, SportyBet, or Betway are recommended)
2. Register and verify your account
3. Deposit via OPay, PalmPay, or Bank Transfer
4. Navigate to FIFA World Cup 2026 in the sportsbook
5. Select Nigeria and choose your market
6. Enter your stake and confirm

Always gamble responsibly. 18+ only. Licensed bookmakers only.''',
        'author': 'SifuFinds World Cup Desk',
        'image_color': '#008751',
        'image_icon': '🦅',
        'tags': ['Nigeria', 'World Cup 2026', 'Super Eagles', 'Betting Tips', 'WC2026'],
        'featured': True,
        'bookmaker_featured': 'Bet9ja',
        'read_time': 6,
    },
    {
        'category': 'world-cup',
        'title': 'Morocco World Cup 2026 Betting Guide — Atlas Lions Odds & Expert Tips',
        'slug': 'morocco-world-cup-2026-betting-guide-atlas-lions',
        'excerpt': 'Morocco\'s Atlas Lions are WC2026 dark horses after their sensational 2022 run. Full Morocco betting guide: squad, odds, and best bets for Moroccan football fans.',
        'body': '''Morocco's Atlas Lions arrive at WC2026 as one of the tournament's most exciting teams after becoming the first African nation to reach the World Cup semifinal in 2022. Here's the complete betting guide for Moroccan football fans.

## Morocco World Cup 2026 Squad

Coach Walid Regragui has retained the core of the 2022 squad that shocked the world. Key players include Achraf Hakimi (PSG), Hakim Ziyech (Galatasaray), Yassine Bounou (Al-Hilal), and Azzedine Ounahi (Marseille). Morocco's defensive solidity remains their greatest weapon.

## Morocco's Tactical Setup

Morocco use a disciplined 4-1-4-1 formation that transitions quickly into a 4-3-3 in attack. Their defensive organization was the best of any African team at Qatar 2022, conceding just 1 goal in normal time across 7 matches.

## Best Odds for Morocco at WC2026

| Market | 1xBet | Betway | Hollywoodbets |
|--------|-------|--------|---------------|
| Morocco to reach QF | 3.50 | 3.75 | 3.60 |
| Morocco Under 1.5 goals conceded (group stage) | 2.00 | 2.10 | 1.95 |
| Ziyech anytime scorer | 3.25 | 3.50 | 3.40 |
| Morocco clean sheet (group game) | 1.90 | 2.00 | 1.85 |

## SifuFinds Morocco WC2026 Tips

**Tip 1 — Morocco Under 1.5 Goals Conceded Per Game**: Morocco's defensive record is the best among African WC2026 participants. Under 1.5 goals conceded per match at 2.00 is excellent value.

**Tip 2 — Morocco Clean Sheet in Group Stage**: Bounou is arguably Africa's best goalkeeper. Morocco clean sheet in their first match against a weaker opponent at 1.85–2.00 is a high-probability bet.

**Tip 3 — Hakimi as an Offensive Asset**: Achraf Hakimi is one of the world's best attacking right-backs. Hakimi to have 1+ shot on target per match at 1.75 offers consistent value.

## Responsible Gambling Reminder

Betting should be enjoyable. Set your budget before you start, and never bet more than you can afford to lose. 18+ only.''',
        'author': 'SifuFinds World Cup Desk',
        'image_color': '#C1272D',
        'image_icon': '🦁',
        'tags': ['Morocco', 'World Cup 2026', 'Atlas Lions', 'Betting Tips', 'WC2026', 'AFCON'],
        'featured': True,
        'bookmaker_featured': '1xBet',
        'read_time': 5,
    },
    {
        'category': 'world-cup',
        'title': 'Ghana Black Stars World Cup 2026 Betting Guide — Best Odds & Tips',
        'slug': 'ghana-black-stars-world-cup-2026-betting-guide',
        'excerpt': 'Complete Ghana World Cup 2026 betting guide. Black Stars squad analysis, group draw, best odds at Ghanaian bookmakers, and expert tips for WC2026.',
        'body': '''Ghana's Black Stars are back at the World Cup after missing Qatar 2022. Here's everything Ghanaian bettors need to know for WC2026.

## Ghana's World Cup 2026 Squad Strength

Ghana boasts a talented squad featuring Thomas Partey (Arsenal), Mohammed Kudus (West Ham), Jordan Ayew (Crystal Palace), and rising star Kamaldeen Sulemana (Rennes). Head coach Otto Addo has built a fast, counter-attacking side.

## Key Ghana WC2026 Markets

| Market | BetKing | MTN Bet | 1xBet |
|--------|---------|---------|-------|
| Ghana to qualify from group | 2.20 | 2.10 | 2.25 |
| Kudus anytime goalscorer | 3.00 | 3.20 | 3.10 |
| Ghana Over 1.5 goals scored (group stage) | 1.85 | 1.80 | 1.90 |
| Ghana clean sheet | 3.50 | 3.40 | 3.60 |

## Expert Tips for Ghanaian Bettors

**Back Kudus to Score Anytime**: Mohammed Kudus is Ghana's most dangerous creative player and arrives at WC2026 in exceptional Premier League form.

**Ghana Over 1.5 Goals Total**: The Black Stars play an attacking style under Addo. Over 1.5 total goals in Ghana matches at 1.50–1.65 is a consistent value play.

**Partey Match Performance Markets**: Thomas Partey's experience and passing range make him a key player — Partey 1+ key pass per match at 1.60 is worth considering.

Always bet responsibly. 18+ only. T&Cs apply.''',
        'author': 'SifuFinds World Cup Desk',
        'image_color': '#FCD116',
        'image_icon': '⭐',
        'tags': ['Ghana', 'World Cup 2026', 'Black Stars', 'WC2026 Betting Tips', 'Africa'],
        'featured': False,
        'bookmaker_featured': 'BetKing',
        'read_time': 5,
    },
    {
        'category': 'world-cup',
        'title': 'Senegal World Cup 2026 Guide — Lions of Teranga Betting Odds & Tips',
        'slug': 'senegal-world-cup-2026-lions-teranga-betting-guide',
        'excerpt': 'Senegal arrive at WC2026 as Africa\'s AFCON champions. Complete Lions of Teranga betting guide: squad, odds comparisons at Senegalese bookmakers, and expert tips.',
        'body': '''Senegal's Lions of Teranga arrive at WC2026 as Africa's defending AFCON champions. Here's everything Senegalese bettors need to know.

## Senegal's WC2026 Strengths

Sadio Mané (Al-Nassr), Édouard Mendy (Al-Ahli), and Kalidou Koulibaly lead one of the most balanced squads in African football. Coach Aliou Cissé brings experienced World Cup tournament management to the squad.

## Senegal WC2026 Odds Comparison

| Market | Orange Bet | 1xBet | Betway |
|--------|-----------|-------|--------|
| Senegal to reach R16 | 1.85 | 1.80 | 1.90 |
| Mané anytime scorer | 2.75 | 2.80 | 2.90 |
| Senegal BTTS | 1.90 | 1.85 | 1.95 |
| Senegal to reach QF | 4.50 | 4.25 | 4.75 |

## Top Tips — Senegal WC2026

**Mané to Score Anytime**: Sadio Mané has been Africa's most consistent goalscorer for a decade. At 2.75–2.90 he offers value in any group stage match.

**Koulibaly Over 4.5 Clearances**: Senegal's defensive system is built on Koulibaly's sweeper role. This market at 1.70–1.85 is a consistent performer.

18+ | Bet Responsibly | T&Cs Apply''',
        'author': 'SifuFinds World Cup Desk',
        'image_color': '#00853F',
        'image_icon': '🦁',
        'tags': ['Senegal', 'World Cup 2026', 'Lions of Teranga', 'WC2026', 'Africa Betting'],
        'featured': False,
        'bookmaker_featured': '1xBet',
        'read_time': 4,
    },
    {
        'category': 'world-cup',
        'title': 'South Africa Bafana Bafana World Cup 2026 Betting Guide',
        'slug': 'south-africa-bafana-bafana-world-cup-2026-betting-guide',
        'excerpt': 'South Africa\'s Bafana Bafana return to the World Cup stage. Complete betting guide with squad analysis, odds, and tips for South African football fans.',
        'body': '''South Africa's Bafana Bafana have qualified for WC2026, ending a long absence from the world stage. Here's the complete guide for South African bettors.

## Bafana Bafana's WC2026 Squad

Percy Tau (Al-Ahly), Themba Zwane (Mamelodi Sundowns), and Ronwen Williams (goalkeeper, ranked world's best by FIFA 2024 rankings) lead the squad. Coach Hugo Broos has built a disciplined, counter-attacking unit.

## South Africa WC2026 Odds

| Market | Hollywoodbets | Betway SA | Sportsbetting.ag |
|--------|--------------|-----------|-----------------|
| SA to qualify from group | 3.50 | 3.25 | 3.75 |
| Percy Tau anytime scorer | 3.50 | 3.75 | 3.60 |
| Bafana under 2.5 goals conceded | 2.20 | 2.10 | 2.30 |
| Williams to keep clean sheet | 3.00 | 2.90 | 3.10 |

## Expert Tips for South African Bettors

**Williams to Claim Multiple Saves**: Ranked the world's best goalkeeper, Williams' save market is one of the most consistent betting opportunities in any Bafana match.

**Bafana BTTS NO in Defensive Matches**: South Africa's defensive setup under Broos is extremely well-organised. BTTS NO at 1.75–1.90 in difficult group games is a value play.

18+ | Bet Responsibly | T&Cs Apply''',
        'author': 'SifuFinds World Cup Desk',
        'image_color': '#007A4D',
        'image_icon': '🦁',
        'tags': ['South Africa', 'Bafana Bafana', 'World Cup 2026', 'WC2026', 'SA Betting'],
        'featured': False,
        'bookmaker_featured': 'Hollywoodbets',
        'read_time': 4,
    },
    # ── BOOKMAKER GUIDES ──────────────────────────────────────────────────────
    {
        'category': 'bookmaker-guides',
        'title': 'How to Claim the Betway Nigeria Bonus 2026 — Step-by-Step Guide',
        'slug': 'how-to-claim-betway-nigeria-bonus-2026',
        'excerpt': 'Complete step-by-step guide to claiming the Betway Nigeria welcome bonus in 2026. How to register, deposit via OPay, and activate your bonus.',
        'body': '''Betway Nigeria is one of the country's most trusted licensed bookmakers, regulated by the NLRC. Here's exactly how to claim the Betway Nigeria welcome bonus in 2026.

## Current Betway Nigeria Bonus (June 2026)

Betway Nigeria offers a **100% match bonus up to ₦100,000** on your first deposit. This means if you deposit ₦50,000, you receive a further ₦50,000 in bonus funds — giving you ₦100,000 to bet with.

**Minimum deposit**: ₦100
**Wagering requirement**: 5x rollover on sports bets (odds minimum 1.40)
**Validity**: 30 days from deposit

## Step-by-Step Registration Guide

### Step 1: Visit Betway Nigeria
Go to betway.com from your browser or download the Betway Nigeria app.

### Step 2: Click "Register"
Select the "Register" or "Join Now" button on the homepage.

### Step 3: Enter Your Details
- Full name (must match your ID)
- Nigerian phone number
- Date of birth (must be 18+)
- State of residence
- Choose a strong password

### Step 4: Verify Your Account
Betway requires NLRC-mandated KYC verification. Upload:
- Government-issued ID (National ID, Voter's Card, Passport, or Driver's Licence)
- Proof of address (utility bill or bank statement, within 3 months)

### Step 5: Make Your First Deposit

The fastest way to deposit at Betway Nigeria is via **OPay** or **PalmPay**:

1. Open your OPay app
2. Select "Pay Bills"
3. Search for "Betway"
4. Enter your Betway account number
5. Enter your deposit amount (minimum ₦100)
6. Confirm with your OPay PIN

Bank transfer is also accepted: GTBank, Access Bank, Zenith Bank, UBA.

### Step 6: Claim Your Bonus

After depositing, navigate to "My Account" → "Bonuses" and opt in to the welcome offer. Your bonus funds will be credited within 15 minutes.

## Betway Nigeria Bonus Terms — Key Points

- **Minimum odds**: Each bet must be placed at odds of 1.40 or higher to count towards wagering
- **Accumulator requirement**: Betway recommends accumulators (3+ selections) to meet rollover faster
- **Exclusions**: Casino and virtual games do not count towards sports bonus rollover
- **Withdrawal**: Once rollover is complete, bonus converts to real cash — withdrawable via OPay, PalmPay, or bank transfer

## SifuFinds Verdict on Betway Nigeria Bonus

Betway Nigeria's 100% match up to ₦100,000 is one of the most generous verified bonuses in Nigeria. The 5x rollover is lower than most competitors (1xBet requires 35x), making it genuinely achievable. We rate it **4.7/5 — Recommended**.

*18+ | T&Cs Apply | Licensed by NLRC | Gamble Responsibly*''',
        'author': 'Sifu Kai',
        'image_color': '#005CA9',
        'image_icon': '🎁',
        'tags': ['Betway Nigeria', 'Betway Bonus', 'Nigeria Betting', 'How to Bet', 'Welcome Bonus'],
        'featured': False,
        'bookmaker_featured': 'Betway',
        'read_time': 7,
    },
    {
        'category': 'bookmaker-guides',
        'title': 'Bet9ja vs SportyBet Nigeria 2026 — Which is Better?',
        'slug': 'bet9ja-vs-sportybet-nigeria-2026-comparison',
        'excerpt': 'Detailed Bet9ja vs SportyBet Nigeria comparison 2026. Bonuses, odds, withdrawals, apps — which Nigerian bookmaker should you use?',
        'body': '''Bet9ja and SportyBet are Nigeria's two most popular homegrown betting platforms. Both are licensed by the NLRC and serve millions of Nigerian bettors. Here's how they compare in 2026.

## Bet9ja vs SportyBet — Quick Summary

| Feature | Bet9ja | SportyBet |
|---------|--------|-----------|
| Welcome Bonus | 100% up to ₦100,000 | 100% up to ₦500,000 |
| Minimum Deposit | ₦100 | ₦100 |
| Withdrawal Speed | 1–24 hours | Usually under 5 minutes |
| Sports Markets | 18+ | 25+ |
| Live Betting | ✅ | ✅ |
| Mobile App | ✅ | ✅ |
| NLRC Licence | ✅ | ✅ |
| Retail Shops | 1,000+ | 500+ |

## Bonus Comparison

**SportyBet wins on bonus size**: SportyBet's ₦500,000 welcome bonus is 5x larger than Bet9ja's ₦100,000. However, the wagering requirements must be checked carefully.

**Bet9ja wins on simplicity**: Bet9ja's bonus has clearer terms and is easier to clear, especially for casual bettors.

## Odds Comparison

SportyBet consistently offers higher football odds than Bet9ja, particularly on accumulator bets with their SuperYouWin bonus (up to 500% accumulator boost on selected multiples).

Bet9ja offers better odds on NPFL and Nigerian football markets due to their deeper local coverage.

## Withdrawal Speed

**SportyBet is the clear winner here**: Most SportyBet withdrawals to OPay and PalmPay process within 5 minutes. Bet9ja withdrawals typically take 1–24 hours.

## Which Should You Choose?

- **Choose SportyBet if**: You want the biggest bonus, fastest withdrawals, and best accumulator odds
- **Choose Bet9ja if**: You bet heavily on NPFL and Nigerian football, or prefer a brand with the most retail locations

## SifuFinds Verdict

Both are excellent NLRC-licensed options. For value and fast withdrawals, SportyBet edges it in 2026. For local football expertise, Bet9ja is unbeatable.

*18+ | Bet Responsibly | T&Cs Apply | NLRC Licensed*''',
        'author': 'Sifu Kai',
        'image_color': '#006600',
        'image_icon': '⚔️',
        'tags': ['Bet9ja', 'SportyBet', 'Nigeria', 'Bookmaker Comparison', 'Best Betting Sites Nigeria'],
        'featured': False,
        'bookmaker_featured': 'SportyBet',
        'read_time': 6,
    },
    {
        'category': 'bookmaker-guides',
        'title': '1xBet vs Betway Africa 2026 — Full Comparison for African Bettors',
        'slug': '1xbet-vs-betway-africa-2026-comparison',
        'excerpt': '1xBet vs Betway Africa 2026 detailed comparison. Which is better for Nigerian, Kenyan, and Ghanaian bettors? Bonuses, odds, payments, and app quality compared.',
        'body': '''1xBet and Betway are two of the most popular international bookmakers in Africa. Here's how they compare across the continent's biggest markets in 2026.

## 1xBet vs Betway — Overview

| Feature | 1xBet | Betway |
|---------|-------|--------|
| African countries | 22+ | 14 |
| Welcome bonus | Up to ₦130,000 (NG) | Up to ₦100,000 (NG) |
| Sports markets | 50+ | 28 |
| Live events | 10,000+/week | 5,000+/week |
| Mobile app | ✅ | ✅ ★★★★★ |
| Withdrawals | 1–3 days | Same day |
| Licensing (Nigeria) | Curaçao (offshore) | NLRC ✅ |

## Bonus Comparison

**1xBet wins on bonus size**: 1xBet offers a larger welcome bonus across all African markets. However, the wagering requirements are significantly higher (35x vs Betway's 5x).

In practice, Betway's bonus is **much easier to clear** and represents better actual value despite the smaller headline figure.

## Odds Quality

1xBet offers the widest market selection in Africa with 50+ sports and over 1,000 markets per major football match. For serious bettors who want niche markets, 1xBet is unbeatable.

Betway offers better odds on mainstream football markets and is generally more reliable for live betting.

## App Quality

Betway has the best-rated betting app in Africa — consistently rated 4.7+ stars on Google Play across all African markets. 1xBet's app is feature-rich but more complex.

## Our Verdict

- **Choose 1xBet if**: You want the most markets, biggest bonus, and are comfortable with offshore licensing
- **Choose Betway if**: You want local licensing, faster withdrawals, and a simpler premium experience

*18+ | Bet Responsibly | T&Cs Apply*''',
        'author': 'Sifu Kai',
        'image_color': '#1565C0',
        'image_icon': '⚔️',
        'tags': ['1xBet', 'Betway', 'Africa Betting', 'Bookmaker Comparison', '2026'],
        'featured': False,
        'bookmaker_featured': 'Betway',
        'read_time': 6,
    },
    # ── COUNTRY BETTING GUIDES ────────────────────────────────────────────────
    {
        'category': 'country-guides',
        'title': 'Best Betting Sites in Kenya 2026 — Top 7 Licensed Bookmakers Compared',
        'slug': 'best-betting-sites-kenya-2026-licensed-bookmakers',
        'excerpt': 'The definitive guide to the best betting sites in Kenya 2026. Top 7 BCLB-licensed bookmakers compared by bonus, odds, M-Pesa speed, and app quality.',
        'body': '''Kenya is one of East Africa's most sophisticated sports betting markets. Here's our updated guide to the best licensed betting sites in Kenya in 2026.

## The 7 Best Betting Sites in Kenya 2026

### 1. Betway Kenya — Best Overall (4.7/5)
**Bonus**: 100% match up to KSh 5,000 | **Min deposit**: KSh 50 | **Licence**: BCLB
Betway is Kenya's top-rated bookmaker for overall quality. Their M-Pesa integration is seamless, withdrawals are instant, and their app is the best in the market. Ideal for serious bettors.

### 2. SportPesa Kenya — Best for Local Football (4.6/5)
**Bonus**: 100% up to KSh 5,000 | **Min deposit**: KSh 50 | **Licence**: BCLB
SportPesa was born in Nairobi and understands the Kenyan market better than any competitor. Their Kenya Premier League coverage and Jackpot games are unmatched.

### 3. 1xBet Kenya — Best for Markets (4.5/5)
**Bonus**: 100% up to KSh 10,000 | **Min deposit**: KSh 100 | **Licence**: BCLB
1xBet offers the widest range of sports and markets in Kenya. Over 50 sports, 1,000+ markets per match, and the highest welcome bonus. Best for experienced bettors.

### 4. BetKing Kenya — Best for Accumulators (4.3/5)
**Bonus**: 100% up to KSh 5,000 | **Min deposit**: KSh 50 | **Licence**: BCLB
BetKing Kenya offers excellent accumulator odds boosts and a clean, fast mobile experience.

### 5. Hollywoodbets Kenya — Best for Horse Racing (4.2/5)
**Bonus**: KSh 3,000 sign-up bonus | **Min deposit**: KSh 50 | **Licence**: BCLB
Hollywoodbets brings South Africa's premier horse racing expertise to Kenya. Best for punters interested in racing alongside football.

## How to Bet with M-Pesa in Kenya

All top Kenya bookmakers accept M-Pesa deposits and withdrawals. Minimum M-Pesa deposit is KSh 50. To deposit:
1. Dial *334# (Safaricom M-Pesa)
2. Select "Lipa na M-Pesa" → "Pay Bill"
3. Enter your bookmaker's business number
4. Enter your betting account number as reference
5. Enter amount and your M-Pesa PIN

## Is Betting Legal in Kenya?

Yes. Sports betting is legal in Kenya under the Betting, Lotteries and Gaming Act. All bookmakers listed above are licensed by the **BCLB (Betting Control and Licensing Board)**. Only use BCLB-licensed bookmakers.

*18+ | Bet Responsibly | T&Cs Apply | BCLB Licensed*''',
        'author': 'Sifu Kai',
        'image_color': '#006600',
        'image_icon': '🦁',
        'tags': ['Kenya Betting', 'Best Betting Sites Kenya', 'BCLB', 'M-Pesa Betting', '2026'],
        'featured': True,
        'bookmaker_featured': 'Betway',
        'read_time': 7,
    },
    {
        'category': 'country-guides',
        'title': 'Best Betting Sites in Ghana 2026 — Top 6 GCA-Licensed Bookmakers',
        'slug': 'best-betting-sites-ghana-2026-gca-licensed',
        'excerpt': 'The complete guide to the best licensed betting sites in Ghana 2026. Top 6 GCA-licensed bookmakers compared by bonus, MTN MoMo speed, odds, and app quality.',
        'body': '''Ghana's sports betting market is one of West Africa's most active, driven by a passionate football culture and widespread MTN MoMo adoption. Here are the best licensed bookmakers in Ghana in 2026.

## Top 6 Betting Sites in Ghana 2026

### 1. Betway Ghana — Best Overall (4.7/5)
**Bonus**: 100% match up to GH₵500 | **Min deposit**: GH₵5 | **Licence**: GCA
Betway Ghana is the market leader for quality. Excellent MTN MoMo integration, fast withdrawals, and a top-rated mobile app.

### 2. 1xBet Ghana — Highest Bonus (4.5/5)
**Bonus**: 100% up to GH₵700 | **Min deposit**: GH₵5 | **Licence**: GCA
1xBet offers Ghana's largest welcome bonus and widest market selection. Best for bettors who want maximum choice.

### 3. SportPesa Ghana — Best for Football (4.4/5)
**Bonus**: 100% up to GH₵300 | **Min deposit**: GH₵5 | **Licence**: GCA
SportPesa's Ghana Premier League and Black Stars coverage is the best in the market.

### 4. SportyBet Ghana — Fastest Withdrawals (4.4/5)
**Bonus**: 100% up to GH₵500 | **Min deposit**: GH₵5 | **Licence**: GCA
SportyBet offers the fastest MTN MoMo withdrawals in Ghana — most under 5 minutes.

### 5. Bet9ja Ghana — Best for West Africa Football (4.3/5)
**Bonus**: 100% up to GH₵500 | **Min deposit**: GH₵5 | **Licence**: GCA
Bet9ja Ghana offers excellent WAFU coverage including the Ghana Premier League and CAF competitions.

### 6. BetKing Ghana — Best Accumulator Odds (4.3/5)
**Bonus**: 100% up to GH₵500 | **Min deposit**: GH₵5 | **Licence**: GCA
BetKing consistently offers the best odds on football accumulators in Ghana.

## MTN MoMo Betting in Ghana

Dial *170# → "Mobile Money" → "Pay Bills" → Enter bookmaker merchant code → Confirm.

## Is Betting Legal in Ghana?

Yes. All bookmakers above are licensed by the **Ghana Gaming Commission (GCA)**. Betting is regulated and legal for Ghanaians aged 18+.

*18+ | Bet Responsibly | T&Cs Apply | GCA Licensed*''',
        'author': 'Sifu Kai',
        'image_color': '#FCD116',
        'image_icon': '⭐',
        'tags': ['Ghana Betting', 'Best Betting Sites Ghana', 'GCA', 'MTN MoMo Betting', '2026'],
        'featured': False,
        'bookmaker_featured': 'Betway',
        'read_time': 6,
    },
    {
        'category': 'country-guides',
        'title': 'Best Betting Sites in Tanzania 2026 — Top 5 GBT-Licensed Bookmakers',
        'slug': 'best-betting-sites-tanzania-2026',
        'excerpt': 'Complete guide to the best betting sites in Tanzania 2026. Top 5 GBT-licensed bookmakers compared by bonus, M-Pesa integration, and football odds.',
        'body': '''Tanzania has one of East Africa's most active sports betting markets, with over 5 million registered bettors. Here are the best licensed bookmakers in 2026.

## Top 5 Betting Sites in Tanzania 2026

### 1. Betway Tanzania — Best Overall (4.7/5)
**Bonus**: 100% up to TSh 150,000 | **Min deposit**: TSh 500 | **Licence**: GBT
Betway Tanzania is the market leader with excellent M-Pesa integration and strong Tanzania Premier League (NBC Premier League) coverage.

### 2. 1xBet Tanzania — Highest Bonus (4.5/5)
**Bonus**: 100% up to TSh 200,000 | **Min deposit**: TSh 500 | **Licence**: GBT
1xBet offers Tanzania's largest welcome bonus and 50+ sports.

### 3. SportPesa Tanzania — Best for Local Football (4.4/5)
**Bonus**: 100% up to TSh 100,000 | **Min deposit**: TSh 500 | **Licence**: GBT
SportPesa has the best NBC Premier League coverage and jackpot products in Tanzania.

### 4. SportyBet Tanzania — Fastest Withdrawals (4.4/5)
**Bonus**: 100% up to TSh 100,000 | **Min deposit**: TSh 500 | **Licence**: GBT
SportyBet offers the fastest M-Pesa withdrawals in Tanzania.

### 5. Meridianbet Tanzania — Best Odds (4.2/5)
**Bonus**: 100% up to TSh 80,000 | **Min deposit**: TSh 500 | **Licence**: GBT
Meridianbet offers consistently competitive odds on football and has been growing strongly in Tanzania.

## M-Pesa Deposits in Tanzania (Vodacom)

Dial *150*00# → "Lipa Bili" (Pay Bill) → Enter bookmaker number → Enter betting account → Confirm.

*18+ | Bet Responsibly | T&Cs Apply | GBT Licensed*''',
        'author': 'Sifu Kai',
        'image_color': '#1EB53A',
        'image_icon': '🦒',
        'tags': ['Tanzania Betting', 'Best Betting Sites Tanzania', 'GBT', 'M-Pesa Betting Tanzania', '2026'],
        'featured': False,
        'bookmaker_featured': 'Betway',
        'read_time': 5,
    },
    # ── BETTING STRATEGY ─────────────────────────────────────────────────────
    {
        'category': 'betting-tips',
        'title': 'Best Accumulator Tips Africa — How to Build Winning Accas in 2026',
        'slug': 'best-accumulator-tips-africa-how-to-build-winning-accas-2026',
        'excerpt': 'Learn how to build profitable football accumulator bets targeting African bookmakers in 2026. Strategy, value markets, and the best accumulator odds boosts.',
        'body': '''Accumulator betting (or "multi" betting) is the most popular bet type among African football bettors. Here's how to build consistently profitable accas in 2026.

## What is an Accumulator Bet?

An accumulator (acca) combines multiple selections into a single bet. All selections must win for the bet to pay out. The advantage: odds multiply, meaning even a 4-team acca at average odds of 1.80 per match pays out at 10.50x your stake.

## The 5 Keys to Profitable Accumulators

### 1. Stick to Markets You Understand
Focus on 1X2 (Match Result), BTTS (Both Teams to Score), or Over/Under Goals. Don't combine obscure markets where you lack edge.

### 2. Use Value — Not Just Favourites
Big favourites at 1.20 add minimal value to an acca but introduce single-point failure. Target realistic favourites at 1.50–1.80 with clear statistical backing.

### 3. Maximum 5 Selections
The industry standard for profitable recreational accumulators is 3–5 selections. Every additional selection reduces expected value.

### 4. Use Accumulator Boosts
SportyBet's **SuperYouWin** offers up to 500% extra on winning accumulators (3+ selections). Betway's **Multi Boost** adds 5–50% to qualifying accas. These are free money — always use them.

### 5. Limit Stake Size
Professional bettors use 1–3% of their bankroll per accumulator. Never exceed 5% on a single acca regardless of confidence.

## Best African Bookmakers for Accumulator Betting

| Bookmaker | Acca Boost | Max Bonus | Min Selections |
|-----------|-----------|-----------|---------------|
| SportyBet | SuperYouWin up to 500% | Unlimited | 3 |
| Betway | Multi Boost up to 50% | Unlimited | 2 |
| 1xBet | Multi Boost up to 120% | Unlimited | 2 |
| BetKing | Acca Boost up to 30% | Unlimited | 3 |
| SportPesa | Jackpot Enhancement | TSh/KSh Jackpot | 5+ |

## Sample 4-Team Acca (Example Analysis)

**Saturday Premier League Acca:**
1. Arsenal to Win vs Wolves — odds 1.65 (Arsenal strong home record)
2. BTTS in Chelsea vs Man City — odds 1.75 (both teams averaging 2+ goals)
3. Over 2.5 Goals in Liverpool vs Fulham — odds 1.70 (Liverpool average 3.1 goals at home)
4. Man United DNB Burnley — odds 1.55 (United safe home favourite)

**Combined odds**: 1.65 × 1.75 × 1.70 × 1.55 = **7.59**
**With SportyBet SuperYouWin (5% boost on 4-team acca)**: **7.97**

On a ₦5,000 stake, this returns ₦39,850 if all four selections win.

## Responsible Accumulator Betting

Accas are high-risk by nature. Always:
- Set a weekly accumulator budget
- Never chase losses with larger stakes
- Treat each acca as entertainment, not income

*18+ | Bet Responsibly | T&Cs Apply*''',
        'author': 'Sifu Kai',
        'image_color': '#1a6b35',
        'image_icon': '📊',
        'tags': ['Accumulator Tips', 'Betting Strategy', 'Acca Tips Africa', 'SportyBet', 'Football Betting'],
        'featured': True,
        'bookmaker_featured': 'SportyBet',
        'read_time': 8,
    },
    {
        'category': 'betting-tips',
        'title': 'M-Pesa Betting Tips — How to Use M-Pesa at Betting Sites in Kenya 2026',
        'slug': 'mpesa-betting-tips-how-to-use-mpesa-betting-sites-kenya-2026',
        'excerpt': 'Complete guide to using M-Pesa for sports betting in Kenya 2026. How to deposit, withdraw, and which bookmakers offer the fastest M-Pesa transactions.',
        'body': '''M-Pesa is Kenya's dominant mobile money platform and the #1 payment method at all BCLB-licensed betting sites. Here's everything you need to know about betting with M-Pesa in 2026.

## How to Deposit with M-Pesa at a Kenyan Betting Site

### Method 1 — USSD (*334#)
1. Dial *334# on your Safaricom line
2. Select "Lipa na M-Pesa"
3. Select "Pay Bill"
4. Enter the bookmaker's business number (e.g., Betway: 290999, SportPesa: 29009)
5. Enter your betting account number as reference
6. Enter the amount (minimum KSh 50)
7. Enter your M-Pesa PIN and confirm

### Method 2 — M-Pesa App
1. Open M-Pesa app → "Pay"
2. Select "Paybill"
3. Enter the bookmaker's paybill number
4. Enter your account number and amount
5. Confirm with PIN or fingerprint

## M-Pesa Withdrawal Guide

### Betway Kenya (Fastest)
Go to "Cashier" → "Withdrawal" → Select M-Pesa → Enter amount → Confirm. Most Betway M-Pesa withdrawals process in under 30 minutes.

### SportPesa Kenya
Request via app or website. SportPesa processes M-Pesa withdrawals within 1 hour during business hours.

### 1xBet Kenya
Request in "Cashier" → M-Pesa. Processing takes 1–24 hours. Complete KYC verification first.

## M-Pesa Deposit Limits at Kenyan Bookmakers

| Bookmaker | Paybill Number | Min Deposit | Max Deposit/Day |
|-----------|---------------|-------------|----------------|
| Betway Kenya | 290999 | KSh 50 | KSh 150,000 |
| SportPesa Kenya | 29009 | KSh 50 | KSh 150,000 |
| 1xBet Kenya | 290078 | KSh 100 | KSh 150,000 |
| BetKing Kenya | 891300 | KSh 50 | KSh 150,000 |
| SportyBet Kenya | 888111 | KSh 50 | KSh 150,000 |

## Troubleshooting M-Pesa Betting Issues

**M-Pesa deposit not showing?**
1. Check your M-Pesa transaction confirmation SMS
2. Wait 10 minutes — mobile money can occasionally be delayed
3. Contact your bookmaker's support with the M-Pesa transaction ID from your SMS

**Withdrawal not received?**
1. Verify your phone number in your betting account matches your M-Pesa number
2. Ensure your KYC verification is complete
3. Contact support with your withdrawal request ID

*18+ | Bet Responsibly | BCLB Licensed*''',
        'author': 'Sifu Kai',
        'image_color': '#4CAF50',
        'image_icon': '📱',
        'tags': ['M-Pesa Betting', 'Kenya Betting', 'How to Use M-Pesa', 'M-Pesa Deposit', 'Betway Kenya'],
        'featured': False,
        'bookmaker_featured': 'Betway',
        'read_time': 7,
    },
    {
        'category': 'betting-tips',
        'title': 'OPay Betting Guide Nigeria 2026 — How to Deposit at Nigerian Bookmakers',
        'slug': 'opay-betting-guide-nigeria-2026-deposit-withdrawal',
        'excerpt': 'Complete guide to using OPay for sports betting in Nigeria 2026. How to deposit, withdraw, and which bookmakers process OPay fastest.',
        'body': '''OPay is Nigeria's fastest-growing fintech platform with over 35 million users. It has become the #1 payment method at Nigerian betting sites. Here's the complete OPay betting guide for 2026.

## How to Deposit with OPay at a Nigerian Betting Site

### Step-by-Step OPay Deposit
1. Open the **OPay app** on your Android or iOS device
2. Select **"Transfer"** from the home screen
3. Select **"To Business"** or search for your bookmaker by name
4. Enter your **betting account number** as the recipient account
5. Enter the deposit amount (minimum ₦100 at most sites)
6. Review the transaction details and confirm with your **OPay PIN or fingerprint**
7. Your betting account is credited **instantly**

### OPay USSD (For Feature Phones)
1. Dial ***955#**
2. Select "Pay Bills"
3. Enter the bookmaker's OPay merchant ID
4. Enter your account reference and amount
5. Confirm with your OPay PIN

## OPay Supported Nigerian Bookmakers

| Bookmaker | OPay Support | Withdrawal Speed |
|-----------|-------------|-----------------|
| Bet9ja | ✅ | 1–6 hours |
| SportyBet | ✅ | Under 5 minutes |
| Betway Nigeria | ✅ | Same day |
| BetKing Nigeria | ✅ | 1–3 hours |
| 1xBet Nigeria | ✅ | 1–24 hours |
| Parimatch Nigeria | ✅ | Same day |

## OPay vs PalmPay — Which is Better for Betting?

Both OPay and PalmPay are excellent for Nigerian betting deposits and withdrawals. OPay has a larger merchant network and more bookmaker partnerships. PalmPay offers slightly higher P2P transfer limits. Both are instant for deposits.

## OPay Betting Limits

- **Minimum deposit**: ₦100 (most bookmakers)
- **Maximum single transaction**: ₦500,000 (verified accounts)
- **Daily limit (unverified)**: ₦200,000
- **Daily limit (verified with BVN)**: ₦1,000,000

## Troubleshooting OPay Betting Issues

**Deposit not showing in betting account?**
1. Check your OPay transaction history for confirmation
2. Take a screenshot of the successful transaction
3. Contact the bookmaker's live chat with your OPay transaction reference number

*18+ | Bet Responsibly | NLRC Licensed Bookmakers*''',
        'author': 'Sifu Kai',
        'image_color': '#00AA55',
        'image_icon': '💚',
        'tags': ['OPay Betting', 'Nigeria Betting', 'How to Deposit OPay', 'Nigerian Bookmakers', 'OPay Guide'],
        'featured': False,
        'bookmaker_featured': 'SportyBet',
        'read_time': 6,
    },
    {
        'category': 'betting-tips',
        'title': 'How to Withdraw from Betway Nigeria 2026 — Fast Withdrawal Guide',
        'slug': 'how-to-withdraw-betway-nigeria-2026',
        'excerpt': 'Step-by-step guide to withdrawing from Betway Nigeria in 2026. How to cash out via OPay, PalmPay, and bank transfer. Processing times and limits explained.',
        'body': '''Betway Nigeria processes fast withdrawals via OPay, PalmPay, and bank transfer. Here's exactly how to withdraw your winnings in 2026.

## Betway Nigeria Withdrawal Methods

| Method | Min Withdrawal | Processing Time | Fee |
|--------|---------------|----------------|-----|
| OPay | ₦100 | Usually under 2 hours | Free |
| PalmPay | ₦100 | Usually under 2 hours | Free |
| Bank Transfer (GTBank, Access, Zenith, UBA) | ₦500 | 1–24 hours | Free |
| Visa/Mastercard | ₦500 | 1–5 business days | Free |

## Step-by-Step Betway Nigeria Withdrawal Guide

### Step 1: Log in to Your Betway Account
Go to betway.com or open the Betway Nigeria app. Log in with your username and password.

### Step 2: Navigate to Cashier
Click on your account icon (top right) → Select "Cashier" → Select "Withdrawal".

### Step 3: Select Your Withdrawal Method
Choose OPay, PalmPay, or Bank Transfer. For OPay/PalmPay, ensure your phone number is registered and linked to your active wallet.

### Step 4: Enter Withdrawal Amount
Enter the amount you wish to withdraw (minimum ₦100 for OPay/PalmPay).

### Step 5: Confirm the Withdrawal
Review the details and click "Withdraw". You'll receive an SMS confirmation from Betway.

## Why Is My Betway Withdrawal Pending?

Common reasons for pending withdrawals:
1. **KYC not complete** — Betway requires NLRC-mandated ID verification. Upload your National ID, Voter's Card, or Passport.
2. **Active bonus not cleared** — If you have an active bonus, wagering requirements must be met before withdrawal
3. **Fraud review** — First-time withdrawals may take up to 24 hours as Betway's security team verifies the account
4. **Bank processing times** — Bank transfers take 1–24 hours regardless of how quickly Betway processes the request

## Betway Nigeria Withdrawal Limits

- **Minimum**: ₦100 (OPay/PalmPay), ₦500 (bank)
- **Maximum per transaction**: ₦2,000,000
- **Daily limit**: ₦5,000,000 (verified accounts)

*18+ | Bet Responsibly | NLRC Licensed*''',
        'author': 'Sifu Kai',
        'image_color': '#005CA9',
        'image_icon': '💰',
        'tags': ['Betway Nigeria Withdrawal', 'How to Withdraw Betway', 'Nigeria Betting', 'OPay Withdrawal'],
        'featured': False,
        'bookmaker_featured': 'Betway',
        'read_time': 5,
    },
    {
        'category': 'betting-tips',
        'title': 'AFCON 2026 Betting Guide — African Cup of Nations Odds & Tips',
        'slug': 'afcon-2026-betting-guide-african-cup-nations-odds-tips',
        'excerpt': 'Complete AFCON 2026 betting guide. Tournament favourites, group stage analysis, best odds at African bookmakers, and expert tips for the African Cup of Nations.',
        'body': '''The African Cup of Nations (AFCON) 2026 is one of the most anticipated tournaments in African football. Here's your complete betting guide.

## AFCON 2026 Tournament Overview

AFCON 2026 brings together the best of African football across 24 national teams. Morocco, Nigeria, Senegal, Ivory Coast, and Egypt are among the favourites to lift the trophy.

## AFCON 2026 Favourites

| Team | To Win AFCON 2026 | Best Bookmaker |
|------|------------------|----------------|
| Morocco | 4.50 | Betway |
| Senegal | 5.00 | 1xBet |
| Nigeria | 6.00 | Bet9ja |
| Ivory Coast | 5.50 | SportyBet |
| Egypt | 7.00 | 1xBet |
| Cameroon | 8.00 | Betway |

## Group Stage Betting Strategy

### Value Bets in Group Stages

The group stage offers excellent value on:
- **Total Goals (Over/Under 2.5)**: Group stage games between continental powers often produce 3+ goals
- **Both Teams to Score**: AFCON group stage BTTS rates average 45% historically
- **Correct Score markets**: Less predictable group stage games offer inflated odds on 1-0, 1-1, 2-1 results

### African Teams Worth Backing at Each Bookmaker

- **Nigeria Each Way to Win AFCON** at 6.00 (Bet9ja) — Outstanding value if Super Eagles come through a comfortable group
- **Morocco Clean Sheet in Group Stage** at 1.85–2.00 — Morocco's defensive record at AFCON 2022 was extraordinary
- **Senegal to Win Group** at 1.60–1.75 — Strongest squad in West Africa

## Live Betting AFCON Tips

Live in-play AFCON betting often offers the best value in the second half of close group stage matches, when the trailing team pushes forward and creates gaps.

Top live betting bookmakers for AFCON: 1xBet, Betway, SportyBet (all offer real-time markets on all AFCON matches).

*18+ | Bet Responsibly | T&Cs Apply*''',
        'author': 'SifuFinds Football Desk',
        'image_color': '#C1272D',
        'image_icon': '🏆',
        'tags': ['AFCON 2026', 'AFCON Betting', 'African Cup of Nations', 'Betting Tips', 'Africa Football'],
        'featured': True,
        'bookmaker_featured': 'Betway',
        'read_time': 7,
    },
    {
        'category': 'betting-tips',
        'title': 'CAF Champions League 2026 Betting Guide — African Club Football Odds',
        'slug': 'caf-champions-league-2026-betting-guide',
        'excerpt': 'CAF Champions League 2026 betting guide. Favourites, group stage tips, and best odds at African bookmakers for Africa\'s premier club competition.',
        'body': '''The CAF Champions League is Africa's premier club football competition. Here's everything bettors need to know about wagering on the tournament in 2026.

## CAF Champions League 2026 Favourites

| Club | Country | To Win CCL | Bookmaker |
|------|---------|-----------|-----------|
| Al-Ahly | Egypt | 3.50 | 1xBet |
| Wydad Casablanca | Morocco | 4.50 | Betway |
| Mamelodi Sundowns | South Africa | 5.00 | Hollywoodbets |
| TP Mazembe | DR Congo | 6.00 | 1xBet |
| Simba SC | Tanzania | 8.00 | Betway |

## CAF Champions League Betting Markets

Most African bookmakers offer the following CAF CL markets:
- **Match Result (1X2)** — Available at all bookmakers
- **Asian Handicap** — Available at 1xBet, Betway
- **Total Goals** — Available at all major bookmakers
- **BTTS** — Available at SportyBet, 1xBet, Betway
- **First Goalscorer** — Available at 1xBet, Betway
- **Correct Score** — Available at 1xBet

## Al-Ahly — The Market Standard

Al-Ahly of Egypt have won the CAF Champions League 11 times — more than any other club. When Al-Ahly are playing, their historical dominance makes them reliable favourites. Their home games in Cairo are near-impregnable.

## Group Stage Tips for CAF CCL

1. **Back home teams in North African derbies** — The travel disadvantage for visiting teams from sub-Saharan Africa to North Africa is significant
2. **Over 2.5 goals in West African group stage clashes** — West African clubs tend to play open, attacking football
3. **Back North African clubs away in East Africa** — Egyptian and Moroccan clubs typically handle away games in East Africa better than expected

*18+ | Bet Responsibly | T&Cs Apply*''',
        'author': 'SifuFinds Football Desk',
        'image_color': '#FF6600',
        'image_icon': '🏆',
        'tags': ['CAF Champions League', 'African Football', 'Betting Tips', 'Al-Ahly', 'Africa'],
        'featured': False,
        'bookmaker_featured': '1xBet',
        'read_time': 6,
    },
]


# seo_title() / seo_meta_description() now live in seo_meta.py (imported
# above) — shared across every generator so the truncation fix can't drift
# out of sync between them again.

_TITLE_TAG_OVERRIDES: dict[str, str] = {}


def _reserved_site_titles() -> dict[str, str]:
    """<title> text already used by non-blog pages (countries/, bookmakers/,
    core pages, etc.) — reserved so a blog post's truncated title can't
    silently collide with e.g. countries/ghana/'s "Best Betting Sites in
    Ghana 2026 | SifuFinds" (confirmed live 2026-07-26: a blog post's own
    title was more specific — "...Top 6 GCA-Licensed..." — but seo_title()'s
    separator truncation cut it down to the exact hub-page title)."""
    reserved: dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(BASE):
        dirnames[:] = [d for d in dirnames
                        if d not in {'.git', '.venv', '__pycache__', 'node_modules',
                                     '.github', 'agents', 'firecrawl',
                                     'geo-content-writer', 'blog'}
                        and not d.startswith('.')]
        if 'index.html' not in filenames:
            continue
        try:
            content = open(os.path.join(dirpath, 'index.html'), encoding='utf-8', errors='ignore').read()
        except OSError:
            continue
        m = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if m:
            reserved[m.group(1).strip()] = os.path.relpath(dirpath, BASE)
    return reserved


def resolve_title_collisions(posts: list, locale_translations: dict | None = None) -> None:
    """Ensure every post/locale-variant's rendered <title> tag is unique,
    and doesn't collide with any non-blog page's <title> either.

    seo_title()'s separator-based truncation still collapses two pages onto
    the same <title> when their titles share an identical lead-in past the
    0.35 threshold (e.g. two "World Cup 2026 Match Preview: ..." posts, or
    two translated titles that happen to render identically). Checks every
    locale variant (out_slug), not just the English title, since translated
    titles collide independently of their English source. When a collision
    is found, disambiguate every occurrence after the first using
    distinctive words from that page's own out_slug.
    """
    global _TITLE_TAG_OVERRIDES
    _TITLE_TAG_OVERRIDES = {}
    suffix = "| SifuFinds"
    seen: dict[str, str] = dict(_reserved_site_titles())
    locale_translations = locale_translations or {}
    locales = list(locale_translations.keys())

    candidates = []
    for post in posts:
        slug = post.get('slug')
        if not slug:
            continue
        candidates.append((slug, post['title']))
        for lg in locales:
            tr = locale_translations[lg].get(slug)
            if tr:
                candidates.append((f'{slug}-{lg}', tr['title']))

    for out_slug, title in candidates:
        rendered = seo_title(title)
        if rendered not in seen:
            seen[rendered] = out_slug
            continue
        words = [w for w in out_slug.replace('-', ' ').split() if w.isalpha() and len(w) > 2]
        tag = ' '.join(w.capitalize() for w in words[:4]) or out_slug
        candidate = f"{tag} {suffix}"
        if len(candidate) > 60:
            available = 60 - len(suffix) - 4
            candidate = f"{tag[:available].rsplit(' ', 1)[0]}... {suffix}"
        n = 2
        base_candidate = candidate
        while candidate in seen:
            candidate = base_candidate.replace(f" {suffix}", f" ({n}) {suffix}")
            n += 1
        seen[candidate] = out_slug
        _TITLE_TAG_OVERRIDES[out_slug] = candidate


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


def _inline_md(text: str) -> str:
    """Apply inline Markdown → HTML: links, bold, italic, code, images."""
    # Images before links (![alt](src))
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" loading="lazy">', text)
    # Hyperlinks [text](url) — internal and external
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # Bare markdown-style url shorthand [url](url) produced by some generators
    text = re.sub(r'\[(https?://[^\]]+)\]\(\1\)', r'<a href="\1">\1</a>', text)
    # Bold / italic
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text


def markdown_to_html(md: str) -> str:
    """Markdown → HTML for blog post bodies."""
    lines = md.split('\n')
    html_lines = []
    in_table = False
    in_ul = False
    in_ol = False

    for line in lines:
        # Headings
        if line.startswith('### '):
            if in_ul: html_lines.append('</ul>'); in_ul = False
            if in_ol: html_lines.append('</ol>'); in_ol = False
            # A literal "Q:"/"Q." label on an FAQ question heading was
            # already found and stripped from the FAQPage JSON-LD schema on
            # 2026-07-26 (see extract_faq_schema below), but that fix never
            # touched this renderer — the one that actually produces the
            # visible page — so readers still saw "Q: What is..." verbatim
            # (GEO scan, 2026-08-01). Same regex, applied where it was
            # always supposed to matter most.
            heading_text = re.sub(r'^Q[:.]\s*', '', line[4:], flags=re.IGNORECASE)
            html_lines.append(f'<h3>{_inline_md(heading_text)}</h3>')
        elif line.startswith('## '):
            if in_ul: html_lines.append('</ul>'); in_ul = False
            if in_ol: html_lines.append('</ol>'); in_ol = False
            html_lines.append(f'<h2>{_inline_md(line[3:])}</h2>')
        elif line.startswith('# '):
            # Never <h1> — the post template already renders its own <h1> from
            # the title field, so a body markdown line starting with a single
            # '# ' (the writer echoing the title back into the body, seen on
            # 69 of 1209 posts, one with 11 <h1>s) must not produce a second,
            # competing <h1> (technical SEO audit, 2026-08-11).
            if in_ul: html_lines.append('</ul>'); in_ul = False
            if in_ol: html_lines.append('</ol>'); in_ol = False
            html_lines.append(f'<h2>{_inline_md(line[2:])}</h2>')
        # Tables
        elif line.startswith('|'):
            if not in_table:
                html_lines.append('<div class="table-wrap"><table class="blog-table">')
                in_table = True
                cells = [c.strip() for c in line.strip('|').split('|')]
                html_lines.append('<thead><tr>' + ''.join(f'<th>{_inline_md(c)}</th>' for c in cells) + '</tr></thead><tbody>')
            elif set(line.replace('|', '').replace('-', '').replace(':', '').strip()) == set():
                pass  # separator row — skip
            else:
                cells = [c.strip() for c in line.strip('|').split('|')]
                html_lines.append('<tr>' + ''.join(f'<td>{_inline_md(c)}</td>' for c in cells) + '</tr>')
        else:
            if in_table:
                html_lines.append('</tbody></table></div>')
                in_table = False

            # Unordered list
            if line.startswith('- ') or line.startswith('* '):
                if not in_ul:
                    if in_ol: html_lines.append('</ol>'); in_ol = False
                    html_lines.append('<ul>')
                    in_ul = True
                html_lines.append(f'<li>{_inline_md(line[2:])}</li>')
            # Numbered list
            elif re.match(r'^\d+\. ', line):
                if not in_ol:
                    if in_ul: html_lines.append('</ul>'); in_ul = False
                    html_lines.append('<ol>')
                    in_ol = True
                item = re.sub(r'^\d+\. ', '', line)
                html_lines.append(f'<li>{_inline_md(item)}</li>')
            else:
                if in_ul: html_lines.append('</ul>'); in_ul = False
                if in_ol: html_lines.append('</ol>'); in_ol = False

                if line.strip() == '':
                    continue
                # Same literal-label leak as the heading case above, for a
                # plain "A: The answer..." line under an FAQ question.
                para_text = re.sub(r'^A[:.]\s*', '', line, flags=re.IGNORECASE)
                html_lines.append(f'<p>{_inline_md(para_text)}</p>')

    if in_table: html_lines.append('</tbody></table></div>')
    if in_ul: html_lines.append('</ul>')
    if in_ol: html_lines.append('</ol>')

    return '\n'.join(html_lines)


def extract_faq_schema(body_md: str) -> str:
    """Extract FAQ entries from markdown and return a FAQPage JSON-LD block, or empty string."""
    faq_section = (
        re.search(r'^##[^\n]*(?:FAQ|Frequently Asked Questions|Common Questions)[^\n]*\n(.*?)(?=^## |\Z)', body_md, re.DOTALL | re.IGNORECASE | re.MULTILINE) or
        re.search(r'^\*\*FAQs?\*\*\s*\n+(.*?)(?=^## |\Z)', body_md, re.DOTALL | re.IGNORECASE | re.MULTILINE)
    )
    if not faq_section:
        return ''

    text = faq_section.group(1)
    # 1. Bold **Q:** format
    pairs = re.findall(r'\*\*(?:Q:|Question:)\s*(.*?)\*\*\s*\n+(?:\*\*(?:A:|Answer:)\s*)?(.*?)(?=\n\*\*(?:Q:|Question:)|\Z)', text, re.DOTALL)
    # 2. Plain Q: / A: lines (no bold markers)
    if not pairs:
        pairs = re.findall(r'^Q[:\.]?\s+(.+?)\nA[:\.]?\s+(.*?)(?=\nQ[:\.]|\Z)', text, re.DOTALL | re.MULTILINE)
    # 3. Bullet-list * Q: / A: format
    if not pairs:
        pairs = re.findall(r'^\*\s+Q[:\.]?\s+(.+?)\nA[:\.]?\s+(.*?)(?=\n\*\s+Q[:\.]|\Z)', text, re.DOTALL | re.MULTILINE)
    # 4. Bullet-list * **Question**: answer format
    if not pairs:
        pairs = re.findall(r'^\*\s+\*\*(.*?)\*\*[:\.]?\s*(.*?)(?=\n\*\s+\*\*|\Z)', text, re.DOTALL | re.MULTILINE)
    # 5. ### heading + paragraph
    if not pairs:
        pairs = re.findall(r'###\s+(.*?)\n+(.*?)(?=\n###|\Z)', text, re.DOTALL)
    # 6. **Bold question?** + paragraph answer (common in expanded blog posts)
    if not pairs:
        pairs = re.findall(r'\*\*([^*\n]+\?)\*\*\s*\n+(.*?)(?=\n\*\*[^*\n]+\?|\Z)', text, re.DOTALL)
    # 7. Numbered list "1. Question?\nAnswer" format (no bold/heading markers)
    if not pairs:
        pairs = re.findall(r'^\d+\.\s+(.+?\?)\s*\n(.*?)(?=\n\d+\.\s|\Z)', text, re.DOTALL | re.MULTILINE)
    if not pairs:
        return ''

    entities = []
    for q, a in pairs[:8]:
        # json.dumps handles quotes/backslashes/newlines/unicode correctly —
        # manual .replace('"', '\\"') left raw newlines in answer text un-escaped,
        # producing invalid JSON-LD (silently unparseable by Google/AI crawlers)
        # on ~20% of posts whose FAQ answers spanned multiple source lines.
        q = re.sub(r'\s+', ' ', q).strip()
        # Pattern #7 (numbered list) doesn't consume a "Q:" label the way
        # patterns #1-#3 do, so a source like "1. Q: What's...?" leaks the
        # literal "Q:" into the schema's own question text too.
        q = re.sub(r'^Q[:.]\s*', '', q).strip()
        a = re.sub(r'<[^>]+>', '', a)
        a = re.sub(r'\s+', ' ', a).strip()
        # Pattern #6 (bold question + plain paragraph answer) doesn't consume
        # a literal "A:"/"A." label the way patterns #1-#3 do, so it leaks
        # into both the visible page and acceptedAnswer.text — a citation
        # reading "According to SifuFinds, A: Nigeria are typically..." reads
        # as broken to both readers and AI engines (GEO audit, 2026-07-26).
        a = re.sub(r'^A[:.]\s*', '', a).strip()[:500]
        if q and a:
            entities.append(f'''    {{
      "@type": "Question",
      "name": {json.dumps(q)},
      "acceptedAnswer": {{"@type": "Answer", "text": {json.dumps(a)}}}
    }}''')

    if not entities:
        return ''

    return f''',
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
{','.join(entities)}
  ]
}}'''


# ── INTERNAL LINKING ─────────────────────────────────────────────────────────

# Country page slugs and keywords that trigger a link to the country page
COUNTRY_LINKS = {
    'nigeria':       ('Nigeria betting guide',      '../../best-bonus-in-nigeria/'),
    'nigerian':      ('Nigeria betting guide',      '../../best-bonus-in-nigeria/'),
    'kenyan':        ('Kenya betting guide',        '../../best-bonus-in-kenya/'),
    'kenya':         ('Kenya betting guide',        '../../best-bonus-in-kenya/'),
    'ghana':         ('Ghana betting guide',        '../../best-bonus-in-ghana/'),
    'ghanaian':      ('Ghana betting guide',        '../../best-bonus-in-ghana/'),
    'south africa':  ('South Africa guide',         '../../best-bonus-in-south-africa/'),
    'south african': ('South Africa guide',         '../../best-bonus-in-south-africa/'),
    'tanzania':      ('Tanzania betting guide',     '../../best-bonus-in-tanzania/'),
    'uganda':        ('Uganda betting guide',       '../../best-bonus-in-uganda/'),
    'zambia':        ('Zambia betting guide',       '../../best-bonus-in-zambia/'),
    'ethiopia':      ('Ethiopia betting guide',     '../../best-bonus-in-ethiopia/'),
    'ethiopia':      ('Ethiopia betting guide',     '../../best-bonus-in-ethiopia/'),
    'egypt':         ('Egypt betting guide',        '../../best-bonus-in-egypt/'),
    'morocco':       ('Morocco betting guide',      '../../best-bonus-in-morocco/'),
    'cameroon':      ('Cameroon guide',             '../../best-bonus-in-cameroon/'),
    'senegal':       ('Senegal guide',              '../../best-bonus-in-senegal/'),
    'zimbabwe':      ('Zimbabwe guide',             '../../best-bonus-in-zimbabwe/'),
    'ivory coast':   ('Ivory Coast betting guide',  '../../best-bonus-in-ivory-coast/'),
    "côte d'ivoire": ('Ivory Coast betting guide',  '../../best-bonus-in-ivory-coast/'),
    'rwanda':        ('Rwanda betting guide',       '../../best-bonus-in-rwanda/'),
    'angola':        ('Angola betting guide',       '../../best-bonus-in-angola/'),
    'dr congo':      ('DR Congo betting guide',     '../../best-bonus-in-dr-congo/'),
    'mozambique':    ('Mozambique betting guide',   '../../best-bonus-in-mozambique/'),
    'botswana':      ('Botswana betting guide',     '../../best-bonus-in-botswana/'),
    'namibia':       ('Namibia betting guide',      '../../best-bonus-in-namibia/'),
    'malawi':        ('Malawi betting guide',       '../../best-bonus-in-malawi/'),
}

def _load_bookmaker_entries() -> list[dict]:
    """Load the bookmaker link registry from data/bookmaker_links.json.

    This is the single source of truth for standalone bookmakers/<slug>/
    review pages. Only status=='active' rows feed BOOKMAKER_LINKS/_BK_SLUG_TO_LINK
    below, so a removed brand stops being linked from new content without
    deleting its history or its (still-live, non-404) page.
    """
    path = os.path.join(BASE, 'data', 'bookmaker_links.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f).get('bookmakers', [])


_BOOKMAKER_ENTRIES = _load_bookmaker_entries()

BOOKMAKER_LINKS = [
    (e['keyword'], e['href'], e['anchor_title'])
    for e in _BOOKMAKER_ENTRIES if e.get('status') == 'active'
]

TOOL_LINKS = [
    ('odds calculator',    '../../tools/odds-calculator/',    'free odds calculator'),
    ('parlay calculator',  '../../tools/parlay-calculator/',  'free parlay calculator'),
    ('accumulator',        '../../tools/parlay-calculator/',  'accumulator calculator'),
]

CORE_LINKS = [
    ('free tips',          '../../tips/',     'free betting tips'),
    ('betting tips',       '../../tips/',     'free betting tips'),
    ('live odds',          '../../odds/',     'live odds comparison'),
    ('compare odds',       '../../odds/',     'live odds comparison'),
]

# External authority links — improve E-E-A-T and make content more citable.
# Each tuple: (regex_pattern, url, anchor_title, re_flags)
# Only the FIRST match per pattern is linked. All use target="_blank" rel="noopener noreferrer".
# Maps tag / category values to internal country page links for the resources box
_TAG_COUNTRY: dict[str, tuple[str, str]] = {
    'nigeria':      ('Nigeria Betting Guide',     '../../best-bonus-in-nigeria/'),
    'kenya':        ('Kenya Betting Guide',       '../../best-bonus-in-kenya/'),
    'ghana':        ('Ghana Betting Guide',       '../../best-bonus-in-ghana/'),
    'south africa': ('South Africa Betting Guide','../../best-bonus-in-south-africa/'),
    'tanzania':     ('Tanzania Betting Guide',    '../../best-bonus-in-tanzania/'),
    'uganda':       ('Uganda Betting Guide',      '../../best-bonus-in-uganda/'),
    'zambia':       ('Zambia Betting Guide',      '../../best-bonus-in-zambia/'),
    'ethiopia':     ('Ethiopia Betting Guide',    '../../best-bonus-in-ethiopia/'),
    'ivory coast':  ('Ivory Coast Betting Guide', '../../best-bonus-in-ivory-coast/'),
    'cameroon':     ('Cameroon Betting Guide',    '../../best-bonus-in-cameroon/'),
    'senegal':      ('Senegal Betting Guide',     '../../best-bonus-in-senegal/'),
    'zimbabwe':     ('Zimbabwe Betting Guide',    '../../best-bonus-in-zimbabwe/'),
    'rwanda':       ('Rwanda Betting Guide',      '../../best-bonus-in-rwanda/'),
    'egypt':        ('Egypt Betting Guide',       '../../best-bonus-in-egypt/'),
    'morocco':      ('Morocco Betting Guide',     '../../best-bonus-in-morocco/'),
}

# Maps sport category to one authoritative external link
_SPORT_ORG: dict[str, tuple[str, str, str]] = {
    'football':    ('FIFA',          'https://www.fifa.com',            'FIFA – world governing body for football'),
    'basketball':  ('NBA',           'https://www.nba.com',             'NBA official site'),
    'cricket':     ('ICC',           'https://www.icc-cricket.com',     'International Cricket Council'),
    'tennis':      ('ATP Tour',      'https://www.atptour.com',         'ATP Tour official site'),
    'rugby':       ('World Rugby',   'https://www.world.rugby',         'World Rugby official site'),
    'motorsport':  ('FIA',           'https://www.fia.com',             'FIA official site'),
    'boxing':      ('WBC',           'https://www.wbcboxing.com',       'World Boxing Council'),
}

_BK_SLUG_TO_LINK: dict[str, tuple[str, str]] = {
    e['keyword']: (e['resource_label'], e['href'])
    for e in _BOOKMAKER_ENTRIES if e.get('status') == 'active'
}

# Bonus pages (gen_bonus_pages.py output at bonuses/<slug>/) — news-category
# posts (transfers/sportnews) already get a bookmaker review link via
# _BK_SLUG_TO_LINK above, but never a bonus-page or comparison-article link
# since a transfer rumour or match report rarely mentions "welcome bonus" or
# "vs" naturally. This table + COMPARISON_LINKS close that gap.
BONUS_LINKS: list[tuple[str, str, str]] = [
    ('Welcome Bonus Offers',  '../../bonuses/welcome-bonus/',  'Best betting welcome bonuses in Africa'),
    ('Free Bet Offers',       '../../bonuses/free-bet/',       'Free bet offers compared'),
    ('Cashback Bonus Offers', '../../bonuses/cashback-bonus/', 'Cashback bonus offers compared'),
    ('Reload Bonus Offers',   '../../bonuses/reload-bonus/',   'Reload bonus offers compared'),
]

# Comparison articles — hand-verified against blog/posts.json slugs, never
# generated/guessed. Adding a link to a page that doesn't exist is the exact
# failure mode sanitize_internal_links() exists to prevent (see CLAUDE.md's
# documented 3-day deploy-block incident from AI-hallucinated internal links).
COMPARISON_LINKS: list[tuple[str, str, str]] = [
    ('bet9ja-vs-sportybet-nigeria-2026-comparison',
     'Bet9ja vs SportyBet (Nigeria) Compared', 'Bet9ja vs SportyBet Nigeria 2026 comparison'),
    ('1xbet-vs-betway-africa-2026-comparison',
     '1xBet vs Betway (Africa) Compared', '1xBet vs Betway Africa 2026 comparison'),
    ('best-betting-welcome-bonuses-africa-2026-compared',
     'Best Welcome Bonuses Compared', 'Best betting welcome bonuses in Africa, compared'),
]

_NEWS_CATEGORIES = {'transfers', 'sportnews'}


def _pick_news_context_links(post: dict) -> tuple[tuple[str, str, str], tuple[str, str, str]]:
    """Deterministically pick one bonus-page link and one comparison-article
    link for a news-category post. Stable across regenerations (hash of
    slug) rather than random, and biased toward the most relevant comparison
    when the post's tags name one of the compared brands."""
    slug = post.get('slug', '')
    idx = zlib.crc32(slug.encode('utf-8'))
    bonus = BONUS_LINKS[idx % len(BONUS_LINKS)]

    tags_lower = {t.lower() for t in post.get('tags', [])}
    if {'bet9ja', 'sportybet'} & tags_lower:
        comparison = COMPARISON_LINKS[0]
    elif {'1xbet', 'betway'} & tags_lower:
        comparison = COMPARISON_LINKS[1]
    else:
        comparison = COMPARISON_LINKS[idx % len(COMPARISON_LINKS)]
    return bonus, comparison


def build_share_bar(canonical_href: str, title: str) -> str:
    """Social share bar with direct intent links + a copy-link button.

    Every post gets a unique, crawlable /blog/{slug}/ URL already (see
    build_post_page canonical/OG/Twitter tags), but nothing on the page let a
    human actually grab and share that link — added 2026-07-24 so posts can
    be shared to X, Facebook, LinkedIn and Telegram in one click, or copied
    for WhatsApp/email/DMs.
    """
    enc_url = urlquote(canonical_href, safe='')
    enc_title = urlquote(title, safe='')
    return f'''<div class="share-bar">
      <span class="share-label">Share this article:</span>
      <a class="share-btn share-x" href="https://twitter.com/intent/tweet?url={enc_url}&amp;text={enc_title}" target="_blank" rel="noopener noreferrer" aria-label="Share on X">𝕏</a>
      <a class="share-btn share-fb" href="https://www.facebook.com/sharer/sharer.php?u={enc_url}" target="_blank" rel="noopener noreferrer" aria-label="Share on Facebook">f</a>
      <a class="share-btn share-li" href="https://www.linkedin.com/sharing/share-offsite/?url={enc_url}" target="_blank" rel="noopener noreferrer" aria-label="Share on LinkedIn">in</a>
      <a class="share-btn share-tg" href="https://t.me/share/url?url={enc_url}&amp;text={enc_title}" target="_blank" rel="noopener noreferrer" aria-label="Share on Telegram">✈</a>
      <button type="button" class="share-btn share-copy" onclick="copyPostLink(this,'{canonical_href}')" aria-label="Copy article link">🔗 Copy Link</button>
    </div>'''


def build_resources_box(post: dict) -> str:
    """Build a 'Useful Resources' panel guaranteed to appear on every post.

    Always contains:
    - 1-2 internal country-page links (from post tags)
    - 1 internal bookmaker review link (from bookmaker_featured)
    - 1 internal core page (tips or odds)
    - for news-category posts (transfers/sportnews): 1 bonus-page link + 1
      comparison-article link (see _pick_news_context_links)
    - 1 external sport-authority link (from category)
    - 1 external reference/backlink to bettingbrainiac.com/african-betting-sites/ (always)
    - 1 external responsible-gambling link (always)
    """
    items: list[str] = []

    # Country pages (up to 2, from tags)
    tags_lower = [t.lower() for t in post.get('tags', [])]
    for tag, (label, href) in _TAG_COUNTRY.items():
        if tag in tags_lower:
            items.append(f'<li><a href="{href}">{label}</a></li>')
        if len(items) >= 2:
            break

    # Bookmaker review page
    bk_key = post.get('bookmaker_featured', '').lower()
    if bk_key and bk_key in _BK_SLUG_TO_LINK:
        label, href = _BK_SLUG_TO_LINK[bk_key]
        items.append(f'<li><a href="{href}">{label}</a></li>')

    # Core page (tips if football category, else odds)
    if post.get('category') == 'football':
        items.append('<li><a href="../../tips/">Free Football Betting Tips</a></li>')
    else:
        items.append('<li><a href="../../odds/">Live Odds Comparison</a></li>')

    # News-category posts (transfers/sportnews) rarely mention a bonus type
    # or a head-to-head bookmaker matchup organically, so give them one of
    # each here — the review link above already covers "reviews".
    if post.get('category') in _NEWS_CATEGORIES:
        (b_label, b_href, b_title), (c_slug, c_label, c_title) = _pick_news_context_links(post)
        items.append(f'<li><a href="{b_href}" title="{b_title}">{b_label}</a></li>')
        items.append(f'<li><a href="../../blog/{c_slug}/" title="{c_title}">{c_label}</a></li>')

    # External: sport authority
    cat = post.get('category', 'football')
    if cat in _SPORT_ORG:
        name, url, title = _SPORT_ORG[cat]
        items.append(
            f'<li><a href="{url}" title="{title}" '
            f'target="_blank" rel="noopener noreferrer">{name} — Official Site ↗</a></li>'
        )

    # External: reference/backlink (always present)
    items.append(
        '<li><a href="https://bettingbrainiac.com/african-betting-sites/" title="BettingBrainiac – African betting sites reference" '
        'target="_blank" rel="noopener noreferrer">BettingBrainiac — African Betting Sites ↗</a></li>'
    )

    # External: responsible gambling (always present)
    items.append(
        '<li><a href="https://www.begambleaware.org" title="BeGambleAware – responsible gambling help" '
        'target="_blank" rel="noopener noreferrer">BeGambleAware — Responsible Gambling ↗</a></li>'
    )

    list_html = '\n    '.join(items)
    return (
        '<div class="resources-box" style="margin:28px 0 0;padding:16px 20px;'
        'background:#f0faf3;border-radius:10px;border-left:4px solid #1a6b35">'
        '<p style="margin:0 0 10px;font-size:13px;font-weight:700;color:#0a3d1e">📌 Useful Resources</p>'
        f'<ul style="margin:0;padding-left:18px;font-size:13px;color:#333;line-height:1.9">'
        f'\n    {list_html}\n  </ul></div>'
    )


EXTERNAL_LINKS = [
    # Regulators (highest E-E-A-T value for gambling content)
    (r'\bNLRC\b',   'https://nlrc.gov.ng',           'Nigeria Lottery Regulatory Commission', 0),
    (r'\bBCLB\b',   'https://bclb.go.ke',            'Betting Control and Licensing Board Kenya', 0),
    (r'\bGCA\b',    'https://www.gca.gov.gh',         'Gaming Commission of Ghana', 0),
    (r'\bWCGRB\b',  'https://www.wcgrb.co.za',        'Western Cape Gambling and Racing Board', 0),
    # Sports organisations
    (r'\bFIFA\b',          'https://www.fifa.com',                                'FIFA official site', 0),
    (r'\bUEFA\b',          'https://www.uefa.com',                                'UEFA official site', 0),
    (r'\bAFCON\b',         'https://www.cafonline.com',                           'Africa Cup of Nations – CAF', 0),
    (r'\bCAF\b',           'https://www.cafonline.com',                           'Confederation of African Football', 0),
    (r'World Cup 2026',    'https://www.fifa.com/worldcup/',                      'FIFA World Cup 2026', re.IGNORECASE),
    (r'Premier League',    'https://www.premierleague.com',                       'Premier League official site', re.IGNORECASE),
    (r'Champions League',  'https://www.uefa.com/uefachampionsleague/',           'UEFA Champions League', re.IGNORECASE),
    (r'\bNBA\b',           'https://www.nba.com',                                 'NBA official site', 0),
    (r'\bBundesliga\b',    'https://www.bundesliga.com/en/bundesliga',            'Bundesliga official site', re.IGNORECASE),
    (r'\bSerie A\b',       'https://www.legaseriea.it/en',                        'Serie A official site', re.IGNORECASE),
    (r'\bLigue 1\b',       'https://www.ligue1.com/en',                          'Ligue 1 official site', re.IGNORECASE),
    (r'\bLa Liga\b',       'https://www.laliga.com/en-GB',                        'La Liga official site', re.IGNORECASE),
    # Responsible gambling
    (r'\bBeGambleAware\b', 'https://www.begambleaware.org',  'BeGambleAware – responsible gambling help', re.IGNORECASE),
    (r'Gambling Therapy',  'https://www.gamblingtherapy.org','Gambling Therapy – free support', re.IGNORECASE),
]


def inject_external_links(body_html: str) -> str:
    """Auto-link first occurrence of authority terms to their external sources.

    Skips matches already inside an <a> tag.
    All external links open in a new tab with rel='noopener noreferrer'."""
    for pattern, url, title, flags in EXTERNAL_LINKS:
        m = re.search(pattern, body_html, flags)
        if not m:
            continue
        # Skip if already inside an anchor
        before = body_html[:m.start()]
        if before.count('<a ') > before.count('</a>'):
            continue
        matched = m.group(0)
        link = (f'<a href="{url}" title="{title}" '
                f'target="_blank" rel="noopener noreferrer">{matched}</a>')
        body_html = body_html[:m.start()] + link + body_html[m.end():]
    return body_html

# Score two posts for relatedness: higher = more related
def _relatedness(a: dict, b: dict) -> int:
    score = 0
    if a.get('category') == b.get('category'):
        score += 3
    a_tags = set(t.lower() for t in a.get('tags', []))
    b_tags = set(t.lower() for t in b.get('tags', []))
    score += len(a_tags & b_tags) * 2
    # Shared words in titles (4+ chars)
    a_words = set(w.lower() for w in re.split(r'\W+', a.get('title', '')) if len(w) >= 4)
    b_words = set(w.lower() for w in re.split(r'\W+', b.get('title', '')) if len(w) >= 4)
    score += len(a_words & b_words)
    return score


def build_related_html(post: dict, all_posts: list) -> str:
    """Return a 'Related Articles' section HTML with 4 related post links."""
    slug = post['slug']
    scored = [
        (p, _relatedness(post, p))
        for p in all_posts
        if p['slug'] != slug
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    related = [p for p, s in scored[:4] if s > 0]
    if not related:
        related = [p for p, _ in scored[:4]]
    if not related:
        return ''

    items = ''.join(
        f'<li><a href="../../blog/{p["slug"]}/">{p["title"]}</a></li>'
        for p in related
    )
    return f'''
<div class="related-posts" style="margin:32px 0 0;padding:20px 24px;background:#f0faf3;border-radius:12px;border-left:4px solid #1a6b35">
  <h3 style="font-size:15px;font-weight:800;color:#0a3d1e;margin:0 0 12px">Related Articles</h3>
  <ul style="margin:0;padding:0 0 0 18px;font-size:14px;line-height:1.9;color:#333">
    {items}
  </ul>
</div>'''


def inject_contextual_links(body_html: str, post: dict) -> str:
    """Add contextual inline links for country pages, tools, and core pages.
    Each keyword is linked only on its first occurrence to avoid over-linking."""
    used = set()

    # Country pages
    body_lower = body_html.lower()
    for keyword, (anchor_text, href) in COUNTRY_LINKS.items():
        if keyword in used:
            continue
        idx = body_lower.find(keyword)
        if idx == -1:
            continue
        # Don't link if already inside an <a> tag
        before = body_html[:idx]
        if before.count('<a ') > before.count('</a>'):
            continue
        actual = body_html[idx:idx + len(keyword)]
        link = f'<a href="{href}" title="{anchor_text}">{actual}</a>'
        body_html = body_html[:idx] + link + body_html[idx + len(keyword):]
        body_lower = body_html.lower()
        used.add(keyword)

    # Tool links
    for keyword, href, anchor_title in TOOL_LINKS:
        if keyword in used:
            continue
        idx = body_lower.find(keyword)
        if idx == -1:
            continue
        before = body_html[:idx]
        if before.count('<a ') > before.count('</a>'):
            continue
        actual = body_html[idx:idx + len(keyword)]
        link = f'<a href="{href}" title="{anchor_title}">{actual}</a>'
        body_html = body_html[:idx] + link + body_html[idx + len(keyword):]
        body_lower = body_html.lower()
        used.add(keyword)

    # Core page links
    for keyword, href, anchor_title in CORE_LINKS:
        if keyword in used:
            continue
        idx = body_lower.find(keyword)
        if idx == -1:
            continue
        before = body_html[:idx]
        if before.count('<a ') > before.count('</a>'):
            continue
        actual = body_html[idx:idx + len(keyword)]
        link = f'<a href="{href}" title="{anchor_title}">{actual}</a>'
        body_html = body_html[:idx] + link + body_html[idx + len(keyword):]
        body_lower = body_html.lower()
        used.add(keyword)

    # Bookmaker review links (first mention only per bookmaker)
    for keyword, href, anchor_title in BOOKMAKER_LINKS:
        if keyword in used:
            continue
        idx = body_lower.find(keyword)
        if idx == -1:
            continue
        before = body_html[:idx]
        if before.count('<a ') > before.count('</a>'):
            continue
        actual = body_html[idx:idx + len(keyword)]
        link = f'<a href="{href}" title="{anchor_title}">{actual}</a>'
        body_html = body_html[:idx] + link + body_html[idx + len(keyword):]
        body_lower = body_html.lower()
        used.add(keyword)

    return body_html


# Global post list populated by main() before generation
_ALL_POSTS: list = []


# ── TRANSLATIONS ──────────────────────────────────────────────────────────────
# Locale pages live at blog/{slug}-{locale}/ (same directory depth as blog/{slug}/,
# not blog/{locale}/{slug}/) so every hardcoded '../../' relative link in this file
# — country pages, bookmaker reviews, tools, external authority links — keeps
# working unmodified for translated pages too.
LOCALES = ['fr', 'de', 'es', 'pt', 'sw']
OG_LOCALE = {'en': 'en_GB', 'fr': 'fr_FR', 'de': 'de_DE', 'es': 'es_ES', 'pt': 'pt_PT', 'sw': 'sw_KE'}
TRANSLATIONS_DIR = os.path.join(BASE, 'blog', 'translations')


def load_translations(locale: str) -> dict:
    """slug -> {title, excerpt, body} for the given locale, or {} if none exist yet."""
    path = os.path.join(TRANSLATIONS_DIR, f'{locale}.json')
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_post_page(post: dict, locale: str = 'en', translations: dict | None = None,
                     available_locales: list[str] | None = None) -> str:
    slug = post['slug']
    tr = (translations or {}).get(slug) if locale != 'en' else None
    title = tr['title'] if tr else post['title']
    excerpt = tr['excerpt'] if tr else post['excerpt']
    body_md = tr['body'] if tr else post.get('body', '')
    # Strip a literal "A:"/"A." answer-label immediately after a bold FAQ
    # question — the source convention "**Question?**\nA: Answer" otherwise
    # renders "A:" as visible page text (see extract_faq_schema for the
    # matching JSON-LD-side fix).
    body_md = re.sub(r'(\*\*[^*\n]+\?\*\*)\s*\n+A[:.]\s+', r'\1\n', body_md)
    # Same leak, different source convention: plain "Q: ...\nA: ..." lines
    # (no bold markers) render both labels as literal visible text. Bolds
    # the question and strips the "A:" label so it renders the same as the
    # bold-question convention above. Confirmed live on 101 of 540 posts
    # (19%, GEO re-audit 2026-07-26) — extract_faq_schema's pattern #2
    # already consumes both labels for the JSON-LD side; this is the
    # matching visible-HTML fix.
    body_md = re.sub(r'^Q[:.]?\s+(.+?)\n+A[:.]?\s+', lambda m: f'**{m.group(1).strip()}**\n',
                      body_md, flags=re.MULTILINE)
    # Third source convention: bullet-list "* Q: ...\nA: ..." lines.
    body_md = re.sub(r'^\*\s+Q[:.]?\s+(.+?)\n+A[:.]?\s+', lambda m: f'**{m.group(1).strip()}**\n',
                      body_md, flags=re.MULTILINE)
    # Fourth: numbered-list "N. Q: ...\nA: ..." lines.
    body_md = re.sub(r'^\d+\.\s+Q[:.]?\s+(.+?)\n+A[:.]?\s+', lambda m: f'**{m.group(1).strip()}**\n',
                      body_md, flags=re.MULTILINE)
    out_slug = slug if locale == 'en' else f'{slug}-{locale}'
    hreflang_links = '\n'.join(
        f'<link rel="alternate" hreflang="{lg}" href="https://sifufinds.com/blog/{slug if lg == "en" else slug + "-" + lg}/">'
        for lg in ['en'] + (available_locales or [])
    )
    hreflang_links += f'\n<link rel="alternate" hreflang="x-default" href="https://sifufinds.com/blog/{slug}/">'
    html_lang_attr = f'lang="{locale}"' + ('' if locale == 'en' else f' data-locale="{locale}"')
    body_html = markdown_to_html(body_md)
    body_html = inject_contextual_links(body_html, post)
    body_html = inject_external_links(body_html)
    resources_html = build_resources_box(post)
    related_html = build_related_html(post, _ALL_POSTS)
    author = post.get('author', 'SifuFinds Editorial Team')
    # Only attribute Person/#sifu-kai schema to posts actually bylined as Sifu Kai —
    # "Desk" bylines (Football Desk, Cricket Desk, etc.) get an Organization author
    # instead, since attributing them to his named identity would misrepresent authorship.
    # reviewedBy: every "Desk" byline is edited under Sifu Kai's stated editorial
    # oversight (see llms.txt "Content reviewed by" claim) — surfacing that as
    # Person-entity schema gives AI engines a named, credentialed signal without
    # misattributing authorship the way relabeling the byline itself would.
    reviewed_by_schema = ''
    if author.strip() == 'Sifu Kai':
        author_schema = ('{"@type": "Person", "@id": "https://sifufinds.com/about/#sifu-kai", '
                          '"name": "Sifu Kai", "url": "https://sifufinds.com/about/", '
                          '"image": {"@type": "ImageObject", "url": "https://sifufinds.com/assets/android-chrome-192x192.png", "width": 192, "height": 192}}')
    else:
        author_schema = (f'{{"@type": "Organization", "@id": "https://sifufinds.com/#organization", '
                          f'"name": "{author}", "url": "https://sifufinds.com/about/#team"}}')
        reviewed_by_schema = (',\n  "reviewedBy": {"@type": "Person", "@id": "https://sifufinds.com/about/#sifu-kai", '
                               '"name": "Sifu Kai", "jobTitle": "Lead Betting Analyst & Editor-in-Chief", '
                               '"url": "https://sifufinds.com/about/"}')
    category = post.get('category', 'football')
    tags = post.get('tags', [])
    read_time = post.get('read_time', 5)
    featured_bk = post.get('bookmaker_featured', '')
    published_at = post.get('published_at', datetime.now(timezone.utc).isoformat())
    faq_schema = extract_faq_schema(body_md)
    # Per-post OG/social preview image (scripts/generate_review_og_images.py) —
    # falls back to the sitewide logo graphic when a post has no dedicated one.
    # Every post shared one identical image until 2026-07-19; unique previews
    # raise AI-search multi-modal selection rates (see GEO audit notes).
    has_feature_image = os.path.exists(f'assets/og/{slug}.png')
    og_image_url = (f'https://sifufinds.com/assets/og/{slug}.png'
                     if has_feature_image
                     else 'https://sifufinds.com/assets/og-image.png')
    # JSON-safe variants for JSON-LD contexts — a raw quote in a title/excerpt
    # (e.g. a translated pull-quote) otherwise breaks the whole ld+json block.
    title_json = json.dumps(title)
    excerpt_json = json.dumps(excerpt)
    title_short_json = json.dumps(title[:60])

    # Format date
    try:
        pub_dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        pub_date = pub_dt.strftime('%B %d, %Y')
        pub_iso = pub_dt.strftime('%Y-%m-%d')
    except Exception:
        pub_date = 'June 2026'
        pub_iso = '2026-06-07'

    # dateModified must reflect a genuine content edit, not just today's
    # regen — hardcoding it to always equal datePublished (pre-2026-07-26)
    # made llms.txt's "factual claims updated within 24 hours" claim
    # unsubstantiated (GEO audit finding). Callers that actually rewrite a
    # post's body/excerpt (agent_content_backfill.py, manual content fixes)
    # set post['updated_at']; everything else correctly falls back to its
    # original publish date.
    updated_at = post.get('updated_at', published_at)
    try:
        mod_iso = datetime.fromisoformat(updated_at.replace('Z', '+00:00')).strftime('%Y-%m-%d')
    except Exception:
        mod_iso = pub_iso

    canonical = f'https://sifufinds.com/blog/{out_slug}/'
    canonical_override = post.get('canonical_override', '') if locale == 'en' else ''
    # noindex is an English-duplicate-consolidation concept (see
    # dedupe_noindex.py, 2026-08-02) — it must not cascade to translated
    # locale variants the same way canonical_override already doesn't,
    # because a post's translation can exist with no equivalent
    # translation on whichever post it's being consolidated into (found
    # 2026-08-02: bet9ja-vs-sportybet-nigeria-2026-comparison had fr/de
    # translations but its noindex target, bet9ja-vs-sportybet-nigeria-2026,
    # had none — cascading noindex would have deindexed the only fr/de
    # coverage of that topic with no replacement, not fixed a duplicate).
    noindex = post.get('noindex', False) if locale == 'en' else False
    canonical_href = canonical_override if canonical_override else canonical
    robots_content = ('noindex, follow' if noindex
                      else 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1')
    tags_html = ''.join(f'<span class="post-tag">{t}</span>' for t in tags[:6])
    share_bar_html = build_share_bar(canonical_href, title)

    return f'''<!DOCTYPE html>
<!-- sifufinds.com/blog/{out_slug}/ — {title} -->
<html {html_lang_attr}>
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-0B51MX2ZKE"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-0B51MX2ZKE');
</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_TITLE_TAG_OVERRIDES.get(out_slug) or seo_title(title)}</title>
<meta name="description" content="{seo_meta_description(excerpt)}">
<meta name="keywords" content="{', '.join(tags[:8]).lower()}">
<meta name="robots" content="{robots_content}">
<meta name="author" content="{author}">
<link rel="canonical" href="{canonical_href}">
{hreflang_links}

<meta property="og:type" content="article">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{seo_meta_description(excerpt, max_len=200)}">
<meta property="og:url" content="{canonical_href}">
<meta property="og:image" content="{og_image_url}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{OG_LOCALE.get(locale, 'en_GB')}">
<meta property="article:published_time" content="{published_at}">
<meta property="article:section" content="{category}">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@sifufinds">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{seo_meta_description(excerpt, max_len=200)}">
<meta name="twitter:image" content="{og_image_url}">

<script type="application/ld+json">
[{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": {title_json},
  "description": {excerpt_json},
  "author": {author_schema}{reviewed_by_schema},
  "publisher": {{
    "@type": "Organization",
    "@id": "https://sifufinds.com/#organization",
    "name": "SifuFinds",
    "url": "https://sifufinds.com",
    "logo": {{"@type": "ImageObject", "url": "https://sifufinds.com/assets/android-chrome-192x192.png", "width": 192, "height": 192}}
  }},
  "datePublished": "{pub_iso}",
  "dateModified": "{mod_iso}",
  "mainEntityOfPage": "{canonical}",
  "keywords": "{', '.join(tags)}",
  "articleSection": "{category}",
  "image": {{"@type": "ImageObject", "url": "{og_image_url}", "width": 1200, "height": 630}}
}},
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://sifufinds.com/"}},
    {{"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://sifufinds.com/blog/"}},
    {{"@type": "ListItem", "position": 3, "name": {title_short_json}, "item": "{canonical}"}}
  ]
}}{faq_schema}]
</script>

<link rel="preload" href="../../assets/shared.css?v=12" as="style">
<link rel="stylesheet" href="../../assets/shared.css?v=12">
<style>
.post-hero{{position:relative;overflow:hidden;background:linear-gradient(135deg,#0a3d1e 0%,#1a6b35 100%);color:#fff;padding:32px 0}}
.post-hero-img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.4}}
.post-hero-overlay{{position:absolute;inset:0;background:linear-gradient(135deg,rgba(10,61,30,.9) 0%,rgba(26,107,53,.85) 100%)}}
.post-hero .wrap{{position:relative;z-index:2}}
.post-hero h1{{font-size:clamp(20px,3.5vw,30px);font-weight:900;margin-bottom:10px;letter-spacing:-.5px;line-height:1.3}}
.post-meta{{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:rgba(255,255,255,.75);margin-top:8px}}
.post-body{{max-width:760px;font-size:15px;color:#222;line-height:1.8}}
.post-body h2{{font-size:20px;font-weight:800;color:#0a3d1e;margin:28px 0 10px;padding-bottom:6px;border-bottom:2px solid #e8f5e9}}
.post-body h3{{font-size:17px;font-weight:700;color:#1a6b35;margin:20px 0 8px}}
.post-body p{{margin-bottom:14px}}
.post-body ul,.post-body ol{{padding-left:20px;margin-bottom:14px}}
.post-body li{{margin-bottom:6px}}
.post-body strong{{color:#0a3d1e}}
.table-wrap{{overflow-x:auto;margin:16px 0}}
.blog-table{{width:100%;border-collapse:collapse;font-size:13px}}
.blog-table th{{background:#0a3d1e;color:#fff;padding:9px 12px;text-align:left;font-weight:700}}
.blog-table td{{padding:8px 12px;border-bottom:1px solid #eee}}
.blog-table tr:nth-child(even) td{{background:#f9fef9}}
.post-tag{{display:inline-block;background:#edf7f0;border:1px solid #c8e6c9;border-radius:5px;padding:3px 9px;font-size:11px;font-weight:700;color:#1a6b35;margin:2px}}
.breadcrumb{{font-size:12px;color:#aaa;margin-bottom:14px;padding:8px 0}}
.breadcrumb a{{color:#1a6b35;text-decoration:none}}
.breadcrumb span{{margin:0 5px;color:#ccc}}
.related-posts{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;margin-top:10px}}
.related-card{{background:#fff;border:1px solid #e8e8e8;border-radius:10px;padding:14px;text-decoration:none;color:inherit;transition:box-shadow .2s}}
.related-card:hover{{box-shadow:0 4px 12px rgba(0,0,0,.1)}}
.related-card h3{{font-size:13px;font-weight:700;color:#111;margin:0 0 6px;line-height:1.4}}
.related-card p{{font-size:12px;color:#666;margin:0}}
.footer-bar{{background:#0a3d1e;color:rgba(255,255,255,.55);text-align:center;padding:18px;font-size:12px;line-height:1.8;margin-top:16px}}
.footer-bar a{{color:rgba(255,255,255,.7);text-decoration:none}}
.share-bar{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:14px 0;padding:10px 0;border-top:1px solid #eee;border-bottom:1px solid #eee}}
.share-label{{font-size:12px;font-weight:700;color:#666;margin-right:2px}}
.share-btn{{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-width:38px;height:38px;padding:0 12px;border-radius:8px;border:1px solid #e0e0e0;background:#fff;color:#111;font-size:14px;font-weight:800;text-decoration:none;cursor:pointer;transition:transform .15s,box-shadow .15s;line-height:1}}
.share-btn:hover{{transform:translateY(-1px);box-shadow:0 3px 10px rgba(0,0,0,.12)}}
.share-x:hover{{background:#000;color:#fff;border-color:#000}}
.share-fb:hover{{background:#1877f2;color:#fff;border-color:#1877f2}}
.share-li:hover{{background:#0a66c2;color:#fff;border-color:#0a66c2}}
.share-tg:hover{{background:#26a5e4;color:#fff;border-color:#26a5e4}}
.share-copy{{font-size:12px;padding:0 14px}}
.share-copy.copied{{background:#1a6b35;color:#fff;border-color:#1a6b35}}
</style>
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
</head>
<body>

<div class="tbar">
  <div class="tbar-l">
    <a href="../../">🏠 Home</a>
    <a href="../">📰 Blog</a>
    <a href="../../responsible/">Responsible Gambling</a>
    <button onclick="openPage('about')">18+ Only</button>
  </div>
  <div class="tbar-r">
    <span class="csel-lbl">Your Country:</span>
    <select class="csel" id="ctySel" onchange="changeCountry(this.value)">
{SELECTOR}
    </select>
  </div>
</div>

<nav class="mnav">
  <div class="mnav-in">
    <a class="logo" href="../../"><img src="../../assets/icon.png" width="38" height="38" alt="SifuFinds logo" style="display:block;object-fit:contain">SifuFinds</a>
    <div class="ntabs">
      <a class="nt" href="../../">⭐ Best Bonuses</a>
      <a class="nt" href="../../tips/">💡 Tips</a>
      <a class="nt" href="../../casino/">🎰 Casino</a>
      <a class="nt" href="../../odds/">📊 Live Odds<span class="lpulse" style="margin-left:4px"></span></a>
      <a class="nt" href="../../countries/">🌍 Countries</a>
      <a class="nt on" href="../">📰 Blog</a>
    </div>
  </div>
</nav>

<div class="post-hero">
  {f'<img class="post-hero-img" src="{og_image_url}" alt="{html.escape(title)}" width="1200" height="630" loading="eager" fetchpriority="high">' if has_feature_image else ''}
  <div class="post-hero-overlay"></div>
  <div class="wrap">
    <h1>{title}</h1>
    <div class="post-meta">
      <span>📅 <time datetime="{pub_iso}">{pub_date}</time></span>
      <span>✍️ <a href="../../about/#team" rel="author" style="color:rgba(255,255,255,.85);text-decoration:none">{author}</a></span>
      <span>⏱️ {read_time} min read</span>
      {'<span>📌 ' + featured_bk + '</span>' if featured_bk else ''}
    </div>
    <div style="margin-top:10px">{tags_html}</div>
  </div>
</div>

<div class="sec-bg"><div class="wrap" style="padding-top:14px">
  <div class="breadcrumb">
    <a href="../../">Home</a><span>›</span>
    <a href="../">Blog</a><span>›</span>
    {title[:50] + '...' if len(title) > 50 else title}
  </div>

  <div class="adv">📢 <strong>Advertiser Disclosure:</strong> SifuFinds may earn commission from bookmaker links. All bonuses verified. 18+.</div>

  <div style="display:grid;grid-template-columns:1fr minmax(0,760px) 1fr;gap:0">
    <div></div>
    <div>
      {share_bar_html}
      <article class="post-body" itemscope itemtype="https://schema.org/Article">
        <meta itemprop="headline" content="{title}">
        <meta itemprop="datePublished" content="{pub_iso}">
        {body_html}
        {resources_html}
        {related_html}
      </article>
      {share_bar_html}
    </div>
    <div></div>
  </div>

  <div class="cbox2" style="margin-top:24px">
    <h2>Compare Bookmakers — Start Betting Today</h2>
    <div id="compare-books"></div>
    <div style="text-align:center;margin-top:12px">
      <a href="../../" style="display:inline-block;background:var(--g);color:#fff;padding:10px 22px;border-radius:7px;font-size:13px;font-weight:800;text-decoration:none">Compare All Bookmakers →</a>
    </div>
  </div>

  <div class="resp">⚠️ Gambling involves risk. Only bet what you can afford to lose. 18+ only. If gambling is causing harm, seek help.</div>
</div></div>

<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison<br>
  <a href="../../">Home</a> · <a href="../">Blog</a> · <a href="../../tips/">Tips</a> · <a href="../../countries/">Countries</a> · <a href="../../bookmakers/">Bookmakers</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only.
</div>

<div class="page-modal-bg" id="page-modal"><div class="page-modal"><button class="page-modal-close" onclick="closePage()">×</button><div class="pm" id="page-content"></div></div></div>

<script src="../../assets/shared.js?v=20"></script>
<script>
const SITE={{home:'../../',tips:'../../tips/',casino:'../../casino/',odds:'../../odds/',countries:'../../countries/'}};
function copyPostLink(btn,url){{
  const done=()=>{{
    const orig=btn.textContent;
    btn.textContent='✓ Copied!';
    btn.classList.add('copied');
    setTimeout(()=>{{btn.textContent=orig;btn.classList.remove('copied');}},2000);
  }};
  if(navigator.clipboard&&window.isSecureContext){{
    navigator.clipboard.writeText(url).then(done).catch(()=>{{}});
  }}else{{
    const ta=document.createElement('textarea');
    ta.value=url;ta.style.position='fixed';ta.style.opacity='0';
    document.body.appendChild(ta);ta.select();
    try{{document.execCommand('copy');done();}}catch(e){{}}
    document.body.removeChild(ta);
  }}
}}
const bookCard=(b,i,rank)=>{{
  const badge=b.badge==='new'?'<span class="badge-new">NEW</span>':b.badge==='hot'?'<span class="badge-hot">HOT</span>':b.nodep?'<span class="badge-nd">NO DEP</span>':'';
  return`<div class="bkcard ${{rank<3?'top3':''}} ${{b.nodep?'nodep-card':''}}">
  <div class="bk-main">
    <span class="bk-rk">#${{rank+1}}</span>
    <div class="bk-logo" style="background:${{b.bg}}">${{logoImg(b.url,b.name,b.abbr,b.tc,60,8)}}</div>
    <div>
      <div class="bk-tag">${{b.tag}}</div>
      <div class="bk-nm">${{b.name}}${{badge}}</div>
      <div class="bk-off">${{b.off}}</div>
      <div class="bk-meta"><span>Min: ${{b.min}}</span><span>${{b.sports}} sports</span><span>${{b.lic}}</span></div>
    </div>
    <div class="bk-act">
      <div class="bk-stars">${{stars(b.stars)}}</div>
      <a class="gbtn${{b.nodep?' gold':''}}" href="${{b.url}}" target="_blank" rel="noopener noreferrer sponsored">Claim Bonus →</a>
      <div class="tc-n">T&amp;Cs Apply · 18+</div>
    </div>
  </div>
  <div class="pm-row">${{(b.pms||[]).map(pm).join('')}}</div>
  <button class="xbtn" onclick="toggleDet(this)">▼ More details</button>
  <div class="xdet">
    <div class="xg">
      <div class="xi"><div class="xl">Min Deposit</div><div class="xv">${{b.min}}</div></div>
      <div class="xi"><div class="xl">Cash Out</div><div class="xv ${{b.cashout?'yes':'no'}}">${{b.cashout?'✓ Yes':'✗ No'}}</div></div>
      <div class="xi"><div class="xl">Live Stream</div><div class="xv ${{b.stream?'yes':'no'}}">${{b.stream?'✓ Yes':'✗ No'}}</div></div>
      <div class="xi"><div class="xl">Instant Pay</div><div class="xv ${{b.instant?'yes':'no'}}">${{b.instant?'✓ Yes':'✗ No'}}</div></div>
      <div class="xi"><div class="xl">No Deposit</div><div class="xv ${{b.nodep?'yes':'no'}}">${{b.nodep?'✓ Yes':'✗ No'}}</div></div>
      <div class="xi"><div class="xl">Sports</div><div class="xv">${{b.sports}}+</div></div>
    </div>
    <div class="trms">${{b.terms}}</div>
    <a class="gbtn" href="${{b.url}}" target="_blank" rel="noopener noreferrer sponsored">Claim Bonus →</a>
  </div>
</div>`;
}};
function init(){{
  H('foot-yr',NOW.getFullYear());
  const books=(BOOKS['NG']||[]).slice(0,4);
  const el=document.getElementById('compare-books');
  if(el&&books.length){{el.innerHTML=books.map((b,i)=>bookCard(b,i,i)).join('');}}
}}
init();
</script>
</body>
</html>'''


def _load_htaccess_redirect_targets() -> set[str]:
    """Mirror scripts/validate_site.py's redirect-target parsing so this
    generator and the pre-deploy validator agree on what counts as 'covered'.
    """
    targets: set[str] = set()
    htaccess_path = os.path.join(BASE, '.htaccess')
    try:
        with open(htaccess_path, encoding='utf-8') as f:
            for line in f:
                m = re.match(r'^\s*Redirect\s+30[12]\s+(/\S+)', line)
                if m:
                    targets.add('https://sifufinds.com' + m.group(1).rstrip('/'))
                    continue
                m = re.match(r'^\s*RewriteRule\s+\^(.+?)\$\s+(/\S+?)\s+\[R=30[12]', line)
                if m:
                    slug = m.group(1).rstrip('/?')
                    targets.add('https://sifufinds.com/' + slug.lstrip('/'))
    except OSError:
        pass
    return targets


_INTERNAL_LINK_RE = re.compile(r'\[([^\]]+)\]\(https://sifufinds\.com/([^)#?]+)\)')


def sanitize_internal_links(posts: list) -> bool:
    """Strip markdown links to sifufinds.com paths that don't resolve to a
    real page and aren't covered by an .htaccess redirect.

    The AI blog-writer agent occasionally hallucinates internal URLs (e.g.
    "[African Bookmakers](https://sifufinds.com/african-bookmakers)") that
    don't exist. Left in place these 404 on the live site and trip
    scripts/validate_site.py CHECK 2, which blocks every deploy until fixed
    by hand — this silently stopped new posts reaching production for days
    (see AGENT-KNOWLEDGE.md, 2026-07-12). Converting them to plain text
    keeps the deploy pipeline moving automatically; the auto-linker below
    (COUNTRY_LINKS / BOOKMAKER_LINKS / CORE_LINKS) still hyperlinks the same
    terms correctly on its own pass.
    """
    redirect_targets = _load_htaccess_redirect_targets()
    changed = False

    def resolve(match: re.Match) -> str:
        text, path = match.group(1), match.group(2).rstrip('/')
        target = f'https://sifufinds.com/{path}'
        index_file = os.path.join(BASE, path, 'index.html')
        html_file = os.path.join(BASE, path + '.html')
        if os.path.exists(index_file) or os.path.exists(html_file) or target in redirect_targets:
            return match.group(0)
        return text

    for post in posts:
        body = post.get('body', '')
        if 'sifufinds.com/' not in body:
            continue
        new_body = _INTERNAL_LINK_RE.sub(resolve, body)
        if new_body != body:
            post['body'] = new_body
            changed = True
            print(f"  ⚠  stripped broken internal link(s) from post '{post.get('slug', '?')}'")
    return changed


def dedupe_slugs(posts: list) -> bool:
    """Ensure every post has a unique slug.

    The generation loop below writes blog/<slug>/index.html for every post in
    array order, so two posts sharing a slug silently collide — the later
    array entry overwrites the earlier one's page and its content is never
    reachable at its own URL. When a collision is found, the later entry (the
    one that actually ends up live) keeps the original slug; every earlier
    entry gets a fresh slug derived from its own title so its content gets
    its own page instead of being shadowed.
    """
    from collections import defaultdict
    by_slug = defaultdict(list)
    for i, p in enumerate(posts):
        by_slug[p.get('slug', '')].append(i)

    existing = {p.get('slug', '') for p in posts}
    changed = False
    for slug, idxs in by_slug.items():
        if not slug or len(idxs) <= 1:
            continue
        for i in idxs[:-1]:
            post = posts[i]
            base = slugify(post.get('title', slug)) or slug
            new_slug, n = base, 2
            while new_slug in existing:
                new_slug = f'{base}-{n}'
                n += 1
            print(f"  ⚠  duplicate slug '{slug}' — renaming post {post.get('id', '?')} → '{new_slug}'")
            post['slug'] = new_slug
            existing.add(new_slug)
            changed = True
    return changed


def main():
    # Load existing posts
    with open(POSTS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if dedupe_slugs(data.get('posts', [])):
        with open(POSTS_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print('  ✓  Fixed duplicate slugs — posts.json updated')

    if sanitize_internal_links(data.get('posts', [])):
        with open(POSTS_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print('  ✓  Stripped broken internal links — posts.json updated')

    existing_slugs = {p['slug'] for p in data.get('posts', [])}

    # Add new posts (avoid duplicates)
    now_iso = datetime.now(timezone.utc).isoformat()
    posts_added = 0
    for post in NEW_POSTS:
        if post['slug'] not in existing_slugs:
            post['id'] = f"post-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{abs(hash(post['slug'])) % 999}"
            post['published_at'] = now_iso
            # Unique feature image — doubles as og:image/twitter:image and the
            # LinkedIn/Facebook/X share preview (see scripts/generate_blog_feature_image.py).
            try:
                from scripts.generate_blog_feature_image import ensure_feature_image
                feature_image = ensure_feature_image(post)
                if feature_image:
                    post['feature_image'] = feature_image
            except Exception as e:
                print(f'  ⚠  feature image generation failed for {post["slug"]}: {e}')
            data['posts'].insert(0, post)
            existing_slugs.add(post['slug'])
            posts_added += 1

    # Save updated posts.json
    with open(POSTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'  ✓  {posts_added} new posts added to posts.json ({len(data["posts"])} total)')

    # Populate global post list for internal linking
    global _ALL_POSTS
    _ALL_POSTS = data['posts']

    # Generate static HTML for every post, plus a locale-suffixed page
    # (blog/{slug}-fr/, blog/{slug}-de/, ...) for every language that has a
    # translation on file in blog/translations/{locale}.json.
    blog_dir = os.path.join(BASE, 'blog')
    pages_created = 0
    pages_skipped = 0

    import sys
    force = '--force' in sys.argv

    locale_translations = {lg: load_translations(lg) for lg in LOCALES}
    resolve_title_collisions(data['posts'], locale_translations)

    for post in data['posts']:
        slug = post.get('slug')
        if not slug:
            continue

        available_locales = [lg for lg in LOCALES if slug in locale_translations[lg]]

        for locale in ['en'] + available_locales:
            out_slug = slug if locale == 'en' else f'{slug}-{locale}'
            post_dir = os.path.join(blog_dir, out_slug)
            out_path = os.path.join(post_dir, 'index.html')

            if os.path.exists(out_path) and not force:
                pages_skipped += 1
                continue

            os.makedirs(post_dir, exist_ok=True)
            html = build_post_page(post, locale=locale,
                                    translations=locale_translations.get(locale),
                                    available_locales=available_locales)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(html)
            pages_created += 1
            marker = '↻' if force else '✓'
            print(f'  {marker}  blog/{out_slug}/index.html')

    print(f'\n✅  {pages_created} static blog post pages created ({pages_skipped} already existed).')
    print(f'    Total blog posts in JSON: {len(data["posts"])}')


if __name__ == '__main__':
    main()
