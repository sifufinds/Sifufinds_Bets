"""
agent_transfer_post.py — Live Transfer News Bot for SifuFinds

Watches the dedicated "transfers" news feed (BBC Sport, Sky Sports News, ESPN,
TalkSport, David Ornstein, and Fabrizio Romano only — see
utils.news_fetcher.TRANSFER_ALLOWED_SOURCE_TERMS; Google News and Yahoo are
excluded by policy), and when a genuinely new transfer story appears:

  1. Writes a full researched blog article via agent_sports_blog.generate_post
     ("transfers" category — same anti-hallucination pipeline as every other
     blog category, grounded in the real, live headlines only).
  2. Extracts structured facts (player, clubs, fee, deal stage) from that
     article via a strict, grounded LLM extraction pass — never invents a
     name, club, or figure not already in the article text.
  3. Uses the REAL image the source article itself carries (see
     find_source_image() / find_raw_fallback_photo() below) — never a
     speculative name-based photo search. utils/news_fetcher.py's fetch
     layers already capture each story's own image where the source
     provides one (DuckDuckGo News results, RSS <media:thumbnail>/
     <enclosure> tags), and generate_post() carries those through as
     post["_source_items"]. The normal flow matches the LLM-extracted
     player/club facts against each candidate source item's title to find
     the one the article is actually about, then uses that item's own
     image — guarding against known generic section-branding graphics
     (Sky Sports "Paper Talk", BBC "branded_*" cards) along the way. This
     replaced an earlier Wikipedia/DuckDuckGo-image-search-by-name
     approach that could and did attach the wrong person's photo (matching
     by name alone, no connection to the actual story) — see
     AGENT-KNOWLEDGE.md 2026-07-28. Every post still gets an image one way
     or another: if no source item has a usable match, Telegram and
     Facebook fall back to the per-post branded graphic already generated
     locally for the blog article (uploaded as a file, not a URL — see the
     "always has an image" note below). Instagram falls back to the site's
     generic branded card, since its API requires a public URL (see note).
  4. Posts a short "breaking news" bulletin (Fabrizio Romano / Sports Arena
     Africa style) to Telegram, Facebook, Instagram, and X, each linking back
     to the new blog article and always crediting the outlet the story came
     from via a "📰 Source: X" line (see primary_source() / build_bulletin_lines()
     below) — never posted as an unsourced claim. Pure transfer news only — no
     bookmaker CTA, no bonus mention, no odds. This is a standalone news feed
     on its own 5-minute schedule (the shortest interval GitHub Actions'
     scheduler reliably supports — the closest a cron job can get to posting
     "as it happens"), independent of the site's betting-tips/bonus posting
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
either (a) the generated story's title closely matches one already in
blog/posts.json — the same recent-title check agent_sports_blog.py's own
run() uses — or (b) the article's underlying source headline(s) (see
post["_source_items"]) match one already covered via the shared registry in
utils/story_dedup.py (as of 2026-08-01, also shared with agent_sports_blog.py's
own run() — see that module's docstring), including the raw-fallback path below.
(b) exists because (a) alone doesn't catch it: the LLM invents a fresh,
differently-worded blog title on every cron cycle even when the underlying
BBC/ESPN headline is the same still-fresh story, so title-prefix matching
against previous *generated* titles never fires — see _source_keys()'s
docstring for the real incident (five differently-titled posts about the
same Henry Lawrence/Ipswich rumour within an hour, 2026-07-30) this closes.

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

from llm import ask, AIProvidersExhausted
from utils.logger import log
from utils.news_fetcher import fetch_category
from utils.player_photo import _looks_like_branded_thumbnail_url, _looks_like_news_column_graphic
from utils.story_dedup import headline_key as _headline_key, source_keys as _source_keys, \
    load_covered_keys as _load_covered_keys, record_covered_keys as _record_covered_keys
from utils.tweet_text import tweet_len as _tweet_len, trim_to_limit as _trim_to_limit
from agent_sports_blog import generate_post, load_posts, save_posts
from agent_telegram_offers import send_to_channel, send_photo_to_channel, SITE_URL
from agent3_social import post_facebook, post_instagram
from agent_twitter_posts import _post_tweet as post_twitter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
# assets/og-image.png is the site's real, live default social/OG image (used
# correctly in index.html's own og:image meta tag, confirmed 200 live
# 2026-07-30) — "assets/social-card.jpg" doesn't exist anywhere in the repo
# and 404s, silently degrading every fallback-to-generic-card post to a
# broken image URL (send_photo_to_channel() then falls back to text-only,
# so the post itself wasn't lost, just its image — same wrong filename also
# found in agent3_social.py and agent3_social_telethon.py's Instagram
# fallbacks).
GENERIC_SOCIAL_IMAGE = f"{SITE_URL}/assets/og-image.png"
# posted_keys is a shared "already covered this source headline" registry —
# see utils/story_dedup.py. Shared with agent_sports_blog.py's own run() as
# of 2026-08-01 so the same rumour can't be covered twice under two
# differently-worded titles by two different agents in the same day either.


def local_feature_image_path(post: dict) -> Path | None:
    """The per-post branded graphic already generated for the blog article
    (assets/og/{slug}.png), as a local filesystem path — used as the
    guaranteed image fallback for Telegram/Facebook when no matching source
    image exists for the story. Returns None only if generation genuinely
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


