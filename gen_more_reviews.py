#!/usr/bin/env python3
"""Generate Betway Africa and Sportybet review pages."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_bk_reviews import make_html, BASE

BOOKMAKERS = [
    {
        'slug': 'betway-africa',
        'name': 'Betway Africa',
        'country_code': 'NG',
        'country_name': 'Africa (15+ Countries)',
        'country_page': None,
        'rating': '4.7',
        'licence': 'Multi-jurisdiction Licensed (NLRC, BCLB, WCGRB)',
        'licence_body': 'NLRC Nigeria / BCLB Kenya / WCGRB South Africa',
        'tagline': 'International Brand Available Across Africa',
        'hero_color': '#005CA9',
        'hero_color2': '#0070CC',
        'bonus': '50–100% Welcome Bonus in local currency across African markets',
        'bonus_desc': 'Country-specific welcome bonuses. M-Pesa, MTN MoMo, OPay accepted. Licensed in Nigeria, Kenya, SA, Tanzania and more.',
        'bonus_code': 'No code required — automatic on first deposit',
        'acca_boost': 'Multi Boost on qualifying accumulators',
        'min_deposit': '₦200 / KSh 50 / GH₵5',
        'min_withdrawal': '₦200',
        'payments': ['M-Pesa', 'MTN MoMo', 'OPay', 'Airtel Money', 'FNB', 'Visa', 'Mastercard'],
        'sports': '28+',
        'url': 'https://www.betway.com',
        'live_stream': True,
        'cashout': True,
        'verdict': "Betway is one of the most trusted international bookmakers operating in Africa, with licences across Nigeria, Kenya, South Africa, Tanzania, Rwanda, Botswana, Namibia and more. It offers consistent odds quality, reliable payments, and excellent live streaming. The welcome bonus varies by country but is always competitive. Betway's mobile app is among the best available in Africa.",
        'pros': [
            'Licensed in 8+ African countries by local regulators',
            'Excellent mobile app — best UI/UX in African betting',
            'Live streaming on 100,000+ events per year',
            'Available across Nigeria, Kenya, SA, Tanzania, Rwanda, Botswana, Namibia',
            'Instant mobile money deposits (M-Pesa, MTN MoMo, OPay)',
            'Cash-out on all markets',
            'Strong in-play betting platform',
        ],
        'cons': [
            'Welcome bonus lower than 1xBet or Melbet',
            'Fewer sports markets vs 1xBet (28 vs 50+)',
            'FICA verification required in South Africa',
        ],
        'faqs': [
            {'q': 'Is Betway licensed in Africa?', 'a': 'Yes. Betway holds licences in multiple African countries: NLRC (Nigeria), BCLB (Kenya), WCGRB (South Africa), Gaming Board Tanzania, Rwanda Gaming Commission, GAB (Botswana), GBN (Namibia) and others. It is one of the most widely licensed bookmakers on the continent.'},
            {'q': 'How do I deposit on Betway in Nigeria?', 'a': 'Betway Nigeria accepts OPay, PalmPay, bank transfer, Visa, and Mastercard. Minimum deposit is ₦200. All deposits process instantly.'},
            {'q': 'Does Betway offer live streaming?', 'a': 'Yes. Betway offers live streaming on 100,000+ events per year across football, tennis, basketball, and more. You need a funded account to access the stream. Available in all African markets where Betway operates.'},
            {'q': 'What is the Betway welcome bonus in Africa?', 'a': 'The Betway welcome bonus varies by country. In Nigeria: 100% match up to ₦1,500. Kenya: 100% match up to KSh 3,000. South Africa: R500 free bet. Tanzania: TSh 120,000. All bonuses are verified by SifuFinds and updated regularly.'},
        ],
    },
    {
        'slug': 'sportybet',
        'name': 'Sportybet',
        'country_code': 'NG',
        'country_name': 'Nigeria, Kenya, Ghana, Tanzania, Uganda',
        'country_page': 'nigeria',
        'rating': '4.7',
        'licence': 'NLRC Licensed (Nigeria) + local licences in 5 African markets',
        'licence_body': 'NLRC Nigeria / BCLB Kenya / GCA Ghana',
        'tagline': "Africa's Most Downloaded Betting App",
        'hero_color': '#004D00',
        'hero_color2': '#00C851',
        'bonus': '150% Welcome Bonus up to ₦30,000 (Nigeria) / KSh 30,000 (Kenya)',
        'bonus_desc': '150% first deposit bonus — one of Africa\'s highest. Free Bet Gifts on multi-bets. Available in Nigeria, Kenya, Ghana, Tanzania, Uganda.',
        'bonus_code': 'No code needed — automatic on first deposit',
        'acca_boost': 'Free Bet Gifts on qualifying accumulators (3+ legs)',
        'min_deposit': '₦100 (Nigeria) / KSh 50 (Kenya)',
        'min_withdrawal': '₦200',
        'payments': ['OPay', 'Quickteller', 'Bank Transfer', 'M-Pesa', 'MTN MoMo', 'Visa'],
        'sports': '30+',
        'url': 'https://www.sportybet.com/ng/',
        'live_stream': False,
        'cashout': True,
        'verdict': "Sportybet has rapidly become one of Nigeria's top bookmakers since launching in Africa. It offers one of the highest welcome bonuses (150%) in the market, strong odds on Nigerian football, and excellent mobile performance. The app is Africa's most downloaded betting application. Available across 5 African markets with local licensing and instant mobile money payments.",
        'pros': [
            '150% welcome bonus — among Africa\'s highest',
            'Africa\'s most downloaded betting app',
            'NLRC licensed in Nigeria',
            'Excellent NPFL and CAF Champions League coverage',
            'Free Bet Gifts on qualifying multi-bets',
            'Instant OPay and M-Pesa deposits',
            'Cash-out available',
        ],
        'cons': [
            'No live streaming',
            'Fewer markets than 1xBet',
            'Available in 5 African countries only (vs 1xBet\'s 21)',
        ],
        'faqs': [
            {'q': 'Is Sportybet licensed in Nigeria?', 'a': 'Yes. Sportybet Nigeria holds an NLRC licence and is one of Nigeria\'s most popular licensed bookmakers. It also holds licences in Kenya (BCLB), Ghana (GCA), Tanzania (GBT), and Uganda.'},
            {'q': 'What is the Sportybet welcome bonus?', 'a': 'Sportybet Nigeria offers a 150% welcome bonus up to ₦30,000 on your first deposit. In Kenya, the bonus is up to KSh 30,000. Minimum deposit ₦100. Free Bet Gifts are automatically applied to qualifying multi-bets of 3+ legs.'},
            {'q': 'Does Sportybet offer live streaming?', 'a': 'No. Sportybet does not offer live streaming. For live streaming, consider Betway, 1xBet, or Bet9ja which offer live streams on selected matches.'},
            {'q': 'How do I deposit on Sportybet Nigeria?', 'a': 'Sportybet Nigeria accepts OPay, Quickteller, bank transfer, Visa, and Mastercard. Minimum deposit is ₦100. All deposits process instantly. In Kenya, M-Pesa is the primary deposit method.'},
        ],
    },
    {
        'slug': 'betking',
        'name': 'BetKing',
        'country_code': 'NG',
        'country_name': 'Nigeria',
        'country_page': 'nigeria',
        'rating': '4.6',
        'licence': 'NLRC Licensed — KingMakers-Backed Nigerian Brand',
        'licence_body': 'NLRC (National Lottery Regulatory Commission)',
        'tagline': "Nigeria's #1 No-Deposit Bonus Bookmaker",
        'hero_color': '#1C3D5A',
        'hero_color2': '#2B5A7A',
        'bonus': '₦100 Free Bets + 10 Aviator Flights on Registration — No Deposit Required',
        'bonus_desc': 'Nigeria\'s best no-deposit bonus. ₦50 sports + ₦50 virtual free bets + 10 Aviator flights with code BONUSKG. No payment required.',
        'bonus_code': 'Code: BONUSKG',
        'acca_boost': 'Accumulator Bonus available',
        'min_deposit': '₦0 (no deposit bonus) / ₦100 (deposit)',
        'min_withdrawal': '₦100',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa', 'Mastercard', 'USSD'],
        'sports': '25+',
        'url': 'https://www.betking.com',
        'live_stream': True,
        'cashout': True,
        'verdict': "BetKing is Nigeria's most exciting no-deposit bonus offer in 2026. Backed by KingMakers, BetKing gives new users ₦100 in free bets plus 10 free Aviator flights with zero deposit required — just registration. NLRC licensed, strong NPFL and EPL markets, and instant OPay/PalmPay payments make it an excellent choice for Nigerian bettors looking to start without risk.",
        'pros': [
            'Best no-deposit bonus in Nigeria — ₦100 free + 10 Aviator flights',
            'NLRC licensed — fully regulated',
            'KingMakers-backed (institutional investment)',
            'Instant OPay and PalmPay deposits',
            'Strong NPFL and virtual sports coverage',
            'Live streaming on selected matches',
        ],
        'cons': [
            'Nigeria-only market',
            'Smaller brand compared to Bet9ja/1xBet',
            'No deposit bonus has 7-day expiry',
        ],
        'faqs': [
            {'q': 'Is BetKing licensed in Nigeria?', 'a': 'Yes. BetKing holds a valid NLRC licence in Nigeria. It is backed by KingMakers, a leading African sports entertainment company, making it one of the most institutionally supported bookmakers in Nigeria.'},
            {'q': 'What is the BetKing no-deposit bonus?', 'a': 'BetKing offers ₦100 free bets (₦50 sportsbook + ₦50 virtual) plus 10 free Aviator flights with code BONUSKG on registration — no deposit needed. Bonuses expire after 7 days. T&Cs apply.'},
            {'q': 'How do I claim the BetKing free bet?', 'a': 'Register at BetKing → Enter code BONUSKG → Verify your phone number → Free bets and Aviator flights are credited automatically within one working day. No deposit required.'},
        ],
    },
]

if __name__ == '__main__':
    for bk in BOOKMAKERS:
        slug = bk['slug']
        out_dir = os.path.join(BASE, 'bookmakers', slug)
        os.makedirs(out_dir, exist_ok=True)
        html = make_html(bk)
        out_path = os.path.join(out_dir, 'index.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'  ✓  /bookmakers/{slug}/')
    print(f'\n✅ Generated {len(BOOKMAKERS)} additional review pages')
