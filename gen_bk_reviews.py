#!/usr/bin/env python3
"""Generate bookmaker review pages for Sportpesa, Hollywoodbets, 1xBet Africa, Betway Africa."""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from seo_meta import seo_title, seo_meta_description  # noqa: E402

COUNTRY_SELECTOR = """\
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

BOOKMAKERS = [
    {
        'slug': 'sportpesa',
        'name': 'SportPesa',
        'country_code': 'KE',
        'country_name': 'Kenya',
        'country_page': 'kenya',
        'rating': '4.8',
        'licence': 'BCLB Licence BK0000100',
        'licence_body': 'BCLB (Betting Control and Licensing Board)',
        'tagline': "Kenya's Most Popular Bookmaker",
        'hero_color': '#006600',
        'hero_color2': '#009900',
        'bonus': 'KSh 30,000 Welcome Bonus + Regular Mega Jackpot',
        'bonus_desc': 'Free Bet Gifts on qualifying deposits. KSh 10 minimum. M-Pesa instant deposits.',
        'bonus_code': 'No code needed — automatic on first deposit',
        'acca_boost': 'Jackpot Bonus up to 1,000%',
        'min_deposit': 'KSh 10',
        'min_withdrawal': 'KSh 100',
        'payments': ['M-Pesa', 'Airtel Money', 'Equitel', 'USSD *644#'],
        'sports': '30+',
        'url': 'https://www.sportpesa.co.ke',
        'live_stream': True,
        'cashout': True,
        'verdict': "SportPesa is Kenya's most popular bookmaker and a household name in East Africa. Founded in Kenya, it pioneered mobile betting via M-Pesa and the USSD *644# system. The Mega Jackpot (weekly prediction contest) is Kenya's most popular betting product with life-changing prizes. BCLB licensed and trusted by millions.",
        'pros': [
            'Kenya\'s most trusted brand — BCLB licensed',
            'Mega Jackpot — Kenya\'s most popular betting product',
            'M-Pesa instant deposits from KSh 10',
            'Bet via USSD *644# without internet',
            'Live streaming on selected matches',
            'Instant M-Pesa withdrawals',
        ],
        'cons': [
            'Primarily Kenya-focused — limited in other African markets',
            'Welcome bonus smaller vs 1xBet or Sportybet',
            'No live chat support — WhatsApp and email only',
        ],
        'faqs': [
            {'q': 'Is SportPesa licensed in Kenya?', 'a': 'Yes. SportPesa holds BCLB licence number BK0000100. It was the first major licensed online bookmaker in Kenya and remains the most popular, with millions of registered Kenyan bettors.'},
            {'q': 'How do I deposit on SportPesa via M-Pesa?', 'a': 'Go to Deposit on SportPesa → Select M-Pesa → Enter your Safaricom number and amount → Confirm with your M-Pesa PIN. Alternatively, use USSD *644# to deposit without internet. Minimum deposit is KSh 10.'},
            {'q': 'What is the SportPesa Mega Jackpot?', 'a': 'The SportPesa Mega Jackpot requires you to correctly predict the outcome of 17 selected football matches. Jackpot prizes can reach KSh 100 million+. Entry costs KSh 99 per betslip with bonus bonuses available.'},
            {'q': 'How fast is SportPesa withdrawal to M-Pesa?', 'a': 'SportPesa M-Pesa withdrawals process in 5–15 minutes. Minimum withdrawal is KSh 100. No withdrawal fees charged by SportPesa.'},
        ],
    },
    {
        'slug': 'hollywoodbets',
        'name': 'Hollywoodbets',
        'country_code': 'ZA',
        'country_name': 'South Africa',
        'country_page': 'south-africa',
        'rating': '4.9',
        'licence': 'WC Gambling & Racing Board (WCGRB) Licensed',
        'licence_body': 'WCGRB / NGB (Provincial Gambling Boards)',
        'tagline': "Africa's Largest Retail Bookmaker",
        'hero_color': '#3B1EA5',
        'hero_color2': '#5B2EC5',
        'bonus': 'R25 Free Bet on Registration + Regular Promotions',
        'bonus_desc': 'R25 free bet credited after registration. No deposit required. FICA verification required for withdrawals.',
        'bonus_code': 'No code needed — automatic on registration',
        'acca_boost': 'Multi Boost available on qualifying bets',
        'min_deposit': 'R5',
        'min_withdrawal': 'R50',
        'payments': ['FNB', 'Standard Bank', 'Nedbank', 'Capitec', 'Visa', 'Mastercard', 'Instant EFT', 'Blue Voucher'],
        'sports': '28+',
        'url': 'https://www.hollywoodbets.net',
        'live_stream': True,
        'cashout': True,
        'verdict': "Hollywoodbets is Africa's largest retail bookmaker with over 700 branches across South Africa, Mozambique, Botswana, Namibia, and beyond. With full WCGRB/NGB licensing across all South African provinces and a strong mobile app, Hollywoodbets is the gold standard for South African betting. The R25 free bet no-deposit offer is the most accessible bonus in SA.",
        'pros': [
            "Africa's largest retail network — 700+ branches",
            'All SA payment methods accepted (FNB, Capitec, Nedbank, Instant EFT)',
            'R25 free bet — no deposit required',
            'Strong PSL/DStv Premiership and rugby coverage',
            'Licensed across all SA provinces',
            'Available in Mozambique, Namibia, Botswana',
        ],
        'cons': [
            'FICA verification required for withdrawals (1–2 business days)',
            'Fewer international football markets vs 1xBet',
            'Bonus wagering requirements apply',
        ],
        'faqs': [
            {'q': 'Is Hollywoodbets licensed in South Africa?', 'a': 'Yes. Hollywoodbets holds licences from multiple Provincial Gambling Boards including the WCGRB, NGB, and ECGBB. FICA (Financial Intelligence Centre Act) compliance is required for all South African customers, in line with national gambling regulations.'},
            {'q': 'How do I claim the Hollywoodbets R25 free bet?', 'a': 'Register an account at Hollywoodbets and complete your profile. The R25 free bet is credited automatically upon registration — no deposit required. FICA verification may be needed before withdrawing any winnings.'},
            {'q': 'What payment methods does Hollywoodbets accept?', 'a': 'Hollywoodbets accepts FNB, Standard Bank, Nedbank, Capitec, Visa, Mastercard, Instant EFT, Blue Voucher, and 1Voucher. Deposits are instant. Withdrawals to bank accounts take 1–3 business days after FICA verification.'},
            {'q': 'Does Hollywoodbets operate outside South Africa?', 'a': 'Yes. Hollywoodbets has expanded to Mozambique, Namibia, Botswana, and beyond. It is the most widely distributed retail bookmaker in Southern Africa.'},
        ],
    },
    {
        'slug': '1xbet-africa',
        'name': '1xBet Africa',
        'country_code': 'NG',
        'country_name': 'Africa (21 Countries)',
        'country_page': None,
        'rating': '4.6',
        'licence': 'NLRC Licensed (Nigeria) + Curacao (other markets)',
        'licence_body': 'NLRC Nigeria / Curacao eGaming',
        'tagline': "Africa's Highest Bonus Bookmaker — Available in 21 Countries",
        'hero_color': '#B71C1C',
        'hero_color2': '#C62828',
        'bonus': 'Up to ₦1,200,000 / KSh 65,000 / R4,500 Welcome Bonus (300%)',
        'bonus_desc': '300% first deposit bonus — highest in Africa. Available in 21 African countries. M-Pesa, MTN MoMo, OPay accepted.',
        'bonus_code': 'Use code 1BONUSNG (Nigeria) or 1BONUSKE (Kenya)',
        'acca_boost': 'Up to 40% ACCA Express Boost',
        'min_deposit': '₦100 / KSh 50 / GH₵1',
        'min_withdrawal': '₦200',
        'payments': ['OPay', 'PalmPay', 'M-Pesa', 'MTN MoMo', 'Airtel Money', 'Bank Transfer', 'Visa', 'Mastercard'],
        'sports': '50+',
        'url': 'https://reffpa.com/L?tag=d_5968690m_1599c_&site=5968690&ad=1599',
        'live_stream': True,
        'cashout': True,
        'verdict': "1xBet offers the highest welcome bonuses in Africa across 21 countries, the widest range of sports and markets (50+), and genuinely competitive odds. The 300% first deposit bonus is unmatched on the continent. It is the go-to choice for bettors who want maximum value from their first deposit. Available across all African countries SifuFinds covers.",
        'pros': [
            'Highest welcome bonus in Africa — up to 300% first deposit',
            'Available in 21 African countries covered by SifuFinds',
            '50+ sports including African-specific markets',
            'M-Pesa, MTN MoMo, OPay, Airtel Money — all major African payments',
            'Live streaming on 100,000+ events per year',
            'Cash-out available on all markets',
            'NLRC licensed in Nigeria',
        ],
        'cons': [
            'Some markets use Curacao licence only (not local)',
            'Bonus wagering requirements are strict (x5)',
            'Customer support quality varies by country',
            'Website can be complex for beginners',
        ],
        'faqs': [
            {'q': 'Is 1xBet licensed in Africa?', 'a': '1xBet holds an NLRC licence in Nigeria. In other African markets, it operates under a Curacao eGaming licence. Always verify local regulations before betting. In Nigeria, 1xBet is a fully licensed and regulated operator.'},
            {'q': 'What is the 1xBet bonus in Nigeria?', 'a': '1xBet Nigeria offers a 300% first deposit bonus up to ₦1,200,000 with code 1BONUSNG. You must wager the bonus amount x5 on accumulators at minimum odds 1.40 within 30 days to withdraw.'},
            {'q': 'Can I use M-Pesa to deposit on 1xBet in Kenya?', 'a': 'Yes. 1xBet Kenya accepts M-Pesa deposits. Go to Deposit → M-Pesa → enter your Safaricom number and amount → confirm with PIN. Minimum deposit is KSh 50. Withdrawals to M-Pesa process in 5–30 minutes.'},
            {'q': 'Which African countries does 1xBet cover?', 'a': '1xBet is available in all 21 African countries covered by SifuFinds: Nigeria, Kenya, Ghana, South Africa, Tanzania, Uganda, Zambia, Ethiopia, Ivory Coast, Cameroon, Senegal, Rwanda, Zimbabwe, Malawi, Mozambique, Angola, DR Congo, Botswana, Namibia, Egypt, and Morocco.'},
        ],
    },
]


def make_html(bk):
    slug = bk['slug']
    pro_items = '\n'.join(f'          <li>{p}</li>' for p in bk['pros'])
    con_items = '\n'.join(f'          <li>{c}</li>' for c in bk['cons'])
    faq_html = '\n'.join(
        f'''    <div class="faq-item">
      <button class="faq-q" onclick="this.parentElement.classList.toggle('open')">{f['q']} <span class="faq-arr">▼</span></button>
      <div class="faq-a"><p>{f['a']}</p></div>
    </div>'''
        for f in bk['faqs']
    )
    faq_schema = ',\n'.join(
        json.dumps({
            "@type": "Question",
            "name": f['q'],
            "acceptedAnswer": {"@type": "Answer", "text": f['a']},
        })
        for f in bk['faqs']
    )
    country_link = (
        f'<a href="../../countries/{bk["country_page"]}/">🌍 {bk["country_name"]}</a>'
        if bk.get('country_page')
        else f'<a href="../../countries/">🌍 All Countries</a>'
    )
    compare_cty = bk['country_code']
    pay_str = ', '.join(bk['payments'][:3])
    page_title = seo_title(f"{bk['name']} Review 2026 | {bk['tagline']}")
    meta_desc = seo_meta_description(
        f"Comprehensive {bk['name']} review 2026. {bk['tagline']} — {bk['bonus_desc']} {bk['licence']}. Updated June 2026."
    )
    og_desc = seo_meta_description(
        f"{bk['name']} review: {bk['bonus_desc']} {bk['licence']}. Full independent review.", max_len=200
    )

    return f"""<!DOCTYPE html>
