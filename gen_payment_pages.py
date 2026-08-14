#!/usr/bin/env python3
"""Generate new payment method pages: EcoCash, Orange Money, Vodacom, bank transfer."""

import json
import os
from seo_meta import seo_title, seo_meta_description

BASE = os.path.dirname(os.path.abspath(__file__))

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
        'slug': 'ecocash-betting',
        'path': 'betting/ecocash-betting',
        'title': 'Best EcoCash Betting Sites 2026 | Bet with EcoCash Zimbabwe | SifuFinds',
        'desc': 'Best EcoCash betting sites in Zimbabwe 2026. Deposit and withdraw instantly via EcoCash at licensed BCLB-regulated bookmakers. Minimum deposit from $1. Verified offers updated daily.',
        'keywords': 'EcoCash betting sites, bet with EcoCash Zimbabwe, EcoCash bookmakers 2026, EcoCash sportsbook Zimbabwe, best betting EcoCash, Econet betting Zimbabwe, EcoCash deposit withdrawal betting',
        'og_title': 'Best EcoCash Betting Sites 2026 | SifuFinds',
        'h1': 'Best EcoCash Betting Sites in Zimbabwe &middot; 2026',
        'geo_region': 'ZW',
        'geo_place': 'Zimbabwe',
        'hreflang_extra': '<link rel="alternate" hreflang="en-ZW" href="https://sifufinds.com/betting/ecocash-betting/">',
        'icon': '📱',
        'color': '#e74c3c',
        'intro': "<strong>EcoCash</strong> is Zimbabwe's dominant mobile money service, operated by Econet Wireless and used by over 8 million Zimbabweans. EcoCash is accepted at all major BCLB-licensed betting sites in Zimbabwe for instant deposits and withdrawals. You can fund your betting account by dialling <strong>*151*2*1#</strong> or via the EcoCash app — no bank account required. Minimum betting deposits start from as little as US$1.",
        'step_title': 'How to Bet with EcoCash in Zimbabwe',
        'steps': [
            ('Register', 'Sign up at a BCLB-licensed bookmaker (Betway Zimbabwe, Sportybet Zimbabwe, or 1xBet Zimbabwe). Verify your identity with your national ID or passport.'),
            ('Select EcoCash as payment', 'Go to the Deposit section and choose EcoCash from the payment options. Enter your EcoCash-registered phone number.'),
            ('Confirm via *151#', 'You will receive a prompt on your phone. Dial *151*2*1# or use the EcoCash app to approve the transaction. Enter your EcoCash PIN.'),
            ('Start betting', 'Your account is funded instantly. Place your first bet on the Castle Lager PSL, Premier League, AFCON, or any available market.'),
        ],
        'countries': ['Zimbabwe — all BCLB-licensed bookmakers'],
        'faq': [
            ('Which betting sites accept EcoCash in Zimbabwe?', "All major BCLB-licensed betting sites in Zimbabwe accept EcoCash, including Betway Zimbabwe, Sportybet Zimbabwe, 1xBet Zimbabwe, TopBet Zimbabwe, and BetZim. EcoCash is the most widely accepted payment method in Zimbabwe's legal betting market."),
            ('What is the minimum EcoCash deposit for betting?', "The minimum EcoCash deposit at most Zimbabwean betting sites is US$1 (approximately RTGS equivalent). Some bookmakers require US$2 or US$5 as a minimum. All deposits process instantly at no extra charge from the bookmaker — though Econet may apply a small transaction fee."),
            ('How do I withdraw winnings to EcoCash?', "To withdraw: go to the Withdrawal section in your betting account, select EcoCash, enter your registered EcoCash number, and the amount. Most bookmakers process EcoCash withdrawals within 24 hours. Some instant withdrawals are available. Minimum withdrawal is typically US$2–US$5."),
            ('Is EcoCash betting safe in Zimbabwe?', "Yes — all EcoCash betting sites listed on SifuFinds are licensed by the BCLB (Betting Control and Licensing Board) Zimbabwe. Your EcoCash transactions are also protected by Econet's own security. Never share your EcoCash PIN with anyone, and always use the official bookmaker website or app."),
        ],
        'schema_name': 'Best EcoCash Betting Sites 2026',
        'schema_desc': 'Best licensed betting sites accepting EcoCash deposits and withdrawals in Zimbabwe.',
        'canonical_path': 'betting/ecocash-betting',
        'breadcrumb_name': 'EcoCash Betting',
        'assets': '../../',
    },
    {
        'slug': 'orange-money-betting',
        'path': 'betting/orange-money-betting',
        'title': 'Best Orange Money Betting Sites 2026 | Bet with Orange Money Africa | SifuFinds',
        'desc': 'Best betting sites accepting Orange Money in Ivory Coast, Senegal, Cameroon, Morocco, Botswana and more. Instant deposits and withdrawals via Orange Money at licensed bookmakers. Updated daily.',
        'keywords': 'Orange Money betting sites, bet with Orange Money Africa, Orange Money sportsbook, Orange Money bookmaker Ivory Coast, Orange Money betting Senegal, Orange Money Cameroon betting, Orange Money Morocco betting 2026',
        'og_title': 'Best Orange Money Betting Sites Africa 2026 | SifuFinds',
        'h1': 'Best Orange Money Betting Sites in Africa &middot; 2026',
        'geo_region': 'CI',
        'geo_place': 'West Africa',
        'hreflang_extra': '<link rel="alternate" hreflang="en-CI" href="https://sifufinds.com/betting/orange-money-betting/">\n<link rel="alternate" hreflang="fr-SN" href="https://sifufinds.com/betting/orange-money-betting/">',
        'icon': '🟠',
        'color': '#e67e22',
        'intro': "<strong>Orange Money</strong> is the largest mobile money network across francophone Africa, operating in Ivory Coast, Senegal, Cameroon, DRC, Botswana, Sierra Leone, Liberia, and 12 other African countries. Orange Money is accepted at licensed betting sites across all these markets for instant deposits and withdrawals. No bank account is required — just your Orange SIM card.",
        'step_title': 'How to Bet with Orange Money in Africa',
        'steps': [
            ('Register at a licensed bookmaker', 'Sign up at an Orange Money-accepting bookmaker for your country. Betway, 1xBet, and Sportybet accept Orange Money across multiple African markets.'),
            ('Select Orange Money as deposit method', 'In the Deposit section, choose Orange Money. Enter your Orange-registered phone number and the deposit amount.'),
            ('Confirm via USSD or Orange Money app', 'You\'ll receive a payment prompt. Confirm via the Orange Money app or dial *144# (varies by country). Enter your Orange Money PIN.'),
            ('Funds credited instantly', 'Your betting account is funded instantly. Place bets on AFCON, CAF Champions League, Premier League, and more.'),
        ],
        'countries': [
            'Ivory Coast — licensed bookmakers accepting Orange Money',
            'Senegal — ARJ-licensed operators',
            'Cameroon — ARJ-licensed operators',
            'DR Congo — ARJH-licensed operators',
            'Botswana — GAB-licensed operators',
            'Sierra Leone — NLA-SL-licensed operators',
            'Liberia — GCC-licensed operators',
            'Morocco — MDJS-licensed operators',
        ],
        'faq': [
            ('Which countries can use Orange Money for betting?', "Orange Money is available for betting in: Ivory Coast, Senegal, Cameroon, DRC, Botswana, Sierra Leone, Liberia, Morocco, Guinea, Mali, Madagascar, and more. The full list of accepted bookmakers per country is available on SifuFinds' country pages. All listed bookmakers are licensed by the local gambling authority."),
            ('How do I deposit via Orange Money for betting?', "Go to the Deposit section of your bookmaker account. Select Orange Money, enter your registered Orange phone number and amount. You'll receive an authorization prompt via the Orange Money app or USSD. Confirm with your PIN. Funds are credited instantly to your betting account."),
            ('What is the minimum Orange Money deposit for betting?', "Minimum Orange Money deposits vary by country and bookmaker: typically 500–1,000 XOF in Ivory Coast/Senegal/Cameroon, equivalent to approximately $1 USD. 1xBet and Betway accept the lowest minimums. All deposits are instant with no bookmaker-side fees."),
            ('Can I withdraw betting winnings to Orange Money?', "Yes. Most bookmakers that accept Orange Money deposits also support withdrawals to Orange Money. Withdrawal processing time is typically 15 minutes to 24 hours. Minimum withdrawals are usually the same as minimum deposits. Some bookmakers require identity verification before the first withdrawal."),
        ],
        'schema_name': 'Best Orange Money Betting Sites Africa 2026',
        'schema_desc': 'Best licensed betting sites accepting Orange Money in Ivory Coast, Senegal, Cameroon, DRC, Morocco, Botswana and more.',
        'canonical_path': 'betting/orange-money-betting',
        'breadcrumb_name': 'Orange Money Betting',
        'assets': '../../',
    },
    {
        'slug': 'vodacom-betting',
        'path': 'betting/vodacom-betting',
        'title': 'Best Vodacom Betting Sites 2026 | Vodacom M-Pesa & Cash Tanzania & SA | SifuFinds',
        'desc': 'Best betting sites accepting Vodacom M-Pesa in Tanzania and Vodacom Cash in South Africa 2026. Instant deposits at licensed bookmakers. Verified offers updated daily.',
        'keywords': 'Vodacom betting sites, Vodacom M-Pesa betting Tanzania, Vodacom Cash betting South Africa, bet with Vodacom Tanzania, Vodacom sportsbook Africa 2026, *150*00# betting Tanzania',
        'og_title': 'Best Vodacom Betting Sites 2026 | SifuFinds',
        'h1': 'Best Vodacom Betting Sites in Africa &middot; 2026',
        'geo_region': 'TZ',
        'geo_place': 'Tanzania',
        'hreflang_extra': '<link rel="alternate" hreflang="en-TZ" href="https://sifufinds.com/betting/vodacom-betting/">\n<link rel="alternate" hreflang="en-ZA" href="https://sifufinds.com/betting/vodacom-betting/">',
        'icon': '📡',
        'color': '#e74c3c',
        'intro': "<strong>Vodacom</strong> operates M-Pesa in Tanzania (and Mozambique) under the Vodacom brand, and provides mobile financial services in South Africa. In Tanzania, Vodacom M-Pesa (*150*00#) is the most popular betting payment method, used by millions to deposit at GBT-licensed bookmakers. In South Africa, Vodacom subscribers can use linked bank accounts and voucher systems at WCGRB-licensed bookmakers.",
        'step_title': 'How to Deposit via Vodacom M-Pesa in Tanzania',
        'steps': [
            ('Register at a GBT-licensed bookmaker', 'Sign up at Sportybet Tanzania, 1xBet Tanzania, or Betway Tanzania. All accept Vodacom M-Pesa.'),
            ('Select M-Pesa (Vodacom) deposit', 'In the Deposit section, choose M-Pesa and enter your Vodacom Tanzania phone number and deposit amount.'),
            ('Dial *150*00# on your Vodacom line', 'Enter your M-Pesa PIN to confirm. The transaction is processed via Vodacom\'s M-Pesa platform.'),
            ('Start betting', 'Funds are available instantly. Bet on the Tanzania Premier League, AFCON, or the Premier League.'),
        ],
        'countries': [
            'Tanzania — Vodacom M-Pesa at GBT-licensed bookmakers',
            'Mozambique — Vodacom M-Pesa at IJM-licensed bookmakers',
            'South Africa — Vodacom subscribers at WCGRB-licensed bookmakers',
        ],
        'faq': [
            ('Is Vodacom M-Pesa different from Safaricom M-Pesa?', "Yes. While they share the M-Pesa brand, they operate independently. Safaricom M-Pesa is used in Kenya (dialling *644#). Vodacom M-Pesa is used in Tanzania (*150*00#) and Mozambique. Both work for betting deposits at licensed bookmakers in their respective countries. SifuFinds has separate pages for each market."),
            ('Which bookmakers accept Vodacom M-Pesa in Tanzania?', "All major GBT-licensed bookmakers in Tanzania accept Vodacom M-Pesa including Sportybet Tanzania, 1xBet Tanzania, Betway Tanzania, Betika Tanzania, and Parimatch Tanzania. The minimum deposit is typically TSh 1,000 (approximately US$0.40) and funds are credited instantly."),
            ('Can I withdraw to Vodacom M-Pesa in Tanzania?', "Yes. All major Tanzanian bookmakers support Vodacom M-Pesa withdrawals. Processing time is usually instant to 4 hours. Minimum withdrawal is typically TSh 1,000. You must have a verified account (national ID or passport) before making your first withdrawal."),
            ('Does Vodacom charge fees for betting deposits?', "Vodacom M-Pesa applies standard transaction fees for sending money — similar to any M-Pesa transaction. Most bookmakers do not charge additional deposit fees on their end. Always check the current Vodacom Tanzania tariff guide for the exact fee scale. Small transactions under TSh 5,000 may have different fee structures."),
        ],
        'schema_name': 'Best Vodacom Betting Sites 2026',
        'schema_desc': 'Best licensed betting sites accepting Vodacom M-Pesa in Tanzania and Mozambique, and Vodacom services in South Africa.',
        'canonical_path': 'betting/vodacom-betting',
        'breadcrumb_name': 'Vodacom Betting',
        'assets': '../../',
    },
    {
        'slug': 'bank-transfer-betting',
        'path': 'betting/bank-transfer-betting',
        'title': 'Best Bank Transfer Betting Sites Africa 2026 | All African Banks Accepted | SifuFinds',
        'desc': 'Best betting sites accepting bank transfers in Nigeria, Kenya, South Africa, Ghana, Egypt, Morocco and more. Direct bank deposits at licensed African bookmakers. Updated daily.',
        'keywords': 'bank transfer betting sites Africa, bank deposit betting Nigeria, bank transfer bookmaker Kenya, online banking betting South Africa, bank betting Ghana, IBAN betting Africa 2026, bank wire betting Africa',
        'og_title': 'Best Bank Transfer Betting Sites Africa 2026 | SifuFinds',
        'h1': 'Best Bank Transfer Betting Sites in Africa &middot; 2026',
        'geo_region': 'NG',
        'geo_place': 'Africa',
        'hreflang_extra': '',
        'icon': '🏦',
        'color': '#2c3e50',
        'intro': "<strong>Bank transfer</strong> is the most universal payment method at African betting sites, available at licensed bookmakers across SifuFinds' 33 African countries where a bookmaker operates. Whether you bank with Access Bank, GTBank, KCB, Standard Bank, Absa, CIH Banque, or any other African bank, you can make betting deposits directly from your account. Bank transfers are ideal for larger deposits where mobile money limits apply.",
        'step_title': 'How to Deposit via Bank Transfer at African Bookmakers',
        'steps': [
            ('Get the bookmaker\'s bank account details', 'After selecting Bank Transfer in the Deposit section, the bookmaker will provide a dedicated bank account number and reference code. Note the exact reference — it is essential for your deposit to be matched.'),
            ('Make the transfer from your bank', 'Log in to your internet banking, mobile banking app, or visit a bank branch. Enter the bookmaker\'s account details and your unique reference. The minimum is usually ₦1,000 / KSh 200 / R100.'),
            ('Wait for credit confirmation', 'Bank transfers take longer than mobile money: 30 minutes to 24 hours in most cases (instant at bookmakers using direct API connections like GTBank and Access Bank in Nigeria). Most bookmakers send an SMS/email when the deposit is confirmed.'),
            ('Start betting', 'Once credited, place bets on any available market. Bank transfers are best for larger amounts above mobile money transaction limits.'),
        ],
        'countries': [
            'Nigeria — GTBank, Access Bank, First Bank, Zenith, UBA at NLRC-licensed bookmakers',
            'Kenya — KCB, Equity Bank, Co-op Bank at BCLB-licensed bookmakers',
            'South Africa — FNB, ABSA, Capitec, Standard Bank, Nedbank at WCGRB-licensed bookmakers',
            'Ghana — GCB Bank, MTN, Fidelity Bank at GCA-licensed bookmakers',
            'Egypt — National Bank of Egypt, CIB, Banque Misr',
            'Morocco — CIH Bank, Attijariwafa Bank, BMCE at MDJS-licensed operators',
            'All 33 African countries SifuFinds covers — local bank options available at each licensed bookmaker',
        ],
        'faq': [
            ('How long does a bank transfer deposit take at African bookmakers?', "It depends on the country and bookmaker. In Nigeria: instant with GTBank/Access Bank API integration, 30 min–4 hours otherwise. In Kenya: 15 min–2 hours via direct bank API. South Africa: instant with FNB/Capitec, 1–24 hours for other banks. Morocco and Egypt: 1–24 hours via standard wire. Bank transfers are slower than mobile money but support larger amounts."),
            ('Is there a maximum deposit via bank transfer?', "Bank transfer deposits have the highest limits of any payment method. Most African bookmakers cap bank transfer deposits at ₦5,000,000 (Nigeria) or KSh 500,000 (Kenya) per transaction. There is no government-imposed upper limit for bank transfers to licensed bookmakers — only the bookmaker's own limits apply."),
            ('Can I withdraw to my bank account from African bookmakers?', "Yes. Bank transfer withdrawals are supported at all licensed African bookmakers. This is typically the preferred withdrawal method for large amounts. Processing time is 24–72 hours. You must have a verified account and the bank account must be in your own name to prevent fraud. Most bookmakers require a one-time bank account verification before the first withdrawal."),
            ('Is bank transfer betting safe in Africa?', "Yes — bank transfers to NLRC, BCLB, WCGRB, or other licensed African bookmakers are safe. Always verify you are on the official bookmaker website before transferring. Never transfer to a personal phone number or untraceable account — legitimate bookmakers provide corporate bank account details. All bookmakers on SifuFinds are licensed and hold valid operator accounts."),
        ],
        'schema_name': 'Best Bank Transfer Betting Sites Africa 2026',
        'schema_desc': 'Best licensed betting sites accepting direct bank transfer deposits across Africa including Nigeria, Kenya, South Africa, Ghana, Egypt, and Morocco.',
        'canonical_path': 'betting/bank-transfer-betting',
        'breadcrumb_name': 'Bank Transfer Betting',
        'assets': '../../',
    },
    {
        'slug': 'telebirr-betting',
        'path': 'betting/telebirr-betting',
        'title': 'Best Telebirr Betting Sites 2026 | Bet with Telebirr Ethiopia | SifuFinds',
        'desc': 'Best Telebirr betting sites in Ethiopia 2026. Deposit and withdraw instantly via Telebirr (Ethio Telecom) at NLA-licensed bookmakers. Updated daily.',
        'keywords': 'Telebirr betting sites, bet with Telebirr Ethiopia, Telebirr bookmakers 2026, Telebirr sportsbook Ethiopia, Ethio Telecom betting, Telebirr sports betting, CBE Birr betting Ethiopia',
        'og_title': 'Best Telebirr Betting Sites 2026 | SifuFinds',
        'h1': 'Best Telebirr Betting Sites in Ethiopia &middot; 2026',
        'geo_region': 'ET',
        'geo_place': 'Ethiopia',
        'hreflang_extra': '<link rel="alternate" hreflang="en-ET" href="https://sifufinds.com/betting/telebirr-betting/">',
        'icon': '🇪🇹',
        'color': '#27ae60',
        'intro': "<strong>Telebirr</strong> is Ethiopia's leading mobile money platform, operated by Ethio Telecom — the state telecom provider with 70+ million subscribers. Launched in 2021, Telebirr has become Ethiopia's most widely used digital payment method with over 40 million registered users. Telebirr is now accepted at NLA-licensed betting sites in Ethiopia for instant deposits and withdrawals.",
        'step_title': 'How to Bet with Telebirr in Ethiopia',
        'steps': [
            ('Register at an NLA-licensed bookmaker', 'Sign up at 1xBet Ethiopia, Betway Ethiopia, or Melbet Ethiopia — all accept Telebirr deposits.'),
            ('Select Telebirr as your deposit method', 'Go to the Deposit section and choose Telebirr. Enter your Ethio Telecom number and the deposit amount.'),
            ('Confirm via Telebirr app or *127#', 'Open the Telebirr app or dial *127# to authorize the payment. Enter your Telebirr PIN to confirm.'),
            ('Place your bets', 'Funds are credited instantly. Bet on the Ethiopian Premier League, AFCON, or Premier League.'),
        ],
        'countries': ['Ethiopia — NLA-licensed bookmakers accepting Telebirr'],
        'faq': [
            ('Which bookmakers accept Telebirr in Ethiopia?', "Telebirr is accepted by 1xBet Ethiopia, Betway Ethiopia, Melbet Ethiopia, and a growing number of NLA-licensed local bookmakers. As Telebirr expands its API to more partners, coverage is increasing rapidly. All bookmakers listed on SifuFinds' Ethiopia page are licensed by the National Lottery Administration (NLA)."),
            ('What is the minimum Telebirr deposit for betting?', "Most Ethiopian bookmakers accept Telebirr deposits from as little as ETB 50–ETB 100 (approximately USD 1). Deposits are processed instantly. Telebirr charges a small transaction fee — check the current Ethio Telecom tariff for exact amounts."),
            ('Is Telebirr the same as CBE Birr?', "No — they are different services. Telebirr is operated by Ethio Telecom. CBE Birr is operated by the Commercial Bank of Ethiopia (CBE). Both are digital payment wallets accepted at Ethiopian betting sites, but they use different infrastructure and registration processes. Most bookmakers accept both."),
            ('Can I withdraw to Telebirr from betting sites?', "Yes. NLA-licensed bookmakers in Ethiopia support Telebirr withdrawals. Processing time is typically 15 minutes to 24 hours. You must pass identity verification (national ID) before your first withdrawal. Minimum withdrawal is typically ETB 100."),
        ],
        'schema_name': 'Best Telebirr Betting Sites 2026',
        'schema_desc': 'Best NLA-licensed betting sites in Ethiopia accepting Telebirr deposits and withdrawals.',
        'canonical_path': 'betting/telebirr-betting',
        'breadcrumb_name': 'Telebirr Betting',
        'assets': '../../',
    },
]


