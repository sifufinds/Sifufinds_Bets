"""
Sports & iGaming Blog Writer Agent — Research-First Edition
Fetches LIVE headlines from RSS feeds before generating content,
so every article is grounded in real, current events.

Covers: Football · Basketball · Tennis · Cricket · Rugby · Transfers · Betting · iGaming
Usage:
  python agent_sports_blog.py                         # 1 article, random category
  python agent_sports_blog.py --category football     # target category
  python agent_sports_blog.py --topics 3              # 3 articles
  python agent_sports_blog.py --mode daily            # 2 articles across 2 categories
  python agent_sports_blog.py --mode weekly           # full week batch
  python agent_sports_blog.py --ticker-only           # update ticker.json without writing
"""
import argparse
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))

from llm import ask, AIProvidersExhausted
from config import SITE_URL, BRAND_NAME
from utils.news_fetcher import fetch_category, format_for_prompt
from utils.ticker_builder import build_and_save as update_ticker
from utils.serp_research import research, build_keyword_from_category
from utils.story_dedup import source_keys as _source_keys, \
    load_covered_keys as _load_covered_keys, record_covered_keys as _record_covered_keys
from agent_fact_checker import check_post as fact_check_post
from utils.title_content_match import check_africa_framing

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from generate_blog_feature_image import ensure_feature_image

# ── CATEGORY METADATA ─────────────────────────────────────────────────────────

CATEGORIES = {
    "football":   {"icon": "⚽", "color": "#1a6b35", "author": "SifuFinds Football Desk"},
    "sportnews":  {"icon": "🗞️", "color": "#7c3aed", "author": "Sport News Desk"},
    "transfers":  {"icon": "🔄", "color": "#0f766e", "author": "Transfer Desk"},
    "betting":    {"icon": "📊", "color": "#d4af37", "author": "Sifu Kai"},
    "igaming":    {"icon": "🎮", "color": "#0055a4", "author": "iGaming Desk"},
    "basketball": {"icon": "🏀", "color": "#c2410c", "author": "Basketball Desk"},
    "tennis":     {"icon": "🎾", "color": "#b45309", "author": "Tennis Desk"},
    "cricket":    {"icon": "🏏", "color": "#166534", "author": "Cricket Desk"},
    "rugby":      {"icon": "🏉", "color": "#9f1239", "author": "Rugby Desk"},
    "boxing":     {"icon": "🥊", "color": "#b91c1c", "author": "Boxing Desk"},
    "f1":            {"icon": "🏎️", "color": "#dc2626", "author": "F1 Desk"},
    "worldcup2026":  {"icon": "🏆", "color": "#c8a951", "author": "World Cup 2026 Desk"},
}

# ── BETTING ANGLE PROMPTS (layered on top of live news) ──────────────────────

