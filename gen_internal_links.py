#!/usr/bin/env python3
"""Inject internal linking sections into all country index pages.

Adds a 'More Betting Guides' block linking to:
- City pages within that country
- Bookmaker × country pages
- Payment × country pages
- Sport × country pages
"""

import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

# Country metadata with all their relevant subpages
COUNTRIES = {
    'nigeria': {
        'name': 'Nigeria', 'flag': '🇳🇬', 'code': 'NG',
        'cities': [
            ('Lagos', 'lagos'), ('Abuja', 'abuja'), ('Kano', 'kano'),
            ('Ibadan', 'ibadan'), ('Port Harcourt', 'port-harcourt'),
            ('Benin City', 'benin-city'), ('Enugu', 'enugu'), ('Kaduna', 'kaduna'),
            ('Onitsha', 'onitsha'), ('Warri', 'warri'), ('Jos', 'jos'),
            ('Aba', 'aba'), ('Ilorin', 'ilorin'), ('Owerri', 'owerri'),
            ('Calabar', 'calabar'), ('Uyo', 'uyo'), ('Abeokuta', 'abeokuta'),
        ],
        'bookmakers': ['betway-africa', '1xbet-africa', 'bet9ja', 'betking', 'sportybet'],
        'bookmaker_names': ['Betway Nigeria', '1xBet Nigeria', 'Bet9ja', 'BetKing Nigeria', 'SportyBet Nigeria'],
        'payments': ['opay-betting-sites', 'mtn-momo-betting-sites', 'airtel-money-betting', 'bank-transfer-betting'],
        'payment_names': ['OPay Betting', 'MTN MoMo Betting', 'Airtel Money Betting', 'Bank Transfer Betting'],
        'sports': ['football-betting', 'basketball-betting', 'cricket-betting', 'tennis-betting'],
        'sport_names': ['Football Betting', 'Basketball Betting', 'Cricket Betting', 'Tennis Betting'],
    },
    'kenya': {
        'name': 'Kenya', 'flag': '🇰🇪', 'code': 'KE',
        'cities': [
            ('Nairobi', 'nairobi'), ('Mombasa', 'mombasa'), ('Kisumu', 'kisumu'),
            ('Nakuru', 'nakuru'), ('Eldoret', 'eldoret'), ('Thika', 'thika'),
            ('Malindi', 'malindi'), ('Kitale', 'kitale'), ('Nyeri', 'nyeri'),
        ],
        'bookmakers': ['betway-africa', '1xbet-africa', 'sportpesa', 'betking', 'hollywoodbets', 'sportybet'],
        'bookmaker_names': ['Betway Kenya', '1xBet Kenya', 'SportPesa Kenya', 'BetKing Kenya', 'Hollywoodbets Kenya', 'SportyBet Kenya'],
        'payments': ['mpesa-betting-sites', 'airtel-money-betting', 'bank-transfer-betting'],
        'payment_names': ['M-Pesa Betting', 'Airtel Money Betting', 'Bank Transfer Betting'],
        'sports': ['football-betting', 'basketball-betting', 'cricket-betting', 'rugby-betting', 'tennis-betting'],
        'sport_names': ['Football Betting', 'Basketball Betting', 'Cricket Betting', 'Rugby Betting', 'Tennis Betting'],
    },
    'ghana': {
        'name': 'Ghana', 'flag': '🇬🇭', 'code': 'GH',
        'cities': [
            ('Accra', 'accra'), ('Kumasi', 'kumasi'), ('Tamale', 'tamale'),
            ('Sekondi-Takoradi', 'sekondi-takoradi'), ('Cape Coast', 'cape-coast'), ('Ho', 'ho'),
        ],
        'bookmakers': ['betway-africa', '1xbet-africa', 'sportpesa', 'bet9ja', 'betking', 'sportybet'],
        'bookmaker_names': ['Betway Ghana', '1xBet Ghana', 'SportPesa Ghana', 'Bet9ja Ghana', 'BetKing Ghana', 'SportyBet Ghana'],
        'payments': ['mtn-momo-betting-sites', 'opay-betting-sites', 'bank-transfer-betting'],
        'payment_names': ['MTN MoMo Betting', 'OPay Betting', 'Bank Transfer Betting'],
        'sports': ['football-betting', 'basketball-betting', 'cricket-betting', 'tennis-betting'],
        'sport_names': ['Football Betting', 'Basketball Betting', 'Cricket Betting', 'Tennis Betting'],
    },
    'south-africa': {
        'name': 'South Africa', 'flag': '🇿🇦', 'code': 'ZA',
        'cities': [
            ('Johannesburg', 'johannesburg'), ('Cape Town', 'cape-town'),
            ('Durban', 'durban'), ('Pretoria', 'pretoria'),
            ('Port Elizabeth', 'port-elizabeth'), ('Bloemfontein', 'bloemfontein'),
        ],
        'bookmakers': ['betway-africa', '1xbet-africa', 'sportpesa', 'hollywoodbets'],
        'bookmaker_names': ['Betway South Africa', '1xBet South Africa', 'SportPesa SA', 'Hollywoodbets SA'],
        'payments': ['mtn-momo-betting-sites', 'bank-transfer-betting', 'vodacom-betting-sites'],
        'payment_names': ['MTN MoMo Betting', 'Bank Transfer Betting', 'Vodacom Betting'],
        'sports': ['football-betting', 'basketball-betting', 'cricket-betting', 'rugby-betting', 'tennis-betting'],
        'sport_names': ['Football Betting', 'Basketball Betting', 'Cricket Betting', 'Rugby Betting', 'Tennis Betting'],
    },
    'tanzania': {
        'name': 'Tanzania', 'flag': '🇹🇿', 'code': 'TZ',
        'cities': [
            ('Dar es Salaam', 'dar-es-salaam'), ('Arusha', 'arusha'), ('Mwanza', 'mwanza'),
            ('Dodoma', 'dodoma'), ('Moshi', 'moshi'), ('Zanzibar City', 'zanzibar'),
        ],
        'bookmakers': ['betway-africa', '1xbet-africa', 'sportpesa', 'sportybet'],
        'bookmaker_names': ['Betway Tanzania', '1xBet Tanzania', 'SportPesa Tanzania', 'SportyBet Tanzania'],
        'payments': ['mpesa-betting-sites', 'airtel-money-betting', 'vodacom-betting-sites', 'bank-transfer-betting'],
        'payment_names': ['M-Pesa Betting', 'Airtel Money Betting', 'Vodacom Betting', 'Bank Transfer Betting'],
        'sports': ['football-betting'],
        'sport_names': ['Football Betting'],
    },
    'uganda': {
        'name': 'Uganda', 'flag': '🇺🇬', 'code': 'UG',
        'cities': [
            ('Kampala', 'kampala'), ('Gulu', 'gulu'), ('Mbarara', 'mbarara'), ('Jinja', 'jinja'),
        ],
        'bookmakers': ['betway-africa', '1xbet-africa', 'sportpesa', 'sportybet'],
        'bookmaker_names': ['Betway Uganda', '1xBet Uganda', 'SportPesa Uganda', 'SportyBet Uganda'],
        'payments': ['mtn-momo-betting-sites', 'airtel-money-betting', 'bank-transfer-betting'],
        'payment_names': ['MTN MoMo Betting', 'Airtel Money Betting', 'Bank Transfer Betting'],
        'sports': ['football-betting'],
        'sport_names': ['Football Betting'],
    },
    'ethiopia': {
        'name': 'Ethiopia', 'flag': '🇪🇹', 'code': 'ET',
        'cities': [
            ('Addis Ababa', 'addis-ababa'), ('Dire Dawa', 'dire-dawa'), ('Hawassa', 'hawassa'),
        ],
        'bookmakers': ['1xbet-africa'],
        'bookmaker_names': ['1xBet Ethiopia'],
        'payments': ['telebirr-betting', 'bank-transfer-betting'],
        'payment_names': ['Telebirr Betting', 'Bank Transfer Betting'],
        'sports': ['football-betting'],
        'sport_names': ['Football Betting'],
    },
    'ivory-coast': {
        'name': 'Ivory Coast', 'flag': '🇨🇮', 'code': 'CI',
        'cities': [
            ('Abidjan', 'abidjan'), ('Bouaké', 'bouake'),
        ],
        'bookmakers': ['1xbet-africa', 'betking', 'sportybet'],
        'bookmaker_names': ['1xBet Ivory Coast', 'BetKing Ivory Coast', 'SportyBet Ivory Coast'],
        'payments': ['mtn-momo-betting-sites', 'orange-money-betting'],
        'payment_names': ['MTN MoMo Betting', 'Orange Money Betting'],
        'sports': ['football-betting'],
        'sport_names': ['Football Betting'],
    },
    'cameroon': {
        'name': 'Cameroon', 'flag': '🇨🇲', 'code': 'CM',
        'cities': [
            ('Douala', 'douala'), ('Yaoundé', 'yaounde'),
        ],
        'bookmakers': ['betway-africa', '1xbet-africa'],
        'bookmaker_names': ['Betway Cameroon', '1xBet Cameroon'],
        'payments': ['mtn-momo-betting-sites', 'orange-money-betting'],
        'payment_names': ['MTN MoMo Betting', 'Orange Money Betting'],
        'sports': ['football-betting'],
        'sport_names': ['Football Betting'],
    },
    'senegal': {
        'name': 'Senegal', 'flag': '🇸🇳', 'code': 'SN',
        'cities': [('Dakar', 'dakar')],
        'bookmakers': ['1xbet-africa'],
        'bookmaker_names': ['1xBet Senegal'],
        'payments': ['orange-money-betting', 'bank-transfer-betting'],
        'payment_names': ['Orange Money Betting', 'Bank Transfer Betting'],
        'sports': ['football-betting', 'basketball-betting'],
        'sport_names': ['Football Betting', 'Basketball Betting'],
    },
    'rwanda': {
        'name': 'Rwanda', 'flag': '🇷🇼', 'code': 'RW',
        'cities': [('Kigali', 'kigali')],
        'bookmakers': ['betway-africa', '1xbet-africa'],
        'bookmaker_names': ['Betway Rwanda', '1xBet Rwanda'],
        'payments': ['mtn-momo-betting-sites', 'airtel-money-betting'],
        'payment_names': ['MTN MoMo Betting', 'Airtel Money Betting'],
        'sports': ['football-betting'],
        'sport_names': ['Football Betting'],
    },
    'zimbabwe': {
        'name': 'Zimbabwe', 'flag': '🇿🇼', 'code': 'ZW',
        'cities': [('Harare', 'harare'), ('Bulawayo', 'bulawayo')],
        'bookmakers': ['betway-africa', '1xbet-africa', 'hollywoodbets'],
        'bookmaker_names': ['Betway Zimbabwe', '1xBet Zimbabwe', 'Hollywoodbets Zimbabwe'],
        'payments': ['ecocash-betting'],
        'payment_names': ['EcoCash Betting'],
        'sports': ['football-betting', 'cricket-betting', 'rugby-betting'],
        'sport_names': ['Football Betting', 'Cricket Betting', 'Rugby Betting'],
    },
    'zambia': {
        'name': 'Zambia', 'flag': '🇿🇲', 'code': 'ZM',
        'cities': [('Lusaka', 'lusaka'), ('Ndola', 'ndola'), ('Livingstone', 'livingstone')],
        'bookmakers': ['betway-africa', '1xbet-africa', 'hollywoodbets', 'sportybet'],
        'bookmaker_names': ['Betway Zambia', '1xBet Zambia', 'Hollywoodbets Zambia', 'SportyBet Zambia'],
        'payments': ['mtn-momo-betting-sites', 'airtel-money-betting'],
        'payment_names': ['MTN MoMo Betting', 'Airtel Money Betting'],
        'sports': ['football-betting'],
        'sport_names': ['Football Betting'],
    },
    'egypt': {
        'name': 'Egypt', 'flag': '🇪🇬', 'code': 'EG',
        'cities': [('Cairo', 'cairo'), ('Alexandria', 'alexandria')],
        'bookmakers': ['1xbet-africa'],
        'bookmaker_names': ['1xBet Egypt'],
        'payments': ['opay-betting-sites', 'bank-transfer-betting'],
        'payment_names': ['OPay Betting', 'Bank Transfer Betting'],
        'sports': ['football-betting', 'basketball-betting', 'tennis-betting'],
        'sport_names': ['Football Betting', 'Basketball Betting', 'Tennis Betting'],
    },
    'morocco': {
        'name': 'Morocco', 'flag': '🇲🇦', 'code': 'MA',
        'cities': [('Casablanca', 'casablanca'), ('Rabat', 'rabat'), ('Marrakech', 'marrakech'), ('Fès', 'fes')],
        'bookmakers': ['1xbet-africa'],
        'bookmaker_names': ['1xBet Morocco'],
        'payments': ['orange-money-betting', 'bank-transfer-betting'],
        'payment_names': ['Orange Money Betting', 'Bank Transfer Betting'],
        'sports': ['football-betting', 'tennis-betting'],
        'sport_names': ['Football Betting', 'Tennis Betting'],
    },
    'angola': {
        'name': 'Angola', 'flag': '🇦🇴', 'code': 'AO',
        'cities': [('Luanda', 'luanda'), ('Huambo', 'huambo')],
        'bookmakers': ['1xbet-africa'],
        'bookmaker_names': ['1xBet Angola'],
        'payments': ['bank-transfer-betting'],
        'payment_names': ['Bank Transfer Betting'],
        'sports': ['football-betting'],
        'sport_names': ['Football Betting'],
    },
    'dr-congo': {
        'name': 'DR Congo', 'flag': '🇨🇩', 'code': 'CD',
        'cities': [('Kinshasa', 'kinshasa'), ('Lubumbashi', 'lubumbashi')],
        'bookmakers': ['1xbet-africa'],
        'bookmaker_names': ['1xBet DR Congo'],
        'payments': ['mpesa-betting-sites', 'airtel-money-betting', 'vodacom-betting-sites'],
        'payment_names': ['M-Pesa Betting', 'Airtel Money Betting', 'Vodacom Betting'],
        'sports': ['football-betting'],
        'sport_names': ['Football Betting'],
    },
    'botswana': {
        'name': 'Botswana', 'flag': '🇧🇼', 'code': 'BW',
        'cities': [('Gaborone', 'gaborone')],
        'bookmakers': ['betway-africa', '1xbet-africa', 'hollywoodbets'],
        'bookmaker_names': ['Betway Botswana', '1xBet Botswana', 'Hollywoodbets Botswana'],
        'payments': [],
        'payment_names': [],
        'sports': ['football-betting', 'rugby-betting'],
        'sport_names': ['Football Betting', 'Rugby Betting'],
    },
    'namibia': {
        'name': 'Namibia', 'flag': '🇳🇦', 'code': 'NA',
        'cities': [('Windhoek', 'windhoek')],
        'bookmakers': ['betway-africa', '1xbet-africa', 'hollywoodbets'],
        'bookmaker_names': ['Betway Namibia', '1xBet Namibia', 'Hollywoodbets Namibia'],
        'payments': [],
        'payment_names': [],
        'sports': ['football-betting', 'rugby-betting'],
        'sport_names': ['Football Betting', 'Rugby Betting'],
    },
    'malawi': {
        'name': 'Malawi', 'flag': '🇲🇼', 'code': 'MW',
        'cities': [('Lilongwe', 'lilongwe'), ('Blantyre', 'blantyre')],
        'bookmakers': ['betway-africa', '1xbet-africa', 'hollywoodbets'],
        'bookmaker_names': ['Betway Malawi', '1xBet Malawi', 'Hollywoodbets Malawi'],
        'payments': ['airtel-money-betting'],
        'payment_names': ['Airtel Money Betting'],
        'sports': ['football-betting'],
        'sport_names': ['Football Betting'],
    },
    'mozambique': {
        'name': 'Mozambique', 'flag': '🇲🇿', 'code': 'MZ',
        'cities': [('Maputo', 'maputo'), ('Beira', 'beira')],
        'bookmakers': ['betway-africa', '1xbet-africa', 'hollywoodbets'],
        'bookmaker_names': ['Betway Mozambique', '1xBet Mozambique', 'Hollywoodbets Mozambique'],
        'payments': ['mpesa-betting-sites', 'vodacom-betting-sites'],
        'payment_names': ['M-Pesa Betting', 'Vodacom Betting'],
        'sports': ['football-betting'],
        'sport_names': ['Football Betting'],
    },
    'sierra-leone': {
        'name': 'Sierra Leone', 'flag': '🇸🇱', 'code': 'SL',
        'cities': [('Freetown', 'freetown'), ('Bo', 'bo')],
        'bookmakers': ['1xbet-africa', 'betking'],
        'bookmaker_names': ['1xBet Sierra Leone', 'BetKing Sierra Leone'],
        'payments': ['orange-money-betting'],
        'payment_names': ['Orange Money Betting'],
        'sports': ['football-betting'],
        'sport_names': ['Football Betting'],
    },
    'liberia': {
        'name': 'Liberia', 'flag': '🇱🇷', 'code': 'LR',
        'cities': [('Monrovia', 'monrovia')],
        'bookmakers': ['1xbet-africa'],
        'bookmaker_names': ['1xBet Liberia'],
        'payments': ['orange-money-betting', 'mtn-momo-betting-sites'],
        'payment_names': ['Orange Money Betting', 'MTN MoMo Betting'],
        'sports': ['football-betting'],
        'sport_names': ['Football Betting'],
    },
}


