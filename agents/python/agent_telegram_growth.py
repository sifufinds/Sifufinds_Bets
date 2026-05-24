"""
Telegram Channel Growth Agent — SifuFinds
Uses a Telethon USER account to post value content in African public Telegram
groups, growing the @sifufinds channel organically.

Strategy:
  - Posts tips/deals/odds in relevant public African sports & betting groups
  - Always leads with genuine value, then includes channel CTA
  - Tracks per-group posting history — 8-hour minimum between posts per group
  - Respects Telegram rate limits (short sleeps between group posts)
  - Groups sourced from GROWTH_GROUPS list + optional EXTRA_GROUPS env var

Setup (same credentials as agent3_social_telethon.py):
  TELEGRAM_API_ID       — from my.telegram.org
  TELEGRAM_API_HASH     — from my.telegram.org
  TELEGRAM_SESSION_STRING — saved session (run locally once to generate)
  TELEGRAM_PHONE        — your number with country code (first run only)

Usage:
  python agent_telegram_growth.py            # post to all due groups
  python agent_telegram_growth.py --dry-run  # preview messages only
  python agent_telegram_growth.py --limit 3  # post to at most 3 groups
"""
import argparse
import asyncio
import json
import os
import random
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))
from utils.logger import log

# ── CONFIG ─────────────────────────────────────────────────────────────────────

SITE_URL    = "https://sifufinds.com"
OWN_CHANNEL = "@sifufinds"

# Minimum hours to wait before re-posting in the same group
GROUP_COOLDOWN_HOURS = 8

# Max groups to post in per run (keeps runtime short for CI)
DEFAULT_RUN_LIMIT = 4

GROWTH_STATE_FILE = Path(__file__).parent / "growth_state.json"

# ── TARGET GROUPS ─────────────────────────────────────────────────────────────
# Public African sports / betting Telegram groups.
# Add more group usernames (without @) as you find relevant ones.
# The agent will attempt to join and post — groups that don't allow it are skipped.

GROWTH_GROUPS: list[dict] = [
    # ── Nigeria ──
    {"username": "bet9jatips",          "region": "Nigeria",       "topic": "betting"},
    {"username": "nigerianfootballfans","region": "Nigeria",       "topic": "football"},
    {"username": "npfl_fans",           "region": "Nigeria",       "topic": "football"},
    {"username": "nigerialivebet",      "region": "Nigeria",       "topic": "betting"},
    {"username": "naijabettingtips",    "region": "Nigeria",       "topic": "betting"},
    {"username": "africanfootballdaily","region": "Pan-Africa",    "topic": "football"},
    {"username": "bettingtipsafrica",   "region": "Pan-Africa",    "topic": "betting"},
    # ── Kenya ──
    {"username": "kenyabettingtips",    "region": "Kenya",         "topic": "betting"},
    {"username": "kplsoccer",           "region": "Kenya",         "topic": "football"},
    {"username": "sportpesatips",       "region": "Kenya",         "topic": "betting"},
    {"username": "eastafricasports",    "region": "East Africa",   "topic": "football"},
    # ── South Africa ──
    {"username": "pslsoccerfans",       "region": "South Africa",  "topic": "football"},
    {"username": "safootballtips",      "region": "South Africa",  "topic": "betting"},
    {"username": "hollywoodbets_tips",  "region": "South Africa",  "topic": "betting"},
    # ── Ghana ──
    {"username": "ghanasportsbetting",  "region": "Ghana",         "topic": "betting"},
    {"username": "gplghana",            "region": "Ghana",         "topic": "football"},
    # ── Pan-Africa ──
    {"username": "africansportsforum",  "region": "Pan-Africa",    "topic": "football"},
    {"username": "cafsoccernews",       "region": "Pan-Africa",    "topic": "football"},
    {"username": "africabettingcommunity","region": "Pan-Africa",  "topic": "betting"},
    {"username": "ibetchannel",         "region": "Pan-Africa",    "topic": "betting"},
]


# ── VALUE-FIRST POST TEMPLATES ─────────────────────────────────────────────────
# Posts lead with genuine value. CTA to join @sifufinds is natural, not spammy.

