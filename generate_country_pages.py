#!/usr/bin/env python3
"""Generate dedicated country landing pages for sifufinds.com."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COUNTRIES_DIR = os.path.join(BASE_DIR, 'countries')

YEAR = '2026'
MONTH_YEAR = 'June 2026'
DOMAIN = 'https://sifufinds.com'

COUNTRIES = {
    'NG': {
        'slug': 'nigeria', 'name': 'Nigeria', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦',
        'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'about': "Nigeria is Africa's largest and most active sports betting market with over 60 million registered bettors. The market is regulated by the National Lottery Regulatory Commission (NLRC) with state-level oversight. Football dominates, particularly the Nigerian Premier Football League (NPFL), UEFA Champions League, and English Premier League.",
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa', 'Mastercard', 'USSD'],
        'leagues': ['NPFL', 'CAF Champions League', 'Premier League', 'UEFA Champions League', 'AFCON'],
        'top_bonus': '₦1,200,000', 'top_bookmaker': '1xBet Nigeria', 'min_deposit': '₦100', 'books_count': 6,
    },
    'KE': {
        'slug': 'kenya', 'name': 'Kenya', 'flag': '🇰🇪',
        'currency': 'KES', 'symbol': 'KSh',
        'regulator': 'BCLB (Betting Control and Licensing Board)',
        'about': "Kenya has one of East Africa's most mature betting markets. The Betting Control and Licensing Board (BCLB) regulates all operators. M-Pesa is the dominant payment method. The Kenya Premier League (KPL) and SportPesa Premier League attract massive local betting interest.",
        'payments': ['M-Pesa', 'Airtel Money', 'Equitel', 'USSD *644#'],
        'leagues': ['Kenya Premier League', 'CAF Champions League', 'Premier League', 'AFCON', 'World Cup Qualifiers'],
        'top_bonus': 'KSh 30,000', 'top_bookmaker': 'Sportybet Kenya', 'min_deposit': 'KSh 10', 'books_count': 7,
    },
    'GH': {
        'slug': 'ghana', 'name': 'Ghana', 'flag': '🇬🇭',
        'currency': 'GHS', 'symbol': 'GH₵',
        'regulator': 'GCA (Gaming Commission of Ghana)',
        'about': "Ghana's betting industry is regulated by the Gaming Commission of Ghana (GCA). MTN MoMo and Vodafone Cash are the preferred deposit methods. The Ghana Premier League (GPL) sees significant local wagering activity alongside international competitions.",
        'payments': ['MTN MoMo', 'Vodafone Cash', 'AirtelTigo Money', 'Visa', 'Mastercard'],
        'leagues': ['Ghana Premier League', 'CAF Confederation Cup', 'Premier League', 'AFCON', 'World Cup Qualifiers'],
        'top_bonus': 'GH₵500', 'top_bookmaker': 'Betano Ghana', 'min_deposit': 'GH₵2', 'books_count': 5,
    },
    'ZA': {
        'slug': 'south-africa', 'name': 'South Africa', 'flag': '🇿🇦',
        'currency': 'ZAR', 'symbol': 'R',
        'regulator': 'WCGRB / NGB / ECGBB (Provincial Gambling Boards)',
        'about': "South Africa has the continent's most regulated betting environment, overseen by provincial gambling boards including the WCGRB and NGB. FICA verification is required for all accounts. Local favourites include the PSL (DStv Premiership), Springboks rugby, and cricket.",
        'payments': ['FNB', 'Standard Bank', 'Nedbank', 'Capitec', 'Visa', 'Mastercard', 'Instant EFT', 'Blue Voucher'],
        'leagues': ['DStv Premiership', 'Springboks Rugby', 'Proteas Cricket', 'CAF Champions League', 'Premier League'],
        'top_bonus': 'R1,500', 'top_bookmaker': 'Hollywoodbets', 'min_deposit': 'R5', 'books_count': 10,
    },
    'TZ': {
        'slug': 'tanzania', 'name': 'Tanzania', 'flag': '🇹🇿',
        'currency': 'TZS', 'symbol': 'TSh',
        'regulator': 'Gaming Board of Tanzania (GBT)',
        'about': "Tanzania's betting market is regulated by the Gaming Board of Tanzania. Mobile money via M-Pesa (Vodacom), Airtel Money, Tigo Pesa, and Halotel is the main payment route. The Tanzania Premier League and CAF competitions are the most wagered events.",
        'payments': ['M-Pesa (Vodacom)', 'Airtel Money', 'Tigo Pesa', 'Halotel Pesa', 'Bank Transfer'],
        'leagues': ['Tanzania Premier League', 'CAF Champions League', 'Premier League', 'AFCON'],
        'top_bonus': 'TSh 500,000', 'top_bookmaker': '1xBet Tanzania', 'min_deposit': 'TSh 200', 'books_count': 6,
    },
    'UG': {
        'slug': 'uganda', 'name': 'Uganda', 'flag': '🇺🇬',
        'currency': 'UGX', 'symbol': 'USh',
        'regulator': 'Uganda National Council for Sports (UNCS)',
        'about': "Uganda's sports betting sector is regulated by the Uganda National Council for Sports. MTN MoMo and Airtel Money Uganda dominate payments. The Uganda Premier League and African competitions drive the most betting activity.",
        'payments': ['MTN MoMo', 'Airtel Money', 'Bank Transfer', 'Visa', 'Mastercard'],
        'leagues': ['Uganda Premier League', 'CAF Confederation Cup', 'Premier League', 'AFCON'],
        'top_bonus': 'USh 1,000,000', 'top_bookmaker': '1xBet Uganda', 'min_deposit': 'USh 500', 'books_count': 5,
    },
    'ZM': {
        'slug': 'zambia', 'name': 'Zambia', 'flag': '🇿🇲',
        'currency': 'ZMW', 'symbol': 'ZK',
        'regulator': 'Gaming and Lotteries Board (GLB)',
        'about': "Zambia's betting industry is supervised by the Gaming and Lotteries Board. MTN MoMo Zambia and Airtel Money Zambia are the main mobile payment channels. The FAZ Super Division and CAF competitions are the most popular betting markets.",
        'payments': ['MTN MoMo Zambia', 'Airtel Money Zambia', 'Zamtel Mobile Money', 'Bank Transfer', 'Visa'],
        'leagues': ['FAZ Super Division', 'CAF Champions League', 'Premier League', 'AFCON'],
        'top_bonus': 'ZK 1,000', 'top_bookmaker': '1xBet Zambia', 'min_deposit': 'ZK 5', 'books_count': 5,
    },
    'ET': {
        'slug': 'ethiopia', 'name': 'Ethiopia', 'flag': '🇪🇹',
        'currency': 'ETB', 'symbol': 'Br',
        'regulator': 'National Lottery Administration (NLA)',
        'about': "Ethiopia is a fast-growing betting market. The National Lottery Administration oversees gambling. Commercial Bank of Ethiopia is the primary banking option. The Ethiopian Premier League is the most-bet local competition.",
        'payments': ['Commercial Bank of Ethiopia', 'Bank Transfer', 'Visa', 'Mastercard'],
        'leagues': ['Ethiopian Premier League', 'CAF Confederation Cup', 'Premier League', 'AFCON'],
        'top_bonus': 'Br 5,000', 'top_bookmaker': '1xBet Ethiopia', 'min_deposit': 'Br 50', 'books_count': 4,
    },
    'CI': {
        'slug': 'ivory-coast', 'name': 'Ivory Coast', 'flag': '🇨🇮',
        'currency': 'XOF', 'symbol': 'CFA',
        'regulator': "ARJEL CI (Autorité de Régulation des Jeux en Ligne)",
        'about': "Côte d'Ivoire has a well-established betting market underpinned by Orange Money and the local PMU network. Orange Bet and international operators compete for share. The Ligue 1 CI and CAF competitions dominate wagering.",
        'payments': ['Orange Money', 'MTN MoMo', 'Wave', 'Bank Transfer', 'Visa'],
        'leagues': ["Ligue 1 CI", 'CAF Champions League', 'Ligue 1 France', 'Premier League', 'AFCON'],
        'top_bonus': 'CFA 100,000', 'top_bookmaker': '1xBet Ivory Coast', 'min_deposit': 'CFA 500', 'books_count': 4,
    },
    'CM': {
        'slug': 'cameroon', 'name': 'Cameroon', 'flag': '🇨🇲',
        'currency': 'XAF', 'symbol': 'CFA',
        'regulator': 'Autorité des Marchés des Jeux (AMJ)',
        'about': "Cameroon's betting market is growing rapidly. Orange Money and MTN MoMo are the dominant payments. The MTN Elite One (local top flight) and AFCON — which Cameroon hosted in 2022 — are the biggest betting events.",
        'payments': ['Orange Money', 'MTN MoMo', 'Bank Transfer', 'Visa', 'Mastercard'],
        'leagues': ['MTN Elite One', 'CAF Champions League', 'Ligue 1 France', 'Premier League', 'AFCON'],
        'top_bonus': 'CFA 100,000', 'top_bookmaker': '1xBet Cameroon', 'min_deposit': 'CFA 500', 'books_count': 4,
    },
    'SN': {
        'slug': 'senegal', 'name': 'Senegal', 'flag': '🇸🇳',
        'currency': 'XOF', 'symbol': 'CFA',
        'regulator': 'Autorité de Régulation des Télécommunications et des Postes (ARTP)',
        'about': "Senegal's betting scene is growing quickly, driven by mobile money and a passionate football culture following AFCON 2022 glory. Wave and Orange Money are the main payment methods. The Ligue 1 Sénégal and European leagues attract most bettors.",
        'payments': ['Orange Money', 'Wave', 'MTN MoMo', 'Bank Transfer', 'Visa'],
        'leagues': ["Ligue 1 Sénégal", 'CAF Champions League', 'Ligue 1 France', 'Premier League', 'AFCON'],
        'top_bonus': 'CFA 100,000', 'top_bookmaker': '1xBet Senegal', 'min_deposit': 'CFA 500', 'books_count': 4,
    },
    'RW': {
        'slug': 'rwanda', 'name': 'Rwanda', 'flag': '🇷🇼',
        'currency': 'RWF', 'symbol': 'RWF',
        'regulator': 'Rwanda Gaming Commission (RGC)',
        'about': "Rwanda has a strictly regulated gaming environment overseen by the Rwanda Gaming Commission. MTN MoMo Rwanda and Airtel Money Rwanda are the primary payments. The Rwanda Premier League and East African club competitions drive local betting.",
        'payments': ['MTN MoMo Rwanda', 'Airtel Money Rwanda', 'Bank Transfer', 'Visa'],
        'leagues': ['Rwanda Premier League', 'CAF Confederation Cup', 'Premier League', 'AFCON'],
        'top_bonus': 'RWF 120,000', 'top_bookmaker': '1xBet Rwanda', 'min_deposit': 'RWF 500', 'books_count': 4,
    },
    'ZW': {
        'slug': 'zimbabwe', 'name': 'Zimbabwe', 'flag': '🇿🇼',
        'currency': 'USD', 'symbol': '$',
        'regulator': 'Lotteries and Gaming Board of Zimbabwe',
        'about': "Zimbabwe operates a USD-denominated betting market regulated by the Lotteries and Gaming Board. EcoCash (Econet) is the dominant mobile payment. The Zimbabwe Premier Soccer League (PSL) and regional African competitions are the most popular markets.",
        'payments': ['EcoCash (Econet)', 'OneMoney (NetOne)', 'Bank Transfer', 'Visa', 'Mastercard'],
        'leagues': ['Zimbabwe Premier Soccer League', 'CAF Champions League', 'Premier League', 'AFCON'],
        'top_bonus': '$500', 'top_bookmaker': '1xBet Zimbabwe', 'min_deposit': '$1', 'books_count': 5,
    },
    'MW': {
        'slug': 'malawi', 'name': 'Malawi', 'flag': '🇲🇼',
        'currency': 'MWK', 'symbol': 'MWK',
        'regulator': 'Malawi Gaming Board',
        'about': "Malawi's betting market is regulated by the Malawi Gaming Board. Airtel Money Malawi and TNM Mpamba are the main mobile payment options. The Super League of Malawi and regional competitions attract local bettors.",
        'payments': ['Airtel Money Malawi', 'TNM Mpamba', 'Bank Transfer', 'Visa'],
        'leagues': ['Super League of Malawi', 'CAF Confederation Cup', 'Premier League', 'AFCON'],
        'top_bonus': 'MWK 150,000', 'top_bookmaker': '1xBet Malawi', 'min_deposit': 'MWK 500', 'books_count': 3,
    },
    'MZ': {
        'slug': 'mozambique', 'name': 'Mozambique', 'flag': '🇲🇿',
        'currency': 'MZN', 'symbol': 'MZN',
        'regulator': 'Instituto para a Gestão das Apostas (IGA)',
        'about': "Mozambique's regulated betting market is overseen by the IGA. M-Pesa Mozambique (Vodacom) is the leading payment method. Hollywoodbets has a strong retail presence alongside digital operators. The Moçambola and CAF events dominate wagering.",
        'payments': ['M-Pesa Mozambique', 'e-Mola', 'Bank Transfer', 'Visa'],
        'leagues': ['Moçambola', 'CAF Champions League', 'Premier League', 'AFCON'],
        'top_bonus': 'MZN 5,000', 'top_bookmaker': '1xBet Mozambique', 'min_deposit': 'MZN 50', 'books_count': 3,
    },
    'AO': {
        'slug': 'angola', 'name': 'Angola', 'flag': '🇦🇴',
        'currency': 'AOA', 'symbol': 'AOA',
        'regulator': 'Instituto do Desporto (ID Angola)',
        'about': "Angola is an emerging betting market with growing smartphone penetration. Unitel Money and bank transfers are the main payment channels. The GiraBola (local top flight) and Portuguese Liga NOS attract most bettors.",
        'payments': ['Unitel Money', 'Bank Transfer', 'Visa', 'Mastercard'],
        'leagues': ['GiraBola', 'CAF Confederation Cup', 'Primeira Liga Portugal', 'Premier League'],
        'top_bonus': 'AOA 100,000', 'top_bookmaker': '1xBet Angola', 'min_deposit': 'AOA 500', 'books_count': 3,
    },
    'CD': {
        'slug': 'dr-congo', 'name': 'DR Congo', 'flag': '🇨🇩',
        'currency': 'CDF', 'symbol': 'CDF',
        'regulator': 'Autorité de Régulation des Jeux (ARJ)',
        'about': "The DRC is one of Africa's largest potential betting markets. M-Pesa DRC, Airtel Money DRC, and Orange Money serve mobile payments. The Linafoot (local top flight) and AFCON draw the most betting interest.",
        'payments': ['M-Pesa DRC (Vodacom)', 'Airtel Money DRC', 'Orange Money', 'Bank Transfer'],
        'leagues': ['Linafoot', 'CAF Champions League', 'Premier League', 'AFCON'],
        'top_bonus': 'CDF 200,000', 'top_bookmaker': '1xBet DRC', 'min_deposit': 'CDF 1,000', 'books_count': 3,
    },
    'BW': {
        'slug': 'botswana', 'name': 'Botswana', 'flag': '🇧🇼',
        'currency': 'BWP', 'symbol': 'BWP',
        'regulator': 'Gambling Authority of Botswana (GAB)',
        'about': "Botswana has a well-regulated betting market overseen by the Gambling Authority. FNB Botswana and Orange Money Botswana are the main payment channels. The Botswana Premier League and South African PSL attract most bettors.",
        'payments': ['FNB Botswana', 'Orange Money Botswana', 'Bank Transfer', 'Visa', 'Mastercard'],
        'leagues': ['Botswana Premier League', 'CAF Confederation Cup', 'DStv Premiership', 'Premier League'],
        'top_bonus': 'BWP 3,400', 'top_bookmaker': 'Melbet Botswana', 'min_deposit': 'BWP 2', 'books_count': 6,
    },
    'NA': {
        'slug': 'namibia', 'name': 'Namibia', 'flag': '🇳🇦',
        'currency': 'NAD', 'symbol': 'NAD',
        'regulator': 'Gambling Board of Namibia',
        'about': "Namibia's betting market mirrors South Africa, sharing currency parity with the ZAR. The Gambling Board of Namibia regulates operators. FNB Namibia and Standard Bank Namibia dominate banking. The NFA Premier League and South African PSL are popular.",
        'payments': ['FNB Namibia', 'Standard Bank Namibia', 'Bank Windhoek', 'Bank Transfer', 'Visa'],
        'leagues': ['NFA Premier League', 'CAF Confederation Cup', 'DStv Premiership', 'Premier League'],
        'top_bonus': 'NAD 4,500', 'top_bookmaker': 'Melbet Namibia', 'min_deposit': 'NAD 5', 'books_count': 6,
    },
}

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
      <option value="NA">🇳🇦 Namibia · NAD</option>"""


