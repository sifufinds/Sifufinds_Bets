#!/usr/bin/env python3
"""Generate dedicated per-country "Best Betting Sites" landing pages for sifufinds.com.

Restores 2026-08-09 (later same day as the best-bonus-in-<slug>/ rename): the
2026-08-09 rename of countries/<slug>/ ("Best Betting Sites in {Country}") to
best-bonus-in-<slug>/ ("Best Bonus Sites in {Country}") collapsed two
previously-distinct pages into one — the general, bonus-agnostic "Best Betting
Sites" page (which also served as each country's geo-routed homepage, see the
"Geo Homepage Routing" standing rule in CLAUDE.md) was deleted and its URL
turned into a redirect stub pointing at the bonus-focused page instead.

This generator outputs "Best Betting Sites in {Country}" pages to
/best-betting-in-<slug>/ at the repo root, restoring that distinct page type
as its own URL (separate from /best-bonus-in-<slug>/) so the two can coexist:
best-betting-in-<slug>/ is the general licensed-bookmaker comparison and each
country's home page; best-bonus-in-<slug>/ stays the bonus-specific page.

Reuses COUNTRIES/COUNTRY_SELECTOR_OPTIONS from generate_country_pages.py
(single source of truth for per-country data) rather than duplicating the
23-country dataset.
"""

import json
import os

from generate_country_pages import COUNTRIES, COUNTRY_SELECTOR_OPTIONS
from seo_meta import seo_meta_description

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PREFIX = 'best-betting-in-'
BONUS_PREFIX = 'best-bonus-in-'

YEAR = '2026'
MONTH_YEAR = 'June 2026'
DOMAIN = 'https://sifufinds.com'

# ── EMERGING MARKETS (added 2026-08-14) ─────────────────────────────────────
# Real, research-verified data for 5 new countries with genuine but thin
# bookmaker coverage (0-2 verified operators, vs 4-10+ for the established
# 22 countries above). No specific bonus percentages/amounts are claimed
# here since none were independently verified for these markets — the
# bookmaker cards themselves (rendered client-side from BOOKS[cty] in
# shared.js) carry whatever real, hedged copy exists per brand. Kept in
# sync by hand with COUNTRY_DATA in assets/shared.js (same pattern already
# used site-wide for the other 22 countries).
EMERGING_COUNTRIES = {
    'BJ': {
        'slug': 'benin', 'name': 'Benin', 'flag': '🇧🇯', 'currency': 'XOF', 'symbol': 'CFA',
        'regulator': 'Cellule de Supervision du Secteur des Jeux (CSJ) / Loterie Nationale du Bénin',
        'about': "Benin's online betting market has historically operated without dedicated licensing, but the Cellule de Supervision du Secteur des Jeux (CSJ), created in 2023, now actively supervises operators, and a 2025 finance law introduced a 25% tax on online gambling revenue.",
        'payments': ['MTN MoMo', 'Moov Money', 'Celtiis Cash', 'Bank Transfer'],
        'leagues': ['Benin Premier League', 'CAF Champions League', 'Premier League', 'AFCON'],
    },
    'BF': {
        'slug': 'burkina-faso', 'name': 'Burkina Faso', 'flag': '🇧🇫', 'currency': 'XOF', 'symbol': 'CFA',
        'regulator': 'Commission Nationale des Jeux de Hasard (CNJH) / LONAB',
        'about': "Burkina Faso's government ordered its telecoms regulator to block all online betting platforms not partnered with the state lottery LONAB from February 2025. Only LONAB's own platform and a small number of confirmed-compliant international partners operate legally — SifuFinds only lists operators with confirmed compliant status here.",
        'payments': ['Orange Money', 'Moov Money', 'Coris Money'],
        'leagues': ['Burkinabé Premier League', 'CAF Champions League', 'Premier League', 'AFCON'],
    },
    'GM': {
        'slug': 'gambia', 'name': 'Gambia', 'flag': '🇬🇲', 'currency': 'GMD', 'symbol': 'D',
        'regulator': 'Gambia Gaming Board (GGB)',
        'about': "The Gambia's online betting market operates without a functioning licensing regime — it is neither explicitly banned nor formally regulated, and the nominal regulator has limited practical oversight of online operators.",
        'payments': ['QMoney', 'AfriMoney (Africell Money)', 'Bank Transfer'],
        'leagues': ['GFF League First Division', 'CAF Champions League', 'Premier League', 'AFCON'],
    },
    'TG': {
        'slug': 'togo', 'name': 'Togo', 'flag': '🇹🇬', 'currency': 'XOF', 'symbol': 'CFA',
        'regulator': 'LONATO (Loterie Nationale Togolaise)',
        'about': "Togo's land-based gambling market is regulated by LONATO, but online betting currently has no dedicated licensing framework. SifuFinds has not yet independently verified a licensed online bookmaker operating in Togo.",
        'payments': ['Flooz (Moov)', 'T-Money (Togocom)', 'Bank Transfer'],
        'leagues': ['Togolese Championnat National', 'CAF Champions League', 'Premier League', 'AFCON'],
    },
    'CG': {
        'slug': 'congo-brazzaville', 'name': 'Congo-Brazzaville', 'flag': '🇨🇬', 'currency': 'XAF', 'symbol': 'CFA',
        'regulator': "Autorité de Régulation des Jeux de Hasard et d'Argent (ARJHA)",
        'about': "The Republic of the Congo (Congo-Brazzaville) introduced a formal licensing regime for sports betting, including online, under a 2024 law, with the regulator ARJHA created in 2025. Note: this market uses the Central African CFA franc (XAF), distinct from West African CFA (XOF) and from DR Congo's currency.",
        'payments': ['MTN MoMo', 'Airtel Money', 'Bank Transfer'],
        'leagues': ['Congo Ligue 1', 'CAF Champions League', 'Premier League', 'AFCON'],
    },
}

