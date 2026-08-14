#!/usr/bin/env python3
"""Generate city-level betting pages for all 23 African countries.

Scales from 8 cities to 200+ cities, targeting searches like:
"betting sites in Kano Nigeria", "best bookmakers Kisumu Kenya", etc.
"""

import json
from seo_meta import seo_meta_description
import os

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

# ── CITIES DATA ─────────────────────────────────────────────────────────────
CITIES = [
    # ── NIGERIA ──────────────────────────────────────────────────────────────
    {
        'path': 'countries/nigeria/lagos',
        'city': 'Lagos', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa', 'Mastercard'],
        'about': "Lagos is Nigeria's commercial capital and Africa's largest city, home to 20+ million people and the highest concentration of registered sports bettors on the continent. All NLRC-licensed bookmakers operate here with hundreds of retail locations and a thriving mobile betting market.",
        'sports': ['Premier League', 'NPFL', 'CAF Champions League', 'AFCON', 'NBA Basketball'],
        'population': '20+ million',
    },
    {
        'path': 'countries/nigeria/abuja',
        'city': 'Abuja', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa', 'Mastercard'],
        'about': "Abuja is Nigeria's federal capital and a rapidly growing betting market. As a city of government workers and professionals, Abuja bettors tend to be tech-savvy and heavily use mobile betting apps. All major NLRC-licensed bookmakers are active here.",
        'sports': ['Premier League', 'Super Eagles', 'Champions League', 'AFCON', 'Basketball'],
        'population': '3+ million',
    },
    {
        'path': 'countries/nigeria/kano',
        'city': 'Kano', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa'],
        'about': "Kano is Nigeria's second largest city and a major commercial hub in the north. Sports betting is popular among the city's large youth population, with football being the dominant market.",
        'sports': ['Premier League', 'NPFL', 'Champions League', 'AFCON'],
        'population': '4+ million',
    },
    {
        'path': 'countries/nigeria/ibadan',
        'city': 'Ibadan', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa', 'Mastercard'],
        'about': "Ibadan, Nigeria's third largest city and home to one of Africa's oldest universities, has a vibrant betting culture driven by its large student and young professional population.",
        'sports': ['Premier League', 'NPFL', 'La Liga', 'AFCON', 'Basketball'],
        'population': '3.5+ million',
    },
    {
        'path': 'countries/nigeria/port-harcourt',
        'city': 'Port Harcourt', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa', 'Mastercard'],
        'about': "Port Harcourt, the oil capital of Nigeria, has one of the fastest-growing mobile betting markets in the country. High disposable incomes in the city have driven strong demand for premium bookmaker services.",
        'sports': ['Premier League', 'NPFL', 'Champions League', 'AFCON'],
        'population': '2+ million',
    },
    {
        'path': 'countries/nigeria/benin-city',
        'city': 'Benin City', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa'],
        'about': "Benin City, the ancient capital of the Benin Kingdom, is a major betting market in South-South Nigeria. The city has a passionate football culture and high smartphone penetration driving mobile betting growth.",
        'sports': ['Premier League', 'NPFL', 'Champions League', 'La Liga'],
        'population': '1.5+ million',
    },
    {
        'path': 'countries/nigeria/enugu',
        'city': 'Enugu', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa'],
        'about': "Enugu, the Coal City, is the commercial hub of Eastern Nigeria and home to many passionate football bettors. The city's large student population from the University of Nigeria drives strong betting app usage.",
        'sports': ['Premier League', 'NPFL (Enugu Rangers)', 'Champions League', 'AFCON'],
        'population': '1+ million',
    },
    {
        'path': 'countries/nigeria/kaduna',
        'city': 'Kaduna', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa'],
        'about': "Kaduna is one of Nigeria's major northern cities and an important industrial and educational centre. The city's large young population makes it a significant sports betting market.",
        'sports': ['Premier League', 'NPFL', 'Champions League', 'AFCON'],
        'population': '1.5+ million',
    },
    {
        'path': 'countries/nigeria/onitsha',
        'city': 'Onitsha', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa'],
        'about': "Onitsha is Nigeria's major commercial hub in Anambra State and home to one of Africa's largest markets. The city's traders and entrepreneurs are an active sports betting community.",
        'sports': ['Premier League', 'NPFL', 'Champions League'],
        'population': '1+ million',
    },
    {
        'path': 'countries/nigeria/warri',
        'city': 'Warri', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa'],
        'about': "Warri, located in Delta State, is an important oil-producing city with a vibrant sports culture. Football is the dominant betting market, with strong interest in both Nigerian and European leagues.",
        'sports': ['Premier League', 'NPFL', 'Champions League', 'La Liga'],
        'population': '600,000+',
    },
    {
        'path': 'countries/nigeria/jos',
        'city': 'Jos', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa'],
        'about': "Jos, the Plateau State capital, sits on Nigeria's central plateau and has a growing sports betting market driven by its young and educated population.",
        'sports': ['Premier League', 'NPFL', 'Champions League', 'AFCON'],
        'population': '900,000+',
    },
    {
        'path': 'countries/nigeria/aba',
        'city': 'Aba', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa'],
        'about': "Aba, the industrial hub of Abia State, is known as Nigeria's commercial city of the east. Its large trader population participates actively in the mobile sports betting market.",
        'sports': ['Premier League', 'NPFL (Aba FC)', 'Champions League'],
        'population': '1+ million',
    },
    {
        'path': 'countries/nigeria/ilorin',
        'city': 'Ilorin', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa'],
        'about': "Ilorin, the Kwara State capital, is an educational hub and one of Nigeria's fastest growing cities. Its large student and young professional population makes it an active betting market.",
        'sports': ['Premier League', 'NPFL', 'Champions League', 'AFCON'],
        'population': '700,000+',
    },
    {
        'path': 'countries/nigeria/owerri',
        'city': 'Owerri', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa'],
        'about': "Owerri, the Imo State capital, is an important commercial and educational city in South-East Nigeria with a passionate sports betting culture.",
        'sports': ['Premier League', 'NPFL', 'Champions League'],
        'population': '600,000+',
    },
    {
        'path': 'countries/nigeria/calabar',
        'city': 'Calabar', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa'],
        'about': "Calabar, the Cross River State capital and festival city of Nigeria, has a vibrant entertainment culture that includes strong sports betting activity among its educated population.",
        'sports': ['Premier League', 'NPFL', 'Champions League', 'AFCON'],
        'population': '400,000+',
    },
    {
        'path': 'countries/nigeria/uyo',
        'city': 'Uyo', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa'],
        'about': "Uyo, the Akwa Ibom State capital, is one of Nigeria's fastest growing cities, driven by oil wealth. It has a young and tech-savvy population that is very active in mobile sports betting.",
        'sports': ['Premier League', 'NPFL', 'Champions League'],
        'population': '500,000+',
    },
    {
        'path': 'countries/nigeria/abeokuta',
        'city': 'Abeokuta', 'country': 'Nigeria', 'code': 'NG', 'flag': '🇳🇬',
        'currency': 'NGN', 'symbol': '₦', 'regulator': 'NLRC (National Lottery Regulatory Commission)',
        'payments': ['OPay', 'PalmPay', 'Bank Transfer', 'Visa'],
        'about': "Abeokuta, the Ogun State capital and Rock City, is an important commercial city near Lagos with a growing sports betting market fuelled by proximity to the commercial capital.",
        'sports': ['Premier League', 'NPFL', 'Champions League', 'La Liga'],
        'population': '600,000+',
    },

    # ── KENYA ────────────────────────────────────────────────────────────────
    {
        'path': 'countries/kenya/nairobi',
        'city': 'Nairobi', 'country': 'Kenya', 'code': 'KE', 'flag': '🇰🇪',
        'currency': 'KES', 'symbol': 'KSh', 'regulator': 'BCLB (Betting Control and Licensing Board)',
        'payments': ['M-Pesa', 'Airtel Money', 'Visa', 'Mastercard'],
        'about': "Nairobi is Kenya's capital and East Africa's major technology hub. The city has one of the highest mobile internet penetration rates in Africa, making it a premier market for mobile sports betting. M-Pesa is the dominant payment method.",
        'sports': ['Premier League', 'Kenyan Premier League', 'Champions League', 'AFCON', 'Rugby'],
        'population': '4.5+ million',
    },
    {
        'path': 'countries/kenya/mombasa',
        'city': 'Mombasa', 'country': 'Kenya', 'code': 'KE', 'flag': '🇰🇪',
        'currency': 'KES', 'symbol': 'KSh', 'regulator': 'BCLB (Betting Control and Licensing Board)',
        'payments': ['M-Pesa', 'Airtel Money', 'Visa', 'Mastercard'],
        'about': "Mombasa is Kenya's coastal city and second largest urban centre. As a major port and tourist destination, Mombasa has a diverse population of active sports bettors who primarily use M-Pesa for deposits and withdrawals.",
        'sports': ['Premier League', 'Kenyan Premier League', 'Champions League', 'AFCON'],
        'population': '1.2+ million',
    },
    {
        'path': 'countries/kenya/kisumu',
        'city': 'Kisumu', 'country': 'Kenya', 'code': 'KE', 'flag': '🇰🇪',
        'currency': 'KES', 'symbol': 'KSh', 'regulator': 'BCLB (Betting Control and Licensing Board)',
        'payments': ['M-Pesa', 'Airtel Money', 'Visa'],
        'about': "Kisumu, on the shores of Lake Victoria, is Kenya's third largest city and the commercial hub of Western Kenya. Its large and growing young population is very active in sports betting, especially football.",
        'sports': ['Premier League', 'Kenyan Premier League', 'Champions League', 'AFCON'],
        'population': '400,000+',
    },
    {
        'path': 'countries/kenya/nakuru',
        'city': 'Nakuru', 'country': 'Kenya', 'code': 'KE', 'flag': '🇰🇪',
        'currency': 'KES', 'symbol': 'KSh', 'regulator': 'BCLB (Betting Control and Licensing Board)',
        'payments': ['M-Pesa', 'Airtel Money', 'Visa'],
        'about': "Nakuru, in Kenya's Rift Valley, is one of the country's fastest growing cities and an important agricultural and commercial hub. Sports betting is a popular leisure activity among its large working population.",
        'sports': ['Premier League', 'Kenyan Premier League', 'Champions League'],
        'population': '500,000+',
    },
    {
        'path': 'countries/kenya/eldoret',
        'city': 'Eldoret', 'country': 'Kenya', 'code': 'KE', 'flag': '🇰🇪',
        'currency': 'KES', 'symbol': 'KSh', 'regulator': 'BCLB (Betting Control and Licensing Board)',
        'payments': ['M-Pesa', 'Airtel Money', 'Visa'],
        'about': "Eldoret, Kenya's athletics capital and home to world-record marathon runners, is a rapidly growing city with a passionate sports culture extending to football and sports betting.",
        'sports': ['Athletics', 'Premier League', 'Kenyan Premier League', 'Champions League'],
        'population': '500,000+',
    },
    {
        'path': 'countries/kenya/thika',
        'city': 'Thika', 'country': 'Kenya', 'code': 'KE', 'flag': '🇰🇪',
        'currency': 'KES', 'symbol': 'KSh', 'regulator': 'BCLB (Betting Control and Licensing Board)',
        'payments': ['M-Pesa', 'Airtel Money', 'Visa'],
        'about': "Thika, located just north of Nairobi, is an important industrial town with a large working population. As a satellite city of Nairobi, Thika bettors have access to all major licensed bookmakers.",
        'sports': ['Premier League', 'Kenyan Premier League', 'Champions League'],
        'population': '200,000+',
    },
    {
        'path': 'countries/kenya/malindi',
        'city': 'Malindi', 'country': 'Kenya', 'code': 'KE', 'flag': '🇰🇪',
        'currency': 'KES', 'symbol': 'KSh', 'regulator': 'BCLB (Betting Control and Licensing Board)',
        'payments': ['M-Pesa', 'Airtel Money', 'Visa'],
        'about': "Malindi, Kenya's coastal resort town, has a growing sports betting community alongside its tourism economy. M-Pesa makes it easy for bettors to deposit and withdraw at any licensed bookmaker.",
        'sports': ['Premier League', 'Kenyan Premier League', 'Champions League'],
        'population': '150,000+',
    },
    {
        'path': 'countries/kenya/kitale',
        'city': 'Kitale', 'country': 'Kenya', 'code': 'KE', 'flag': '🇰🇪',
        'currency': 'KES', 'symbol': 'KSh', 'regulator': 'BCLB (Betting Control and Licensing Board)',
        'payments': ['M-Pesa', 'Airtel Money', 'Visa'],
        'about': "Kitale, in Kenya's Trans-Nzoia County, is an agricultural town with a growing mobile betting market. Its young population actively participates in football betting via M-Pesa.",
        'sports': ['Premier League', 'Kenyan Premier League', 'Champions League'],
        'population': '150,000+',
    },
    {
        'path': 'countries/kenya/nyeri',
        'city': 'Nyeri', 'country': 'Kenya', 'code': 'KE', 'flag': '🇰🇪',
        'currency': 'KES', 'symbol': 'KSh', 'regulator': 'BCLB (Betting Control and Licensing Board)',
        'payments': ['M-Pesa', 'Airtel Money', 'Visa'],
        'about': "Nyeri, located in the Mt. Kenya region, is an important administrative and commercial centre in Central Kenya. Its residents are among Kenya's most active mobile money users, making mobile betting highly accessible.",
        'sports': ['Premier League', 'Kenyan Premier League', 'Champions League', 'Rugby'],
        'population': '120,000+',
    },

    # ── GHANA ─────────────────────────────────────────────────────────────────
    {
        'path': 'countries/ghana/accra',
        'city': 'Accra', 'country': 'Ghana', 'code': 'GH', 'flag': '🇬🇭',
        'currency': 'GHS', 'symbol': 'GH₵', 'regulator': 'GCA (Ghana Gaming Commission)',
        'payments': ['MTN MoMo', 'Vodafone Cash', 'AirtelTigo', 'Visa', 'Mastercard'],
        'about': "Accra is Ghana's vibrant capital city and the beating heart of West African sports culture. With high smartphone penetration and widely available mobile money via MTN MoMo and Vodafone Cash, Accra is Ghana's premier sports betting market.",
        'sports': ['Premier League', 'Ghana Premier League', 'Champions League', 'AFCON', 'Black Stars'],
        'population': '2.5+ million',
    },
    {
        'path': 'countries/ghana/kumasi',
        'city': 'Kumasi', 'country': 'Ghana', 'code': 'GH', 'flag': '🇬🇭',
        'currency': 'GHS', 'symbol': 'GH₵', 'regulator': 'GCA (Ghana Gaming Commission)',
        'payments': ['MTN MoMo', 'Vodafone Cash', 'AirtelTigo', 'Visa'],
        'about': "Kumasi, the Ashanti capital and Ghana's second largest city, is home to one of Africa's most passionate football fanbases. Asante Kotoko's supporters are among the most loyal in African football, driving strong local betting interest.",
        'sports': ['Ghana Premier League (Asante Kotoko)', 'Premier League', 'Champions League', 'AFCON'],
        'population': '3+ million',
    },
    {
        'path': 'countries/ghana/tamale',
        'city': 'Tamale', 'country': 'Ghana', 'code': 'GH', 'flag': '🇬🇭',
        'currency': 'GHS', 'symbol': 'GH₵', 'regulator': 'GCA (Ghana Gaming Commission)',
        'payments': ['MTN MoMo', 'Vodafone Cash', 'AirtelTigo', 'Visa'],
        'about': "Tamale, the capital of Ghana's Northern Region, is the country's third largest city and a rapidly developing sports betting market. Football is extremely popular among its large and young population.",
        'sports': ['Premier League', 'Ghana Premier League', 'Champions League', 'AFCON'],
        'population': '600,000+',
    },
    {
        'path': 'countries/ghana/sekondi-takoradi',
        'city': 'Sekondi-Takoradi', 'country': 'Ghana', 'code': 'GH', 'flag': '🇬🇭',
        'currency': 'GHS', 'symbol': 'GH₵', 'regulator': 'GCA (Ghana Gaming Commission)',
        'payments': ['MTN MoMo', 'Vodafone Cash', 'AirtelTigo', 'Visa'],
        'about': "Sekondi-Takoradi, Ghana's oil capital and western port city, has strong economic activity and high incomes driving active participation in sports betting. The city has an established football culture.",
        'sports': ['Premier League', 'Ghana Premier League', 'Champions League'],
        'population': '400,000+',
    },
    {
        'path': 'countries/ghana/cape-coast',
        'city': 'Cape Coast', 'country': 'Ghana', 'code': 'GH', 'flag': '🇬🇭',
        'currency': 'GHS', 'symbol': 'GH₵', 'regulator': 'GCA (Ghana Gaming Commission)',
        'payments': ['MTN MoMo', 'Vodafone Cash', 'AirtelTigo', 'Visa'],
        'about': "Cape Coast, Ghana's historical coastal city and home to one of Africa's most prestigious universities, has a strong student betting community. The University of Cape Coast drives significant youth engagement in sports betting.",
        'sports': ['Premier League', 'Ghana Premier League', 'Champions League', 'AFCON'],
        'population': '200,000+',
    },
    {
        'path': 'countries/ghana/ho',
        'city': 'Ho', 'country': 'Ghana', 'code': 'GH', 'flag': '🇬🇭',
        'currency': 'GHS', 'symbol': 'GH₵', 'regulator': 'GCA (Ghana Gaming Commission)',
        'payments': ['MTN MoMo', 'Vodafone Cash', 'AirtelTigo', 'Visa'],
        'about': "Ho, the Volta Region capital, is a growing commercial and educational city in eastern Ghana. Its young population and improving mobile infrastructure are driving steady growth in the sports betting market.",
        'sports': ['Premier League', 'Ghana Premier League', 'Champions League'],
        'population': '180,000+',
    },

    # ── SOUTH AFRICA ─────────────────────────────────────────────────────────
    {
        'path': 'countries/south-africa/johannesburg',
        'city': 'Johannesburg', 'country': 'South Africa', 'code': 'ZA', 'flag': '🇿🇦',
        'currency': 'ZAR', 'symbol': 'R', 'regulator': 'WCGRB (Western Cape Gambling and Racing Board)',
        'payments': ['FNB', 'Nedbank', 'Standard Bank', 'Capitec', 'Visa', 'Mastercard'],
        'about': "Johannesburg is South Africa's economic capital and Africa's wealthiest city. The betting market here is the most regulated and sophisticated on the continent, with strong horse racing, football, and rugby betting cultures.",
        'sports': ['Premier League', 'PSL (Kaizer Chiefs, Orlando Pirates)', 'Rugby', 'Horse Racing', 'Cricket'],
        'population': '5.5+ million',
    },
    {
        'path': 'countries/south-africa/cape-town',
        'city': 'Cape Town', 'country': 'South Africa', 'code': 'ZA', 'flag': '🇿🇦',
        'currency': 'ZAR', 'symbol': 'R', 'regulator': 'WCGRB (Western Cape Gambling and Racing Board)',
        'payments': ['FNB', 'Nedbank', 'Standard Bank', 'Capitec', 'Visa', 'Mastercard'],
        'about': "Cape Town is South Africa's legislative capital and a world-class city with a thriving sports culture. The Cape is particularly famous for its rugby and cricket traditions alongside a strong Premier League following.",
        'sports': ['Premier League', 'PSL', 'Rugby (Stormers)', 'Cricket', 'Horse Racing'],
        'population': '4.5+ million',
    },
    {
        'path': 'countries/south-africa/durban',
        'city': 'Durban', 'country': 'South Africa', 'code': 'ZA', 'flag': '🇿🇦',
        'currency': 'ZAR', 'symbol': 'R', 'regulator': 'WCGRB (Western Cape Gambling and Racing Board)',
        'payments': ['FNB', 'Nedbank', 'Standard Bank', 'Capitec', 'Visa', 'Mastercard'],
        'about': "Durban, KwaZulu-Natal's coastal city, has a rich horse racing tradition as home to the Durban July — South Africa's most prestigious race. Football and cricket also drive strong betting volumes.",
        'sports': ['Horse Racing (Durban July)', 'Premier League', 'PSL', 'Cricket', 'Rugby'],
        'population': '3.5+ million',
    },
    {
        'path': 'countries/south-africa/pretoria',
        'city': 'Pretoria', 'country': 'South Africa', 'code': 'ZA', 'flag': '🇿🇦',
        'currency': 'ZAR', 'symbol': 'R', 'regulator': 'WCGRB (Western Cape Gambling and Racing Board)',
        'payments': ['FNB', 'Nedbank', 'Standard Bank', 'Capitec', 'Visa', 'Mastercard'],
        'about': "Pretoria, South Africa's administrative capital, is home to a large government workforce and student population. The city has a strong rugby and football culture with active participation in licensed sports betting.",
        'sports': ['Premier League', 'PSL', 'Rugby', 'Cricket', 'Horse Racing'],
        'population': '2.5+ million',
    },
    {
        'path': 'countries/south-africa/port-elizabeth',
        'city': 'Port Elizabeth', 'country': 'South Africa', 'code': 'ZA', 'flag': '🇿🇦',
        'currency': 'ZAR', 'symbol': 'R', 'regulator': 'WCGRB (Western Cape Gambling and Racing Board)',
        'payments': ['FNB', 'Nedbank', 'Standard Bank', 'Visa', 'Mastercard'],
        'about': "Port Elizabeth (Gqeberha) in the Eastern Cape is an important industrial and commercial city with a strong cricket and football culture. Its bettors have access to all major WCGRB-licensed bookmakers.",
        'sports': ['Premier League', 'PSL', 'Cricket', 'Rugby'],
        'population': '1.5+ million',
    },
    {
        'path': 'countries/south-africa/bloemfontein',
        'city': 'Bloemfontein', 'country': 'South Africa', 'code': 'ZA', 'flag': '🇿🇦',
        'currency': 'ZAR', 'symbol': 'R', 'regulator': 'WCGRB (Western Cape Gambling and Racing Board)',
        'payments': ['FNB', 'Nedbank', 'Standard Bank', 'Visa', 'Mastercard'],
        'about': "Bloemfontein, South Africa's judicial capital, is the Free State's major city and home to one of the country's most passionate rugby fanbases. Free State Cheetahs supporters are major participants in the local betting market.",
        'sports': ['Rugby (Free State Cheetahs)', 'Premier League', 'PSL', 'Cricket'],
        'population': '800,000+',
    },

    # ── TANZANIA ──────────────────────────────────────────────────────────────
    {
        'path': 'countries/tanzania/dar-es-salaam',
        'city': 'Dar es Salaam', 'country': 'Tanzania', 'code': 'TZ', 'flag': '🇹🇿',
        'currency': 'TZS', 'symbol': 'TSh', 'regulator': 'GBT (Gaming Board of Tanzania)',
        'payments': ['M-Pesa', 'Airtel Money', 'Tigo Pesa', 'Halopesa', 'Visa'],
        'about': "Dar es Salaam is Tanzania's largest city and economic capital. With a population of over 6 million and growing mobile money adoption, it is the dominant sports betting market in Tanzania. Football is king, with strong interest in the English Premier League and local Tanzanian Premier League.",
        'sports': ['Premier League', 'Tanzanian Premier League', 'Champions League', 'AFCON'],
        'population': '6+ million',
    },
    {
        'path': 'countries/tanzania/arusha',
        'city': 'Arusha', 'country': 'Tanzania', 'code': 'TZ', 'flag': '🇹🇿',
        'currency': 'TZS', 'symbol': 'TSh', 'regulator': 'GBT (Gaming Board of Tanzania)',
        'payments': ['M-Pesa', 'Airtel Money', 'Tigo Pesa', 'Visa'],
        'about': "Arusha, Tanzania's tourism hub and home to the African Union Court, is a rapidly growing city with high smartphone penetration. Its diverse population of local workers and regional professionals makes it an active betting market.",
        'sports': ['Premier League', 'Tanzanian Premier League', 'Champions League'],
        'population': '700,000+',
    },
    {
        'path': 'countries/tanzania/mwanza',
        'city': 'Mwanza', 'country': 'Tanzania', 'code': 'TZ', 'flag': '🇹🇿',
        'currency': 'TZS', 'symbol': 'TSh', 'regulator': 'GBT (Gaming Board of Tanzania)',
        'payments': ['M-Pesa', 'Airtel Money', 'Tigo Pesa', 'Visa'],
        'about': "Mwanza, on the southern shores of Lake Victoria, is Tanzania's second largest city and an important fishing and trading hub. Its large youth population is very active in mobile sports betting.",
        'sports': ['Premier League', 'Tanzanian Premier League', 'Champions League'],
        'population': '1.2+ million',
    },
    {
        'path': 'countries/tanzania/dodoma',
        'city': 'Dodoma', 'country': 'Tanzania', 'code': 'TZ', 'flag': '🇹🇿',
        'currency': 'TZS', 'symbol': 'TSh', 'regulator': 'GBT (Gaming Board of Tanzania)',
        'payments': ['M-Pesa', 'Airtel Money', 'Tigo Pesa', 'Visa'],
        'about': "Dodoma, Tanzania's capital city, is a growing administrative centre with an expanding young population. Sports betting is a popular leisure activity among government workers and students in the city.",
        'sports': ['Premier League', 'Tanzanian Premier League', 'Champions League'],
        'population': '400,000+',
    },
    {
        'path': 'countries/tanzania/moshi',
        'city': 'Moshi', 'country': 'Tanzania', 'code': 'TZ', 'flag': '🇹🇿',
        'currency': 'TZS', 'symbol': 'TSh', 'regulator': 'GBT (Gaming Board of Tanzania)',
        'payments': ['M-Pesa', 'Airtel Money', 'Tigo Pesa', 'Visa'],
        'about': "Moshi, at the foot of Mount Kilimanjaro, is a commercial and tourist hub in the Kilimanjaro region. It has a young and educated population that participates actively in mobile sports betting.",
        'sports': ['Premier League', 'Tanzanian Premier League', 'Champions League'],
        'population': '200,000+',
    },
    {
        'path': 'countries/tanzania/zanzibar',
        'city': 'Zanzibar City', 'country': 'Tanzania', 'code': 'TZ', 'flag': '🇹🇿',
        'currency': 'TZS', 'symbol': 'TSh', 'regulator': 'GBT (Gaming Board of Tanzania)',
        'payments': ['M-Pesa', 'Airtel Money', 'Tigo Pesa', 'Visa'],
        'about': "Zanzibar City, the historical capital of the Zanzibar archipelago, has a growing sports betting market driven by its young coastal population. Mobile money is the primary payment method for bettors here.",
        'sports': ['Premier League', 'Tanzanian Premier League', 'Champions League'],
        'population': '500,000+',
    },

    # ── UGANDA ────────────────────────────────────────────────────────────────
    {
        'path': 'countries/uganda/kampala',
        'city': 'Kampala', 'country': 'Uganda', 'code': 'UG', 'flag': '🇺🇬',
        'currency': 'UGX', 'symbol': 'USh', 'regulator': 'NLB (National Lotteries Board)',
        'payments': ['MTN MoMo', 'Airtel Money', 'Visa', 'Mastercard'],
        'about': "Kampala is Uganda's capital city and East Africa's fastest growing urban centre. With a young population of over 3 million, Kampala has the most vibrant sports betting scene in Uganda. MTN MoMo is the dominant payment method.",
        'sports': ['Premier League', 'Uganda Premier League', 'Champions League', 'AFCON'],
        'population': '3.5+ million',
    },
    {
        'path': 'countries/uganda/gulu',
        'city': 'Gulu', 'country': 'Uganda', 'code': 'UG', 'flag': '🇺🇬',
        'currency': 'UGX', 'symbol': 'USh', 'regulator': 'NLB (National Lotteries Board)',
        'payments': ['MTN MoMo', 'Airtel Money', 'Visa'],
        'about': "Gulu is northern Uganda's largest city and an important commercial hub. Following a period of post-conflict recovery, Gulu has seen rapid economic growth and a thriving youth sports betting market.",
        'sports': ['Premier League', 'Uganda Premier League', 'Champions League'],
        'population': '350,000+',
    },
    {
        'path': 'countries/uganda/mbarara',
        'city': 'Mbarara', 'country': 'Uganda', 'code': 'UG', 'flag': '🇺🇬',
        'currency': 'UGX', 'symbol': 'USh', 'regulator': 'NLB (National Lotteries Board)',
        'payments': ['MTN MoMo', 'Airtel Money', 'Visa'],
        'about': "Mbarara, Uganda's second largest city, is an important commercial and educational centre in the southwest. Its growing student and professional population makes it an active mobile betting market.",
        'sports': ['Premier League', 'Uganda Premier League', 'Champions League'],
        'population': '300,000+',
    },
    {
        'path': 'countries/uganda/jinja',
        'city': 'Jinja', 'country': 'Uganda', 'code': 'UG', 'flag': '🇺🇬',
        'currency': 'UGX', 'symbol': 'USh', 'regulator': 'NLB (National Lotteries Board)',
        'payments': ['MTN MoMo', 'Airtel Money', 'Visa'],
        'about': "Jinja, at the source of the Nile River, is Uganda's major industrial city and an adventure tourism hub. Its residents are avid football bettors with access to all major NLB-licensed bookmakers.",
        'sports': ['Premier League', 'Uganda Premier League', 'Champions League'],
        'population': '200,000+',
    },

    # ── ETHIOPIA ──────────────────────────────────────────────────────────────
    {
        'path': 'countries/ethiopia/addis-ababa',
        'city': 'Addis Ababa', 'country': 'Ethiopia', 'code': 'ET', 'flag': '🇪🇹',
        'currency': 'ETB', 'symbol': 'Br', 'regulator': 'Lottery and Charitable Games Administration',
        'payments': ['Telebirr', 'CBE Birr', 'Visa', 'Mastercard'],
        'about': "Addis Ababa, Africa's diplomatic capital and Ethiopia's main city, has a rapidly growing sports betting market. The introduction of Telebirr mobile money has opened up betting to millions of Ethiopians in the city.",
        'sports': ['Premier League', 'Ethiopian Premier League', 'Champions League', 'AFCON'],
        'population': '5+ million',
    },
    {
        'path': 'countries/ethiopia/dire-dawa',
        'city': 'Dire Dawa', 'country': 'Ethiopia', 'code': 'ET', 'flag': '🇪🇹',
        'currency': 'ETB', 'symbol': 'Br', 'regulator': 'Lottery and Charitable Games Administration',
        'payments': ['Telebirr', 'CBE Birr', 'Visa'],
        'about': "Dire Dawa is Ethiopia's second largest city and an important commercial hub in the east. Its large young population is increasingly participating in mobile sports betting via Telebirr.",
        'sports': ['Premier League', 'Ethiopian Premier League', 'Champions League'],
        'population': '500,000+',
    },
    {
        'path': 'countries/ethiopia/hawassa',
        'city': 'Hawassa', 'country': 'Ethiopia', 'code': 'ET', 'flag': '🇪🇹',
        'currency': 'ETB', 'symbol': 'Br', 'regulator': 'Lottery and Charitable Games Administration',
        'payments': ['Telebirr', 'CBE Birr', 'Visa'],
        'about': "Hawassa, the southern Ethiopia capital on the shores of Lake Hawassa, is one of the country's fastest growing cities. Sports betting is growing in popularity among its educated and young population.",
        'sports': ['Premier League', 'Ethiopian Premier League', 'Champions League'],
        'population': '400,000+',
    },

    # ── IVORY COAST ───────────────────────────────────────────────────────────
    {
        'path': 'countries/ivory-coast/abidjan',
        'city': 'Abidjan', 'country': 'Ivory Coast', 'code': 'CI', 'flag': '🇨🇮',
        'currency': 'XOF', 'symbol': 'CFA', 'regulator': 'LONACI (Loterie Nationale de Côte d\'Ivoire)',
        'payments': ['MTN MoMo', 'Orange Money', 'Moov Money', 'Visa', 'Mastercard'],
        'about': "Abidjan, Ivory Coast's economic capital and West Africa's third largest city, is a sophisticated betting market. Football is the dominant sport, driven by the passionate Éléphants national team fanbase and strong French Ligue 1 following.",
        'sports': ['Ligue 1 (France)', 'Premier League', 'Ivorian Premier League', 'AFCON', 'Champions League'],
        'population': '5+ million',
    },
    {
        'path': 'countries/ivory-coast/bouake',
        'city': 'Bouaké', 'country': 'Ivory Coast', 'code': 'CI', 'flag': '🇨🇮',
        'currency': 'XOF', 'symbol': 'CFA', 'regulator': 'LONACI (Loterie Nationale de Côte d\'Ivoire)',
        'payments': ['MTN MoMo', 'Orange Money', 'Moov Money', 'Visa'],
        'about': "Bouaké, Ivory Coast's second largest city, is an important commercial and transport hub in the centre of the country. Its residents are active football bettors with strong interest in both local and European leagues.",
        'sports': ['Ligue 1 (France)', 'Premier League', 'Ivorian Premier League', 'AFCON'],
        'population': '700,000+',
    },

    # ── CAMEROON ──────────────────────────────────────────────────────────────
    {
        'path': 'countries/cameroon/douala',
        'city': 'Douala', 'country': 'Cameroon', 'code': 'CM', 'flag': '🇨🇲',
        'currency': 'XAF', 'symbol': 'CFA', 'regulator': 'Ministry of Finance Cameroon',
        'payments': ['MTN MoMo', 'Orange Money', 'Visa', 'Mastercard'],
        'about': "Douala is Cameroon's economic capital and the largest city in Central Africa. With a youthful and sports-passionate population, Douala has a large and growing sports betting market driven by football and the Indomitable Lions' performances.",
        'sports': ['Ligue 1 (France)', 'Premier League', 'Cameroon Elite One', 'AFCON', 'Champions League'],
        'population': '4+ million',
    },
    {
        'path': 'countries/cameroon/yaounde',
        'city': 'Yaoundé', 'country': 'Cameroon', 'code': 'CM', 'flag': '🇨🇲',
        'currency': 'XAF', 'symbol': 'CFA', 'regulator': 'Ministry of Finance Cameroon',
        'payments': ['MTN MoMo', 'Orange Money', 'Visa', 'Mastercard'],
        'about': "Yaoundé, Cameroon's political capital, hosted AFCON 2022 matches and has a football culture deeply tied to the national Indomitable Lions. The city's large government and student population is highly active in sports betting.",
        'sports': ['Ligue 1 (France)', 'Premier League', 'Cameroon Elite One', 'AFCON'],
        'population': '3.5+ million',
    },

    # ── SENEGAL ───────────────────────────────────────────────────────────────
    {
        'path': 'countries/senegal/dakar',
        'city': 'Dakar', 'country': 'Senegal', 'code': 'SN', 'flag': '🇸🇳',
        'currency': 'XOF', 'symbol': 'CFA', 'regulator': 'Direction Générale des Jeux et Paris Sportifs',
        'payments': ['Orange Money', 'Wave', 'Free Money', 'Visa', 'Mastercard'],
        'about': "Dakar, Senegal's vibrant capital, is West Africa's westernmost city and a growing sports betting market. Following the Lions of Teranga's AFCON 2022 victory, Senegalese football passion is at an all-time high, driving strong sports betting engagement.",
        'sports': ['Ligue 1 (France)', 'Premier League', 'Senegalese Premier League', 'AFCON', 'Champions League'],
        'population': '3.5+ million',
    },

    # ── RWANDA ────────────────────────────────────────────────────────────────
    {
        'path': 'countries/rwanda/kigali',
        'city': 'Kigali', 'country': 'Rwanda', 'code': 'RW', 'flag': '🇷🇼',
        'currency': 'RWF', 'symbol': 'RWF', 'regulator': 'RGA (Rwanda Gaming Authority)',
        'payments': ['MTN MoMo', 'Airtel Money', 'Visa', 'Mastercard'],
        'about': "Kigali is one of Africa's cleanest and most modern capitals, with extremely high smartphone penetration and digital payments adoption. Rwanda's tech-forward population makes Kigali one of East Africa's most sophisticated mobile betting markets.",
        'sports': ['Premier League', 'Rwanda Premier League', 'Champions League', 'AFCON'],
        'population': '1+ million',
    },

    # ── ZIMBABWE ──────────────────────────────────────────────────────────────
    {
        'path': 'countries/zimbabwe/harare',
        'city': 'Harare', 'country': 'Zimbabwe', 'code': 'ZW', 'flag': '🇿🇼',
        'currency': 'USD', 'symbol': '$', 'regulator': 'Lotteries and Gaming Board Zimbabwe',
        'payments': ['EcoCash', 'OneMoney', 'Visa', 'Mastercard'],
        'about': "Harare, Zimbabwe's capital, has a passionate football culture despite economic challenges. EcoCash mobile money has enabled millions of Zimbabweans to participate in sports betting. The Warriors national team and English football are the most popular betting markets.",
        'sports': ['Premier League', 'Zimbabwe Premier League', 'Champions League', 'AFCON'],
        'population': '2.5+ million',
    },
    {
        'path': 'countries/zimbabwe/bulawayo',
        'city': 'Bulawayo', 'country': 'Zimbabwe', 'code': 'ZW', 'flag': '🇿🇼',
        'currency': 'USD', 'symbol': '$', 'regulator': 'Lotteries and Gaming Board Zimbabwe',
        'payments': ['EcoCash', 'OneMoney', 'Visa', 'Mastercard'],
        'about': "Bulawayo, Zimbabwe's second city and the country's industrial hub, has a strong sporting culture with passion for football and cricket. EcoCash is the dominant payment method for bettors in the city.",
        'sports': ['Premier League', 'Zimbabwe Premier League', 'Cricket', 'AFCON'],
        'population': '700,000+',
    },

    # ── ZAMBIA ────────────────────────────────────────────────────────────────
    {
        'path': 'countries/zambia/lusaka',
        'city': 'Lusaka', 'country': 'Zambia', 'code': 'ZM', 'flag': '🇿🇲',
        'currency': 'ZMW', 'symbol': 'ZK', 'regulator': 'GLAZ (Gaming and Lotteries Act Zambia)',
        'payments': ['MTN MoMo', 'Airtel Money', 'Zamtel Kwacha', 'Visa', 'Mastercard'],
        'about': "Lusaka, Zambia's capital and largest city, is the centre of the country's sports betting activity. The Copper Queens' success and the Zambia national team's passionate fanbase drive strong football betting interest across the city.",
        'sports': ['Premier League', 'Zambia Super League', 'Champions League', 'AFCON'],
        'population': '3+ million',
    },
    {
        'path': 'countries/zambia/ndola',
        'city': 'Ndola', 'country': 'Zambia', 'code': 'ZM', 'flag': '🇿🇲',
        'currency': 'ZMW', 'symbol': 'ZK', 'regulator': 'GLAZ (Gaming and Lotteries Act Zambia)',
        'payments': ['MTN MoMo', 'Airtel Money', 'Visa', 'Mastercard'],
        'about': "Ndola, the capital of the Copperbelt Province, is Zambia's second largest city. As the centre of the copper mining industry, Ndola has high employment rates and an active sports betting market among its large working population.",
        'sports': ['Premier League', 'Zambia Super League', 'Champions League'],
        'population': '500,000+',
    },
    {
        'path': 'countries/zambia/livingstone',
        'city': 'Livingstone', 'country': 'Zambia', 'code': 'ZM', 'flag': '🇿🇲',
        'currency': 'ZMW', 'symbol': 'ZK', 'regulator': 'GLAZ (Gaming and Lotteries Act Zambia)',
        'payments': ['MTN MoMo', 'Airtel Money', 'Visa'],
        'about': "Livingstone, Zambia's tourist capital at Victoria Falls, has a diverse community of local residents and hospitality workers who are active participants in mobile sports betting.",
        'sports': ['Premier League', 'Zambia Super League', 'Champions League'],
        'population': '200,000+',
    },

    # ── EGYPT ─────────────────────────────────────────────────────────────────
    {
        'path': 'countries/egypt/cairo',
        'city': 'Cairo', 'country': 'Egypt', 'code': 'EG', 'flag': '🇪🇬',
        'currency': 'EGP', 'symbol': 'EGP', 'regulator': 'Egyptian Regulatory Authority',
        'payments': ['Vodafone Cash', 'Orange Money Egypt', 'Etisalat Cash', 'Visa', 'Mastercard'],
        'about': "Cairo is Africa's largest city and one of the Arab world's most important sports markets. Egyptian football has a massive following, with Al-Ahly and Zamalek among the most supported clubs in Africa. International bookmakers serve Cairo's large betting community.",
        'sports': ['Egyptian Premier League (Al-Ahly, Zamalek)', 'Champions League', 'Premier League', 'AFCON', 'Basketball'],
        'population': '20+ million',
    },
    {
        'path': 'countries/egypt/alexandria',
        'city': 'Alexandria', 'country': 'Egypt', 'code': 'EG', 'flag': '🇪🇬',
        'currency': 'EGP', 'symbol': 'EGP', 'regulator': 'Egyptian Regulatory Authority',
        'payments': ['Vodafone Cash', 'Orange Money Egypt', 'Visa', 'Mastercard'],
        'about': "Alexandria, Egypt's second city and Mediterranean port, has a proud sporting tradition and is home to many passionate football bettors. The city's vibrant youth culture drives strong engagement with online sports betting.",
        'sports': ['Egyptian Premier League', 'Champions League', 'Premier League', 'AFCON'],
        'population': '5+ million',
    },

    # ── MOROCCO ───────────────────────────────────────────────────────────────
    {
        'path': 'countries/morocco/casablanca',
        'city': 'Casablanca', 'country': 'Morocco', 'code': 'MA', 'flag': '🇲🇦',
        'currency': 'MAD', 'symbol': 'MAD', 'regulator': 'MDJS (Marocaine des Jeux et des Sports)',
        'payments': ['Maroc Telecom Money', 'Orange Money Morocco', 'CIH Bank', 'Visa', 'Mastercard'],
        'about': "Casablanca, Morocco's economic capital, is North Africa's most important financial hub and has a large, passionate sports betting community. Following Morocco's historic 2022 World Cup semifinal run, football excitement in Casablanca is at an all-time high.",
        'sports': ['Botola Pro (Wydad, Raja)', 'Ligue 1 (France)', 'Premier League', 'Champions League', 'AFCON'],
        'population': '4+ million',
    },
    {
        'path': 'countries/morocco/rabat',
        'city': 'Rabat', 'country': 'Morocco', 'code': 'MA', 'flag': '🇲🇦',
        'currency': 'MAD', 'symbol': 'MAD', 'regulator': 'MDJS (Marocaine des Jeux et des Sports)',
        'payments': ['Maroc Telecom Money', 'Orange Money Morocco', 'Visa', 'Mastercard'],
        'about': "Rabat, Morocco's political capital and a UNESCO World Heritage city, has a well-educated population with strong interest in European and African football. It is served by all MDJS-licensed bookmakers.",
        'sports': ['Botola Pro', 'Ligue 1 (France)', 'Premier League', 'Champions League'],
        'population': '1.8+ million',
    },
    {
        'path': 'countries/morocco/marrakech',
        'city': 'Marrakech', 'country': 'Morocco', 'code': 'MA', 'flag': '🇲🇦',
        'currency': 'MAD', 'symbol': 'MAD', 'regulator': 'MDJS (Marocaine des Jeux et des Sports)',
        'payments': ['Maroc Telecom Money', 'Orange Money Morocco', 'Visa', 'Mastercard'],
        'about': "Marrakech, Morocco's cultural capital and a major tourist destination, has a growing sports betting market. Its large youth population and improving digital infrastructure are driving steady growth in mobile betting activity.",
        'sports': ['Botola Pro', 'Ligue 1 (France)', 'Premier League', 'Champions League'],
        'population': '1+ million',
    },
    {
        'path': 'countries/morocco/fes',
        'city': 'Fès', 'country': 'Morocco', 'code': 'MA', 'flag': '🇲🇦',
        'currency': 'MAD', 'symbol': 'MAD', 'regulator': 'MDJS (Marocaine des Jeux et des Sports)',
        'payments': ['Maroc Telecom Money', 'Orange Money Morocco', 'Visa', 'Mastercard'],
        'about': "Fès, Morocco's historical and spiritual capital, is one of the world's oldest university cities. Its educated population has strong interest in football betting, particularly for European leagues and the Atlas Lions.",
        'sports': ['Botola Pro', 'Ligue 1 (France)', 'Premier League', 'AFCON'],
        'population': '1+ million',
    },

    # ── ANGOLA ────────────────────────────────────────────────────────────────
    {
        'path': 'countries/angola/luanda',
        'city': 'Luanda', 'country': 'Angola', 'code': 'AO', 'flag': '🇦🇴',
        'currency': 'AOA', 'symbol': 'Kz', 'regulator': 'IRSE (Instituto Regulador de Jogos de Angola)',
        'payments': ['Multicaixa', 'Unitel Money', 'Visa', 'Mastercard'],
        'about': "Luanda, Angola's oil-wealthy capital, is one of Africa's most expensive cities and has a growing middle class with strong interest in sports betting. Football dominates, with the Palancas Negras national team and European leagues driving betting volumes.",
        'sports': ['Girabola (Angola Premier League)', 'Premier League', 'Champions League', 'AFCON'],
        'population': '8+ million',
    },
    {
        'path': 'countries/angola/huambo',
        'city': 'Huambo', 'country': 'Angola', 'code': 'AO', 'flag': '🇦🇴',
        'currency': 'AOA', 'symbol': 'Kz', 'regulator': 'IRSE (Instituto Regulador de Jogos de Angola)',
        'payments': ['Multicaixa', 'Unitel Money', 'Visa'],
        'about': "Huambo, Angola's second largest city and the capital of the highlands, has a growing sports betting market. Football is the leading sport, with the city having produced several national team players.",
        'sports': ['Girabola', 'Premier League', 'Champions League', 'AFCON'],
        'population': '800,000+',
    },

    # ── DR CONGO ──────────────────────────────────────────────────────────────
    {
        'path': 'countries/dr-congo/kinshasa',
        'city': 'Kinshasa', 'country': 'DR Congo', 'code': 'CD', 'flag': '🇨🇩',
        'currency': 'CDF', 'symbol': 'CDF', 'regulator': 'CNJH (Commission Nationale des Jeux de Hasard)',
        'payments': ['M-Pesa', 'Airtel Money', 'Orange Money', 'Visa'],
        'about': "Kinshasa, Africa's third largest city, is a vibrant mega-city with a passionate football culture. The Leopards (DR Congo national team) have a massive fanbase, and football betting is extremely popular across the city's 15+ million residents.",
        'sports': ['LINAFOOT (DR Congo League)', 'Premier League', 'Ligue 1 (France)', 'Champions League', 'AFCON'],
        'population': '15+ million',
    },
    {
        'path': 'countries/dr-congo/lubumbashi',
        'city': 'Lubumbashi', 'country': 'DR Congo', 'code': 'CD', 'flag': '🇨🇩',
        'currency': 'CDF', 'symbol': 'CDF', 'regulator': 'CNJH (Commission Nationale des Jeux de Hasard)',
        'payments': ['M-Pesa', 'Airtel Money', 'Orange Money', 'Visa'],
        'about': "Lubumbashi, the Katanga Province capital and DRC's second largest city, is an important mining hub. It has a passionate football culture with TP Mazembe — one of Africa's most successful clubs — based here.",
        'sports': ['LINAFOOT (TP Mazembe)', 'Premier League', 'Champions League', 'AFCON'],
        'population': '2.5+ million',
    },

    # ── BOTSWANA ──────────────────────────────────────────────────────────────
    {
        'path': 'countries/botswana/gaborone',
        'city': 'Gaborone', 'country': 'Botswana', 'code': 'BW', 'flag': '🇧🇼',
        'currency': 'BWP', 'symbol': 'BWP', 'regulator': 'GCAB (Gambling Control Authority Botswana)',
        'payments': ['Orange Money', 'Smega', 'FNB', 'Barclays', 'Visa', 'Mastercard'],
        'about': "Gaborone, Botswana's capital, is one of Africa's fastest growing cities and has one of the continent's highest GDP per capita. The city's affluent and educated population participates actively in sports betting, especially football and rugby.",
        'sports': ['Premier League', 'Botswana Premier League', 'Rugby', 'AFCON'],
        'population': '500,000+',
    },

    # ── NAMIBIA ───────────────────────────────────────────────────────────────
    {
        'path': 'countries/namibia/windhoek',
        'city': 'Windhoek', 'country': 'Namibia', 'code': 'NA', 'flag': '🇳🇦',
        'currency': 'NAD', 'symbol': 'NAD', 'regulator': 'GBN (Gambling Board of Namibia)',
        'payments': ['FNB Namibia', 'Bank Windhoek', 'Standard Bank', 'Visa', 'Mastercard'],
        'about': "Windhoek, Namibia's capital, is a modern and well-organised city with a growing sports betting market. Football and rugby are the dominant betting sports, with both Namibia's local leagues and international competitions drawing strong interest.",
        'sports': ['Premier League', 'Namibia Premier League', 'Rugby', 'AFCON'],
        'population': '450,000+',
    },

    # ── SIERRA LEONE ─────────────────────────────────────────────────────────
    {
        'path': 'countries/sierra-leone/freetown',
        'city': 'Freetown', 'country': 'Sierra Leone', 'code': 'SL', 'flag': '🇸🇱',
        'currency': 'SLL', 'symbol': 'Le', 'regulator': 'National Lottery Authority Sierra Leone',
        'payments': ['Orange Money', 'Africell Money', 'Visa', 'Mastercard'],
        'about': "Freetown, Sierra Leone's capital, is a West African city with a rapidly growing sports betting market. Football is the nation's favourite sport, with the Leone Stars national team inspiring strong local betting engagement.",
        'sports': ['Premier League', 'Sierra Leone Premier League', 'Champions League', 'AFCON'],
        'population': '1+ million',
    },
    {
        'path': 'countries/sierra-leone/bo',
        'city': 'Bo', 'country': 'Sierra Leone', 'code': 'SL', 'flag': '🇸🇱',
        'currency': 'SLL', 'symbol': 'Le', 'regulator': 'National Lottery Authority Sierra Leone',
        'payments': ['Orange Money', 'Africell Money', 'Visa'],
        'about': "Bo is Sierra Leone's second city and the capital of the Southern Province. It has a large youth population that is very active in mobile sports betting, particularly football.",
        'sports': ['Premier League', 'Sierra Leone Premier League', 'Champions League'],
        'population': '200,000+',
    },

    # ── LIBERIA ───────────────────────────────────────────────────────────────
    {
        'path': 'countries/liberia/monrovia',
        'city': 'Monrovia', 'country': 'Liberia', 'code': 'LR', 'flag': '🇱🇷',
        'currency': 'LRD', 'symbol': '$', 'regulator': 'Casino Control Board Liberia',
        'payments': ['Orange Money', 'Lonestar Money', 'MTN MoMo', 'Visa'],
        'about': "Monrovia, Liberia's capital, is a growing West African city with strong football culture. The Lone Star national team has a passionate fanbase, and mobile sports betting is gaining popularity among the city's large youth population.",
        'sports': ['Premier League', 'Liberia First Division', 'Champions League', 'AFCON'],
        'population': '1.5+ million',
    },

    # ── MALAWI ────────────────────────────────────────────────────────────────
    {
        'path': 'countries/malawi/lilongwe',
        'city': 'Lilongwe', 'country': 'Malawi', 'code': 'MW', 'flag': '🇲🇼',
        'currency': 'MWK', 'symbol': 'MWK', 'regulator': 'GBM (Gaming Board of Malawi)',
        'payments': ['Airtel Money', 'TNM Mpamba', 'Visa', 'Mastercard'],
        'about': "Lilongwe, Malawi's capital and largest city, is the centre of the country's sports betting market. Football is the dominant sport, and mobile money via Airtel Money and TNM Mpamba has made sports betting accessible to Lilongwe's large young population.",
        'sports': ['Premier League', 'TNM Super League', 'Champions League', 'AFCON'],
        'population': '1.2+ million',
    },
    {
        'path': 'countries/malawi/blantyre',
        'city': 'Blantyre', 'country': 'Malawi', 'code': 'MW', 'flag': '🇲🇼',
        'currency': 'MWK', 'symbol': 'MWK', 'regulator': 'GBM (Gaming Board of Malawi)',
        'payments': ['Airtel Money', 'TNM Mpamba', 'Visa', 'Mastercard'],
        'about': "Blantyre, Malawi's commercial capital and second largest city, is home to major clubs like Nyasa Big Bullets. Its passionate football fanbase and growing mobile money adoption make it an important betting market.",
        'sports': ['TNM Super League (Nyasa Big Bullets)', 'Premier League', 'Champions League'],
        'population': '1+ million',
    },

    # ── MOZAMBIQUE ────────────────────────────────────────────────────────────
    {
        'path': 'countries/mozambique/maputo',
        'city': 'Maputo', 'country': 'Mozambique', 'code': 'MZ', 'flag': '🇲🇿',
        'currency': 'MZN', 'symbol': 'MT', 'regulator': 'GCMZ (Gaming Control Authority of Mozambique)',
        'payments': ['M-Pesa', 'Mkesh', 'e-Mola', 'Visa', 'Mastercard'],
        'about': "Maputo, Mozambique's coastal capital, is a vibrant city with Portuguese-African culture. Football is the national sport, with Mozambique's proximity to South Africa exposing bettors to both local and international leagues. M-Pesa is the leading payment method.",
        'sports': ['Premier League', 'Moçambola (Mozambique League)', 'Champions League', 'AFCON'],
        'population': '1.5+ million',
    },
    {
        'path': 'countries/mozambique/beira',
        'city': 'Beira', 'country': 'Mozambique', 'code': 'MZ', 'flag': '🇲🇿',
        'currency': 'MZN', 'symbol': 'Mt', 'regulator': 'GCMZ (Gaming Control Authority of Mozambique)',
        'payments': ['M-Pesa', 'Mkesh', 'e-Mola', 'Visa'],
        'about': "Beira, Mozambique's second largest city and Indian Ocean port, has a passionate sports community. Following the city's recovery from Cyclone Idai, its economy and digital services have grown significantly, supporting a developing betting market.",
        'sports': ['Premier League', 'Moçambola', 'Champions League'],
        'population': '600,000+',
    },
]


