#!/usr/bin/env python3
"""
Generate World Cup 2026 team pages for sifufinds.com.
Creates /tips/world-cup-2026/{slug}/index.html for all 48 qualified nations.

Run:  python3 gen_wc2026_teams.py
"""
import os, json, re
from datetime import datetime
from seo_meta import seo_title, seo_meta_description

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OUT_DIR    = os.path.join(BASE_DIR, "tips", "world-cup-2026")
DOMAIN     = "https://sifufinds.com"
GA_ID      = "G-0B51MX2ZKE"

# ── 48 QUALIFIED TEAMS ────────────────────────────────────────────────────────
TEAMS = [
    # CONCACAF (6) — includes 3 hosts
    {"slug":"united-states","name":"United States","flag":"🇺🇸","conf":"CONCACAF","host":True,
     "ranking":11,"style":"Athletic, high-press","key_players":["Christian Pulisic","Tyler Adams","Ricardo Pepi"],
     "nickname":"USMNT","color":"#b22234"},
    {"slug":"canada","name":"Canada","flag":"🇨🇦","conf":"CONCACAF","host":True,
     "ranking":38,"style":"Fast transitions, set-pieces","key_players":["Alphonso Davies","Jonathan David","Cyle Larin"],
     "nickname":"The Canucks","color":"#ff0000"},
    {"slug":"mexico","name":"Mexico","flag":"🇲🇽","conf":"CONCACAF","host":True,
     "ranking":14,"style":"Possession-based, technical","key_players":["Santiago Giménez","Edson Álvarez","Hirving Lozano"],
     "nickname":"El Tri","color":"#006847"},
    {"slug":"panama","name":"Panama","flag":"🇵🇦","conf":"CONCACAF","host":False,
     "ranking":49,"style":"Defensive, counter-attack","key_players":["Rolando Blackburn","Adalberto Carrasquilla","César Yanis"],
     "nickname":"Los Canaleros","color":"#005293"},
    {"slug":"honduras","name":"Honduras","flag":"🇭🇳","conf":"CONCACAF","host":False,
     "ranking":74,"style":"Physical, direct play","key_players":["Alberth Elis","Romell Quioto","Luis Palma"],
     "nickname":"Los Catrachos","color":"#0056a2"},
    {"slug":"jamaica","name":"Jamaica","flag":"🇯🇲","conf":"CONCACAF","host":False,
     "ranking":55,"style":"Athletic, pressing football","key_players":["Michail Antonio","Bobby Decordova-Reid","Demarai Gray"],
     "nickname":"The Reggae Boyz","color":"#000000"},

    # CONMEBOL (6)
    {"slug":"argentina","name":"Argentina","flag":"🇦🇷","conf":"CONMEBOL","host":False,
     "ranking":1,"style":"Possession, Messi-led attack","key_players":["Lionel Messi","Lautaro Martínez","Rodrigo De Paul"],
     "nickname":"La Albiceleste","color":"#74acdf"},
    {"slug":"brazil","name":"Brazil","flag":"🇧🇷","conf":"CONMEBOL","host":False,
     "ranking":5,"style":"Attacking, flair football","key_players":["Vinícius Jr","Rodrygo","Casemiro"],
     "nickname":"Seleção","color":"#009c3b"},
    {"slug":"colombia","name":"Colombia","flag":"🇨🇴","conf":"CONMEBOL","host":False,
     "ranking":9,"style":"High-press, direct","key_players":["Luis Díaz","James Rodríguez","Falcao"],
     "nickname":"Los Cafeteros","color":"#fcd116"},
    {"slug":"uruguay","name":"Uruguay","flag":"🇺🇾","conf":"CONMEBOL","host":False,
     "ranking":17,"style":"Defensive solidity, clinical","key_players":["Darwin Núñez","Federico Valverde","Ronald Araújo"],
     "nickname":"La Celeste","color":"#5aaff3"},
    {"slug":"ecuador","name":"Ecuador","flag":"🇪🇨","conf":"CONMEBOL","host":False,
     "ranking":35,"style":"Counter-attack, disciplined","key_players":["Enner Valencia","Moisés Caicedo","Gonzalo Plata"],
     "nickname":"La Tri","color":"#ffd100"},
    {"slug":"venezuela","name":"Venezuela","flag":"🇻🇪","conf":"CONMEBOL","host":False,
     "ranking":46,"style":"High-energy, attacking","key_players":["Salomón Rondón","Darwin Machís","Jhon Murillo"],
     "nickname":"La Vinotinto","color":"#cf142b"},

    # UEFA (16)
    {"slug":"france","name":"France","flag":"🇫🇷","conf":"UEFA","host":False,
     "ranking":2,"style":"Balanced, world-class attack","key_players":["Kylian Mbappé","Antoine Griezmann","Aurélien Tchouaméni"],
     "nickname":"Les Bleus","color":"#002395"},
    {"slug":"england","name":"England","flag":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","conf":"UEFA","host":False,
     "ranking":4,"style":"Direct, physical, set-pieces","key_players":["Jude Bellingham","Harry Kane","Bukayo Saka"],
     "nickname":"The Three Lions","color":"#cf142b"},
    {"slug":"germany","name":"Germany","flag":"🇩🇪","conf":"UEFA","host":False,
     "ranking":12,"style":"Pressing, structured attack","key_players":["Florian Wirtz","Jamal Musiala","Kai Havertz"],
     "nickname":"Die Mannschaft","color":"#000000"},
    {"slug":"spain","name":"Spain","flag":"🇪🇸","conf":"UEFA","host":False,
     "ranking":7,"style":"Tiki-taka, possession","key_players":["Pedri","Lamine Yamal","Álvaro Morata"],
     "nickname":"La Roja","color":"#aa151b"},
    {"slug":"portugal","name":"Portugal","flag":"🇵🇹","conf":"UEFA","host":False,
     "ranking":6,"style":"Counter-attack, Ronaldo-led","key_players":["Cristiano Ronaldo","Bruno Fernandes","Bernardo Silva"],
     "nickname":"A Seleção das Quinas","color":"#006600"},
    {"slug":"netherlands","name":"Netherlands","flag":"🇳🇱","conf":"UEFA","host":False,
     "ranking":8,"style":"Total football, pressing","key_players":["Virgil van Dijk","Cody Gakpo","Xavi Simons"],
     "nickname":"Oranje","color":"#ff6600"},
    {"slug":"belgium","name":"Belgium","flag":"🇧🇪","conf":"UEFA","host":False,
     "ranking":3,"style":"Organised, clinical","key_players":["Kevin De Bruyne","Romelu Lukaku","Thibaut Courtois"],
     "nickname":"Red Devils","color":"#ef3340"},
    {"slug":"croatia","name":"Croatia","flag":"🇭🇷","conf":"UEFA","host":False,
     "ranking":10,"style":"Technical, midfield excellence","key_players":["Luka Modrić","Mateo Kovačić","Ivan Perišić"],
     "nickname":"The Blazers","color":"#ff0000"},
    {"slug":"switzerland","name":"Switzerland","flag":"🇨🇭","conf":"UEFA","host":False,
     "ranking":19,"style":"Organized, hard-working","key_players":["Granit Xhaka","Xherdan Shaqiri","Yann Sommer"],
     "nickname":"Die Nati","color":"#ff0000"},
    {"slug":"denmark","name":"Denmark","flag":"🇩🇰","conf":"UEFA","host":False,
     "ranking":21,"style":"Pressing, set-pieces","key_players":["Christian Eriksen","Kasper Dolberg","Pierre-Emile Højbjerg"],
     "nickname":"Danish Dynamite","color":"#c60c30"},
    {"slug":"austria","name":"Austria","flag":"🇦🇹","conf":"UEFA","host":False,
     "ranking":25,"style":"High-press, aggressive","key_players":["Marcel Sabitzer","David Alaba","Marko Arnautović"],
     "nickname":"Das Team","color":"#ed2939"},
    {"slug":"turkey","name":"Turkey","flag":"🇹🇷","conf":"UEFA","host":False,
     "ranking":30,"style":"Compact, counter-attack","key_players":["Hakan Çalhanoğlu","Arda Güler","Kerem Aktürkoğlu"],
     "nickname":"Crescent-Stars","color":"#e30a17"},
    {"slug":"serbia","name":"Serbia","flag":"🇷🇸","conf":"UEFA","host":False,
     "ranking":33,"style":"Physical, direct play","key_players":["Dušan Vlahović","Sergej Milinković-Savić","Aleksandar Mitrović"],
     "nickname":"The Eagles","color":"#c6363c"},
    {"slug":"scotland","name":"Scotland","flag":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","conf":"UEFA","host":False,
     "ranking":37,"style":"High-energy, physical","key_players":["Andrew Robertson","Scott McTominay","Che Adams"],
     "nickname":"The Tartan Army","color":"#003f87"},
    {"slug":"poland","name":"Poland","flag":"🇵🇱","conf":"UEFA","host":False,
     "ranking":28,"style":"Counter-attack, Lewandowski-led","key_players":["Robert Lewandowski","Piotr Zieliński","Wojciech Szczęsny"],
     "nickname":"The White Eagles","color":"#dc143c"},
    {"slug":"czech-republic","name":"Czech Republic","flag":"🇨🇿","conf":"UEFA","host":False,
     "ranking":36,"style":"Organised, counter-attack","key_players":["Tomáš Souček","Patrik Schick","Vladimír Coufal"],
     "nickname":"The Lions","color":"#d7141a"},

    # CAF (9 — Africa)
    {"slug":"morocco","name":"Morocco","flag":"🇲🇦","conf":"CAF","host":False,
     "ranking":13,"style":"Defensive solidity, fast breaks","key_players":["Achraf Hakimi","Hakim Ziyech","Youssef En-Nesyri"],
     "nickname":"The Atlas Lions","color":"#c1272d"},
    {"slug":"senegal","name":"Senegal","flag":"🇸🇳","conf":"CAF","host":False,
     "ranking":20,"style":"Athletic, physical dominance","key_players":["Sadio Mané","Édouard Mendy","Idrissa Gueye"],
     "nickname":"The Teranga Lions","color":"#00853f"},
    {"slug":"nigeria","name":"Nigeria","flag":"🇳🇬","conf":"CAF","host":False,
     "ranking":40,"style":"Direct attack, individual flair","key_players":["Victor Osimhen","Wilfred Ndidi","Alex Iwobi"],
     "nickname":"Super Eagles","color":"#008751"},
    {"slug":"egypt","name":"Egypt","flag":"🇪🇬","conf":"CAF","host":False,
     "ranking":34,"style":"Counter-attack, Mo Salah-led","key_players":["Mohamed Salah","Mohamed Elneny","Mostafa Mohamed"],
     "nickname":"The Pharaohs","color":"#ce1126"},
    {"slug":"south-africa","name":"South Africa","flag":"🇿🇦","conf":"CAF","host":False,
     "ranking":58,"style":"Organized, set-pieces","key_players":["Percy Tau","Bongani Zungu","Ronwen Williams"],
     "nickname":"Bafana Bafana","color":"#007a4d"},
    {"slug":"dr-congo","name":"DR Congo","flag":"🇨🇩","conf":"CAF","host":False,
     "ranking":62,"style":"Athletic, attacking","key_players":["Cédric Bakambu","Arthur Masuaku","Chancel Mbemba"],
     "nickname":"The Leopards","color":"#007fff"},
    {"slug":"mali","name":"Mali","flag":"🇲🇱","conf":"CAF","host":False,
     "ranking":50,"style":"Organized, disciplined","key_players":["Moussa Diaby","Yves Bissouma","Hamari Traoré"],
     "nickname":"The Eagles","color":"#009a00"},
    {"slug":"tunisia","name":"Tunisia","flag":"🇹🇳","conf":"CAF","host":False,
     "ranking":32,"style":"Technical, midfield-focused","key_players":["Wahbi Khazri","Hannibal Mejbri","Naim Sliti"],
     "nickname":"The Eagles of Carthage","color":"#e70013"},
    {"slug":"ivory-coast","name":"Côte d'Ivoire","flag":"🇨🇮","conf":"CAF","host":False,
     "ranking":43,"style":"Attacking, individual brilliance","key_players":["Sébastien Haller","Nicolas Pépé","Franck Kessié"],
     "nickname":"The Elephants","color":"#f77f00"},

    # AFC (8 — Asia)
    {"slug":"japan","name":"Japan","flag":"🇯🇵","conf":"AFC","host":False,
     "ranking":18,"style":"High-press, technical","key_players":["Takumi Minamino","Daichi Kamada","Ritsu Doan"],
     "nickname":"Samurai Blue","color":"#003087"},
    {"slug":"south-korea","name":"South Korea","flag":"🇰🇷","conf":"AFC","host":False,
     "ranking":23,"style":"Pressing, disciplined","key_players":["Son Heung-min","Kim Min-jae","Lee Jae-sung"],
     "nickname":"Taegeuk Warriors","color":"#cd2e3a"},
    {"slug":"iran","name":"Iran","flag":"🇮🇷","conf":"AFC","host":False,
     "ranking":22,"style":"Defensive, counter-attack","key_players":["Mehdi Taremi","Sardar Azmoun","Alireza Jahanbakhsh"],
     "nickname":"Team Melli","color":"#239f40"},
    {"slug":"australia","name":"Australia","flag":"🇦🇺","conf":"AFC","host":False,
     "ranking":24,"style":"Physical, set-pieces","key_players":["Mathew Ryan","Craig Goodwin","Jackson Irvine"],
     "nickname":"The Socceroos","color":"#ffcd00"},
    {"slug":"iraq","name":"Iraq","flag":"🇮🇶","conf":"AFC","host":False,
     "ranking":67,"style":"Compact, set-pieces","key_players":["Amjad Attwan","Ali Adnan","Mohanad Ali"],
     "nickname":"Lions of Mesopotamia","color":"#007a3d"},
    {"slug":"jordan","name":"Jordan","flag":"🇯🇴","conf":"AFC","host":False,
     "ranking":70,"style":"Physical, defensive solidity","key_players":["Musa Al-Taamari","Yazan Al-Naimat","Salem Al-Ajalin"],
     "nickname":"The Nashama","color":"#007a3d"},
    {"slug":"saudi-arabia","name":"Saudi Arabia","flag":"🇸🇦","conf":"AFC","host":False,
     "ranking":56,"style":"Counter-attack, disciplined","key_players":["Salem Al-Dawsari","Firas Al-Buraikan","Mohammed Al-Owais"],
     "nickname":"The Green Falcons","color":"#006c35"},
    {"slug":"uzbekistan","name":"Uzbekistan","flag":"🇺🇿","conf":"AFC","host":False,
     "ranking":60,"style":"Technical, improving","key_players":["Eldor Shomurodov","Otabek Shukurov","Abdullajon Abdullayev"],
     "nickname":"The White Wolves","color":"#1eb53a"},

    # OFC (1)
    {"slug":"new-zealand","name":"New Zealand","flag":"🇳🇿","conf":"OFC","host":False,
     "ranking":99,"style":"Physical, long ball","key_players":["Chris Wood","Clayton Lewis","Tim Payne"],
     "nickname":"All Whites","color":"#000000"},

    # Intercontinental playoff qualifiers (2)
    {"slug":"ghana","name":"Ghana","flag":"🇬🇭","conf":"CAF","host":False,
     "ranking":65,"style":"Technical, attack-minded","key_players":["Mohammed Kudus","Jordan Ayew","Thomas Partey"],
     "nickname":"Black Stars","color":"#006b3f"},
    {"slug":"chile","name":"Chile","flag":"🇨🇱","conf":"CONMEBOL","host":False,
     "ranking":42,"style":"High-press, organized","key_players":["Alexis Sánchez","Claudio Bravo","Arturo Vidal"],
     "nickname":"La Roja","color":"#d52b1e"},
]

