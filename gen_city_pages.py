#!/usr/bin/env python3
"""Generate city-level betting pages for Lagos, Nairobi, Johannesburg, Accra, Cape Town."""

import json
import os
from seo_meta import seo_meta_description

BASE = os.path.dirname(os.path.abspath(__file__))


def seo_title(title: str, max_len: int = 60) -> str:
    """Return a ≤ max_len char <title> string with '| SifuFinds' suffix."""
    suffix = "| SifuFinds"
    full = f"{title} {suffix}"
    if len(full) <= max_len:
        return full
    for sep in [" — ", " - ", ": ", " | "]:
        idx = title.find(sep)
        if idx > 10:
            candidate = f"{title[:idx]} {suffix}"
            if len(candidate) <= max_len:
                return candidate
    available = max_len - len(suffix) - 2
    truncated = title[:available].rsplit(" ", 1)[0]
    return f"{truncated}… {suffix}"

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

CITIES = [
    {
        'path': 'countries/nigeria/lagos',
        'slug': 'lagos',
        'city': 'Lagos',
        'country': 'Nigeria',
        'country_code': 'NG',
        'country_slug': 'nigeria',
        'flag': '🇳🇬',
        'currency': 'NGN',
        'symbol': '₦',
        'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'population': "Africa's largest city with 20+ million people",
        'about': "Lagos is Nigeria's commercial capital and home to millions of passionate football bettors. As Africa's largest city, Lagos has the highest concentration of registered bettors in Nigeria. All major NLRC-licensed bookmakers have a strong presence in Lagos with hundreds of retail shops and a thriving mobile betting market via OPay and PalmPay.",
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa', 'Mastercard'],
        'popular_leagues': ['NPFL Lagos teams (Enyimba, Rangers)', 'Premier League', 'CAF Champions League', 'AFCON'],
        'assets_prefix': '../../../',
        'country_prefix': '../../',
        'depth': 3,
    },
    {
        'path': 'countries/kenya/nairobi',
        'slug': 'nairobi',
        'city': 'Nairobi',
        'country': 'Kenya',
        'country_code': 'KE',
        'country_slug': 'kenya',
        'flag': '🇰🇪',
        'currency': 'KES',
        'symbol': 'KSh',
        'regulator': 'BCLB (Betting Control and Licensing Board)',
        'population': "Kenya's capital city with 5+ million people",
        'about': "Nairobi is Kenya's capital and the beating heart of East African sports betting. The city is home to Sportpesa's headquarters, Betika's main offices, and millions of M-Pesa-connected bettors. Nairobi bettors can deposit via *644# on any Safaricom line with no internet required.",
        'payments': ['M-Pesa', 'Airtel Money', 'Equitel', 'USSD *644#'],
        'popular_leagues': ['Kenya Premier League (Gor Mahia, AFC Leopards)', 'Premier League', 'CAF Champions League', 'AFCON'],
        'assets_prefix': '../../../',
        'country_prefix': '../../',
        'depth': 3,
    },
    {
        'path': 'countries/south-africa/johannesburg',
        'slug': 'johannesburg',
        'city': 'Johannesburg',
        'country': 'South Africa',
        'country_code': 'ZA',
        'country_slug': 'south-africa',
        'flag': '🇿🇦',
        'currency': 'ZAR',
        'symbol': 'R',
        'regulator': 'Gauteng Gambling Board (GGB) / NGB',
        'population': "South Africa's largest city with 6+ million people",
        'about': "Johannesburg (Joburg/Jozi) is South Africa's financial capital and home to the Gauteng Gambling Board (GGB). All major South African bookmakers — Hollywoodbets, Betway SA, Supabets — have retail branches and online operations serving Johannesburg bettors. FICA verification is required for all South African betting accounts.",
        'payments': ['FNB', 'Standard Bank', 'Nedbank', 'Capitec', 'Instant EFT', 'Visa'],
        'popular_leagues': ['DStv Premiership (Kaizer Chiefs, Orlando Pirates, Mamelodi Sundowns)', 'Premier League', 'CAF Champions League', 'Rugby'],
        'assets_prefix': '../../../',
        'country_prefix': '../../',
        'depth': 3,
    },
    {
        'path': 'countries/ghana/accra',
        'slug': 'accra',
        'city': 'Accra',
        'country': 'Ghana',
        'country_code': 'GH',
        'country_slug': 'ghana',
        'flag': '🇬🇭',
        'currency': 'GHS',
        'symbol': 'GH₵',
        'regulator': 'GCA (Gaming Commission of Ghana)',
        'population': "Ghana's capital and largest city with 3+ million people",
        'about': "Accra is Ghana's capital and the centre of Ghanaian sports betting. MTN MoMo and Vodafone Cash are the dominant payment methods. The GCA-licensed bookmakers have a strong presence in Accra with retail shops across the city and growing online/mobile platforms.",
        'payments': ['MTN MoMo', 'Vodafone Cash', 'AirtelTigo Money', 'Visa', 'Mastercard'],
        'popular_leagues': ['Ghana Premier League (Hearts of Oak, Asante Kotoko)', 'Premier League', 'CAF Champions League', 'AFCON'],
        'assets_prefix': '../../../',
        'country_prefix': '../../',
        'depth': 3,
    },
    {
        'path': 'countries/south-africa/cape-town',
        'slug': 'cape-town',
        'city': 'Cape Town',
        'country': 'South Africa',
        'country_code': 'ZA',
        'country_slug': 'south-africa',
        'flag': '🇿🇦',
        'currency': 'ZAR',
        'symbol': 'R',
        'regulator': 'WCGRB (Western Cape Gambling and Racing Board)',
        'population': "South Africa's legislative capital with 4+ million people",
        'about': "Cape Town is regulated by the Western Cape Gambling and Racing Board (WCGRB), the regulator that oversees Hollywoodbets' home province. The Western Cape has a mature betting market with strong rugby (Stormers), cricket (Western Province), and football (Cape Town City FC) interest.",
        'payments': ['FNB', 'Standard Bank', 'Nedbank', 'Capitec', 'Instant EFT', 'Visa'],
        'popular_leagues': ['DStv Premiership (Cape Town City)', 'Stormers Rugby', 'Western Province Cricket', 'Premier League'],
        'assets_prefix': '../../../',
        'country_prefix': '../../',
        'depth': 3,
    },
]


