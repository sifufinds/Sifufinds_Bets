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
  3. Looks up a free, legal photo for the named player via Wikipedia's REST
     API (utils/player_photo.py, Wikimedia Commons-licensed) and falls back to
     SifuFinds' generic branded social card if none is found — never scrapes
     or rehosts a copyrighted news photo.
  4. Posts a short "breaking news" bulletin (Fabrizio Romano / Sports Arena
     Africa style) to Telegram, Facebook, Instagram, and X, each linking back
     to the new blog article, with the standard bookmaker CTA + responsible
     gambling disclaimer.

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
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

from llm import ask
from utils.logger import log
from utils.affiliate_links import cta_html, cta_plain, CTA_CLAIM_BONUS
from utils.player_photo import fetch_player_photo, looks_like_person_name
from agent_sports_blog import generate_post, load_posts, save_posts
from agent_telegram_offers import send_to_channel, send_photo_to_channel, _stars, SITE_URL
from agent_match_post import pick_cta_brand
from agent3_social import post_facebook, post_instagram
from agent_twitter_posts import _post_tweet as post_twitter

GENERIC_SOCIAL_IMAGE = f"{SITE_URL}/assets/social-card.jpg"

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
        facts = json.loads(_clean_json(raw))
        for key in fallback:
            facts.setdefault(key, fallback[key])
        return facts
    except Exception as e:
        print(f"  ⚠ Fact extraction failed, using excerpt fallback: {e}")
        return fallback


# ── BULLETIN BODY (shared core, platform wrappers add branding/CTA) ─────────

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


def build_bonus_cta(cta: dict, html: bool) -> str:
    def b(s: str) -> str:
        return f"<b>{s}</b>" if html else s
    claim_link = cta_html(cta, label=CTA_CLAIM_BONUS) if html else cta_plain(cta, label=CTA_CLAIM_BONUS)
    return (
        f"🎁 While the transfer window plays out: {b(cta['name'])} {_stars(cta['stars'])} "
        f"— {b(cta['welcome'])}\n{claim_link}"
    )


_REACT_PROMPT_TG = "💬 Tap a reaction below — 🔥 big move · 😳 shock · 🤔 not convinced"
_REACT_PROMPT_FB = "💬 React below — 🔥 if this is a good move, 😳 if it shocked you!"


def build_telegram_caption(facts: dict, post: dict, cta: dict) -> str:
    lines = build_bulletin_lines(facts)
    blog_url = f"{SITE_URL}/blog/{post['slug']}/"
    return (
        "\n".join(lines) +
        f"\n{build_bonus_cta(cta, html=True)}\n\n"
        f"📰 Full story: <a href=\"{blog_url}\">{post['title']}</a>\n\n"
        f"{_REACT_PROMPT_TG}\n\n"
        f"🔞 18+ | Gamble Responsibly"
    )


def build_facebook_caption(facts: dict, post: dict, cta: dict) -> str:
    lines = build_bulletin_lines(facts)
    blog_url = f"{SITE_URL}/blog/{post['slug']}/"
    hashtags = "#TransferNews #SifuFinds #Football #BettingTips"
    return (
        "\n".join(lines) +
        f"\n{build_bonus_cta(cta, html=False)}\n\n"
        f"📰 Full story: {blog_url}\n\n"
        f"{_REACT_PROMPT_FB}\n\n"
        f"🔞 18+ | Gamble Responsibly\n\n"
        f"{hashtags}"
    )


