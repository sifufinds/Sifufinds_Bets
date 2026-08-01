"""Canonical list of SifuFinds' 23 supported African countries.

Mirrors the `MAP`/`CTY_NAMES` objects in index.html's geo-redirect script
and COUNTRY_LINKS in gen_blog_post_pages.py. Keyword/content research agents
should import this instead of config.COUNTRIES — that list only carries
currency/bookmaker/payment detail for 6 markets and silently under-covers
the other 17 countries the site actually serves (see CLAUDE.md's Geo
Homepage Routing standing rule for why the country set must stay in sync).
"""

AFRICAN_COUNTRIES: list[dict[str, str]] = [
    {"code": "NG", "name": "Nigeria", "slug": "nigeria"},
    {"code": "KE", "name": "Kenya", "slug": "kenya"},
    {"code": "GH", "name": "Ghana", "slug": "ghana"},
    {"code": "ZA", "name": "South Africa", "slug": "south-africa"},
    {"code": "TZ", "name": "Tanzania", "slug": "tanzania"},
    {"code": "UG", "name": "Uganda", "slug": "uganda"},
    {"code": "ZM", "name": "Zambia", "slug": "zambia"},
    {"code": "ET", "name": "Ethiopia", "slug": "ethiopia"},
    {"code": "CI", "name": "Ivory Coast", "slug": "ivory-coast"},
    {"code": "CM", "name": "Cameroon", "slug": "cameroon"},
    {"code": "SN", "name": "Senegal", "slug": "senegal"},
    {"code": "RW", "name": "Rwanda", "slug": "rwanda"},
    {"code": "ZW", "name": "Zimbabwe", "slug": "zimbabwe"},
    {"code": "MW", "name": "Malawi", "slug": "malawi"},
    {"code": "MZ", "name": "Mozambique", "slug": "mozambique"},
    {"code": "AO", "name": "Angola", "slug": "angola"},
    {"code": "CD", "name": "DR Congo", "slug": "dr-congo"},
    {"code": "BW", "name": "Botswana", "slug": "botswana"},
    {"code": "NA", "name": "Namibia", "slug": "namibia"},
    {"code": "EG", "name": "Egypt", "slug": "egypt"},
    {"code": "MA", "name": "Morocco", "slug": "morocco"},
    {"code": "SL", "name": "Sierra Leone", "slug": "sierra-leone"},
    {"code": "LR", "name": "Liberia", "slug": "liberia"},
]
