"""
Telegram Outreach Agent — SifuFinds
Scrapes active users from competitor betting groups, builds contextual profiles,
and runs a 5-touch personalized DM sequence to convert them into @sifufinds
channel subscribers.

Anti-ban strategy:
  - Max 25 new DMs per day (low and slow; build account trust first)
  - Random 35–120s delay between every send
  - Auto-pause on FloodWaitError
  - Hard-stop if user blocks, reports, or opts out
  - Only DM users active in the last 30 days
  - Never re-contact a user within 48 h

Stages per prospect:
  scraped → dm1 → dm2 → dm3 → dm4 → dm5 → cold
  Any stage can flip to: replied | converted | blocked | opted_out

Usage:
  python agent_telegram_outreach.py --scrape           # scrape new prospects
  python agent_telegram_outreach.py --outreach         # send DMs + follow-ups
  python agent_telegram_outreach.py --scrape --outreach  # both (CI default)
  python agent_telegram_outreach.py --dry-run          # preview, no sends
  python agent_telegram_outreach.py --limit 10         # cap sends per run
"""

import argparse
import asyncio
import json
import os
import random
import re
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

MAX_DMS_PER_RUN        = 25     # hard cap per CI run
FOLLOW_UP_STAGES       = 5      # DM1 → DM5 then cold
MIN_DELAY_S            = 35     # seconds between sends (min)
MAX_DELAY_S            = 120    # seconds between sends (max)
RECONTACT_HOURS        = 48     # minimum gap between any two messages to same user
SCRAPE_ACTIVE_DAYS     = 30     # only scrape users seen in last N days
SCRAPE_MESSAGES_LIMIT  = 400    # recent group messages to scan per group
MAX_PROSPECTS_PER_GROUP = 60    # cap per group scrape run

PROSPECTS_FILE = Path(__file__).parent / "outreach_prospects.json"
STATE_FILE     = Path(__file__).parent / "outreach_state.json"

# ── TARGET GROUPS (competitors + high-traffic African betting communities) ─────

TARGET_GROUPS: list[dict] = [
    # Nigeria
    {"username": "bet9jatips",           "region": "Nigeria"},
    {"username": "nigerialivebet",        "region": "Nigeria"},
    {"username": "naijabettingtips",      "region": "Nigeria"},
    {"username": "npfl_fans",             "region": "Nigeria"},
    {"username": "nigerianfootballfans",  "region": "Nigeria"},
    # Kenya
    {"username": "kenyabettingtips",      "region": "Kenya"},
    {"username": "sportpesatips",         "region": "Kenya"},
    {"username": "kplsoccer",             "region": "Kenya"},
    {"username": "eastafricasports",      "region": "East Africa"},
    # South Africa
    {"username": "safootballtips",        "region": "South Africa"},
    {"username": "hollywoodbets_tips",    "region": "South Africa"},
    {"username": "pslsoccerfans",         "region": "South Africa"},
    # Ghana
    {"username": "ghanasportsbetting",    "region": "Ghana"},
    {"username": "gplghana",              "region": "Ghana"},
    # Pan-Africa
    {"username": "africanbettingcommunity", "region": "Pan-Africa"},
    {"username": "bettingtipsafrica",     "region": "Pan-Africa"},
    {"username": "africanfootballdaily",  "region": "Pan-Africa"},
    {"username": "ibetchannel",           "region": "Pan-Africa"},
]

# ── COUNTRY HINTS ──────────────────────────────────────────────────────────────

_COUNTRY_KEYWORDS = {
    "Nigeria":      ["nigeria", "naija", "lagos", "abuja", "₦", "nlrc", "bet9ja", "betking", "sportybet"],
    "Kenya":        ["kenya", "nairobi", "ksh", "mpesa", "bclb", "sportpesa", "betika", "odibets"],
    "South Africa": ["south africa", "cape town", "johannesburg", "joburg", "r ", "zar", "hollywoodbets", "supabets", "psl"],
    "Ghana":        ["ghana", "accra", "ghs", "gpl", "betway gh"],
    "Uganda":       ["uganda", "kampala", "ugx"],
    "Tanzania":     ["tanzania", "dar es salaam", "tzs"],
}

