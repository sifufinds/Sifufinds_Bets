#!/usr/bin/env python3
"""
SifuFinds Reddit Post Agent
Posts about free tools and content to relevant subreddits to drive
backlinks, traffic and brand awareness for African bettors.

Requires GitHub secrets:
  REDDIT_CLIENT_ID      — from https://www.reddit.com/prefs/apps
  REDDIT_CLIENT_SECRET  — from the same app
  REDDIT_USERNAME       — your Reddit account username
  REDDIT_PASSWORD       — your Reddit account password
  REDDIT_USER_AGENT     — e.g. "SifuFinds:v1.0 (by u/sifufinds)"

Install: pip install praw
Usage:
  python agent_reddit_posts.py              # auto-rotate next queued post
  python agent_reddit_posts.py --dry-run    # preview without posting
  python agent_reddit_posts.py --mode tool  # force tool post
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

ROOT       = Path(__file__).resolve().parents[2]
STATE_FILE = Path(__file__).parent / "reddit_state.json"
SITE_URL   = "https://sifufinds.com"

# Hours to wait before posting to the same subreddit again
SUBREDDIT_COOLDOWN_HOURS = 72

# ── SUBREDDIT TARGETS ─────────────────────────────────────────────────────────
# Ordered by most relevant first.
# "flair" is optional — only set if the sub requires/benefits from post flair.

SUBREDDITS = [
    {
        "name": "sportsbetting",
        "min_karma": 50,          # most subs require some karma
        "flair": None,
        "topics": ["tool", "tips"],
    },
    {
        "name": "Kenya",
        "min_karma": 0,
        "flair": None,
        "topics": ["tool", "content"],
    },
    {
        "name": "Nigeria",
        "min_karma": 0,
        "flair": None,
        "topics": ["tool", "content"],
    },
    {
        "name": "SouthAfrica",
        "min_karma": 0,
        "flair": None,
        "topics": ["tool"],
    },
    {
        "name": "ghana",
        "min_karma": 0,
        "flair": None,
        "topics": ["tool", "content"],
    },
    {
        "name": "africa",
        "min_karma": 0,
        "flair": None,
        "topics": ["content"],
    },
    {
        "name": "soccer",
        "min_karma": 50,
        "flair": None,
        "topics": ["tips"],
    },
    {
        "name": "bettingadvice",
        "min_karma": 20,
        "flair": None,
        "topics": ["tool", "tips"],
    },
    {
        "name": "AfricanFootball",
        "min_karma": 0,
        "flair": None,
        "topics": ["tips", "content"],
    },
]

# ── POST TEMPLATES ─────────────────────────────────────────────────────────────

POSTS = {
    "tool_parlay": {
        "topic": "tool",
        "title": "I built a free parlay/accumulator calculator for African bettors (supports ₦, KSh, GH₵, R)",
        "body": (
            "Hey everyone,\n\n"
            "I built a free parlay calculator specifically for bettors in Africa. "
            "It supports the local currencies most sites don't bother with — Nigerian Naira (₦), "
            "Kenyan Shilling (KSh), Ghanaian Cedi (GH₵) and South African Rand (R).\n\n"
            "**What it does:**\n"
            "- Add up to 20 legs\n"
            "- Shows combined decimal odds instantly\n"
            "- Calculates total payout and profit in your currency\n"
            "- Works with decimal, fractional, and American odds input\n"
            "- No signup required, no ads\n\n"
            "Works with Bet9ja, Betway, 1xBet, SportyBet, Hollywoodbets — whatever "
            "odds format your bookmaker shows.\n\n"
            f"Link: {SITE_URL}/tools/parlay-calculator/\n\n"
            "Happy to take feedback or add features. "
            "Let me know if there's a currency or bookmaker I should add."
        ),
        "subreddits": ["sportsbetting", "Kenya", "Nigeria", "ghana", "bettingadvice"],
    },
    "tool_odds": {
        "topic": "tool",
        "title": "Free odds converter for African bookmakers — decimal, fractional, American + payout calculator",
        "body": (
            "Built this for African bettors who switch between bookmakers that show different odds formats.\n\n"
            "Bet9ja shows decimal (2.50). Some European sites show fractional (3/2). "
            "American sites use moneyline (+150). They're all the same bet — just different notation.\n\n"
            "**Features:**\n"
            "- Convert between all three formats instantly\n"
            "- Payout calculator in ₦, KSh, GH₵, R, or USD\n"
            "- Quick reference table for the most common odds\n"
            "- No login needed\n\n"
            f"Link: {SITE_URL}/tools/odds-calculator/\n\n"
            "Also built a parlay calculator if anyone wants that: "
            f"{SITE_URL}/tools/parlay-calculator/"
        ),
        "subreddits": ["sportsbetting", "Nigeria", "SouthAfrica", "bettingadvice"],
    },
    "content_nigeria": {
        "topic": "content",
        "title": "Bet9ja vs SportyBet 2026 — which is actually better for Nigerian bettors?",
        "body": (
            "Been comparing these two for a while and wanted to share what I found.\n\n"
            "**Welcome Bonus:**\n"
            "- SportyBet: 300% up to ₦300,000 (higher)\n"
            "- Bet9ja: 170% up to ₦100,000\n\n"
            "**Odds Quality:**\n"
            "- Bet9ja wins on African football and live markets\n"
            "- SportyBet is better for mainstream EPL/UCL matches\n\n"
            "**Withdrawals:**\n"
            "- SportyBet: usually under 5 minutes to OPay/PalmPay\n"
            "- Bet9ja: 24 hrs average, can be slower on weekends\n\n"
            "**App:**\n"
            "- SportyBet's app is cleaner and faster\n"
            "- Bet9ja has more markets and live betting options\n\n"
            "Most serious Nigerian bettors hold accounts on both and pick the better "
            "odds per match. That's honestly the optimal play.\n\n"
            f"Full comparison with current bonuses: {SITE_URL}/countries/nigeria/\n\n"
            "What's everyone's experience? Any other bookmakers worth adding to this comparison?"
        ),
        "subreddits": ["Nigeria", "sportsbetting", "AfricanFootball"],
    },
    "content_kenya": {
        "topic": "content",
        "title": "Best betting sites in Kenya 2026 — M-Pesa deposits, licensed by BCLB",
        "body": (
            "Putting together everything I know about the Kenyan betting market right now.\n\n"
            "**Top licensed sites (BCLB approved):**\n"
            "1. Betway Kenya — best withdrawal speed via M-Pesa, usually instant\n"
            "2. 1xBet Kenya — highest odds, widest market selection\n"
            "3. SportyBet Kenya — best welcome bonus (200% first deposit)\n"
            "4. Melbet Kenya — good for live betting\n\n"
            "**Payment reality:**\n"
            "M-Pesa is the standard for deposits AND withdrawals. "
            "Almost every site supports it. Airtel Money is accepted by most too.\n\n"
            "**What to watch:**\n"
            "Withholding tax on winnings is 20% in Kenya — factor this into your "
            "expected value calculations. Some sites show pre-tax, others post-tax.\n\n"
            f"Full breakdown with current bonuses: {SITE_URL}/countries/kenya/\n\n"
            "Any Kenyan bettors here with recent experience on these sites?"
        ),
        "subreddits": ["Kenya", "africa", "AfricanFootball"],
    },
    "content_wc2026": {
        "topic": "content",
        "title": "WC2026 African betting guide — 9 African teams, biggest African betting event ever",
        "body": (
            "With 9 African teams in WC2026 (record representation), this is the biggest "
            "betting event African bookmakers have ever seen.\n\n"
            "**African teams qualified:**\n"
            "Morocco 🇲🇦 | Nigeria 🇳🇬 | Senegal 🇸🇳 | Cameroon 🇨🇲 | "
            "Egypt 🇪🇬 | Ghana 🇬🇭 | Ivory Coast 🇨🇮 | South Africa 🇿🇦 | DR Congo 🇨🇩\n\n"
            "**Best odds by bookmaker:**\n"
            "- 1xBet: best World Cup odds overall, plus accumulator boosts\n"
            "- Bet9ja: accumulator insurance on 5+ fold bets\n"
            "- Betway: early cash-out available on most WC markets\n\n"
            "**Tips for WC betting in Africa:**\n"
            "- Compare odds across sites before placing — can be 15-20% difference\n"
            "- Claim welcome bonuses NOW before the tournament starts (June 11)\n"
            "- Check withdrawal limits — some sites cap WC winnings\n\n"
            f"Compare all current WC2026 bonuses: {SITE_URL}\n\n"
            "Which African team are you backing?"
        ),
        "subreddits": ["AfricanFootball", "soccer", "africa", "sportsbetting"],
    },
}

# ── STATE ──────────────────────────────────────────────────────────────────────

def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"posted": [], "subreddit_last_posted": {}, "post_queue_index": 0}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _sub_on_cooldown(sub: str, state: dict) -> bool:
    last = state.get("subreddit_last_posted", {}).get(sub)
    if not last:
        return False
    elapsed = datetime.now(timezone.utc) - datetime.fromisoformat(last)
    return elapsed < timedelta(hours=SUBREDDIT_COOLDOWN_HOURS)


# ── POSTING ────────────────────────────────────────────────────────────────────

def _post_to_reddit(subreddit: str, title: str, body: str, dry_run: bool = False) -> bool:
    try:
        import praw
    except ImportError:
        print("✗ praw not installed. Run: pip install praw")
        return False

    client_id     = os.getenv("REDDIT_CLIENT_ID", "")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
    username      = os.getenv("REDDIT_USERNAME", "")
    password      = os.getenv("REDDIT_PASSWORD", "")
    user_agent    = os.getenv("REDDIT_USER_AGENT", f"SifuFinds:v1.0 (by u/{username})")

    if not all([client_id, client_secret, username, password]):
        print("✗ Reddit credentials missing. Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD")
        return False

    if dry_run:
        print(f"\n[DRY RUN] Would post to r/{subreddit}:")
        print(f"  Title: {title}")
        print(f"  Body preview: {body[:200]}...")
        return True

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent=user_agent,
        )
        sub = reddit.subreddit(subreddit)
        submission = sub.submit(title=title, selftext=body)
        print(f"  ✓ Posted to r/{subreddit}: https://reddit.com{submission.permalink}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to post to r/{subreddit}: {e}")
        return False


def run(mode: str = "auto", dry_run: bool = False) -> None:
    state = _load_state()
    now   = datetime.now(timezone.utc).isoformat()

    # Pick next post from queue
    post_keys = list(POSTS.keys())
    if mode == "auto":
        idx  = state.get("post_queue_index", 0) % len(post_keys)
        key  = post_keys[idx]
        state["post_queue_index"] = (idx + 1) % len(post_keys)
    elif mode in POSTS:
        key = mode
    else:
        # mode is a topic filter — pick first post matching that topic
        matches = [k for k, v in POSTS.items() if v["topic"] == mode]
        if not matches:
            print(f"✗ No posts for topic: {mode}")
            sys.exit(1)
        idx   = state.get("post_queue_index", 0) % len(matches)
        key   = matches[idx]
        state["post_queue_index"] = (idx + 1) % len(matches)

    post = POSTS[key]
    print(f"Selected post: {key}")

    posted_count = 0
    for sub_name in post["subreddits"]:
        if _sub_on_cooldown(sub_name, state):
            print(f"  ⏳ r/{sub_name} — cooldown active, skipping")
            continue

        success = _post_to_reddit(sub_name, post["title"], post["body"], dry_run=dry_run)

        if success and not dry_run:
            state.setdefault("subreddit_last_posted", {})[sub_name] = now
            state.setdefault("posted", []).append({
                "post_key": key,
                "subreddit": sub_name,
                "title": post["title"],
                "ts": now,
            })
            posted_count += 1

        # Only post to one subreddit per run to avoid spam detection
        if success:
            break

    _save_state(state)
    print(f"\n[DONE] Posted to {posted_count} subreddit(s)")
    if posted_count == 0 and not dry_run:
        print("  All subreddits on cooldown or credentials missing.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Reddit Post Agent")
    parser.add_argument(
        "--mode",
        default="auto",
        help="auto | tool | content | tips | or a specific post key",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    args = parser.parse_args()
    run(mode=args.mode, dry_run=args.dry_run)
