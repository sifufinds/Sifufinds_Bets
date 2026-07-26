"""
agent_transfer_post.py — Live Transfer News Bot for SifuFinds

Watches the dedicated "transfers" news feeds (BBC/Guardian/Mirror + DuckDuckGo
+ Google News search, all via utils/news_fetcher.py), and when a genuinely new
transfer story appears:

  1. Writes a full researched blog article via agent_sports_blog.generate_post
     ("transfers" category — same anti-hallucination pipeline as every other
     blog category, grounded in the real, live headlines only).
  2. Extracts structured facts (player, clubs, fee, deal stage) from that
     article via a strict, grounded LLM extraction pass — never invents a
     name, club, or figure not already in the article text.
  3. Looks up a real, current photo of the named player via
     utils/player_photo.py's find_player_image(): sports news outlets and
     social platforms first (DuckDuckGo image search, per explicit product
     decision — see that module's docstring for the copyright tradeoff this
     carries vs. Wikimedia-only sourcing), then Wikipedia as a safe
     fallback. Every post gets an image one way or another: if neither tier
     finds a photo, Telegram and Facebook fall back to the per-post branded
     graphic already generated locally for the blog article (uploaded as a
     file, not a URL — see the "always has an image" note below). Instagram
     falls back to the site's generic branded card, since its API requires
     a public URL (see note).
  4. Posts a short "breaking news" bulletin (Fabrizio Romano / Sports Arena
     Africa style) to Telegram, Facebook, Instagram, and X, each linking back
     to the new blog article. Pure transfer news only — no bookmaker CTA, no
     bonus mention, no odds. This is a standalone news feed on its own
     30-minute schedule, independent of the site's betting-tips/bonus posting
     cadence (see agent_accumulator_post.py / agent_telegram_offers.py).

Why Instagram can't reuse the per-post graphic like Telegram/Facebook do:
Instagram's Content Publishing API only accepts a public image URL, not an
uploaded file. The per-post PNG is generated locally in this same run, before
the blog article is committed/pushed/deployed to sifufinds.com, so its URL
isn't live yet at the moment this script would need to hand it to Instagram —
posting it would 404. Telegram and Facebook don't have this problem because
both accept a direct file upload of the same local PNG, so they always get a
real per-post image; Instagram uses the sitewide generic card in that case.

Duplicate protection: skips the whole cycle (no blog post, no social post) if
the generated story's title closely matches one already in blog/posts.json —
the same recent-title check agent_sports_blog.py's own run() uses — so a 30
minute cron doesn't repost the same still-trending rumour every cycle.

Usage:
  python3 agent_transfer_post.py                # normal run (all 4 platforms)
  python3 agent_transfer_post.py --dry-run       # preview only, publish nothing
  python3 agent_transfer_post.py --no-twitter    # skip one platform
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

from llm import ask
from utils.logger import log
from utils.player_photo import find_player_image, looks_like_person_name
from agent_sports_blog import generate_post, load_posts, save_posts
from agent_telegram_offers import send_to_channel, send_photo_to_channel, SITE_URL
from agent3_social import post_facebook, post_instagram
from agent_twitter_posts import _post_tweet as post_twitter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GENERIC_SOCIAL_IMAGE = f"{SITE_URL}/assets/social-card.jpg"


def local_feature_image_path(post: dict) -> Path | None:
    """The per-post branded graphic already generated for the blog article
    (assets/og/{slug}.png), as a local filesystem path — used as the
    guaranteed image fallback for Telegram/Facebook when no Wikipedia photo
    exists for the named player. Returns None only if generation genuinely
    failed (see generate_blog_feature_image.py — never raises, so this is
    the sole failure path)."""
    feature_image = post.get("feature_image")
    if not feature_image:
        return None
    path = REPO_ROOT / feature_image.lstrip("/")
    return path if path.exists() else None


# Common footballing nations — never guessed, only used when the extraction
# step found an explicit nationality in the article text.
FLAG_MAP = {
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "France": "🇫🇷", "Spain": "🇪🇸", "Portugal": "🇵🇹",
    "Germany": "🇩🇪", "Italy": "🇮🇹", "Netherlands": "🇳🇱", "Belgium": "🇧🇪",
    "Brazil": "🇧🇷", "Argentina": "🇦🇷", "Uruguay": "🇺🇾", "Croatia": "🇭🇷",
    "Norway": "🇳🇴", "Sweden": "🇸🇪", "Denmark": "🇩🇰", "Poland": "🇵🇱",
    "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "Ireland": "🇮🇪", "Serbia": "🇷🇸",
    "Switzerland": "🇨🇭", "Austria": "🇦🇹", "Ukraine": "🇺🇦", "Turkey": "🇹🇷",
    "Nigeria": "🇳🇬", "Kenya": "🇰🇪", "South Africa": "🇿🇦", "Ghana": "🇬🇭",
    "Ivory Coast": "🇨🇮", "Côte d'Ivoire": "🇨🇮", "Cameroon": "🇨🇲", "Senegal": "🇸🇳",
    "Morocco": "🇲🇦", "Egypt": "🇪🇬", "Algeria": "🇩🇿", "Tunisia": "🇹🇳",
    "Mali": "🇲🇱", "Guinea": "🇬🇳", "DR Congo": "🇨🇩",
}


def flag_for(nationality: str | None) -> str:
    return FLAG_MAP.get((nationality or "").strip(), "")


# ── FACT EXTRACTION (strictly grounded — never invents) ──────────────────────

FACT_SYSTEM_PROMPT = """You extract structured facts from an already-published, real SifuFinds transfer news article.