def build_page(city_data):
    city = city_data['city']
    country = city_data['country']
    code = city_data['code']
    flag = city_data['flag']
    currency = city_data['currency']
    symbol = city_data['symbol']
    regulator = city_data['regulator']
    payments = city_data['payments']
    about = city_data['about']
    sports = city_data['sports']
    path = city_data['path']

    # Depth from root (3 segments for countries/X/Y)
    depth = path.count('/')
    assets = '../' * (depth + 1)

    slug = path.split('/')[-1]
    country_slug = path.split('/')[1]
    city_slug = slug

    # 2026-08-09: country pages moved from countries/<slug>/ to best-bonus-in-<slug>/
    # (see generate_country_pages.py) — link straight to the new location.
    country_prefix = f'{assets}best-bonus-in-{country_slug}/'

    canonical = f'https://sifufinds.com/{path}/'
    hreflang = f'en-{code}'

    title = f'Betting Sites in {city}, {country} 2026 | SifuFinds'
    description = f'Best licensed betting sites in {city}, {country} 2026. Compare verified bonuses from {regulator} regulated bookmakers. {", ".join(payments[:2])} accepted. Updated daily.'
    keywords = f'betting sites {city.lower()}, {city.lower()} bookmakers 2026, sports betting {city.lower()}, best betting {city.lower()} {country.lower()}, online betting {city.lower()}'

    pay_chips = ''.join(f'<span class="pay-chip">{p}</span>' for p in payments)
    sports_list = ''.join(f'<li>{s}</li>' for s in sports)

    faq_items = [
        (f'Is sports betting legal in {city}?',
         f'Yes. Sports betting is legal in {city}, {country}, regulated by the <strong>{regulator}</strong>. All bookmakers on SifuFinds hold valid licences for the {country} market.'),
        (f'What are the best betting sites in {city}?',
         f'The best licensed {city} betting sites are listed above. All are regulated by {regulator} and accept local payment methods including {", ".join(payments[:2])}. Use the Highest Bonus filter to find the top current offer.'),
        (f'What payment methods are accepted in {city}?',
         f'Licensed betting sites in {city} accept {", ".join(payments)}. Mobile money is the most popular and fastest way to deposit and withdraw.'),
        (f'How do I start betting in {city}?',
         f'To start betting in {city}: (1) Choose a licensed bookmaker from the list above, (2) Register with your phone number, (3) Verify your identity if required by {regulator}, (4) Deposit via {payments[0]}, (5) Claim your welcome bonus and place your first bet. Always bet responsibly.'),
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

    breadcrumb_country = country_slug.replace('-', ' ').title()

    return f'''<!DOCTYPE html>
<!-- sifufinds.com/{path}/ — Betting Sites in {city} {country} -->
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
<link rel="alternate" hreflang="{hreflang}" href="{canonical}">
<link rel="alternate" hreflang="en" href="{canonical}">
<meta name="geo.region" content="{code}">
<meta name="geo.placename" content="{city}">

<meta property="og:type" content="website">
<meta property="og:site_name" content="SifuFinds">
<meta property="og:title" content="Betting Sites in {city} 2026 | SifuFinds">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="https://sifufinds.com/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_GB">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@sifufinds">
<meta name="twitter:title" content="Betting Sites in {city} 2026 | SifuFinds">
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
        {{"@type": "ListItem", "position": 2, "name": "Countries", "item": "https://sifufinds.com/countries/"}},
        {{"@type": "ListItem", "position": 3, "name": "{country} Bonus Sites", "item": "https://sifufinds.com/best-bonus-in-{country_slug}/"}},
        {{"@type": "ListItem", "position": 4, "name": "{city} Betting", "item": "{canonical}"}}
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
.reg-badge{{display:inline-block;background:#edf7f0;border:1px solid #c8e6c9;border-radius:6px;padding:5px 12px;font-size:12px;font-weight:700;color:#1a6b35;margin-bottom:10px}}
.pay-grid{{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}}
.pay-chip{{background:#f5f5f5;border:1px solid #e0e0e0;border-radius:5px;padding:4px 10px;font-size:12px;font-weight:500;color:#333}}
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
    <a href="{country_prefix}">{flag} {country}</a>
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
      <a class="nt" href="{assets}">⭐ Best Bonuses</a>
      <a class="nt" href="{assets}tips/">💡 Tips</a>
      <a class="nt" href="{assets}casino/">🎰 Casino</a>
      <a class="nt" href="{assets}odds/">📊 Live Odds<span class="lpulse" style="margin-left:4px"></span></a>
      <a class="nt on" href="{assets}countries/">🌍 Countries</a>
      <a class="nt" href="{assets}blog/">📰 Blog</a>
    </div>
  </div>
</nav>

<div id="hbrands" class="hbrands"></div>

<div class="hero"><div class="wrap">
  <h1>Betting Sites in {city}, {country} &middot; 2026</h1>
  <p>{about}</p>
  <div class="trust">
    <div class="tb">✅ Licensed &amp; Verified</div>
    <div class="tb">📱 Mobile-First</div>
    <div class="tb">🔄 Updated Daily</div>
    <div class="tb">💳 {payments[0]}</div>
  </div>
</div></div>

<div class="sec-bg"><div class="wrap">
  <div class="breadcrumb">
    <a href="{assets}">Home</a><span>›</span>
    <a href="{assets}countries/">Countries</a><span>›</span>
    <a href="{country_prefix}">{country}</a><span>›</span>
    {city}
  </div>

  <div class="adv">📢 <strong>Advertiser Disclosure:</strong> We earn commission from some bookmaker links. All bonuses verified. Check T&Cs. 18+.</div>

  <div class="cbox2">
    <h2>Is Betting Legal in {city}?</h2>
    <div class="reg-badge">✅ Regulated — {regulator}</div>
    <p>Yes. Sports betting is <strong>legal and regulated</strong> in {city}, {country}. The licensing authority is the <strong>{regulator}</strong>. All bookmakers on SifuFinds are fully licensed for the {country} market.</p>
  </div>

  <div class="sec-lbl" style="font-size:11px;font-weight:700;color:#aaa;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">LICENSED BOOKMAKERS · {city.upper()} · 2026</div>
  <h2 style="font-size:17px;font-weight:800;color:#111;margin-bottom:9px">Best Betting Sites in {city} — Verified 2026</h2>

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

  <div class="cbox2">
    <h2>Payment Methods in {city}</h2>
    <p>Accepted payment methods at licensed {city} betting sites:</p>
    <div class="pay-grid">{pay_chips}</div>
  </div>

  <div class="cbox2">
    <h2>Popular Sports &amp; Leagues in {city}</h2>
    <ul style="padding-left:18px;margin:0">
      {sports_list}
    </ul>
  </div>

  <div class="cbox2">
    <h2>FAQ — Betting in {city}</h2>
{faq_html}  </div>

  <div class="resp">⚠️ Gambling involves risk. Only bet what you can afford to lose. 18+ only.</div>
</div></div>

<div class="footer-bar">
  <strong style="color:#fff">SifuFinds</strong> — Africa's #1 Independent Betting Comparison<br>
  <a href="{assets}">Home</a> · <a href="{assets}countries/">Countries</a> · <a href="{country_prefix}">{country} Betting</a> · <a href="{assets}tips/">Tips</a> · <a href="{assets}blog/">Blog</a><br>
  © <span id="foot-yr"></span> SifuFinds. All rights reserved. 18+ only.
</div>

<div class="page-modal-bg" id="page-modal"><div class="page-modal"><button class="page-modal-close" onclick="closePage()">×</button><div class="pm" id="page-content"></div></div></div>

<script src="{assets}assets/shared.js?v=22"></script>
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
    skipped = 0

    for city_data in CITIES:
        path = city_data['path']
        out_dir = os.path.join(BASE, path)
        out_path = os.path.join(out_dir, 'index.html')

        # Skip if already exists (preserve hand-crafted pages like Lagos, Nairobi)
        if os.path.exists(out_path):
            skipped += 1
            print(f'  ⟳  Skipped (exists): {path}/index.html')
            continue

        os.makedirs(out_dir, exist_ok=True)
        html = build_page(city_data)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        created += 1
        print(f'  ✓  {path}/index.html')

    print(f'\n✅  {created} new city pages generated ({skipped} existing pages preserved).')


if __name__ == '__main__':
    main()
