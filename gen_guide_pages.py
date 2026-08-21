#!/usr/bin/env python3
"""Generate new betting guide pages."""

import json
import os
from seo_meta import seo_title, seo_meta_description
from site_stats import total_country_count

TOTAL_COUNTRIES = total_country_count()

BASE = os.path.dirname(os.path.abspath(__file__))

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

GUIDES = [
    {
        'slug': 'live-betting',
        'title': 'Live Betting Guide for African Bettors 2026 | In-Play Betting Explained | SifuFinds',
        'desc': 'Complete guide to live (in-play) betting in Africa 2026. Learn how to bet on football while the match is in progress. Best live betting bookmakers in Nigeria, Kenya, South Africa and Ghana.',
        'keywords': 'live betting Africa, in-play betting Nigeria, live sports betting Kenya, in-play betting guide Africa 2026, live bet South Africa, in-play bookmakers Africa, how to live bet football Africa',
        'og_title': 'Live Betting Guide Africa 2026 | SifuFinds',
        'h1': 'Live Betting (In-Play) Guide for African Bettors &middot; 2026',
        'icon': '⚡',
        'intro': "Live betting — also called <strong>in-play betting</strong> — lets you place bets on a match <em>while it is being played</em>. Odds change in real time as the game progresses. You can bet on the next goal scorer, the next team to score, total goals, and hundreds of other markets — all after kick-off. Live betting is now available at all major licensed bookmakers across Nigeria, Kenya, South Africa, and Ghana.",
        'sections': [
            ('How Does Live Betting Work?', "When a match starts, the bookmaker opens live markets with continuously updating odds. If Arsenal are losing 0-1 at half-time, their odds to win the match rise — giving you a higher-value entry point than if you had bet before kick-off. You can see live statistics, match timelines, and sometimes live streams alongside the markets. Bets settle as events occur (e.g., next goal market settles the moment a goal is scored)."),
            ('Best Live Betting Markets for African Football', """<ul>
<li><strong>Next Goal Scorer</strong> — Predict which player scores next. High odds, high risk.</li>
<li><strong>Next Team to Score</strong> — Simpler version — just pick the team. Easier to win.</li>
<li><strong>Total Goals Over/Under</strong> — Bet whether the total goals in the match exceeds or falls below a target (e.g., Over 2.5 total goals).</li>
<li><strong>Draw No Bet</strong> — Your stake is returned if the match ends level. Reduces risk.</li>
<li><strong>Half-Time / Full-Time</strong> — Predict both the half-time and full-time result. Higher odds.</li>
<li><strong>Correct Score</strong> — Exact score prediction. Very high odds but difficult.</li>
<li><strong>Match Result 1X2</strong> — Classic Home/Draw/Away during the match.</li>
</ul>"""),
            ('Live Betting Tips for African Bettors', """<ol>
<li><strong>Watch the match</strong> — The best live bettors watch or follow live stats closely. Use a bookmaker with live streaming (Betway, 1xBet).</li>
<li><strong>Bet on momentum shifts</strong> — If a strong team goes 0-1 down early against a weaker opponent, their odds to win increase significantly. Look for value immediately after the goal.</li>
<li><strong>Use Cash Out</strong> — Live betting works best with a Cash Out feature. Lock in profit when your bet is winning, before the match ends.</li>
<li><strong>Bet on African leagues you know</strong> — Your knowledge of the NPFL (Nigeria), Kenya Premier League, or PSL (South Africa) gives you an edge on live markets that offshore traders may price less accurately.</li>
<li><strong>Avoid tilt-chasing</strong> — Don't place rushed live bets to recover losses from pre-match bets. Each bet should stand on its own logic.</li>
</ol>"""),
        ],
        'faq': [
            ('Which African bookmakers have the best live betting?', "The best live betting bookmakers in Africa are Betway (live streaming + 1,000+ daily live markets), 1xBet (most live markets), Sportybet (fastest odds updates on African leagues), and Hollywoodbets (South Africa — best local league live coverage). All offer Cash Out on live bets. All are fully licensed in their respective African markets."),
            ('Can I live bet on AFCON and CAF Champions League?', "Yes. All major licensed African bookmakers cover AFCON and CAF Champions League with live markets including 1X2, Over/Under, Next Goal Scorer, and Correct Score. Live streaming is available for select CAF matches at Betway Africa and 1xBet. Most bookmakers also cover the Nigeria Premier League (NPFL), Kenya Premier League, and South African PSL live."),
            ('What is Cash Out in live betting?', "Cash Out lets you settle your bet before the match ends — at a value reflecting the current match situation. If your team is winning, you can Cash Out for a guaranteed (smaller) profit without waiting for the final whistle. If your bet is going badly, you can Cash Out for a partial refund. Available at Betway, 1xBet, Bet9ja, and most other major African bookmakers."),
            ('Is live betting different from virtual sports betting?', "Yes. Live betting is on real matches happening in real time. Virtual sports are computer-generated simulations that run every few minutes and are independent of actual sports. Live betting requires the match to be in progress. Both are available at major African bookmakers but are entirely separate products."),
        ],
        'canonical_path': 'guides/live-betting',
        'breadcrumb_name': 'Live Betting Guide',
        'schema_name': 'Live Betting Guide for African Bettors 2026',
        'schema_desc': 'Complete guide to live (in-play) sports betting in Africa. How in-play markets work, best tips, and top licensed bookmakers for live betting in Nigeria, Kenya, South Africa and Ghana.',
    },
    {
        'slug': 'over-under-betting',
        'title': 'Over/Under Betting Guide for Africa 2026 | Goals Over Under Explained | SifuFinds',
        'desc': 'Complete guide to Over/Under (goals) betting in Africa 2026. What does Over 2.5 goals mean? Best tips and strategies for African football bettors in Nigeria, Kenya, South Africa and Ghana.',
        'keywords': 'over under betting Africa, over 2.5 goals Nigeria, under 2.5 goals Kenya, over under football betting guide Africa, what does over 2.5 mean, goals betting Africa 2026, over under tips Africa',
        'og_title': 'Over/Under Betting Guide Africa 2026 | SifuFinds',
        'h1': 'Over/Under Goals Betting Guide for Africa &middot; 2026',
        'icon': '⚽',
        'intro': "<strong>Over/Under betting</strong> — also called totals betting — is one of the simplest and most popular bet types at African bookmakers. Instead of picking a winner, you predict whether the total goals scored in a match will be <em>more</em> or <em>fewer</em> than a set number (usually 2.5 goals). Over/Under markets are available on the NPFL, Kenya Premier League, AFCON, CAF Champions League, and all major European leagues.",
        'sections': [
            ('What Does Over 2.5 Goals Mean?', """The most common Over/Under line is <strong>2.5 goals</strong>. Because you cannot score half a goal, the .5 eliminates the possibility of a tie result:
<ul>
<li><strong>Over 2.5 goals</strong> wins if there are 3 or more total goals scored in the match (by both teams combined).</li>
<li><strong>Under 2.5 goals</strong> wins if there are 0, 1, or 2 total goals scored.</li>
</ul>
Other common lines you'll see at African bookmakers:
<ul>
<li>Over/Under 1.5 goals (wins with 2+ goals, very likely in most matches)</li>
<li>Over/Under 3.5 goals (higher risk, needs 4+ goals)</li>
<li>Over/Under 4.5 goals (very high risk, but very high odds)</li>
</ul>"""),
            ('Over/Under Tips for African Football', """<ol>
<li><strong>Know the league averages</strong> — African leagues often have fewer goals than European leagues. The NPFL averages around 2.0 goals per match, the Kenya Premier League around 2.2. Blind Over 2.5 bets on African derbies often fail — look for weaker sides facing strong attacks.</li>
<li><strong>Check team form</strong> — Look at the last 5 matches for each team. How many went Over 2.5? A team like Manchester City consistently scores 3+ goals — Over 2.5 at home is a strong value bet.</li>
<li><strong>Weather and pitch conditions</strong> — African rainy season affects pitch quality, which can slow attacking play. Muddy pitches tend to produce fewer goals.</li>
<li><strong>AFCON group stages</strong> — The AFCON group stages often produce cagey, defensive 1-0 or 0-0 results. Under 2.5 is often value in AFCON group matches, especially between defensively organized teams.</li>
<li><strong>Use both teams to score (BTTS)</strong> alongside Over 2.5</strong> — If both teams have scored in their last 5 games, BTTS + Over 2.5 is a strong combined market with good odds.</li>
</ol>"""),
            ('Over/Under on AFCON and CAF Champions League', "AFCON and CAF Champions League are major Over/Under markets at all African bookmakers. AFCON knockout rounds tend to produce fewer goals (average ~2.1 goals in knockout rounds, ~2.4 in the group stage). CAF Champions League group stages are often high-scoring when strong clubs (TP Mazembe, Al-Ahly, ES Tunis) face smaller opposition."),
        ],
        'faq': [
            ('What does Over 2.5 goals mean in betting?', "Over 2.5 goals means you are predicting that the total goals scored in the match (both teams combined) will be 3 or more. If the match ends 2-1 (3 total goals), the Over 2.5 bet wins. If it ends 1-1 (2 goals), the bet loses. The .5 means a push (tie result) is impossible."),
            ('Is Over/Under better than 1X2 betting?', "Neither is objectively better — they suit different situations. Over/Under is popular because you don't need to predict which team wins; you just need the total goals to be above or below the line. Many African bettors prefer Over/Under on high-profile matches (AFCON, Premier League) because it feels more predictable than picking the outright winner."),
            ('What is Asian Handicap Over/Under?', "Asian Handicap Over/Under uses quarter-goal lines like 2.25 or 2.75 to eliminate most push scenarios. For example, Over 2.75 means: if 3 goals are scored, half your stake wins at full odds and half at even (you get a partial win). If 4+ goals are scored, the full bet wins. Asian Over/Under is available at 1xBet and Betway in Africa."),
            ('Which leagues have the most Over 2.5 goals in Africa?', "In Africa: the NPFL (Nigeria) averages ~2.0 goals/game, CAF Champions League ~2.3. Outside Africa: the Premier League averages ~2.75, the Bundesliga ~3.1, and La Liga ~2.55. For regular Over 2.5 bets, European leagues offer more consistent value. For Under 2.5 bets, African derbies and AFCON knockout rounds are often strong selections."),
        ],
        'canonical_path': 'guides/over-under-betting',
        'breadcrumb_name': 'Over/Under Betting Guide',
        'schema_name': 'Over/Under Betting Guide Africa 2026',
        'schema_desc': 'Complete guide to Over/Under (goals) betting for African bettors. How Over 2.5 works, strategies for AFCON and CAF matches, and tips for Nigerian, Kenyan, and South African football.',
    },
    {
        'slug': 'responsible-gambling',
        'title': 'Responsible Gambling in Africa 2026 | Safe Betting Guide | SifuFinds',
        'desc': 'Responsible gambling guide for African bettors 2026. Learn how to set limits, recognise problem gambling, and access help in Nigeria, Kenya, South Africa, Ghana and more. 18+ only.',
        'keywords': 'responsible gambling Africa, safe betting Nigeria, problem gambling Kenya, gambling addiction Africa, set betting limits Africa, self-exclusion bookmakers Africa, gambling help Africa 2026',
        'og_title': 'Responsible Gambling Guide Africa 2026 | SifuFinds',
        'h1': 'Responsible Gambling — Safe Betting Guide for Africa &middot; 2026',
        'icon': '🛡',
        'intro': f"Betting should be fun — but it carries real financial risks. SifuFinds is committed to promoting responsible gambling across all {TOTAL_COUNTRIES} African countries we cover. This guide explains how to gamble safely, recognise the early signs of problem gambling, and access support in Nigeria, Kenya, South Africa, Ghana, and beyond. <strong>All licensed bookmakers on SifuFinds offer free responsible gambling tools.</strong>",
        'sections': [
            ('Golden Rules for Safe Betting', """<ol>
<li><strong>Only bet what you can afford to lose.</strong> Your betting bankroll should come from entertainment money — never from rent, food, or essential expenses.</li>
<li><strong>Set a budget before you start.</strong> Decide the maximum you will bet per week before placing any bets. Most licensed bookmakers (Betway, 1xBet, Bet9ja) allow you to set deposit limits in your account settings.</li>
<li><strong>Never chase losses.</strong> Placing extra bets to recover money you've lost is the most common path to serious problem gambling. Each bet should stand on its own merits.</li>
<li><strong>Keep track of your bets.</strong> Use the bet history section of your bookmaker app to review what you've won and lost this month. Knowledge is control.</li>
<li><strong>Take breaks.</strong> Even when you are winning, take a complete break from betting regularly. Most bookmakers offer a Cool-Off period (24 hours, 1 week, or 1 month) you can activate instantly.</li>
<li><strong>Never bet under the influence.</strong> Alcohol and stress impair decision-making. Only bet with a clear head.</li>
<li><strong>Keep betting separate from your emotions.</strong> Don't bet on your favourite team to relieve pre-match anxiety. Your emotional connection clouds objective analysis.</li>
</ol>"""),
            ('Warning Signs of Problem Gambling', """Seek help if you recognise these signs in yourself or someone you know:
<ul>
<li>Betting more than you planned, or more than you can afford</li>
<li>Borrowing money to gamble</li>
<li>Hiding your betting activity from family or friends</li>
<li>Feeling anxious, irritable, or depressed when not gambling</li>
<li>Skipping work, school, or family obligations to bet</li>
<li>Believing you have a "system" to beat the bookmaker consistently</li>
<li>Chasing losses — placing bigger bets to win back what you've lost</li>
</ul>
If you recognise 2 or more of these signs, it is time to seek support."""),
            ('Responsible Gambling Tools at African Bookmakers', """All licensed bookmakers covered by SifuFinds offer free tools:
<ul>
<li><strong>Deposit Limits</strong> — Cap your daily, weekly, or monthly deposits. Changes to increase limits take 24 hours to activate; reductions are instant.</li>
<li><strong>Reality Check</strong> — Set a timer to receive pop-up reminders of how long you have been logged in and how much you have spent.</li>
<li><strong>Cool-Off Period</strong> — Take a temporary break for 24 hours, 1 week, or 1 month. You can still log in to view history but cannot bet.</li>
<li><strong>Self-Exclusion</strong> — A permanent or long-term exclusion from all gambling at the bookmaker. Takes effect immediately. Available at all NLRC, BCLB, and WCGRB licensed operators.</li>
<li><strong>Account Closure</strong> — Request the permanent closure of your account at any time. Contact customer support on the bookmaker's official website.</li>
</ul>"""),
            ('Help Organisations in Africa', """<ul>
<li><strong>Nigeria:</strong> Contact the NLRC (National Lottery Regulatory Commission) at nlrc.gov.ng. National helpline: call NLRC directly or reach the Problem Gambling Helpline via Bet9ja's responsible gambling page.</li>
<li><strong>Kenya:</strong> BCLB (Betting Control and Licensing Board) — bclb.go.ke. Kenya has a National Problem Gambling Helpline available 24/7.</li>
<li><strong>South Africa:</strong> Responsible Gambling Foundation — rgf.org.za. National Responsible Gambling Helpline: 0800 006 008 (free, 24/7).</li>
<li><strong>Ghana:</strong> Gaming Commission of Ghana — gcg.gov.gh.</li>
<li><strong>All countries:</strong> Gamblers Anonymous has chapters in multiple African countries — visit gamblers-anonymous.org.uk for a directory.</li>
</ul>"""),
        ],
        'faq': [
            ('How do I set betting limits at African bookmakers?', "Log in to your bookmaker account and go to Account Settings > Responsible Gambling or Safety Tools. Most licensed bookmakers (Betway, 1xBet, Bet9ja, Sportpesa) offer deposit limits, session time limits, and cool-off periods. Limit reductions take effect immediately. Limit increases may have a 24-hour cooling-off period before activation."),
            ('How do I self-exclude from an African bookmaker?', "Contact the bookmaker's customer support via live chat, email, or phone and request self-exclusion. Most NLRC-licensed Nigerian bookmakers and BCLB-licensed Kenyan bookmakers can process this within 24 hours. In South Africa, you can self-exclude through the National Responsible Gambling Programme (NRGP) which coordinates with all WCGRB-licensed operators."),
            ('What is the legal gambling age in Africa?', "The minimum legal gambling age varies by country. In Nigeria: 18+. Kenya: 18+. South Africa: 18+. Ghana: 18+. Tanzania: 18+. Zimbabwe: 18+. Morocco: 18+. Egypt: 21+. All licensed bookmakers on SifuFinds strictly enforce age verification — you will be asked to provide a government-issued ID before your first withdrawal."),
            ('Is it possible to win money consistently from sports betting?', "Long-term profitable betting requires substantial expertise, discipline, and time investment. The bookmaker's built-in margin (overround) means that without exceptional skill, most bettors lose money over time. Sports betting should be treated as paid entertainment, not as a source of income. SifuFinds always recommends setting a monthly entertainment budget for betting and never exceeding it."),
        ],
        'canonical_path': 'guides/responsible-gambling',
        'breadcrumb_name': 'Responsible Gambling',
        'schema_name': 'Responsible Gambling Guide Africa 2026',
        'schema_desc': 'Complete responsible gambling guide for African bettors. Safe betting rules, problem gambling warning signs, self-exclusion tools, and help organisations across Nigeria, Kenya, South Africa and more.',
    },
    {
        'slug': 'accumulator-tips',
        'title': 'Accumulator Betting Tips for Africa 2026 | Acca Guide & Strategies | SifuFinds',
        'desc': 'Best accumulator (acca) betting tips for African bettors 2026. How to build winning multi-bets on AFCON, Premier League, and African football. Strategies, mistakes to avoid, and top bookmakers.',
        'keywords': 'accumulator betting tips Africa, acca tips Nigeria, multi-bet guide Kenya, accumulator strategy South Africa, acca betting Africa 2026, football accumulator tips Africa, AFCON accumulator tips',
        'og_title': 'Accumulator Betting Tips Africa 2026 | SifuFinds',
        'h1': 'Accumulator Betting Tips for African Football &middot; 2026',
        'icon': '🎯',
        'intro': "An <strong>accumulator</strong> (or 'acca') combines multiple selections into a single bet — all selections must win for the bet to pay out. The more selections you add, the higher the potential return. A 5-fold accumulator at average odds of 2.00 per selection returns 32× your stake. Accumulators are the most popular bet type across Africa, accounting for the majority of all bets placed at Nigerian, Kenyan, and South African bookmakers.",
        'sections': [
            ('How Accumulators Work', """When you build an accumulator, each selection's odds are multiplied together:
<ul>
<li>Arsenal to Win: 1.75</li>
<li>Real Madrid to Win: 1.65</li>
<li>AFCON Favourites to Win: 1.90</li>
</ul>
Total accumulator odds = 1.75 × 1.65 × 1.90 = <strong>5.48</strong>. A ₦1,000 bet returns ₦5,480 profit.
<br><br>
<strong>The catch:</strong> All three must win. If just one loses, the entire accumulator loses. This is why accumulators have very high variance — huge wins are possible but consistent profit is very difficult.
<br><br>
Most African bookmakers set a minimum accumulator of 2 selections and a maximum of 20–30. Minimum stake is typically ₦100 / KSh 50."""),
            ('Accumulator Strategy for African Bettors', """<ol>
<li><strong>Use 4–6 selections, not 10+</strong> — Each added selection reduces your probability of winning dramatically. A 10-fold accumulator where each selection is 60% likely has only a 0.6% chance of winning. 4–5 selections is the sweet spot between odds and probability.</li>
<li><strong>Mix strong favourites with one value pick</strong> — Build your accumulator on 3–4 very likely outcomes (1.30–1.60 odds) and add one higher-value selection (2.00–3.00) to boost the total odds without adding too many legs.</li>
<li><strong>Avoid including your team</strong> — Emotion distorts analysis. Never include your favourite club in an accumulator.</li>
<li><strong>Bet on leagues you follow</strong> — Your knowledge of the NPFL, Kenya Premier League, or PSL is an edge most bookmakers under-price. Domestic African leagues often have softer odds than European competitions.</li>
<li><strong>Use Acca Boost and Acca Insurance</strong> — Many African bookmakers (1xBet, Betway) offer Acca Boost (extra bonus on winnings at 5+ selections) and Acca Insurance (refund if one leg loses). Always check the promotions section before placing.</li>
<li><strong>Keep stakes small</strong> — Never risk more than 1–2% of your monthly betting bankroll on a single accumulator. High-odds bets should always have small stakes.</li>
</ol>"""),
            ('Common Accumulator Mistakes to Avoid', """<ul>
<li><strong>Too many selections</strong> — 10+ leg accas are almost always losing bets long term. The bookmaker margin multiplies with every added selection.</li>
<li><strong>Adding poor-value favourites</strong> — Including 1.05 or 1.10 selections adds almost no value to the accumulator odds but dramatically increases the chance of a single selection killing the bet.</li>
<li><strong>Chasing a losing streak with bigger accas</strong> — If your last 5 accumulators lost, the answer is not a bigger 20-fold bet. Reduce your stakes and reassess your selections.</li>
<li><strong>Ignoring team news</strong> — A key player missing through injury or suspension can flip a favourite from 1.40 to 1.80 odds. Always check team news before locking in your accumulator.</li>
</ul>"""),
        ],
        'faq': [
            ('What is the best number of selections for an accumulator?', "Research and professional bettors consistently recommend 4–6 selections as the optimal range. This gives meaningful odds uplift (5–20× returns possible) while keeping the probability of winning reasonable. Accumulators with 10+ selections are highly entertaining but are essentially lottery tickets — the probability of all winning is usually under 2%."),
            ('Which African bookmakers offer the best accumulator bonuses?', "The best accumulator bonuses in Africa come from 1xBet (up to 50% bonus on 5+ selections), Betway (Acca Boost on 5+ selections), Sportybet (Profit Boost), and Bet9ja. Acca Insurance — where you get a refund if just one leg loses — is available at Hollywoodbets and Betway. Always check the promotions section of each bookmaker for current terms."),
            ('Can I cash out an accumulator in Africa?', "Yes. All major African bookmakers (Betway, 1xBet, Bet9ja, Sportpesa, Hollywoodbets) offer Cash Out on accumulators. You can cash out for a guaranteed profit before the final leg settles, or for a partial refund if your accumulator is losing. Partial Cash Out (cashing out a portion of your bet while leaving the rest running) is available at select bookmakers."),
            ('Are accumulators profitable long term?', "Accumulators are entertaining but statistically unfavourable long term due to the bookmaker's built-in margin multiplying with each selection. Professional bettors rarely rely on accumulators as their primary strategy. However, with careful selection and small stakes, accumulators can be profitable if you have genuine edge on individual selections and apply strict bankroll management."),
        ],
        'canonical_path': 'guides/accumulator-tips',
        'breadcrumb_name': 'Accumulator Tips Guide',
        'schema_name': 'Accumulator Betting Tips Africa 2026',
        'schema_desc': 'Complete accumulator (acca) betting guide for African football bettors. How multi-bets work, strategies, mistakes to avoid, and the best bookmakers with acca boost in Nigeria, Kenya, South Africa and Ghana.',
    },
]


