#!/usr/bin/env python3
"""Generate payment method × country pages.

Creates /betting/{payment-slug}/{country-slug}/index.html for every
valid payment × country combination — targeting searches like
"M-Pesa betting sites Kenya", "MTN MoMo betting Ghana", etc.
"""

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

PAYMENTS = [
    {
        'slug': 'mpesa-betting-sites',
        'name': 'M-Pesa',
        'icon': '📱',
        'provider': 'Safaricom / Vodacom',
        'about': 'M-Pesa is East and Southern Africa\'s leading mobile money platform. Launched by Safaricom in Kenya in 2007, it now operates across 7 African countries. Bettors use M-Pesa USSD (*334# in Kenya) or the M-Pesa app to deposit and withdraw instantly at licensed bookmakers.',
        'how_to': [
            'Go to M-Pesa on your phone (dial *334# or use the app)',
            'Select "Lipa na M-Pesa" → "Pay Bill"',
            'Enter the bookmaker\'s business number',
            'Enter your betting account number as the reference',
            'Enter the amount and your M-Pesa PIN',
            'Your betting account is credited instantly',
        ],
        'countries': {
            'kenya':      {'code': 'KE', 'flag': '🇰🇪', 'name': 'Kenya',      'provider': 'Safaricom', 'min': 'KSh 50',   'ussd': '*334#',    'regulator': 'BCLB'},
            'tanzania':   {'code': 'TZ', 'flag': '🇹🇿', 'name': 'Tanzania',   'provider': 'Vodacom',   'min': 'TSh 500',  'ussd': '*150*00#', 'regulator': 'GBT'},
            'ghana':      {'code': 'GH', 'flag': '🇬🇭', 'name': 'Ghana',      'provider': 'Vodafone',  'min': 'GH₵5',     'ussd': '*110#',    'regulator': 'GCA'},
            'mozambique': {'code': 'MZ', 'flag': '🇲🇿', 'name': 'Mozambique', 'provider': 'Vodacom',   'min': 'MT 20',    'ussd': '*847#',    'regulator': 'GCMZ'},
            'dr-congo':   {'code': 'CD', 'flag': '🇨🇩', 'name': 'DR Congo',   'provider': 'Vodacom',   'min': 'CDF 500',  'ussd': '*144#',    'regulator': 'CNJH'},
            'lesotho':    {'code': 'LS', 'flag': '🇱🇸', 'name': 'Lesotho',    'provider': 'Vodacom',   'min': 'LSL 20',   'ussd': '*109#',    'regulator': 'LGC'},
        },
    },
    {
        'slug': 'mtn-momo-betting-sites',
        'name': 'MTN Mobile Money',
        'icon': '📲',
        'provider': 'MTN Group',
        'about': 'MTN Mobile Money (MoMo) is the most widely used mobile money platform across West and Central Africa. Operated by MTN Group — Africa\'s largest telecom — MoMo is available in 16 African countries and is the primary method for sports betting deposits and withdrawals across Nigeria, Ghana, Uganda, Rwanda, Cameroon and more.',
        'how_to': [
            'Dial the MTN MoMo USSD code for your country',
            'Select "Payment" or "Pay Bill"',
            'Enter the bookmaker\'s MoMo merchant code',
            'Enter the amount and your MoMo PIN',
            'Confirm the transaction',
            'Your betting account is credited instantly',
        ],
        'countries': {
            'ghana':       {'code': 'GH', 'flag': '🇬🇭', 'name': 'Ghana',        'provider': 'MTN Ghana',    'min': 'GH₵5',     'ussd': '*170#',  'regulator': 'GCA'},
            'uganda':      {'code': 'UG', 'flag': '🇺🇬', 'name': 'Uganda',       'provider': 'MTN Uganda',   'min': 'USh 500',  'ussd': '*165#',  'regulator': 'NLB'},
            'rwanda':      {'code': 'RW', 'flag': '🇷🇼', 'name': 'Rwanda',       'provider': 'MTN Rwanda',   'min': 'RWF 500',  'ussd': '*182#',  'regulator': 'RGA'},
            'cameroon':    {'code': 'CM', 'flag': '🇨🇲', 'name': 'Cameroon',     'provider': 'MTN Cameroon', 'min': 'CFA 500',  'ussd': '*126#',  'regulator': 'MinFin'},
            'ivory-coast': {'code': 'CI', 'flag': '🇨🇮', 'name': 'Ivory Coast',  'provider': 'MTN CI',       'min': 'CFA 500',  'ussd': '*133#',  'regulator': 'LONACI'},
            'zambia':      {'code': 'ZM', 'flag': '🇿🇲', 'name': 'Zambia',       'provider': 'MTN Zambia',   'min': 'ZK 10',    'ussd': '*303#',  'regulator': 'GLAZ'},
            'south-africa':{'code': 'ZA', 'flag': '🇿🇦', 'name': 'South Africa', 'provider': 'MTN SA',       'min': 'R20',      'ussd': '*141#',  'regulator': 'WCGRB'},
            'nigeria':     {'code': 'NG', 'flag': '🇳🇬', 'name': 'Nigeria',      'provider': 'MTN Nigeria',  'min': '₦100',     'ussd': '*600#',  'regulator': 'NLRC'},
            'liberia':     {'code': 'LR', 'flag': '🇱🇷', 'name': 'Liberia',      'provider': 'MTN Liberia',  'min': '$1',       'ussd': '*155#',  'regulator': 'CCB'},
        },
    },
    {
        'slug': 'airtel-money-betting',
        'name': 'Airtel Money',
        'icon': '📡',
        'provider': 'Airtel Africa',
        'about': 'Airtel Money is operated by Airtel Africa and is available across 14 African countries. It is the second-largest mobile money platform in East and Southern Africa, competing directly with M-Pesa and MTN MoMo. Airtel Money enables fast and fee-free sports betting deposits and withdrawals at all major licensed bookmakers.',
        'how_to': [
            'Dial the Airtel Money USSD code for your country',
            'Select "Make Payments" or "Pay Bills"',
            'Enter the bookmaker\'s Airtel Money code',
            'Enter the amount and your Airtel Money PIN',
            'Confirm the transaction',
            'Account credited instantly',
        ],
        'countries': {
            'kenya':    {'code': 'KE', 'flag': '🇰🇪', 'name': 'Kenya',    'provider': 'Airtel Kenya',  'min': 'KSh 50',  'ussd': '*334#', 'regulator': 'BCLB'},
            'tanzania': {'code': 'TZ', 'flag': '🇹🇿', 'name': 'Tanzania', 'provider': 'Airtel TZ',    'min': 'TSh 500', 'ussd': '*150#', 'regulator': 'GBT'},
            'uganda':   {'code': 'UG', 'flag': '🇺🇬', 'name': 'Uganda',   'provider': 'Airtel Uganda', 'min': 'USh 500', 'ussd': '*185#', 'regulator': 'NLB'},
            'zambia':   {'code': 'ZM', 'flag': '🇿🇲', 'name': 'Zambia',   'provider': 'Airtel Zambia', 'min': 'ZK 10',   'ussd': '*778#', 'regulator': 'GLAZ'},
            'malawi':   {'code': 'MW', 'flag': '🇲🇼', 'name': 'Malawi',   'provider': 'Airtel Malawi', 'min': 'MWK 200', 'ussd': '*211#', 'regulator': 'GBM'},
            'rwanda':   {'code': 'RW', 'flag': '🇷🇼', 'name': 'Rwanda',   'provider': 'Airtel Rwanda', 'min': 'RWF 500', 'ussd': '*185#', 'regulator': 'RGA'},
            'nigeria':  {'code': 'NG', 'flag': '🇳🇬', 'name': 'Nigeria',  'provider': 'Airtel Nigeria','min': '₦100',    'ussd': '*432#', 'regulator': 'NLRC'},
            'dr-congo': {'code': 'CD', 'flag': '🇨🇩', 'name': 'DR Congo', 'provider': 'Airtel DRC',   'min': 'CDF 500', 'ussd': '*123#', 'regulator': 'CNJH'},
        },
    },
    {
        'slug': 'opay-betting-sites',
        'name': 'OPay',
        'icon': '💚',
        'provider': 'OPay / Opera',
        'about': 'OPay is Nigeria\'s fastest-growing fintech platform and has become the dominant payment method for sports betting in Nigeria. With over 35 million users, OPay offers instant deposits and withdrawals at all major NLRC-licensed bookmakers. The OPay app is available on Android and iOS.',
        'how_to': [
            'Open the OPay app on your smartphone',
            'Select "Transfer" or "Pay Bills"',
            'Search for your bookmaker (e.g., Bet9ja, SportyBet)',
            'Enter your betting account number',
            'Enter the amount and confirm with your PIN or fingerprint',
            'Your betting account is credited instantly',
        ],
        'countries': {
            'nigeria': {'code': 'NG', 'flag': '🇳🇬', 'name': 'Nigeria', 'provider': 'OPay Nigeria', 'min': '₦100', 'ussd': 'OPay App', 'regulator': 'NLRC'},
            'ghana':   {'code': 'GH', 'flag': '🇬🇭', 'name': 'Ghana',   'provider': 'OPay Ghana',   'min': 'GH₵5', 'ussd': 'OPay App', 'regulator': 'GCA'},
            'egypt':   {'code': 'EG', 'flag': '🇪🇬', 'name': 'Egypt',   'provider': 'OPay Egypt',   'min': 'EGP 50','ussd': 'OPay App', 'regulator': 'ERA'},
        },
    },
    {
        'slug': 'orange-money-betting',
        'name': 'Orange Money',
        'icon': '🟠',
        'provider': 'Orange Africa',
        'about': 'Orange Money is operated by Orange Africa and is the leading mobile money platform in Francophone West and Central Africa. It is particularly dominant in Senegal, Ivory Coast, Cameroon, Mali, and Guinea. Orange Money enables seamless sports betting deposits and withdrawals at licensed bookmakers across the region.',
        'how_to': [
            'Dial the Orange Money USSD code for your country',
            'Select "Payment" or "Merchant Payment"',
            'Enter the bookmaker\'s Orange Money merchant code',
            'Enter the amount and your Orange Money PIN',
            'Confirm the transaction with the code sent by SMS',
            'Account credited instantly',
        ],
        'countries': {
            'senegal':     {'code': 'SN', 'flag': '🇸🇳', 'name': 'Senegal',     'provider': 'Orange Senegal',    'min': 'CFA 500', 'ussd': '#144#', 'regulator': 'DGJPS'},
            'ivory-coast': {'code': 'CI', 'flag': '🇨🇮', 'name': 'Ivory Coast', 'provider': 'Orange CI',         'min': 'CFA 500', 'ussd': '#144#', 'regulator': 'LONACI'},
            'cameroon':    {'code': 'CM', 'flag': '🇨🇲', 'name': 'Cameroon',    'provider': 'Orange Cameroon',   'min': 'CFA 500', 'ussd': '#150#', 'regulator': 'MinFin'},
            'morocco':     {'code': 'MA', 'flag': '🇲🇦', 'name': 'Morocco',     'provider': 'Orange Morocco',    'min': 'MAD 20',  'ussd': '#501#', 'regulator': 'MDJS'},
            'sierra-leone':{'code': 'SL', 'flag': '🇸🇱', 'name': 'Sierra Leone','provider': 'Orange SL',         'min': 'Le 5,000','ussd': '#144#', 'regulator': 'NLA'},
            'liberia':     {'code': 'LR', 'flag': '🇱🇷', 'name': 'Liberia',     'provider': 'Orange Liberia',    'min': '$1',      'ussd': '#144#', 'regulator': 'CCB'},
            'mali':        {'code': 'ML', 'flag': '🇲🇱', 'name': 'Mali',        'provider': 'Orange Mali',       'min': 'CFA 500', 'ussd': '#144#', 'regulator': 'DGDL'},
        },
    },
    {
        'slug': 'ecocash-betting',
        'name': 'EcoCash',
        'icon': '💚',
        'provider': 'Econet Wireless',
        'about': 'EcoCash is Zimbabwe\'s dominant mobile money platform, operated by Econet Wireless. With over 8 million active wallets, EcoCash is used by the vast majority of Zimbabweans for sports betting deposits and withdrawals. It has become an essential tool for betting in Zimbabwe\'s USD-denominated economy.',
        'how_to': [
            'Dial *151# on your Econet line',
            'Select "EcoCash" → "Send Money" or "Pay Merchant"',
            'Enter the bookmaker\'s EcoCash merchant code',
            'Enter the amount in USD',
            'Enter your EcoCash PIN to confirm',
            'Account credited instantly',
        ],
        'countries': {
            'zimbabwe': {'code': 'ZW', 'flag': '🇿🇼', 'name': 'Zimbabwe', 'provider': 'Econet Wireless', 'min': '$1', 'ussd': '*151#', 'regulator': 'LGB'},
        },
    },
    {
        'slug': 'telebirr-betting',
        'name': 'Telebirr',
        'icon': '📱',
        'provider': 'Ethio Telecom',
        'about': 'Telebirr is Ethiopia\'s national mobile money platform, operated by Ethio Telecom. Launched in 2021, it has grown rapidly to over 40 million users, making Ethiopia one of Africa\'s fastest-growing mobile money markets. Telebirr is now the primary payment method for sports betting in Ethiopia.',
        'how_to': [
            'Open the Telebirr app or dial *127#',
            'Select "Pay" or "Merchant Payment"',
            'Search for your bookmaker',
            'Enter your betting account number',
            'Enter the amount and confirm with your PIN',
            'Account credited instantly',
        ],
        'countries': {
            'ethiopia': {'code': 'ET', 'flag': '🇪🇹', 'name': 'Ethiopia', 'provider': 'Ethio Telecom', 'min': 'ETB 50', 'ussd': '*127#', 'regulator': 'LCGA'},
        },
    },
    {
        'slug': 'bank-transfer-betting',
        'name': 'Bank Transfer',
        'icon': '🏦',
        'provider': 'All major banks',
        'about': 'Bank transfer is a widely accepted payment method at licensed African bookmakers. While slower than mobile money, bank transfers often allow larger deposit and withdrawal amounts. They are particularly popular for high-volume bettors in Nigeria, South Africa, Kenya, and Ghana.',
        'how_to': [
            'Log in to your online banking or mobile banking app',
            'Select "Transfer" or "Pay a Bill"',
            'Add the bookmaker as a payee with their account details',
            'Enter the transfer amount',
            'Use your betting account number as the reference',
            'Confirm the transfer — credited within 1-24 hours',
        ],
        'countries': {
            'nigeria':      {'code': 'NG', 'flag': '🇳🇬', 'name': 'Nigeria',      'provider': 'GTBank, Access, Zenith, UBA',   'min': '₦100',   'ussd': 'Internet Banking', 'regulator': 'NLRC'},
            'kenya':        {'code': 'KE', 'flag': '🇰🇪', 'name': 'Kenya',        'provider': 'KCB, Equity, Co-op, DTB',       'min': 'KSh 100','ussd': 'Internet Banking', 'regulator': 'BCLB'},
            'south-africa': {'code': 'ZA', 'flag': '🇿🇦', 'name': 'South Africa', 'provider': 'FNB, Nedbank, Standard, ABSA',  'min': 'R20',    'ussd': 'Internet Banking', 'regulator': 'WCGRB'},
            'ghana':        {'code': 'GH', 'flag': '🇬🇭', 'name': 'Ghana',        'provider': 'GCB, Ecobank, Fidelity, ADB',   'min': 'GH₵10', 'ussd': 'Internet Banking', 'regulator': 'GCA'},
            'tanzania':     {'code': 'TZ', 'flag': '🇹🇿', 'name': 'Tanzania',     'provider': 'CRDB, NMB, NBC, Stanbic',       'min': 'TSh 500','ussd': 'Internet Banking', 'regulator': 'GBT'},
            'uganda':       {'code': 'UG', 'flag': '🇺🇬', 'name': 'Uganda',       'provider': 'Stanbic, DFCU, Centenary',      'min': 'USh 500','ussd': 'Internet Banking', 'regulator': 'NLB'},
            'egypt':        {'code': 'EG', 'flag': '🇪🇬', 'name': 'Egypt',        'provider': 'CIB, NBE, Banque Misr',         'min': 'EGP 50', 'ussd': 'Internet Banking', 'regulator': 'ERA'},
            'morocco':      {'code': 'MA', 'flag': '🇲🇦', 'name': 'Morocco',      'provider': 'Attijariwafa, CIH, BMCE',       'min': 'MAD 20', 'ussd': 'Internet Banking', 'regulator': 'MDJS'},
            'senegal':      {'code': 'SN', 'flag': '🇸🇳', 'name': 'Senegal',      'provider': 'Ecobank, CBAO, BIS',            'min': 'CFA 500','ussd': 'Internet Banking', 'regulator': 'DGJPS'},
            'angola':       {'code': 'AO', 'flag': '🇦🇴', 'name': 'Angola',       'provider': 'BFA, BCI, BAI, Millennium',     'min': 'AOA 200','ussd': 'Internet Banking', 'regulator': 'IRSE'},
        },
    },
    {
        'slug': 'vodacom-betting-sites',
        'name': 'Vodacom M-Pesa',
        'icon': '📡',
        'provider': 'Vodacom',
        'about': 'Vodacom M-Pesa (distinct from Safaricom M-Pesa) operates across Tanzania, DRC, and Mozambique. While sharing the M-Pesa brand, Vodacom M-Pesa operates on separate infrastructure. It is the dominant mobile money platform in Tanzania and provides seamless betting deposits and withdrawals at licensed bookmakers.',
        'how_to': [
            'Dial the Vodacom M-Pesa USSD code',
            'Select "Lipa Bili" (Pay Bill)',
            'Enter the bookmaker\'s business number',
            'Enter your betting account reference',
            'Enter the amount and your PIN',
            'Account credited instantly',
        ],
        'countries': {
            'tanzania':   {'code': 'TZ', 'flag': '🇹🇿', 'name': 'Tanzania',   'provider': 'Vodacom TZ', 'min': 'TSh 500', 'ussd': '*150*00#', 'regulator': 'GBT'},
            'mozambique': {'code': 'MZ', 'flag': '🇲🇿', 'name': 'Mozambique', 'provider': 'Vodacom MZ', 'min': 'Mt 20',   'ussd': '*847#',    'regulator': 'GCMZ'},
            'dr-congo':   {'code': 'CD', 'flag': '🇨🇩', 'name': 'DR Congo',   'provider': 'Vodacom DRC','min': 'CDF 500', 'ussd': '*144#',    'regulator': 'CNJH'},
            'south-africa':{'code': 'ZA', 'flag': '🇿🇦', 'name': 'South Africa','provider': 'Vodacom SA', 'min': 'R20',    'ussd': '*147#',    'regulator': 'WCGRB'},
        },
    },
]

