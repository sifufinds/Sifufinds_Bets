import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "fd_554baa8cfac7cfe33ba92edfbc00f3e2a179ba179f44ada9")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# ── Site ──────────────────────────────────────────────────────────────────────
SITE_URL = "https://sifufinds.com"
BRAND_NAME = "SifuFinds"

# ── Content rotation — 9 slots repeat on a 3-day cycle ───────────────────────
CONTENT_SLOTS = [
    "Today's Best Betting Odds across African leagues",
    "Best Welcome Bonus in a featured African country",
    "Match Prediction and tips post",
    "Casino Jackpot or casino promo",
    "Betting education — How To guide",
    "Weekend Accumulator Picks",
    "Best Bookmaker in a featured country — monthly review",
    "Live Betting Guide",
    "Breaking news or trending match content",
]

# ── African country/bookmaker rotation ───────────────────────────────────────
COUNTRIES = [
    {"name": "Nigeria", "currency": "NGN", "bookmakers": ["Bet9ja", "BetKing", "1xBet", "Betway", "NairaBet"], "payment": "OPay, Flutterwave, bank transfer"},
    {"name": "Kenya", "currency": "KES", "bookmakers": ["Sportpesa", "Betway", "1xBet", "Odibets", "Shabiki"], "payment": "M-Pesa, Airtel Money"},
    {"name": "South Africa", "currency": "ZAR", "bookmakers": ["Hollywoodbets", "Supabets", "Betway", "10bet", "World Sports Betting"], "payment": "EFT, Capitec Pay"},
    {"name": "Ghana", "currency": "GHS", "bookmakers": ["Betway", "1xBet", "SportyBet", "BetPawa"], "payment": "MTN MoMo, Vodafone Cash"},
    {"name": "Tanzania", "currency": "TZS", "bookmakers": ["Betway", "1xBet", "Sportpesa", "Parimatch"], "payment": "M-Pesa, Tigo Pesa"},
    {"name": "Uganda", "currency": "UGX", "bookmakers": ["Betway", "1xBet", "FortunesBet", "Parimatch"], "payment": "MTN MoMo, Airtel Money"},
]

# ── Football API endpoints ─────────────────────────────────────────────────────
FOOTBALL_API_BASE = "https://api.footballdata.io/v1"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# ── Hashtag bank (rotate 25 per Instagram post) ───────────────────────────────
INSTAGRAM_HASHTAGS = [
    "#SifuFinds", "#AfricanBetting", "#SportsBetting", "#BettingTips", "#FootballBetting",
    "#FreeBets", "#BettingCommunity", "#NigerianBetting", "#KenyanBetting", "#SouthAfricaBetting",
    "#GhanaBetting", "#BettingAfrica", "#Bet9ja", "#Sportpesa", "#Hollywoodbets",
    "#BetKing", "#Betway", "#1xBet", "#Parimatch", "#AFCON",
    "#CAFChampionsLeague", "#NPFL", "#KPL", "#PSL", "#PremierLeague",
    "#LaLiga", "#WinBig", "#BettingLife", "#SmartBetting", "#AccumulatorBets",
    "#FootballTips", "#BettingPicks", "#OddsOn", "#iGamingAfrica", "#MobileBetting",
]