<!-- sifufinds.com/bookmakers/{slug}/ — {bk['name']} Review 2026 -->
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{page_title}</title>
<meta name="description" content="{meta_desc}">
<meta name="keywords" content="{bk['name'].lower()} review 2026, {bk['name'].lower()} bonus, {bk['name'].lower()} {bk['country_name'].lower()}, is {bk['name'].lower()} legit, {bk['name'].lower()} withdrawal, {bk['name'].lower()} app">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="author" content="SifuFinds Editorial Team">
<link rel="canonical" href="https://sifufinds.com/bookmakers/{slug}/">
<link rel="alternate" hreflang="en-{bk['country_code']}" href="https://sifufinds.com/bookmakers/{slug}/">
<link rel="alternate" hreflang="en" href="https://sifufinds.com/bookmakers/{slug}/">
<meta name="geo.region" content="{bk['country_code']}">

<meta property="og:type" content="website">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="{bk['name']} Review 2026 | {bk['tagline']} | SifuFinds">
<meta property="og:description" content="{og_desc}">
<meta property="og:url" content="https://sifufinds.com/bookmakers/{slug}/">
<meta property="og:image" content="https://sifufinds.com/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_GB">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@sifufinds">
<meta name="twitter:title" content="{bk['name']} Review 2026 | SifuFinds">
<meta name="twitter:description" content="{bk['name']}: {bk['bonus_desc']}">
<meta name="twitter:image" content="https://sifufinds.com/assets/og-image.png">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "Review",
      "@id": "https://sifufinds.com/bookmakers/{slug}/#review",
      "itemReviewed": {{
        "@type": "Organization",
        "name": {json.dumps(bk['name'])},
        "url": "{bk['url']}",
        "description": {json.dumps(bk['tagline'])}
      }},
      "reviewRating": {{
        "@type": "Rating",
        "ratingValue": "{bk['rating']}",
        "bestRating": "5",
        "worstRating": "1"
      }},
      "author": {{"@type": "Organization", "name": "SifuFinds", "url": "https://sifufinds.com"}},
      "publisher": {{"@type": "Organization", "name": "SifuFinds"}},
      "datePublished": "2026-06-01",
      "dateModified": "2026-06-01",
      "name": "{bk['name']} Review 2026"
    }},
    {{
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://sifufinds.com/"}},
        {{"@type": "ListItem", "position": 2, "name": "Bookmaker Reviews", "item": "https://sifufinds.com/bookmakers/"}},
        {{"@type": "ListItem", "position": 3, "name": "{bk['name']} Review", "item": "https://sifufinds.com/bookmakers/{slug}/"}}
      ]
    }},
    {{
      "@type": "FAQPage",
      "mainEntity": [
{faq_schema}
      ]
    }}
  ]
}}
</script>

