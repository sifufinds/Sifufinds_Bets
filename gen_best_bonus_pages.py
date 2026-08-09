#!/usr/bin/env python3
"""Generate dedicated per-country bonus landing pages for sifufinds.com.

Each of the 23 supported countries gets a static page at
/best-bonus-in-<slug>/ — e.g. /best-bonus-in-nigeria/, /best-bonus-in-kenya/,
/best-bonus-in-sierra-leone/. These are distinct from /countries/<slug>/
(which compares bookmakers in general) — this page type is bonus-focused:
"Best Bonus Sites in {Country}", not "Best Betting Sites in {Country}".

Reuses the per-country data already maintained in generate_country_pages.py
(name, flag, currency, regulator, payments, leagues, top_bonus, etc.) so
figures stay consistent between the two page types for the same country.
generate_country_pages.py's COUNTRIES dict only covers 19 of the 23
supported countries (missing Egypt, Morocco, Sierra Leone, Liberia) — the
4 extras below were sourced directly from the live countries/<slug>/ pages
so the numbers match what's already published, without touching or
regenerating those existing pages.
"""

import json
import os

from generate_country_pages import COUNTRIES as BASE_COUNTRIES

BASE = os.path.dirname(os.path.abspath(__file__))

YEAR = '2026'
DOMAIN = 'https://sifufinds.com'

EXTRA_COUNTRIES = {
    'EG': {
        'slug': 'egypt', 'name': 'Egypt', 'flag': '🇪🇬',
        'currency': 'EGP', 'symbol': 'EGP',
        'regulator': 'Egyptian Gambling Regulatory Authority (EGRA)',
        'payments': ['Vodafone Cash Egypt', 'Orange Money Egypt', 'Bank Transfer', 'Visa', 'Mastercard'],
        'top_bonus': 'EGP 30,000', 'top_bookmaker': 'Melbet Egypt', 'min_deposit': 'EGP 10', 'books_count': 5,
    },
    'MA': {
        'slug': 'morocco', 'name': 'Morocco', 'flag': '🇲🇦',
        'currency': 'MAD', 'symbol': 'MAD',
        'regulator': 'MDJS (Marocaine des Jeux et des Sports)',
        'payments': ['Bank Transfer', 'CIH Bank', 'Attijari Bank', 'Orange Money Morocco', 'Visa', 'Mastercard'],
        'top_bonus': 'MAD 5,000', 'top_bookmaker': 'Melbet Maroc', 'min_deposit': 'MAD 10', 'books_count': 4,
    },
    'SL': {
        'slug': 'sierra-leone', 'name': 'Sierra Leone', 'flag': '🇸🇱',
        'currency': 'SLL', 'symbol': 'Le',
        'regulator': 'National Lotteries Authority (NLA)',
        'payments': ['Orange Money Sierra Leone', 'Africell Money', 'Bank Transfer', 'Visa'],
        'top_bonus': 'Le 2,000,000', 'top_bookmaker': '1xBet Sierra Leone', 'min_deposit': 'Le 1,000', 'books_count': 3,
    },
    'LR': {
        'slug': 'liberia', 'name': 'Liberia', 'flag': '🇱🇷',
        'currency': 'LRD', 'symbol': '$',
        'regulator': 'National Lottery of Liberia',
        'payments': ['Lonestar MTN Mobile Money', 'Orange Liberia', 'Bank Transfer', 'Visa'],
        'top_bonus': '$200', 'top_bookmaker': '1xBet Liberia', 'min_deposit': '$2', 'books_count': 3,
    },
}

COUNTRIES = {**BASE_COUNTRIES, **EXTRA_COUNTRIES}