def build_bulletin_lines(facts: dict, source: str | None = None) -> list[str]:
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

    # Every transfer bulletin quotes where the story came from — never posted
    # as an unsourced claim.
    lines.append(f"📰 Source: {source}" if source else "📰 Source: multiple outlets")
    lines.append("")

    return lines


def primary_source(post: dict) -> str | None:
    """First outlet credited for this story's headlines (see _sources in
    agent_sports_blog.generate_post) — the name shown in every social
    bulletin's "Source:" line so no transfer post goes out unattributed."""
    sources = post.get("_sources") or []
    return sources[0] if sources else None


_REACT_PROMPT_TG = "💬 Tap a reaction below — 🔥 big move · 😳 shock · 🤔 not convinced"
_REACT_PROMPT_FB = "💬 React below — 🔥 if this is a good move, 😳 if it shocked you!"


def build_telegram_caption(facts: dict, post: dict) -> str:
    lines = build_bulletin_lines(facts, source=primary_source(post))
    blog_url = f"{SITE_URL}/blog/{post['slug']}/"
    return (
        "\n".join(lines) +
        f"📰 Full story: <a href=\"{blog_url}\">{post['title']}</a>\n\n"
        f"{_REACT_PROMPT_TG}"
    )


def build_facebook_caption(facts: dict, post: dict) -> str:
    lines = build_bulletin_lines(facts, source=primary_source(post))
    blog_url = f"{SITE_URL}/blog/{post['slug']}/"
    hashtags = "#TransferNews #SifuFinds #Football #TransferWindow"
    return (
        "\n".join(lines) +
        f"📰 Full story: {blog_url}\n\n"
        f"{_REACT_PROMPT_FB}\n\n"
        f"{hashtags}"
    )


def build_instagram_caption(facts: dict, post: dict) -> str:
    lines = build_bulletin_lines(facts, source=primary_source(post))
    hashtags = "#TransferNews #SifuFinds #Football #TransferWindow #FootballNews"
    return (
        "\n".join(lines) +
        f"👉 Link in bio for the full story\n\n"
        f".\n.\n.\n{hashtags}"
    )




def build_twitter_text(facts: dict, post: dict) -> str:
    lines = build_bulletin_lines(facts, source=primary_source(post))
    blog_url = f"{SITE_URL}/blog/{post['slug']}/"
    tweet = (
        "\n".join(lines) +
        f"👉 {blog_url}\n\n"
        f"#TransferNews #SifuFinds"
    )
    return _trim_to_limit(tweet)