def _detect_country(text: str) -> str:
    low = (text or "").lower()
    for country, keywords in _COUNTRY_KEYWORDS.items():
        if any(k in low for k in keywords):
            return country
    return "Africa"


_BETTING_KEYWORDS = [
    "bet", "odds", "tips", "football", "soccer", "sport", "accumulator",
    "acca", "banker", "jackpot", "free bet", "bonus", "predict", "1xbet",
    "betway", "melbet", "bet9ja", "sportybet", "betika", "sportpesa",
    "correct score", "over 2.5", "btts", "win", "stake",
]

def _extract_keywords(text: str) -> list[str]:
    low = (text or "").lower()
    return [k for k in _BETTING_KEYWORDS if k in low]


# ── MESSAGE TEMPLATES (5-touch sequence) ──────────────────────────────────────
# Each template receives: first_name, region, site_url, channel

def _msg1(first_name: str, region: str, **_) -> str:
    name = first_name or "there"
    return (
        f"Hey {name} 👋\n\n"
        f"I noticed you're active in the {region} betting community — thought you'd find this useful.\n\n"
        f"We built a free tool that compares odds across all the major African bookmakers in real time "
        f"(Bet9ja, 1xBet, Betway, SportPesa, Melbet and more).\n\n"
        f"Same bet, best price — every time.\n\n"
        f"👉 {SITE_URL}\n\n"
        f"No catch, completely free. Let me know what you think!"
    )

def _msg2(first_name: str, region: str, **_) -> str:
    name = first_name or "boss"
    tips = {
        "Nigeria":      "Nigerian Premier League + AFCON qualifiers",
        "Kenya":        "Kenya Premier League + CAF Champions League",
        "South Africa": "PSL + CAF Champions League",
        "Ghana":        "Ghana Premier League + AFCON qualifiers",
        "East Africa":  "KPL + Tanzanian Premier League",
    }.get(region, "African football leagues")
    return (
        f"{name}, quick one —\n\n"
        f"Did you know the same bet on {tips} can pay up to 40% more depending on the bookmaker?\n\n"
        f"Example: Over 2.5 goals priced at 1.60 on one site is sometimes 2.30 on another.\n"
        f"On a ₦1,000 stake that's ₦700 extra — for zero extra risk.\n\n"
        f"We compare all of them live: {SITE_URL}\n\n"
        f"Join the channel for daily best-odds picks → {OWN_CHANNEL}"
    )

def _msg3(first_name: str, **_) -> str:
    name = first_name or "fam"
    return (
        f"Checking in {name} 🙌\n\n"
        f"In case you missed it — {OWN_CHANNEL} posts:\n\n"
        f"✅ Daily best-odds picks across African leagues\n"
        f"✅ Free bet alerts (no deposit offers)\n"
        f"✅ Accumulator ideas with compared odds\n"
        f"✅ Bookmaker bonus breakdowns\n\n"
        f"All free. 1,000+ bettors already use it.\n\n"
        f"Join here → {OWN_CHANNEL}\n"
        f"Or compare odds now → {SITE_URL}"
    )

def _msg4(first_name: str, region: str, **_) -> str:
    name = first_name or "chief"
    bookmakers = {
        "Nigeria":      "Bet9ja, BetKing, Sportybet, 1xBet",
        "Kenya":        "Betika, SportPesa, Odibets, 1xBet",
        "South Africa": "Hollywoodbets, Supabets, Betway, 1xBet",
        "Ghana":        "Betway, 1xBet, Melbet, Sportybet",
    }.get(region, "Bet9ja, 1xBet, Betway, SportPesa, Melbet")
    return (
        f"Last one from me {name} —\n\n"
        f"We've just added better filtering for {region} so you can instantly see:\n\n"
        f"• Best odds for your local leagues\n"
        f"• Which of {bookmakers} is paying most today\n"
        f"• Current no-deposit free bet offers\n\n"
        f"Check it: {SITE_URL}\n\n"
        f"If this isn't useful just ignore and I won't message again 🙏"
    )

