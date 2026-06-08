"""
X (Twitter) Posts Agent — SifuFinds
Posts rotating content to @SifuFinds: bookmaker offers, blog news, and betting tips.

Requires GitHub secrets:
  TWITTER_API_KEY            — Consumer Key (app)
  TWITTER_API_SECRET         — Consumer Secret (app)
  TWITTER_ACCESS_TOKEN       — Access Token (@SifuFinds account)
  TWITTER_ACCESS_TOKEN_SECRET — Access Token Secret

Modes:
  python agent_twitter_posts.py --mode offer   # Bookmaker promo
  python agent_twitter_posts.py --mode news    # Latest blog post
  python agent_twitter_posts.py --mode tip     # Betting tips CTA
  python agent_twitter_posts.py --mode auto    # Rotate (default)
  python agent_twitter_posts.py --dry-run      # Preview without posting
"""
import argparse
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

# ── CONFIG ────────────────────────────────────────────────────────────────────

SITE_URL   = "https://sifufinds.com"
TIPS_URL   = "https://sifufinds.com/tips/"
BLOG_URL   = "https://sifufinds.com/blog/"
STATE_FILE = Path(__file__).parent / "twitter_state.json"
POSTS_PATH = Path(__file__).parent.parent.parent / "blog" / "posts.json"

BRAND_COOLDOWN_HOURS = 48
# Twitter wraps all URLs to t.co — always 23 chars in the character count
TWITTER_URL_LEN = 23
TWEET_MAX = 280

# Content-type rotation for --mode auto: news → offer → tip → offer
ROTATION = ["news", "offer", "tip", "offer"]

# ── AFFILIATE BRANDS ─────────────────────────────────────────────────────────

BRANDS = [
    {
        "name": "1xBet",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania", "Uganda", "Zambia"],
        "welcome": "300% First Deposit Bonus – Up to ₦1,200,000",
        "highlight": "Highest welcome bonus in Africa",
        "url": "https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97",
        "min_deposit": "₦100",
        "licence": "NLRC + BCLB",
        "hashtags": "#1xBet #Africa #SportsBetting #300Bonus",
    },
    {
        "name": "Melbet",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania", "Ethiopia"],
        "welcome": "200% First Deposit Bonus – Up to ₦480,000",
        "highlight": "150+ sports markets — widest range in Africa",
        "url": "https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559",
        "min_deposit": "₦100",
        "licence": "NLRC + BCLB",
        "hashtags": "#Melbet #Africa #200Bonus #SportsBetting",
    },
    {
        "name": "BetWinner",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania"],
        "welcome": "200% First Deposit Bonus – Up to ₦130,000",
        "highlight": "Easy 5x wagering — 40+ sports",
        "url": "https://bwredir.com/1Lvf?p=%2Fregistration%2F",
        "min_deposit": "₦400",
        "licence": "NLRC + BCLB",
        "hashtags": "#BetWinner #200Bonus #Africa #SportsBetting",
    },
    {
        "name": "HelaBet",
        "flag": "🇰🇪",
        "countries": ["Kenya"],
        "welcome": "100% Welcome Bonus – Up to KSh 5,000",
        "highlight": "Instant M-Pesa payouts — BCLB licensed",
        "url": "https://1212fghnna.com/L?tag=d_2204817m_52235c_&site=2204817&ad=52235",
        "min_deposit": "KSh 10",
        "licence": "BCLB",
        "hashtags": "#HelaBet #Kenya #MPesa #SportsBetting",
    },
    {
        "name": "Paripesa",
        "flag": "🌍",
        "countries": ["Nigeria", "Kenya", "Ghana", "Tanzania"],
        "welcome": "200% First Deposit Bonus – Up to ₦200,000",
        "highlight": "50+ sports, live streaming included",
        "url": "https://combodef.com/L?tag=d_2350859m_45569c_&site=2350859&ad=45569",
        "min_deposit": "₦100",
        "licence": "NLRC + BCLB",
        "hashtags": "#Paripesa #200Bonus #Africa #LiveBetting",
    },
]

# Category → emoji + Twitter hashtag
CATEGORY_META = {
    "football":    {"icon": "⚽", "tag": "#Football"},
    "sportnews":   {"icon": "🗞️", "tag": "#SportNews"},
    "betting":     {"icon": "📊", "tag": "#BettingTips"},
    "igaming":     {"icon": "🎮", "tag": "#iGaming"},
    "basketball":  {"icon": "🏀", "tag": "#Basketball"},
    "tennis":      {"icon": "🎾", "tag": "#Tennis"},
    "cricket":     {"icon": "🏏", "tag": "#Cricket"},
    "rugby":       {"icon": "🏉", "tag": "#Rugby"},
    "boxing":      {"icon": "🥊", "tag": "#Boxing"},
    "f1":          {"icon": "🏎️", "tag": "#F1"},
    "worldcup2026":{"icon": "🏆", "tag": "#WorldCup2026"},
}

# ── STATE ─────────────────────────────────────────────────────────────────────

def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {
        "rotation_index": 0,
        "last_brand_index": -1,
        "brand_last_posted": {},
        "tweeted_slugs": [],
    }