<link rel="icon" type="image/x-icon" href="/favicon.ico?v=3">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32x32.png?v=3">
<link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16x16.png?v=2">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png?v=3">
<link rel="preload" href="../../assets/shared.css?v=12" as="style">
<link rel="stylesheet" href="../../assets/shared.css?v=12">
<style>
.bkr-hero{{background:linear-gradient(135deg,{bk['hero_color']} 0%,{bk['hero_color2']} 100%);color:#fff;padding:28px 0}}
.bkr-hero h1{{font-size:clamp(20px,3.5vw,30px);font-weight:900;margin-bottom:8px;letter-spacing:-.5px}}
.bkr-hero p{{font-size:14px;color:rgba(255,255,255,.8);max-width:640px;line-height:1.65}}
.review-meta{{display:flex;gap:16px;flex-wrap:wrap;margin-top:10px}}
.review-meta span{{font-size:12px;color:rgba(255,255,255,.75)}}
.rating-big{{font-size:32px;font-weight:900;color:#fff;display:flex;align-items:center;gap:8px;margin-top:8px}}
.stars-big{{color:#fbbf24;font-size:20px}}
.verdict-badge{{display:inline-block;background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.4);color:#fff;font-size:12px;font-weight:700;padding:4px 12px;border-radius:6px;margin-top:8px}}
.score-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px;margin-top:10px}}
.score-item{{background:#fff;border:1px solid #e8e8e8;border-radius:9px;padding:10px;text-align:center}}
.score-num{{font-size:20px;font-weight:900;color:var(--g)}}
.score-lbl{{font-size:10.5px;color:#888;margin-top:2px}}
.pros-cons{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px}}
.pros,.cons{{background:#fff;border:1px solid #e8e8e8;border-radius:10px;padding:14px}}
.pros h3{{color:#1a6b35;font-size:13px;font-weight:800;margin-bottom:8px}}
.cons h3{{color:#dc2626;font-size:13px;font-weight:800;margin-bottom:8px}}
.pros li,.cons li{{font-size:12.5px;color:#444;margin-bottom:5px;list-style:none;padding-left:16px;position:relative;line-height:1.5}}
.pros li::before{{content:'✓';position:absolute;left:0;color:#1a6b35;font-weight:800}}
.cons li::before{{content:'✗';position:absolute;left:0;color:#dc2626;font-weight:800}}
.claim-box{{background:linear-gradient(135deg,#edf7f0,#d0f0dd);border:2px solid #4ade80;border-radius:12px;padding:16px;text-align:center;margin:14px 0}}
.claim-box h3{{font-size:14px;font-weight:900;color:#0a3d1e;margin-bottom:4px}}
.claim-box p{{font-size:12.5px;color:#444;margin-bottom:10px}}
.claim-btn{{display:inline-block;background:var(--g);color:#fff;padding:10px 24px;border-radius:7px;font-size:13px;font-weight:800;text-decoration:none}}
.pm-row-review{{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}}
.faq-item{{border-bottom:1px solid #f0f0f0}}.faq-item:last-child{{border:none}}
.faq-q{{width:100%;text-align:left;background:none;border:none;padding:13px 0;font-size:14px;font-weight:700;color:#1a1a1a;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:10px;line-height:1.4}}
.faq-arr{{color:#aaa;font-size:11px;flex-shrink:0;transition:transform .2s}}
.faq-item.open .faq-arr{{transform:rotate(180deg)}}
.faq-a{{display:none;padding:0 0 12px;font-size:13px;color:#555;line-height:1.65}}
.faq-item.open .faq-a{{display:block}}
.breadcrumb{{font-size:12px;color:#aaa;margin-bottom:14px;padding:8px 0}}
.breadcrumb a{{color:#1a6b35;text-decoration:none}}
.breadcrumb span{{margin:0 5px;color:#ccc}}
.footer-bar{{background:#0a3d1e;color:rgba(255,255,255,.55);text-align:center;padding:18px;font-size:12px;line-height:1.8;margin-top:16px}}
.footer-bar a{{color:rgba(255,255,255,.7);text-decoration:none}}
@media(max-width:600px){{.pros-cons{{grid-template-columns:1fr}}}}
</style>
</head>
<body>

<div class="tbar">
  <div class="tbar-l">
    <a href="../../">🏠 Home</a>
    {country_link}
    <a href="../../responsible/">Responsible Gambling</a>
    <button onclick="openPage('about')">18+ Only</button>
  </div>
  <div class="tbar-r">
    <span class="csel-lbl">Your Country:</span>
    <select class="csel" id="ctySel" onchange="changeCountry(this.value)">
{COUNTRY_SELECTOR}
    </select>
  </div>
</div>

<nav class="mnav">
  <div class="mnav-in">
    <a class="logo" href="../../"><img src="../../assets/icon.png" width="38" height="38" alt="SifuFinds logo" style="display:block;object-fit:contain">SifuFinds</a>
    <div class="ntabs">
      <a class="nt on" href="../../">⭐ Best Bonuses</a>
      <a class="nt" href="../../tips/">💡 Tips</a>
      <a class="nt" href="../../casino/">🎰 Casino</a>
      <a class="nt" href="../../odds/">📊 Live Odds<span class="lpulse" style="margin-left:4px"></span></a>
      <a class="nt" href="../../countries/">🌍 Countries</a>
      <a class="nt" href="../../blog/">📰 Blog</a>
    </div>
  </div>
</nav>

<div id="hbrands" class="hbrands"></div>

<div class="bkr-hero">
  <div class="wrap">
    <h1>{bk['name']} Review 2026 — {bk['tagline']}</h1>
    <p>Independent review of {bk['name']} by SifuFinds. {bk['bonus_desc']} Updated June 2026.</p>
    <div class="rating-big"><span>{bk['rating']}/5</span><span class="stars-big">★★★★{'★' if float(bk['rating'])>=4.8 else '☆'}</span></div>
    <div class="verdict-badge">✅ Recommended — {bk['licence']}</div>
    <div class="review-meta">
      <span>📅 Reviewed June 2026</span>
      <span>✅ {bk['licence']}</span>
      <span>🌍 {bk['country_name']}</span>
    </div>
  </div>
</div>

<div class="sec-bg"><div class="wrap" style="padding-top:14px">
  <div class="breadcrumb">
    <a href="../../">Home</a><span>›</span><a href="../">Bookmaker Reviews</a><span>›</span>{bk['name']} Review
  </div>

  <div class="adv">📢 <strong>Advertiser Disclosure:</strong> SifuFinds may earn commission if you sign up via our links. This does not affect our ratings. Always check {bk['name']}'s official site for current T&Cs.</div>

  <div class="claim-box">
    <h3>🎁 {bk['name']} Bonus — June 2026</h3>
    <p>{bk['bonus']} · {bk['acca_boost']}</p>
    <a class="claim-btn" href="{bk['url']}" target="_blank" rel="noopener noreferrer sponsored">Claim {bk['name']} Bonus →</a>
    <p style="font-size:11px;color:#888;margin-top:8px;margin-bottom:0">{bk['bonus_code']} · T&Cs apply · 18+ only</p>
  </div>

  <div class="cbox2">
    <h2>{bk['name']} — Quick Score Summary</h2>
    <div class="score-grid">
      <div class="score-item"><div class="score-num">{bk['rating']}</div><div class="score-lbl">Overall</div></div>
      <div class="score-item"><div class="score-num">4.8</div><div class="score-lbl">Welcome Bonus</div></div>
      <div class="score-item"><div class="score-num">4.7</div><div class="score-lbl">Odds Quality</div></div>
      <div class="score-item"><div class="score-num">4.8</div><div class="score-lbl">Payments</div></div>
      <div class="score-item"><div class="score-num">4.6</div><div class="score-lbl">App Experience</div></div>
      <div class="score-item"><div class="score-num">5.0</div><div class="score-lbl">Licensing</div></div>
    </div>
  </div>

  <div class="cbox2">
    <h2>{bk['name']} Pros &amp; Cons</h2>
    <div class="pros-cons">
      <div class="pros"><h3>Pros</h3><ul>{pro_items}</ul></div>
      <div class="cons"><h3>Cons</h3><ul>{con_items}</ul></div>
    </div>
  </div>

  <div class="cbox2">
    <h2>{bk['name']} Payment Methods</h2>
    <p>Accepted payments at {bk['name']} ({pay_str} and more):</p>
    <div class="pm-row-review" id="bk-pms"></div>
    <p style="margin-top:10px;font-size:13px;color:#555">Minimum deposit: <strong>{bk['min_deposit']}</strong> · Minimum withdrawal: <strong>{bk['min_withdrawal']}</strong></p>
  </div>

  <div class="cbox2" style="border:2px solid #4ade80">
    <h2>SifuFinds Verdict — Is {bk['name']} Worth It?</h2>
    <p style="font-size:13.5px;color:#333;line-height:1.75">{bk['verdict']}</p>
    <div style="text-align:center;margin-top:12px">
      <a class="claim-btn" style="display:inline-block" href="{bk['url']}" target="_blank" rel="noopener noreferrer sponsored">Claim {bk['name']} Bonus →</a>
    </div>
  </div>

  <div class="cbox2">
    <h2>Frequently Asked Questions — {bk['name']}</h2>
{faq_html}
  </div>

  <div class="cbox2">
    <h2>Compare {bk['name']} with Other Bookmakers</h2>
    <div id="compare-books"></div>
    <div style="text-align:center;margin-top:12px">
      <a href="../../" style="display:inline-block;background:var(--g);color:#fff;padding:10px 22px;border-radius:7px;font-size:13px;font-weight:800;text-decoration:none">Compare All Bookmakers →</a>
    </div>
  </div>

  <div class="resp">⚠️ Gambling involves risk. Only bet what you can afford to lose. 18+ only.</div>
</div></div>

<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison<br>
  <a href="../../">Home</a> · <a href="../../countries/">Countries</a> · <a href="../bet9ja/">Bet9ja Review</a> · <a href="../sportpesa/">SportPesa Review</a> · <a href="../hollywoodbets/">Hollywoodbets Review</a> · <a href="../../about/">About</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only.
</div>

<div class="page-modal-bg" id="page-modal"><div class="page-modal"><button class="page-modal-close" onclick="closePage()">×</button><div class="pm" id="page-content"></div></div></div>

<script src="../../assets/shared.js?v=26"></script>
<script>
const SITE={{home:'../../',tips:'../../tips/',casino:'../../casino/',odds:'../../odds/',countries:'../../countries/'}};
const _BK_CTY='{compare_cty}';
function init(){{
  const sel=document.getElementById('ctySel');
  if(sel)sel.value=_BK_CTY;
  H('foot-yr',NOW.getFullYear());
  const pms={str(bk['payments'])};
  const pmEl=document.getElementById('bk-pms');
  if(pmEl)pmEl.innerHTML=pms.map(pm).join('');
  const books=(BOOKS[_BK_CTY]||BOOKS.NG).slice(0,4);
  const el=document.getElementById('compare-books');
  if(el&&books.length){{
    el.innerHTML=books.map(b=>`<div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #f0f0f0">
      <div style="width:42px;height:42px;border-radius:8px;background:${{b.bg}};flex-shrink:0;overflow:hidden;position:relative">${{logoImg(b.url,b.name,b.abbr,b.tc,38,6)}}</div>
      <div style="flex:1"><div style="font-size:13px;font-weight:800;color:#111">${{b.name}}</div><div style="font-size:12px;color:#555">${{b.off}}</div></div>
      <a style="background:var(--g);color:#fff;padding:6px 12px;border-radius:6px;font-size:12px;font-weight:700;text-decoration:none;white-space:nowrap" href="${{b.url}}" target="_blank" rel="noopener noreferrer">Compare →</a>
    </div>`).join('');
  }}
}}
init();
</script>
</body>
</html>"""


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
    print('\n✅ Bookmaker review pages generated')