def make_payment_page(p):
    faq_items = '\n'.join(f"""    <div class="faq-item">
      <button class="faq-q" onclick="this.parentElement.classList.toggle('open')">{q} <span class="faq-arr">▼</span></button>
      <div class="faq-a"><p>{a}</p></div>
    </div>""" for q, a in p['faq'])

    step_items = '\n'.join(
        f'    <li><strong>{i+1}. {t}</strong> — {d}</li>'
        for i, (t, d) in enumerate(p['steps'])
    )

    countries_items = '\n'.join(f'    <li>{c}</li>' for c in p['countries'])

    faq_schema = ',\n'.join(
        json.dumps({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a},
        })
        for q, a in p['faq']
    )

    howto_steps_json = ', '.join(
        json.dumps({"@type": "HowToStep", "name": t, "text": d})
        for t, d in p['steps']
    )

    ap = p['assets']

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
{p['hreflang_extra']}
<meta name="geo.region" content="{p['geo_region']}">
<meta name="geo.placename" content="{p['geo_place']}">

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
      "isPartOf": {{"@id": "https://sifufinds.com/#website"}},
      "about": [
        {{"@type": "Thing", "name": "{p['breadcrumb_name']}"}},
        {{"@type": "Thing", "name": "Sports Betting"}},
        {{"@type": "Thing", "name": "Mobile Money Betting"}}
      ]
    }},
    {{
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://sifufinds.com/"}},
        {{"@type": "ListItem", "position": 2, "name": "Betting Guides", "item": "https://sifufinds.com/betting/"}},
        {{"@type": "ListItem", "position": 3, "name": "{p['breadcrumb_name']}", "item": "https://sifufinds.com/{p['canonical_path']}/"}}
      ]
    }},
    {{
      "@type": "FAQPage",
      "mainEntity": [{faq_schema}]
    }},
    {{
      "@type": "HowTo",
      "name": "{p['step_title']}",
      "step": [{howto_steps_json}]
    }}
  ]
}}
</script>

