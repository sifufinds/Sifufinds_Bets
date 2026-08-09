"""
Agent 3 — Social Media Manager
Posts to Telegram (Bot API), Facebook, and Instagram.
No session strings. No SMS codes. Just tokens.
"""
import sys
import os
import json
import time
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

_FACEBOOK_MAX_ATTEMPTS = 3
_FACEBOOK_RETRY_DELAYS = (5, 15)  # seconds between attempts 1->2 and 2->3


def _post_facebook_once(message: str, image_path: str | Path | None, image_url: str | None):
    """Single attempt — returns the requests.Response (or raises on a
    network-level exception, left to the caller's retry loop)."""
    if image_path and Path(image_path).exists():
        # Photo posts outperform plain link posts on Pages and let each post
        # carry its own on-brand image. Graph API auto-linkifies the URL that
        # appears in the caption text, so the message still delivers a working link.
        with open(image_path, "rb") as f:
            return requests.post(
                f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos",
                data={"caption": message, "access_token": FACEBOOK_TOKEN},
                files={"source": f},
                timeout=30,
            )
    elif image_url:
        # Graph API can also fetch a hosted image by URL instead of an
        # uploaded file — used for e.g. a Wikimedia-hosted player photo.
        return requests.post(
            f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos",
            data={"caption": message, "url": image_url, "access_token": FACEBOOK_TOKEN},
            timeout=30,
        )
    else:
        return requests.post(
            f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed",
            data={"message": message, "access_token": FACEBOOK_TOKEN},
            timeout=15,
        )


def post_facebook(message: str, image_path: str | Path | None = None, image_url: str | None = None) -> bool:
    """Retries transient failures up to _FACEBOOK_MAX_ATTEMPTS times before
    giving up — added 2026-08-08 after finding every call site here treated
    a single failed HTTP request (network blip, momentary 5xx/429 from
    Graph API) as a permanent "this post never gets announced" outcome,
    with no second attempt of any kind. A 4xx auth/permission error (bad
    token, page not found) will also legitimately fail every retry, but
    that's cheap to rule out this way and correctly still returns False for
    the caller's own backlog/retry-later handling (see
    agent_sports_blog.announce_to_facebook) to pick up."""
    if not FACEBOOK_PAGE_ID or not FACEBOOK_TOKEN:
        print("⚠ Facebook not configured yet.")
        return False

    last_error = ""
    for attempt in range(1, _FACEBOOK_MAX_ATTEMPTS + 1):
        try:
            r = _post_facebook_once(message, image_path, image_url)
        except requests.RequestException as e:
            last_error = str(e)[:150]
        else:
            if r.status_code == 200:
                if attempt > 1:
                    log("agent3", "facebook", "success_after_retry", f"attempt {attempt}")
                else:
                    log("agent3", "facebook", "success", "")
                return True
            last_error = r.text[:150]

        if attempt < _FACEBOOK_MAX_ATTEMPTS:
            delay = _FACEBOOK_RETRY_DELAYS[attempt - 1]
            print(f"  ⚠ Facebook post attempt {attempt}/{_FACEBOOK_MAX_ATTEMPTS} failed ({last_error}) — retrying in {delay}s...")
            time.sleep(delay)

    log("agent3", "facebook", "failed", f"after {_FACEBOOK_MAX_ATTEMPTS} attempts: {last_error}")
    return False


# ── Instagram ─────────────────────────────────────────────────────────────────

def post_instagram(caption: str, image_url: str | None = None) -> bool:
    if not INSTAGRAM_ACCOUNT_ID or not FACEBOOK_TOKEN:
        print("⚠ Instagram not configured yet.")
        return False
    # assets/og-image.png is the site's real default social image (used in
    # index.html's own og:image tag) — "assets/social-card.jpg" doesn't
    # exist and 404s, confirmed live 2026-07-30.
    image_url = image_url or "https://sifufinds.com/assets/og-image.png"
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
    hashtags = social.get("hashtags", "")
    ig_caption = social.get("instagram", "") + "\n.\n.\n.\n" + hashtags
    # Facebook posts must always carry hashtags — never post the bare message.
    fb_caption = social.get("facebook", "").rstrip() + ("\n\n" + hashtags if hashtags else "")

    results = {
        "telegram":  post_telegram(social.get("telegram", "")),
        "facebook":  post_facebook(fb_caption),
        "instagram": post_instagram(ig_caption),
    }

    ok = sum(results.values())
    print(f"✓ Posted {ok}/{len(results)} platforms: {results}")
    if ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    run()
