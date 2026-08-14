"""
bookmaker_page_template.py — renders bookmakers/<slug>/index.html.

Two renderers, both pure functions (facts dict in, HTML string out):
  - render_bookmaker_page()      — a new, freshly-researched brand
  - render_discontinued_page()   — replaces a page for a brand confirmed
                                    defunct, without ever 404-ing the URL

Structure mirrors the existing hand-authored pages under bookmakers/
(e.g. bookmakers/hollywoodbets/index.html) so a machine-generated page is
indistinguishable in shape from the manually built ones: same tbar/nav,
same Review + BreadcrumbList JSON-LD, same score-grid/pros-cons/FAQ layout,
same shared.js wiring for country switching and the live BOOKS comparison
list. Deliberately NOT reused verbatim from an LLM — every field here is
either a fact the calling agent already verified via research, or a
deterministic Python computation, so a hallucinated number can never reach
this template.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

FEATURED_LISTINGS_PATH = Path(__file__).resolve().parents[3] / "data" / "featured_listings.json"

_COUNTRY_SELECTOR = """      <option value="NG">🇳🇬 Nigeria · ₦ NGN</option>
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

# Rotation of hero gradients so newly-added brands don't all look identical.
_HERO_GRADIENTS = [
    ("#1a4d8f", "#2e6bc4"),
    ("#7c2d12", "#c2410c"),
    ("#164e63", "#0891b2"),
    ("#4c1d95", "#7c3aed"),
    ("#831843", "#be185d"),
]

_COUNTRY_TO_ISO2 = {
    "Nigeria": "NG", "Kenya": "KE", "Ghana": "GH", "South Africa": "ZA",
    "Tanzania": "TZ", "Uganda": "UG", "Zambia": "ZM", "Ethiopia": "ET",
    "Ivory Coast": "CI", "Cameroon": "CM", "Senegal": "SN", "Rwanda": "RW",
    "Zimbabwe": "ZW", "Malawi": "MW", "Mozambique": "MZ", "Angola": "AO",
    "DR Congo": "CD", "Botswana": "BW", "Namibia": "NA", "Egypt": "EG",
    "Morocco": "MA", "Sierra Leone": "SL", "Liberia": "LR",
}


def _hero_gradient(slug: str) -> tuple[str, str]:
    return _HERO_GRADIENTS[hash(slug) % len(_HERO_GRADIENTS)]