# ── LEGALLY RESTRICTED MARKETS (added 2026-08-14) ───────────────────────────
# Informational-only, no bookmaker listings and no affiliate links — see
# CLAUDE.md 2026-08-14 entry for the research and the explicit decision
# behind this. Do not add bookmaker cards or CTAs for these countries.
RESTRICTED_COUNTRIES = {
    'DZ': {
        'slug': 'algeria', 'name': 'Algeria', 'flag': '🇩🇿', 'currency': 'DZD', 'symbol': 'DA',
        'regulator': 'None — online gambling has no licensing framework',
        'about': "Online sports betting and gambling are prohibited in Algeria under Law 18-05, with only the state lottery and horse-racing tote legally permitted (land-based only). A 2025 law also criminalised VPN use to access banned content, including gambling sites.",
        'payments': ['CIB (Carte Interbancaire)', 'Edahabia', 'Bank Transfer'],
        'leagues': ['Ligue Professionnelle 1', 'CAF Champions League', 'AFCON'],
    },
    'LY': {
        'slug': 'libya', 'name': 'Libya', 'flag': '🇱🇾', 'currency': 'LYD', 'symbol': 'LD',
        'regulator': 'None — no gambling regulator exists',
        'about': "Gambling is fully prohibited in Libya under the Penal Code and a 2022 cybercrime law that criminalises operating an online gambling site, carrying a minimum 2-year prison sentence.",
        'payments': ['LYPAY/ONEPAY interbank transfer', 'Aman Pay', 'Bank Transfer'],
        'leagues': ['Libyan Premier League', 'CAF Champions League', 'AFCON'],
    },
    'MR': {
        'slug': 'mauritania', 'name': 'Mauritania', 'flag': '🇲🇷', 'currency': 'MRU', 'symbol': 'UM',
        'regulator': 'None — no gambling regulator exists',
        'about': "Gambling is fully prohibited in Mauritania, with advertising or marketing of gambling products also explicitly banned.",
        'payments': ['Bankily', 'Masrvi'],
        'leagues': ['Mauritanian Premier League', 'CAF Champions League', 'AFCON'],
    },
    'SO': {
        'slug': 'somalia', 'name': 'Somalia', 'flag': '🇸🇴', 'currency': 'SOS', 'symbol': 'Sh',
        'regulator': 'None — enforcement runs through NAMLC/FRC (anti-money-laundering bodies), not a gambling regulator',
        'about': "Gambling is banned in Somalia. The Federal Government formalised this in 2023, and the National Anti-Money Laundering & Countering Terrorist Financing Commission explicitly named the operator 1xBet in a November 2023 order directing banks to freeze related accounts.",
        'payments': ['EVC Plus', 'Zaad', 'Sahal', 'eDahab'],
        'leagues': ['Somali First Division', 'Premier League', 'UEFA Champions League'],
    },
    'TN': {
        'slug': 'tunisia', 'name': 'Tunisia', 'flag': '🇹🇳', 'currency': 'TND', 'symbol': 'DT',
        'regulator': 'Ministry of Youth, Sports and Physical Education / Promosport (state monopoly)',
        'about': "Only the state-run Promosport pools product is legally licensed for sports predictions in Tunisia. All fixed-odds bookmakers, including international brands, are illegal for Tunisian residents to use, and a law reported in 2026 would criminalise promoting unlicensed platforms.",
        'payments': ['e-Dinar (La Poste Tunisienne)', 'Visa', 'Mastercard'],
        'leagues': ['Ligue Professionnelle 1', 'CAF Champions League', 'AFCON'],
    },
}


def make_faqs(c):
    name = c['name']
    regulator = c['regulator']
    top_book = c['top_bookmaker']
    top_bonus = c['top_bonus']
    min_dep = c['min_deposit']
    payments = c['payments']
    leagues = c['leagues']

    return [
        {
            'q': f'Is online betting legal in {name}?',
            'a': f'Yes. Sports betting is legal and regulated in {name}. The licensing authority is the {regulator}. All bookmakers listed on SifuFinds hold valid licences for the {name} market — we only list fully licensed operators.',
        },
        {
            'q': f'What payment methods can I use at {name} betting sites?',
            'a': f"The most popular deposit and withdrawal methods at {name} betting sites include {', '.join(payments[:3])}. Most licensed bookmakers process withdrawals within 24 hours to mobile money accounts.",
        },
        {
            'q': f'Which betting site has the highest bonus in {name}?',
            'a': f'{top_book} currently offers one of the highest welcome bonuses in {name} at {top_bonus}. SifuFinds compares all verified offers daily — use the Highest Bonus sort to see the current leader.',
        },
        {
            'q': f'What is the minimum deposit at {name} betting sites?',
            'a': f'Minimum deposits at {name} betting sites start from {min_dep} at some bookmakers. Mobile money platforms typically have very low minimums to keep betting accessible.',
        },
        {
            'q': f'What sports and leagues can I bet on in {name}?',
            'a': f"The most popular betting markets in {name} include {', '.join(leagues[:3])}. Football is the dominant sport, with both local leagues and international competitions attracting high betting volumes.",
        },
    ]