# ── CONF LABELS ───────────────────────────────────────────────────────────────
CONF_LABEL = {
    "CONCACAF": "CONCACAF",
    "CONMEBOL": "CONMEBOL (South America)",
    "UEFA":     "UEFA (Europe)",
    "CAF":      "CAF (Africa)",
    "AFC":      "AFC (Asia)",
    "OFC":      "OFC (Oceania)",
}

NAV_HTML = """<nav class="site-nav" aria-label="Main navigation">
  <div class="nav-inner">
    <a href="/" class="nav-logo"><img src="/assets/icon.png" alt="SifuFinds" width="32" height="32"></a>
    <ul class="nav-links">
      <li><a href="/tips/world-cup-2026/">WC2026</a></li>
      <li><a href="/blog/">Blog</a></li>
      <li><a href="/odds/">Odds</a></li>
      <li><a href="/bookmakers/">Bookmakers</a></li>
    </ul>
  </div>
</nav>"""

def _slug_name(t: dict) -> str:
    return t["name"].replace("'", "").replace(" ", "-").lower()


def page_html(t: dict) -> str:
    name    = t["name"]
    flag    = t["flag"]
    slug    = t["slug"]
    conf    = t["conf"]
    rank    = t["ranking"]
    style   = t["style"]
    players = t["key_players"]
    nick    = t["nickname"]
    color   = t["color"]
    host    = " · Tournament Host" if t.get("host") else ""
    conf_label = CONF_LABEL.get(conf, conf)
    players_li = "\n".join(f"<li>{p}</li>" for p in players)
    canonical  = f"{DOMAIN}/tips/world-cup-2026/{slug}/"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}');</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{seo_title(f'{name} World Cup 2026 Odds, Predictions & Betting Tips')}</title>