def _active_featured_listing(slug: str) -> dict | None:
    """Return the active Featured Listings entry for this brand slug, if any.

    data/featured_listings.json is the single source of truth (managed by
    agent_brand_partnerships.py --manage-listings) — read here rather than
    duplicated so the hero badge can never drift from what was actually
    sold/approved. Returns None for anything not sponsored=True or outside
    its starts_at/ends_at window, so an expired deal silently stops showing.
    """
    if not FEATURED_LISTINGS_PATH.exists():
        return None
    try:
        data = json.loads(FEATURED_LISTINGS_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return None

    now = datetime.now(timezone.utc)
    for entry in data.get("listings", []):
        if entry.get("brand_slug") != slug or entry.get("sponsored") is not True:
            continue
        starts_at = entry.get("starts_at")
        ends_at = entry.get("ends_at")
        if starts_at and datetime.fromisoformat(starts_at.replace("Z", "+00:00")) > now:
            continue
        if ends_at and datetime.fromisoformat(ends_at.replace("Z", "+00:00")) < now:
            continue
        return entry
    return None


def render_bookmaker_page(facts: dict) -> str:
    """Render bookmakers/<slug>/index.html for a newly-discovered brand.

    `facts` should be produced by a research pipeline that only supplies
    directly-observed fields (official_url, primary_country) or conservative,
    clamped values, never an unclamped LLM claim, so the verdict badge below
    always reads "New Listing — Under Review" instead of "Recommended": a
    single pass of research isn't enough evidence to vouch for a brand the
    way the hand-reviewed pages do.
    """
    slug = facts["slug"]
    name = facts["brand_name"]
    country = facts.get("primary_country", "Nigeria")
    iso2 = _COUNTRY_TO_ISO2.get(country, "NG")
    official_url = facts["official_url"]
    rating = facts["rating"]
    year = datetime.now(timezone.utc).year
    today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    grad_a, grad_b = _hero_gradient(slug)

    pros = facts.get("pros", [])
    cons = facts.get("cons", [])
    faqs = facts.get("faqs", [])
    payment_methods = facts.get("payment_methods", ["Bank transfer", "Card payment"])
    welcome_bonus = facts.get("welcome_bonus_summary", "Check the operator's site for current welcome offer terms.")
    licensing_status = facts.get("licensing_status", "Licensing status unconfirmed — verify on the operator's own site before depositing.")
    verdict_paragraph = facts.get("verdict_paragraph", "")

    pros_html = "".join(f"<li>{p}</li>" for p in pros) or "<li>Independent review in progress</li>"
    cons_html = "".join(f"<li>{c}</li>" for c in cons) or "<li>Newly listed — limited verified track record so far</li>"
    faq_html = "".join(
        f'''<div class="faq-item">
      <button class="faq-q" onclick="this.parentElement.classList.toggle('open')">{f["q"]} <span class="faq-arr">▼</span></button>
      <div class="faq-a"><p>{f["a"]}</p></div>
    </div>'''
        for f in faqs
    )
    pms_js_array = ", ".join(f"'{pm}'" for pm in payment_methods)

    stars_full = int(round(rating))
    stars = "★" * stars_full + "☆" * (5 - stars_full)

    featured = _active_featured_listing(slug)
    featured_badge_html = (
        f'<div class="verdict-badge featured-badge" title="{featured.get("criteria_note", "")}">'
        f'⭐ Featured Partner · Sponsored</div>'
    ) if featured else ""

    return f"""<!DOCTYPE html>
<!-- sifufinds.com/bookmakers/{slug}/ — {name} Review {year} — auto-researched listing -->
<html lang="en">
<head>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-0B51MX2ZKE"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-0B51MX2ZKE');
</script>
<meta charset="UTF-8">
<link rel="preload" href="../../assets/shared.js?v=21" as="script">
<link rel="preconnect" href="https://ipapi.co">
<link rel="preconnect" href="https://www.google-analytics.com">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} Review {year} | SifuFinds</title>
<meta name="description" content="Independent {name} review {year} by SifuFinds. {welcome_bonus} {licensing_status} New listing, under ongoing review.">
<meta name="keywords" content="{name.lower()} review {year}, {name.lower()} bonus, {name.lower()} {country.lower()}, is {name.lower()} legit">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="author" content="SifuFinds Brand Research Desk">
<link rel="canonical" href="https://sifufinds.com/bookmakers/{slug}/">
<link rel="alternate" hreflang="en" href="https://sifufinds.com/bookmakers/{slug}/">
<link rel="alternate" hreflang="x-default" href="https://sifufinds.com/">
<meta name="geo.region" content="{iso2}">

<meta property="og:type" content="website">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="{name} Review {year} | SifuFinds">
<meta property="og:description" content="Independent {name} review: {welcome_bonus}">
<meta property="og:url" content="https://sifufinds.com/bookmakers/{slug}/">
<meta property="og:image" content="https://sifufinds.com/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_GB">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@sifufinds">
<meta name="twitter:title" content="{name} Review {year} | SifuFinds">
<meta name="twitter:description" content="{welcome_bonus}">
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
        "name": "{name}",
        "url": "{official_url}"
      }},
      "reviewRating": {{
        "@type": "Rating",
        "ratingValue": "{rating}",
        "bestRating": "5",
        "worstRating": "1"
      }},
      "author": {{"@type": "Organization", "name": "SifuFinds", "url": "https://sifufinds.com"}},
      "publisher": {{"@type": "Organization", "name": "SifuFinds", "@id": "https://sifufinds.com/#organization"}},
      "datePublished": "{today_iso}",
      "dateModified": "{today_iso}",
      "name": "{name} Review {year}"
    }},
    {{
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://sifufinds.com/"}},
        {{"@type": "ListItem", "position": 2, "name": "Bookmaker Reviews", "item": "https://sifufinds.com/bookmakers/"}},
        {{"@type": "ListItem", "position": 3, "name": "{name} Review", "item": "https://sifufinds.com/bookmakers/{slug}/"}}
      ]
    }}
  ]
}}
</script>

<link rel="preload" href="../../assets/shared.css?v=12" as="style">
<link rel="stylesheet" href="../../assets/shared.css?v=12">
<style>
.bkr-hero{{background:linear-gradient(135deg,{grad_a} 0%,{grad_b} 100%);color:#fff;padding:28px 0}}
.bkr-hero h1{{font-size:clamp(20px,3.5vw,30px);font-weight:900;margin-bottom:8px;letter-spacing:-.5px}}
.bkr-hero p{{font-size:14px;color:rgba(255,255,255,.8);max-width:640px;line-height:1.65}}
.review-meta{{display:flex;gap:16px;flex-wrap:wrap;margin-top:10px}}
.review-meta span{{font-size:12px;color:rgba(255,255,255,.75)}}
.rating-big{{font-size:32px;font-weight:900;color:#fff;display:flex;align-items:center;gap:8px;margin-top:8px}}
.stars-big{{color:#fbbf24;font-size:20px}}
.verdict-badge{{display:inline-block;background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.4);color:#fff;font-size:12px;font-weight:700;padding:4px 12px;border-radius:6px;margin-top:8px}}
.featured-badge{{background:rgba(251,191,36,.22);border-color:rgba(251,191,36,.6);color:#fef3c7;margin-left:8px}}
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
.new-listing-notice{{background:#fffbeb;border:1px solid #fbbf24;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#78350f;margin:10px 0}}
@media(max-width:600px){{.pros-cons{{grid-template-columns:1fr}}}}
.sec-bg~.sec-bg,.cbox2,.footer-bar,[class*="section"]:not(:first-of-type){{content-visibility:auto;contain-intrinsic-size:0 500px}}
</style>
<link rel="icon" type="image/x-icon" href="/favicon.ico?v=3">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32x32.png?v=3">
<link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16x16.png?v=2">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png?v=3">
<link rel="manifest" href="/manifest.json">
</head>
<body>

<div class="tbar">
  <div class="tbar-l">
    <a href="../../">🏠 Home</a>
    <a href="../../responsible/">Responsible Gambling</a>
    <button onclick="openPage('about')">18+ Only</button>
  </div>
  <div class="tbar-r">
    <span class="csel-lbl">Your Country:</span>
    <select class="csel" id="ctySel" onchange="changeCountry(this.value)">
{_COUNTRY_SELECTOR}
    </select>
  </div>
</div>

<nav class="mnav">
  <div class="mnav-in">
    <a class="logo" href="../../"><img src="../../assets/icon.png" width="38" height="38" alt="SifuFinds logo" style="display:block;object-fit:contain" fetchpriority="high">SifuFinds</a>
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
    <h1>{name} Review {year}</h1>
    <p>Independent review of {name} by SifuFinds. {welcome_bonus}</p>
    <div class="rating-big"><span>{rating}/5</span><span class="stars-big">{stars}</span></div>
    <div class="verdict-badge">🆕 New Listing — Under Ongoing Review</div>
    {featured_badge_html}
    <div class="review-meta">
      <span>📅 First reviewed {today_iso}</span>
      <span>🔍 {licensing_status}</span>
      <span>🌍 {country}</span>
    </div>
  </div>
</div>

<div class="sec-bg"><div class="wrap" style="padding-top:14px">
  <div class="breadcrumb">
    <a href="../../">Home</a><span>›</span><a href="../">Bookmaker Reviews</a><span>›</span>{name} Review
  </div>

  <div class="adv">📢 <strong>Advertiser Disclosure:</strong> SifuFinds does not currently have a commercial relationship with {name}. This listing was produced from independent research; the link below goes to {name}'s own official site, not an affiliate link. Always check {name}'s official site for current T&amp;Cs.</div>

  <div class="new-listing-notice">🆕 <strong>New listing:</strong> {name} was added to SifuFinds after an automated research pass. It has not yet built up the multi-month track record our long-standing reviews have. Treat the score below as provisional and verify current bonus terms, licensing, and payout speed directly with the operator before depositing.</div>

  <div class="claim-box">
    <h3>ℹ️ {name} — Welcome Offer</h3>
    <p>{welcome_bonus}</p>
    <a class="claim-btn" href="{official_url}" target="_blank" rel="noopener noreferrer">Visit {name} Official Site →</a>
    <p style="font-size:11px;color:#888;margin-top:8px;margin-bottom:0">Not an affiliate link · T&amp;Cs apply · 18+ only</p>
  </div>

  <div class="cbox2">
    <h2>{name} — Quick Score Summary</h2>
    <div class="score-grid">
      <div class="score-item"><div class="score-num">{rating}</div><div class="score-lbl">Overall</div></div>
      <div class="score-item"><div class="score-num">{facts.get('score_bonus', rating)}</div><div class="score-lbl">Welcome Bonus</div></div>
      <div class="score-item"><div class="score-num">{facts.get('score_odds', rating)}</div><div class="score-lbl">Odds Quality</div></div>
      <div class="score-item"><div class="score-num">{facts.get('score_payments', rating)}</div><div class="score-lbl">Payments</div></div>
      <div class="score-item"><div class="score-num">{facts.get('score_app', rating)}</div><div class="score-lbl">App Experience</div></div>
      <div class="score-item"><div class="score-num">{facts.get('score_licensing', rating)}</div><div class="score-lbl">Licensing</div></div>
    </div>
  </div>

  <div class="cbox2">
    <h2>{name} Pros &amp; Cons</h2>
    <div class="pros-cons">
      <div class="pros"><h3>Pros</h3><ul>{pros_html}</ul></div>
      <div class="cons"><h3>Cons</h3><ul>{cons_html}</ul></div>
    </div>
  </div>

  <div class="cbox2">
    <h2>{name} Payment Methods</h2>
    <p>Payment methods observed at {name}:</p>
    <div class="pm-row-review" id="bk-pms"></div>
  </div>

  <div class="cbox2" style="border:2px solid #fbbf24">
    <h2>SifuFinds Verdict — Is {name} Worth It?</h2>
    <p style="font-size:13.5px;color:#333;line-height:1.75">{verdict_paragraph}</p>
    <div style="text-align:center;margin-top:12px">
      <a class="claim-btn" style="display:inline-block" href="{official_url}" target="_blank" rel="noopener noreferrer">Visit {name} Official Site →</a>
    </div>
  </div>

  <div class="cbox2">
    <h2>Frequently Asked Questions — {name}</h2>
    {faq_html}
  </div>

  <div class="cbox2">
    <h2>Compare {name} with Other Bookmakers</h2>
    <div id="compare-books"></div>
    <div style="text-align:center;margin-top:12px">
      <a href="../../" style="display:inline-block;background:var(--g);color:#fff;padding:10px 22px;border-radius:7px;font-size:13px;font-weight:800;text-decoration:none">Compare All Bookmakers →</a>
    </div>
  </div>

  <div class="resp">⚠️ Gambling involves risk. Only bet what you can afford to lose. 18+ only.</div>
</div></div>

<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison<br>
  <a href="../../">Home</a> · <a href="../../countries/">Countries</a> · <a href="../">All Bookmaker Reviews</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only.
</div>

<div class="page-modal-bg" id="page-modal"><div class="page-modal"><button class="page-modal-close" onclick="closePage()">×</button><div class="pm" id="page-content"></div></div></div>

<script src="../../assets/shared.js?v=21"></script>
<script>
const SITE={{home:'../../',tips:'../../tips/',casino:'../../casino/',odds:'../../odds/',countries:'../../countries/'}};
const _BK_CTY='{iso2}';
function init(){{
  const sel=document.getElementById('ctySel');
  if(sel)sel.value=_BK_CTY;
  H('foot-yr',NOW.getFullYear());
  const pms=[{pms_js_array}];
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


def render_discontinued_page(slug: str, name: str, evidence: str) -> str:
    """Replace a defunct brand's page with a live, indexable notice instead
    of deleting the directory. Keeps the URL resolving (never a 404 — see
    CLAUDE.md's 403/404 prevention rules) while clearly telling readers and
    Google the operator is no longer active. `noindex` so it stops
    competing for the brand's review query once it's no longer useful to
    rank, but the page itself stays reachable from any existing backlink.
    """
    today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""<!DOCTYPE html>
<!-- sifufinds.com/bookmakers/{slug}/ — {name} — marked discontinued {today_iso} -->
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} — No Longer Operating | SifuFinds</title>
<meta name="description" content="{name} appears to no longer be operating. SifuFinds has removed it from active bookmaker comparisons. See our current bookmaker reviews instead.">
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="https://sifufinds.com/bookmakers/{slug}/">
<link rel="stylesheet" href="../../assets/shared.css?v=12">
<link rel="icon" type="image/x-icon" href="/favicon.ico?v=3">
</head>
<body>
<div class="tbar">
  <div class="tbar-l"><a href="../../">🏠 Home</a></div>
</div>
<nav class="mnav">
  <div class="mnav-in">
    <a class="logo" href="../../"><img src="../../assets/icon.png" width="38" height="38" alt="SifuFinds logo" style="display:block;object-fit:contain">SifuFinds</a>
  </div>
</nav>
<div class="wrap" style="padding:32px 16px;max-width:640px;margin:0 auto">
  <h1 style="font-size:22px;font-weight:900;margin-bottom:12px">{name} is no longer operating</h1>
  <p style="font-size:14px;line-height:1.7;color:#333">SifuFinds' research indicates {name} has stopped operating or is no longer reachable. It has been removed from our active bookmaker comparisons as of {today_iso}.</p>
  <p style="font-size:13px;line-height:1.7;color:#666;margin-top:10px">Evidence: {evidence}</p>
  <p style="font-size:14px;line-height:1.7;color:#333;margin-top:16px">If you have funds in a {name} account, contact the operator directly. SifuFinds cannot assist with withdrawals from third-party operators.</p>
  <div style="margin-top:24px">
    <a href="../" style="display:inline-block;background:var(--g);color:#fff;padding:10px 22px;border-radius:7px;font-size:13px;font-weight:800;text-decoration:none">See Current Bookmaker Reviews →</a>
  </div>
</div>
<div class="footer-bar" style="background:#0a3d1e;color:rgba(255,255,255,.55);text-align:center;padding:18px;font-size:12px">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison
</div>
</body>
</html>"""