RULES — NON-NEGOTIABLE:
- Only use facts explicitly present in the article text provided below
- Never invent a player name, club, fee, or deal stage that isn't in the text
- If a field isn't mentioned, use null — do not guess

Return ONLY this JSON, nothing else:
{
  "player": "player's full name exactly as named in the text, or null",
  "nationality": "player's nationality/home country ONLY if explicitly named in the text, or null",
  "from_club": "the club they are leaving or currently at, if named, or null",
  "to_club": "the club they are joining or linked with, if named, or null",
  "status": "the deal stage in 1-3 words only, e.g. confirmed / here we go / in talks / medical booked / bid rejected / rumour / loan move / fee agreed, or null",
  "fee": "transfer fee ONLY if a specific figure is stated in the text, or null",
  "headline_fact": "ONE punchy, self-contained sentence (max 25 words) stating the single most newsworthy fact from the article"
}"""


def _clean_json(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("```")[1]
        if s.startswith("json"):
            s = s[4:]
    return s.strip()


def _parse_json_object(s: str) -> dict:
    """Parse the first complete JSON object in the string, ignoring any
    trailing text the model tacks on after it (e.g. a stray closing remark)
    — plain json.loads() raises "Extra data" on that instead of just
    parsing the object it found."""
    s = _clean_json(s)
    obj, _ = json.JSONDecoder().raw_decode(s)
    return obj


def extract_transfer_facts(post: dict) -> dict:
    user_message = (
        f"HEADLINE: {post.get('title', '')}\n\n"
        f"EXCERPT: {post.get('excerpt', '')}\n\n"
        f"ARTICLE:\n{post.get('body', '')[:2500]}"
    )
    fallback = {
        "player": None, "nationality": None, "from_club": None, "to_club": None,
        "status": None, "fee": None, "headline_fact": post.get("excerpt", "")[:150],
    }
    try:
        raw = ask(FACT_SYSTEM_PROMPT, user_message)
        facts = _parse_json_object(raw)
        for key in fallback:
            facts.setdefault(key, fallback[key])
        return facts
    except Exception as e:
        print(f"  ⚠ Fact extraction failed, using excerpt fallback: {e}")
        return fallback


# ── BULLETIN BODY (shared core — pure news, no CTA/bonus/bookmaker content) ──

def _sentence_case(s: str) -> str:
    s = str(s).strip()
    return s[0].upper() + s[1:] if s else s


def build_bulletin_lines(facts: dict) -> list[str]:
    flag = flag_for(facts.get("nationality"))
    headline = facts.get("headline_fact") or facts.get("player") or "Transfer news"
    lines = [f"🚨 {(flag + ' ') if flag else ''}{headline}".strip(), ""]

    detail_bits = []
    if facts.get("from_club") and facts.get("to_club"):
        detail_bits.append(f"{facts['from_club']} → {facts['to_club']}")
    elif facts.get("to_club"):
        detail_bits.append(f"Linked with a move to {facts['to_club']}")
    elif facts.get("from_club"):
        detail_bits.append(f"Currently at {facts['from_club']}")
    if facts.get("fee"):
        detail_bits.append(f"Fee: {facts['fee']}")
    if facts.get("status"):
        detail_bits.append(f"Status: {_sentence_case(facts['status'])}")
    if detail_bits:
        lines.append(" · ".join(detail_bits))
        lines.append("")

    return lines


_REACT_PROMPT_TG = "💬 Tap a reaction below — 🔥 big move · 😳 shock · 🤔 not convinced"
_REACT_PROMPT_FB = "💬 React below — 🔥 if this is a good move, 😳 if it shocked you!"


def build_telegram_caption(facts: dict, post: dict) -> str:
    lines = build_bulletin_lines(facts)
    blog_url = f"{SITE_URL}/blog/{post['slug']}/"
    return (
        "\n".join(lines) +
        f"📰 Full story: <a href=\"{blog_url}\">{post['title']}</a>\n\n"
        f"{_REACT_PROMPT_TG}"
    )


def build_facebook_caption(facts: dict, post: dict) -> str:
    lines = build_bulletin_lines(facts)
    blog_url = f"{SITE_URL}/blog/{post['slug']}/"
    hashtags = "#TransferNews #SifuFinds #Football #TransferWindow"
    return (
        "\n".join(lines) +
        f"📰 Full story: {blog_url}\n\n"
        f"{_REACT_PROMPT_FB}\n\n"
        f"{hashtags}"
    )


def build_instagram_caption(facts: dict, post: dict) -> str:
    lines = build_bulletin_lines(facts)
    hashtags = "#TransferNews #SifuFinds #Football #TransferWindow #FootballNews"
    return (
        "\n".join(lines) +
        f"👉 Link in bio for the full story\n\n"
        f".\n.\n.\n{hashtags}"
    )


def _tweet_len(text: str) -> int:
    url_pattern = re.compile(r"https?://\S+")
    count, last = 0, 0
    for m in url_pattern.finditer(text):
        count += len(text[last:m.start()]) + 23
        last = m.end()
    count += len(text[last:])
    return count


def _trim_to_limit(text: str, limit: int = 280) -> str:
    lines = text.split("\n")
    while lines and _tweet_len("\n".join(lines)) > limit:
        words = lines[-1].split()
        if len(words) <= 1:
            lines.pop()
        else:
            lines[-1] = " ".join(words[:-1]) + "..."
    return "\n".join(lines)


def build_twitter_text(facts: dict, post: dict) -> str:
    lines = build_bulletin_lines(facts)
    blog_url = f"{SITE_URL}/blog/{post['slug']}/"
    tweet = (
        "\n".join(lines) +
        f"👉 {blog_url}\n\n"
        f"#TransferNews #SifuFinds"
    )
    return _trim_to_limit(tweet)


def _post_with_retry(platform: str, fn, *args, attempts: int = 3, delay: int = 8, **kwargs) -> bool:
    """Retry a single platform post a few times before giving up — covers
    transient failures (a network blip, a momentary rate limit) that would
    otherwise permanently drop that platform's copy of this specific story,
    since the next cron cycle posts whatever's freshest then, not a retry of
    this one. Not a substitute for fixing a genuinely dead credential (that
    still fails after every attempt and gets reported as a real failure by
    the caller), just insurance against the failures that resolve themselves
    a few seconds later."""
    for attempt in range(1, attempts + 1):
        try:
            if fn(*args, **kwargs):
                return True
        except Exception as e:
            print(f"  ⚠ {platform} attempt {attempt}/{attempts} raised: {e}")
        if attempt < attempts:
            print(f"  ⏳ {platform} attempt {attempt}/{attempts} failed — retrying in {delay}s...")
            time.sleep(delay)
    return False


# ── MAIN ──────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False, telegram: bool = True, facebook: bool = True,
        instagram: bool = True, twitter: bool = True) -> tuple[dict | None, dict[str, bool]]:
    log("transfer_post", "start", "running")

    existing = load_posts()
    recent_titles = {p["title"].lower()[:40] for p in existing[:40]}

    print("📡 Generating transfer news article from live feeds...")
    post = generate_post("transfers")
    if post is None:
        print("⚠ No fresh transfer news available this cycle — nothing to post.")
        log("transfer_post", "generate", "skipped", "no fresh news")
        return None, {}

    title_key = post["title"].lower()[:40]
    if title_key in recent_titles:
        print(f"⚠ Similar transfer story already published — skipping. ('{post['title']}')")
        log("transfer_post", "generate", "skipped", "duplicate title")
        return None, {}

    print(f"  ✓ '{post['title']}'")

    print("🔎 Extracting structured facts for the social bulletin...")
    facts = extract_transfer_facts(post)
    print(f"  ✓ player={facts.get('player')!r} status={facts.get('status')!r}")

    photo_url = None
    player = facts.get("player") or ""
    if player and looks_like_person_name(player):
        context_clubs = [facts.get("from_club"), facts.get("to_club")]
        photo_url = find_player_image(player, context_clubs=context_clubs)
        print(f"  {'✓ Found a real photo' if photo_url else '— No real photo found'} for {player!r}")

    # Guaranteed image: real Wikipedia player photo when found, otherwise the
    # per-post branded graphic already generated for the blog article
    # (uploaded as a local file for Telegram/Facebook — see module docstring
    # for why Instagram can't use this same fallback).
    local_image = None if photo_url else local_feature_image_path(post)
    tg_fb_image = photo_url or local_image
    print(f"  → Image for Telegram/Facebook: {'Wikipedia photo' if photo_url else ('branded graphic' if local_image else 'NONE — feature image generation failed')}")

    telegram_text = build_telegram_caption(facts, post)
    facebook_text = build_facebook_caption(facts, post)
    instagram_text = build_instagram_caption(facts, post)
    twitter_text = build_twitter_text(facts, post)

    print("\n" + "═" * 60)
    print(f"TELEGRAM {'(photo)' if tg_fb_image else '(text)'} — {'preview' if dry_run else 'auto-posting'}")
    print("═" * 60)
    print(telegram_text)
    print("\n" + "─" * 60)
    print("FACEBOOK")
    print("─" * 60)
    print(facebook_text)
    print("\n" + "─" * 60)
    print("INSTAGRAM")
    print("─" * 60)
    print(instagram_text)
    print("\n" + "─" * 60)
    print("X / TWITTER")
    print("─" * 60)
    print(twitter_text)
    print("═" * 60 + "\n")

    if dry_run:
        print("Dry run — blog post NOT saved, nothing sent.")
        return post, {}

    # Publish the blog article first — social posts link back to it.
    all_posts = [post] + existing
    save_posts(all_posts)
    print(f"✅ Blog post saved. Total in blog: {len(all_posts)}")

    results: dict[str, bool] = {}

    if telegram:
        if tg_fb_image:
            results["telegram"] = _post_with_retry("telegram", send_photo_to_channel, tg_fb_image, telegram_text)
        else:
            results["telegram"] = _post_with_retry("telegram", send_to_channel, telegram_text)
        print("✓ Posted to Telegram." if results["telegram"] else "✗ Telegram post failed after retries.")

    if facebook:
        results["facebook"] = _post_with_retry(
            "facebook", post_facebook, facebook_text,
            image_path=local_image if not photo_url else None,
            image_url=photo_url,
        )
        print("✓ Posted to Facebook." if results["facebook"] else "✗ Facebook post failed after retries.")

    if instagram:
        results["instagram"] = _post_with_retry(
            "instagram", post_instagram, instagram_text,
            image_url=photo_url or GENERIC_SOCIAL_IMAGE,
        )
        print("✓ Posted to Instagram." if results["instagram"] else "✗ Instagram post failed after retries.")

    if twitter:
        results["twitter"] = _post_with_retry("twitter", post_twitter, twitter_text)
        print("✓ Posted to X/Twitter." if results["twitter"] else "✗ X/Twitter post failed after retries.")

    for platform, ok in results.items():
        log("transfer_post", platform, "success" if ok else "failed", post["title"])

    return post, results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Live Transfer News Bot")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, publish nothing")
    parser.add_argument("--no-telegram", dest="telegram", action="store_false")
    parser.add_argument("--no-facebook", dest="facebook", action="store_false")
    parser.add_argument("--no-instagram", dest="instagram", action="store_false")
    parser.add_argument("--no-twitter", dest="twitter", action="store_false")
    args = parser.parse_args()
    post, results = run(
        dry_run=args.dry_run, telegram=args.telegram, facebook=args.facebook,
        instagram=args.instagram, twitter=args.twitter,
    )

    # Exit code must actually reflect reality — a story generated but not
    # delivered anywhere is a real failure the GitHub Actions watchdog/retry
    # workflows need to see and act on, not a silent green checkmark. "No
    # fresh news this cycle" (post is None) stays a soft success: that's the
    # dedup/no-news case working as designed, not something to retry.
    if args.dry_run or post is None:
        sys.exit(0)
    if results and not any(results.values()):
        print("\n✗✗✗ Every requested platform failed to post this story — flagging as a real failure.")
        sys.exit(1)
    sys.exit(0)