def _save_state(state: dict) -> None:
    # Keep tweeted_slugs bounded
    state["tweeted_slugs"] = state.get("tweeted_slugs", [])[-200:]
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── TWEET LENGTH HELPERS ──────────────────────────────────────────────────────

def _tweet_len(text: str) -> int:
    """Approximate Twitter character count: URLs = 23, other chars as-is."""
    import re
    url_pattern = re.compile(r'https?://\S+')
    count = 0
    last = 0
    for m in url_pattern.finditer(text):
        count += len(text[last:m.start()])
        count += TWITTER_URL_LEN
        last = m.end()
    count += len(text[last:])
    return count


def _trim_to_limit(text: str, limit: int = TWEET_MAX) -> str:
    """Hard-truncate a tweet that exceeds the limit, breaking at a word boundary."""
    if _tweet_len(text) <= limit:
        return text
    words = text.split()
    result = []
    count = 0
    for word in words:
        import re
        word_len = TWITTER_URL_LEN if re.match(r'https?://', word) else len(word)
        if count + word_len + (1 if result else 0) > limit - 3:
            result.append("...")
            break
        if result:
            count += 1
        count += word_len
        result.append(word)
    return " ".join(result)


# ── OFFER MODE ────────────────────────────────────────────────────────────────

def _next_brand(state: dict, force: bool = False) -> dict | None:
    now = datetime.now(timezone.utc)
    brand_last = state.get("brand_last_posted", {})
    n = len(BRANDS)
    start = (state.get("last_brand_index", -1) + 1) % n

    for offset in range(n):
        idx = (start + offset) % n
        brand = BRANDS[idx]
        last_str = brand_last.get(brand["name"])
        if force or not last_str:
            state["last_brand_index"] = idx
            return brand
        last_dt = datetime.fromisoformat(last_str)
        if (now - last_dt) >= timedelta(hours=BRAND_COOLDOWN_HOURS):
            state["last_brand_index"] = idx
            return brand

    # All on cooldown — post the oldest
    oldest = min(BRANDS, key=lambda b: brand_last.get(b["name"], "2000-01-01T00:00:00+00:00"))
    state["last_brand_index"] = BRANDS.index(oldest)
    return oldest


def _build_offer_tweet(brand: dict) -> str:
    countries = " · ".join(brand["countries"][:4])
    if len(brand["countries"]) > 4:
        countries += f" +{len(brand['countries']) - 4} more"

    tweet = (
        f"🔥 {brand['name']} {brand['flag']} — DEAL OF THE DAY\n"
        f"💰 {brand['welcome']}\n"
        f"✨ {brand['highlight']}\n\n"
        f"Min deposit: {brand['min_deposit']} | {brand['licence']}\n"
        f"🌍 {countries}\n\n"
        f"👉 Claim → {brand['url']}\n"
        f"📊 Compare all → {SITE_URL}\n\n"
        f"{brand['hashtags']} #SifuFinds #AfricanBetting"
    )
    return _trim_to_limit(tweet)


# ── NEWS MODE ─────────────────────────────────────────────────────────────────

def _load_posts() -> list[dict]:
    if not POSTS_PATH.exists():
        return []
    try:
        data = json.loads(POSTS_PATH.read_text())
        posts = data.get("posts", [])
        # Sort newest first
        return sorted(posts, key=lambda p: p.get("published_at", ""), reverse=True)
    except Exception:
        return []


def _pick_unposted(posts: list[dict], tweeted_slugs: list[str]) -> dict | None:
    for post in posts:
        if post.get("slug") not in tweeted_slugs:
            return post
    # All posted — return the newest anyway
    return posts[0] if posts else None


def _build_news_tweet(post: dict) -> str:
    cat = post.get("category", "football")
    meta = CATEGORY_META.get(cat, {"icon": "📰", "tag": f"#{cat.capitalize()}"})
    icon = meta["icon"]
    tag = meta["tag"]

    title = post.get("title", "")
    excerpt = post.get("excerpt", "")
    slug = post.get("slug", "")
    post_url = f"{BLOG_URL}{slug}/"

    # Budget: title ≤60, excerpt ≤100, rest fixed
    title_short = title[:57] + "..." if len(title) > 60 else title
    excerpt_short = excerpt[:97] + "..." if len(excerpt) > 100 else excerpt

    tweet = (
        f"{icon} {title_short}\n\n"
        f"{excerpt_short}\n\n"
        f"Read more 👉 {post_url}\n\n"
        f"{tag} #SifuFinds #AfricanBetting"
    )
    return _trim_to_limit(tweet)


# ── TIP MODE ─────────────────────────────────────────────────────────────────