def build_instagram_caption(facts: dict, post: dict, cta: dict) -> str:
    lines = build_bulletin_lines(facts)
    hashtags = "#TransferNews #SifuFinds #Football #TransferWindow #AfricanBetting #BettingTips"
    return (
        "\n".join(lines) +
        f"\n{build_bonus_cta(cta, html=False)}\n\n"
        f"👉 Link in bio for the full story + latest bonuses\n\n"
        f"🔞 18+ | Gamble Responsibly\n"
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


def build_twitter_text(facts: dict, post: dict, cta: dict) -> str:
    lines = build_bulletin_lines(facts)
    blog_url = f"{SITE_URL}/blog/{post['slug']}/"
    tweet = (
        "\n".join(lines) +
        f"\n👉 {blog_url}\n\n"
        f"#TransferNews #SifuFinds 🔞 18+"
    )
    return _trim_to_limit(tweet)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False, telegram: bool = True, facebook: bool = True,
        instagram: bool = True, twitter: bool = True) -> dict | None:
    log("transfer_post", "start", "running")

    existing = load_posts()
    recent_titles = {p["title"].lower()[:40] for p in existing[:40]}

    print("📡 Generating transfer news article from live feeds...")
    post = generate_post("transfers")
    if post is None:
        print("⚠ No fresh transfer news available this cycle — nothing to post.")
        log("transfer_post", "generate", "skipped", "no fresh news")
        return None

    title_key = post["title"].lower()[:40]
    if title_key in recent_titles:
        print(f"⚠ Similar transfer story already published — skipping. ('{post['title']}')")
        log("transfer_post", "generate", "skipped", "duplicate title")
        return None

    print(f"  ✓ '{post['title']}'")

    print("🔎 Extracting structured facts for the social bulletin...")
    facts = extract_transfer_facts(post)
    print(f"  ✓ player={facts.get('player')!r} status={facts.get('status')!r}")

    photo_url = None
    player = facts.get("player") or ""
    if player and looks_like_person_name(player):
        photo_url = fetch_player_photo(player)
        print(f"  {'✓ Found Wikipedia photo' if photo_url else '— No Wikipedia photo found'} for {player!r}")

    cta = pick_cta_brand()

    telegram_text = build_telegram_caption(facts, post, cta)
    facebook_text = build_facebook_caption(facts, post, cta)
    instagram_text = build_instagram_caption(facts, post, cta)
    twitter_text = build_twitter_text(facts, post, cta)

    print("\n" + "═" * 60)
    print(f"TELEGRAM {'(photo)' if photo_url else '(text)'} — {'preview' if dry_run else 'auto-posting'}")
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
        return post

    # Publish the blog article first — social posts link back to it.
    all_posts = [post] + existing
    save_posts(all_posts)
    print(f"✅ Blog post saved. Total in blog: {len(all_posts)}")

    results: dict[str, bool] = {}

    if telegram:
        if photo_url:
            results["telegram"] = send_photo_to_channel(photo_url, telegram_text)
        else:
            results["telegram"] = send_to_channel(telegram_text)
        print("✓ Posted to Telegram." if results["telegram"] else "✗ Telegram post failed.")

    if facebook:
        results["facebook"] = post_facebook(facebook_text, image_url=photo_url)
        print("✓ Posted to Facebook." if results["facebook"] else "✗ Facebook post failed or not configured.")

    if instagram:
        results["instagram"] = post_instagram(instagram_text, image_url=photo_url or GENERIC_SOCIAL_IMAGE)
        print("✓ Posted to Instagram." if results["instagram"] else "✗ Instagram post failed or not configured.")

    if twitter:
        results["twitter"] = post_twitter(twitter_text)
        print("✓ Posted to X/Twitter." if results["twitter"] else "✗ X/Twitter post failed or not configured.")

    for platform, ok in results.items():
        log("transfer_post", platform, "success" if ok else "failed", post["title"])

    return post


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Live Transfer News Bot")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, publish nothing")
    parser.add_argument("--no-telegram", dest="telegram", action="store_false")
    parser.add_argument("--no-facebook", dest="facebook", action="store_false")
    parser.add_argument("--no-instagram", dest="instagram", action="store_false")
    parser.add_argument("--no-twitter", dest="twitter", action="store_false")
    args = parser.parse_args()
    result = run(
        dry_run=args.dry_run, telegram=args.telegram, facebook=args.facebook,
        instagram=args.instagram, twitter=args.twitter,
    )
    sys.exit(0 if result is not None or args.dry_run else 0)
