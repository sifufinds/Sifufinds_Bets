"""Canonical list of SifuFinds' 28 promotable African countries.

Mirrors the `MAP`/`CTY_NAMES` objects in index.html's geo-redirect script
and COUNTRY_LINKS in gen_blog_post_pages.py. Keyword/content research agents
should import this instead of config.COUNTRIES — that list only carries
currency/bookmaker/payment detail for 6 markets and silently under-covers
the rest of the countries the site actually serves (see CLAUDE.md's Geo
Homepage Routing standing rule for why the country set must stay in sync).

2026-08-14: extended from 23 to 28 with the 5 new "emerging" markets
(Benin, Burkina Faso, Gambia, Togo, Congo-Brazzaville) added the same day.
Deliberately does NOT include the 5 "restricted" markets added at the same
time (Algeria, Libya, Mauritania, Somalia, Tunisia) — online betting is
banned or heavily restricted in all five, SifuFinds lists no bookmaker and
runs no affiliate link there, and this list feeds keyword/content agents
whose entire purpose is driving promotional betting content. Adding those
five here would risk an agent later writing exactly the kind of promotional
content the site deliberately does not publish for those markets. SifuFinds
covers 33 countries in total (see /countries/); this list is 28, not 33, by
design — the site's own README count and this agent-targeting list are not
the same number and should not be conflated.
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
    {"code": "BJ", "name": "Benin", "slug": "benin"},
    {"code": "BF", "name": "Burkina Faso", "slug": "burkina-faso"},
    {"code": "GM", "name": "Gambia", "slug": "gambia"},
    {"code": "TG", "name": "Togo", "slug": "togo"},
    {"code": "CG", "name": "Congo-Brazzaville", "slug": "congo-brazzaville"},
]