# ── RAW-HEADLINE FALLBACK (no LLM — used only when every AI provider is
# exhausted, so live coverage never fully stops during an outage) ───────────
#
# Does NOT create a blog post: a single wire headline has nowhere near the
# researched depth CLAUDE.md's blog protocol requires (SEO research, 1000+
# words, FAQ section), and faking that would be thin content. Instead this
# posts a short, honest repost straight to socials — always naming and
# linking the real outlet that broke the story, never a SifuFinds page —
# so "live" transfer coverage keeps its promise even while Groq/Gemini are
# both out of daily quota. The moment a provider has headroom again,
# generate_post() succeeds and the normal full-article path takes back over
# automatically (this path is only reached when that raises
# AIProvidersExhausted).

def _usable_source_image(image: str, title: str) -> bool:
    """A real image is only usable if it's not one of the known generic
    section-branding graphics outlets reuse across unrelated stories (Sky
    Sports "Paper Talk", BBC "branded_*" cards, etc. — see
    utils/player_photo.py's _looks_like_branded_thumbnail_url /
    _looks_like_news_column_graphic, reused here rather than duplicated)."""
    if not image:
        return False
    if _looks_like_branded_thumbnail_url(image):
        return False
    if _looks_like_news_column_graphic(title):
        return False
    return True


def find_raw_fallback_photo(item: dict) -> str | None:
    """The raw headline *is* the source article — its own scraped image
    (see utils/news_fetcher.py's image field, populated from DuckDuckGo
    News results and RSS <media:thumbnail>/<enclosure> tags) is the only
    photo ever used here. No speculative name-based photo search: that
    previously matched wrong/random people by name overlap alone, which is
    strictly worse than falling back to the generic branded social card."""
    image = item.get("image", "")
    if _usable_source_image(image, item.get("title", "")):
        print(f"  ✓ Using the source's own image ({item.get('source', 'unknown')})")
        return image
    print("  — No usable source image for this headline — using generic branded card")
    return None


def find_source_image(post: dict, facts: dict) -> tuple[str | None, str | None]:
    """The real, source-provided image for whichever specific story the
    generated article turned out to be about — matched against the
    extracted facts (player/from_club/to_club) by keyword overlap with each
    candidate source item's title, never a speculative name-based photo
    search. Requires an actual match (score > 0): an unmatched top item's
    image could easily belong to a different story entirely, since
    generate_post() feeds the LLM several fresh headlines at once. Returns
    (image_url, source_name) or (None, None)."""
    candidates = [c for c in (facts.get("player"), facts.get("from_club"), facts.get("to_club")) if c]
    if not candidates:
        return None, None

    best_item, best_score = None, 0
    for item in post.get("_source_items", []):
        image = item.get("image", "")
        title = item.get("title", "")
        if not _usable_source_image(image, title):
            continue
        title_l = title.lower()
        score = sum(1 for c in candidates if c.lower() in title_l)
        if score > best_score:
            best_item, best_score = item, score

    if best_item:
        return best_item["image"], best_item.get("source")
    return None, None


def pick_fresh_raw_headline(recent_titles: set[str]) -> dict | None:
    """Freshest transfers headline not already covered by a real blog post
    (recent_titles, same key scheme as the caller's dedup) and not already
    reposted via this fallback (see utils/story_dedup.py)."""
    items = fetch_category("transfers", max_per_feed=6)
    posted = _load_covered_keys()

    for item in items:
        key = _headline_key(item["title"])
        if key in posted or key in recent_titles:
            continue
        return item
    return None


def build_raw_fallback_telegram(item: dict) -> str:
    lines = [f"🚨 {item['title']}", ""]
    if item.get("description"):
        lines.append(item["description"][:220])
        lines.append("")
    lines.append(f"📰 Source: {item['source']}")
    lines.append(f'🔗 <a href="{item["url"]}">Read the full story</a>')
    lines.append("")
    lines.append(_REACT_PROMPT_TG)
    return "\n".join(lines)


