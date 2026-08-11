#!/usr/bin/env python3
"""Generate bookmaker × country pages for SEO.

Creates /bookmakers/{bk-slug}/{country-slug}/index.html for every
valid bookmaker × country combination — targeting high-commercial-intent
searches like "Betway Nigeria review 2026", "SportPesa Kenya bonus", etc.
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

# ── BOOKMAKERS ─────────────────────────────────────────────────────────────
BOOKMAKERS = [
    {
        'slug': 'betway-africa',
        'name': 'Betway',
        'display': 'Betway Africa',
        'color': '#005CA9',
        'url': 'https://www.betway.com',
        'rating': 4.7,
        'stars': '★★★★☆',
        'sports': 28,
        'app': True,
        'cashout': True,
        'live_stream': True,
        'pros': [
            'Licensed by local regulators in each country',
            'Excellent mobile app — best UI/UX in African betting',
            'Live streaming on 100,000+ events per year',
            'Instant mobile money deposits',
            'Cash-out available on all markets',
        ],
        'cons': [
            'Welcome bonus lower than 1xBet or Melbet',
            'Fewer sports markets than 1xBet',
        ],
        'countries': {
            'nigeria':      {'bonus': '₦100,000', 'min_dep': '₦100',  'lic': 'NLRC',  'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa', 'Mastercard'],        'bonus_desc': '100% match up to ₦100,000 on first deposit'},
            'kenya':        {'bonus': 'KSh 5,000', 'min_dep': 'KSh 50',  'lic': 'BCLB',  'payments': ['M-Pesa', 'Airtel Money', 'Visa', 'Mastercard'],                   'bonus_desc': '100% match up to KSh 5,000 on first deposit'},
            'south-africa': {'bonus': 'R1,000',    'min_dep': 'R20',     'lic': 'WCGRB', 'payments': ['FNB', 'Nedbank', 'Standard Bank', 'Visa', 'Mastercard'],           'bonus_desc': 'R1,000 free bet on first qualifying deposit'},
            'tanzania':     {'bonus': 'TSh 150,000','min_dep': 'TSh 500','lic': 'GBT',   'payments': ['M-Pesa', 'Airtel Money', 'Tigo Pesa', 'Visa'],                     'bonus_desc': '100% match up to TSh 150,000 on first deposit'},
            'uganda':       {'bonus': 'USh 100,000','min_dep': 'USh 500','lic': 'NLB',   'payments': ['MTN MoMo', 'Airtel Money', 'Visa', 'Mastercard'],                  'bonus_desc': '100% match up to USh 100,000 on first deposit'},
            'ghana':        {'bonus': 'GH₵500',    'min_dep': 'GH₵5',   'lic': 'GCA',   'payments': ['MTN MoMo', 'Vodafone Cash', 'AirtelTigo', 'Visa', 'Mastercard'],   'bonus_desc': '100% match up to GH₵500 on first deposit'},
            'rwanda':       {'bonus': 'RWF 50,000','min_dep': 'RWF 500','lic': 'RGA',   'payments': ['MTN MoMo', 'Airtel Money', 'Visa', 'Mastercard'],                  'bonus_desc': '100% match up to RWF 50,000 on first deposit'},
            'zimbabwe':     {'bonus': '$20',        'min_dep': '$1',      'lic': 'BCLB',  'payments': ['EcoCash', 'OneMoney', 'Visa', 'Mastercard'],                       'bonus_desc': '100% match up to $20 on first deposit'},
            'zambia':       {'bonus': 'ZK 500',     'min_dep': 'ZK 10',  'lic': 'GLAZ',  'payments': ['MTN MoMo', 'Airtel Money', 'Visa', 'Mastercard'],                  'bonus_desc': '100% match up to ZK 500 on first deposit'},
            'botswana':     {'bonus': 'BWP 500',    'min_dep': 'BWP 10', 'lic': 'GCAB',  'payments': ['Orange Money', 'Smega', 'Visa', 'Mastercard'],                     'bonus_desc': '100% match up to BWP 500 on first deposit'},
            'namibia':      {'bonus': 'NAD 500',    'min_dep': 'NAD 10', 'lic': 'GBN',   'payments': ['FNB Namibia', 'Bank Windhoek', 'Visa', 'Mastercard'],              'bonus_desc': '100% match up to NAD 500 on first deposit'},
            'malawi':       {'bonus': 'MWK 5,000',  'min_dep': 'MWK 200','lic': 'GBM',   'payments': ['Airtel Money', 'TNM Mpamba', 'Visa', 'Mastercard'],                'bonus_desc': '100% match up to MWK 5,000 on first deposit'},
            'mozambique':   {'bonus': 'MZN 500',    'min_dep': 'MZN 20', 'lic': 'GCMZ',  'payments': ['M-Pesa', 'Mkesh', 'Visa', 'Mastercard'],                          'bonus_desc': '100% match up to MZN 500 on first deposit'},
            'cameroon':     {'bonus': 'CFA 50,000', 'min_dep': 'CFA 500','lic': 'LONACI','payments': ['MTN MoMo', 'Orange Money', 'Visa', 'Mastercard'],                  'bonus_desc': '100% match up to CFA 50,000 on first deposit'},
        },
    },
    {
        'slug': '1xbet-africa',
        'name': '1xBet',
        'display': '1xBet Africa',
        'color': '#1565C0',
        'url': 'https://www.1xbet.com',
        'rating': 4.5,
        'stars': '★★★★½',
        'sports': 50,
        'app': True,
        'cashout': True,
        'live_stream': True,
        'pros': [
            '50+ sports and 1,000+ betting markets per event',
            'Highest welcome bonus in Africa',
            'Available in all 23 African countries on SifuFinds',
            'Excellent live betting platform',
            'Accepts all major mobile money providers',
        ],
        'cons': [
            'Licensed offshore (Curaçao) — not locally regulated in all countries',
            'Withdrawal can take 1–3 days',
            'Complex bonus wagering requirements (35x)',
        ],
        'countries': {
            'nigeria':      {'bonus': '₦130,000',   'min_dep': '₦100',   'lic': 'Curaçao eGaming', 'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa', 'Mastercard', 'Bitcoin'],      'bonus_desc': '100% match up to ₦130,000 on first deposit'},
            'kenya':        {'bonus': 'KSh 10,000', 'min_dep': 'KSh 100','lic': 'BCLB',             'payments': ['M-Pesa', 'Airtel Money', 'Visa', 'Mastercard'],                            'bonus_desc': '100% match up to KSh 10,000 on first deposit'},
            'ghana':        {'bonus': 'GH₵700',     'min_dep': 'GH₵5',   'lic': 'GCA',              'payments': ['MTN MoMo', 'Vodafone Cash', 'AirtelTigo', 'Visa'],                         'bonus_desc': '100% match up to GH₵700 on first deposit'},
            'south-africa': {'bonus': 'R3,000',     'min_dep': 'R20',     'lic': 'WCGRB',            'payments': ['EFT', 'FNB', 'Nedbank', 'Visa', 'Mastercard'],                             'bonus_desc': '100% match up to R3,000 on first deposit'},
            'tanzania':     {'bonus': 'TSh 200,000','min_dep': 'TSh 500','lic': 'GBT',              'payments': ['M-Pesa', 'Airtel Money', 'Tigo Pesa', 'Halopesa'],                         'bonus_desc': '100% match up to TSh 200,000 on first deposit'},
            'uganda':       {'bonus': 'USh 200,000','min_dep': 'USh 500','lic': 'NLB',              'payments': ['MTN MoMo', 'Airtel Money', 'Visa'],                                         'bonus_desc': '100% match up to USh 200,000 on first deposit'},
            'ethiopia':     {'bonus': 'ETB 1,500',  'min_dep': 'ETB 50', 'lic': 'Curaçao eGaming', 'payments': ['Telebirr', 'CBE Birr', 'Visa', 'Mastercard'],                              'bonus_desc': '100% match up to ETB 1,500 on first deposit'},
            'ivory-coast':  {'bonus': 'CFA 65,000', 'min_dep': 'CFA 500','lic': 'Curaçao eGaming', 'payments': ['MTN MoMo', 'Orange Money', 'Moov Money', 'Visa'],                          'bonus_desc': '100% match up to CFA 65,000 on first deposit'},
            'cameroon':     {'bonus': 'CFA 65,000', 'min_dep': 'CFA 500','lic': 'Curaçao eGaming', 'payments': ['MTN MoMo', 'Orange Money', 'Visa', 'Mastercard'],                          'bonus_desc': '100% match up to CFA 65,000 on first deposit'},
            'senegal':      {'bonus': 'CFA 65,000', 'min_dep': 'CFA 500','lic': 'Curaçao eGaming', 'payments': ['Orange Money', 'Wave', 'Free Money', 'Visa'],                              'bonus_desc': '100% match up to CFA 65,000 on first deposit'},
            'rwanda':       {'bonus': 'RWF 80,000', 'min_dep': 'RWF 500','lic': 'RGA',              'payments': ['MTN MoMo', 'Airtel Money', 'Visa'],                                         'bonus_desc': '100% match up to RWF 80,000 on first deposit'},
            'zimbabwe':     {'bonus': '$30',         'min_dep': '$1',      'lic': 'Curaçao eGaming', 'payments': ['EcoCash', 'OneMoney', 'Visa', 'Mastercard', 'Bitcoin'],                   'bonus_desc': '100% match up to $30 on first deposit'},
            'zambia':       {'bonus': 'ZK 700',      'min_dep': 'ZK 10',  'lic': 'GLAZ',             'payments': ['MTN MoMo', 'Airtel Money', 'Visa'],                                         'bonus_desc': '100% match up to ZK 700 on first deposit'},
            'botswana':     {'bonus': 'BWP 700',     'min_dep': 'BWP 10', 'lic': 'GCAB',             'payments': ['Orange Money', 'Smega', 'Visa', 'Mastercard'],                             'bonus_desc': '100% match up to BWP 700 on first deposit'},
            'namibia':      {'bonus': 'NAD 700',     'min_dep': 'NAD 10', 'lic': 'GBN',              'payments': ['FNB Namibia', 'Visa', 'Mastercard'],                                        'bonus_desc': '100% match up to NAD 700 on first deposit'},
            'egypt':        {'bonus': 'EGP 3,000',   'min_dep': 'EGP 50', 'lic': 'Curaçao eGaming', 'payments': ['Vodafone Cash', 'Orange Money Egypt', 'Visa', 'Mastercard'],              'bonus_desc': '100% match up to EGP 3,000 on first deposit'},
            'morocco':      {'bonus': 'MAD 1,000',   'min_dep': 'MAD 20', 'lic': 'Curaçao eGaming', 'payments': ['Maroc Telecom', 'Orange Morocco', 'Visa', 'Mastercard'],                  'bonus_desc': '100% match up to MAD 1,000 on first deposit'},
            'angola':       {'bonus': 'AOA 10,000',  'min_dep': 'AOA 200','lic': 'Curaçao eGaming', 'payments': ['Multicaixa', 'Visa', 'Mastercard'],                                         'bonus_desc': '100% match up to AOA 10,000 on first deposit'},
            'dr-congo':     {'bonus': 'CDF 50,000',  'min_dep': 'CDF 500','lic': 'Curaçao eGaming', 'payments': ['M-Pesa', 'Airtel Money', 'Orange Money', 'Visa'],                         'bonus_desc': '100% match up to CDF 50,000 on first deposit'},
            'malawi':       {'bonus': 'MWK 7,000',   'min_dep': 'MWK 200','lic': 'GBM',              'payments': ['Airtel Money', 'TNM Mpamba', 'Visa'],                                       'bonus_desc': '100% match up to MWK 7,000 on first deposit'},
            'mozambique':   {'bonus': 'MZN 700',     'min_dep': 'MZN 20', 'lic': 'Curaçao eGaming', 'payments': ['M-Pesa', 'Mkesh', 'Visa'],                                                  'bonus_desc': '100% match up to MZN 700 on first deposit'},
            'sierra-leone': {'bonus': 'Le 500,000',  'min_dep': 'Le 5,000','lic': 'Curaçao eGaming','payments': ['Orange Money', 'Africell Money', 'Visa'],                                  'bonus_desc': '100% match up to Le 500,000 on first deposit'},
            'liberia':      {'bonus': '$20',          'min_dep': '$1',      'lic': 'Curaçao eGaming', 'payments': ['Orange Money', 'Lonestar Money', 'Visa'],                                  'bonus_desc': '100% match up to $20 on first deposit'},
        },
    },
    {
        'slug': 'sportpesa',
        'name': 'SportPesa',
        'display': 'SportPesa',
        'color': '#006400',
        'url': 'https://www.sportpesa.com',
        'rating': 4.4,
        'stars': '★★★★☆',
        'sports': 20,
        'app': True,
        'cashout': True,
        'live_stream': False,
        'pros': [
            'Africa-born brand — founded in Nairobi',
            'Excellent mobile experience optimised for low-data devices',
            'Strong football coverage for African leagues',
            'Reliable and fast M-Pesa withdrawals',
            'Jackpot games exclusive to African bettors',
        ],
        'cons': [
            'Limited to 5 African countries',
            'No live streaming',
            'Fewer sports than global competitors',
        ],
        'countries': {
            'kenya':        {'bonus': 'KSh 5,000', 'min_dep': 'KSh 50', 'lic': 'BCLB', 'payments': ['M-Pesa', 'Airtel Money', 'Visa', 'Mastercard'], 'bonus_desc': '100% match up to KSh 5,000 on first deposit'},
            'tanzania':     {'bonus': 'TSh 100,000','min_dep': 'TSh 500','lic': 'GBT',  'payments': ['M-Pesa', 'Airtel Money', 'Tigo Pesa', 'Halopesa'], 'bonus_desc': '100% match up to TSh 100,000 on first deposit'},
            'uganda':       {'bonus': 'USh 80,000','min_dep': 'USh 500','lic': 'NLB',   'payments': ['MTN MoMo', 'Airtel Money', 'Visa'], 'bonus_desc': '100% match up to USh 80,000 on first deposit'},
            'ghana':        {'bonus': 'GH₵300',    'min_dep': 'GH₵5',  'lic': 'GCA',   'payments': ['MTN MoMo', 'Vodafone Cash', 'AirtelTigo', 'Visa'], 'bonus_desc': '100% match up to GH₵300 on first deposit'},
            'south-africa': {'bonus': 'R500',       'min_dep': 'R20',    'lic': 'WCGRB','payments': ['FNB', 'Nedbank', 'Standard Bank', 'Visa', 'Mastercard'], 'bonus_desc': 'R500 free bet on first qualifying deposit'},
        },
    },
    {
        'slug': 'bet9ja',
        'name': 'Bet9ja',
        'display': 'Bet9ja',
        'color': '#006600',
        'url': 'https://www.bet9ja.com',
        'rating': 4.3,
        'stars': '★★★★☆',
        'sports': 18,
        'app': True,
        'cashout': True,
        'live_stream': False,
        'pros': [
            "Nigeria's #1 most popular betting brand",
            'Best odds on NPFL and Super Eagles matches',
            'Fastest OPay and PalmPay withdrawals',
            'Retail shops across all 36 Nigerian states',
            'Exclusive Nigerian football jackpots',
        ],
        'cons': [
            'Available in Nigeria only',
            'No live streaming',
            'Mobile app less polished than Betway',
        ],
        'countries': {
            'nigeria': {'bonus': '₦100,000', 'min_dep': '₦100', 'lic': 'NLRC', 'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa', 'Mastercard'], 'bonus_desc': '100% match up to ₦100,000 on first deposit'},
            'ghana':   {'bonus': 'GH₵500',   'min_dep': 'GH₵5', 'lic': 'GCA',  'payments': ['MTN MoMo', 'Vodafone Cash', 'AirtelTigo', 'Visa'],        'bonus_desc': '100% match up to GH₵500 on first deposit'},
        },
    },
    {
        'slug': 'betking',
        'name': 'BetKing',
        'display': 'BetKing',
        'color': '#C0392B',
        'url': 'https://www.betking.com',
        'rating': 4.3,
        'stars': '★★★★☆',
        'sports': 22,
        'app': True,
        'cashout': True,
        'live_stream': False,
        'pros': [
            'Very competitive odds on football',
            'Fast and reliable mobile money withdrawals',
            'Good accumulator odds boosts',
            'Strong brand awareness in West Africa',
            'Excellent customer support in local languages',
        ],
        'cons': [
            'Available in 5 countries only',
            'No live streaming',
        ],
        'countries': {
            'nigeria':     {'bonus': '₦100,000',  'min_dep': '₦100',   'lic': 'NLRC', 'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa'],        'bonus_desc': '100% match up to ₦100,000 on first deposit'},
            'kenya':       {'bonus': 'KSh 5,000', 'min_dep': 'KSh 50', 'lic': 'BCLB', 'payments': ['M-Pesa', 'Airtel Money', 'Visa'],                  'bonus_desc': '100% match up to KSh 5,000 on first deposit'},
            'ghana':       {'bonus': 'GH₵500',    'min_dep': 'GH₵5',  'lic': 'GCA',   'payments': ['MTN MoMo', 'Vodafone Cash', 'AirtelTigo', 'Visa'], 'bonus_desc': '100% match up to GH₵500 on first deposit'},
            'sierra-leone':{'bonus': 'Le 200,000','min_dep': 'Le 2,000','lic': 'NLB-SL','payments': ['Orange Money', 'Africell Money', 'Visa'],         'bonus_desc': '100% match up to Le 200,000 on first deposit'},
            'ivory-coast': {'bonus': 'CFA 50,000','min_dep': 'CFA 500','lic': 'LONACI','payments': ['MTN MoMo', 'Orange Money', 'Moov Money', 'Visa'],  'bonus_desc': '100% match up to CFA 50,000 on first deposit'},
        },
    },
    {
        'slug': 'hollywoodbets',
        'name': 'Hollywoodbets',
        'display': 'Hollywoodbets',
        'color': '#6A0DAD',
        'url': 'https://www.hollywoodbets.net',
        'rating': 4.2,
        'stars': '★★★★☆',
        'sports': 16,
        'app': True,
        'cashout': True,
        'live_stream': False,
        'pros': [
            'South Africa heritage brand — trusted for 25+ years',
            'Strong horse racing and greyhound markets',
            'Best casino games selection in Africa',
            'Retail shops across South Africa',
            'Licensed in 8 African countries',
        ],
        'cons': [
            'Focused on Southern Africa — limited West/East Africa presence',
            'No live streaming',
            'Lower bonus than 1xBet',
        ],
        'countries': {
            'south-africa': {'bonus': 'R500',     'min_dep': 'R10',    'lic': 'WCGRB', 'payments': ['FNB', 'Nedbank', 'Standard Bank', 'Capitec', 'Visa', 'Mastercard'], 'bonus_desc': 'R500 sign-up free bet on first deposit'},
            'zimbabwe':     {'bonus': '$15',       'min_dep': '$1',     'lic': 'GBZ',   'payments': ['EcoCash', 'OneMoney', 'Visa', 'Mastercard'],                         'bonus_desc': '$15 free bet on first deposit'},
            'namibia':      {'bonus': 'NAD 300',   'min_dep': 'NAD 10', 'lic': 'GBN',   'payments': ['FNB Namibia', 'Bank Windhoek', 'Visa', 'Mastercard'],               'bonus_desc': 'NAD 300 free bet on first deposit'},
            'botswana':     {'bonus': 'BWP 300',   'min_dep': 'BWP 10', 'lic': 'GCAB',  'payments': ['Orange Money', 'First National', 'Visa', 'Mastercard'],              'bonus_desc': 'BWP 300 free bet on first deposit'},
            'mozambique':   {'bonus': 'MZN 300',   'min_dep': 'MZN 10', 'lic': 'GCMZ', 'payments': ['M-Pesa', 'Mkesh', 'Visa'],                                           'bonus_desc': 'MZN 300 free bet on first deposit'},
            'zambia':       {'bonus': 'ZK 400',    'min_dep': 'ZK 10',  'lic': 'GLAZ',  'payments': ['MTN MoMo', 'Airtel Money', 'Visa'],                                  'bonus_desc': 'ZK 400 free bet on first deposit'},
            'malawi':       {'bonus': 'MWK 4,000', 'min_dep': 'MWK 200','lic': 'GBM',   'payments': ['Airtel Money', 'TNM Mpamba', 'Visa'],                                'bonus_desc': 'MWK 4,000 free bet on first deposit'},
            'kenya':        {'bonus': 'KSh 3,000', 'min_dep': 'KSh 50', 'lic': 'BCLB', 'payments': ['M-Pesa', 'Airtel Money', 'Visa'],                                    'bonus_desc': 'KSh 3,000 sign-up bonus on first deposit'},
        },
    },
    {
        'slug': 'sportybet',
        'name': 'SportyBet',
        'display': 'SportyBet',
        'color': '#FF6600',
        'url': 'https://www.sportybet.com',
        'rating': 4.4,
        'stars': '★★★★☆',
        'sports': 25,
        'app': True,
        'cashout': True,
        'live_stream': True,
        'pros': [
            'Fastest withdrawal speeds in Africa — most under 5 minutes',
            'Best odds on football accumulators',
            'Excellent SuperYouWin bonus (extra 500% on accas)',
            'Live streaming available',
            'Very low minimum deposit',
        ],
        'cons': [
            'Available in 7 countries only',
            'Customer support can be slow',
        ],
        'countries': {
            'nigeria':     {'bonus': '₦500,000',  'min_dep': '₦100',   'lic': 'NLRC', 'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa'],         'bonus_desc': '100% match up to ₦500,000 on first deposit'},
            'kenya':       {'bonus': 'KSh 5,000', 'min_dep': 'KSh 50', 'lic': 'BCLB', 'payments': ['M-Pesa', 'Airtel Money', 'Visa'],                   'bonus_desc': '100% match up to KSh 5,000 on first deposit'},
            'ghana':       {'bonus': 'GH₵500',    'min_dep': 'GH₵5',  'lic': 'GCA',   'payments': ['MTN MoMo', 'Vodafone Cash', 'AirtelTigo', 'Visa'],  'bonus_desc': '100% match up to GH₵500 on first deposit'},
            'tanzania':    {'bonus': 'TSh 100,000','min_dep': 'TSh 500','lic': 'GBT',  'payments': ['M-Pesa', 'Airtel Money', 'Tigo Pesa'],               'bonus_desc': '100% match up to TSh 100,000 on first deposit'},
            'uganda':      {'bonus': 'USh 100,000','min_dep': 'USh 500','lic': 'NLB',  'payments': ['MTN MoMo', 'Airtel Money', 'Visa'],                  'bonus_desc': '100% match up to USh 100,000 on first deposit'},
            'zambia':      {'bonus': 'ZK 500',     'min_dep': 'ZK 10',  'lic': 'GLAZ', 'payments': ['MTN MoMo', 'Airtel Money', 'Visa'],                  'bonus_desc': '100% match up to ZK 500 on first deposit'},
            'ivory-coast': {'bonus': 'CFA 50,000', 'min_dep': 'CFA 500','lic': 'LONACI','payments': ['MTN MoMo', 'Orange Money', 'Moov Money', 'Visa'],  'bonus_desc': '100% match up to CFA 50,000 on first deposit'},
        },
    },
]

# ── COUNTRIES ──────────────────────────────────────────────────────────────
COUNTRIES = {
    'nigeria':      {'name': 'Nigeria',       'code': 'NG', 'flag': '🇳🇬', 'currency': 'NGN', 'symbol': '₦',    'regulator': 'NLRC (National Lottery Regulatory Commission)',        'hreflang': 'en-NG', 'lang': 'en'},
    'kenya':        {'name': 'Kenya',          'code': 'KE', 'flag': '🇰🇪', 'currency': 'KES', 'symbol': 'KSh',  'regulator': 'BCLB (Betting Control and Licensing Board)',           'hreflang': 'en-KE', 'lang': 'en'},
    'south-africa': {'name': 'South Africa',   'code': 'ZA', 'flag': '🇿🇦', 'currency': 'ZAR', 'symbol': 'R',    'regulator': 'WCGRB (Western Cape Gambling and Racing Board)',        'hreflang': 'en-ZA', 'lang': 'en'},
    'ghana':        {'name': 'Ghana',          'code': 'GH', 'flag': '🇬🇭', 'currency': 'GHS', 'symbol': 'GH₵', 'regulator': 'GCA (Ghana Gaming Commission)',                         'hreflang': 'en-GH', 'lang': 'en'},
    'tanzania':     {'name': 'Tanzania',       'code': 'TZ', 'flag': '🇹🇿', 'currency': 'TZS', 'symbol': 'TSh',  'regulator': 'GBT (Gaming Board of Tanzania)',                       'hreflang': 'en-TZ', 'lang': 'en'},
    'uganda':       {'name': 'Uganda',         'code': 'UG', 'flag': '🇺🇬', 'currency': 'UGX', 'symbol': 'USh',  'regulator': 'NLB (National Lotteries Board)',                       'hreflang': 'en-UG', 'lang': 'en'},
    'ethiopia':     {'name': 'Ethiopia',       'code': 'ET', 'flag': '🇪🇹', 'currency': 'ETB', 'symbol': 'Br',   'regulator': 'Lottery and Charitable Games Administration',          'hreflang': 'en-ET', 'lang': 'en'},
    'ivory-coast':  {'name': 'Ivory Coast',    'code': 'CI', 'flag': '🇨🇮', 'currency': 'XOF', 'symbol': 'CFA',  'regulator': 'LONACI (Loterie Nationale de Côte d\'Ivoire)',         'hreflang': 'fr-CI', 'lang': 'fr'},
    'cameroon':     {'name': 'Cameroon',       'code': 'CM', 'flag': '🇨🇲', 'currency': 'XAF', 'symbol': 'CFA',  'regulator': 'Ministry of Finance Cameroon',                         'hreflang': 'fr-CM', 'lang': 'fr'},
    'senegal':      {'name': 'Senegal',        'code': 'SN', 'flag': '🇸🇳', 'currency': 'XOF', 'symbol': 'CFA',  'regulator': 'Direction Générale des Jeux et Paris Sportifs',        'hreflang': 'fr-SN', 'lang': 'fr'},
    'rwanda':       {'name': 'Rwanda',         'code': 'RW', 'flag': '🇷🇼', 'currency': 'RWF', 'symbol': 'RWF',  'regulator': 'RGA (Rwanda Gaming Authority)',                        'hreflang': 'en-RW', 'lang': 'en'},
    'zimbabwe':     {'name': 'Zimbabwe',       'code': 'ZW', 'flag': '🇿🇼', 'currency': 'USD', 'symbol': '$',    'regulator': 'Lotteries and Gaming Board Zimbabwe',                  'hreflang': 'en-ZW', 'lang': 'en'},
    'zambia':       {'name': 'Zambia',         'code': 'ZM', 'flag': '🇿🇲', 'currency': 'ZMW', 'symbol': 'ZK',   'regulator': 'GLAZ (Gaming and Lotteries Act Zambia)',               'hreflang': 'en-ZM', 'lang': 'en'},
    'botswana':     {'name': 'Botswana',       'code': 'BW', 'flag': '🇧🇼', 'currency': 'BWP', 'symbol': 'BWP',  'regulator': 'GCAB (Gambling Control Authority Botswana)',           'hreflang': 'en-BW', 'lang': 'en'},
    'namibia':      {'name': 'Namibia',        'code': 'NA', 'flag': '🇳🇦', 'currency': 'NAD', 'symbol': 'NAD',  'regulator': 'GBN (Gambling Board of Namibia)',                      'hreflang': 'en-NA', 'lang': 'en'},
    'egypt':        {'name': 'Egypt',          'code': 'EG', 'flag': '🇪🇬', 'currency': 'EGP', 'symbol': 'EGP',  'regulator': 'Egyptian Regulatory Authority',                        'hreflang': 'ar-EG', 'lang': 'ar'},
    'morocco':      {'name': 'Morocco',        'code': 'MA', 'flag': '🇲🇦', 'currency': 'MAD', 'symbol': 'MAD',  'regulator': 'MDJS (Marocaine des Jeux et des Sports)',               'hreflang': 'fr-MA', 'lang': 'fr'},
    'angola':       {'name': 'Angola',         'code': 'AO', 'flag': '🇦🇴', 'currency': 'AOA', 'symbol': 'Kz',   'regulator': 'IRSE (Instituto Regulador de Jogos de Angola)',        'hreflang': 'pt-AO', 'lang': 'pt'},
    'dr-congo':     {'name': 'DR Congo',       'code': 'CD', 'flag': '🇨🇩', 'currency': 'CDF', 'symbol': 'CDF',  'regulator': 'Commission Nationale des Jeux de Hasard (CNJH)',       'hreflang': 'fr-CD', 'lang': 'fr'},
    'malawi':       {'name': 'Malawi',         'code': 'MW', 'flag': '🇲🇼', 'currency': 'MWK', 'symbol': 'MWK',  'regulator': 'GBM (Gaming Board of Malawi)',                         'hreflang': 'en-MW', 'lang': 'en'},
    'mozambique':   {'name': 'Mozambique',     'code': 'MZ', 'flag': '🇲🇿', 'currency': 'MZN', 'symbol': 'MT',   'regulator': 'GCMZ (Gaming Control Authority of Mozambique)',        'hreflang': 'pt-MZ', 'lang': 'pt'},
    'sierra-leone': {'name': 'Sierra Leone',   'code': 'SL', 'flag': '🇸🇱', 'currency': 'SLL', 'symbol': 'Le',   'regulator': 'National Lottery Authority Sierra Leone',              'hreflang': 'en-SL', 'lang': 'en'},
    'liberia':      {'name': 'Liberia',        'code': 'LR', 'flag': '🇱🇷', 'currency': 'LRD', 'symbol': '$',    'regulator': 'Casino Control Board Liberia',                         'hreflang': 'en-LR', 'lang': 'en'},
}


def stars_html(rating):
    full = int(rating)
    half = 1 if (rating - full) >= 0.5 else 0
    empty = 5 - full - half
    return '★' * full + ('½' if half else '') + '☆' * empty


def payments_html(payments):
    return ''.join(f'<span class="pay-chip">{p}</span>' for p in payments)


def pros_html(pros):
    return ''.join(f'<li>{p}</li>' for p in pros)


def cons_html(cons):
    return ''.join(f'<li>{c}</li>' for c in cons)


def build_page(bk, country_slug, country, combo):
    name = bk['name']
    cname = country['name']
    code = country['code']
    flag = country['flag']
    regulator = country['regulator']
    hreflang = country['hreflang']
    bonus = combo['bonus']
    min_dep = combo['min_dep']
    lic = combo['lic']
    payments = combo['payments']
    bonus_desc = combo['bonus_desc']
    url = bk['url']
    color = bk['color']
    rating = bk['rating']
    sports = bk['sports']
    bk_slug = bk['slug']
    assets = '../../../'
    canonical = f'https://sifufinds.com/bookmakers/{bk_slug}/{country_slug}/'

    title = seo_title(f'{name} {cname} Review 2026')
    description = f'Independent {name} {cname} review 2026. {bonus_desc}. Accepts {payments[0]} and {payments[1] if len(payments) > 1 else "cards"}. Licensed by {lic}. Verified by SifuFinds. Updated June 2026.'
    keywords = f'{name.lower()} {cname.lower()}, {name.lower()} {cname.lower()} review 2026, {name.lower()} {cname.lower()} bonus, {name.lower()} {cname.lower()} registration, {name.lower()} {cname.lower()} app, {name.lower()} {cname.lower()} withdrawal'

    pay_str = payments_html(payments)
    pro_str = pros_html(bk['pros'])
    con_str = cons_html(bk['cons'])
    stars_str = stars_html(rating)

    faq_items = [
        (f'Is {name} legal in {cname}?',
         f'{name} is licensed and regulated in {cname} by <strong>{lic}</strong>. It is legal to bet with {name} in {cname}. All {cname} bettors are protected under local gambling regulations.'),
        (f'What is the {name} {cname} welcome bonus?',
         f'The current {name} {cname} welcome bonus is <strong>{bonus_desc}</strong>. Minimum deposit is {min_dep}. Bonus must be wagered before withdrawal. Always check {name}\'s official site for the latest T&Cs.'),
        (f'How do I register on {name} {cname}?',
         f'To register on {name} in {cname}: (1) Visit {name}\'s website, (2) Click \'Register\' or \'Join Now\', (3) Enter your {cname} phone number and personal details, (4) Verify your ID as required by {lic}, (5) Make your first deposit to claim the welcome bonus.'),
        (f'How do I withdraw from {name} in {cname}?',
         f'{name} processes withdrawals in {cname} via {", ".join(payments[:2])}. Most withdrawals are processed within 1–24 hours. Minimum withdrawal amount varies — check the {name} {cname} cashier for current limits.'),
        (f'Does {name} have an app for {cname}?',
         f'{"Yes. " + name + " has a dedicated mobile app for " + cname + " available on Android and iOS. Download directly from the " + name + " website." if bk["app"] else name + " offers a fully optimised mobile website for " + cname + " bettors. Download is not required."}'),
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

    # Rating stars visual
    rating_int = int(rating)
    stars_display = '★' * rating_int + ('½' if (rating - rating_int) >= 0.5 else '') + '☆' * (5 - rating_int - (1 if (rating - rating_int) >= 0.5 else 0))

    return f'''<!DOCTYPE html>
<!-- sifufinds.com/bookmakers/{bk_slug}/{country_slug}/ — {name} {cname} Review 2026 -->
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
<meta name="author" content="SifuFinds Editorial Team">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="{hreflang}" href="{canonical}">
<link rel="alternate" hreflang="en" href="{canonical}">
<meta name="geo.region" content="{code}">
<meta name="geo.placename" content="{cname}">

<meta property="og:type" content="website">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="{name} {cname} Review 2026 | SifuFinds">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="https://sifufinds.com/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_GB">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@sifufinds">
<meta name="twitter:title" content="{name} {cname} Review 2026 | SifuFinds">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="https://sifufinds.com/assets/og-image.png">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "Review",
      "@id": "{canonical}#review",
      "itemReviewed": {{
        "@type": "Organization",
        "name": "{name} {cname}",
        "url": "{url}",
        "description": "{name} — licensed betting operator in {cname}"
      }},
      "reviewRating": {{
        "@type": "Rating",
        "ratingValue": "{rating}",
        "bestRating": "5",
        "worstRating": "1"
      }},
      "author": {{"@type": "Organization", "name": "SifuFinds", "url": "https://sifufinds.com"}},
      "publisher": {{"@type": "Organization", "name": "SifuFinds"}},
      "datePublished": "2026-06-01",
      "dateModified": "2026-06-07",
      "name": "{name} {cname} Review 2026"
    }},
    {{
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://sifufinds.com/"}},
        {{"@type": "ListItem", "position": 2, "name": "Bookmaker Reviews", "item": "https://sifufinds.com/bookmakers/"}},
        {{"@type": "ListItem", "position": 3, "name": "{name} Africa Review", "item": "https://sifufinds.com/bookmakers/{bk_slug}/"}},
        {{"@type": "ListItem", "position": 4, "name": "{name} {cname} Review", "item": "{canonical}"}}
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
.bkr-hero{{background:linear-gradient(135deg,{color} 0%,{color}cc 100%);color:#fff;padding:28px 0}}
.bkr-hero h1{{font-size:clamp(20px,3.5vw,30px);font-weight:900;margin-bottom:8px;letter-spacing:-.5px}}
.bkr-hero p{{font-size:14px;color:rgba(255,255,255,.85);max-width:640px;line-height:1.65}}
.rating-big{{font-size:30px;font-weight:900;color:#fff;display:flex;align-items:center;gap:8px;margin-top:8px}}
.stars-big{{color:#fbbf24;font-size:20px}}
.verdict-badge{{display:inline-block;background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.4);color:#fff;font-size:12px;font-weight:700;padding:4px 12px;border-radius:6px;margin-top:8px}}
.review-meta{{display:flex;gap:16px;flex-wrap:wrap;margin-top:10px}}
.review-meta span{{font-size:12px;color:rgba(255,255,255,.8)}}
.score-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px;margin-top:10px}}
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
.info-table{{width:100%;border-collapse:collapse;margin-top:10px}}
.info-table tr:nth-child(even){{background:#f9f9f9}}
.info-table td{{padding:9px 12px;font-size:13px;border-bottom:1px solid #eee;line-height:1.5}}
.info-table td:first-child{{font-weight:700;color:#555;width:40%}}
@media(max-width:600px){{.pros-cons{{grid-template-columns:1fr}}}}
</style>
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
</head>
<body>

<div class="tbar">
  <div class="tbar-l">
    <a href="{assets}">🏠 Home</a>
    <a href="{assets}best-bonus-in-{country_slug}/">{flag} {cname}</a>
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

<div class="bkr-hero">
  <div class="wrap">
    <h1>{flag} {name} {cname} Review 2026 — {bonus_desc}</h1>
    <p>Independent review of {name} in {cname} by SifuFinds. {bonus_desc}. Accepts {", ".join(payments[:3])}. Licensed by {lic}. Updated June 2026.</p>
    <div class="rating-big"><span>{rating}/5</span><span class="stars-big">{stars_display}</span></div>
    <div class="verdict-badge">✅ Recommended — Licensed by {lic}</div>
    <div class="review-meta">
      <span>📅 Reviewed June 2026</span>
      <span>✅ {lic}</span>
      <span>🌍 {cname}</span>
      <span>📱 {"App available" if bk["app"] else "Mobile web"}</span>
    </div>
  </div>
</div>

<div class="sec-bg"><div class="wrap" style="padding-top:14px">
  <div class="breadcrumb">
    <a href="{assets}">Home</a><span>›</span>
    <a href="{assets}bookmakers/">Bookmaker Reviews</a><span>›</span>
    <a href="{assets}bookmakers/{bk_slug}/">{name} Africa</a><span>›</span>
    {name} {cname}
  </div>

  <div class="adv">📢 <strong>Advertiser Disclosure:</strong> SifuFinds may earn commission if you sign up via our links. This does not affect our ratings. Always check {name}'s official site for current T&Cs.</div>

  <div class="claim-box">
    <h3>🎁 {name} {cname} Bonus — June 2026</h3>
    <p>{bonus_desc} · Min deposit: {min_dep}</p>
    <a class="claim-btn" href="{url}" target="_blank" rel="noopener noreferrer sponsored">Claim {name} {cname} Bonus →</a>
    <p style="font-size:11px;color:#888;margin-top:8px;margin-bottom:0">T&amp;Cs Apply · 18+ only · {cname} residents only</p>
  </div>

  <div class="cbox2">
    <h2>{name} {cname} — Quick Facts</h2>
    <table class="info-table">
      <tr><td>Welcome Bonus</td><td><strong>{bonus}</strong> — {bonus_desc}</td></tr>
      <tr><td>Minimum Deposit</td><td>{min_dep}</td></tr>
      <tr><td>Licence</td><td>{lic}</td></tr>
      <tr><td>Sports Markets</td><td>{sports}+ sports covered</td></tr>
      <tr><td>Mobile App</td><td>{"✅ Available for Android & iOS" if bk["app"] else "📱 Mobile-optimised website"}</td></tr>
      <tr><td>Cash Out</td><td>{"✅ Available on all markets" if bk["cashout"] else "❌ Not available"}</td></tr>
      <tr><td>Live Streaming</td><td>{"✅ Available" if bk["live_stream"] else "❌ Not available"}</td></tr>
      <tr><td>Payment Methods</td><td>{", ".join(payments)}</td></tr>
    </table>
  </div>

  <div class="cbox2">
    <h2>{name} {cname} — Rating Breakdown</h2>
    <div class="score-grid">
      <div class="score-item"><div class="score-num">{rating}</div><div class="score-lbl">Overall</div></div>
      <div class="score-item"><div class="score-num">{min(5.0, rating + 0.1):.1f}</div><div class="score-lbl">Welcome Bonus</div></div>
      <div class="score-item"><div class="score-num">{min(5.0, rating - 0.1):.1f}</div><div class="score-lbl">Odds Quality</div></div>
      <div class="score-item"><div class="score-num">{min(5.0, rating + 0.2):.1f}</div><div class="score-lbl">Payments</div></div>
      <div class="score-item"><div class="score-num">{min(5.0, rating - 0.2):.1f}</div><div class="score-lbl">App / UX</div></div>
      <div class="score-item"><div class="score-num">5.0</div><div class="score-lbl">Licensing</div></div>
    </div>
  </div>

  <div class="cbox2">
    <h2>{name} {cname} — Pros &amp; Cons</h2>
    <div class="pros-cons">
      <div class="pros"><h3>Pros</h3><ul>{pro_str}</ul></div>
      <div class="cons"><h3>Cons</h3><ul>{con_str}</ul></div>
    </div>
  </div>

  <div class="cbox2">
    <h2>{name} {cname} — Payment Methods</h2>
    <p>Accepted payment methods at {name} for {cname} bettors:</p>
    <div class="pay-grid">{pay_str}</div>
    <p style="margin-top:10px;font-size:13px;color:#555">Minimum deposit: <strong>{min_dep}</strong> · Withdrawals processed within 1–24 hours.</p>
  </div>

  <div class="cbox2">
    <h2>Is {name} Legal in {cname}?</h2>
    <p>{name} is <strong>licensed and regulated</strong> in {cname} by the <strong>{lic} ({regulator})</strong>. Sports betting is legal in {cname} for residents aged 18 and over. {name} complies with all local licensing requirements and responsible gambling standards.</p>
  </div>

  <div class="cbox2" style="border:2px solid #4ade80">
    <h2>SifuFinds Verdict — Is {name} Worth It in {cname}?</h2>
    <p style="font-size:13.5px;color:#333;line-height:1.75">{name} is a <strong>{rating}/5 rated</strong> bookmaker for {cname} bettors. It is licensed by <strong>{lic}</strong>, accepts {", ".join(payments[:2])}, and offers <strong>{bonus_desc}</strong> for new customers. With {sports}+ sports markets{"and live streaming" if bk["live_stream"] else ""}, it is one of the best options for {cname} sports bettors in 2026.</p>
    <div style="text-align:center;margin-top:12px">
      <a class="claim-btn" style="display:inline-block" href="{url}" target="_blank" rel="noopener noreferrer sponsored">Get {name} {cname} Bonus →</a>
    </div>
  </div>

  <div class="cbox2">
    <h2>Frequently Asked Questions — {name} {cname}</h2>
{faq_html}  </div>

  <div class="cbox2">
    <h2>Compare {name} With Other {cname} Bookmakers</h2>
    <div id="compare-books"></div>
    <div style="text-align:center;margin-top:12px">
      <a href="{assets}best-bonus-in-{country_slug}/" style="display:inline-block;background:var(--g);color:#fff;padding:10px 22px;border-radius:7px;font-size:13px;font-weight:800;text-decoration:none">All {cname} Bookmakers →</a>
    </div>
  </div>

  <div class="resp">⚠️ Gambling involves risk. Only bet what you can afford to lose. 18+ only. If gambling is causing you harm, call the national helpline.</div>
</div></div>

<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison<br>
  <a href="{assets}">Home</a> · <a href="{assets}best-bonus-in-{country_slug}/">{cname} Betting</a> · <a href="{assets}bookmakers/{bk_slug}/">{name} Africa Review</a> · <a href="{assets}tips/">Tips</a> · <a href="{assets}blog/">Blog</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only.
</div>

<div class="page-modal-bg" id="page-modal"><div class="page-modal"><button class="page-modal-close" onclick="closePage()">×</button><div class="pm" id="page-content"></div></div></div>

<script src="{assets}assets/shared.js?v=20"></script>
<script>
const SITE={{home:'{assets}',tips:'{assets}tips/',casino:'{assets}casino/',odds:'{assets}odds/',countries:'{assets}countries/'}};
const _BK_CTY='{code}';
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
function init(){{
  const sel=document.getElementById('ctySel');
  if(sel)sel.value=_BK_CTY;
  H('foot-yr',NOW.getFullYear());
  const books=(BOOKS[_BK_CTY]||BOOKS.NG).slice(0,4);
  const el=document.getElementById('compare-books');
  if(el&&books.length){{el.innerHTML=books.map((b,i)=>bookCard(b,i,i)).join('');}}
}}
init();
</script>
</body>
</html>'''


def main():
    created = 0
    for bk in BOOKMAKERS:
        bk_slug = bk['slug']
        for country_slug, combo in bk['countries'].items():
            country = COUNTRIES.get(country_slug)
            if not country:
                print(f'⚠  Unknown country: {country_slug}')
                continue

            out_dir = os.path.join(BASE, 'bookmakers', bk_slug, country_slug)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, 'index.html')

            html = build_page(bk, country_slug, country, combo)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(html)
            created += 1
            print(f'  ✓  {out_path.replace(BASE + "/", "")}')

    print(f'\n✅  {created} bookmaker × country pages generated.')


if __name__ == '__main__':
    main()
