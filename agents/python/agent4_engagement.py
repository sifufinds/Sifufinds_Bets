"""
Agent 4 — Community Engagement
Generates authentic comments and engagement actions for African betting communities.
Called by GitHub Actions 4x per day.

Note: This agent GENERATES the comments and logs them.
Actual posting to Facebook/Instagram/Telegram requires the APIs configured in agent3.
For Reddit and Quora, see the manual posting notes at the bottom.
"""
import json
import sys
import os
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from llm import ask
from config import (
    TELEGRAM_BOT_TOKEN, FACEBOOK_PAGE_ACCESS_TOKEN,
    INSTAGRAM_ACCOUNT_ID, SITE_URL,
)
from utils.football_api import get_todays_matches
from utils.logger import log

SYSTEM_PROMPT = """You are the Community Engagement specialist for SifuFinds (sifufinds.com), Africa's #1 betting comparison site.

Your job: write authentic, value-driven comments for African betting communities. You sound like a fellow bettor who genuinely uses SifuFinds — not a corporate account.

TONE: Street-smart, African, conversational. Use phrases like "Guy", "bro", "my guy", "eish", "sawa", "sharp", "na" naturally. Short and punchy. Max 2-3 sentences per comment.

NEVER: Hard-sell, promise guaranteed wins, repeat the same comment, sound robotic.

ALWAYS: Add genuine value first, then soft-mention SifuFinds.

COMMENT TYPES:
A - Value-add: Answer a question with comparison data, mention sifufinds.com as the tool you used
B - Promotional: Amplify a bookmaker's own post, point to SifuFinds for the full comparison
C - Expert tip: Add match insight, reference sifufinds.com/tips/ for full analysis
D - Follow invite: Invite to SifuFinds Telegram channel

Return ONLY valid JSON:
{
  "comments": [
    {
      "type": "A|B|C|D",
      "target": "description of where to post this (e.g., 'Bet9ja Facebook post about AFCON', 'Nigerian betting Facebook group', 'Sportpesa Instagram promo post')",
      "platform": "facebook|instagram|telegram|reddit|quora",
      "text": "the exact comment text"
    }
  ],
  "telegram_group_messages": [
    {
      "group_type": "African sports tips group",
      "text": "message text"
    }
  ],
  "quora_answer": {
    "question": "relevant unanswered question about African betting",
    "answer": "150-200 word authoritative answer mentioning sifufinds.com"
  },
  "follow_accounts": [
    "description of account type to follow for growth"
  ]
}"""


def post_to_telegram_group(group_id: str, message: str) -> bool:
    """Post to a Telegram group (not just your channel)."""
    if not TELEGRAM_BOT_TOKEN or not group_id:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": group_id,
        "text": message,
        "parse_mode": "HTML",
    }, timeout=15)
    return r.status_code == 200


def comment_on_facebook_post(post_id: str, comment: str) -> bool:
    """Comment on a specific Facebook post."""
    if not FACEBOOK_PAGE_ACCESS_TOKEN or not post_id:
        return False
    url = f"https://graph.facebook.com/v19.0/{post_id}/comments"
    r = requests.post(url, data={
        "message": comment,
        "access_token": FACEBOOK_PAGE_ACCESS_TOKEN,
    }, timeout=15)
    return r.status_code == 200


def run():
    log("agent4", "start", "running")

    matches = get_todays_matches()
    hour = datetime.now(timezone.utc).hour

    # Vary engagement focus by time of day
    if hour < 8:
        focus = "early morning — focus on overnight match results and upcoming fixtures"
    elif hour < 14:
        focus = "midday — focus on today's best odds and upcoming afternoon matches"
    elif hour < 20:
        focus = "evening — focus on match previews and tip sharing before kick-off"
    else:
        focus = "night — focus on live match engagement and late-night casino promos"

    user_message = f"""Generate engagement content for this session.

Time focus: {focus}
Today's matches: {matches}
Site: {SITE_URL}

Target these communities:
- Bet9ja Facebook page (Nigeria)
- Sportpesa Facebook page (Kenya)
- Hollywoodbets Instagram (South Africa)
- African Sports Betting Facebook groups
- Telegram sports tips groups
- One Quora answer about African betting

Generate 5 unique comments (no repetition), 2 Telegram group messages, and 1 Quora answer.
Return only valid JSON."""

    try:
        raw = ask(SYSTEM_PROMPT, user_message)
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(raw)

        # Save engagement content to log for review
        output_path = os.path.join(os.path.dirname(__file__), "engagement_queue.json")
        existing = []
        if os.path.exists(output_path):
            with open(output_path) as f:
                try:
                    existing = json.load(f)
                except Exception:
                    existing = []

        entry = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "focus": focus,
            "content": result,
        }
        existing.append(entry)
        existing = existing[-100:]  # Keep last 100 sessions

        with open(output_path, "w") as f:
            json.dump(existing, f, indent=2)

        # Post Telegram group messages to configured groups
        # Add your Telegram group IDs to this list after manually joining them
        telegram_groups = [
            # "-100123456789",  # e.g., African Betting Tips group
            # "-100987654321",  # e.g., Nigeria Football Bets group
        ]

        tg_messages = result.get("telegram_group_messages", [])
        for i, group_id in enumerate(telegram_groups):
            if i < len(tg_messages):
                success = post_to_telegram_group(group_id, tg_messages[i]["text"])
                log("agent4", f"telegram_group_{group_id}", "success" if success else "failed")

        comments = result.get("comments", [])
        log("agent4", "comments_generated", "success", f"{len(comments)} comments ready")

        print(f"✓ Generated {len(comments)} engagement comments")
        print(f"✓ {len(tg_messages)} Telegram group messages")
        if result.get("quora_answer"):
            print(f"✓ Quora answer: {result['quora_answer'].get('question', '')[:60]}...")

        # Print comments for manual review / Facebook posting
        print("\n── COMMENTS READY TO POST ──")
        for c in comments:
            print(f"\n[{c['type']}] {c['platform'].upper()} → {c['target']}")
            print(f"   {c['text']}")

        if result.get("quora_answer"):
            print(f"\n── QUORA ANSWER ──")
            print(f"Q: {result['quora_answer']['question']}")
            print(f"A: {result['quora_answer']['answer'][:200]}...")

    except json.JSONDecodeError as e:
        log("agent4", "parse_error", "failed", str(e))
        print(f"✗ JSON parse error: {e}")
        sys.exit(1)
    except Exception as e:
        log("agent4", "error", "failed", str(e))
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()

# ── Manual posting guide (for Reddit + Quora) ─────────────────────────────────
#
# Reddit:  Read engagement_queue.json → post comments manually to:
#          r/AfricanFootball, r/sportsbetting (Africa match threads)
#          Reddit bans API bots aggressively — manual posting is safer.
#
# Quora:   Read the quora_answer in engagement_queue.json → post manually at
#          quora.com. Search for the generated question and post the answer.
#          10-15 min work per week, not per day.
#
# Facebook comments: The Graph API requires posting as the Page, not as a user.
#          To comment on OTHER pages' posts, you need a user access token
#          (not a page token). This is a Meta restriction. Best approach:
#          Read the comments from engagement_queue.json and post manually once/day.
#          Takes ~15 mins and looks more authentic anyway.