def build_raw_fallback_facebook(item: dict) -> str:
    lines = [f"🚨 {item['title']}", ""]
    if item.get("description"):
        lines.append(item["description"][:220])
        lines.append("")
    lines.append(f"📰 Source: {item['source']}")
    lines.append(f"🔗 {item['url']}")
    lines.append("")
    lines.append(_REACT_PROMPT_FB)
    lines.append("")
    lines.append("#TransferNews #SifuFinds #Football #TransferWindow")
    return "\n".join(lines)


def build_raw_fallback_instagram(item: dict) -> str:
    lines = [f"🚨 {item['title']}", ""]
    if item.get("description"):
        lines.append(item["description"][:220])
        lines.append("")
    lines.append(f"📰 Source: {item['source']}")
    lines.append("👉 Link in bio for more transfer coverage")
    lines.append("")
    lines.append(".\n.\n.\n#TransferNews #SifuFinds #Football #TransferWindow")
    return "\n".join(lines)


def build_raw_fallback_twitter(item: dict) -> str:
    lines = [
        f"🚨 {item['title']}", "",
        f"📰 Source: {item['source']}",
        f"🔗 {item['url']}", "",
        "#TransferNews #SifuFinds",
    ]
    return _trim_to_limit("\n".join(lines))


def run_raw_fallback(dry_run: bool, telegram: bool, facebook: bool,
                      instagram: bool, twitter: bool,
                      recent_titles: set[str]) -> tuple[dict | None, dict[str, bool]]:
    item = pick_fresh_raw_headline(recent_titles)
    if item is None:
        print("⚠ No fresh, not-yet-covered transfer headline to repost this cycle.")
        log("transfer_post", "raw_fallback", "skipped", "no fresh headline")
        return None, {}

    print(f"  ✓ Reposting directly from {item['source']!r}: '{item['title']}'")
    photo_url = find_raw_fallback_photo(item)
    image_url = photo_url or GENERIC_SOCIAL_IMAGE

    telegram_text = build_raw_fallback_telegram(item)
    facebook_text = build_raw_fallback_facebook(item)
    instagram_text = build_raw_fallback_instagram(item)
    twitter_text = build_raw_fallback_twitter(item)

    print("\n" + "═" * 60)
    print(f"RAW FALLBACK REPOST (AI unavailable) — image: {'real photo' if photo_url else 'generic branded card'} — {'preview' if dry_run else 'auto-posting'}")
    print("═" * 60)
    print(telegram_text)
    print("═" * 60 + "\n")

    if dry_run:
        print("Dry run — nothing sent.")
        return None, {}

    results: dict[str, bool] = {}
    if telegram:
        results["telegram"] = _post_with_retry("telegram", send_photo_to_channel, image_url, telegram_text)
        print("✓ Posted to Telegram." if results["telegram"] else "✗ Telegram post failed after retries.")
    if facebook:
        results["facebook"] = _post_with_retry("facebook", post_facebook, facebook_text, image_url=image_url)
        print("✓ Posted to Facebook." if results["facebook"] else "✗ Facebook post failed after retries.")
    if instagram:
        results["instagram"] = _post_with_retry("instagram", post_instagram, instagram_text, image_url=image_url)
        print("✓ Posted to Instagram." if results["instagram"] else "✗ Instagram post failed after retries.")
    if twitter:
        results["twitter"] = _post_with_retry("twitter", post_twitter, twitter_text)
        print("✓ Posted to X/Twitter." if results["twitter"] else "✗ X/Twitter post failed after retries.")

    if any(results.values()):
        _record_covered_keys({_headline_key(item["title"])})

    for platform, ok in results.items():
        log("transfer_post", f"raw_fallback_{platform}", "success" if ok else "failed", item["title"])

    return None, results


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
    try:
        post = generate_post("transfers")
    except AIProvidersExhausted as e:
        # Every LLM backend is over quota — rather than going dark until the
        # next successful cycle (previously a hard failure the workflow had
        # to wait out or get retried by the watchdog), repost the freshest
        # headline directly from the free news feed with no AI involved. See
        # run_raw_fallback()'s docstring for why this never creates a blog
        # post. Full-article generation takes back over automatically the
        # next time generate_post() succeeds.
        print(f"  ⚠ {e}")
        log("transfer_post", "generate", "ai_exhausted_fallback", str(e))
        return run_raw_fallback(dry_run, telegram, facebook, instagram, twitter, recent_titles)
    if post is None:
        print("⚠ No fresh transfer news available this cycle — nothing to post.")
        log("transfer_post", "generate", "skipped", "no fresh news")
        return None, {}

    title_key = post["title"].lower()[:40]
    if title_key in recent_titles:
        print(f"⚠ Similar transfer story already published — skipping. ('{post['title']}')")
        log("transfer_post", "generate", "skipped", "duplicate title")
        return None, {}

    # Also check the *source* headline(s) this article was actually built
    # from against the shared "already covered" registry — catches the case
    # the title check above can't: the LLM invents a fresh, differently-
    # worded blog title every cycle even when the underlying BBC/ESPN story
    # is the same one still sitting inside the freshness window. See
    # utils/story_dedup.py's docstring for the real incident this fixes.
    covered_keys = _load_covered_keys()
    source_keys = _source_keys(post)
    matched = source_keys & covered_keys
    if matched:
        print(f"⚠ Underlying story already covered this cycle — skipping. ('{post['title']}')")
        log("transfer_post", "generate", "skipped", "duplicate source headline")
        return None, {}

    print(f"  ✓ '{post['title']}'")

    print("🔎 Extracting structured facts for the social bulletin...")
    facts = extract_transfer_facts(post)
    print(f"  ✓ player={facts.get('player')!r} status={facts.get('status')!r}")

    photo_url, photo_source = find_source_image(post, facts)
    print(f"  {'✓ Using source image from ' + photo_source if photo_url else '— No matching source image found'}")
    # This post dict is about to be written to blog/posts.json — strip the
    # source-item list now that it's served its purpose (it's only ever
    # needed transiently, right here, to pick the image above) rather than
    # bloating the public JSON every visitor's browser fetches.
    post.pop("_source_items", None)

    # Guaranteed image: the real source-article photo when a confident match
    # was found, otherwise the per-post branded graphic already generated
    # for the blog article (uploaded as a local file for Telegram/Facebook —
    # see module docstring for why Instagram can't use this same fallback).
    # Never a speculative name-based photo search — see find_source_image's
    # docstring and AGENT-KNOWLEDGE.md 2026-07-28.
    local_image = None if photo_url else local_feature_image_path(post)
    tg_fb_image = photo_url or local_image
    print(f"  → Image for Telegram/Facebook: {'source photo' if photo_url else ('branded graphic' if local_image else 'NONE — feature image generation failed')}")

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

    # Record the source headline(s) this article covered into the shared
    # "already covered" registry so a later cycle recognizes the same
    # underlying story even under a brand-new LLM-invented title — see
    # utils/story_dedup.py's docstring.
    _record_covered_keys(source_keys)

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
    # workflows need to see and act on, not a silent green checkmark. Checked
    # on `results` alone (not `post is None`) so the raw-fallback repost path
    # (run_raw_fallback always returns post=None even on a real, attempted
    # post — see its docstring) still gets this same accountability instead
    # of silently reporting success while every platform actually failed.
    # "No fresh news/headline this cycle" (post is None AND results == {})
    # stays a soft success: that's the dedup/no-news case working as designed.
    if args.dry_run:
        sys.exit(0)
    if results and not any(results.values()):
        print("\n✗✗✗ Every requested platform failed to post this story — flagging as a real failure.")
        sys.exit(1)
    sys.exit(0)