def build_links_block(country_slug: str, c: dict) -> str:
    """Build an HTML block with internal links to all related pages."""
    cname = c['name']
    flag = c['flag']

    # Cities section
    cities_html = ''
    if c['cities']:
        city_links = ' · '.join(
            f'<a href="./{city_slug}/" style="color:#1a6b35;text-decoration:none;font-weight:600">{city_name}</a>'
            for city_name, city_slug in c['cities'][:12]
        )
        cities_html = f'''
  <div class="cbox2" style="margin-top:12px">
    <h2>Betting Sites by City — {cname}</h2>
    <p>Find the best licensed bookmakers in your city:</p>
    <p style="font-size:13px;line-height:2">{city_links}</p>
  </div>'''

    # Bookmaker guides
    bk_html = ''
    if c['bookmakers']:
        bk_links = []
        for bk_slug, bk_name in zip(c['bookmakers'], c['bookmaker_names']):
            bk_links.append(
                f'<a href="../../bookmakers/{bk_slug}/{country_slug}/" '
                f'style="display:inline-block;background:#edf7f0;border:1px solid #c8e6c9;'
                f'border-radius:6px;padding:6px 12px;font-size:12px;font-weight:700;'
                f'color:#1a6b35;text-decoration:none;margin:3px">{bk_name}</a>'
            )
        bk_html = f'''
  <div class="cbox2" style="margin-top:12px">
    <h2>Bookmaker Reviews — {cname}</h2>
    <p>Read our independent reviews of all bookmakers licensed in {cname}:</p>
    <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">
      {''.join(bk_links)}
    </div>
  </div>'''

    # Payment methods
    pm_html = ''
    if c['payments']:
        pm_links = []
        for pm_slug, pm_name in zip(c['payments'], c['payment_names']):
            pm_links.append(
                f'<a href="../../betting/{pm_slug}/{country_slug}/" '
                f'style="display:inline-block;background:#fff8e1;border:1px solid #fdd835;'
                f'border-radius:6px;padding:6px 12px;font-size:12px;font-weight:700;'
                f'color:#f57f17;text-decoration:none;margin:3px">{pm_name}</a>'
            )
        pm_html = f'''
  <div class="cbox2" style="margin-top:12px">
    <h2>Payment Methods — {cname}</h2>
    <p>Deposit and withdraw at licensed {cname} bookmakers using these payment methods:</p>
    <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">
      {''.join(pm_links)}
    </div>
  </div>'''

    # Sports betting
    sp_html = ''
    if c['sports']:
        sp_links = []
        for sp_slug, sp_name in zip(c['sports'], c['sport_names']):
            sp_links.append(
                f'<a href="../../betting/{sp_slug}/{country_slug}/" '
                f'style="display:inline-block;background:#e3f2fd;border:1px solid #90caf9;'
                f'border-radius:6px;padding:6px 12px;font-size:12px;font-weight:700;'
                f'color:#1565c0;text-decoration:none;margin:3px">{sp_name}</a>'
            )
        sp_html = f'''
  <div class="cbox2" style="margin-top:12px">
    <h2>Sports Betting — {cname}</h2>
    <p>Find the best odds and bonuses for each sport at licensed {cname} bookmakers:</p>
    <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">
      {''.join(sp_links)}
    </div>
  </div>'''

    return f'''\n  <!-- ── INTERNAL LINKS BLOCK (auto-generated by gen_internal_links.py) ── -->{cities_html}{bk_html}{pm_html}{sp_html}\n  <!-- ── END INTERNAL LINKS BLOCK ── -->'''


INJECT_MARKER = '<div class="resp">⚠️ Gambling involves risk.'


def update_country_page(country_slug: str, c: dict) -> bool:
    path = os.path.join(BASE, 'countries', country_slug, 'index.html')
    if not os.path.exists(path):
        print(f'  ⚠  Missing: countries/{country_slug}/index.html')
        return False

    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Skip if already injected
    if 'auto-generated by gen_internal_links.py' in html:
        print(f'  ⟳  Already updated: countries/{country_slug}/index.html')
        return False

    links_block = build_links_block(country_slug, c)

    if INJECT_MARKER not in html:
        print(f'  ⚠  Marker not found in countries/{country_slug}/index.html')
        return False

    # Inject before the responsibility disclaimer
    new_html = html.replace(INJECT_MARKER, links_block + '\n\n  ' + INJECT_MARKER, 1)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_html)

    return True


def main():
    updated = 0
    for country_slug, c in COUNTRIES.items():
        result = update_country_page(country_slug, c)
        if result:
            updated += 1
            print(f'  ✓  countries/{country_slug}/index.html — links injected')

    print(f'\n✅  {updated} country pages updated with internal links.')


if __name__ == '__main__':
    main()