def faq_schema_json(faqs):
    items = []
    for f in faqs:
        items.append(json.dumps({
            "@type": "Question",
            "name": f['q'],
            "acceptedAnswer": {"@type": "Answer", "text": f['a']},
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
    about = c['about']
    regulator = c['regulator']
    payments = c['payments']
    leagues = c['leagues']
    top_bonus = c['top_bonus']
    top_bookmaker = c['top_bookmaker']
    books_count = c['books_count']
    key_payment = payments[0]

    faqs = make_faqs(c)
    faq_schema = faq_schema_json(faqs)
    faq_block = faq_html(faqs)

    pay_chips = ' '.join(f'<span class="pay-chip">{p}</span>' for p in payments)
    league_items = '\n'.join(f'      <li>{lg}</li>' for lg in leagues)

    pay_str = ', '.join(payments[:2])
    meta_desc = (
        f'Compare the {books_count} best licensed betting sites in {name} {YEAR}. '
        f'Verified bonuses, {pay_str} payments and expert bookmaker reviews. Updated daily.'
    )
    title = f'Best Betting Sites in {name} {YEAR} | SifuFinds'
    canonical = f'{DOMAIN}/{OUT_PREFIX}{slug}/'
    h1 = f'Best Betting Sites in {name} &middot; {MONTH_YEAR}'

    return f"""<!DOCTYPE html>
<!-- sifufinds.com/{OUT_PREFIX}{slug}/ – Best Betting Sites in {name} {YEAR} -->
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{seo_meta_description(meta_desc)}">
<meta name="keywords" content="betting sites {name.lower()}, best bookmakers {name.lower()}, {name.lower()} betting bonuses {YEAR}, online betting {name.lower()}, {key_payment.lower()} betting">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="author" content="SifuFinds">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="en" href="{canonical}">
<link rel="alternate" hreflang="en-{code}" href="{canonical}">

<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{DOMAIN}/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Best Betting Sites in {name} — SifuFinds">
<meta property="og:locale" content="en_GB">
<meta property="og:locale:alternate" content="en_{code}">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@sifufinds">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{meta_desc}">
<meta name="twitter:image" content="{DOMAIN}/assets/og-image.png">

<!-- Geo -->
<meta name="geo.region" content="{code}">
<meta name="geo.placename" content="{name}">
<meta name="language" content="English">
<meta name="coverage" content="Africa">

<!-- Structured Data -->
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
        {{"@type": "ListItem", "position": 2, "name": "Countries", "item": "{DOMAIN}/countries/"}},
        {{"@type": "ListItem", "position": 3, "name": {json.dumps(name + " Betting Sites")}, "item": "{canonical}"}}
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
<link rel="preload" href="../assets/shared.css?v=12" as="style">
<link rel="stylesheet" href="../assets/shared.css?v=12">
<style>
.reg-badge{{display:inline-block;background:#edf7f0;border:1px solid #c8e6c9;border-radius:6px;padding:5px 12px;font-size:12px;font-weight:700;color:#1a6b35;margin-bottom:10px}}
.pay-grid{{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}}
.pay-chip{{background:#f5f5f5;border:1px solid #e0e0e0;border-radius:5px;padding:4px 10px;font-size:12px;font-weight:500;color:#333}}
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
.bonus-cta{{display:flex;align-items:center;gap:10px;background:#fff8e1;border:1px solid #ffe082;border-radius:10px;padding:12px 16px;margin-bottom:16px;font-size:13px;color:#333}}
.bonus-cta a{{color:#8a6100;font-weight:700;text-decoration:none}}
.bonus-cta a:hover{{text-decoration:underline}}
</style>
</head>
<body>

<!-- TOP BAR -->
<div class="tbar">
  <div class="tbar-l">
    <a href="../">🏠 Home</a>
    <a href="../countries/">🌍 Africa</a>
    <a href="../responsible/">Responsible Gambling</a>
    <button onclick="openPage('about')">18+ Only</button>
  </div>
  <div class="tbar-r">
    <span class="csel-lbl">Your Country:</span>
    <select class="csel" id="ctySel" onchange="changeCountry(this.value)">
{COUNTRY_SELECTOR_OPTIONS}
    </select>
  </div>
</div>

<!-- MAIN NAV -->
<nav class="mnav">
  <div class="mnav-in">
    <a class="logo" href="../">
      <img src="../assets/icon.png" width="38" height="38" alt="SifuFinds logo" style="display:block;object-fit:contain">
      SifuFinds
    </a>
    <div class="ntabs">
      <a class="nt" href="../">⭐ Best Bonuses</a>
      <a class="nt" href="../tips/">💡 Tips</a>
      <a class="nt" href="../casino/">🎰 Casino</a>
      <a class="nt" href="../odds/">📊 Live Odds<span class="lpulse" style="margin-left:4px"></span></a>
      <a class="nt" href="../leagues/">⚽ Leagues</a>
      <a class="nt on" href="../countries/">🌍 Countries</a>
      <a class="nt" href="../blog/">📰 Blog</a>
      <a class="nt" href="../contact/">✉️ Contact</a>
    </div>
    <div class="srch-wrap">
      <input class="srch-inp" id="srch-inp" type="text" placeholder="Search bookmakers..." autocomplete="off" aria-label="Search bookmakers">
    </div>
  </div>
</nav>

<!-- HEADER BRANDS BAR -->
<div id="hbrands" class="hbrands"></div>

<!-- HERO -->
<div class="hero"><div class="wrap">
  <h1>{h1}</h1>
  <p>{name} is home to {books_count} licensed betting sites, led by {top_bookmaker} with a {top_bonus} welcome offer. SifuFinds tracks odds coverage, payment methods, cash out and mobile apps across every licensed bookmaker in {name} — verified and updated daily. {about}</p>
  <div class="ctrs">
    <div class="ctr"><div class="ctr-n">{top_bonus}</div><div class="ctr-l">largest welcome bonus</div></div>
    <div class="ctr"><div class="ctr-n">{books_count}</div><div class="ctr-l">licensed bookmakers</div></div>
    <div class="ctr"><div class="ctr-n" id="today-d"></div><div class="ctr-l">last updated</div></div>
  </div>
  <div class="trust">
    <div class="tb">✅ Licensed &amp; Verified</div>
    <div class="tb">📱 Mobile-First</div>
    <div class="tb">🔄 Updated Daily</div>
    <div class="tb">💳 {key_payment}</div>
  </div>
</div></div>

<!-- FEATURED -->
<div class="feat-bar"><div class="wrap">
  <div class="feat-lbl">⭐ Top Picks · {name}</div>
  <div class="feat-grid" id="feat-cards"></div>
</div></div>

<!-- MAIN CONTENT -->
<div class="sec-bg"><div class="wrap">
  <div class="breadcrumb">
    <a href="../">Home</a><span>›</span><a href="../countries/">Countries</a><span>›</span>{name} Betting Sites
  </div>

  <div class="adv">📢 <strong>Advertiser Disclosure:</strong> We may earn commission from bookmaker links. All bonuses independently verified. Always check the bookmaker's official site for current T&amp;Cs.</div>

  <div class="bonus-cta">🎁 Looking for the biggest welcome offer? See our <a href="../{BONUS_PREFIX}{slug}/">Best Bonus Sites in {name}</a> guide, ranked by bonus size.</div>

  <!-- Legality & Regulation -->
  <div class="cbox2">
    <h2>Is Online Betting Legal in {name}?</h2>
    <div class="reg-badge">✅ Regulated Market — {YEAR}</div>
    <p>Yes. Sports betting is <strong>legal and regulated</strong> in {name}. The licensing authority is the <strong>{regulator}</strong>. All bookmakers listed on SifuFinds hold valid licences for the {name} market — we do not list unlicensed operators.</p>
    <p>Always verify a bookmaker's licence before depositing. The {regulator} maintains a register of approved operators.</p>
  </div>

  <!-- Bookmaker listings -->
  <div class="sec-lbl">LICENSED BOOKMAKERS · {name.upper()} · {YEAR}</div>
  <h2 style="font-size:17px;font-weight:800;color:#111;margin-bottom:9px">{books_count} Best Betting Sites in {name} — Verified {YEAR}</h2>

  <div class="fbar"><div class="fr">
    <span class="fr-label">Sort:</span>
    <select class="fsel" id="srt" onchange="renderBooks()">
      <option value="default">Editors' Picks</option>
      <option value="stars">Highest Rated</option>
      <option value="bonus">Highest Bonus</option>
      <option value="sports">Most Sports</option>
    </select>
    <span class="fr-label" style="margin-left:4px">Filter:</span>
    <button class="fp on" data-f="all" onclick="setFilt(this)">All</button>
    <button class="fp" data-f="nodep" onclick="setFilt(this)">No Deposit</button>
    <button class="fp" data-f="cashout" onclick="setFilt(this)">Cash Out</button>
    <button class="fp" data-f="instant" onclick="setFilt(this)">Instant Pay</button>
  </div></div>

  <div class="mc" id="mcount"></div>
  <div id="bk-cards">
    <noscript><p style="padding:20px;color:#666">Enable JavaScript to view bookmaker listings, or visit <a href="../">SifuFinds.com</a>.</p></noscript>
  </div>

  <!-- Payment Methods -->
  <div class="cbox2">
    <h2>How to Deposit at {name} Betting Sites</h2>
    <p>These payment methods are accepted at licensed {name} betting sites in {YEAR}:</p>
    <div class="pay-grid">{pay_chips}</div>
    <p style="margin-top:12px">Most bookmakers process <strong>withdrawals within 24 hours</strong> to mobile money accounts. Bank transfers may take 1–3 business days.</p>
  </div>

  <!-- Popular Leagues -->
  <div class="cbox2">
    <h2>Most Popular Sports &amp; Leagues to Bet on in {name}</h2>
    <ul style="padding-left:18px;margin:0">
{league_items}
    </ul>
    <p style="margin-top:10px">Football is the dominant sport for betting in {name}. International competitions like the CAF Champions League and AFCON attract very high betting volumes.</p>
  </div>

  <!-- FAQ -->
  <div class="cbox2">
    <h2>Frequently Asked Questions — Betting in {name}</h2>
{faq_block}
  </div>

  <div class="resp">⚠️ Gambling involves risk. Only bet what you can afford to lose.
    <a href="../responsible/">GamCare</a> ·
    <a href="../responsible/">BeGambleAware</a> ·
    <a href="../responsible/">NCPG Africa</a>. 18+ only.
  </div>
</div></div>

<!-- FOOTER -->
<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison · <span id="foot-date"></span><br>
  <a href="../">Home</a> · <a href="../{BONUS_PREFIX}{slug}/">{name} Bonuses</a> · <a href="../countries/">All Countries</a> · <a href="../tips/">Tips</a> · <a href="../casino/">Casino</a> · <a href="../odds/">Odds</a> · <a href="../blog/">Blog</a> · <a href="../about/">About</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only. Gambling can be addictive. Play responsibly.
</div>

<!-- PAGE MODAL -->
<div class="page-modal-bg" id="page-modal">
  <div class="page-modal">
    <button class="page-modal-close" onclick="closePage()">×</button>
    <div class="pm" id="page-content"></div>
  </div>
</div>

<script src="../assets/shared.js?v=24"></script>
<script>
const SITE={{home:'../',tips:'../tips/',casino:'../casino/',odds:'../odds/',countries:'../countries/'
}};
const _PAGE_CTY='{code}';
let _activeFilt='all';

// Override — this page always shows the country's books regardless of localStorage
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
  if(f==='instant')return books.filter(b=>b.instant);
  return books;
}}

function sortBooks(books){{
  const s=document.getElementById('srt')?.value||'default';
  if(s==='stars')return[...books].sort((a,b)=>b.stars-a.stars);
  if(s==='sports')return[...books].sort((a,b)=>b.sports-a.sports);
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
  H('mcount',`Showing ${{books.length}} betting site${{books.length!==1?'s':''}}`);
}}

function renderFeatCards(){{
  const books=(BOOKS[_PAGE_CTY]||[]).slice(0,12);
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


def make_faqs_emerging(c):
    name = c['name']
    regulator = c['regulator']
    payments = c['payments']
    leagues = c['leagues']
    return [
        {
            'q': f'Is online betting legal in {name}?',
            'a': f"{c['about']} The regulator/licensing authority referenced for {name} is the {regulator}.",
        },
        {
            'q': f'What payment methods can I use for betting in {name}?',
            'a': f"The main payment channels used in {name} are {', '.join(payments[:3])}. Availability varies by operator — always confirm on the bookmaker's own site before depositing.",
        },
        {
            'q': f'Which bookmakers does SifuFinds list for {name}?',
            'a': f"SifuFinds only lists operators for {name} that we could independently verify are actually targeting or licensed for this market. We do not pad this list with unverified brands, so it may be shorter than for larger, more established markets — we update it as new verified information becomes available.",
        },
        {
            'q': f'What is the most popular sport to bet on in {name}?',
            'a': f"Football is the dominant sport in {name}. The most followed competitions are {', '.join(leagues[:3])}.",
        },
    ]


def generate_emerging_page(code, c):
    name = c['name']
    slug = c['slug']
    about = c['about']
    regulator = c['regulator']
    payments = c['payments']
    leagues = c['leagues']
    key_payment = payments[0]

    faqs = make_faqs_emerging(c)
    faq_schema = faq_schema_json(faqs)
    faq_block = faq_html(faqs)

    pay_chips = ' '.join(f'<span class="pay-chip">{p}</span>' for p in payments)
    league_items = '\n'.join(f'      <li>{lg}</li>' for lg in leagues)

    meta_desc = (
        f'Betting sites in {name} {YEAR}: legal status, regulator, payment methods and '
        f'verified bookmakers. Independently researched, updated as new information becomes available.'
    )
    title = f'Betting Sites in {name} {YEAR} | SifuFinds'
    canonical = f'{DOMAIN}/{OUT_PREFIX}{slug}/'
    h1 = f'Betting Sites in {name} &middot; {MONTH_YEAR}'

    return f"""<!DOCTYPE html>
<!-- sifufinds.com/{OUT_PREFIX}{slug}/ – Betting Sites in {name} {YEAR} (emerging market coverage) -->
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{seo_meta_description(meta_desc)}">
<meta name="keywords" content="betting sites {name.lower()}, online betting {name.lower()}, {key_payment.lower()} betting, is betting legal in {name.lower()}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="author" content="SifuFinds">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="en" href="{canonical}">
<link rel="alternate" hreflang="en-{code}" href="{canonical}">

<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{DOMAIN}/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Betting Sites in {name} — SifuFinds">
<meta property="og:locale" content="en_GB">
<meta property="og:locale:alternate" content="en_{code}">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@sifufinds">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{meta_desc}">
<meta name="twitter:image" content="{DOMAIN}/assets/og-image.png">

<!-- Geo -->
<meta name="geo.region" content="{code}">
<meta name="geo.placename" content="{name}">
<meta name="language" content="English">
<meta name="coverage" content="Africa">

<!-- Structured Data -->
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
        {{"@type": "ListItem", "position": 2, "name": "Countries", "item": "{DOMAIN}/countries/"}},
        {{"@type": "ListItem", "position": 3, "name": {json.dumps(name + " Betting Sites")}, "item": "{canonical}"}}
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
<link rel="preload" href="../assets/shared.css?v=12" as="style">
<link rel="stylesheet" href="../assets/shared.css?v=12">
<style>
.reg-badge{{display:inline-block;background:#fff3e0;border:1px solid #ffcc80;border-radius:6px;padding:5px 12px;font-size:12px;font-weight:700;color:#8a5600;margin-bottom:10px}}
.pay-grid{{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}}
.pay-chip{{background:#f5f5f5;border:1px solid #e0e0e0;border-radius:5px;padding:4px 10px;font-size:12px;font-weight:500;color:#333}}
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

<!-- TOP BAR -->
<div class="tbar">
  <div class="tbar-l">
    <a href="../">🏠 Home</a>
    <a href="../countries/">🌍 Africa</a>
    <a href="../responsible/">Responsible Gambling</a>
    <button onclick="openPage('about')">18+ Only</button>
  </div>
  <div class="tbar-r">
    <span class="csel-lbl">Your Country:</span>
    <select class="csel" id="ctySel" onchange="changeCountry(this.value)">
{COUNTRY_SELECTOR_OPTIONS}
    </select>
  </div>
</div>

<!-- MAIN NAV -->
<nav class="mnav">
  <div class="mnav-in">
    <a class="logo" href="../">
      <img src="../assets/icon.png" width="38" height="38" alt="SifuFinds logo" style="display:block;object-fit:contain">
      SifuFinds
    </a>
    <div class="ntabs">
      <a class="nt" href="../">⭐ Best Bonuses</a>
      <a class="nt" href="../tips/">💡 Tips</a>
      <a class="nt" href="../casino/">🎰 Casino</a>
      <a class="nt" href="../odds/">📊 Live Odds<span class="lpulse" style="margin-left:4px"></span></a>
      <a class="nt" href="../leagues/">⚽ Leagues</a>
      <a class="nt on" href="../countries/">🌍 Countries</a>
      <a class="nt" href="../blog/">📰 Blog</a>
      <a class="nt" href="../contact/">✉️ Contact</a>
    </div>
    <div class="srch-wrap">
      <input class="srch-inp" id="srch-inp" type="text" placeholder="Search bookmakers..." autocomplete="off" aria-label="Search bookmakers">
    </div>
  </div>
</nav>

<!-- HEADER BRANDS BAR -->
<div id="hbrands" class="hbrands"></div>

<!-- HERO -->
<div class="hero"><div class="wrap">
  <h1>{h1}</h1>
  <p>{about}</p>
  <div class="trust">
    <div class="tb">🔎 Independently Researched</div>
    <div class="tb">🔄 Updated As Verified</div>
    <div class="tb">💳 {key_payment}</div>
  </div>
</div></div>

<!-- MAIN CONTENT -->
<div class="sec-bg"><div class="wrap">
  <div class="breadcrumb">
    <a href="../">Home</a><span>›</span><a href="../countries/">Countries</a><span>›</span>{name} Betting Sites
  </div>

  <div class="adv">📢 <strong>Advertiser Disclosure:</strong> Where we list a bookmaker with a partner link, we may earn commission. All information here is independently researched, not paid placement. Always check the bookmaker's official site for current terms.</div>

  <!-- Legality & Regulation -->
  <div class="cbox2">
    <h2>Is Online Betting Legal in {name}?</h2>
    <div class="reg-badge">🔎 Emerging / Evolving Market — {YEAR}</div>
    <p>{about}</p>
    <p>Regulatory landscape referenced: <strong>{regulator}</strong>. Always verify current local law before betting.</p>
  </div>

  <!-- Bookmaker listings -->
  <div class="sec-lbl">VERIFIED BOOKMAKERS · {name.upper()} · {YEAR}</div>
  <h2 style="font-size:17px;font-weight:800;color:#111;margin-bottom:9px">Betting Sites in {name} — Verified {YEAR}</h2>

  <div class="mc" id="mcount"></div>
  <div id="bk-cards">
    <noscript><p style="padding:20px;color:#666">Enable JavaScript to view bookmaker listings, or visit <a href="../">SifuFinds.com</a>.</p></noscript>
  </div>

  <!-- Payment Methods -->
  <div class="cbox2">
    <h2>Payment Methods Used in {name}</h2>
    <p>These are the payment channels commonly used for online transactions in {name} in {YEAR}:</p>
    <div class="pay-grid">{pay_chips}</div>
  </div>

  <!-- Popular Leagues -->
  <div class="cbox2">
    <h2>Most Popular Sports &amp; Leagues in {name}</h2>
    <ul style="padding-left:18px;margin:0">
{league_items}
    </ul>
    <p style="margin-top:10px">Football is the dominant sport in {name}. International competitions like the CAF Champions League and AFCON attract the most interest.</p>
  </div>

  <!-- FAQ -->
  <div class="cbox2">
    <h2>Frequently Asked Questions — Betting in {name}</h2>
{faq_block}
  </div>

  <div class="resp">⚠️ Gambling involves risk. Only bet what you can afford to lose, and only where it is legal to do so.
    <a href="../responsible/">GamCare</a> ·
    <a href="../responsible/">BeGambleAware</a> ·
    <a href="../responsible/">NCPG Africa</a>. 18+ only.
  </div>
</div></div>

<!-- FOOTER -->
<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison · <span id="foot-date"></span><br>
  <a href="../">Home</a> · <a href="../countries/">All Countries</a> · <a href="../tips/">Tips</a> · <a href="../casino/">Casino</a> · <a href="../odds/">Odds</a> · <a href="../blog/">Blog</a> · <a href="../about/">About</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only. Gambling can be addictive. Play responsibly.
</div>

<!-- PAGE MODAL -->
<div class="page-modal-bg" id="page-modal">
  <div class="page-modal">
    <button class="page-modal-close" onclick="closePage()">×</button>
    <div class="pm" id="page-content"></div>
  </div>
</div>

<script src="../assets/shared.js?v=23"></script>
<script>
const SITE={{home:'../',tips:'../tips/',casino:'../casino/',odds:'../odds/',countries:'../countries/'
}};
const _PAGE_CTY='{code}';

function getCurrentCountry(){{return _PAGE_CTY;}}

const bookCard=(b,i,rank)=>{{
  const badge=b.badge==='new'?'<span class="badge-new">NEW</span>':b.badge==='hot'?'<span class="badge-hot">HOT</span>':b.nodep?'<span class="badge-nd">NO DEP</span>':'';
  return`<div class="bkcard ${{rank<3?'top3':''}}">
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
      <a class="gbtn" href="${{b.url}}" target="_blank" rel="noopener noreferrer sponsored">Visit Site →</a>
      <div class="tc-n">T&amp;Cs Apply · 18+</div>
    </div>
  </div>
  <div class="pm-row">${{(b.pms||[]).map(pm).join('')}}</div>
  <div class="xdet" style="display:block">
    <div class="trms">${{b.terms}}</div>
  </div>
</div>`;
}};

function renderBooks(){{
  const books=BOOKS[_PAGE_CTY]||[];
  const el=document.getElementById('bk-cards');
  if(!books.length){{el.innerHTML='<div class="no-results">We have not yet independently verified a licensed bookmaker operating in {name}. Check back as our research continues.</div>';return;}}
  el.innerHTML=books.map((b,i)=>bookCard(b,i,i)).join('');
  H('mcount',`Showing ${{books.length}} verified betting site${{books.length!==1?'s':''}}`);
}}

function init(){{
  const sel=document.getElementById('ctySel');
  if(sel)sel.value=_PAGE_CTY;
  H('today-d',SHORT_DATE);
  H('foot-date',DATE_STR);
  H('foot-yr',NOW.getFullYear());
  renderBooks();
}}
init();
</script>
</body>
</html>"""


def make_faqs_restricted(c):
    name = c['name']
    regulator = c['regulator']
    return [
        {
            'q': f'Is online betting legal in {name}?',
            'a': c['about'],
        },
        {
            'q': f'Does {name} have a gambling regulator?',
            'a': f"{regulator}." if regulator.lower().startswith('none') else f"The relevant authority is the {regulator}.",
        },
        {
            'q': f'Does SifuFinds list or recommend any bookmaker for {name}?',
            'a': f"No. SifuFinds does not list, promote, or link to any betting operator for {name}. This page is provided for informational purposes only, so readers can understand the legal situation in their own country.",
        },
        {
            'q': f'What is the most popular sport in {name}?',
            'a': f"Football is the most popular sport in {name}.",
        },
    ]


def generate_restricted_page(code, c):
    name = c['name']
    slug = c['slug']
    about = c['about']
    regulator = c['regulator']
    payments = c['payments']
    leagues = c['leagues']

    faqs = make_faqs_restricted(c)
    faq_schema = faq_schema_json(faqs)
    faq_block = faq_html(faqs)

    pay_chips = ' '.join(f'<span class="pay-chip">{p}</span>' for p in payments)
    league_items = '\n'.join(f'      <li>{lg}</li>' for lg in leagues)

    meta_desc = seo_meta_description(
        f'Is online sports betting legal in {name}? {YEAR} legal status, regulation and what SifuFinds does '
        f'and does not list for this market. Independently researched.'
    )
    title = f'Is Online Betting Legal in {name}? — {YEAR} | SifuFinds'
    canonical = f'{DOMAIN}/{OUT_PREFIX}{slug}/'
    h1 = f'Is Online Betting Legal in {name}?'

    return f"""<!DOCTYPE html>
<!-- sifufinds.com/{OUT_PREFIX}{slug}/ – Is Online Betting Legal in {name}? (informational only, no bookmaker listings) -->
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{meta_desc}">
<meta name="keywords" content="is betting legal in {name.lower()}, {name.lower()} gambling laws, online betting {name.lower()}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="author" content="SifuFinds">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="en" href="{canonical}">
<link rel="alternate" hreflang="en-{code}" href="{canonical}">

<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{DOMAIN}/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{name} Gambling Laws — SifuFinds">
<meta property="og:locale" content="en_GB">
<meta property="og:locale:alternate" content="en_{code}">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@sifufinds">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{meta_desc}">
<meta name="twitter:image" content="{DOMAIN}/assets/og-image.png">

<!-- Geo -->
<meta name="geo.region" content="{code}">
<meta name="geo.placename" content="{name}">
<meta name="language" content="English">
<meta name="coverage" content="Africa">

<!-- Structured Data -->
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
        {{"@type": "ListItem", "position": 2, "name": "Countries", "item": "{DOMAIN}/countries/"}},
        {{"@type": "ListItem", "position": 3, "name": {json.dumps(name + " Gambling Laws")}, "item": "{canonical}"}}
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
<link rel="preload" href="../assets/shared.css?v=12" as="style">
<link rel="stylesheet" href="../assets/shared.css?v=12">
<style>
.reg-badge{{display:inline-block;background:#fdecea;border:1px solid #f5b7b1;border-radius:6px;padding:5px 12px;font-size:12px;font-weight:700;color:#a12a1f;margin-bottom:10px}}
.pay-grid{{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}}
.pay-chip{{background:#f5f5f5;border:1px solid #e0e0e0;border-radius:5px;padding:4px 10px;font-size:12px;font-weight:500;color:#333}}
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
.notice-box{{background:#fdecea;border:1px solid #f5b7b1;border-radius:10px;padding:14px 16px;margin-bottom:16px;font-size:13px;color:#7a1f16;line-height:1.6}}
</style>
</head>
<body>

<!-- TOP BAR -->
<div class="tbar">
  <div class="tbar-l">
    <a href="../">🏠 Home</a>
    <a href="../countries/">🌍 Africa</a>
    <a href="../responsible/">Responsible Gambling</a>
    <button onclick="openPage('about')">18+ Only</button>
  </div>
</div>

<!-- MAIN NAV -->
<nav class="mnav">
  <div class="mnav-in">
    <a class="logo" href="../">
      <img src="../assets/icon.png" width="38" height="38" alt="SifuFinds logo" style="display:block;object-fit:contain">
      SifuFinds
    </a>
    <div class="ntabs">
      <a class="nt" href="../">⭐ Best Bonuses</a>
      <a class="nt" href="../tips/">💡 Tips</a>
      <a class="nt" href="../casino/">🎰 Casino</a>
      <a class="nt" href="../odds/">📊 Live Odds<span class="lpulse" style="margin-left:4px"></span></a>
      <a class="nt" href="../leagues/">⚽ Leagues</a>
      <a class="nt on" href="../countries/">🌍 Countries</a>
      <a class="nt" href="../blog/">📰 Blog</a>
      <a class="nt" href="../contact/">✉️ Contact</a>
    </div>
  </div>
</nav>

<!-- HERO -->
<div class="hero"><div class="wrap">
  <h1>{h1}</h1>
  <p>{about}</p>
  <div class="trust">
    <div class="tb">⚖️ Legal Status: Restricted</div>
    <div class="tb">🔎 Independently Researched</div>
    <div class="tb">🚫 No Bookmakers Listed</div>
  </div>
</div></div>

<!-- MAIN CONTENT -->
<div class="sec-bg"><div class="wrap">
  <div class="breadcrumb">
    <a href="../">Home</a><span>›</span><a href="../countries/">Countries</a><span>›</span>{name} Gambling Laws
  </div>

  <div class="notice-box">⚖️ <strong>No bookmaker listings for {name}.</strong> Based on our research, online sports betting is restricted or prohibited in {name}. SifuFinds does not list, promote, or link to any betting operator for this market. This page is informational only.</div>

  <!-- Legality & Regulation -->
  <div class="cbox2">
    <h2>Is Online Betting Legal in {name}?</h2>
    <div class="reg-badge">🚫 Restricted Market — {YEAR}</div>
    <p>{about}</p>
    <p>Regulatory situation: <strong>{regulator}</strong>.</p>
  </div>

  <!-- Payment Methods (informational only) -->
  <div class="cbox2">
    <h2>Common Online Payment Methods in {name}</h2>
    <p>For general informational context, these are common online payment channels used in {name} (not a betting endorsement):</p>
    <div class="pay-grid">{pay_chips}</div>
  </div>

  <!-- Popular Leagues -->
  <div class="cbox2">
    <h2>Most Popular Sports in {name}</h2>
    <ul style="padding-left:18px;margin:0">
{league_items}
    </ul>
    <p style="margin-top:10px">Football is the dominant sport in {name}.</p>
  </div>

  <!-- FAQ -->
  <div class="cbox2">
    <h2>Frequently Asked Questions — Betting Laws in {name}</h2>
{faq_block}
  </div>

  <div class="resp">⚠️ Gambling involves risk. Follow the laws of your own country.
    <a href="../responsible/">GamCare</a> ·
    <a href="../responsible/">BeGambleAware</a> ·
    <a href="../responsible/">NCPG Africa</a>. 18+ only.
  </div>
</div></div>

<!-- FOOTER -->
<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison · <span id="foot-date"></span><br>
  <a href="../">Home</a> · <a href="../countries/">All Countries</a> · <a href="../tips/">Tips</a> · <a href="../casino/">Casino</a> · <a href="../odds/">Odds</a> · <a href="../blog/">Blog</a> · <a href="../about/">About</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only. Gambling can be addictive. Play responsibly.
</div>

<script src="../assets/shared.js?v=23"></script>
<script>
const SITE={{home:'../',tips:'../tips/',casino:'../casino/',odds:'../odds/',countries:'../countries/'
}};
function init(){{
  H('foot-date',DATE_STR);
  H('foot-yr',NOW.getFullYear());
}}
init();
</script>
</body>
</html>"""


if __name__ == '__main__':
    created = 0
    for code, country in COUNTRIES.items():
        slug = country['slug']
        out_dir = os.path.join(BASE_DIR, f'{OUT_PREFIX}{slug}')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'index.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(generate_page(code, country))
        print(f'  ✓  /{OUT_PREFIX}{slug}/')
        created += 1

    for code, country in EMERGING_COUNTRIES.items():
        slug = country['slug']
        out_dir = os.path.join(BASE_DIR, f'{OUT_PREFIX}{slug}')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'index.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(generate_emerging_page(code, country))
        print(f'  ✓  /{OUT_PREFIX}{slug}/ (emerging market)')
        created += 1

    for code, country in RESTRICTED_COUNTRIES.items():
        slug = country['slug']
        out_dir = os.path.join(BASE_DIR, f'{OUT_PREFIX}{slug}')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'index.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(generate_restricted_page(code, country))
        print(f'  ✓  /{OUT_PREFIX}{slug}/ (restricted market, informational only)')
        created += 1

    print(f'\n✅ Generated {created} best-betting-in-<country> pages')