def make_faqs(c):
    name = c['name']
    regulator = c['regulator']
    payments = c['payments']
    top_book = c['top_bookmaker']
    top_bonus = c['top_bonus']
    min_dep = c['min_deposit']
    leagues = c['leagues']

    pay_str = ', '.join(payments[:3])
    league_str = ', '.join(leagues[:3])

    return [
        {
            'q': f'Is online betting legal in {name}?',
            'a': f'Yes. Sports betting is legal and regulated in {name}. The licensing authority is the <strong>{regulator}</strong>. All bookmakers listed on SifuFinds hold valid licences for the {name} market — we only list fully licensed operators.',
        },
        {
            'q': f'What payment methods can I use at {name} betting sites?',
            'a': f'The most popular deposit and withdrawal methods at {name} betting sites include {pay_str}. Most licensed bookmakers process withdrawals within 24 hours to mobile money accounts.',
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
            'a': f'The most popular betting markets in {name} include {league_str}. Football is the dominant sport, with both local leagues and international competitions attracting high betting volumes.',
        },
    ]


def faq_schema_json(faqs):
    items = []
    for f in faqs:
        a_text = f['a'].replace('<strong>', '').replace('</strong>', '').replace('"', '\\"')
        q_text = f['q'].replace('"', '\\"')
        items.append(f'''        {{
          "@type": "Question",
          "name": "{q_text}",
          "acceptedAnswer": {{"@type": "Answer", "text": "{a_text}"}}
        }}''')
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
    title = f'Best Betting Sites in {name} {YEAR} | Licensed Bookmakers | SifuFinds'
    canonical = f'{DOMAIN}/countries/{slug}/'
    h1 = f'Best Betting Sites in {name} &middot; {MONTH_YEAR}'

    return f"""<!DOCTYPE html>
<!-- sifufinds.com/countries/{slug}/ – Best Betting Sites in {name} {YEAR} -->
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{meta_desc}">
<meta name="keywords" content="betting sites {name.lower()}, best bookmakers {name.lower()}, {name.lower()} betting bonuses {YEAR}, online betting {name.lower()}, {key_payment.lower()} betting">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="author" content="SifuFinds">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="en" href="{canonical}">
<link rel="alternate" hreflang="en-{code}" href="{canonical}">

<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="Best Betting Sites in {name} {YEAR} | SifuFinds">
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
<meta name="twitter:title" content="Best Betting Sites in {name} {YEAR} | SifuFinds">
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
      "name": "{title}",
      "description": "{meta_desc}",
      "url": "{canonical}",
      "inLanguage": "en-GB",
      "isPartOf": {{"@id": "{DOMAIN}/#website"}}
    }},
    {{
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Home", "item": "{DOMAIN}/"}},
        {{"@type": "ListItem", "position": 2, "name": "Countries", "item": "{DOMAIN}/countries/"}},
        {{"@type": "ListItem", "position": 3, "name": "{name} Betting Sites", "item": "{canonical}"}}
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

<link rel="icon" href="../../assets/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="../../assets/favicon.png">
<link rel="preload" href="../../assets/shared.css" as="style">
<link rel="stylesheet" href="../../assets/shared.css">
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
</style>
</head>
<body>

<!-- TOP BAR -->
<div class="tbar">
  <div class="tbar-l">
    <a href="../../">🏠 Home</a>
    <a href="../">🌍 Africa</a>
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

<!-- MAIN NAV -->
<nav class="mnav">
  <div class="mnav-in">
    <a class="logo" href="../../">
      <img src="../../assets/icon.png" height="38" alt="SifuFinds logo" style="display:block;object-fit:contain">
      SifuFinds
    </a>
    <div class="ntabs">
      <a class="nt" href="../../">⭐ Best Bonuses</a>
      <a class="nt" href="../../tips/">💡 Tips</a>
      <a class="nt" href="../../casino/">🎰 Casino</a>
      <a class="nt" href="../../odds/">📊 Live Odds<span class="lpulse" style="margin-left:4px"></span></a>
      <a class="nt on" href="../">🌍 Countries</a>
      <a class="nt" href="../../blog/">📰 Blog</a>
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

<!-- MAIN CONTENT -->
<div class="sec-bg"><div class="wrap">
  <div class="breadcrumb">
    <a href="../../">Home</a><span>›</span><a href="../">Countries</a><span>›</span>{name} Betting Sites
  </div>

  <div class="adv">📢 <strong>Advertiser Disclosure:</strong> We may earn commission from bookmaker links. All bonuses independently verified. Always check the bookmaker's official site for current T&amp;Cs.</div>

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
    <noscript><p style="padding:20px;color:#666">Enable JavaScript to view bookmaker listings, or visit <a href="../../">SifuFinds.com</a>.</p></noscript>
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
    <button onclick="openPage('responsible')">GamCare</button> ·
    <button onclick="openPage('responsible')">BeGambleAware</button> ·
    <button onclick="openPage('responsible')">NCPG Africa</button>. 18+ only.
  </div>
</div></div>

<!-- FOOTER -->
<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison · <span id="foot-date"></span><br>
  <a href="../../">Home</a> · <a href="../">All Countries</a> · <a href="../../tips/">Tips</a> · <a href="../../casino/">Casino</a> · <a href="../../odds/">Odds</a> · <a href="../../blog/">Blog</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only. Gambling can be addictive. Play responsibly.
</div>

<!-- PAGE MODAL -->
<div class="page-modal-bg" id="page-modal">
  <div class="page-modal">
    <button class="page-modal-close" onclick="closePage()">×</button>
    <div class="pm" id="page-content"></div>
  </div>
</div>

<script src="../../assets/shared.js"></script>
<script>
const SITE={{home:'../../',tips:'../../tips/',casino:'../../casino/',odds:'../../odds/',countries:'../'
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
      <a class="gbtn${{b.nodep?' gold':''}}" href="${{b.url}}" target="_blank" rel="noopener noreferrer">Claim Bonus →</a>
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
    <a class="gbtn" href="${{b.url}}" target="_blank" rel="noopener noreferrer">Claim Bonus →</a>
  </div>
</div>`;
}};

function renderBooks(){{
  const books=filterBooks(sortBooks(BOOKS[_PAGE_CTY]||[]));
  const el=document.getElementById('bk-cards');
  if(!books.length){{el.innerHTML='<div class="no-results">No bookmakers match this filter.</div>';return;}}
  el.innerHTML=books.map((b,i)=>bookCard(b,i,i)).join('');
  H('mcount',`Showing ${{books.length}} bookmaker${{books.length!==1?'s':''}}`);
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


if __name__ == '__main__':
    created = 0
    for code, country in COUNTRIES.items():
        slug = country['slug']
        out_dir = os.path.join(COUNTRIES_DIR, slug)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'index.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(generate_page(code, country))
        print(f'  ✓  /countries/{slug}/')
        created += 1

    print(f'\n✅ Generated {created} country pages')
