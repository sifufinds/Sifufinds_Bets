"""
Agent 3 — Social Media Manager (Telethon version for Telegram)

Telegram: Uses Telethon — log in with YOUR phone number, no developer account.
Facebook/Instagram: Still uses the free Graph API — but it's YOUR Facebook account,
                    no separate developer account. See FB_SETUP_SIMPLE.md.

First run: You'll get an SMS on your phone — normal, one-time only.
After that: Runs silently forever.
"""
import sys
import os
import json
import asyncio
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from config import (
    FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN,
    INSTAGRAM_ACCOUNT_ID,
)
from utils.queue_manager import pop_next
from utils.logger import log

# ── Telegram via Telethon (phone number login — no bot, no developer account) ──

async def post_to_telegram_channel(channel_username: str, message: str) -> bool:
    """
    Posts to your Telegram channel using YOUR account (not a bot).
    First run only: asks for SMS code. Saves session after that.
    """
    try:
        from telethon import TelegramClient
        from telethon.sessions import StringSession
    except ImportError:
        print("Install Telethon: pip install telethon")
        return False

    api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash = os.getenv("TELEGRAM_API_HASH", "")
    session_string = os.getenv("TELEGRAM_SESSION_STRING", "")
    phone = os.getenv("TELEGRAM_PHONE", "")

    if api_id == 0:
        print("⚠ TELEGRAM_API_ID not set. See setup note below.")
        return False

    session = StringSession(session_string) if session_string else StringSession()

    async with TelegramClient(session, api_id, api_hash) as client:
        if not session_string:
            # First run: authenticate
            await client.start(phone=phone)
            saved_session = client.session.save()
            print(f"\n✓ SESSION STRING (add this to GitHub Secrets as TELEGRAM_SESSION_STRING):\n{saved_session}\n")

        await client.send_message(channel_username, message)

    log("agent3", "telegram_post", "success")
    return True


# ── Facebook — free, uses your existing account ───────────────────────────────

def post_facebook(message: str) -> bool:
    if not FACEBOOK_PAGE_ID or not FACEBOOK_PAGE_ACCESS_TOKEN:
        print("⚠ Facebook not configured.")
        return False
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed",
        data={"message": message, "access_token": FACEBOOK_PAGE_ACCESS_TOKEN},
        timeout=15,
    )
    ok = r.status_code == 200
    log("agent3", "facebook_post", "success" if ok else "failed", "" if ok else r.text[:100])
    return ok


def post_instagram(caption: str) -> bool:
    if not INSTAGRAM_ACCOUNT_ID or not FACEBOOK_PAGE_ACCESS_TOKEN:
        print("⚠ Instagram not configured.")
        return False
    image_url = "https://sifufinds.com/assets/social-card.jpg"
    r1 = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media",
        data={"image_url": image_url, "caption": caption, "access_token": FACEBOOK_PAGE_ACCESS_TOKEN},
        timeout=15,
    )
    if r1.status_code != 200:
        log("agent3", "instagram_create", "failed", r1.text[:100])
        return False
    creation_id = r1.json().get("id")
    r2 = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish",
        data={"creation_id": creation_id, "access_token": FACEBOOK_PAGE_ACCESS_TOKEN},
        timeout=15,
    )
    ok = r2.status_code == 200
    log("agent3", "instagram_post", "success" if ok else "failed")
    return ok


def build_fallback() -> dict:
    from llm import ask
    raw = ask(
        "You are the social media manager for SifuFinds (sifufinds.com), Africa's #1 betting site.",
        'Return only valid JSON: {"social": {"telegram": "short tip post", "facebook": "150-word post", "instagram": "100-word caption + 25 hashtags"}}',
    )
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    return json.loads(raw)


def run():
    log("agent3", "start", "running")
    content = pop_next()

    if not content:
        print("Queue empty — generating fallback content.")
        try:
            content = build_fallback()
        except Exception as e:
            log("agent3", "fallback_error", "failed", str(e))
            sys.exit(1)

    social = content.get("social", {})
    channel = os.getenv("TELEGRAM_CHANNEL_USERNAME", "")

    results = {}
    if channel and social.get("telegram"):
        results["telegram"] = asyncio.run(
            post_to_telegram_channel(channel, social["telegram"])
        )
    if social.get("facebook"):
        results["facebook"] = post_facebook(social["facebook"])
    if social.get("instagram"):
        ig_text = social["instagram"] + "\n" + social.get("hashtags", "")
        results["instagram"] = post_instagram(ig_text)

    success = sum(results.values())
    print(f"✓ Posted to {success}/{len(results)} platforms: {results}")
    if success == 0:
        sys.exit(1)


if __name__ == "__main__":
    run()


# ══════════════════════════════════════════════════════════════════════════════
# TELEGRAM SETUP — 5 minutes, no developer account, just your phone number
# ══════════════════════════════════════════════════════════════════════════════
#
# Step 1: Go to https://my.telegram.org — log in with your phone number
#         (this is YOUR Telegram account, not a bot or developer account)
# Step 2: Click "API Development Tools" → Create App
#         Give it any name, e.g. "SifuFinds"
#         You get: api_id (a number) and api_hash (a string)
#         These are FREE — my.telegram.org is just your Telegram account settings
#
# Step 3: Add to your .env or GitHub Secrets:
#         TELEGRAM_API_ID=12345678
#         TELEGRAM_API_HASH=abcdef1234567890abcdef
#         TELEGRAM_PHONE=+2348012345678  (your number with country code)
#         TELEGRAM_CHANNEL_USERNAME=@YourChannelUsername
#
# Step 4: Run locally ONCE: python agent3_social_telethon.py
#         It texts your phone. Enter the code. Done.
#         Copy the SESSION STRING it prints → add as TELEGRAM_SESSION_STRING secret
#         After that it runs silently on GitHub Actions forever, no phone needed.
#
# ══════════════════════════════════════════════════════════════════════════════
# FACEBOOK SETUP — 20 minutes, uses your EXISTING Facebook account
# ══════════════════════════════════════════════════════════════════════════════
#
# The Facebook "developer" setup is just your Facebook account.
# Go to: developers.facebook.com → Log in with Facebook → it's the same account.
# Then follow FB_SETUP_SIMPLE.md for the exact steps.
# ══════════════════════════════════════════════════════════════════════════════
