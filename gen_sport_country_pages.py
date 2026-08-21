#!/usr/bin/env python3
"""Generate sport × country betting pages.

Creates /betting/{sport-slug}/{country-slug}/index.html targeting searches like
"football betting Nigeria", "basketball betting Kenya", "cricket betting South Africa".
"""

import json
import os
from seo_meta import current_month_year, current_year, seo_meta_description, seo_title

BASE = os.path.dirname(os.path.abspath(__file__))
YEAR = current_year()
MONTH_YEAR = current_month_year()


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

SPORTS = [
    {
        'slug': 'football-betting',
        'name': 'Football Betting',
        'sport': 'Football',
        'icon': '⚽',
        'about': 'Football is Africa\'s most popular sport and the dominant market at every licensed bookmaker on the continent. From the English Premier League to AFCON, CAF Champions League, and local domestic leagues, African football bettors have thousands of matches and markets available every week.',
        'bet_types': ['Match Result (1X2)', 'Both Teams to Score (BTTS)', 'Over/Under Goals', 'Asian Handicap', 'Correct Score', 'Accumulator / Multi', 'First Goalscorer', 'Half-Time Result'],
        'countries': {
            'nigeria':      {'code': 'NG', 'flag': '🇳🇬', 'name': 'Nigeria',       'regulator': 'NLRC',  'leagues': ['NPFL (Nigeria Professional Football League)', 'English Premier League', 'CAF Champions League', 'AFCON (Super Eagles)', 'UEFA Champions League', 'La Liga'], 'top_tip': 'Nigerian bettors strongly favour the Premier League and NPFL. BTTS and Over 2.5 markets are most popular.', 'payments': ['OPay', 'PalmPay', 'Bank Transfer']},
            'kenya':        {'code': 'KE', 'flag': '🇰🇪', 'name': 'Kenya',         'regulator': 'BCLB',  'leagues': ['Kenyan Premier League', 'English Premier League', 'CAF Champions League', 'AFCON (Harambee Stars)', 'Serie A'], 'top_tip': 'Kenyan bettors are among Africa\'s most sophisticated, with strong interest in correct score and accumulator betting.', 'payments': ['M-Pesa', 'Airtel Money', 'Visa']},
            'ghana':        {'code': 'GH', 'flag': '🇬🇭', 'name': 'Ghana',         'regulator': 'GCA',   'leagues': ['Ghana Premier League', 'English Premier League', 'CAF Confederation Cup', 'AFCON (Black Stars)', 'Bundesliga'], 'top_tip': 'Ghanaian bettors follow the Black Stars closely. Match result and accumulator markets dominate.', 'payments': ['MTN MoMo', 'Vodafone Cash', 'Visa']},
            'south-africa': {'code': 'ZA', 'flag': '🇿🇦', 'name': 'South Africa',  'regulator': 'WCGRB', 'leagues': ['PSL (Kaizer Chiefs, Orlando Pirates, Sundowns)', 'English Premier League', 'UEFA Champions League', 'La Liga', 'Bundesliga'], 'top_tip': 'South African bettors are highly engaged with the PSL and global European leagues. The market is among the most mature in Africa.', 'payments': ['FNB', 'Nedbank', 'Visa', 'Mastercard']},
            'tanzania':     {'code': 'TZ', 'flag': '🇹🇿', 'name': 'Tanzania',      'regulator': 'GBT',   'leagues': ['NBC Premier League', 'English Premier League', 'CAF Champions League', 'AFCON (Taifa Stars)', 'Serie A'], 'top_tip': 'Tanzanian bettors love accumulators and the Premier League. M-Pesa deposits are near-instant.', 'payments': ['M-Pesa', 'Airtel Money', 'Tigo Pesa']},
            'uganda':       {'code': 'UG', 'flag': '🇺🇬', 'name': 'Uganda',        'regulator': 'NLB',   'leagues': ['FUFA Big League', 'English Premier League', 'CAF Champions League', 'AFCON (Uganda Cranes)', 'Serie A'], 'top_tip': 'Ugandan bettors are very active on weekend accumulators. MTN MoMo is the preferred payment method.', 'payments': ['MTN MoMo', 'Airtel Money', 'Visa']},
            'ethiopia':     {'code': 'ET', 'flag': '🇪🇹', 'name': 'Ethiopia',      'regulator': 'LCGA',  'leagues': ['Ethiopian Premier League', 'English Premier League', 'CAF Champions League', 'AFCON (Walya Antelope)', 'Bundesliga'], 'top_tip': 'Ethiopian football betting is rapidly growing with Telebirr mobile money enabling easy deposits.', 'payments': ['Telebirr', 'CBE Birr', 'Visa']},
            'ivory-coast':  {'code': 'CI', 'flag': '🇨🇮', 'name': 'Ivory Coast',   'regulator': 'LONACI','leagues': ['MTN Ligue 1 CI', 'Ligue 1 (France)', 'English Premier League', 'CAF Champions League', 'AFCON (Éléphants)'], 'top_tip': 'Ivorian bettors closely follow Ligue 1 (France) and the Éléphants national team. Orange Money is the dominant payment method.', 'payments': ['MTN MoMo', 'Orange Money', 'Moov Money']},
            'cameroon':     {'code': 'CM', 'flag': '🇨🇲', 'name': 'Cameroon',      'regulator': 'MinFin','leagues': ['MTN Elite One', 'Ligue 1 (France)', 'English Premier League', 'CAF Champions League', 'AFCON (Indomitable Lions)'], 'top_tip': 'Cameroonians bet heavily on the Indomitable Lions and Ligue 1 (France). AFCON generates massive betting volumes.', 'payments': ['MTN MoMo', 'Orange Money', 'Visa']},
            'senegal':      {'code': 'SN', 'flag': '🇸🇳', 'name': 'Senegal',       'regulator': 'DGJPS', 'leagues': ['Ligue 1 Sénégal', 'Ligue 1 (France)', 'English Premier League', 'CAF Champions League', 'AFCON (Lions of Teranga)'], 'top_tip': 'Senegalese bettors are among the most active in West Africa, following the AFCON champion Lions of Teranga and European leagues closely.', 'payments': ['Orange Money', 'Wave', 'Free Money']},
            'rwanda':       {'code': 'RW', 'flag': '🇷🇼', 'name': 'Rwanda',        'regulator': 'RGA',   'leagues': ['Rwanda Premier League', 'English Premier League', 'CAF Champions League', 'AFCON (Amavubi Stars)', 'La Liga'], 'top_tip': 'Rwanda has one of Africa\'s fastest-growing mobile betting markets thanks to its high digital adoption. MTN MoMo drives most transactions.', 'payments': ['MTN MoMo', 'Airtel Money', 'Visa']},
            'zimbabwe':     {'code': 'ZW', 'flag': '🇿🇼', 'name': 'Zimbabwe',      'regulator': 'LGB',   'leagues': ['Castle Lager PSL', 'English Premier League', 'CAF Champions League', 'AFCON (Warriors)', 'La Liga'], 'top_tip': 'Zimbabwean bettors use EcoCash for fast deposits and withdrawals. Premier League and the Warriors are most-bet markets.', 'payments': ['EcoCash', 'OneMoney', 'Visa']},
            'zambia':       {'code': 'ZM', 'flag': '🇿🇲', 'name': 'Zambia',        'regulator': 'GLAZ',  'leagues': ['Super League of Zambia', 'English Premier League', 'CAF Champions League', 'AFCON (Chipolopolo Boys)', 'La Liga'], 'top_tip': 'Zambian bettors are passionate about the Chipolopolo and the Super League. Accumulators on European football are the most popular bet type.', 'payments': ['MTN MoMo', 'Airtel Money', 'Visa']},
            'egypt':        {'code': 'EG', 'flag': '🇪🇬', 'name': 'Egypt',         'regulator': 'ERA',   'leagues': ['Egyptian Premier League (Al-Ahly, Zamalek)', 'CAF Champions League', 'English Premier League', 'La Liga', 'Serie A'], 'top_tip': 'Egyptian bettors follow Al-Ahly and Zamalek fanatically. European leagues also generate strong betting volumes.', 'payments': ['Vodafone Cash', 'Orange Money Egypt', 'Visa']},
            'morocco':      {'code': 'MA', 'flag': '🇲🇦', 'name': 'Morocco',       'regulator': 'MDJS',  'leagues': ['Botola Pro (Wydad, Raja)', 'Ligue 1 (France)', 'La Liga', 'English Premier League', 'AFCON (Atlas Lions)'], 'top_tip': 'Morocco\'s 2022 World Cup semifinal run created a massive surge in sports betting interest. Botola Pro and European leagues are most popular.', 'payments': ['Maroc Telecom Money', 'Orange Morocco', 'Visa']},
            'angola':       {'code': 'AO', 'flag': '🇦🇴', 'name': 'Angola',        'regulator': 'IRSE',  'leagues': ['Girabola (Angola Premier League)', 'English Premier League', 'CAF Champions League', 'AFCON (Palancas Negras)', 'La Liga'], 'top_tip': 'Angolan bettors follow European football closely. Multicaixa is the primary payment method for betting deposits.', 'payments': ['Multicaixa', 'Unitel Money', 'Visa']},
            'dr-congo':     {'code': 'CD', 'flag': '🇨🇩', 'name': 'DR Congo',      'regulator': 'CNJH',  'leagues': ['LINAFOOT (TP Mazembe, Vita Club)', 'Ligue 1 (France)', 'English Premier League', 'CAF Champions League', 'AFCON (Leopards)'], 'top_tip': 'DR Congo has Africa\'s most passionate football culture. The Leopards and TP Mazembe drive massive local betting interest.', 'payments': ['M-Pesa', 'Airtel Money', 'Orange Money']},
            'malawi':       {'code': 'MW', 'flag': '🇲🇼', 'name': 'Malawi',        'regulator': 'GBM',   'leagues': ['TNM Super League (Nyasa Big Bullets)', 'English Premier League', 'CAF Champions League', 'AFCON (Flames)', 'La Liga'], 'top_tip': 'Malawian bettors are passionate about the Flames and the TNM Super League. Airtel Money and TNM Mpamba are the leading payment methods.', 'payments': ['Airtel Money', 'TNM Mpamba', 'Visa']},
            'mozambique':   {'code': 'MZ', 'flag': '🇲🇿', 'name': 'Mozambique',    'regulator': 'GCMZ',  'leagues': ['Moçambola', 'English Premier League', 'CAF Champions League', 'AFCON (Mambas)', 'La Liga'], 'top_tip': 'Mozambican bettors are growing rapidly in number with M-Pesa enabling easy deposits. Premier League is most popular.', 'payments': ['M-Pesa', 'Mkesh', 'Visa']},
            'botswana':     {'code': 'BW', 'flag': '🇧🇼', 'name': 'Botswana',      'regulator': 'GCAB',  'leagues': ['Botswana Premier League', 'English Premier League', 'CAF Champions League', 'AFCON (Zebras)', 'La Liga'], 'top_tip': 'Botswana has one of Africa\'s highest smartphone penetration rates, supporting a sophisticated mobile betting market.', 'payments': ['Orange Money', 'First National', 'Visa']},
            'namibia':      {'code': 'NA', 'flag': '🇳🇦', 'name': 'Namibia',       'regulator': 'GBN',   'leagues': ['Namibia Premier League', 'English Premier League', 'PSL (South Africa)', 'AFCON (Brave Warriors)', 'La Liga'], 'top_tip': 'Namibian bettors follow both local football and South African PSL closely. Hollywoodbets and Betway dominate the market.', 'payments': ['FNB Namibia', 'Bank Windhoek', 'Visa']},
            'sierra-leone': {'code': 'SL', 'flag': '🇸🇱', 'name': 'Sierra Leone',  'regulator': 'NLA',   'leagues': ['Sierra Leone Premier League', 'English Premier League', 'CAF Champions League', 'AFCON (Leone Stars)', 'La Liga'], 'top_tip': 'Sierra Leone\'s betting market is growing rapidly. Orange Money enables quick deposits at licensed bookmakers.', 'payments': ['Orange Money', 'Africell Money', 'Visa']},
            'liberia':      {'code': 'LR', 'flag': '🇱🇷', 'name': 'Liberia',       'regulator': 'CCB',   'leagues': ['Liberia First Division', 'English Premier League', 'CAF Champions League', 'AFCON (Lone Star)', 'La Liga'], 'top_tip': 'Liberian bettors follow the Lone Star national team closely, especially during AFCON qualifying campaigns.', 'payments': ['Orange Money', 'Lonestar Money', 'MTN MoMo']},
        },
    },
    {
        'slug': 'basketball-betting',
        'name': 'Basketball Betting',
        'sport': 'Basketball',
        'icon': '🏀',
        'about': 'Basketball betting is the second most popular sport at African bookmakers after football. The NBA draws enormous interest from bettors across Africa, particularly in Nigeria, South Africa, and Kenya. African basketball is also growing rapidly, with the BAL (Basketball Africa League) and national competitions gaining traction.',
        'bet_types': ['Match Winner (Moneyline)', 'Point Spread', 'Total Points (Over/Under)', '1st Quarter Result', 'Player Props', 'Accumulator / Parlay'],
        'countries': {
            'nigeria':      {'code': 'NG', 'flag': '🇳🇬', 'name': 'Nigeria',      'regulator': 'NLRC', 'leagues': ['NBA (All Teams)', 'BAL (Basketball Africa League)', 'NBBF (Nigeria Basketball Federation)', 'NCAA Basketball', 'EuroLeague'], 'top_tip': 'Nigeria produces top NBA players (including Giannis, Achiuwa families). NBA betting is extremely popular, with live in-play markets dominant.', 'payments': ['OPay', 'PalmPay', 'Bank Transfer']},
            'kenya':        {'code': 'KE', 'flag': '🇰🇪', 'name': 'Kenya',        'regulator': 'BCLB', 'leagues': ['NBA', 'BAL', 'Kenya Basketball Federation League', 'NCAA'], 'top_tip': 'Kenyan bettors increasingly follow the NBA and BAL. Point spread and totals markets are growing in popularity.', 'payments': ['M-Pesa', 'Airtel Money', 'Visa']},
            'south-africa': {'code': 'ZA', 'flag': '🇿🇦', 'name': 'South Africa', 'regulator': 'WCGRB','leagues': ['NBA', 'BAL', 'South African Basketball League', 'EuroLeague'], 'top_tip': 'South Africa has the most developed basketball betting market on the continent, with deep NBA interest and strong domestic competition.', 'payments': ['FNB', 'Nedbank', 'Visa', 'Mastercard']},
            'ghana':        {'code': 'GH', 'flag': '🇬🇭', 'name': 'Ghana',        'regulator': 'GCA',  'leagues': ['NBA', 'BAL', 'Ghana Basketball Association', 'NCAA'], 'top_tip': 'Ghanaian bettors are passionate NBA followers, particularly for teams featuring African players or players of African descent.', 'payments': ['MTN MoMo', 'Vodafone Cash', 'Visa']},
            'senegal':      {'code': 'SN', 'flag': '🇸🇳', 'name': 'Senegal',      'regulator': 'DGJPS','leagues': ['NBA', 'BAL', 'Nationale 1 (Senegal Basketball)', 'FIBA AfroBasket'], 'top_tip': 'Senegal has produced NBA players and has a strong basketball culture. BAL and NBA betting are increasingly popular.', 'payments': ['Orange Money', 'Wave', 'Free Money']},
            'egypt':        {'code': 'EG', 'flag': '🇪🇬', 'name': 'Egypt',        'regulator': 'ERA',  'leagues': ['NBA', 'BAL', 'Egyptian Basketball League', 'EuroLeague', 'FIBA Africa'], 'top_tip': 'Egyptian bettors follow both the NBA and EuroLeague. The national team\'s strength in FIBA Africa drives local interest.', 'payments': ['Vodafone Cash', 'Orange Money Egypt', 'Visa']},
        },
    },
    {
        'slug': 'cricket-betting',
        'name': 'Cricket Betting',
        'sport': 'Cricket',
        'icon': '🏏',
        'about': 'Cricket betting in Africa is concentrated in Southern Africa and East Africa. South Africa is the continent\'s strongest cricket nation, with the Proteas drawing large betting volumes for Test matches, ODIs, and T20s. Zimbabwe and Kenya also have established cricket cultures.',
        'bet_types': ['Match Winner', 'Top Batsman', 'Top Bowler', 'Total Runs (Over/Under)', 'Toss Winner', 'Player of the Match', 'Series Winner'],
        'countries': {
            'south-africa': {'code': 'ZA', 'flag': '🇿🇦', 'name': 'South Africa', 'regulator': 'WCGRB', 'leagues': ['Proteas (SA National Team)', 'CSA T20 Challenge', 'ICC World Cup', 'IPL', 'The Hundred', 'Test Cricket'], 'top_tip': 'South Africa is Africa\'s premier cricket betting market. Proteas tests and IPL generate enormous volumes. Top batsman markets are especially popular.', 'payments': ['FNB', 'Nedbank', 'Standard Bank', 'Visa']},
            'zimbabwe':     {'code': 'ZW', 'flag': '🇿🇼', 'name': 'Zimbabwe',     'regulator': 'LGB',   'leagues': ['Zimbabwe National Team', 'ICC T20 World Cup', 'IPL', 'Test Cricket'], 'top_tip': 'Zimbabwe has a passionate cricket following, with EcoCash making betting accessible. IPL and Zimbabwe international matches are most popular.', 'payments': ['EcoCash', 'OneMoney', 'Visa']},
            'kenya':        {'code': 'KE', 'flag': '🇰🇪', 'name': 'Kenya',        'regulator': 'BCLB',  'leagues': ['Kenya Cricket National Team', 'ICC World Cricket League', 'IPL', 'The Hundred'], 'top_tip': 'Kenya has a growing cricket culture and dedicated cricket bettors. IPL is the most popular competition for betting.', 'payments': ['M-Pesa', 'Airtel Money', 'Visa']},
            'nigeria':      {'code': 'NG', 'flag': '🇳🇬', 'name': 'Nigeria',      'regulator': 'NLRC',  'leagues': ['IPL', 'ICC T20 World Cup', 'The Hundred', 'BBL', 'Test Cricket'], 'top_tip': 'Nigerian cricket betting is growing rapidly, driven by IPL and T20 format popularity. OPay deposits are instant.', 'payments': ['OPay', 'PalmPay', 'Bank Transfer']},
            'ghana':        {'code': 'GH', 'flag': '🇬🇭', 'name': 'Ghana',        'regulator': 'GCA',   'leagues': ['IPL', 'ICC T20 World Cup', 'The Hundred', 'Test Cricket'], 'top_tip': 'Ghanaian cricket betting is primarily driven by IPL. Ghana Cricket Association has been growing the sport domestically.', 'payments': ['MTN MoMo', 'Vodafone Cash', 'Visa']},
        },
    },
    {
        'slug': 'rugby-betting',
        'name': 'Rugby Betting',
        'sport': 'Rugby',
        'icon': '🏉',
        'about': 'Rugby betting in Africa is dominated by Southern Africa, where the sport has deep historical roots. The Springboks of South Africa are the world\'s top team, making rugby betting extremely popular in South Africa, Namibia, Zimbabwe, and Botswana. The Rugby World Cup, Super Rugby, and United Rugby Championship draw large betting volumes.',
        'bet_types': ['Match Winner', 'Handicap', 'Total Points', 'First Try Scorer', 'Winning Margin', 'Half-Time Leader'],
        'countries': {
            'south-africa': {'code': 'ZA', 'flag': '🇿🇦', 'name': 'South Africa', 'regulator': 'WCGRB', 'leagues': ['Springboks (World Champions)', 'URC (United Rugby Championship)', 'Super Rugby', 'Rugby Championship', 'Rugby World Cup'], 'top_tip': 'South Africa is the world\'s top rugby betting market on the continent. Springboks matches generate massive volumes at Hollywoodbets, Betway, and other licensed bookmakers.', 'payments': ['FNB', 'Nedbank', 'Standard Bank', 'Visa']},
            'namibia':      {'code': 'NA', 'flag': '🇳🇦', 'name': 'Namibia',      'regulator': 'GBN',   'leagues': ['Namibia Welwitschias', 'Rugby World Cup', 'Super Rugby', 'URC'], 'top_tip': 'Namibia has qualified for multiple Rugby World Cups. Local betting on Welwitschias and Springboks is extremely popular.', 'payments': ['FNB Namibia', 'Bank Windhoek', 'Visa']},
            'zimbabwe':     {'code': 'ZW', 'flag': '🇿🇼', 'name': 'Zimbabwe',     'regulator': 'LGB',   'leagues': ['Zimbabwe Sables', 'Rugby World Cup', 'Super Rugby', 'Rugby Africa Cup'], 'top_tip': 'Rugby has a strong following in Zimbabwe alongside cricket. The Sables and Springboks are the most popular rugby betting markets.', 'payments': ['EcoCash', 'OneMoney', 'Visa']},
            'botswana':     {'code': 'BW', 'flag': '🇧🇼', 'name': 'Botswana',     'regulator': 'GCAB',  'leagues': ['Botswana Vultures', 'Rugby Africa Cup', 'Super Rugby', 'URC'], 'top_tip': 'Rugby is Botswana\'s second most popular sport for betting after football. Springboks proximity drives strong interest in South African rugby.', 'payments': ['Orange Money', 'First National', 'Visa']},
            'kenya':        {'code': 'KE', 'flag': '🇰🇪', 'name': 'Kenya',        'regulator': 'BCLB',  'leagues': ['Kenya Simbas (Rugby 7s and 15s)', 'World Rugby Sevens Series', 'Rugby Africa Cup', 'Rugby World Cup'], 'top_tip': 'Kenya is a rugby powerhouse in 7s format. The World Sevens Series generates strong local betting interest, with M-Pesa enabling fast deposits.', 'payments': ['M-Pesa', 'Airtel Money', 'Visa']},
        },
    },
    {
        'slug': 'tennis-betting',
        'name': 'Tennis Betting',
        'sport': 'Tennis',
        'icon': '🎾',
        'about': 'Tennis betting is popular across Africa, driven by the global ATP and WTA tours. Grand Slam tournaments — Australian Open, French Open, Wimbledon, and US Open — generate enormous betting volumes. African tennis has also been growing, with Moroccan and South African players gaining international recognition.',
        'bet_types': ['Match Winner', 'Set Betting', 'Total Games (Over/Under)', 'First Set Winner', 'Handicap Games', 'Tournament Winner'],
        'countries': {
            'south-africa': {'code': 'ZA', 'flag': '🇿🇦', 'name': 'South Africa', 'regulator': 'WCGRB', 'leagues': ['Wimbledon', 'US Open', 'French Open', 'Australian Open', 'ATP Tour', 'WTA Tour'], 'top_tip': 'South Africa has the most sophisticated tennis betting market in Africa, with deep interest in all four Grand Slams.', 'payments': ['FNB', 'Nedbank', 'Visa', 'Mastercard']},
            'nigeria':      {'code': 'NG', 'flag': '🇳🇬', 'name': 'Nigeria',      'regulator': 'NLRC',  'leagues': ['Wimbledon', 'US Open', 'French Open', 'Australian Open', 'ATP Tour'], 'top_tip': 'Nigerian tennis bettors focus on Grand Slams and top ATP players. Match winner and set betting are the most popular markets.', 'payments': ['OPay', 'PalmPay', 'Bank Transfer']},
            'kenya':        {'code': 'KE', 'flag': '🇰🇪', 'name': 'Kenya',        'regulator': 'BCLB',  'leagues': ['Wimbledon', 'US Open', 'French Open', 'ATP Tour', 'WTA Tour'], 'top_tip': 'Kenyan tennis betting is growing, with Grand Slams generating the highest volumes. M-Pesa deposits are near-instant.', 'payments': ['M-Pesa', 'Airtel Money', 'Visa']},
            'morocco':      {'code': 'MA', 'flag': '🇲🇦', 'name': 'Morocco',      'regulator': 'MDJS',  'leagues': ['French Open (Roland Garros)', 'Wimbledon', 'ATP Tour', 'WTA Tour', 'Grand Prix Hassan II'], 'top_tip': 'Morocco has a strong tennis tradition. Roland Garros is the most popular tournament for Moroccan bettors, given its cultural proximity.', 'payments': ['Maroc Telecom Money', 'Orange Morocco', 'Visa']},
            'egypt':        {'code': 'EG', 'flag': '🇪🇬', 'name': 'Egypt',        'regulator': 'ERA',   'leagues': ['French Open', 'Wimbledon', 'US Open', 'ATP Tour', 'WTA Tour'], 'top_tip': 'Egypt has a growing tennis betting market. Grand Slam match winner markets are dominant among Egyptian bettors.', 'payments': ['Vodafone Cash', 'Orange Money Egypt', 'Visa']},
            'ghana':        {'code': 'GH', 'flag': '🇬🇭', 'name': 'Ghana',        'regulator': 'GCA',   'leagues': ['Wimbledon', 'US Open', 'French Open', 'ATP Tour', 'WTA Tour'], 'top_tip': 'Ghanaian tennis betting is growing steadily. Grand Slam match winner and over/under games markets are most popular.', 'payments': ['MTN MoMo', 'Vodafone Cash', 'Visa']},
        },
    },
]