def _msg5(first_name: str, **_) -> str:
    name = first_name or "mate"
    return (
        f"Hey {name}, final message I promise 😅\n\n"
        f"Sharing one last thing — we've got a daily Telegram channel that sends:\n\n"
        f"🔔 Real-time odds alerts\n"
        f"🎁 Free bet drops before they expire\n"
        f"⚽ Best picks from African leagues\n\n"
        f"Completely free, you can leave any time.\n"
        f"→ {OWN_CHANNEL}\n\n"
        f"Take care and good luck with your bets! 🤝"
    )

SEQUENCE = [_msg1, _msg2, _msg3, _msg4, _msg5]

# Days to wait before each follow-up (after previous message)
FOLLOW_UP_DELAYS_DAYS = [0, 2, 5, 10, 18]


# ── PROSPECT STATE ─────────────────────────────────────────────────────────────

def _load_prospects() -> list[dict]:
    if PROSPECTS_FILE.exists():
        try:
            return json.loads(PROSPECTS_FILE.read_text())
        except Exception:
            pass
    return []


def _save_prospects(prospects: list[dict]) -> None:
    PROSPECTS_FILE.write_text(json.dumps(prospects, indent=2, default=str))


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def _prospect_key(user_id: int) -> str:
    return str(user_id)


def _stage_index(stage: str) -> int:
    """dm1→0, dm2→1, …, dm5→4; anything else→-1"""
    m = re.match(r"dm(\d+)$", stage)
    return int(m.group(1)) - 1 if m else -1


def _next_stage(current: str) -> str:
    idx = _stage_index(current)
    if idx < 0:
        return "dm1"
    next_idx = idx + 1
    return f"dm{next_idx + 1}" if next_idx < FOLLOW_UP_STAGES else "cold"


def _is_terminal(stage: str) -> bool:
    return stage in ("cold", "converted", "blocked", "opted_out", "replied")


def _is_due(record: dict) -> bool:
    if _is_terminal(record.get("stage", "scraped")):
        return False
    next_str = record.get("next_contact")
    if not next_str:
        return True
    try:
        next_dt = datetime.fromisoformat(next_str)
        return datetime.now(timezone.utc) >= next_dt
    except Exception:
        return True


# ── TELETHON HELPERS ───────────────────────────────────────────────────────────

async def _get_client():
    from telethon import TelegramClient
    from telethon.sessions import StringSession

    api_id   = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()
    session  = os.getenv("TELEGRAM_SESSION_STRING", "").strip()

    if not api_id or not api_hash or not session:
        raise RuntimeError("Missing TELEGRAM_API_ID / TELEGRAM_API_HASH / TELEGRAM_SESSION_STRING")

    client = TelegramClient(StringSession(session), api_id, api_hash)
    await client.start()
    return client


# ── SCRAPER ────────────────────────────────────────────────────────────────────