BETTING_ANGLES = {
    "football": [
        "analyse the betting implications and best odds for African bettors",
        "identify value bets for African bookmakers (Bet9ja, Sportybet, 1xBet, Betway)",
        "build a match preview with goal scorer odds and correct score markets",
        "create an AFCON or CAF angle connecting the news to African football fans",
    ],
    "sportnews": [
        "cover this trending global sports story and connect it to betting markets for African fans",
        "analyse transfer news and how squad changes shift betting odds (title, relegation, golden boot)",
        "round up the biggest world sport stories this week and highlight the best betting angles",
        "break down the most viral sports story right now and explain the betting implications",
    ],
    "transfers": [
        "break down this transfer story (deal stage, fee, wages if reported) and what it means for the club's title/relegation/top-4 odds",
        "explain how this signing or exit shifts the selling and buying club's odds for the season ahead",
        "cover the transfer saga stage by stage (interest, bid, medical, here-we-go) and connect it to African bettors following the story",
        "analyse how this transfer window business changes a club's squad depth and betting value for upcoming fixtures",
    ],
    "betting": [
        "build an accumulator with these fixtures and compare odds across bookmakers",
        "explain bankroll management strategy using these matches as examples",
        "identify where the bookmaker odds are mispriced vs true probability",
    ],
    "igaming": [
        "explain what this regulatory news means for African bettors and their deposits",
        "compare how this industry trend affects operators licensed in Nigeria, Kenya, SA",
        "discuss responsible gambling implications for African mobile betting users",
    ],
    "basketball": [
        "build NBA betting guide for African fans with odds from 1xBet and Betway",
        "compare Basketball Africa League (BAL) odds across African bookmakers",
        "explain player prop betting using these performances as examples",
    ],
    "tennis": [
        "build Grand Slam match betting guide with set betting and total games markets",
        "identify value in the tournament outright odds given this news",
        "explain in-play tennis betting strategy based on this player's form",
    ],
    "cricket": [
        "build a match betting guide for African fans covering Proteas and major series",
        "explain how pitch conditions and weather affect betting markets",
        "identify value in the series winner and top batsman/bowler markets",
    ],
    "rugby": [
        "build a Springboks or Six Nations betting guide for South African fans",
        "explain first try scorer and correct score rugby markets",
        "identify value in tournament winner odds given this news",
    ],
    "boxing": [
        "build a fight-night betting guide with method of victory and round betting markets",
        "identify value in the outright winner odds and compare across African bookmakers",
        "explain how to bet on boxing underdogs and why African bettors love upset picks",
    ],
    "f1": [
        "build a race weekend betting guide with race winner, podium, and fastest lap markets",
        "identify value in the drivers and constructors championship odds given this news",
        "explain in-race betting strategy and safety car impact on F1 markets for African fans",
    ],
    "worldcup2026": [
        "build a World Cup 2026 match preview with group stage betting markets and best odds for African fans",
        "analyse the African teams' (Nigeria, Morocco, Senegal, Egypt, South Africa) World Cup 2026 performance and betting markets",
        "compare World Cup 2026 outright winner odds across Bet9ja, Sportybet, 1xBet, and Betway for African bettors",
        "break down today's World Cup 2026 results and identify value in upcoming knockout stage bets",
    ],
}

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""You are the Sports & iGaming Blog Writer for SifuFinds ({SITE_URL}), Africa's #1 betting comparison website.

YOUR JOB: Write authoritative articles about the REAL, CURRENT news items provided below. Each news item shows its exact age (e.g. "2.3h ago"). You MUST write about what actually happened — do NOT invent scores, signings, transfers, or events.

ACCURACY RULES — NON-NEGOTIABLE:
- Only write about stories explicitly listed in the provided headlines
- Quote or paraphrase the actual headline/story — name the real teams, players, events
- If a headline says "Villa beat Freiburg", write about that specific match
- Odds are the one exception to "don't invent numbers": always estimate odds in
  realistic ranges (1.30–12.00) for the betting-angle content, and always frame
  them as illustrative market pricing, e.g. "odds are trading around 4.50 with
  Bet9ja" — never as a fact you're claiming happened
- NEVER invent a transfer fee, a specific date/deadline, or a statistic that
  isn't in the headlines/snippets above — if the source doesn't give a fee or
  date, don't guess one; write "undisclosed fee" or "no date confirmed yet"
  instead of a specific-sounding number. WRONG example (do not do this): if
  a headline just says "Barcelona bid for Rodri", do not write "Barcelona's
  initial bid for Rodri was £38.5m" — no figure was given, so no figure gets
  written, not even a plausible-sounding one