def make_city_page(c):
    pay_chips = ' '.join(f'<span class="pay-chip">{p}</span>' for p in c['payments'])
    league_items = '\n'.join(f'      <li>{lg}</li>' for lg in c['popular_leagues'])
    ap = c['assets_prefix']
    # 2026-08-09: country pages moved from countries/<slug>/ to best-bonus-in-<slug>/
    # (see generate_country_pages.py) — link straight to the new location rather
    # than through countries/<slug>/'s redirect stub. c['country_prefix'] (the old
    # relative-up-N-levels path) is intentionally unused here now.
    cp = f"{ap}best-bonus-in-{c['country_slug']}/"

    title = seo_title(f"Betting Sites in {c['city']}, {c['country']} 2026")
    meta_desc = f"Best licensed betting sites in {c['city']}, {c['country']} 2026. Compare verified bonuses from {c['regulator']} regulated bookmakers. {', '.join(c['payments'][:2])} accepted. Updated daily."
    canonical = f"https://sifufinds.com/countries/{c['country_slug']}/{c['slug']}/"
    h1 = f"Betting Sites in {c['city']}, {c['country']} &middot; 2026"

    faq_items = [
        (
            f"Is sports betting legal in {c['city']}?",
            f"Yes. Sports betting is legal in {c['city']}, {c['country']}, regulated by the {c['regulator']}. All bookmakers listed on SifuFinds hold valid licences for the {c['country']} market.",
        ),
        (
            f"What are the best betting sites in {c['city']}?",
            f"The best licensed betting sites serving {c['city']} bettors are listed on SifuFinds. All are regulated by the {c['regulator']} and accept local payment methods including {', '.join(c['payments'][:2])}. Use the bookmaker comparison above to find current verified bonuses.",
        ),
    ]
    faq_schema = ',\n'.join(
        json.dumps({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a},
        })
        for q, a in faq_items
    )

    return f"""<!DOCTYPE html>
<!-- sifufinds.com/countries/{c['country_slug']}/{c['slug']}/ — Betting Sites in {c['city']} {c['country']} -->
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{seo_meta_description(meta_desc)}">
<meta name="keywords" content="betting sites {c['city'].lower()}, {c['city'].lower()} bookmakers, sports betting {c['city'].lower()} 2026, best betting {c['city'].lower()} {c['country'].lower()}, online betting {c['city'].lower()}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="author" content="SifuFinds">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="en-{c['country_code']}" href="{canonical}">
<link rel="alternate" hreflang="en" href="{canonical}">
<meta name="geo.region" content="{c['country_code']}">
<meta name="geo.placename" content="{c['city']}">

<meta property="og:type" content="website">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="Betting Sites in {c['city']} 2026 | SifuFinds">
<meta property="og:description" content="{meta_desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="https://sifufinds.com/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_{c['country_code']}">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@sifufinds">
<meta name="twitter:title" content="Betting Sites in {c['city']} 2026 | SifuFinds">
<meta name="twitter:description" content="{meta_desc}">
<meta name="twitter:image" content="https://sifufinds.com/assets/og-image.png">

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
      "isPartOf": {{"@id": "https://sifufinds.com/#website"}}
    }},
    {{
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://sifufinds.com/"}},
        {{"@type": "ListItem", "position": 2, "name": "Countries", "item": "https://sifufinds.com/countries/"}},
        {{"@type": "ListItem", "position": 3, "name": {json.dumps(c['country'] + " Bonus Sites")}, "item": "https://sifufinds.com/best-bonus-in-{c['country_slug']}/"}},
        {{"@type": "ListItem", "position": 4, "name": {json.dumps(c['city'] + " Betting")}, "item": "{canonical}"}}
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
<link rel="preload" href="{ap}assets/shared.css" as="style">
<link rel="stylesheet" href="{ap}assets/shared.css">
<style>
.reg-badge{{display:inline-block;background:#edf7f0;border:1px solid #c8e6c9;border-radius:6px;padding:5px 12px;font-size:12px;font-weight:700;color:#1a6b35;margin-bottom:10px}}
.pay-grid{{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}}
.pay-chip{{background:#f5f5f5;border:1px solid #e0e0e0;border-radius:5px;padding:4px 10px;font-size:12px;font-weight:500;color:#333}}
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
</style>
</head>
<body>

<div class="tbar">
  <div class="tbar-l">
    <a href="{ap}">🏠 Home</a>
    <a href="{cp}">🌍 {c['country']}</a>
    <button onclick="openPage('responsible')">Responsible Gambling</button>
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
    <a class="logo" href="{ap}"><img src="{ap}assets/icon.png" height="38" alt="SifuFinds logo" style="display:block;object-fit:contain">SifuFinds</a>
    <div class="ntabs">
      <a class="nt" href="{ap}">⭐ Best Bonuses</a>
      <a class="nt" href="{ap}tips/">💡 Tips</a>
      <a class="nt" href="{ap}casino/">🎰 Casino</a>
      <a class="nt" href="{ap}odds/">📊 Live Odds<span class="lpulse" style="margin-left:4px"></span></a>
      <a class="nt on" href="{ap}countries/">🌍 Countries</a>
      <a class="nt" href="{ap}blog/">📰 Blog</a>
    </div>
  </div>
</nav>

<div id="hbrands" class="hbrands"></div>

<div class="hero"><div class="wrap">
  <h1>{h1}</h1>
  <p>{c['about']}</p>
  <div class="trust">
    <div class="tb">✅ Licensed &amp; Verified</div>
    <div class="tb">📱 Mobile-First</div>
    <div class="tb">🔄 Updated Daily</div>
    <div class="tb">💳 {c['payments'][0]}</div>
  </div>
</div></div>

<div class="sec-bg"><div class="wrap">
  <div class="breadcrumb">
    <a href="{ap}">Home</a><span>›</span><a href="{ap}countries/">Countries</a><span>›</span><a href="{cp}">{c['country']}</a><span>›</span>{c['city']}
  </div>

  <div class="adv">📢 <strong>Advertiser Disclosure:</strong> We earn commission from some bookmaker links. All bonuses verified. Check T&Cs. 18+.</div>

  <div class="cbox2">
    <h2>Is Betting Legal in {c['city']}?</h2>
    <div class="reg-badge">✅ Regulated — {c['regulator']}</div>
    <p>Yes. Sports betting is <strong>legal and regulated</strong> in {c['city']}, {c['country']}. The licensing authority is the <strong>{c['regulator']}</strong>. All bookmakers on SifuFinds are fully licensed for the {c['country']} market.</p>
  </div>

  <div class="sec-lbl" style="font-size:11px;font-weight:700;color:#aaa;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">LICENSED BOOKMAKERS · {c['city'].upper()} · 2026</div>
  <h2 style="font-size:17px;font-weight:800;color:#111;margin-bottom:9px">Best Betting Sites in {c['city']} — Verified 2026</h2>

  <div class="fbar"><div class="fr">
    <span class="fr-label">Sort:</span>
    <select class="fsel" id="srt" onchange="renderBooks()">
      <option value="default">Editors' Picks</option>
      <option value="stars">Highest Rated</option>
      <option value="bonus">Highest Bonus</option>
    </select>
    <span class="fr-label" style="margin-left:4px">Filter:</span>
    <button class="fp on" data-f="all" onclick="setFilt(this)">All</button>
    <button class="fp" data-f="nodep" onclick="setFilt(this)">No Deposit</button>
    <button class="fp" data-f="cashout" onclick="setFilt(this)">Cash Out</button>
  </div></div>

  <div class="mc" id="mcount"></div>
  <div id="bk-cards"><noscript><p style="padding:16px;color:#666">Enable JavaScript to view bookmaker listings.</p></noscript></div>

  <div class="cbox2">
    <h2>Payment Methods in {c['city']}</h2>
    <p>These payment methods are accepted at licensed {c['city']} betting sites:</p>
    <div class="pay-grid">{pay_chips}</div>
  </div>

  <div class="cbox2">
    <h2>Popular Sports &amp; Leagues in {c['city']}</h2>
    <ul style="padding-left:18px;margin:0">
{league_items}
    </ul>
  </div>

  <div class="cbox2">
    <h2>FAQ — Betting in {c['city']}</h2>
    <div class="faq-item">
      <button class="faq-q" onclick="this.parentElement.classList.toggle('open')">Is sports betting legal in {c['city']}? <span class="faq-arr">▼</span></button>
      <div class="faq-a"><p>Yes. Sports betting is legal in {c['city']}, {c['country']}, regulated by the <strong>{c['regulator']}</strong>. Only use bookmakers listed on SifuFinds — all hold valid licences for the {c['country']} market.</p></div>
    </div>
    <div class="faq-item">
      <button class="faq-q" onclick="this.parentElement.classList.toggle('open')">What are the best betting sites in {c['city']}? <span class="faq-arr">▼</span></button>
      <div class="faq-a"><p>The best licensed {c['city']} betting sites are listed above. All are regulated by the {c['regulator']} and accept {c['payments'][0]} and other local payment methods. Use the Highest Bonus sort to see the top current offer.</p></div>
    </div>
  </div>

  <div class="resp">⚠️ Gambling involves risk. Only bet what you can afford to lose. 18+ only.</div>
</div></div>

<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison<br>
  <a href="{ap}">Home</a> · <a href="{ap}countries/">Countries</a> · <a href="{cp}">{c['country']} Betting</a> · <a href="{ap}tips/">Tips</a> · <a href="{ap}blog/">Blog</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only.
</div>

<div class="page-modal-bg" id="page-modal"><div class="page-modal"><button class="page-modal-close" onclick="closePage()">×</button><div class="pm" id="page-content"></div></div></div>

<script src="{ap}assets/shared.js"></script>
<script>
const SITE={{home:'{ap}',tips:'{ap}tips/',casino:'{ap}casino/',odds:'{ap}odds/',countries:'{ap}countries/'}};
const _PAGE_CTY='{c['country_code']}';
let _activeFilt='all';
function getCurrentCountry(){{return _PAGE_CTY;}}
function setFilt(btn){{document.querySelectorAll('.fp').forEach(b=>b.classList.remove('on'));btn.classList.add('on');_activeFilt=btn.dataset.f;renderBooks();}}
function filterBooks(books){{const f=_activeFilt;if(f==='all')return books;if(f==='nodep')return books.filter(b=>b.nodep);if(f==='cashout')return books.filter(b=>b.cashout);return books;}}
function sortBooks(books){{const s=document.getElementById('srt')?.value||'default';if(s==='stars')return[...books].sort((a,b)=>b.stars-a.stars);if(s==='bonus')return[...books].sort((a,b)=>(b.nodep?1:0)-(a.nodep?1:0));return books;}}
const bookCard=(b,i,rank)=>{{
  const badge=b.badge==='new'?'<span class="badge-new">NEW</span>':b.badge==='hot'?'<span class="badge-hot">HOT</span>':b.nodep?'<span class="badge-nd">NO DEP</span>':'';
  return`<div class="bkcard ${{rank<3?'top3':''}} ${{b.nodep?'nodep-card':''}}"><div class="bk-main"><span class="bk-rk">#${{rank+1}}</span><div class="bk-logo" style="background:${{b.bg}}">${{logoImg(b.url,b.name,b.abbr,b.tc,60,8)}}</div><div><div class="bk-tag">${{b.tag}}</div><div class="bk-nm">${{b.name}}${{badge}}</div><div class="bk-off">${{b.off}}</div><div class="bk-meta"><span>Min: ${{b.min}}</span><span>${{b.sports}} sports</span><span>${{b.lic}}</span></div></div><div class="bk-act"><div class="bk-stars">${{stars(b.stars)}}</div><a class="gbtn${{b.nodep?' gold':''}}" href="${{b.url}}" target="_blank" rel="noopener noreferrer">Claim Bonus →</a><div class="tc-n">T&amp;Cs Apply · 18+</div></div></div><div class="pm-row">${{(b.pms||[]).map(pm).join('')}}</div></div>`;
}};
function renderBooks(){{const books=filterBooks(sortBooks(BOOKS[_PAGE_CTY]||[]));const el=document.getElementById('bk-cards');if(!books.length){{el.innerHTML='<div class="no-results">No bookmakers match this filter.</div>';return;}}el.innerHTML=books.map((b,i)=>bookCard(b,i,i)).join('');H('mcount',`Showing ${{books.length}} bookmaker${{books.length!==1?'s':''}}`);}}
function init(){{const sel=document.getElementById('ctySel');if(sel)sel.value=_PAGE_CTY;H('foot-yr',NOW.getFullYear());renderBooks();}}
init();
</script>
</body>
</html>"""


if __name__ == '__main__':
    for city in CITIES:
        out_dir = os.path.join(BASE, city['path'])
        os.makedirs(out_dir, exist_ok=True)
        html = make_city_page(city)
        out_path = os.path.join(out_dir, 'index.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  ✓  /{city['path']}/")
    print(f'\n✅ Generated {len(CITIES)} city pages')