async def scrape_group(client, group_info: dict, existing_ids: set) -> list[dict]:
    """
    Read recent messages from a group, extract active unique senders,
    build contextual prospect records.
    """
    from telethon import errors
    from telethon.tl.types import User

    username = group_info["username"]
    region   = group_info["region"]
    new_prospects = []

    cutoff = datetime.now(timezone.utc) - timedelta(days=SCRAPE_ACTIVE_DAYS)

    try:
        entity   = await client.get_entity(username)
        messages = await client.get_messages(entity, limit=SCRAPE_MESSAGES_LIMIT)
    except errors.FloodWaitError as e:
        print(f"  ⏳ Flood wait {e.seconds}s scraping @{username} — skipping")
        return []
    except Exception as e:
        print(f"  ✗ Cannot access @{username}: {e}")
        return []

    seen_in_batch: set[int] = set()

    for msg in messages:
        if not msg.date or msg.date.replace(tzinfo=timezone.utc) < cutoff:
            continue
        sender = msg.sender
        if not isinstance(sender, User):
            continue
        if sender.bot or sender.id in existing_ids or sender.id in seen_in_batch:
            continue
        if len(new_prospects) >= MAX_PROSPECTS_PER_GROUP:
            break

        seen_in_batch.add(sender.id)

        # Build context
        bio_text   = getattr(sender, "about", "") or ""
        name_text  = f"{sender.first_name or ''} {sender.last_name or ''} {sender.username or ''}"
        msg_text   = msg.message or ""
        full_text  = f"{bio_text} {name_text} {msg_text}"

        country  = _detect_country(full_text) or region
        keywords = _extract_keywords(full_text)

        new_prospects.append({
            "user_id":     sender.id,
            "username":    sender.username or "",
            "first_name":  sender.first_name or "",
            "last_name":   sender.last_name or "",
            "bio":         bio_text[:200],
            "source_group": username,
            "region":      country,
            "keywords":    keywords,
            "stage":       "scraped",
            "messages_sent": 0,
            "replied":     False,
            "converted":   False,
            "opted_out":   False,
            "last_contact":  None,
            "next_contact":  None,
            "scraped_at":  datetime.now(timezone.utc).isoformat(),
        })

    print(f"  ✓ @{username} — {len(new_prospects)} new prospects from {len(messages)} messages")
    return new_prospects


async def run_scrape(dry_run: bool = False) -> int:
    print(f"\n🔍 Scraping {len(TARGET_GROUPS)} target groups...")
    client = await _get_client()

    prospects  = _load_prospects()
    state      = _load_state()
    existing   = {p["user_id"] for p in prospects} | {int(k) for k in state}
    total_new  = 0

    try:
        for group in TARGET_GROUPS:
            new = await scrape_group(client, group, existing)
            if not dry_run:
                prospects.extend(new)
                existing.update(p["user_id"] for p in new)
            total_new += len(new)
            await asyncio.sleep(random.uniform(3, 8))
    finally:
        await client.disconnect()

    if not dry_run:
        _save_prospects(prospects)

    print(f"\n✓ Scrape complete — {total_new} new prospects added (total: {len(prospects)})")
    log("outreach", "scrape", "done", f"new:{total_new}")
    return total_new


# ── OUTREACH ENGINE ────────────────────────────────────────────────────────────

async def send_dm(client, prospect: dict, record: dict, dry_run: bool) -> str:
    """
    Send the appropriate DM in the sequence. Returns outcome string.
    """
    from telethon import errors

    stage      = record.get("stage", "scraped")
    next_stage = _next_stage(stage)

    if next_stage == "cold":
        return "cold"

    # Choose template
    seq_idx = _stage_index(next_stage)
    if seq_idx < 0 or seq_idx >= len(SEQUENCE):
        return "error"

    fn    = prospect.get("first_name", "")
    region = prospect.get("region", "Africa")
    message = SEQUENCE[seq_idx](first_name=fn, region=region)

    target = prospect.get("username") or prospect["user_id"]

    if dry_run:
        print(f"\n── DRY RUN [{next_stage}] → @{target} ({region}) ──\n{message}\n")
        return "dry_run"

    try:
        entity = await client.get_entity(
            f"@{target}" if prospect.get("username") else int(prospect["user_id"])
        )
        await client.send_message(entity, message)
        return "sent"

    except errors.FloodWaitError as e:
        print(f"  ⏳ Flood wait {e.seconds}s — pausing")
        await asyncio.sleep(e.seconds + 5)
        return "flood_wait"

    except errors.UserPrivacyRestrictedError:
        return "privacy_restricted"

    except errors.UserIsBlockedError:
        return "blocked"

    except errors.PeerFloodError:
        print("  ✗ PeerFlood — stopping run to protect account")
        return "peer_flood"

    except Exception as e:
        err = str(e)
        if "blocked" in err.lower():
            return "blocked"
        print(f"  ✗ {target}: {err[:80]}")
        return "error"


