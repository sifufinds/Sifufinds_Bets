#!/usr/bin/env python3
"""Generate new bonus type pages: welcome-bonus, free-bet, cashback, reload."""

import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
from seo_meta import seo_title, seo_meta_description

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

PAGES = [
    {
        'slug': 'welcome-bonus',
        'title': 'Best Betting Welcome Bonuses in Africa 2026 | 100% Match Bonus | SifuFinds',
        'desc': 'Best welcome bonuses at licensed African bookmakers 2026. Claim 100% match bonuses, free bets, and deposit matches in Nigeria, Kenya, South Africa, Ghana and 19 more countries. Verified and updated daily.',
        'keywords': 'betting welcome bonus Africa, sports betting bonus Nigeria, welcome offer Kenya bookmakers, best welcome bonus Ghana, deposit match bonus South Africa, first deposit bonus Africa 2026',
        'og_title': 'Best Betting Welcome Bonuses Africa 2026 | SifuFinds',
        'h1': 'Best Betting Welcome Bonuses in Africa &middot; 2026',
        'intro': "A welcome bonus is the first bonus offered to new bettors when they register and make their first deposit. Most African bookmakers offer a <strong>100% match welcome bonus</strong> — meaning if you deposit ₦5,000, you get another ₦5,000 in bonus funds. Welcome bonuses are available at licensed bookmakers in all 23 African countries covered by SifuFinds.",
        'filter_default': 'all',
        'faq': [
            ('What is a sports betting welcome bonus?', "A welcome bonus is a promotional offer for new customers. Most bookmakers in Africa offer a 100% deposit match — they double your first deposit up to a set limit. For example, deposit ₦10,000 and get ₦10,000 bonus = ₦20,000 total to bet with. You must meet wagering requirements (usually 5–10× the bonus) before withdrawing winnings."),
            ('Which African bookmaker has the best welcome bonus?', "The best welcome bonuses in Africa in 2026 are from 1xBet (up to ₦130,000 in Nigeria / KSh 35,000 in Kenya), Melbet, and Betway. All three offer 100% first deposit matches. Bonus amounts and T&Cs vary by country — use the comparison above to find the current top offer in your country."),
            ('How do I claim a welcome bonus at an African bookmaker?', "To claim a welcome bonus: (1) Register at a licensed bookmaker. (2) Complete KYC verification. (3) Make your first qualifying deposit (minimum amounts apply). (4) The bonus is automatically credited in most cases — some bookmakers require a promo code. (5) Meet the wagering requirements before withdrawing."),
            ('What are wagering requirements on welcome bonuses?', "Wagering requirements mean you must bet the bonus amount a set number of times before you can withdraw winnings. Most African bookmakers set this at 5× to 10× the bonus amount. For example: ₦5,000 bonus × 5× = ₦25,000 in total bets required before withdrawal. Always check the specific T&Cs for each offer."),
        ],
        'schema_name': 'Best Betting Welcome Bonuses in Africa 2026',
        'schema_desc': 'Best 100% match welcome bonuses at licensed African bookmakers across Nigeria, Kenya, South Africa, Ghana and 19 more countries.',
        'canonical_path': 'bonuses/welcome-bonus',
        'breadcrumb_name': 'Welcome Bonuses',
        'icon': '🎁',
        'color': '#1a6b35',
    },
    {
        'slug': 'free-bet',
        'title': 'Best Free Bet Offers in Africa 2026 | Free Sports Betting | SifuFinds',
        'desc': 'Best free bet offers at licensed African bookmakers 2026. Claim free bets in Nigeria, Kenya, South Africa, Ghana and more. No deposit and deposit free bets compared. Verified daily.',
        'keywords': 'free bet Africa, free bet Nigeria 2026, free bet Kenya bookmakers, free sports bet South Africa, free bet offer Ghana, free bet no deposit Africa, free bets African bookmakers 2026',
        'og_title': 'Best Free Bet Offers Africa 2026 | SifuFinds',
        'h1': 'Best Free Bet Offers in Africa &middot; 2026',
        'intro': "A <strong>free bet</strong> lets you place a wager without risking your own money. African bookmakers offer free bets as welcome offers, loyalty rewards, and weekly promotions. Free bets come in two types: <strong>No Deposit Free Bets</strong> (available just for registering) and <strong>Deposit Free Bets</strong> (credited after your first deposit). SifuFinds verifies all free bet offers daily across 23 African countries.",
        'filter_default': 'nodep',
        'faq': [
            ('What is a free bet at an African bookmaker?', "A free bet lets you place a wager without using your own money. If your free bet wins, you receive the winnings (minus the stake). For example, if you have a KSh 500 free bet and win at 3.00 odds, you receive KSh 1,000 (profit only — the KSh 500 stake is not returned). Free bets are one of the most popular promotions at African bookmakers."),
            ('How do I get a free bet in Nigeria or Kenya?', "To get a free bet in Nigeria: register at Bet9ja, 1xBet Nigeria, or Betway Nigeria, and claim the welcome offer. In Kenya: register at Sportpesa, Betika, or Betway Kenya. Most require a small first deposit (minimum ₦100 or KSh 100). Some bookmakers offer no-deposit free bets just for registering your mobile number."),
            ('What is the difference between a free bet and a no deposit bonus?', "A free bet is a specific token to place one wager at no risk. A no deposit bonus is free bonus cash credited to your account without depositing — you can use it across multiple bets. Both are available at African bookmakers covered by SifuFinds, though no deposit bonuses are rarer and typically smaller."),
            ('Do free bets expire?', "Yes. Most free bets expire within 7 days of being credited. Always check the T&Cs. In Nigeria: free bets from Bet9ja typically expire within 7 days. In Kenya: Sportpesa free bets typically expire within 72 hours. The comparison above shows current expiry terms for each bookmaker."),
        ],
        'schema_name': 'Best Free Bet Offers in Africa 2026',
        'schema_desc': 'Best free bet offers at licensed African bookmakers in Nigeria, Kenya, South Africa and 20 more countries. No deposit and deposit free bets compared.',
        'canonical_path': 'bonuses/free-bet',
        'breadcrumb_name': 'Free Bets',
        'icon': '🎟',
        'color': '#c0392b',
    },
    {
        'slug': 'cashback-bonus',
        'title': 'Best Cashback Betting Bonuses in Africa 2026 | Get Money Back | SifuFinds',
        'desc': 'Best cashback and money-back betting bonuses in Africa 2026. Get a percentage of losses back at licensed bookmakers in Nigeria, Kenya, South Africa, Ghana and more. Updated daily.',
        'keywords': 'cashback betting bonus Africa, money back offer Nigeria, cashback sportsbook Kenya, refund bonus Africa 2026, cashback bookmaker South Africa, insurance bet Africa, bet refund Africa',
        'og_title': 'Best Cashback Betting Bonuses Africa 2026 | SifuFinds',
        'h1': 'Best Cashback Betting Bonuses in Africa &middot; 2026',
        'intro': "A <strong>cashback bonus</strong> returns a percentage of your net losses over a period — giving you a safety net when results go against you. African bookmakers typically offer <strong>10–20% cashback</strong> on weekly losses, credited as bonus funds. Some offer cashback only on accumulators (multi-bets). Cashback promotions reward loyal customers and are widely available across Nigeria, Kenya, South Africa, and Ghana.",
        'filter_default': 'all',
        'faq': [
            ('What is a cashback betting bonus?', "A cashback bonus returns a percentage of your net losses as bonus funds. For example, if you lose ₦10,000 in a week and the cashback rate is 10%, you receive ₦1,000 back as a bonus. The bonus is usually subject to 1× wagering — meaning you must use it to place one more bet before withdrawing. Cashback makes it easier to manage your bankroll during a losing run."),
            ('Which African bookmakers offer cashback bonuses?', "Leading African bookmakers with cashback promotions include 1xBet (up to 30% cashback on losses), Betway (Money Back on specific markets), Hollywoodbets (South Africa — Money Back specials on accumulators), and Sportpesa (Kenya — regular cashback promos). The cashback rates and terms change frequently — check the latest offers in the comparison above."),
            ('Is cashback the same as insurance?', "They are similar. Cashback typically applies to your overall weekly or monthly losses. An insurance bet (or 'bet refund') applies to a single specific bet — you get your stake back if you lose by a defined margin (e.g., if your team loses by exactly 1 goal). Both types of protection are offered by African bookmakers, and both are featured in SifuFinds comparisons."),
            ('Can I combine cashback with a welcome bonus?', "No — you cannot combine a welcome bonus and a cashback promotion at the same time at most bookmakers. Cashback is typically for existing customers who have already used their welcome offer. Some bookmakers run concurrent promotions, but cashback is generally a loyalty benefit for regular bettors."),
        ],
        'schema_name': 'Best Cashback Betting Bonuses in Africa 2026',
        'schema_desc': 'Best cashback and money-back betting promotions at licensed African bookmakers. Get a percentage of losses returned at top bookmakers in Nigeria, Kenya, South Africa and more.',
        'canonical_path': 'bonuses/cashback-bonus',
        'breadcrumb_name': 'Cashback Bonuses',
        'icon': '💸',
        'color': '#d35400',
    },
    {
        'slug': 'reload-bonus',
        'title': 'Best Reload Bonuses for African Bettors 2026 | Deposit Bonus Every Week | SifuFinds',
        'desc': 'Best weekly reload and re-deposit bonuses at licensed African bookmakers 2026. Get extra funds on your 2nd, 3rd and subsequent deposits in Nigeria, Kenya, South Africa and more. Updated daily.',
        'keywords': 'reload bonus Africa, weekly deposit bonus Nigeria, re-deposit bonus Kenya, second deposit bonus Africa, reload offer South Africa 2026, recurring betting bonus Africa',
        'og_title': 'Best Reload Bonuses Africa 2026 | SifuFinds',
        'h1': 'Best Reload (Re-Deposit) Bonuses in Africa &middot; 2026',
        'intro': "A <strong>reload bonus</strong> (also called a re-deposit or weekly deposit bonus) rewards existing customers for topping up their account. Unlike a welcome bonus (which is one-time only), reload bonuses recur — typically every week or month. African bookmakers offer reload bonuses ranging from <strong>10% to 50% on qualifying deposits</strong>, making them one of the most valuable ongoing promotions for regular bettors.",
        'filter_default': 'all',
        'faq': [
            ('What is a reload bonus?', "A reload bonus is a deposit bonus for existing customers — not just new ones. Bookmakers award a percentage of your deposit (e.g., 50% up to ₦5,000) when you reload your account. The bonus is credited instantly alongside your deposit. Wagering requirements (usually 3–8×) apply before withdrawal. Reload bonuses are the most commonly recurring promotion across African bookmakers."),
            ('How often can I claim a reload bonus in Africa?', "Most African bookmakers offer reload bonuses weekly. Some run daily deposit promotions (1xBet, Melbet). Others tie reload bonuses to specific events — a Champions League week or AFCON matchday reload. Check the promotions tab of each bookmaker for the current schedule. SifuFinds lists active reload promotions updated daily."),
            ('Are reload bonuses available on mobile money in Africa?', "Yes. Reload bonuses apply to all qualifying deposit methods including M-Pesa, MTN MoMo, OPay, and Airtel Money — not just card deposits. The minimum deposit to trigger a reload bonus varies (typically ₦500 / KSh 100) but mobile money deposits qualify at all major African bookmakers."),
            ('Do reload bonuses expire?', "Yes — typically within 7 days of being credited. Always check the expiry before depositing. Some bookmakers require you to opt-in to the reload bonus before making your deposit (especially at 1xBet and Melbet). The comparison above shows current T&Cs for each reload offer."),
        ],
        'schema_name': 'Best Reload Bonuses for African Bettors 2026',
        'schema_desc': 'Best weekly reload and re-deposit bonuses at licensed African bookmakers. Get extra funds on repeat deposits in Nigeria, Kenya, South Africa and more.',
        'canonical_path': 'bonuses/reload-bonus',
        'breadcrumb_name': 'Reload Bonuses',
        'icon': '🔄',
        'color': '#2980b9',
    },
]


