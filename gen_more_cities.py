#!/usr/bin/env python3
"""Generate additional city-level betting pages."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_city_pages import make_city_page, BASE

CITIES = [
    {
        'path': 'countries/nigeria/abuja',
        'slug': 'abuja',
        'city': 'Abuja',
        'country': 'Nigeria',
        'country_code': 'NG',
        'country_slug': 'nigeria',
        'flag': '🇳🇬',
        'currency': 'NGN',
        'symbol': '₦',
        'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'population': "Nigeria's Federal Capital Territory with 3+ million people",
        'about': "Abuja is Nigeria's Federal Capital Territory and a fast-growing betting market. As the seat of the Nigerian government, Abuja bettors are served by all NLRC-licensed bookmakers with major retail shops across Wuse, Garki, and Maitama. OPay and PalmPay enable instant mobile betting for Abuja's tech-savvy population.",
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa', 'Mastercard'],
        'popular_leagues': ['NPFL (Abuja teams)', 'Premier League', 'CAF Champions League', 'AFCON', 'World Cup 2026'],
        'assets_prefix': '../../../',
        'country_prefix': '../../',
        'depth': 3,
    },
    {
        'path': 'countries/kenya/mombasa',
        'slug': 'mombasa',
        'city': 'Mombasa',
        'country': 'Kenya',
        'country_code': 'KE',
        'country_slug': 'kenya',
        'flag': '🇰🇪',
        'currency': 'KES',
        'symbol': 'KSh',
        'regulator': 'BCLB (Betting Control and Licensing Board)',
        'population': "Kenya's second largest city and major port with 1.2+ million people",
        'about': "Mombasa is Kenya's second largest city and the gateway to the Kenyan coast. Mombasa bettors use M-Pesa via *644# for instant deposits at BCLB-licensed bookmakers including Sportpesa, Betika, and 1xBet Kenya. The coastal city has a passionate football culture focused on the Kenya Premier League.",
        'payments': ['M-Pesa', 'Airtel Money', 'Equitel', 'USSD *644#'],
        'popular_leagues': ['Kenya Premier League', 'CAF Champions League', 'Premier League', 'AFCON'],
        'assets_prefix': '../../../',
        'country_prefix': '../../',
        'depth': 3,
    },
    {
        'path': 'countries/ghana/kumasi',
        'slug': 'kumasi',
        'city': 'Kumasi',
        'country': 'Ghana',
        'country_code': 'GH',
        'country_slug': 'ghana',
        'flag': '🇬🇭',
        'currency': 'GHS',
        'symbol': 'GH₵',
        'regulator': 'GCA (Gaming Commission of Ghana)',
        'population': "Ghana's second largest city and the heart of Ashanti Region with 3+ million people",
        'about': "Kumasi is Ghana's second largest city, home to Asante Kotoko FC — one of the most popular football clubs in Africa. Kumasi bettors are passionate football fans who use MTN MoMo and AirtelTigo Money at GCA-licensed bookmakers. The Kumasi betting market is among the most active in Ghana.",
        'payments': ['MTN MoMo', 'AirtelTigo Money', 'Vodafone Cash', 'Bank Transfer'],
        'popular_leagues': ['Ghana Premier League (Asante Kotoko)', 'CAF Champions League', 'Premier League', 'AFCON'],
        'assets_prefix': '../../../',
        'country_prefix': '../../',
        'depth': 3,
    },
]

if __name__ == '__main__':
    for city in CITIES:
        out_dir = os.path.join(BASE, city['path'])
        os.makedirs(out_dir, exist_ok=True)
        html = make_city_page(city)
        out_path = os.path.join(out_dir, 'index.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  ✓  /{city['path']}/")
    print(f'\n✅ Generated {len(CITIES)} additional city pages')