COUNTRY_SELECTOR_OPTIONS = """\
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

BONUS_TYPE_LINKS = [
    ('🎉', 'Welcome Bonuses', '../bonuses/welcome-bonus/'),
    ('🆓', 'No-Deposit Bonuses', '../bonuses/no-deposit/'),
    ('🎯', 'Free Bets', '../bonuses/free-bet/'),
    ('💰', 'Cashback Bonuses', '../bonuses/cashback-bonus/'),
    ('🔄', 'Reload Bonuses', '../bonuses/reload-bonus/'),
]


def make_faqs(c):
    name = c['name']
    top_book = c['top_bookmaker']
    top_bonus = c['top_bonus']
    min_dep = c['min_deposit']
    key_payment = c['payments'][0]

    return [
        {
            'q': f'What types of betting bonuses are available in {name}?',
            'a': f'Licensed betting sites in {name} offer welcome bonuses (first-deposit matches), no-deposit bonuses, free bets, cashback on losses, and weekly reload bonuses. Welcome bonuses are the largest and most common, with the current top offer at {top_bonus}.',
        },
        {
            'q': f'Which betting site has the biggest bonus in {name}?',
            'a': f'{top_book} currently offers one of the biggest bonuses in {name} at {top_bonus}. Bonus offers change frequently, so SifuFinds verifies and updates these figures daily — use the Highest Bonus sort above to see the current leader.',
        },
        {
            'q': f'How do I claim a betting bonus in {name}?',
            'a': f'Register at a licensed bookmaker, complete KYC verification, make a qualifying first deposit (minimum {min_dep} at some sites), and the bonus is credited automatically or via a promo code. Always read the specific terms before depositing.',
        },
        {
            'q': f'Are there wagering requirements on bonuses in {name}?',
            'a': f'Yes. Most bonuses in {name} carry a wagering requirement of 3x to 10x the bonus amount that must be bet before winnings can be withdrawn. No-deposit and cashback bonuses often carry lower requirements than welcome bonuses.',
        },
        {
            'q': f'Can I get a bonus without depositing in {name}?',
            'a': f'Some bookmakers in {name} offer no-deposit bonuses just for registering and verifying an account, usually via {key_payment} or a mobile number. These are smaller than deposit-matched welcome bonuses but let you try a site risk-free.',
        },
    ]


def faq_schema_json(faqs):
    items = []
    for f in faqs:
        a_text = f['a'].replace('<strong>', '').replace('</strong>', '')
        items.append(json.dumps({
            "@type": "Question",
            "name": f['q'],
            "acceptedAnswer": {"@type": "Answer", "text": a_text},
        }))
    return ',\n'.join(items)


def faq_html(faqs):
    parts = []
    for f in faqs:
        parts.append(
            f'    <div class="faq-item">\n'
            f'      <button class="faq-q" onclick="this.parentElement.classList.toggle(\'open\')">'
            f'{f["q"]} <span class="faq-arr">▼</span></button>\n'
            f'      <div class="faq-a"><p>{f["a"]}</p></div>\n'
            f'    </div>'
        )
    return '\n'.join(parts)


def generate_page(code, c):
    name = c['name']
    slug = c['slug']
    top_bonus = c['top_bonus']
    top_bookmaker = c['top_bookmaker']
    min_dep = c['min_deposit']
    books_count = c['books_count']
    key_payment = c['payments'][0]

    faqs = make_faqs(c)
    faq_schema = faq_schema_json(faqs)
    faq_block = faq_html(faqs)

    bonus_type_cards = '\n'.join(
        f'''    <a href="{href}" class="bk-card" style="display:block;background:#fff;border-radius:12px;padding:18px 20px;border:2px solid #e8f5e9;text-decoration:none;color:inherit;transition:box-shadow .2s" onmouseover="this.style.boxShadow='0 4px 16px rgba(0,0,0,.1)'" onmouseout="this.style.boxShadow='none'">
      <div style="font-size:22px;margin-bottom:6px">{icon}</div>
      <div style="font-weight:800;color:#0a3d1e;font-size:15px">{label}</div>
      <div style="font-size:12px;color:#666;margin-top:3px">In {name}</div>
    </a>'''
        for icon, label, href in BONUS_TYPE_LINKS
    )

    title = f'Best Bonus Sites in {name} {YEAR} | SifuFinds'
    meta_desc = (
        f'Compare the best betting bonus sites in {name} {YEAR} — welcome offers, no-deposit '
        f'bonuses, free bets and cashback at {books_count} licensed bookmakers. Verified daily.'
    )
    canonical = f'{DOMAIN}/best-bonus-in-{slug}/'
    h1 = f'Best Bonus Sites in {name} &middot; {YEAR}'
    og_alt = f'Best Bonus Sites in {name} — SifuFinds'

    return f"""<!DOCTYPE html>
<!-- sifufinds.com/best-bonus-in-{slug}/ – Best Bonus Sites in {name} {YEAR} -->
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{meta_desc}">
<meta name="keywords" content="best bonus sites {name.lower()}, betting bonus {name.lower()} {YEAR}, welcome bonus {name.lower()}, no deposit bonus {name.lower()}, free bet {name.lower()}, cashback betting {name.lower()}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="author" content="SifuFinds">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="en" href="{canonical}">
<link rel="alternate" hreflang="en-{code}" href="{canonical}">

