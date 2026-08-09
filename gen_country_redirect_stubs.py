#!/usr/bin/env python3
"""Write minimal redirect-stub pages at the old countries/<slug>/index.html
locations, now that gen_best_betting_pages.py outputs to
/best-betting-in-<slug>/ instead (originally renamed 2026-08-09, briefly
pointed at /best-bonus-in-<slug>/ the same day, corrected back to the
distinct /best-betting-in-<slug>/ page the same day — see that generator's
docstring for the full story).

The physical countries/<slug>/ directory and its index.html are kept (not
deleted) because countries/<slug>/<city>/ sub-pages still live inside that
same directory and need a non-403 parent. The real redirect is the 301 in
.htaccess (server-side, fires before this file is ever served); this stub
is defense-in-depth only — noindex + canonical + meta-refresh — so no
duplicate "Best Betting Sites" content is indexable even if .htaccess is
ever bypassed.
"""

import os

from generate_country_pages import COUNTRIES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COUNTRIES_DIR = os.path.join(BASE_DIR, 'countries')
DOMAIN = 'https://sifufinds.com'


def make_stub(name, slug):
    new_url = f'{DOMAIN}/best-betting-in-{slug}/'
    return f"""<!DOCTYPE html>
<!-- sifufinds.com/countries/{slug}/ – moved to {new_url} on 2026-08-09 -->
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Moved: Best Betting Sites in {name} | SifuFinds</title>
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{new_url}">
<meta http-equiv="refresh" content="0; url={new_url}">
</head>
<body>
<p>This page has moved to <a href="{new_url}">{new_url}</a>.</p>
</body>
</html>
"""


if __name__ == '__main__':
    written = 0
    for code, country in COUNTRIES.items():
        slug = country['slug']
        name = country['name']
        out_dir = os.path.join(COUNTRIES_DIR, slug)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'index.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(make_stub(name, slug))
        print(f'  ✓  countries/{slug}/ -> best-betting-in-{slug}/ (stub)')
        written += 1

    print(f'\n✅ Wrote {written} redirect-stub pages')