async def run_outreach(dry_run: bool = False, limit: int = MAX_DMS_PER_RUN) -> int:
    print(f"\n📨 Starting outreach run (limit: {limit} DMs)...")
    client = await _get_client()

    prospects = _load_prospects()
    state     = _load_state()
    sent      = 0
    peer_flood = False

    # Build queue: due prospects, prioritised by scrape time (oldest first)
    due_prospects = []
    for p in prospects:
        uid = _prospect_key(p["user_id"])
        rec = state.get(uid, {"stage": "scraped", "next_contact": None})
        if _is_due(rec):
            due_prospects.append((p, rec, uid))

    due_prospects.sort(key=lambda x: x[0].get("scraped_at", ""))
    print(f"  {len(due_prospects)} prospects due for contact")

    try:
        for prospect, record, uid in due_prospects:
            if sent >= limit or peer_flood:
                break

            outcome = await send_dm(client, prospect, record, dry_run)
            now     = datetime.now(timezone.utc)

            if outcome == "peer_flood":
                peer_flood = True
                break

            if outcome in ("privacy_restricted", "error"):
                record["stage"] = "blocked"
                print(f"  ✗ {prospect.get('username', uid)}: {outcome}")

            elif outcome == "blocked":
                record["stage"] = "blocked"
                print(f"  ✗ {prospect.get('username', uid)}: blocked")

            elif outcome in ("sent", "dry_run"):
                next_s = _next_stage(record.get("stage", "scraped"))
                delay_idx = min(_stage_index(next_s), len(FOLLOW_UP_DELAYS_DAYS) - 1)
                days_ahead = FOLLOW_UP_DELAYS_DAYS[max(delay_idx, 0) + 1] if delay_idx + 1 < len(FOLLOW_UP_DELAYS_DAYS) else 999
                record["stage"]       = next_s
                record["last_contact"] = now.isoformat()
                record["next_contact"] = (now + timedelta(days=days_ahead)).isoformat()
                record["messages_sent"] = record.get("messages_sent", 0) + 1
                stage_label = "cold" if next_s == "cold" else next_s
                name = prospect.get("username") or prospect.get("first_name") or uid
                print(f"  ✓ [{stage_label}] → {name} ({prospect.get('region','?')})")
                sent += 1

                # Check if sequence is now exhausted
                if _is_terminal(record["stage"]):
                    record["stage"] = "cold"

                if outcome == "sent":
                    await asyncio.sleep(random.uniform(MIN_DELAY_S, MAX_DELAY_S))

            elif outcome == "flood_wait":
                # Already slept; try next prospect
                pass

            if not dry_run:
                state[uid] = record

    finally:
        await client.disconnect()

    if not dry_run:
        _save_state(state)

    print(f"\n✓ Outreach complete — sent {sent} messages")
    log("outreach", "send", "done", f"sent:{sent}")
    return sent


# ── INBOX MONITOR (read replies + detect opt-outs) ────────────────────────────