<meta property="og:type" content="website">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{DOMAIN}/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{og_alt}">
<meta property="og:locale" content="en_GB">
<meta property="og:locale:alternate" content="en_{code}">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@sifufinds">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{meta_desc}">
<meta name="twitter:image" content="{DOMAIN}/assets/og-image.png">

<meta name="geo.region" content="{code}">
<meta name="geo.placename" content="{name}">
<meta name="language" content="English">
<meta name="coverage" content="Africa">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "WebPage",
      "@id": "{canonical}#webpage",
      "name": {json.dumps(title)},
      "description": {json.dumps(meta_desc)},
      "url": "{canonical}",
      "inLanguage": "en-GB",
      "isPartOf": {{"@id": "{DOMAIN}/#website"}}
    }},
    {{
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Home", "item": "{DOMAIN}/"}},
        {{"@type": "ListItem", "position": 2, "name": "Bonuses", "item": "{DOMAIN}/bonuses/"}},
        {{"@type": "ListItem", "position": 3, "name": {json.dumps(name + " Bonus Sites")}, "item": "{canonical}"}}
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

<link rel="icon" type="image/x-icon" href="/favicon.ico?v=2">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32x32.png?v=2">
<link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16x16.png?v=2">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png?v=2">
<link rel="preload" href="../assets/shared.css?v=11" as="style">
<link rel="stylesheet" href="../assets/shared.css?v=11">
<style>
.reg-badge{{display:inline-block;background:#edf7f0;border:1px solid #c8e6c9;border-radius:6px;padding:5px 12px;font-size:12px;font-weight:700;color:#1a6b35;margin-bottom:10px}}
.faq-item{{border-bottom:1px solid #f0f0f0}}
.faq-item:last-child{{border:none}}
.faq-q{{width:100%;text-align:left;background:none;border:none;padding:13px 0;font-size:14px;font-weight:700;color:#1a1a1a;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:10px;line-height:1.4}}
.faq-arr{{color:#aaa;font-size:11px;flex-shrink:0;transition:transform .2s}}
.faq-item.open .faq-arr{{transform:rotate(180deg)}}
.faq-a{{display:none;padding:0 0 12px;font-size:13px;color:#555;line-height:1.65}}
.faq-item.open .faq-a{{display:block}}
.footer-bar{{background:#0a3d1e;color:rgba(255,255,255,.55);text-align:center;padding:18px;font-size:12px;line-height:1.8;margin-top:16px}}
.footer-bar a{{color:rgba(255,255,255,.7);text-decoration:none}}
.footer-bar a:hover{{text-decoration:underline}}
.sec-lbl{{font-size:11px;font-weight:700;color:#aaa;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;margin-top:4px}}
.breadcrumb{{font-size:12px;color:#aaa;margin-bottom:10px;padding:8px 0}}
.breadcrumb a{{color:#1a6b35;text-decoration:none}}
.breadcrumb a:hover{{text-decoration:underline}}
.breadcrumb span{{margin:0 5px;color:#ccc}}
</style>
</head>
<body>

<div class="tbar">
  <div class="tbar-l">
    <a href="../">🏠 Home</a>
    <a href="../bonuses/">🎁 All Bonuses</a>
    <button onclick="openPage('responsible')">Responsible Gambling</button>
    <button onclick="openPage('about')">18+ Only</button>
  </div>
  <div class="tbar-r">
    <span class="csel-lbl">Your Country:</span>
    <select class="csel" id="ctySel" onchange="changeCountry(this.value)">
{COUNTRY_SELECTOR_OPTIONS}
    </select>
  </div>
</div>

<nav class="mnav">
  <div class="mnav-in">
    <a class="logo" href="../">
      <img src="../assets/icon.png" height="38" alt="SifuFinds logo" style="display:block;object-fit:contain">
      SifuFinds
    </a>
    <div class="ntabs">
      <a class="nt" href="../">⭐ Best Bonuses</a>
      <a class="nt" href="../tips/">💡 Tips</a>
      <a class="nt" href="../casino/">🎰 Casino</a>
      <a class="nt" href="../odds/">📊 Live Odds<span class="lpulse" style="margin-left:4px"></span></a>
      <a class="nt" href="../countries/{slug}/">🌍 {name} Sites</a>
      <a class="nt" href="../blog/">📰 Blog</a>
    </div>
  </div>
</nav>

<div id="hbrands" class="hbrands"></div>

<div class="hero"><div class="wrap">
  <h1>{c['flag']} {h1}</h1>
  <p>Looking for the best betting bonus in {name}? {top_bookmaker} currently leads with a {top_bonus} welcome offer, but SifuFinds tracks welcome bonuses, no-deposit offers, free bets, cashback and reload promotions across all {books_count} licensed bookmakers in {name} — verified and updated daily.</p>
  <div class="ctrs">
    <div class="ctr"><div class="ctr-n">{top_bonus}</div><div class="ctr-l">largest bonus</div></div>
    <div class="ctr"><div class="ctr-n">{books_count}</div><div class="ctr-l">bonus sites compared</div></div>
    <div class="ctr"><div class="ctr-n" id="today-d"></div><div class="ctr-l">last updated</div></div>
  </div>
  <div class="trust">
    <div class="tb">✅ Verified Bonuses</div>
    <div class="tb">📱 Mobile-First</div>
    <div class="tb">🔄 Updated Daily</div>
    <div class="tb">💳 {key_payment}</div>
  </div>
</div></div>

<div class="feat-bar"><div class="wrap">
  <div class="feat-lbl">⭐ Top Bonus Offers · {name}</div>
  <div class="feat-grid" id="feat-cards"></div>
</div></div>

<div class="sec-bg"><div class="wrap">
  <div class="breadcrumb">
    <a href="../">Home</a><span>›</span><a href="../bonuses/">Bonuses</a><span>›</span>{name} Bonus Sites
  </div>

  <div class="adv">📢 <strong>Advertiser Disclosure:</strong> We may earn commission from bookmaker links. All bonuses independently verified. Always check the bookmaker's official site for current T&amp;Cs.</div>

  <div class="sec-lbl">TYPES OF BONUSES · {name.upper()} · {YEAR}</div>
  <h2 style="font-size:17px;font-weight:800;color:#111;margin-bottom:9px">Betting Bonus Types Available in {name}</h2>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-bottom:8px">
{bonus_type_cards}
  </div>

  <div class="sec-lbl">VERIFIED BONUS OFFERS · {name.upper()} · {YEAR}</div>
  <h2 style="font-size:17px;font-weight:800;color:#111;margin-bottom:9px">{books_count} Best Bonus Sites in {name} — Verified {YEAR}</h2>

  <div class="fbar"><div class="fr">
    <span class="fr-label">Sort:</span>
    <select class="fsel" id="srt" onchange="renderBooks()">
      <option value="bonus">Highest Bonus</option>
      <option value="default">Editors' Picks</option>
      <option value="stars">Highest Rated</option>
    </select>
    <span class="fr-label" style="margin-left:4px">Filter:</span>
    <button class="fp on" data-f="all" onclick="setFilt(this)">All</button>
    <button class="fp" data-f="nodep" onclick="setFilt(this)">No Deposit</button>
    <button class="fp" data-f="cashout" onclick="setFilt(this)">Cash Out</button>
  </div></div>

  <div class="mc" id="mcount"></div>
  <div id="bk-cards">
    <noscript><p style="padding:20px;color:#666">Enable JavaScript to view bonus listings, or visit <a href="../">SifuFinds.com</a>.</p></noscript>
  </div>

  <div class="cbox2">
    <h2>How to Claim a Betting Bonus in {name}</h2>
    <ol style="padding-left:18px;margin:0;color:#333;line-height:1.8">
      <li>Register at a licensed bookmaker from the list above.</li>
      <li>Complete ID/KYC verification (required before your first withdrawal).</li>
      <li>Make a qualifying first deposit — minimums start from {min_dep}.</li>
      <li>The bonus credits automatically, or enter a promo code if required.</li>
      <li>Meet the wagering requirement before withdrawing bonus winnings.</li>
    </ol>
  </div>

  <div class="cbox2">
    <h2>Bonus Terms to Check Before You Claim</h2>
    <p>Not all bonuses are equal. Before claiming a betting bonus in {name}, check:</p>
    <ul style="padding-left:18px;margin:0;color:#333;line-height:1.8">
      <li><strong>Wagering requirement</strong> — how many times you must bet the bonus before withdrawing.</li>
      <li><strong>Expiry window</strong> — most bonuses expire within 7 days of being credited.</li>
      <li><strong>Minimum odds</strong> — some bonuses only count bets above a set odds threshold.</li>
      <li><strong>Eligible payment method</strong> — a handful of bonuses exclude e-wallet deposits.</li>
      <li><strong>Maximum withdrawal</strong> — some no-deposit bonuses cap how much bonus-derived winnings you can cash out.</li>
    </ul>
  </div>

  <div class="cbox2">
    <h2>Frequently Asked Questions — Bonuses in {name}</h2>
{faq_block}
  </div>

  <div class="resp">⚠️ Gambling involves risk. Only bet what you can afford to lose.
    <button onclick="openPage('responsible')">GamCare</button> ·
    <button onclick="openPage('responsible')">BeGambleAware</button> ·
    <button onclick="openPage('responsible')">NCPG Africa</button>. 18+ only.
  </div>
</div></div>

<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison · <span id="foot-date"></span><br>
  <a href="../">Home</a> · <a href="../bonuses/">All Bonuses</a> · <a href="../countries/{slug}/">Full {name} Site Reviews</a> · <a href="../tips/">Tips</a> · <a href="../odds/">Odds</a> · <a href="../blog/">Blog</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only. Gambling can be addictive. Play responsibly.
</div>

<div class="page-modal-bg" id="page-modal">
  <div class="page-modal">
    <button class="page-modal-close" onclick="closePage()">×</button>
    <div class="pm" id="page-content"></div>
  </div>
</div>

<script src="../assets/shared.js?v=16"></script>
<script>
const SITE={{home:'../',tips:'../tips/',casino:'../casino/',odds:'../odds/',countries:'../countries/'}};
const _PAGE_CTY='{code}';
let _activeFilt='all';

function getCurrentCountry(){{return _PAGE_CTY;}}

function setFilt(btn){{
  document.querySelectorAll('.fp').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  _activeFilt=btn.dataset.f;
  renderBooks();
}}

function filterBooks(books){{
  const f=_activeFilt;
  if(f==='all')return books;
  if(f==='nodep')return books.filter(b=>b.nodep);
  if(f==='cashout')return books.filter(b=>b.cashout);
  return books;
}}

function sortBooks(books){{
  const s=document.getElementById('srt')?.value||'bonus';
  if(s==='stars')return[...books].sort((a,b)=>b.stars-a.stars);
  if(s==='bonus')return[...books].sort((a,b)=>(b.nodep?1:0)-(a.nodep?1:0));
  return books;
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

function renderBooks(){{
  const books=filterBooks(sortBooks(BOOKS[_PAGE_CTY]||[]));
  const el=document.getElementById('bk-cards');
  if(!books.length){{el.innerHTML='<div class="no-results">No bookmakers match this filter.</div>';return;}}
  el.innerHTML=books.map((b,i)=>bookCard(b,i,i)).join('');
  H('mcount',`Showing ${{books.length}} bonus offer${{books.length!==1?'s':''}}`);
}}

function renderFeatCards(){{
  const books=sortBooks((BOOKS[_PAGE_CTY]||[]).slice()).slice(0,12);
  H('feat-cards',books.map(b=>`
  <div class="fc">
    <div class="fc-img" style="background:${{b.bg}}">
      <img src="${{logoUrl(b.url,b.abbr)}}" data-fb="${{logoFb(b.url,b.abbr)}}" alt="${{b.name}} logo" width="180" height="180" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;padding:0;opacity:0;transition:opacity .25s" loading="eager" onload="_logoLoaded(this)" onerror="_imgFallback(this)">
      <span class="fc-nm">${{b.name}}</span>
    </div>
    <div class="fc-body">
      <div class="fc-stars">${{stars(b.stars)}}</div>
      <div class="fc-off">${{b.off}}</div>
      <a class="gbtn" href="${{b.url}}" target="_blank" rel="noopener noreferrer sponsored">Claim →</a>
    </div>
  </div>`).join(''));
}}

function init(){{
  const sel=document.getElementById('ctySel');
  if(sel)sel.value=_PAGE_CTY;
  H('today-d',SHORT_DATE);
  H('foot-date',DATE_STR);
  H('foot-yr',NOW.getFullYear());
  renderBooks();
  renderFeatCards();
}}
init();
</script>
</body>
</html>"""


if __name__ == '__main__':
    created = 0
    for code, country in COUNTRIES.items():
        slug = country['slug']
        out_dir = os.path.join(BASE, f'best-bonus-in-{slug}')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'index.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(generate_page(code, country))
        print(f'  ✓  /best-bonus-in-{slug}/')
        created += 1

    print(f'\n✅ Generated {created} best-bonus-in-<country> pages')
