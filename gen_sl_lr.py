#!/usr/bin/env python3
"""Generate Sierra Leone and Liberia country pages."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_country_pages import generate_page, COUNTRIES_DIR

SL_LR = {
    'SL': {
        'slug': 'sierra-leone', 'name': 'Sierra Leone', 'flag': '🇸🇱',
        'currency': 'SLL', 'symbol': 'Le',
        'regulator': 'National Lotteries Authority (NLA)',
        'about': "Sierra Leone has a growing sports betting market regulated by the National Lotteries Authority. Orange Money Sierra Leone and Africell Money are the main mobile payment channels. The Sierra Leone Premier League and AFCON attract the most betting interest, with international competitions like the Premier League also popular.",
        'payments': ['Orange Money Sierra Leone', 'Africell Money', 'Bank Transfer', 'Visa'],
        'leagues': ['Sierra Leone Premier League', 'CAF Confederation Cup', 'Premier League', 'AFCON'],
        'top_bonus': 'Le 2,000,000', 'top_bookmaker': '1xBet Sierra Leone', 'min_deposit': 'Le 1,000', 'books_count': 3,
    },
    'LR': {
        'slug': 'liberia', 'name': 'Liberia', 'flag': '🇱🇷',
        'currency': 'LRD', 'symbol': '$',
        'regulator': 'National Lottery of Liberia',
        'about': "Liberia has an emerging sports betting market. The National Lottery of Liberia oversees gambling activities. Lonestar Cell MTN Mobile Money and Orange Liberia are the main mobile payment options. Football is the dominant sport with the LFA League and international competitions attracting strong interest.",
        'payments': ['Lonestar MTN Mobile Money', 'Orange Liberia', 'Bank Transfer', 'Visa'],
        'leagues': ['LFA League', 'CAF Confederation Cup', 'Premier League', 'AFCON'],
        'top_bonus': '$200', 'top_bookmaker': '1xBet Liberia', 'min_deposit': '$2', 'books_count': 3,
    },
}

for code, country in SL_LR.items():
    slug = country['slug']
    out_dir = os.path.join(COUNTRIES_DIR, slug)
    os.makedirs(out_dir, exist_ok=True)
    html = generate_page(code, country)
    out_path = os.path.join(out_dir, 'index.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'  ✓  /countries/{slug}/')

print('\n✅ Sierra Leone and Liberia pages generated')