COUNTRIES_META = {
    'kenya':       {'hreflang': 'en-KE'},
    'tanzania':    {'hreflang': 'en-TZ'},
    'ghana':       {'hreflang': 'en-GH'},
    'nigeria':     {'hreflang': 'en-NG'},
    'uganda':      {'hreflang': 'en-UG'},
    'south-africa':{'hreflang': 'en-ZA'},
    'zambia':      {'hreflang': 'en-ZM'},
    'malawi':      {'hreflang': 'en-MW'},
    'rwanda':      {'hreflang': 'en-RW'},
    'zimbabwe':    {'hreflang': 'en-ZW'},
    'ethiopia':    {'hreflang': 'en-ET'},
    'ivory-coast': {'hreflang': 'fr-CI'},
    'cameroon':    {'hreflang': 'fr-CM'},
    'senegal':     {'hreflang': 'fr-SN'},
    'morocco':     {'hreflang': 'fr-MA'},
    'sierra-leone':{'hreflang': 'en-SL'},
    'liberia':     {'hreflang': 'en-LR'},
    'angola':      {'hreflang': 'pt-AO'},
    'dr-congo':    {'hreflang': 'fr-CD'},
    'egypt':       {'hreflang': 'ar-EG'},
    'mali':        {'hreflang': 'fr-ML'},
    'mozambique':  {'hreflang': 'pt-MZ'},
    'botswana':    {'hreflang': 'en-BW'},
}


