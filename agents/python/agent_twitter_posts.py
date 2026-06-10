"""
X (Twitter) Posts Agent — SifuFinds
Posts rotating content to @SifuFinds: bookmaker offers, blog news, and betting tips.

Requires GitHub secrets (preferred):
  TWITTER_SESSION — base64-encoded Playwright storage state (cookies + localStorage)
                    generated once locally by: python save_twitter_session.py

Fallback secrets (only used if session is missing/expired):
  X_USERNAME / X_PASSWORD / X_EMAIL

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
    """Truncate the last line of a tweet that exceeds the limit."""
    if _tweet_len(text) <= limit:
        return text
    import re
    # Truncate preserving newlines: shorten the last line
    lines = text.split("\n")
    while lines and _tweet_len("\n".join(lines)) > limit:
        last = lines[-1]
        if not last:
            lines.pop()
            continue
        words = last.split()
        if len(words) <= 1:
            lines.pop()
        else:
            lines[-1] = " ".join(words[:-1]) + "..."
    return "\n".join(lines)


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
    tweet = (
        f"🔥 TODAY'S DEAL — {brand['name']} {brand['flag']}\n"
        f"💰 {brand['welcome']}\n"
        f"✨ {brand['highlight']}\n\n"
        f"Min deposit: {brand['min_deposit']} | {brand['licence']}\n\n"
        f"👉 Claim → {brand['url']}\n\n"
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


# ── PLAYWRIGHT POSTER ────────────────────────────────────────────────────────

async def _stealth_context(browser):
    """Create a browser context that masks headless/automation signals."""
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
        locale="en-US",
        timezone_id="America/New_York",
    )
    # Mask the most common automation detection signals
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        window.chrome = {runtime: {}};
    """)
    return context


async def _login_x(page) -> None:
    """Handle X.com login including the optional account-confirmation step."""
    from playwright.async_api import TimeoutError as PWTimeout

    await page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=30_000)
    await page.wait_for_timeout(2_000)

    # Step 1: username
    await page.wait_for_selector('input[autocomplete="username"]', timeout=15_000)
    await page.fill('input[autocomplete="username"]', os.environ["X_USERNAME"])
    await page.wait_for_timeout(500)
    await page.get_by_role("button", name="Next").click()
    await page.wait_for_timeout(2_000)

    # Step 2: unusual-activity confirmation (email/phone)
    try:
        confirm = page.locator('input[data-testid="ocfEnterTextTextInput"]')
        await confirm.wait_for(timeout=3_000)
        await confirm.fill(os.getenv("X_EMAIL", os.environ["X_USERNAME"]))
        await page.get_by_role("button", name="Next").click()
        await page.wait_for_timeout(2_000)
    except PWTimeout:
        pass

    # Step 3: password
    await page.wait_for_selector('input[name="password"]', timeout=10_000)
    await page.fill('input[name="password"]', os.environ["X_PASSWORD"])
    await page.wait_for_timeout(500)
    await page.get_by_role("button", name="Log in").click()

    # Wait up to 20s to land on a non-login page
    await page.wait_for_timeout(3_000)
    for _ in range(17):
        if "login" not in page.url and "flow" not in page.url:
            break
        await page.wait_for_timeout(1_000)

    print(f"✓ Login complete — URL: {page.url}")


async def _post_playwright(text: str) -> bool:
    import base64
    import tempfile
    from playwright.async_api import async_playwright, TimeoutError as PWTimeout

    session_b64 = os.getenv("TWITTER_SESSION", "").strip()
    username    = os.getenv("X_USERNAME", "").strip()
    password    = os.getenv("X_PASSWORD", "").strip()

    if not session_b64 and (not username or not password):
        print("✗ Set TWITTER_SESSION or X_USERNAME+X_PASSWORD")
        return False

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        if session_b64:
            # Decode the pre-saved session — no login flow, no bot-detection trigger
            state_json = base64.b64decode(session_b64.encode()).decode()
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            tmp.write(state_json)
            tmp.flush()
            tmp.close()
            context = await browser.new_context(
                storage_state=tmp.name,
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
                locale="en-US",
                timezone_id="America/New_York",
            )
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                window.chrome = {runtime: {}};
            """)
            Path(tmp.name).unlink(missing_ok=True)
        else:
            context = await _stealth_context(browser)

        page = await context.new_page()
        await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(3_000)
        print(f"Initial URL: {page.url}")

        # Fall back to login if session is missing or expired
        if page.url.rstrip("/") != "https://x.com/home":
            if username and password:
                print("Session invalid — falling back to login flow...")
                await _login_x(page)
                await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=20_000)
                await page.wait_for_timeout(3_000)
                print(f"Post-login URL: {page.url}")
            else:
                raise Exception(f"Not authenticated, no credentials set — URL: {page.url}")

        if page.url.rstrip("/") != "https://x.com/home":
            raise Exception(f"Authentication failed — URL: {page.url}")

        # Click the compose button in the left sidebar
        compose_btn = page.locator('[data-testid="SideNav_NewTweet_Button"]')
        await compose_btn.wait_for(state="visible", timeout=15_000)
        await compose_btn.click()
        await page.wait_for_timeout(1_000)

        # Find the tweet textarea
        textarea = page.locator(
            '[data-testid="tweetTextarea_0"], '
            'div[role="textbox"][contenteditable="true"]'
        ).first
        await textarea.wait_for(state="visible", timeout=15_000)
        await textarea.click()
        await page.keyboard.type(text, delay=25)
        await page.wait_for_timeout(800)

        # Click Post
        post_btn = page.locator(
            '[data-testid="tweetButton"], [data-testid="tweetButtonInline"]'
        ).first
        await post_btn.wait_for(state="visible", timeout=8_000)
        await post_btn.click()
        await page.wait_for_timeout(3_000)

        await context.close()
        await browser.close()
        print("✓ Tweet posted via browser")
        return True


def _post_playwright_sync(text: str) -> bool:
    import asyncio
    try:
        return asyncio.run(_post_playwright(text))
    except Exception as e:
        print(f"✗ Playwright error: {e}")
        return False


# ── TWITTER CLIENT ────────────────────────────────────────────────────────────

def _post_tweet(text: str, dry_run: bool = False) -> bool:
    if dry_run:
        print(f"\n{'─'*50}")
        print("DRY RUN — tweet preview:")
        print(text)
        print(f"\nChar count (approx): {_tweet_len(text)}")
        print(f"{'─'*50}\n")
        return True

    # Playwright path — preferred when session or credentials are set
    if os.getenv("TWITTER_SESSION") or (os.getenv("X_USERNAME") and os.getenv("X_PASSWORD")):
        print("Using Playwright browser poster...")
        return _post_playwright_sync(text)

    # Tweepy path (Twitter API v2) — requires paid Basic tier
    try:
        import tweepy
    except ImportError:
        print("✗ tweepy not installed — run: pip install tweepy")
        return False

    api_key             = os.getenv("TWITTER_API_KEY", "").strip()
    api_secret          = os.getenv("TWITTER_API_SECRET", "").strip()
    access_token        = os.getenv("TWITTER_ACCESS_TOKEN", "").strip()
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "").strip()

    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("✗ No posting credentials found (set X_USERNAME+X_PASSWORD or TWITTER_API_KEY)")
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
