#!/usr/bin/env python3
"""Generate Egypt and Morocco country pages."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_country_pages import generate_page, COUNTRIES_DIR

EG_MA = {
    'EG': {
        'slug': 'egypt', 'name': 'Egypt', 'flag': '🇪🇬',
        'currency': 'EGP', 'symbol': 'EGP',
        'regulator': 'Egyptian Gambling Regulatory Authority (EGRA)',
        'about': "Egypt is one of Africa's largest sports betting markets with a passionate football culture. The Egyptian Premier League is among Africa's strongest domestic competitions. International bookmakers serve Egyptian bettors and the market is growing with mobile penetration. Vodafone Cash Egypt and bank transfer are the main payment routes.",
        'payments': ['Vodafone Cash Egypt', 'Orange Money Egypt', 'Bank Transfer', 'Visa', 'Mastercard'],
        'leagues': ['Egyptian Premier League', 'CAF Champions League', 'Premier League', 'La Liga', 'World Cup 2026'],
        'top_bonus': 'EGP 30,000', 'top_bookmaker': 'Melbet Egypt', 'min_deposit': 'EGP 10', 'books_count': 5,
    },
    'MA': {
        'slug': 'morocco', 'name': 'Morocco', 'flag': '🇲🇦',
        'currency': 'MAD', 'symbol': 'MAD',
        'regulator': 'MDJS (Marocaine des Jeux et des Sports)',
        'about': "Morocco has a regulated gambling market overseen by MDJS. PMU Maroc (Pari Mutuel Urbain) is the state-licensed operator. Morocco's 2022 World Cup semi-final run ignited massive betting interest — they are favourites as Africa's best side at World Cup 2026. The Botola Pro is the top domestic league, while La Liga, Champions League and Serie A are hugely popular.",
        'payments': ['Bank Transfer', 'CIH Bank', 'Attijari Bank', 'Orange Money Morocco', 'Visa', 'Mastercard'],
        'leagues': ['Botola Pro', 'CAF Champions League', 'Premier League', 'La Liga', 'World Cup 2026'],
        'top_bonus': 'MAD 5,000', 'top_bookmaker': 'Melbet Maroc', 'min_deposit': 'MAD 10', 'books_count': 4,
    },
}

for code, country in EG_MA.items():
    slug = country['slug']
    out_dir = os.path.join(COUNTRIES_DIR, slug)
    os.makedirs(out_dir, exist_ok=True)
    html = generate_page(code, country)
    out_path = os.path.join(out_dir, 'index.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'  ✓  /countries/{slug}/')

print('\n✅ Egypt and Morocco pages generated')
