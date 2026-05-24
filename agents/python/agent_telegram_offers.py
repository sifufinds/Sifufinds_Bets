"""
Telegram Brand Offers Agent — SifuFinds
Posts one brand offer per run to @sifufinds, rotating through all 19 bookmakers.
Uses the existing Bot Token (no Telethon needed for own channel).

Usage:
  python agent_telegram_offers.py            # next brand in rotation
  python agent_telegram_offers.py --brand Bet9ja  # specific brand
  python agent_telegram_offers.py --force    # ignore cooldown, post anyway
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
import requests

load_dotenv(Path(__file__).parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))
from utils.logger import log

# ── CONFIG ────────────────────────────────────────────────────────────────────

CHANNEL    = os.getenv("TELEGRAM_CHANNEL_USERNAME", "@sifufinds")
BOT_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
SITE_URL   = "https://sifufinds.com"
STATE_FILE = Path(__file__).parent / "offers_state.json"

# Minimum hours between posts of the SAME brand
BRAND_COOLDOWN_HOURS = 48

# ── BRANDS (full rotation — all 19 bookmakers) ────────────────────────────────

BRANDS = [
    {
        "name": "Bet9ja",
        "flag": "🇳🇬",
        "countries": ["Nigeria"],
        "welcome": "₦2,500 Free Bet on Signup + 170% ACCA Boost",
        "bonus_highlight": "No deposit needed",
        "promo_code": "9BONUS",
        "min_deposit": "₦100",
        "stars": 5,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC Licensed",
        "tag": "Nigeria's No.1 Licensed Bookmaker",
        "hashtags": "#Bet9ja #Nigeria #FreeBet #NLRC #NigerianBetting",
    },
    {
        "name": "Sportybet",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Uganda", "Tanzania"],
        "welcome": "150% Welcome Bonus – Up to ₦30,000",
        "bonus_highlight": "150% free bet gifts on qualifying deposits",
        "promo_code": None,
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC + BCLB Licensed",
        "tag": "Africa's Most Downloaded Betting App",
        "hashtags": "#Sportybet #Africa #BettingApp #FreeBet #SportsBetting",
    },
    {
        "name": "BetKing",
        "flag": "🇳🇬",
        "countries": ["Nigeria"],
        "welcome": "₦100 Free Bets + 10 Aviator Flights — No Deposit",
        "bonus_highlight": "Zero deposit required to claim",
        "promo_code": "BONUSKG",
        "min_deposit": "₦0",
        "stars": 5,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC Licensed",
        "tag": "KingMakers-Backed, No Deposit Bonus",
        "hashtags": "#BetKing #Nigeria #Aviator #NoDeposit #FreeBet",
    },
    {
        "name": "1xBet",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania", "Uganda", "Zambia"],
        "welcome": "300% First Deposit Bonus – Up to ₦1,200,000",
        "bonus_highlight": "Highest welcome bonus in Africa",
        "promo_code": "1BONUSNG",
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC + BCLB + Curaçao Licensed",
        "tag": "50+ Sports — Highest Bonus in Africa",
        "hashtags": "#1xBet #Africa #SportsBetting #300Bonus #FreeBet",
    },
    {
        "name": "Betway",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "South Africa", "Ghana", "Tanzania"],
        "welcome": "Up to ₦100,000 in Free Bets — First 7 Days",
        "bonus_highlight": "Free bets on every settled stake for 7 days",
        "promo_code": "WAYBON",
        "min_deposit": "₦1,000",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC + BCLB + NGBB Licensed",
        "tag": "International Brand Trusted Across 12 African Countries",
        "hashtags": "#Betway #Africa #FreeBets #Trusted #SportsBetting",
    },
    {
        "name": "Hollywoodbets",
        "flag": "🇿🇦",
        "countries": ["South Africa", "Kenya", "Uganda", "Tanzania"],
        "welcome": "R25 Free Bet on Registration — No Deposit",
        "bonus_highlight": "25 years of trust in South Africa",
        "promo_code": "HOLLYWOODBETS",
        "min_deposit": "R5",
        "stars": 5,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "Western Cape Gambling Board",
        "tag": "South Africa's Biggest Homegrown Bookmaker",
        "hashtags": "#Hollywoodbets #SouthAfrica #PSL #FreeBet #ZABetting",
    },
    {
        "name": "Betika",
        "flag": "🇰🇪",
        "countries": ["Kenya", "Tanzania", "Uganda", "Malawi", "Ghana"],
        "welcome": "Free Bet + Aviator Free Bets on Signup",
        "bonus_highlight": "Operator of the Year 2025 — 8M+ users",
        "promo_code": None,
        "min_deposit": "KSh 10",
        "stars": 5,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "BCLB Licensed (No. BK0000679)",
        "tag": "Operator of the Year 2025 — 8M Users",
        "hashtags": "#Betika #Kenya #KPL #Aviator #EastAfrica",
    },
    {
        "name": "SportPesa",
        "flag": "🇰🇪",
        "countries": ["Kenya", "Tanzania", "Uganda", "Rwanda"],
        "welcome": "300% Welcome Karibu Gift on First Deposit",
        "bonus_highlight": "Triple your first deposit as free bets",
        "promo_code": None,
        "min_deposit": "KSh 10",
        "stars": 5,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "BCLB Licensed",
        "tag": "Official Sponsor of the Kenya Premier League",
        "hashtags": "#SportPesa #Kenya #KPL #300Bonus #MegaJackpot",
    },
    {
        "name": "Melbet",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania", "Ethiopia"],
        "welcome": "200% First Deposit Bonus – Up to ₦480,000",
        "bonus_highlight": "150+ sports markets — most in Africa",
        "promo_code": "MBMAX",
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": False,
        "cashout": False,
        "licence": "NLRC + BCLB + Curaçao Licensed",
        "tag": "150+ Sports — Widest Market Range",
        "hashtags": "#Melbet #Africa #200Bonus #SportsBetting #Esports",
    },
    {
        "name": "MozzartBet",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Zimbabwe"],
        "welcome": "100% Bonus Up to ₦50,000 + 500 Aviator Free Bets",
        "bonus_highlight": "500 Aviator free bets included",
        "promo_code": None,
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC + BCLB Licensed",
        "tag": "100% Bonus + 500 Aviator Free Bets",
        "hashtags": "#MozzartBet #Aviator #Nigeria #Kenya #100Bonus",
    },
    {
        "name": "NairaBet",
        "flag": "🇳🇬",
        "countries": ["Nigeria"],
        "welcome": "Free Bet on First Deposit + Daily Free Bets",
        "bonus_highlight": "Nigeria's pioneer bookmaker since 2009",
        "promo_code": None,
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC Licensed",
        "tag": "Nigeria's Pioneer Bookmaker — Est. 2009",
        "hashtags": "#NairaBet #Nigeria #NLRC #FreeBet #DailyBonus",
    },
    {
        "name": "22Bet",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania"],
        "welcome": "100% First Deposit Bonus – Up to ₦207,500",
        "bonus_highlight": "Proven fast payouts, 35 sports",
        "promo_code": "BNSNG",
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC + BCLB + Curaçao Licensed",
        "tag": "100% Bonus — Reliable Fast Payouts",
        "hashtags": "#22Bet #Africa #FastPayout #100Bonus #SportsBetting",
    },
    {
        "name": "Betpawa",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Uganda", "Tanzania"],
        "welcome": "Weekly Jackpot — Win Millions from ₦50 Stake",
        "bonus_highlight": "Jackpot entry from just ₦50 / KSh 1 min stake",
        "promo_code": None,
        "min_deposit": "₦50",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": False,
        "licence": "NLRC + BCLB + Ghana GC Licensed",
        "tag": "Jackpot from ₦50 — Pan-African Operator",
        "hashtags": "#Betpawa #Jackpot #Africa #LowStake #WinBig",
    },
    {
        "name": "BetWinner",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania"],
        "welcome": "200% First Deposit Bonus – Up to ₦130,000",
        "bonus_highlight": "Easy 5x wagering requirement",
        "promo_code": "WBONUS1",
        "min_deposit": "₦400",
        "stars": 3,
        "instant_withdrawal": False,
        "cashout": True,
        "licence": "NLRC + BCLB + Curaçao Licensed",
        "tag": "200% Bonus — Easy 5x Wagering on 40+ Sports",
        "hashtags": "#BetWinner #200Bonus #Africa #SportsBetting #LiveBetting",
    },
    {
        "name": "Odibets",
        "flag": "🇰🇪",
        "countries": ["Kenya"],
        "welcome": "KSh 30 Free Bet on Registration — No Deposit",
        "bonus_highlight": "Min stake KSh 1 — most affordable in Kenya",
        "promo_code": None,
        "min_deposit": "KSh 10",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "BCLB Licensed",
        "tag": "Bet from KSh 10 — Kenya's Low-Stake Champion",
        "hashtags": "#Odibets #Kenya #MPesa #LowStake #KPL",
    },
    {
        "name": "Supabets",
        "flag": "🇿🇦",
        "countries": ["South Africa", "Zimbabwe", "Zambia"],
        "welcome": "R10 Free Bet on Registration",
        "bonus_highlight": "SuperBanker weekly cash bonuses",
        "promo_code": None,
        "min_deposit": "R5",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "Western Cape Gambling Board",
        "tag": "South Africa's Homegrown Underdog — Massive Jackpots",
        "hashtags": "#Supabets #SouthAfrica #PSL #Jackpot #Rugby",
    },
    {
        "name": "Bangbet",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya"],
        "welcome": "Deposit ₦50, Get ₦200 in Free Bets",
        "bonus_highlight": "Beginner-friendly low minimum stake",
        "promo_code": None,
        "min_deposit": "₦50",
        "stars": 3,
        "instant_withdrawal": True,
        "cashout": False,
        "licence": "NLRC + BCLB Licensed",
        "tag": "Low Minimum Stake — Great for New Bettors",
        "hashtags": "#Bangbet #Nigeria #Kenya #LowStake #FreeBet",
    },
    {
        "name": "HelaBet",
        "flag": "🇰🇪",
        "countries": ["Kenya"],
        "welcome": "100% Welcome Bonus – Up to KSh 5,000",
        "bonus_highlight": "Instant M-Pesa payouts",
        "promo_code": None,
        "min_deposit": "KSh 10",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "BCLB Licensed",
        "tag": "Licensed Kenyan Brand — Instant M-Pesa Payouts",
        "hashtags": "#HelaBet #Kenya #MPesa #KPL #FreeBet",
    },
    {
        "name": "Paripesa",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania"],
        "welcome": "200% First Deposit Bonus – Up to ₦200,000",
        "bonus_highlight": "50+ sports markets, live streaming",
        "promo_code": None,
        "min_deposit": "₦100",
        "stars": 4,
        "instant_withdrawal": True,
        "cashout": True,
        "licence": "NLRC + BCLB + Curaçao Licensed",
        "tag": "200% Bonus — 50+ Sports, Rising Fast in Africa",
        "hashtags": "#Paripesa #200Bonus #Africa #LiveBetting #SportsBetting",
    },
]

BRAND_NAMES = [b["name"] for b in BRANDS]


# ── STATE MANAGEMENT ──────────────────────────────────────────────────────────

def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_index": -1, "brand_last_posted": {}}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _next_brand(state: dict, force_name: str | None = None, force: bool = False) -> dict | None:
    now = datetime.now(timezone.utc)
    brand_last = state.get("brand_last_posted", {})

    if force_name:
        candidates = [b for b in BRANDS if b["name"].lower() == force_name.lower()]
        if not candidates:
            print(f"✗ Brand '{force_name}' not found. Options: {', '.join(BRAND_NAMES)}")
            return None
        return candidates[0]

    # Round-robin, respecting cooldown
    start = (state.get("last_index", -1) + 1) % len(BRANDS)
    for offset in range(len(BRANDS)):
        idx = (start + offset) % len(BRANDS)
        brand = BRANDS[idx]
        last_str = brand_last.get(brand["name"])
        if force or not last_str:
            state["last_index"] = idx
            return brand
        last_dt = datetime.fromisoformat(last_str)
        if (now - last_dt) >= timedelta(hours=BRAND_COOLDOWN_HOURS):
            state["last_index"] = idx
            return brand

    # All on cooldown — pick the one with the oldest post
    oldest = min(BRANDS, key=lambda b: brand_last.get(b["name"], "2000-01-01T00:00:00+00:00"))
    state["last_index"] = BRANDS.index(oldest)
    return oldest


# ── MESSAGE FORMATTER ─────────────────────────────────────────────────────────

def _stars(n: int) -> str:
    return "⭐" * n + "☆" * (5 - n)


def _yes_no(v: bool) -> str:
    return "✅" if v else "❌"


def _country_flags(countries: list[str]) -> str:
    flag_map = {
        "Nigeria": "🇳🇬", "Kenya": "🇰🇪", "South Africa": "🇿🇦",
        "Ghana": "🇬🇭", "Tanzania": "🇹🇿", "Uganda": "🇺🇬",
        "Zambia": "🇿🇲", "Zimbabwe": "🇿🇼", "Rwanda": "🇷🇼",
        "Malawi": "🇲🇼", "Ethiopia": "🇪🇹", "Namibia": "🇳🇦",
        "Mozambique": "🇲🇿", "Botswana": "🇧🇼", "Ivory Coast": "🇨🇮",
        "Cameroon": "🇨🇲",
    }
    return " ".join(flag_map.get(c, "🌍") for c in countries[:6])


def build_offer_message(brand: dict) -> str:
    code_line = f"🎟 Promo Code: <b>{brand['promo_code']}</b>\n" if brand.get("promo_code") else ""
    flags = _country_flags(brand["countries"])
    countries_str = " · ".join(brand["countries"][:5])
    if len(brand["countries"]) > 5:
        countries_str += f" +{len(brand['countries']) - 5} more"

    msg = (
        f"🔥 <b>TODAY'S TOP DEAL</b> — {brand['name']} {flags}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>{brand['welcome']}</b>\n"
        f"✨ {brand['bonus_highlight']}\n"
        f"{code_line}"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{_stars(brand['stars'])}  {brand['tag']}\n\n"
        f"💳 Min Deposit: {brand['min_deposit']}\n"
        f"⚡ Instant Withdrawal: {_yes_no(brand['instant_withdrawal'])}\n"
        f"💸 Cash-Out: {_yes_no(brand['cashout'])}\n"
        f"🛡 {brand['licence']}\n\n"
        f"🌍 Available in: {countries_str}\n\n"
        f"👉 Compare all bonuses → <a href=\"{SITE_URL}\">{SITE_URL}</a>\n"
        f"📲 Join our channel → @sifufinds\n\n"
        f"{brand['hashtags']} #SifuFinds #BettingBonus #AfricanBetting\n\n"
        f"<i>18+ | Bet Responsibly | T&Cs Apply</i>"
    )
    return msg


# ── TELEGRAM SENDER ───────────────────────────────────────────────────────────

async def _send_telethon(message: str) -> bool:
    """Primary sender — uses Telethon user session (same creds as all other agents)."""
    api_id_str = os.getenv("TELEGRAM_API_ID", "").strip()
    api_hash   = os.getenv("TELEGRAM_API_HASH", "").strip()
    session    = os.getenv("TELEGRAM_SESSION_STRING", "").strip()

    if not api_id_str or not api_hash or not session:
        return False

    try:
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        async with TelegramClient(StringSession(session), int(api_id_str), api_hash) as client:
            await client.send_message(CHANNEL, message, parse_mode="html")
        return True
    except Exception as e:
        print(f"✗ Telethon error: {e}")
        return False


def _send_bot_token(message: str) -> bool:
    """Fallback sender — uses Bot Token if Telethon creds not available."""
    if not BOT_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": CHANNEL,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }, timeout=15)
    ok = resp.status_code == 200
    if not ok:
        print(f"✗ Bot token error: {resp.json().get('description', resp.text[:200])}")
    return ok


def send_to_channel(message: str) -> bool:
    """Try Telethon first, fall back to bot token."""
    if asyncio.run(_send_telethon(message)):
        return True
    print("Telethon unavailable — trying bot token fallback...")
    return _send_bot_token(message)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def run(brand_name: str | None = None, force: bool = False) -> None:
    log("offers", "start", "running")
    state = _load_state()

    brand = _next_brand(state, force_name=brand_name, force=force)
    if not brand:
        sys.exit(1)

    print(f"📣 Posting offer for: {brand['name']}")
    message = build_offer_message(brand)

    if send_to_channel(message):
        now_iso = datetime.now(timezone.utc).isoformat()
        state.setdefault("brand_last_posted", {})[brand["name"]] = now_iso
        _save_state(state)
        log("offers", "post", "success", brand["name"])
        print(f"✓ Offer posted for {brand['name']}")
    else:
        log("offers", "post", "failed", brand["name"])
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Telegram Brand Offers")
    parser.add_argument("--brand", type=str, default=None, help="Post a specific brand offer")
    parser.add_argument("--force", action="store_true", help="Ignore cooldown and post anyway")
    args = parser.parse_args()
    run(brand_name=args.brand, force=args.force)