async def sync_replies(dry_run: bool = False) -> None:
    """
    Scan recent DM conversations to detect replies and opt-out keywords.
    Updates state so replied users are marked and removed from sequence.
    """
    from telethon.tl.types import User

    client = await _get_client()
    state  = _load_state()
    updated = 0

    OPT_OUT_PATTERNS = re.compile(
        r"\b(stop|unsubscribe|remove|leave me|don'?t message|no thanks|not interested|fuck off|go away)\b",
        re.IGNORECASE,
    )

    try:
        # Get recent DM dialogs
        async for dialog in client.iter_dialogs(limit=200):
            if not isinstance(dialog.entity, User):
                continue
            uid = _prospect_key(dialog.entity.id)
            if uid not in state:
                continue
            record = state[uid]
            if _is_terminal(record.get("stage", "")):
                continue

            # Get messages in this dialog
            msgs = await client.get_messages(dialog.entity, limit=10)
            me   = await client.get_me()

            for msg in msgs:
                if msg.sender_id == me.id:
                    continue  # our message
                text = (msg.message or "").strip()
                if not text:
                    continue

                if OPT_OUT_PATTERNS.search(text):
                    record["stage"]     = "opted_out"
                    record["opted_out"] = True
                    print(f"  🚫 Opted out: {dialog.entity.username or uid}")
                    updated += 1
                    break
                else:
                    record["stage"]   = "replied"
                    record["replied"] = True
                    print(f"  💬 Replied: {dialog.entity.username or uid} — \"{text[:60]}\"")
                    updated += 1
                    break

    finally:
        await client.disconnect()

    if not dry_run and updated:
        _save_state(state)

    print(f"  Inbox sync: {updated} records updated")
    log("outreach", "sync", "done", f"updated:{updated}")


# ── STATS ──────────────────────────────────────────────────────────────────────

def print_stats() -> None:
    prospects = _load_prospects()
    state     = _load_state()

    stage_counts: dict[str, int] = {}
    for p in prospects:
        uid = _prospect_key(p["user_id"])
        stage = state.get(uid, {}).get("stage", "scraped")
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    total = len(prospects)
    print(f"\n📊 Outreach Stats — {total} total prospects")
    print("─" * 35)
    for stage, count in sorted(stage_counts.items()):
        pct = f"{count/total*100:.0f}%" if total else "0%"
        print(f"  {stage:20} {count:5}  ({pct})")

    replied   = sum(1 for r in state.values() if r.get("replied"))
    converted = sum(1 for r in state.values() if r.get("converted"))
    opted_out = sum(1 for r in state.values() if r.get("opted_out"))
    print(f"\n  Replied:   {replied}")
    print(f"  Converted: {converted}")
    print(f"  Opted out: {opted_out}")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def run(
    do_scrape: bool = False,
    do_outreach: bool = False,
    do_sync: bool = True,
    dry_run: bool = False,
    limit: int = MAX_DMS_PER_RUN,
) -> None:
    log("outreach", "start", "running")

    if not do_scrape and not do_outreach:
        # Default: both
        do_scrape = do_outreach = True

    if do_scrape:
        asyncio.run(run_scrape(dry_run=dry_run))

    if do_sync:
        asyncio.run(sync_replies(dry_run=dry_run))

    if do_outreach:
        asyncio.run(run_outreach(dry_run=dry_run, limit=limit))

    print_stats()
    log("outreach", "done", "success")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Telegram Outreach Agent")
    parser.add_argument("--scrape",    action="store_true", help="Scrape new prospects from target groups")
    parser.add_argument("--outreach",  action="store_true", help="Send DMs and follow-ups")
    parser.add_argument("--no-sync",   action="store_true", help="Skip inbox reply sync")
    parser.add_argument("--dry-run",   action="store_true", help="Preview messages without sending")
    parser.add_argument("--limit",     type=int, default=MAX_DMS_PER_RUN,
                        help=f"Max DMs per run (default: {MAX_DMS_PER_RUN})")
    parser.add_argument("--stats",     action="store_true", help="Print stats and exit")
    args = parser.parse_args()

    if args.stats:
        print_stats()
        sys.exit(0)

    run(
        do_scrape=args.scrape,
        do_outreach=args.outreach,
        do_sync=not args.no_sync,
        dry_run=args.dry_run,
        limit=args.limit,
    )