def build_page(payment, country_slug, country_data):
    pm_name = payment['name']
    pm_slug = payment['slug']
    pm_icon = payment['icon']
    pm_about = payment['about']
    pm_provider = payment['provider']
    how_to = payment['how_to']

    cname = country_data['name']
    code = country_data['code']
    flag = country_data['flag']
    provider_local = country_data['provider']
    min_dep = country_data['min']
    ussd = country_data['ussd']
    regulator = country_data['regulator']

    meta = COUNTRIES_META.get(country_slug, {'hreflang': 'en'})
    hreflang = meta['hreflang']

    assets = '../../../'
    canonical = f'https://sifufinds.com/betting/{pm_slug}/{country_slug}/'

    title = seo_title(f'Best {pm_name} Betting Sites {cname} 2026')
    description = f'Best {pm_name} betting sites in {cname} 2026. Deposit and withdraw instantly via {pm_name} ({provider_local}) at licensed bookmakers. Min deposit {min_dep}. Updated daily.'
    keywords = f'{pm_name.lower()} betting sites {cname.lower()}, bet with {pm_name.lower()} {cname.lower()}, {pm_name.lower()} bookmakers {cname.lower()}, {pm_name.lower()} sports betting {cname.lower()} 2026'

    how_to_html = ''.join(f'<li>{step}</li>' for step in how_to)

    faq_items = [
        (f'Which betting sites accept {pm_name} in {cname}?',
         f'All major bookmakers listed on SifuFinds accept {pm_name} ({provider_local}) for deposits and withdrawals in {cname}. The minimum deposit via {pm_name} is {min_dep}. All listed bookmakers are licensed by {regulator}.'),
        (f'How do I deposit with {pm_name} at a betting site?',
         f'To deposit with {pm_name} at a {cname} bookmaker: (1) Dial {ussd} or open the {pm_name} app, (2) Select Pay Bill or Merchant Payment, (3) Enter the bookmaker\'s {pm_name} code, (4) Enter your betting account number as reference, (5) Enter the amount ({min_dep} minimum) and confirm with your PIN.'),
        (f'How long does a {pm_name} withdrawal take?',
         f'{pm_name} withdrawals at licensed {cname} bookmakers are typically processed within 5 minutes to 24 hours. Processing times vary by bookmaker. Most major licensed bookmakers process {pm_name} withdrawals instantly or within a few hours.'),
        (f'Is it safe to bet with {pm_name} in {cname}?',
         f'Yes. Betting with {pm_name} at licensed bookmakers in {cname} is safe. All bookmakers on SifuFinds are regulated by {regulator} and use secure {pm_name} payment processing. Always check that your bookmaker is listed on SifuFinds before depositing.'),
    ]

    faq_schema = ',\n'.join(
        json.dumps({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a},
        })
        for q, a in faq_items
    )

    faq_html = ''
    for q, a in faq_items:
        faq_html += f'''    <div class="faq-item">
      <button class="faq-q" onclick="this.parentElement.classList.toggle('open')">{q} <span class="faq-arr">▼</span></button>
      <div class="faq-a"><p>{a}</p></div>
    </div>
'''

    return f'''<!DOCTYPE html>
<!-- sifufinds.com/betting/{pm_slug}/{country_slug}/ — {pm_name} Betting Sites {cname} 2026 -->
<html lang="en">
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
<title>{title}</title>
<meta name="description" content="{seo_meta_description(description)}">
<meta name="keywords" content="{keywords}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="author" content="SifuFinds">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="{hreflang}" href="{canonical}">
<link rel="alternate" hreflang="en" href="{canonical}">
<meta name="geo.region" content="{code}">
<meta name="geo.placename" content="{cname}">

<meta property="og:type" content="website">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="Best {pm_name} Betting Sites {cname} 2026 | SifuFinds">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="https://sifufinds.com/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_GB">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@sifufinds">
<meta name="twitter:title" content="Best {pm_name} Betting Sites {cname} 2026 | SifuFinds">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="https://sifufinds.com/assets/og-image.png">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "WebPage",
      "@id": "{canonical}#webpage",
      "name": "{title}",
      "description": "{description}",
      "url": "{canonical}",
      "inLanguage": "en-GB",
      "isPartOf": {{"@id": "https://sifufinds.com/#website"}}
    }},
    {{
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://sifufinds.com/"}},
        {{"@type": "ListItem", "position": 2, "name": "{pm_name} Betting", "item": "https://sifufinds.com/betting/{pm_slug}/"}},
        {{"@type": "ListItem", "position": 3, "name": "{pm_name} Betting {cname}", "item": "{canonical}"}}
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

<link rel="preload" href="{assets}assets/shared.css?v=12" as="style">
<link rel="stylesheet" href="{assets}assets/shared.css?v=12">
<style>
.pm-hero{{background:linear-gradient(135deg,#0a3d1e 0%,#1a6b35 100%);color:#fff;padding:28px 0}}
.pm-hero h1{{font-size:clamp(20px,3.5vw,28px);font-weight:900;margin-bottom:8px;letter-spacing:-.5px}}
.pm-hero p{{font-size:14px;color:rgba(255,255,255,.85);max-width:640px;line-height:1.65}}
.pm-badge{{display:inline-block;background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.4);color:#fff;font-size:12px;font-weight:700;padding:4px 12px;border-radius:6px;margin-top:8px}}
.how-to-steps{{counter-reset:steps;list-style:none;padding:0;margin:10px 0}}
.how-to-steps li{{counter-increment:steps;padding:8px 0 8px 36px;position:relative;font-size:13px;color:#333;border-bottom:1px solid #f0f0f0;line-height:1.5}}
.how-to-steps li::before{{content:counter(steps);position:absolute;left:0;top:8px;background:var(--g);color:#fff;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800}}
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
.info-table{{width:100%;border-collapse:collapse;margin-top:10px}}
.info-table tr:nth-child(even){{background:#f9f9f9}}
.info-table td{{padding:9px 12px;font-size:13px;border-bottom:1px solid #eee;line-height:1.5}}
.info-table td:first-child{{font-weight:700;color:#555;width:40%}}
</style>
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
</head>
<body>

<div class="tbar">
  <div class="tbar-l">
    <a href="{assets}">🏠 Home</a>
    <a href="{assets}betting/{pm_slug}/">{pm_icon} {pm_name}</a>
    <a href="{assets}responsible/">Responsible Gambling</a>
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
    <a class="logo" href="{assets}"><img src="{assets}assets/icon.png" width="38" height="38" alt="SifuFinds logo" style="display:block;object-fit:contain">SifuFinds</a>
    <div class="ntabs">
      <a class="nt on" href="{assets}">⭐ Best Bonuses</a>
      <a class="nt" href="{assets}tips/">💡 Tips</a>
      <a class="nt" href="{assets}casino/">🎰 Casino</a>
      <a class="nt" href="{assets}odds/">📊 Live Odds<span class="lpulse" style="margin-left:4px"></span></a>
      <a class="nt" href="{assets}countries/">🌍 Countries</a>
      <a class="nt" href="{assets}blog/">📰 Blog</a>
    </div>
  </div>
</nav>

<div id="hbrands" class="hbrands"></div>

<div class="pm-hero">
  <div class="wrap">
    <h1>{flag} Best {pm_name} Betting Sites in {cname} 2026</h1>
    <p>Deposit and withdraw instantly via <strong>{pm_name}</strong> ({provider_local}) at licensed {cname} bookmakers. Minimum deposit: <strong>{min_dep}</strong>. All bookmakers verified and regulated by {regulator}. Updated June 2026.</p>
    <div class="pm-badge">{pm_icon} {pm_name} · {provider_local} · {ussd}</div>
  </div>
</div>

<div class="sec-bg"><div class="wrap" style="padding-top:14px">
  <div class="breadcrumb">
    <a href="{assets}">Home</a><span>›</span>
    <a href="{assets}betting/{pm_slug}/">{pm_name} Betting</a><span>›</span>
    {pm_name} Betting {cname}
  </div>

  <div class="adv">📢 <strong>Advertiser Disclosure:</strong> We earn commission from some bookmaker links. All bonuses verified. Check T&Cs. 18+.</div>

  <div class="cbox2">
    <h2>{pm_name} Betting in {cname} — Quick Facts</h2>
    <table class="info-table">
      <tr><td>Payment Method</td><td><strong>{pm_icon} {pm_name}</strong></td></tr>
      <tr><td>Provider in {cname}</td><td>{provider_local}</td></tr>
      <tr><td>USSD / Access</td><td><strong>{ussd}</strong></td></tr>
      <tr><td>Minimum Deposit</td><td><strong>{min_dep}</strong></td></tr>
      <tr><td>Deposit Speed</td><td>✅ Instant</td></tr>
      <tr><td>Withdrawal Speed</td><td>5 minutes – 24 hours</td></tr>
      <tr><td>Regulator</td><td>{regulator}</td></tr>
    </table>
  </div>

  <div class="sec-lbl" style="font-size:11px;font-weight:700;color:#aaa;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">BOOKMAKERS ACCEPTING {pm_name.upper()} · {cname.upper()} · 2026</div>
  <h2 style="font-size:17px;font-weight:800;color:#111;margin-bottom:9px">Best {pm_name} Betting Sites in {cname} — Verified 2026</h2>

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
    <h2>What is {pm_name}?</h2>
    <p>{pm_about}</p>
  </div>

  <div class="cbox2">
    <h2>How to Deposit with {pm_name} at a Betting Site in {cname}</h2>
    <ol class="how-to-steps">
      {how_to_html}
    </ol>
  </div>

  <div class="cbox2">
    <h2>Frequently Asked Questions — {pm_name} Betting {cname}</h2>
{faq_html}  </div>

  <div class="cbox2">
    <h2>More Payment Methods in {cname}</h2>
    <p>Looking for other ways to fund your betting account in {cname}? Explore more payment options:</p>
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:10px">
      <a href="{assets}betting/mpesa-betting-sites/{country_slug}/" style="background:#edf7f0;border:1px solid #c8e6c9;border-radius:6px;padding:6px 12px;font-size:12px;font-weight:700;color:#1a6b35;text-decoration:none">📱 M-Pesa</a>
      <a href="{assets}betting/mtn-momo-betting-sites/{country_slug}/" style="background:#fff8e1;border:1px solid #fdd835;border-radius:6px;padding:6px 12px;font-size:12px;font-weight:700;color:#f57f17;text-decoration:none">📲 MTN MoMo</a>
      <a href="{assets}betting/airtel-money-betting/{country_slug}/" style="background:#ffebee;border:1px solid #ef9a9a;border-radius:6px;padding:6px 12px;font-size:12px;font-weight:700;color:#c62828;text-decoration:none">📡 Airtel Money</a>
      <a href="{assets}betting/bank-transfer-betting/{country_slug}/" style="background:#e3f2fd;border:1px solid #90caf9;border-radius:6px;padding:6px 12px;font-size:12px;font-weight:700;color:#1565c0;text-decoration:none">🏦 Bank Transfer</a>
    </div>
  </div>

  <div class="resp">⚠️ Gambling involves risk. Only bet what you can afford to lose. 18+ only.</div>
</div></div>

<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison<br>
  <a href="{assets}">Home</a> · <a href="{assets}betting/{pm_slug}/">{pm_name} Betting Africa</a> · <a href="{assets}best-bonus-in-{country_slug}/">{cname} Betting</a> · <a href="{assets}tips/">Tips</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only.
</div>

<div class="page-modal-bg" id="page-modal"><div class="page-modal"><button class="page-modal-close" onclick="closePage()">×</button><div class="pm" id="page-content"></div></div></div>

<script src="{assets}assets/shared.js?v=20"></script>
<script>
const SITE={{home:'{assets}',tips:'{assets}tips/',casino:'{assets}casino/',odds:'{assets}odds/',countries:'{assets}countries/'}};
const _PAGE_CTY='{code}';
let _activeFilt='all';
function getCurrentCountry(){{return _PAGE_CTY;}}
function setFilt(btn){{document.querySelectorAll('.fp').forEach(b=>b.classList.remove('on'));btn.classList.add('on');_activeFilt=btn.dataset.f;renderBooks();}}
function filterBooks(books){{const f=_activeFilt;if(f==='all')return books;if(f==='nodep')return books.filter(b=>b.nodep);if(f==='cashout')return books.filter(b=>b.cashout);return books;}}
function sortBooks(books){{const s=document.getElementById('srt')?.value||'default';if(s==='stars')return[...books].sort((a,b)=>b.stars-a.stars);if(s==='bonus')return[...books].sort((a,b)=>(b.nodep?1:0)-(a.nodep?1:0));return books;}}
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
function renderBooks(){{const books=filterBooks(sortBooks(BOOKS[_PAGE_CTY]||[]));const el=document.getElementById('bk-cards');if(!books.length){{el.innerHTML='<div class="no-results">No bookmakers match this filter.</div>';return;}}el.innerHTML=books.map((b,i)=>bookCard(b,i,i)).join('');H('mcount',`Showing ${{books.length}} bookmaker${{books.length!==1?'s':''}}`);}}
function init(){{const sel=document.getElementById('ctySel');if(sel)sel.value=_PAGE_CTY;H('foot-yr',NOW.getFullYear());renderBooks();}}
init();
</script>
</body>
</html>'''


def main():
    created = 0
    for payment in PAYMENTS:
        pm_slug = payment['slug']
        for country_slug, country_data in payment['countries'].items():
            out_dir = os.path.join(BASE, 'betting', pm_slug, country_slug)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, 'index.html')

            html = build_page(payment, country_slug, country_data)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(html)
            created += 1
            print(f'  ✓  betting/{pm_slug}/{country_slug}/index.html')

    print(f'\n✅  {created} payment × country pages generated.')


if __name__ == '__main__':
    main()