FOOTBALL_TEMPLATES = [
    (
        "⚽ AFRICAN FOOTBALL PICKS — {date}\n\n"
        "🔍 Our analysts have identified 3 high-value bets across African leagues today.\n\n"
        "🇳🇬 NPFL · 🇰🇪 KPL · 🇿🇦 PSL · 🌍 CAF\n\n"
        "Best odds comparison across Bet9ja, Betway, 1xBet & more 👇\n"
        "📲 {site_url}\n\n"
        "Follow {channel} for daily picks, odds alerts and free bets!\n\n"
        "#FootballTips #AfricanFootball #BettingTips #SifuFinds"
    ),
    (
        "🏆 {day} ACCUMULATOR IDEAS\n\n"
        "Building an ACCA for today's African matches?\n"
        "We've compared odds across 19 bookmakers so you get the best value.\n\n"
        "✅ Best ACCA boost: Bet9ja (170%) + BetKing\n"
        "✅ Lowest min stake: Betpawa (₦1 / KSh 1)\n\n"
        "Full picks & odds → {site_url}\n"
        "Join {channel} for instant updates 🔔\n\n"
        "#Accumulator #AfricanBetting #BettingTips #SifuFinds"
    ),
    (
        "📊 TODAY'S BEST VALUE BETS — {date}\n\n"
        "Our odds scanner just flagged over-priced markets on today's matches.\n\n"
        "🇳🇬 Nigerian Premier League\n"
        "🇰🇪 Kenya Premier League\n"
        "🌍 CAF Champions League qualifiers\n\n"
        "Real-time odds comparison: {site_url}\n"
        "Daily tips + free bet alerts → {channel}\n\n"
        "#ValueBets #OddsComparison #AfricanFootball #SifuFinds"
    ),
]

BONUS_TEMPLATES = [
    (
        "💰 FREE BETS AVAILABLE RIGHT NOW IN AFRICA\n\n"
        "Top offers this week:\n"
        "🔥 Bet9ja — ₦2,500 no-deposit free bet (Code: 9BONUS)\n"
        "🔥 1xBet — 300% first deposit up to ₦1.2M\n"
        "🔥 BetKing — ₦100 free + 10 Aviator flights (no deposit)\n"
        "🔥 Betway — up to ₦100,000 in free bets (7 days)\n\n"
        "Compare all 19 bookmakers → {site_url}\n"
        "Get alerts first → {channel}\n\n"
        "#FreeBets #BettingBonus #AfricanBetting #SifuFinds"
    ),
    (
        "🎁 NEW PLAYER BONUSES — DON'T MISS THESE\n\n"
        "Haven't signed up yet? Here's what you're leaving on the table:\n\n"
        "🇳🇬 Nigeria: Bet9ja, BetKing, Sportybet\n"
        "🇰🇪 Kenya: Betika, SportPesa, Odibets\n"
        "🇿🇦 South Africa: Hollywoodbets, Supabets\n"
        "🌍 Pan-Africa: 1xBet, Betway, Melbet\n\n"
        "Full bonus comparison → {site_url}\n"
        "Join for daily deals → {channel}\n\n"
        "#BettingBonus #NewPlayer #Africa #SifuFinds"
    ),
    (
        "⚡ ODDS ALERT — BEST PRICES RIGHT NOW\n\n"
        "We track live odds across 19 African bookmakers 24/7.\n\n"
        "Tip: Always compare before placing. The same bet can pay 40% more\n"
        "at one bookmaker vs another.\n\n"
        "Live odds comparison: {site_url}\n"
        "Follow {channel} for instant price alerts 🔔\n\n"
        "#OddsAlert #BestOdds #SmartBetting #SifuFinds #Africa"
    ),
]

EDUCATION_TEMPLATES = [
    (
        "📚 BETTING SMART IN AFRICA — Quick Guide\n\n"
        "3 rules serious African bettors follow:\n\n"
        "1️⃣ Always compare odds before betting (saves 15-40%)\n"
        "2️⃣ Use licensed bookmakers only (NLRC, BCLB, NGBB)\n"
        "3️⃣ Claim free bets before depositing your own money\n\n"
        "Your free bet & odds comparison tool: {site_url}\n"
        "More tips daily: {channel}\n\n"
        "#BettingTips #SmartBetting #ResponsibleBetting #SifuFinds"
    ),
    (
        "💡 DID YOU KNOW?\n\n"
        "The difference between the best and worst odds on a typical\n"
        "African football match can be 30-50%.\n\n"
        "Example: Over 2.5 goals on a NPFL match\n"
        "❌ Some books: 1.60\n"
        "✅ Best price:  2.30 (at 1xBet or Betway)\n\n"
        "That's a ₦700 difference on every ₦1,000 bet.\n\n"
        "Compare live: {site_url}\n"
        "Join {channel} for daily best-odds picks!\n\n"
        "#OddsComparison #BettingValue #Africa #SifuFinds"
    ),
]

ALL_TEMPLATES = FOOTBALL_TEMPLATES + BONUS_TEMPLATES + EDUCATION_TEMPLATES


def _build_message(group: dict) -> str:
    template = random.choice(ALL_TEMPLATES)
    now = datetime.now(timezone.utc)
    return template.format(
        date=now.strftime("%A %d %b"),
        day=now.strftime("%A"),
        site_url=SITE_URL,
        channel=OWN_CHANNEL,
        region=group.get("region", "Africa"),
    )


# ── STATE MANAGEMENT ──────────────────────────────────────────────────────────

def _load_growth_state() -> dict:
    if GROWTH_STATE_FILE.exists():
        try:
            return json.loads(GROWTH_STATE_FILE.read_text())
        except Exception:
            pass
    return {"group_last_posted": {}}