def make_guide_page(g):
    sections_html = '\n'.join(
        f'''  <div class="cbox2">
    <h2>{title}</h2>
    <div style="font-size:13px;color:#444;line-height:1.75">{body}</div>
  </div>'''
        for title, body in g['sections']
    )

    faq_items = '\n'.join(f"""    <div class="faq-item">
      <button class="faq-q" onclick="this.parentElement.classList.toggle('open')">{q} <span class="faq-arr">▼</span></button>
      <div class="faq-a"><p>{a}</p></div>
    </div>""" for q, a in g['faq'])

    faq_schema = ',\n'.join(
        json.dumps({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a},
        })
        for q, a in g['faq']
    )

    return f"""<!DOCTYPE html>
<!-- sifufinds.com/{g['canonical_path']}/ — {g['og_title']} -->
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{seo_title(g['title'].removesuffix(' | SifuFinds'))}</title>
<meta name="description" content="{seo_meta_description(g['desc'])}">
<meta name="keywords" content="{g['keywords']}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="author" content="SifuFinds">
<link rel="canonical" href="https://sifufinds.com/{g['canonical_path']}/">
<link rel="alternate" hreflang="en" href="https://sifufinds.com/{g['canonical_path']}/">

<meta property="og:type" content="article">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="{g['og_title']}">
<meta property="og:description" content="{g['desc']}">
<meta property="og:url" content="https://sifufinds.com/{g['canonical_path']}/">
<meta property="og:image" content="https://sifufinds.com/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_GB">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@sifufinds">
<meta name="twitter:title" content="{g['og_title']}">
<meta name="twitter:description" content="{g['desc']}">
<meta name="twitter:image" content="https://sifufinds.com/assets/og-image.png">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "Article",
      "@id": "https://sifufinds.com/{g['canonical_path']}/#article",
      "headline": "{g['schema_name']}",
      "description": "{g['schema_desc']}",
      "url": "https://sifufinds.com/{g['canonical_path']}/",
      "inLanguage": "en-GB",
      "author": {{"@type": "Organization", "name": "SifuFinds"}},
      "publisher": {{"@type": "Organization", "name": "SifuFinds", "url": "https://sifufinds.com"}},
      "datePublished": "2026-01-01",
      "dateModified": "2026-06-02",
      "isPartOf": {{"@id": "https://sifufinds.com/#website"}}
    }},
    {{
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://sifufinds.com/"}},
        {{"@type": "ListItem", "position": 2, "name": "Guides", "item": "https://sifufinds.com/guides/"}},
        {{"@type": "ListItem", "position": 3, "name": "{g['breadcrumb_name']}", "item": "https://sifufinds.com/{g['canonical_path']}/"}}
      ]
    }},
    {{
      "@type": "FAQPage",
      "mainEntity": [{faq_schema}]
    }}
  ]
}}
</script>

<link rel="icon" type="image/x-icon" href="/favicon.ico?v=3">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32x32.png?v=3">
<link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16x16.png?v=2">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png?v=3">
<link rel="preload" href="../../assets/shared.css?v=12" as="style">
<link rel="stylesheet" href="../../assets/shared.css?v=12">
<style>
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
</style>
</head>
<body>

<div class="tbar">
  <div class="tbar-l">
    <a href="../../">🏠 Home</a>
    <a href="../../guides/">📚 Guides</a>
    <a href="../../responsible/">Responsible Gambling</a>
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
    <a class="logo" href="../../"><img src="../../assets/icon.png" width="38" height="38" alt="SifuFinds logo" style="display:block;object-fit:contain">SifuFinds</a>
    <div class="ntabs">
      <a class="nt" href="../../">⭐ Best Bonuses</a>
      <a class="nt" href="../../tips/">💡 Tips</a>
      <a class="nt" href="../../casino/">🎰 Casino</a>
      <a class="nt" href="../../odds/">📊 Live Odds<span class="lpulse" style="margin-left:4px"></span></a>
      <a class="nt" href="../../countries/">🌍 Countries</a>
      <a class="nt" href="../../blog/">📰 Blog</a>
    </div>
  </div>
</nav>

<div id="hbrands" class="hbrands"></div>

<div class="hero"><div class="wrap">
  <h1>{g['icon']} {g['h1']}</h1>
  <p>{g['intro']}</p>
  <div class="trust">
    <div class="tb">📚 Expert Guide</div>
    <div class="tb">🌍 All {TOTAL_COUNTRIES} African Countries</div>
    <div class="tb">🔄 Updated 2026</div>
    <div class="tb">✅ Verified Info</div>
  </div>
</div></div>

<div class="sec-bg"><div class="wrap">
  <div class="breadcrumb">
    <a href="../../">Home</a><span>›</span><a href="../../guides/">Guides</a><span>›</span>{g['breadcrumb_name']}
  </div>

  <div class="adv">📢 <strong>Advertiser Disclosure:</strong> We earn commission from some bookmaker links. All bonuses verified. Check T&Cs. 18+.</div>

{sections_html}

  <div class="cbox2">
    <h2>FAQ — {g['breadcrumb_name']}</h2>
{faq_items}
  </div>

  <div class="sec-lbl" style="font-size:11px;font-weight:700;color:#aaa;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;margin-top:24px">TOP LICENSED BOOKMAKERS · AFRICA · 2026</div>
  <h2 style="font-size:17px;font-weight:800;color:#111;margin-bottom:9px">Top Rated African Bookmakers</h2>

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

  <div class="resp">⚠️ Gambling involves risk. Only bet what you can afford to lose. 18+ only.</div>
</div></div>

<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison<br>
  <a href="../../">Home</a> · <a href="../../guides/">Guides</a> · <a href="../../countries/">Countries</a> · <a href="../../tips/">Tips</a> · <a href="../../blog/">Blog</a> · <a href="../../about/">About</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only.
</div>

<div class="page-modal-bg" id="page-modal"><div class="page-modal"><button class="page-modal-close" onclick="closePage()">×</button><div class="pm" id="page-content"></div></div></div>

<script src="../../assets/shared.js?v=28"></script>
<script>
const SITE={{home:'../../',tips:'../../tips/',casino:'../../casino/',odds:'../../odds/',countries:'../../countries/'}};
let _activeFilt='all';
function getCurrentCountry(){{const sel=document.getElementById('ctySel');return sel?sel.value:'NG';}}
function setFilt(btn){{document.querySelectorAll('.fp').forEach(b=>b.classList.remove('on'));btn.classList.add('on');_activeFilt=btn.dataset.f;renderBooks();}}
function filterBooks(books){{const f=_activeFilt;if(f==='all')return books;if(f==='nodep')return books.filter(b=>b.nodep);if(f==='cashout')return books.filter(b=>b.cashout);return books;}}
function sortBooks(books){{const s=document.getElementById('srt')?.value||'default';if(s==='stars')return[...books].sort((a,b)=>b.stars-a.stars);if(s==='bonus')return[...books].sort((a,b)=>(b.nodep?1:0)-(a.nodep?1:0));return books;}}
const bookCard=(b,i,rank)=>{{
  const badge=b.badge==='new'?'<span class="badge-new">NEW</span>':b.badge==='hot'?'<span class="badge-hot">HOT</span>':b.nodep?'<span class="badge-nd">NO DEP</span>':'';
  return`<div class="bkcard ${{rank<3?'top3':''}} ${{b.nodep?'nodep-card':''}}"><div class="bk-main"><span class="bk-rk">#${{rank+1}}</span><div class="bk-logo" style="background:${{b.bg}}">${{logoImg(b.url,b.name,b.abbr,b.tc,60,8)}}</div><div><div class="bk-tag">${{b.tag}}</div><div class="bk-nm">${{b.name}}${{badge}}</div><div class="bk-off">${{b.off}}</div><div class="bk-meta"><span>Min: ${{b.min}}</span><span>${{b.sports}} sports</span><span>${{b.lic}}</span></div></div><div class="bk-act"><div class="bk-stars">${{stars(b.stars)}}</div><a class="gbtn${{b.nodep?' gold':''}}" href="${{b.url}}" target="_blank" rel="noopener noreferrer">Claim Bonus →</a><div class="tc-n">T&amp;Cs Apply · 18+</div></div></div><div class="pm-row">${{(b.pms||[]).map(pm).join('')}}</div></div>`;
}};
function renderBooks(){{const cty=getCurrentCountry();const books=filterBooks(sortBooks(BOOKS[cty]||BOOKS['NG']||[]));const el=document.getElementById('bk-cards');if(!books.length){{el.innerHTML='<div class="no-results">No bookmakers match this filter.</div>';return;}}el.innerHTML=books.map((b,i)=>bookCard(b,i,i)).join('');H('mcount',`Showing ${{books.length}} bookmaker${{books.length!==1?'s':''}}`);}}
function init(){{H('foot-yr',NOW.getFullYear());renderBooks();}}
init();
</script>
</body>
</html>"""


if __name__ == '__main__':
    guides_dir = os.path.join(BASE, 'guides')
    for g in GUIDES:
        slug = g['slug']
        out_dir = os.path.join(guides_dir, slug)
        os.makedirs(out_dir, exist_ok=True)
        html = make_guide_page(g)
        out_path = os.path.join(out_dir, 'index.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'  ✓  /guides/{slug}/')
    print(f'\n✅ Generated {len(GUIDES)} guide pages')