<meta name="description" content="{seo_meta_description(f'{name} ({nick}) FIFA World Cup 2026 betting tips, odds, and predictions. Expert analysis for African bettors — compare Bet9ja, Sportybet, 1xBet odds. Updated daily.')}">
<meta name="keywords" content="{name} World Cup 2026, {name} WC2026 odds, {name} betting tips, {nick} World Cup 2026, FIFA World Cup 2026 {name}">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<meta name="author" content="SifuFinds World Cup Desk">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="{name} World Cup 2026 Odds & Betting Tips | SifuFinds">
<meta property="og:description" content="Expert {name} WC2026 betting tips and odds for African fans. Compare Bet9ja, Sportybet, 1xBet and more.">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{DOMAIN}/assets/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@sifufinds">
<script type="application/ld+json">{{
  "@context":"https://schema.org",
  "@type":"Article",
  "headline":"{name} World Cup 2026 Odds, Predictions & Betting Tips",
  "description":"Expert {name} WC2026 betting tips and odds for African bettors.",
  "author":{{"@type":"Organization","name":"SifuFinds"}},
  "publisher":{{"@type":"Organization","name":"SifuFinds","url":"{DOMAIN}"}},
  "url":"{canonical}",
  "dateModified":"{datetime.utcnow().strftime('%Y-%m-%d')}"
}}</script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f1117;color:#e8eaf0;line-height:1.6}}
.site-nav{{background:#161b27;border-bottom:1px solid #2a2d3a;padding:0 1rem}}
.nav-inner{{max-width:1200px;margin:0 auto;display:flex;align-items:center;gap:2rem;height:56px}}
.nav-logo img{{display:block}}
.nav-links{{list-style:none;display:flex;gap:1.5rem}}
.nav-links a{{color:#a0a8c0;text-decoration:none;font-size:.9rem;font-weight:500}}
.nav-links a:hover{{color:#fff}}
.hero{{background:linear-gradient(135deg,{color}22 0%,#161b27 60%);border-bottom:1px solid #2a2d3a;padding:3rem 1rem}}
.hero-inner{{max-width:800px;margin:0 auto}}
.flag-title{{display:flex;align-items:center;gap:1rem;margin-bottom:.75rem}}
.flag-title .flag{{font-size:3rem}}
.flag-title h1{{font-size:clamp(1.6rem,4vw,2.4rem);font-weight:800;color:#fff}}
.badge{{display:inline-block;background:{color};color:#fff;font-size:.75rem;font-weight:700;padding:.25rem .75rem;border-radius:20px;text-transform:uppercase;letter-spacing:.05em}}
.meta-row{{display:flex;flex-wrap:wrap;gap:.75rem;margin-top:1rem;font-size:.85rem;color:#a0a8c0}}
.meta-row span{{background:#1e2336;padding:.25rem .6rem;border-radius:6px}}
.main{{max-width:800px;margin:0 auto;padding:2rem 1rem}}
.card{{background:#161b27;border:1px solid #2a2d3a;border-radius:12px;padding:1.5rem;margin-bottom:1.5rem}}
.card h2{{font-size:1.1rem;font-weight:700;color:#e8eaf0;margin-bottom:1rem;display:flex;align-items:center;gap:.5rem}}
.players-list{{list-style:none;display:flex;flex-direction:column;gap:.5rem}}
.players-list li{{padding:.5rem .75rem;background:#1e2336;border-radius:8px;font-size:.9rem}}
table{{width:100%;border-collapse:collapse;font-size:.85rem}}
th{{background:#1e2336;color:#a0a8c0;font-weight:600;padding:.6rem .75rem;text-align:left}}
td{{padding:.6rem .75rem;border-bottom:1px solid #2a2d3a}}
tr:last-child td{{border-bottom:none}}
.odds-val{{font-weight:700;color:#f0c040}}
.cta-box{{background:linear-gradient(135deg,{color}33,#1e2336);border:1px solid {color}66;border-radius:12px;padding:1.5rem;text-align:center;margin-top:1.5rem}}
.cta-box h3{{color:#fff;margin-bottom:.5rem}}
.cta-box p{{color:#a0a8c0;font-size:.9rem;margin-bottom:1rem}}
.cta-btn{{display:inline-block;background:{color};color:#fff;font-weight:700;padding:.75rem 2rem;border-radius:8px;text-decoration:none;font-size:1rem}}
.cta-btn:hover{{opacity:.9}}
.rg-note{{font-size:.75rem;color:#6b7280;text-align:center;margin-top:1.5rem}}
footer{{background:#161b27;border-top:1px solid #2a2d3a;padding:2rem 1rem;text-align:center;font-size:.8rem;color:#6b7280}}
footer a{{color:#a0a8c0;text-decoration:none}}
@media(max-width:600px){{.nav-links{{display:none}}.flag-title h1{{font-size:1.4rem}}}}
</style>
</head>
<body>
{NAV_HTML}

<section class="hero">
  <div class="hero-inner">
    <div class="flag-title">
      <span class="flag" aria-hidden="true">{flag}</span>
      <h1>{name}</h1>
    </div>
    <span class="badge">{conf_label}{host}</span>
    <div class="meta-row">
      <span>🏆 FIFA World Cup 2026</span>
      <span>📊 FIFA Rank #{rank}</span>
      <span>⚽ {style}</span>
    </div>
  </div>
</section>

<main class="main">

  <div class="card">
    <h2>⭐ Key Players to Watch</h2>
    <ul class="players-list">{players_li}</ul>
  </div>

  <div class="card">
    <h2>💰 World Cup 2026 Outright Odds</h2>
    <p style="color:#a0a8c0;font-size:.85rem;margin-bottom:1rem">Indicative odds — always check your bookmaker for live prices.</p>
    <table>
      <thead><tr><th>Market</th><th>Bet9ja</th><th>Sportybet</th><th>1xBet</th></tr></thead>
      <tbody>
        <tr><td>Tournament Winner</td><td class="odds-val">TBC</td><td class="odds-val">TBC</td><td class="odds-val">TBC</td></tr>
        <tr><td>Top Scorer</td><td class="odds-val">TBC</td><td class="odds-val">TBC</td><td class="odds-val">TBC</td></tr>
        <tr><td>Reach Semi-Finals</td><td class="odds-val">TBC</td><td class="odds-val">TBC</td><td class="odds-val">TBC</td></tr>
        <tr><td>Reach Quarter-Finals</td><td class="odds-val">TBC</td><td class="odds-val">TBC</td><td class="odds-val">TBC</td></tr>
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>📰 Daily Match Updates</h2>
    <p style="color:#a0a8c0;font-size:.9rem">Our <a href="/blog/" style="color:#f0c040">World Cup 2026 blog</a> publishes daily match previews, results analysis, and betting tips for every {name} game. Check back after every result for the latest odds movements and expert tips.</p>
  </div>

  <div class="cta-box">
    <h3>Get the Best {name} Odds</h3>
    <p>Compare live World Cup 2026 odds from Africa's top bookmakers — Bet9ja, Sportybet, 1xBet, Betway and more.</p>
    <a href="{DOMAIN}" class="cta-btn">Compare Odds Now →</a>
  </div>

  <p class="rg-note">18+ | Bet Responsibly | T&amp;Cs Apply | Gambling can be addictive — please play responsibly.</p>

</main>

<footer>
  <p><a href="{DOMAIN}">SifuFinds</a> · Africa's #1 Betting Comparison Site · <a href="{DOMAIN}/tips/world-cup-2026/">World Cup 2026 Hub</a></p>
  <p style="margin-top:.5rem">Odds shown are indicative and subject to change. Always verify with your bookmaker before placing bets.</p>
</footer>
</body>
</html>"""


def main() -> None:
    created = 0
    for team in TEAMS:
        slug   = team["slug"]
        folder = os.path.join(OUT_DIR, slug)
        os.makedirs(folder, exist_ok=True)
        path   = os.path.join(folder, "index.html")
        html   = page_html(team)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        created += 1
        print(f"  ✓ {team['flag']} {team['name']} → tips/world-cup-2026/{slug}/")

    # Also write a JSON manifest for the hub page to consume
    manifest_path = os.path.join(OUT_DIR, "teams.json")
    manifest = [
        {"slug": t["slug"], "name": t["name"], "flag": t["flag"],
         "conf": t["conf"], "ranking": t["ranking"], "host": t.get("host", False)}
        for t in TEAMS
    ]
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Generated {created} team pages + teams.json manifest")
    print(f"   Hub: {OUT_DIR}/")


if __name__ == "__main__":
    main()