def make_bonus_page(p):
    faq_items = '\n'.join(f"""    <div class="faq-item">
      <button class="faq-q" onclick="this.parentElement.classList.toggle('open')">{q} <span class="faq-arr">▼</span></button>
      <div class="faq-a"><p>{a}</p></div>
    </div>""" for q, a in p['faq'])

    faq_schema = ',\n'.join(
        json.dumps({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a},
        })
        for q, a in p['faq']
    )

    return f"""<!DOCTYPE html>
<!-- sifufinds.com/{p['canonical_path']}/ — {p['og_title']} -->
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{seo_title(p['title'].removesuffix(' | SifuFinds'))}</title>
<meta name="description" content="{seo_meta_description(p['desc'])}">
<meta name="keywords" content="{p['keywords']}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="author" content="SifuFinds">
<link rel="canonical" href="https://sifufinds.com/{p['canonical_path']}/">
<link rel="alternate" hreflang="en" href="https://sifufinds.com/{p['canonical_path']}/">

<meta property="og:type" content="website">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="{p['og_title']}">
<meta property="og:description" content="{p['desc']}">
<meta property="og:url" content="https://sifufinds.com/{p['canonical_path']}/">
<meta property="og:image" content="https://sifufinds.com/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_GB">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@sifufinds">
<meta name="twitter:title" content="{p['og_title']}">
<meta name="twitter:description" content="{p['desc']}">
<meta name="twitter:image" content="https://sifufinds.com/assets/og-image.png">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "WebPage",
      "@id": "https://sifufinds.com/{p['canonical_path']}/#webpage",
      "name": "{p['schema_name']}",
      "description": "{p['schema_desc']}",
      "url": "https://sifufinds.com/{p['canonical_path']}/",
      "inLanguage": "en-GB",
      "isPartOf": {{"@id": "https://sifufinds.com/#website"}}
    }},
    {{
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://sifufinds.com/"}},
        {{"@type": "ListItem", "position": 2, "name": "Bonuses", "item": "https://sifufinds.com/bonuses/"}},
        {{"@type": "ListItem", "position": 3, "name": "{p['breadcrumb_name']}", "item": "https://sifufinds.com/{p['canonical_path']}/"}}
      ]
    }},
    {{
      "@type": "FAQPage",
      "mainEntity": [{faq_schema}]
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
.bonus-badge{{display:inline-block;background:#edf7f0;border:1px solid #c8e6c9;border-radius:6px;padding:5px 14px;font-size:12px;font-weight:700;color:{p['color']};margin-bottom:10px}}
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
    <a href="../../">🏠 Home</a>
    <a href="../../bonuses/">🎁 Bonuses</a>
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

<div class="hero"><div class="wrap">
  <h1>{p['icon']} {p['h1']}</h1>
  <p>{p['intro']}</p>
  <div class="trust">
    <div class="tb">✅ Verified Bonuses</div>
    <div class="tb">📱 All 23 African Countries</div>
    <div class="tb">🔄 Updated Daily</div>
    <div class="tb">🏛 Licensed Only</div>
  </div>
</div></div>

<div class="sec-bg"><div class="wrap">
  <div class="breadcrumb">
    <a href="../../">Home</a><span>›</span><a href="../../bonuses/">Bonuses</a><span>›</span>{p['breadcrumb_name']}
  </div>

  <div class="adv">📢 <strong>Advertiser Disclosure:</strong> We earn commission from some bookmaker links. All bonuses verified. Check T&Cs. 18+.</div>

  <div class="sec-lbl" style="font-size:11px;font-weight:700;color:#aaa;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">VERIFIED OFFERS · AFRICA · 2026</div>
  <h2 style="font-size:17px;font-weight:800;color:#111;margin-bottom:9px">{p['breadcrumb_name']} — Top African Bookmakers</h2>

  <div class="fbar"><div class="fr">
    <span class="fr-label">Sort:</span>
    <select class="fsel" id="srt" onchange="renderBooks()">
      <option value="default">Editors' Picks</option>
      <option value="stars">Highest Rated</option>
      <option value="bonus">No Deposit First</option>
    </select>
    <span class="fr-label" style="margin-left:4px">Filter:</span>
    <button class="fp {'on' if p['filter_default']=='all' else ''}" data-f="all" onclick="setFilt(this)">All</button>
    <button class="fp {'on' if p['filter_default']=='nodep' else ''}" data-f="nodep" onclick="setFilt(this)">No Deposit</button>
    <button class="fp" data-f="cashout" onclick="setFilt(this)">Cash Out</button>
  </div></div>

  <div class="mc" id="mcount"></div>
  <div id="bk-cards"><noscript><p style="padding:16px;color:#666">Enable JavaScript to view bookmaker listings.</p></noscript></div>

  <div class="cbox2">
    <h2>FAQ — {p['breadcrumb_name']}</h2>
{faq_items}
  </div>

  <div class="resp">⚠️ Gambling involves risk. Only bet what you can afford to lose. 18+ only. T&Cs apply to all bonuses.</div>
</div></div>

<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison<br>
  <a href="../../">Home</a> · <a href="../../bonuses/">Bonuses</a> · <a href="../../countries/">Countries</a> · <a href="../../tips/">Tips</a> · <a href="../../blog/">Blog</a> · <a href="../../about/">About</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only.
</div>

<div class="page-modal-bg" id="page-modal"><div class="page-modal"><button class="page-modal-close" onclick="closePage()">×</button><div class="pm" id="page-content"></div></div></div>

<script src="../../assets/shared.js?v=24"></script>
<script>
const SITE={{home:'../../',tips:'../../tips/',casino:'../../casino/',odds:'../../odds/',countries:'../../countries/'}};
let _activeFilt='{p['filter_default']}';
function getCurrentCountry(){{const sel=document.getElementById('ctySel');return sel?sel.value:'NG';}}
function setFilt(btn){{document.querySelectorAll('.fp').forEach(b=>b.classList.remove('on'));btn.classList.add('on');_activeFilt=btn.dataset.f;renderBooks();}}
function filterBooks(books){{const f=_activeFilt;if(f==='all')return books;if(f==='nodep')return books.filter(b=>b.nodep);if(f==='cashout')return books.filter(b=>b.cashout);return books;}}
function sortBooks(books){{const s=document.getElementById('srt')?.value||'default';if(s==='stars')return[...books].sort((a,b)=>b.stars-a.stars);if(s==='bonus')return[...books].sort((a,b)=>(b.nodep?1:0)-(a.nodep?1:0));return books;}}
const bookCard=(b,i,rank)=>{{
  const badge=b.badge==='new'?'<span class="badge-new">NEW</span>':b.badge==='hot'?'<span class="badge-hot">HOT</span>':b.nodep?'<span class="badge-nd">NO DEP</span>':'';
  return`<div class="bkcard ${{rank<3?'top3':''}} ${{b.nodep?'nodep-card':''}}"><div class="bk-main"><span class="bk-rk">#${{rank+1}}</span><div class="bk-logo" style="background:${{b.bg}}">${{logoImg(b.url,b.name,b.abbr,b.tc,60,8)}}</div><div><div class="bk-tag">${{b.tag}}</div><div class="bk-nm">${{b.name}}${{badge}}</div><div class="bk-off">${{b.off}}</div><div class="bk-meta"><span>Min: ${{b.min}}</span><span>${{b.sports}} sports</span><span>${{b.lic}}</span></div></div><div class="bk-act"><div class="bk-stars">${{stars(b.stars)}}</div><a class="gbtn${{b.nodep?' gold':''}}" href="${{b.url}}" target="_blank" rel="noopener noreferrer">Claim Bonus →</a><div class="tc-n">T&amp;Cs Apply · 18+</div></div></div><div class="pm-row">${{(b.pms||[]).map(pm).join('')}}</div></div>`;
}};
function renderBooks(){{const cty=getCurrentCountry();const books=filterBooks(sortBooks(BOOKS[cty]||BOOKS['NG']||[]));const el=document.getElementById('bk-cards');if(!books.length){{el.innerHTML='<div class="no-results">No bookmakers match this filter.</div>';return;}}el.innerHTML=books.map((b,i)=>bookCard(b,i,i)).join('');H('mcount',`Showing ${{books.length}} bookmaker${{books.length!==1?'s':''}}`);}}
function init(){{H('foot-yr',NOW.getFullYear());renderBooks();}}
init();
</script>
</body>
</html>"""


if __name__ == '__main__':
    bonuses_dir = os.path.join(BASE, 'bonuses')
    for p in PAGES:
        slug = p['slug']
        out_dir = os.path.join(bonuses_dir, slug)
        os.makedirs(out_dir, exist_ok=True)
        html = make_bonus_page(p)
        out_path = os.path.join(out_dir, 'index.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'  ✓  /bonuses/{slug}/')
    print(f'\n✅ Generated {len(PAGES)} bonus pages')
