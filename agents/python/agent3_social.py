"""
Agent 3 — Social Media Manager
Posts to Telegram (Bot API), Facebook, and Instagram.
No session strings. No SMS codes. Just tokens.
"""
import sys
import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

sys.path.insert(0, os.path.dirname(__file__))

from utils.queue_manager import pop_next
from utils.logger import log

TELEGRAM_BOT_TOKEN      = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL        = os.getenv("TELEGRAM_CHANNEL_USERNAME", "")
FACEBOOK_PAGE_ID        = os.getenv("FACEBOOK_PAGE_ID", "")
FACEBOOK_TOKEN          = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID    = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")


# ── Telegram ──────────────────────────────────────────────────────────────────

def post_telegram(message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL:
        print("⚠ Telegram not configured yet.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": TELEGRAM_CHANNEL,
        "text": message,
        "parse_mode": "HTML",
    }, timeout=15)
    ok = r.status_code == 200
    log("agent3", "telegram", "success" if ok else "failed", "" if ok else r.json().get("description",""))
    return ok


# ── Facebook ──────────────────────────────────────────────────────────────────

def post_facebook(message: str) -> bool:
    if not FACEBOOK_PAGE_ID or not FACEBOOK_TOKEN:
        print("⚠ Facebook not configured yet.")
        return False
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed",
        data={"message": message, "access_token": FACEBOOK_TOKEN},
        timeout=15,
    )
    ok = r.status_code == 200
    log("agent3", "facebook", "success" if ok else "failed", "" if ok else r.text[:100])
    return ok


# ── Instagram ─────────────────────────────────────────────────────────────────

def post_instagram(caption: str) -> bool:
    if not INSTAGRAM_ACCOUNT_ID or not FACEBOOK_TOKEN:
        print("⚠ Instagram not configured yet.")
        return False
    image_url = "https://sifufinds.com/assets/social-card.jpg"
    r1 = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media",
        data={"image_url": image_url, "caption": caption, "access_token": FACEBOOK_TOKEN},
        timeout=15,
    )
    if r1.status_code != 200:
        log("agent3", "instagram_create", "failed", r1.text[:100])
        return False
    r2 = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish",
        data={"creation_id": r1.json().get("id"), "access_token": FACEBOOK_TOKEN},
        timeout=15,
    )
    ok = r2.status_code == 200
    log("agent3", "instagram", "success" if ok else "failed")
    return ok


# ── Fallback content if queue is empty ────────────────────────────────────────

def build_fallback() -> dict:
    from llm import ask
    raw = ask(
        "You are the social media manager for SifuFinds (sifufinds.com), Africa's #1 betting comparison site.",
        """Return ONLY this JSON, no other text:
{
  "social": {
    "telegram": "short punchy tip post under 400 chars with emoji pointing to sifufinds.com",
    "facebook": "150-word engaging post with emoji",
    "instagram": "100-word caption",
    "hashtags": "#SifuFinds #AfricanBetting #SportsBetting #BettingTips #Bet9ja #Sportpesa #Hollywoodbets #AFCON #EPL #CAFChampionsLeague #NPFL #KPL #PSL #FreeBets #BettingBonus #OnlineBetting #MobileBetting #FootballTips #AccumulatorTips #WinBig #BettingCommunity #iGamingAfrica #SmartBetting #BettingAfrica #BettingLife"
  }
}"""
    )
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    return json.loads(raw)


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    log("agent3", "start", "running")

    content = pop_next()
    if not content:
        print("Queue empty — generating fallback.")
        try:
            content = build_fallback()
        except Exception as e:
            log("agent3", "fallback_error", "failed", str(e))
            sys.exit(1)

    social = content.get("social", {})
    ig_caption = social.get("instagram", "") + "\n.\n.\n.\n" + social.get("hashtags", "")

    results = {
        "telegram":  post_telegram(social.get("telegram", "")),
        "facebook":  post_facebook(social.get("facebook", "")),
        "instagram": post_instagram(ig_caption),
    }

    ok = sum(results.values())
    print(f"✓ Posted {ok}/{len(results)} platforms: {results}")
    if ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    run()