def _save_growth_state(state: dict) -> None:
    GROWTH_STATE_FILE.write_text(json.dumps(state, indent=2))


def _is_due(group: dict, state: dict) -> bool:
    last_str = state["group_last_posted"].get(group["username"])
    if not last_str:
        return True
    last_dt = datetime.fromisoformat(last_str)
    return (datetime.now(timezone.utc) - last_dt) >= timedelta(hours=GROUP_COOLDOWN_HOURS)


def _mark_posted(group: dict, state: dict) -> None:
    state["group_last_posted"][group["username"]] = datetime.now(timezone.utc).isoformat()


# ── EXTRA GROUPS FROM ENV ─────────────────────────────────────────────────────

def _load_extra_groups() -> list[dict]:
    """
    Optional: set TELEGRAM_GROWTH_GROUPS in .env as comma-separated usernames.
    Example: TELEGRAM_GROWTH_GROUPS=groupone,grouptwo,groupthree
    """
    raw = os.getenv("TELEGRAM_GROWTH_GROUPS", "")
    extras = []
    for username in raw.split(","):
        username = username.strip().lstrip("@")
        if username:
            extras.append({"username": username, "region": "Africa", "topic": "general"})
    return extras


# ── TELETHON POSTER ───────────────────────────────────────────────────────────

async def post_to_groups(
    due_groups: list[dict],
    state: dict,
    dry_run: bool = False,
    limit: int = DEFAULT_RUN_LIMIT,
) -> dict[str, str]:
    results: dict[str, str] = {}

    try:
        from telethon import TelegramClient, errors
        from telethon.sessions import StringSession
    except ImportError:
        print("Install Telethon: pip install telethon")
        return results

    api_id   = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash = os.getenv("TELEGRAM_API_HASH", "")
    session  = os.getenv("TELEGRAM_SESSION_STRING", "")
    phone    = os.getenv("TELEGRAM_PHONE", "")

    if api_id == 0:
        print("✗ TELEGRAM_API_ID not set.")
        return results

    session_obj = StringSession(session) if session else StringSession()

    async with TelegramClient(session_obj, api_id, api_hash) as client:
        if not session:
            await client.start(phone=phone)
            saved = client.session.save()
            print(f"\n✓ SESSION STRING (add as TELEGRAM_SESSION_STRING secret):\n{saved}\n")

        posted = 0
        for group in due_groups:
            if posted >= limit:
                break

            username = group["username"]
            message  = _build_message(group)

            if dry_run:
                print(f"\n─── DRY RUN: @{username} ───\n{message}\n")
                results[username] = "dry_run"
                continue

            try:
                entity = await client.get_entity(username)
                await client.send_message(entity, message)
                _mark_posted(group, state)
                results[username] = "success"
                print(f"  ✓ Posted to @{username} ({group['region']})")
                posted += 1
                # Polite rate-limiting between groups
                await asyncio.sleep(random.uniform(8, 18))

            except errors.FloodWaitError as e:
                print(f"  ⏳ Rate limit on @{username} — wait {e.seconds}s — skipping")
                results[username] = f"flood_wait:{e.seconds}s"

            except errors.ChatWriteForbiddenError:
                print(f"  ✗ @{username} — write not allowed, skipping")
                results[username] = "write_forbidden"
                # Still mark as attempted so we don't retry immediately
                _mark_posted(group, state)

            except errors.UsernameNotOccupiedError:
                print(f"  ✗ @{username} — group not found, skipping")
                results[username] = "not_found"
                _mark_posted(group, state)

            except Exception as e:
                print(f"  ✗ @{username} — error: {e}")
                results[username] = f"error:{str(e)[:80]}"

    return results


# ── MAIN ──────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False, limit: int = DEFAULT_RUN_LIMIT) -> None:
    log("growth", "start", "running")

    state = _load_growth_state()

    all_groups = GROWTH_GROUPS + _load_extra_groups()
    due = [g for g in all_groups if _is_due(g, state)]

    if not due:
        print("✓ All groups on cooldown — nothing to post right now.")
        log("growth", "skip", "all_on_cooldown")
        return

    print(f"📣 {len(due)} group(s) due for posting (limit: {limit} per run)")

    results = asyncio.run(post_to_groups(due, state, dry_run=dry_run, limit=limit))

    if not dry_run:
        _save_growth_state(state)

    success  = sum(1 for v in results.values() if v == "success")
    skipped  = len(results) - success
    print(f"\n✓ Growth run complete — posted to {success} groups, skipped {skipped}")
    log("growth", "done", "success", f"posted:{success} skipped:{skipped}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Telegram Channel Growth Agent")
    parser.add_argument("--dry-run", action="store_true", help="Preview messages without sending")
    parser.add_argument("--limit",   type=int, default=DEFAULT_RUN_LIMIT,
                        help=f"Max groups to post in per run (default: {DEFAULT_RUN_LIMIT})")
    args = parser.parse_args()
    run(dry_run=args.dry_run, limit=args.limit)