<link rel="icon" type="image/x-icon" href="/favicon.ico?v=3">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32x32.png?v=3">
<link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16x16.png?v=2">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png?v=3">
<link rel="preload" href="{ap}assets/shared.css?v=12" as="style">
<link rel="stylesheet" href="{ap}assets/shared.css?v=12">
<style>
.pay-badge{{display:inline-block;background:#edf7f0;border:1px solid #c8e6c9;border-radius:6px;padding:5px 14px;font-size:12px;font-weight:700;color:{p['color']};margin-bottom:10px}}
.how-steps{{list-style:none;padding:0;margin:0;counter-reset:steps}}
.how-steps li{{counter-increment:steps;padding:10px 0 10px 44px;position:relative;border-bottom:1px solid #f0f0f0;font-size:13px;color:#444;line-height:1.6}}
.how-steps li:last-child{{border:none}}
.how-steps li::before{{content:counter(steps);position:absolute;left:0;top:10px;width:28px;height:28px;background:{p['color']};color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800}}
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
    <a href="{ap}betting/">💳 Payment Methods</a>
    <a href="{ap}responsible/">Responsible Gambling</a>
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
    <a class="logo" href="{ap}"><img src="{ap}assets/icon.png" width="38" height="38" alt="SifuFinds logo" style="display:block;object-fit:contain">SifuFinds</a>
    <div class="ntabs">
      <a class="nt on" href="{ap}">⭐ Best Bonuses</a>
      <a class="nt" href="{ap}tips/">💡 Tips</a>
      <a class="nt" href="{ap}casino/">🎰 Casino</a>
      <a class="nt" href="{ap}odds/">📊 Live Odds<span class="lpulse" style="margin-left:4px"></span></a>
      <a class="nt" href="{ap}countries/">🌍 Countries</a>
      <a class="nt" href="{ap}blog/">📰 Blog</a>
    </div>
  </div>
</nav>

<div id="hbrands" class="hbrands"></div>

<div class="hero"><div class="wrap">
  <h1>{p['icon']} {p['h1']}</h1>
  <p>{p['intro']}</p>
  <div class="trust">
    <div class="tb">⚡ Instant Deposits</div>
    <div class="tb">✅ Licensed Bookmakers</div>
    <div class="tb">🔄 Updated Daily</div>
    <div class="tb">🏛 Regulated</div>
  </div>
</div></div>

<div class="sec-bg"><div class="wrap">
  <div class="breadcrumb">
    <a href="{ap}">Home</a><span>›</span><a href="{ap}betting/">Payment Methods</a><span>›</span>{p['breadcrumb_name']}
  </div>

  <div class="adv">📢 <strong>Advertiser Disclosure:</strong> We earn commission from some bookmaker links. All bonuses verified. Check T&Cs. 18+.</div>

  <div class="cbox2">
    <h2>{p['step_title']}</h2>
    <ol class="how-steps">
{step_items}
    </ol>
  </div>

  <div class="cbox2">
    <h2>Countries Where {p['breadcrumb_name']} is Available</h2>
    <ul style="padding-left:18px;margin:0;font-size:13px;color:#444;line-height:2">
{countries_items}
    </ul>
  </div>

  <div class="sec-lbl" style="font-size:11px;font-weight:700;color:#aaa;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">LICENSED BOOKMAKERS · ACCEPTING {p['breadcrumb_name'].upper()} · 2026</div>
  <h2 style="font-size:17px;font-weight:800;color:#111;margin-bottom:9px">Top Bookmakers Accepting {p['breadcrumb_name']}</h2>

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
    <h2>FAQ — {p['breadcrumb_name']}</h2>
{faq_items}
  </div>

  <div class="resp">⚠️ Gambling involves risk. Only bet what you can afford to lose. 18+ only.</div>
</div></div>

<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison<br>
  <a href="{ap}">Home</a> · <a href="{ap}betting/">Payment Methods</a> · <a href="{ap}countries/">Countries</a> · <a href="{ap}tips/">Tips</a> · <a href="{ap}blog/">Blog</a> · <a href="{ap}about/">About</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only.
</div>

<div class="page-modal-bg" id="page-modal"><div class="page-modal"><button class="page-modal-close" onclick="closePage()">×</button><div class="pm" id="page-content"></div></div></div>

<script src="{ap}assets/shared.js?v=24"></script>
<script>
const SITE={{home:'{ap}',tips:'{ap}tips/',casino:'{ap}casino/',odds:'{ap}odds/',countries:'{ap}countries/'}};
let _activeFilt='all';
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
    for p in PAGES:
        out_dir = os.path.join(BASE, p['path'])
        os.makedirs(out_dir, exist_ok=True)
        html = make_payment_page(p)
        out_path = os.path.join(out_dir, 'index.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'  ✓  /{p["canonical_path"]}/')
    print(f'\n✅ Generated {len(PAGES)} payment pages')