def build_page(sport, country_slug, country_data):
    sport_name = sport['name']
    sport_slug = sport['slug']
    sport_icon = sport['icon']
    sport_sport = sport['sport']
    sport_about = sport['about']
    bet_types = sport['bet_types']

    cname = country_data['name']
    code = country_data['code']
    flag = country_data['flag']
    regulator = country_data['regulator']
    leagues = country_data['leagues']
    top_tip = country_data['top_tip']
    payments = country_data['payments']

    assets = '../../../'
    canonical = f'https://sifufinds.com/betting/{sport_slug}/{country_slug}/'

    title = seo_title(f'Best {sport_sport} Betting Sites {cname} {YEAR}')
    description = f'Best {sport_sport.lower()} betting sites in {cname} {YEAR}. Compare verified bonuses, {sport_sport.lower()} odds and bookmaker reviews. All bookmakers licensed by {regulator}. Updated daily.'
    keywords = f'{sport_sport.lower()} betting {cname.lower()}, {sport_sport.lower()} betting sites {cname.lower()} {YEAR}, best {sport_sport.lower()} bookmakers {cname.lower()}, {sport_sport.lower()} odds {cname.lower()}'

    leagues_html = ''.join(f'<li>{lg}</li>' for lg in leagues)
    bet_types_html = ''.join(f'<span class="pay-chip">{bt}</span>' for bt in bet_types)

    faq_items = [
        (f'What are the best {sport_sport.lower()} betting sites in {cname}?',
         f'The best licensed {sport_sport.lower()} betting sites in {cname} are listed above. All are regulated by {regulator} and accept {", ".join(payments[:2])}. Use the Highest Bonus filter to compare current welcome offers.'),
        (f'What {sport_sport.lower()} markets can I bet on in {cname}?',
         f'At licensed {cname} bookmakers, you can bet on: {", ".join(bet_types[:5])}. Most bookmakers offer 100+ markets per {sport_sport.lower()} match including pre-match and live in-play betting.'),
        (f'How do I bet on {sport_sport.lower()} in {cname}?',
         f'To bet on {sport_sport.lower()} in {cname}: (1) Choose a licensed bookmaker from the list above, (2) Register and verify your account, (3) Deposit via {payments[0]}, (4) Navigate to {sport_sport} in the sportsbook, (5) Select your event and market, (6) Enter your stake and confirm your bet.'),
        (f'Is {sport_sport.lower()} betting legal in {cname}?',
         f'Yes. {sport_sport} betting is legal in {cname}. All bookmakers listed on SifuFinds are licensed and regulated by <strong>{regulator}</strong>. Only bet with licensed bookmakers.'),
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

    return f'''<!DOCTYPE html>
<!-- sifufinds.com/betting/{sport_slug}/{country_slug}/ — {sport_sport} Betting {cname} {YEAR} -->
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
<meta name="author" content="SifuFinds">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="en-{code}" href="{canonical}">
<link rel="alternate" hreflang="en" href="{canonical}">
<meta name="geo.region" content="{code}">
<meta name="geo.placename" content="{cname}">

<meta property="og:type" content="website">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="Best {sport_sport} Betting Sites {cname} {YEAR} | SifuFinds">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="https://sifufinds.com/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_GB">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@sifufinds">
<meta name="twitter:title" content="Best {sport_sport} Betting Sites {cname} {YEAR} | SifuFinds">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="https://sifufinds.com/assets/og-image.png">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "WebPage",
      "@id": "{canonical}#webpage",
      "name": "{title}",
      "description": "{description}",
      "url": "{canonical}",
      "inLanguage": "en-GB",
      "isPartOf": {{"@id": "https://sifufinds.com/#website"}}
    }},
    {{
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://sifufinds.com/"}},
        {{"@type": "ListItem", "position": 2, "name": "{sport_sport} Betting Africa", "item": "https://sifufinds.com/betting/{sport_slug}/"}},
        {{"@type": "ListItem", "position": 3, "name": "{sport_sport} Betting {cname}", "item": "{canonical}"}}
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
.sport-hero{{background:linear-gradient(135deg,#0a3d1e 0%,#1a6b35 100%);color:#fff;padding:28px 0}}
.sport-hero h1{{font-size:clamp(20px,3.5vw,28px);font-weight:900;margin-bottom:8px;letter-spacing:-.5px}}
.sport-hero p{{font-size:14px;color:rgba(255,255,255,.85);max-width:640px;line-height:1.65}}
.tip-box{{background:#fff8e1;border:2px solid #fdd835;border-radius:10px;padding:14px;margin:14px 0}}
.tip-box h3{{font-size:13px;font-weight:800;color:#f57f17;margin-bottom:6px}}
.tip-box p{{font-size:13px;color:#333;line-height:1.6;margin:0}}
.pay-chip{{background:#f5f5f5;border:1px solid #e0e0e0;border-radius:5px;padding:4px 10px;font-size:12px;font-weight:500;color:#333}}
.market-grid{{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}}
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

<div class="sport-hero">
  <div class="wrap">
    <h1>{flag} {sport_icon} Best {sport_sport} Betting Sites in {cname} {YEAR}</h1>
    <p>Compare the best licensed {sport_sport.lower()} bookmakers in {cname}. Verified bonuses, competitive {sport_sport.lower()} odds, and all regulated by {regulator}. Updated {MONTH_YEAR}.</p>
  </div>
</div>

<div class="sec-bg"><div class="wrap" style="padding-top:14px">
  <div class="breadcrumb">
    <a href="{assets}">Home</a><span>›</span>
    <a href="{assets}betting/{sport_slug}/">{sport_sport} Betting</a><span>›</span>
    {sport_sport} Betting {cname}
  </div>

  <div class="adv">📢 <strong>Advertiser Disclosure:</strong> We earn commission from some bookmaker links. All bonuses verified. Check T&Cs. 18+.</div>

  <div class="tip-box">
    <h3>💡 SifuFinds Expert Tip — {sport_sport} Betting in {cname}</h3>
    <p>{top_tip}</p>
  </div>

  <div class="sec-lbl" style="font-size:11px;font-weight:700;color:#aaa;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">BEST {sport_sport.upper()} BOOKMAKERS · {cname.upper()} · {YEAR}</div>
  <h2 style="font-size:17px;font-weight:800;color:#111;margin-bottom:9px">Best {sport_sport} Betting Sites in {cname} — Verified {YEAR}</h2>

  <div class="fbar"><div class="fr">
    <span class="fr-label">Sort:</span>
    <select class="fsel" id="srt" onchange="renderBooks()">
      <option value="default">Editors' Picks</option>
      <option value="stars">Highest Rated</option>
      <option value="bonus">Highest Bonus</option>
    </select>
    <span class="fr-label" style="margin-left:4px">Filter:</span>
    <button class="fp on" data-f="all" onclick="setFilt(this)">All</button>
    <button class="fp" data-f="cashout" onclick="setFilt(this)">Cash Out</button>
    <button class="fp" data-f="nodep" onclick="setFilt(this)">No Deposit</button>
  </div></div>

  <div class="mc" id="mcount"></div>
  <div id="bk-cards"><noscript><p style="padding:16px;color:#666">Enable JavaScript to view bookmaker listings.</p></noscript></div>

  <div class="cbox2">
    <h2>About {sport_sport} Betting in Africa</h2>
    <p>{sport_about}</p>
  </div>

  <div class="cbox2">
    <h2>Popular {sport_sport} Competitions in {cname}</h2>
    <ul style="padding-left:18px;margin:0">
      {leagues_html}
    </ul>
  </div>

  <div class="cbox2">
    <h2>{sport_sport} Betting Markets Available in {cname}</h2>
    <div class="market-grid">{bet_types_html}</div>
  </div>

  <div class="cbox2">
    <h2>FAQ — {sport_sport} Betting in {cname}</h2>
{faq_html}  </div>

  <div class="resp">⚠️ Gambling involves risk. Only bet what you can afford to lose. 18+ only.</div>
</div></div>

<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison<br>
  <a href="{assets}">Home</a> · <a href="{assets}best-bonus-in-{country_slug}/">{cname} Betting</a> · <a href="{assets}betting/{sport_slug}/">{sport_sport} Betting Africa</a> · <a href="{assets}tips/">{sport_sport} Tips</a> · <a href="{assets}about/">About</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only.
</div>

<div class="page-modal-bg" id="page-modal"><div class="page-modal"><button class="page-modal-close" onclick="closePage()">×</button><div class="pm" id="page-content"></div></div></div>

<script src="{assets}assets/shared.js?v=27"></script>
<script>
const SITE={{home:'{assets}',tips:'{assets}tips/',casino:'{assets}casino/',odds:'{assets}odds/',countries:'{assets}countries/'}};
const _PAGE_CTY='{code}';
let _activeFilt='all';
function getCurrentCountry(){{return _PAGE_CTY;}}
function setFilt(btn){{document.querySelectorAll('.fp').forEach(b=>b.classList.remove('on'));btn.classList.add('on');_activeFilt=btn.dataset.f;renderBooks();}}
function filterBooks(books){{const f=_activeFilt;if(f==='all')return books;if(f==='nodep')return books.filter(b=>b.nodep);if(f==='cashout')return books.filter(b=>b.cashout);return books;}}
function sortBooks(books){{const s=document.getElementById('srt')?.value||'default';if(s==='stars')return[...books].sort((a,b)=>b.stars-a.stars);if(s==='bonus')return[...books].sort((a,b)=>(b.nodep?1:0)-(a.nodep?1:0));return books;}}
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
function renderBooks(){{const books=filterBooks(sortBooks(BOOKS[_PAGE_CTY]||[]));const el=document.getElementById('bk-cards');if(!books.length){{el.innerHTML='<div class="no-results">No bookmakers match this filter.</div>';return;}}el.innerHTML=books.map((b,i)=>bookCard(b,i,i)).join('');H('mcount',`Showing ${{books.length}} bookmaker${{books.length!==1?'s':''}}`);}}
function init(){{const sel=document.getElementById('ctySel');if(sel)sel.value=_PAGE_CTY;H('foot-yr',NOW.getFullYear());renderBooks();}}
init();
</script>
</body>
</html>'''


def main():
    created = 0
    for sport in SPORTS:
        sport_slug = sport['slug']
        for country_slug, country_data in sport['countries'].items():
            out_dir = os.path.join(BASE, 'betting', sport_slug, country_slug)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, 'index.html')

            html = build_page(sport, country_slug, country_data)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(html)
            created += 1
            print(f'  ✓  betting/{sport_slug}/{country_slug}/index.html')

    print(f'\n✅  {created} sport × country pages generated.')


if __name__ == '__main__':
    main()