_TIP_TEMPLATES = [
    (
        "⚽ TODAY'S FREE TIPS — African Leagues\n\n"
        "Expert picks across NPFL 🇳🇬 · KPL 🇰🇪 · PSL 🇿🇦 · GFA 🇬🇭\n\n"
        "Daily analysis from our team of tipsters.\n"
        "Bet responsibly. Free picks, no signup.\n\n"
        f"👉 Get tips → {TIPS_URL}\n\n"
        "#BettingTips #FootballTips #SifuFinds #AfricanBetting #FreeTips"
    ),
    (
        "📊 SMART BETTING — Today's Value Picks\n\n"
        "Odds from Bet9ja · 1xBet · Betway · SportyBet\n"
        "African football + Premier League analysis\n\n"
        "Our tips are free. Your winnings are yours.\n\n"
        f"👉 {TIPS_URL}\n\n"
        "#BettingPicks #SportsBetting #SifuFinds #ValueBets #AfricanBetting"
    ),
    (
        "🏆 WEEKEND ACCA PICKS — Free for All\n\n"
        "Top accumulator selections from our analysts:\n"
        "⚽ Premier League | 🌍 CAF CL | 🇳🇬 NPFL\n\n"
        "Compare odds, pick your best price.\n\n"
        f"👉 See picks → {TIPS_URL}\n\n"
        "#Accumulator #BettingTips #SifuFinds #WeekendBetting #Football"
    ),
    (
        "💡 BETTING EDUCATION — Bet Smarter\n\n"
        "Understand: value bets · Asian handicap · BTTS\n"
        "Learn to read odds like a pro.\n\n"
        "Free guides for African bettors on SifuFinds.\n\n"
        f"👉 {SITE_URL}\n\n"
        "#BettingEducation #SmartBetting #SifuFinds #AfricanBetting #OddsGuide"
    ),
]


def _build_tip_tweet(state: dict) -> str:
    idx = state.get("tip_template_index", 0) % len(_TIP_TEMPLATES)
    state["tip_template_index"] = (idx + 1) % len(_TIP_TEMPLATES)
    return _trim_to_limit(_TIP_TEMPLATES[idx])


# ── TWITTER CLIENT ────────────────────────────────────────────────────────────

def _post_tweet(text: str, dry_run: bool = False) -> bool:
    if dry_run:
        print(f"\n{'─'*50}")
        print("DRY RUN — tweet preview:")
        print(text)
        print(f"\nChar count (approx): {_tweet_len(text)}")
        print(f"{'─'*50}\n")
        return True

    try:
        import tweepy
    except ImportError:
        print("✗ tweepy not installed — run: pip install tweepy")
        return False

    api_key    = os.getenv("TWITTER_API_KEY", "").strip()
    api_secret = os.getenv("TWITTER_API_SECRET", "").strip()
    access_token        = os.getenv("TWITTER_ACCESS_TOKEN", "").strip()
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "").strip()

    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("✗ Missing Twitter credentials in environment")
        return False

    try:
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )
        response = client.create_tweet(text=text)
        tweet_id = response.data["id"]
        print(f"✓ Tweet posted: https://x.com/SifuFinds/status/{tweet_id}")
        return True
    except Exception as e:
        print(f"✗ Twitter API error: {e}")
        return False


# ── MAIN ──────────────────────────────────────────────────────────────────────

def run(mode: str = "auto", dry_run: bool = False, force: bool = False) -> None:
    log("twitter", "start", "running", mode)
    state = _load_state()

    # Resolve auto → concrete mode from rotation
    if mode == "auto":
        idx = state.get("rotation_index", 0) % len(ROTATION)
        mode = ROTATION[idx]
        state["rotation_index"] = (idx + 1) % len(ROTATION)
        print(f"Auto mode → selected: {mode}")

    if mode == "offer":
        brand = _next_brand(state, force=force)
        if not brand:
            print("✗ No brands available")
            sys.exit(1)
        print(f"📣 Posting offer for: {brand['name']}")
        tweet = _build_offer_tweet(brand)

    elif mode == "news":
        posts = _load_posts()
        if not posts:
            print("No blog posts found — falling back to tip mode")
            mode = "tip"
            tweet = _build_tip_tweet(state)
        else:
            tweeted = state.get("tweeted_slugs", [])
            post = _pick_unposted(posts, tweeted)
            print(f"📰 Posting blog news: {post['title'][:60]}")
            tweet = _build_news_tweet(post)

    elif mode == "tip":
        print("💡 Posting betting tip")
        tweet = _build_tip_tweet(state)

    else:
        print(f"✗ Unknown mode: {mode}")
        sys.exit(1)

    success = _post_tweet(tweet, dry_run=dry_run)

    if success and not dry_run:
        now_iso = datetime.now(timezone.utc).isoformat()
        if mode == "offer":
            state.setdefault("brand_last_posted", {})[brand["name"]] = now_iso
        elif mode == "news" and post:
            state.setdefault("tweeted_slugs", []).append(post["slug"])
        _save_state(state)
        log("twitter", "post", "success", mode)
    elif not success:
        log("twitter", "post", "failed", mode)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds X (Twitter) Posts Agent")
    parser.add_argument(
        "--mode",
        choices=["auto", "offer", "news", "tip"],
        default="auto",
        help="Content type to post (default: auto-rotate)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview tweet without posting")
    parser.add_argument("--force", action="store_true", help="Ignore brand cooldown")
    args = parser.parse_args()
    run(mode=args.mode, dry_run=args.dry_run, force=args.force)