- NEVER put words in anyone's mouth — do not write a direct quote (in quotation
  marks) attributed to a player, club, bookmaker, or "a representative" unless
  that exact quote appears in the source snippets. Describe reactions and
  sentiment in your own voice instead (e.g. "bettors are reacting fast to the
  news" rather than inventing what someone supposedly said)
- When in doubt about whether a specific number, date, or quote is actually
  in the source snippets, leave it out entirely rather than guess — a vaguer
  sentence that passes fact-check beats a specific one that gets the whole
  article rejected
- If the news shows the story is X hours old, reflect that timing accurately in the article
- Attribute the story to the outlet that reported it, by name, at least once in the article (e.g. "as per BBC Sport", "Sky Sports News reports", "according to Fabrizio Romano") — the source for each headline is shown in brackets in the headlines list below
- NEVER title or frame an article as being about "Africa"/"African clubs"/an
  "African transfer window" unless the actual clubs, players, or league in
  the headlines are genuinely African. It is fine, and expected, to say the
  article is written FOR African bettors/punters — that describes the
  audience and is true of every article regardless of which clubs are
  involved. It is NOT fine to imply the STORY itself is African when it
  isn't. WRONG example (do not do this): headlines are about West Ham,
  Sunderland, Chelsea, and Newcastle (all English clubs) — do not title
  this "Transfer Frenzy in Africa" or "Africa's Top Transfer Stories", and
  do not open the article with "Africa's transfer window is heating up" or
  "the transfer window in Africa is buzzing". RIGHT example: title it
  "Premier League Transfer News: West Ham, Sunderland Deals" and open with
  "The Premier League transfer window is heating up" — then connect it to
  the African betting angle in the body/CTA, not the headline claim

BRAND VOICE:
- Confident, knowledgeable, street-smart African analyst
- Reference African bookmakers naturally: Bet9ja, Sportybet, 1xBet, Betway, Hollywoodbets, Betika, Melbet
- Never promote just one bookmaker — always compare at least 2
- Use natural African English; occasional Pidgin/slang where it fits ("This odds na fire!", "Eish, massive news!")

ARTICLE REQUIREMENTS:
- 700-900 words, grounded in the real news provided
- Compare odds across at least 2 African bookmakers per market
- Include a responsible gambling section
- End with a CTA mentioning {SITE_URL} as plain text — do NOT wrap it in a markdown link
- FINAL LINE must be: *18+ | Bet Responsibly | T&Cs Apply*

LINKING RULES — NON-NEGOTIABLE:
- NEVER write a markdown link to any {SITE_URL}/<path> page (e.g. do not write "[African Bookmakers]({SITE_URL}/african-bookmakers)")
- The site automatically hyperlinks bookmaker names, country names, and key terms for you after you submit the article — you only need to MENTION them in plain text, never link them yourself
- You may mention {SITE_URL} as bare plain text (no brackets, no parentheses) in the CTA, nothing else
- External links (FIFA, UEFA, CAF, etc.) are also auto-inserted — mention the organisation by name in plain text only, do not add markdown links for them either

OUTPUT FORMAT — return EXACTLY this structure, nothing outside the markers:

===META===
{{
  "category": "ONE of: football, sportnews, transfers, betting, igaming, basketball, tennis, cricket, rugby, boxing, f1, worldcup2026 — pick exactly one word",
  "icon": "emoji for the category",
  "title": "Specific title referencing the ACTUAL news story (max 80 chars)",
  "slug": "url-slug-format",
  "excerpt": "150-200 char excerpt naming the real story and promising betting insight",
  "image_color": "#hex color",
  "tags": ["Tag1", "Tag2", "Tag3", "Tag4"],
  "featured": false,
  "bookmaker_featured": "primary bookmaker referenced",
  "read_time": 4
}}
===BLOG===
[Full article in plain markdown — 700-900 words]
[MUST reference the actual named events from the headlines provided]
[Must include odds comparison table where relevant]
[Must include responsible betting section]
[Final line: *18+ | Bet Responsibly | T&Cs Apply*]
===END==="""


# ── CORE GENERATION ───────────────────────────────────────────────────────────

def discard_feature_image(post: dict) -> None:
    """Delete the branded OG image already generated for a post that's about
    to be thrown away (fact-check FLAG, or a caller's own dedup rejection —
    see agent_transfer_post.py's run()). Without this, ensure_feature_image()
    has already written a real PNG to assets/og/ by the time any rejection
    check runs, and every caller's git-add step (transfer_news.yml's
    `git add ... assets/og/`) stages it unconditionally — producing a real
    commit every ~5 minutes with no corresponding post ever landing in
    posts.json, which silently disguises a 100%-rejection-rate outage as
    normal ongoing activity (confirmed live 2026-08-02: 3 days, zero new
    transfer posts, while the workflow kept committing orphaned images the
    whole time)."""
    feature_image = post.get("feature_image")
    if not feature_image:
        return
    path = Path(__file__).resolve().parent.parent.parent / feature_image.lstrip("/")
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def generate_post(category: str) -> Optional[dict]:
    today = datetime.now(timezone.utc).strftime("%A, %d %B %Y")
    cat_meta = CATEGORIES.get(category, CATEGORIES["football"])

    # 1. Fetch live headlines — strict freshness enforced inside fetch_category
    print(f"  📡 Fetching live {category} news...")
    news_items = fetch_category(category, max_per_feed=6)
    news_text = format_for_prompt(news_items, limit=10)

    if not news_items:
        print(f"  ⚠ No fresh news found for {category} (all items exceed freshness window) — skipping")
        return None

    oldest_h = max(i.get("age_hours", 0) for i in news_items)
    freshest_h = min(i.get("age_hours", 0) for i in news_items)
    print(f"  ✓ {len(news_items)} fresh items — newest: {freshest_h:.1f}h ago, oldest: {oldest_h:.1f}h ago")

    # 2. SERP + competitor research — Firecrawl search + Apify RAG
    print(f"  🔍 Running SERP research...")
    serp_block = research(build_keyword_from_category(category))

    # 3. Pick a betting angle
    angles = BETTING_ANGLES.get(category, BETTING_ANGLES["football"])
    angle = random.choice(angles)

    # 4. Build the prompt with live news + SERP research context
    user_message = f"""TODAY: {today}

LIVE NEWS HEADLINES FOR {category.upper()} — these are real stories published within the last {oldest_h:.0f} hours:
{news_text}

YOUR TASK: Write a compelling sports blog article about {category} that:
1. References the REAL named stories, teams, and players from the headlines above — do not invent anything
2. {angle}
3. Is written for African sports bettors (Nigeria, Kenya, South Africa, Ghana, Tanzania)

AFRICAN CONTEXT:
- Primary currencies: NGN (₦), KES (KSh), GHS (GH₵), ZAR (R), TZS (TSh)
- Top bookmakers in Africa: Bet9ja, Sportybet, 1xBet, Betway, Hollywoodbets, Betika, Melbet, BetKing
- Popular payment methods: M-Pesa, MTN MoMo, OPay, PalmPay
- Key African leagues: NPFL (Nigeria), KPL (Kenya), PSL (South Africa), GPL (Ghana), CAF Champions League, AFCON

Write the article now. Base it on the REAL news provided above — do not invent events.

{serp_block}"""

    try:
        print(f"  🤖 Generating article with Groq LLM...")
        # transfers content names specific fees/deal stages — the single
        # most fact-check-fragile category (see llm.py's prefer_accuracy
        # docstring and AGENT-KNOWLEDGE.md's 2026-08-10 entry for the 3-day
        # content blackout this caused when g4f's fallback tier kept
        # inventing fees other categories don't hinge on as heavily).
        raw = ask(SYSTEM_PROMPT, user_message, prefer_accuracy=(category == "transfers"))

        meta_raw = _extract(raw, "===META===", "===BLOG===")
        blog_body = _extract(raw, "===BLOG===", "===END===", end_required=False)

        if not meta_raw or not blog_body:
            print(f"  ✗ LLM response missing required sections")
            return None

        meta = json.loads(_clean_json(meta_raw))

        # Sanitise category: LLMs sometimes echo the enum notation "a|b|c" — take first token
        raw_cat = str(meta.get("category", category))
        clean_cat = raw_cat.split("|")[0].split(",")[0].strip().lower()
        if clean_cat not in CATEGORIES:
            clean_cat = category

        post = {
            "id": f"post-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}",
            "category": clean_cat,
            "title": meta.get("title", ""),
            "slug": meta.get("slug", ""),
            "excerpt": meta.get("excerpt", ""),
            "body": blog_body.strip(),
            "author": cat_meta["author"],
            "published_at": datetime.now(timezone.utc).isoformat(),
            "image_color": meta.get("image_color", cat_meta["color"]),
            "image_icon": meta.get("icon", cat_meta["icon"]),
            "tags": meta.get("tags", []),
            "featured": meta.get("featured", False),
            "bookmaker_featured": meta.get("bookmaker_featured", ""),
            "read_time": meta.get("read_time", 4),
            "_sources": [item["source"] for item in news_items[:5]],
            # Kept so callers (agent_transfer_post.py) can attach the real,
            # source-provided image for whichever specific story the article
            # turned out to be about, instead of a speculative name-based
            # photo search — see AGENT-KNOWLEDGE.md 2026-07-28.
            "_source_items": [
                {"title": i["title"], "url": i["url"], "image": i.get("image", ""),
                 "source": i["source"], "description": i.get("description", "")}
                for i in news_items[:8]
            ],
        }
        # Unique feature image per post — doubles as the og:image/twitter:image
        # (picked up automatically by gen_blog_post_pages.py) and the LinkedIn/
        # Facebook/X share preview, since those all render off the same OG tags.
        feature_image = ensure_feature_image(post)
        if feature_image:
            post["feature_image"] = feature_image

        # Title/content topic-match gate — deterministic check that the
        # title/slug don't claim an African transfer/club story the body
        # never delivers (see utils/title_content_match.py's docstring for
        # the live incident this was built from: a "transfers" post titled
        # "Transfer Frenzy in Africa" that was entirely about West Ham,
        # Sunderland, Chelsea and Newcastle). Held back the same way a
        # fact-check FLAG is — nothing publishable this run, not a crash.
        africa_violation = check_africa_framing(post["title"], post["slug"], post["body"])
        if africa_violation:
            print(f"  ✗ Title/content check held back this article: {africa_violation}")
            discard_feature_image(post)
            return None

        # Fact-check gate — second LLM pass cross-checking the draft against
        # its own source snippets before it's ever returned to a caller.
        # Both agent_sports_blog.run() and agent_transfer_post.py (which
        # imports generate_post directly) go through this single choke
        # point. A FLAG holds the post back this run (logged to
        # fact_check_flags.json) rather than publishing an unverified claim
        # — the AIProvidersExhausted case does the same, deliberately, so a
        # fact-checker outage can never become a silent bypass.
        passed, flags = fact_check_post(post)
        if not passed:
            print(f"  ✗ Fact-checker held back this article: {flags}")
            discard_feature_image(post)
            return None
        return post

    except json.JSONDecodeError as e:
        print(f"  ✗ JSON parse error: {e}")
        return None
    except AIProvidersExhausted:
        # Not the same as "no fresh news" — this is an infra failure (every
        # LLM backend rate-limited or over quota). Swallowing it into a plain
        # `return None` here made it indistinguishable from a benign skip, so
        # callers (agent_transfer_post.py) logged it as "no fresh news" and
        # exited 0, and no GitHub Actions retry/watchdog workflow ever saw a
        # failure to act on — real, fresh stories went unposted for hours
        # with nothing flagging it. Let it propagate so the caller's process
        # exits non-zero and the existing retry infra actually retries it.
        raise
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def _extract(text: str, start: str, end: str, end_required: bool = True) -> str:
    try:
        s = text.index(start) + len(start)
        try:
            e = text.index(end, s)
            return text[s:e].strip()
        except ValueError:
            if end_required:
                return ""
            return text[s:].strip()
    except ValueError:
        return ""


def _clean_json(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("```")[1]
        if s.startswith("json"):
            s = s[4:]
    return s.strip()


# ── POST STORAGE ──────────────────────────────────────────────────────────────

POSTS_PATH = Path(__file__).parent.parent.parent / "blog" / "posts.json"


def load_posts() -> list[dict]:
    """Load blog/posts.json, retrying briefly against concurrent writers.

    2026-08-09 incident: this used to swallow any read/parse failure and
    return [] on the spot. Multiple bot workflows (agent_priority_writer.py,
    agent_country_trending_writer.py, agent_transfer_post.py, etc.) call
    save_posts() on overlapping schedules with no file locking, so a reader
    can catch the target file mid-write (truncated/invalid JSON) purely by
    bad timing. Treating that transient race as "there are zero posts" is
    catastrophic: the caller then does save_posts(new_posts + []), silently
    replacing the entire ~850-post database with a handful of posts. That
    happened repeatedly for ~9 hours before being caught and restored from
    git history. A short retry absorbs the race; if the file is still
    unreadable after that, we raise instead of returning an empty list, so
    a real corruption fails the run loudly rather than overwriting good data.
    """
    if not POSTS_PATH.exists():
        return []
    last_err: Exception | None = None
    for attempt in range(5):
        try:
            with open(POSTS_PATH) as f:
                return json.load(f).get("posts", [])
        except (json.JSONDecodeError, OSError) as e:
            last_err = e
            time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(
        f"Could not read {POSTS_PATH} after 5 attempts — refusing to treat "
        f"this as an empty post list (that would overwrite existing posts "
        f"on the next save_posts() call). Last error: {last_err}"
    )


def save_posts(posts: list[dict]) -> None:
    """Write blog/posts.json + posts-data.js atomically.

    Writes to a temp file in the same directory and os.replace()s it into
    place, so a concurrent load_posts() in another process can never observe
    a partially-written file — os.replace is atomic on POSIX. Also refuses
    to write a suspiciously small post list over a much larger existing one,
    as a last-resort guard against the same class of bug this fixes.
    """
    POSTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if POSTS_PATH.exists():
        try:
            existing_count = len(json.loads(POSTS_PATH.read_text()).get("posts", []))
            if existing_count >= 20 and len(posts) < existing_count * 0.5:
                raise RuntimeError(
                    f"save_posts() refused: about to write {len(posts)} posts "
                    f"over an existing {existing_count} — looks like data loss, "
                    f"not a real edit. Aborting instead of overwriting."
                )
        except (json.JSONDecodeError, OSError):
            pass  # existing file unreadable — nothing to compare against, proceed
    payload = {"posts": posts}

    tmp_path = POSTS_PATH.with_suffix(".json.tmp")
    with open(tmp_path, "w") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp_path, POSTS_PATH)

    # Also write posts-data.js so the blog works on file:// protocol
    js_path = POSTS_PATH.parent / "posts-data.js"
    js_tmp_path = js_path.with_suffix(".js.tmp")
    with open(js_tmp_path, "w", encoding="utf-8") as f:
        f.write(f"window.POSTS_DATA={json.dumps(payload, ensure_ascii=False)};\n")
    os.replace(js_tmp_path, js_path)


# ── FACEBOOK ANNOUNCEMENT (every published article, not just transfers) ───────
# agent_transfer_post.py already announces its own "transfers" category posts
# to Facebook via a heavier fact-extraction pipeline; every other category
# generated here (football, sportnews, betting, igaming, basketball, tennis,
# cricket, rugby, boxing, f1) previously had no social announcement at all.
# This is the lightweight equivalent for those: title + excerpt + link, using
# the same per-post branded image already generated by ensure_feature_image()
# above, via the same post_facebook() used everywhere else in this codebase.

_CATEGORY_HASHTAGS = {
    "football":     "#SifuFinds #Football #AfricanFootball",
    "sportnews":    "#SifuFinds #SportsNews",
    "betting":      "#SifuFinds #BettingTips #SmartBetting",
    "igaming":      "#SifuFinds #iGaming",
    "basketball":   "#SifuFinds #Basketball #NBA",
    "tennis":       "#SifuFinds #Tennis",
    "cricket":      "#SifuFinds #Cricket",
    "rugby":        "#SifuFinds #Rugby",
    "boxing":       "#SifuFinds #Boxing",
    "f1":           "#SifuFinds #F1",
    "worldcup2026": "#SifuFinds #WorldCup2026",
}

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Persistent backlog for posts whose Facebook announcement still failed
# after post_facebook()'s own in-request retries (agent3_social.py) — added
# 2026-08-08. Before this, a failure here was permanent: the post published
# fine, but its Facebook announcement was gone the moment the process
# exited, with nothing to pick it up again. Every blog-writing entrypoint in
# this codebase (agent_sports_blog.run(), agent_priority_writer.py,
# agent_country_trending_writer.py) calls announce_to_facebook() for every
# post it writes, so flushing this backlog at the top of that one shared
# function gives every one of those a real, persistent "keep trying until
# it actually posts" guarantee instead of a single best-effort attempt.
FACEBOOK_BACKLOG_PATH = Path(__file__).parent / "facebook_announce_backlog.json"
_FACEBOOK_BACKLOG_MAX_ENTRIES = 50
# A backlog entry older than this is almost certainly stale news by the time
# it would post (this pipeline publishes several times an hour) — better to
# drop it than announce day-old "breaking" news as if it were fresh.
_FACEBOOK_BACKLOG_MAX_AGE_HOURS = 48


def build_facebook_caption(post: dict) -> str:
    icon = CATEGORIES.get(post["category"], {}).get("icon", "📰")
    blog_url = f"{SITE_URL}/blog/{post['slug']}/"
    hashtags = _CATEGORY_HASHTAGS.get(post["category"], "#SifuFinds")
    return (
        f"{icon} {post['title']}\n\n"
        f"{post.get('excerpt', '').strip()}\n\n"
        f"📰 Read the full story: {blog_url}\n\n"
        f"{hashtags}"
    )


def _load_facebook_backlog() -> list[dict]:
    if FACEBOOK_BACKLOG_PATH.exists():
        try:
            return json.loads(FACEBOOK_BACKLOG_PATH.read_text()).get("pending", [])
        except (OSError, json.JSONDecodeError):
            pass
    return []


def _save_facebook_backlog(entries: list[dict]) -> None:
    FACEBOOK_BACKLOG_PATH.write_text(
        json.dumps({"pending": entries[-_FACEBOOK_BACKLOG_MAX_ENTRIES:]}, indent=2, ensure_ascii=False)
    )


def _queue_facebook_backlog(post: dict) -> None:
    image_path = post.get("_facebook_image_path")
    entries = _load_facebook_backlog()
    entries.append({
        "title": post["title"],
        "caption": build_facebook_caption(post),
        "image_path": str(image_path) if image_path else "",
        "queued_at": datetime.now(timezone.utc).isoformat(),
    })
    _save_facebook_backlog(entries)


def retry_pending_facebook_announcements() -> int:
    """Flush the backlog — called automatically at the top of every
    announce_to_facebook() so a post that failed on an earlier run (a
    different Python process, possibly a different GitHub Actions job
    entirely) gets picked up the very next time ANY writer agent announces
    a new post, not just its own retry. Returns how many were successfully
    posted this call."""
    entries = _load_facebook_backlog()
    if not entries:
        return 0

    from agent3_social import post_facebook

    now = datetime.now(timezone.utc)
    still_pending = []
    posted = 0
    for entry in entries:
        try:
            queued_at = datetime.fromisoformat(entry["queued_at"])
        except (KeyError, ValueError):
            queued_at = now
        age_hours = (now - queued_at).total_seconds() / 3600
        if age_hours > _FACEBOOK_BACKLOG_MAX_AGE_HOURS:
            print(f"  ⚠ Dropping stale Facebook backlog entry ({age_hours:.0f}h old): '{entry.get('title', '')}'")
            continue

        image_path = entry.get("image_path") or None
        if image_path and not Path(image_path).exists():
            image_path = None
        if post_facebook(entry["caption"], image_path=image_path):
            posted += 1
            print(f"  ✓ Posted previously-failed Facebook announcement: '{entry.get('title', '')}'")
        else:
            still_pending.append(entry)

    _save_facebook_backlog(still_pending)
    return posted


def announce_to_facebook(post: dict) -> bool:
    """A Facebook failure must never block blog generation or take down the
    rest of the run — but unlike a purely best-effort attempt, a failure
    here (even after post_facebook()'s own in-request retries) is queued to
    FACEBOOK_BACKLOG_PATH and retried automatically on the next call from
    ANY writer agent, so the post's announcement keeps trying until it
    actually succeeds rather than being silently lost the moment this
    process exits."""
    try:
        from agent3_social import post_facebook
        from utils.logger import log

        retry_pending_facebook_announcements()

        image_path = None
        feature_image = post.get("feature_image")
        if feature_image:
            candidate = REPO_ROOT / feature_image.lstrip("/")
            if candidate.exists():
                image_path = candidate
        # Stored as a str, never the Path itself — this dict is `post`,
        # which save_posts() later json.dump()s wholesale into posts.json.
        # A raw PosixPath here crashed every run that reached this line
        # with a real feature image (json.dump has no default encoder for
        # Path), which was most runs — see AGENT-KNOWLEDGE.md 2026-08-16.
        post["_facebook_image_path"] = str(image_path) if image_path else None

        ok = post_facebook(build_facebook_caption(post), image_path=image_path)
        log("sports_blog", "facebook_announce", "success" if ok else "failed", post["title"])
        if not ok:
            _queue_facebook_backlog(post)
            print(f"  ⚠ Facebook announcement failed after retries — queued for next attempt (blog post itself is unaffected)")
        return ok
    except Exception as e:
        print(f"  ⚠ Facebook announcement failed (blog post itself is unaffected): {e}")
        try:
            _queue_facebook_backlog(post)
        except Exception:
            pass
        return False


# ── RUN MODES ─────────────────────────────────────────────────────────────────

def run(topics: int = 1, specific_category: Optional[str] = None,
        update_ticker: bool = True) -> None:
    """Generate articles from LIVE news research."""
    print(f"🚀 Sports Blog Agent — generating {topics} article(s) from live news")

    if update_ticker:
        print("\n📡 Updating live ticker first...")
        from utils.ticker_builder import build_and_save
        build_and_save()

    existing = load_posts()
    recent_titles = {p["title"].lower()[:40] for p in existing[:30]}
    new_posts: list[dict] = []

    # Source-headline dedup shared with agent_transfer_post.py (see
    # utils/story_dedup.py). recent_titles above only matches when the LLM
    # happens to reuse the same 40-char title prefix, which almost never
    # happens for a fresh phrasing of the same real-world story — this is
    # the same duplicate-content bug already fixed for the dedicated
    # transfers feed on 2026-07-30, now closed here too after a 2026-08-01
    # site scan found 56 duplicate-title post pairs traced back to this gap.
    covered_keys = _load_covered_keys()

    categories = list(CATEGORIES.keys())
    if specific_category:
        categories = [specific_category] * topics
    else:
        categories = random.choices(categories, k=topics)

    for cat in categories:
        print(f"\n📝 Category: {cat.upper()}")
        post = generate_post(cat)

        if post is None:
            continue

        title_key = post["title"].lower()[:40]
        if title_key in recent_titles:
            print(f"  ⚠ Similar title already exists — skipping")
            continue

        post_source_keys = _source_keys(post)
        if post_source_keys & covered_keys:
            print(f"  ⚠ Underlying story already covered recently — skipping")
            continue
        covered_keys |= post_source_keys
        _record_covered_keys(post_source_keys)

        new_posts.append(post)
        recent_titles.add(title_key)
        print(f"  ✓ '{post['title']}'")
        print(f"  ✓ Tags: {', '.join(post['tags'][:3])}")
        print(f"  ✓ Sources: {', '.join(post.get('_sources', [])[:3])}")

        if cat != "transfers":  # transfers gets its own richer bulletin via agent_transfer_post.py
            if announce_to_facebook(post):
                print("  ✓ Announced on Facebook")

    if new_posts:
        all_posts = new_posts + existing
        save_posts(all_posts)
        print(f"\n✅ Added {len(new_posts)} article(s). Total in blog: {len(all_posts)}")
    else:
        print("\n⚠ No new articles generated.")


def run_daily() -> None:
    """2 articles across different categories — for GitHub Actions daily schedule."""
    cats = random.sample(list(CATEGORIES.keys()), 2)
    print(f"📅 Daily run — categories: {', '.join(cats)}")
    for cat in cats:
        run(topics=1, specific_category=cat, update_ticker=(cat == cats[0]))


def run_weekly() -> None:
    """Cover all categories — run on Mondays for a full week of content."""
    print("📅 Weekly batch run — all categories")
    # Football twice (most popular), others once
    for cat in ["football", "football", "sportnews", "betting", "igaming",
                "basketball", "tennis", "cricket", "boxing", "f1"]:
        run(topics=1, specific_category=cat, update_ticker=False)
    # Update ticker once at the end
    from utils.ticker_builder import build_and_save
    build_and_save()


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Sports Blog Writer Agent")
    parser.add_argument("--topics", type=int, default=1)
    parser.add_argument("--category", type=str, default=None,
                        choices=list(CATEGORIES.keys()))
    parser.add_argument("--mode", type=str, default="single",
                        choices=["single", "daily", "weekly"])
    parser.add_argument("--ticker-only", action="store_true",
                        help="Only update ticker.json, don't write articles")
    args = parser.parse_args()

    if args.ticker_only:
        from utils.ticker_builder import build_and_save
        build_and_save()
    elif args.mode == "daily":
        run_daily()
    elif args.mode == "weekly":
        run_weekly()
    else:
        run(topics=args.topics, specific_category=args.category)
