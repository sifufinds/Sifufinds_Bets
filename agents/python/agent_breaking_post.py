"""
agent_breaking_post.py — Year-round breaking sport news bot for SifuFinds.

Why this exists: agent_transfer_post.py only runs inside the Jan / Jun-Aug
transfer windows, and agent_sports_blog.py's long betting-angle articles are
frequently rejected by the fact-checker, so a genuinely big story (a manager
sacked, a star's death, a season-ending injury) could go uncovered for days.

Flow, each run:
  1. utils.news_fetcher.fetch_breaking() — fresh, high-impact headlines from
     trusted outlets only (sackings, appointments, deaths, retirements, bans,
     season-ending injuries involving a notable club/player/country/competition).
  2. Skip anything already covered (utils.story_dedup — shared with the other
     news agents).
  3. Write a SHORT (150-300 word), source-grounded news article. Deliberately
     not the 700-900 word betting format: a short factual piece has far less
     surface for the fact-checker to reject. It only restates what the
     headlines/descriptions say.
  4. Fact-check (agent_fact_checker.check_post), save to blog/posts.json,
     post to Telegram / Facebook / Instagram / X.
  5. If every LLM tier is exhausted, repost the attributed headline directly
     (no blog post, always crediting the outlet) so coverage never goes dark.

Usage:
  python3 agent_breaking_post.py             # normal run
  python3 agent_breaking_post.py --dry-run   # preview only
  python3 agent_breaking_post.py --no-twitter --no-instagram
"""
import argparse
import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

from llm import ask, AIProvidersExhausted
from utils.logger import log
from utils.news_fetcher import fetch_breaking
from utils.story_dedup import headline_key as _headline_key, \
    load_covered_keys as _load_covered_keys, record_covered_keys as _record_covered_keys
from utils.tweet_text import trim_to_limit as _trim_to_limit
from utils.title_content_match import check_africa_framing
from agent_fact_checker import check_post as fact_check_post
from agent_sports_blog import load_posts, save_posts, discard_feature_image
from agent_telegram_offers import send_to_channel, send_photo_to_channel, SITE_URL
from agent3_social import post_facebook, post_instagram
from agent_twitter_posts import _post_tweet as post_twitter
from agent_transfer_post import (
    _post_with_retry, _usable_source_image, local_feature_image_path, GENERIC_SOCIAL_IMAGE,
)
from generate_blog_feature_image import ensure_feature_image

AUTHOR = "Sport News Desk"
MAX_ITEMS_FOR_PROMPT = 4
MIN_BODY_WORDS = 60
HASHTAGS = "#BreakingNews #SifuFinds #Football #SportsNews"

SYSTEM_PROMPT = """You are a UK-based sports news writer for SifuFinds, a site for African sports fans.
Write a SHORT breaking-news article (80 to 180 words) from the real headlines supplied. If the sources give little detail, write fewer words. Never pad with background, career history, reactions or context that the sources do not state.

NON-NEGOTIABLE RULES:
- Use ONLY facts stated in the supplied headlines/descriptions. Never invent a quote, score, date, fee, reason, statistic or detail.
- If the sources don't say why something happened, don't say why. Say "reports have not confirmed".
- Attribute claims to the outlet that reported them (e.g. "according to Sky Sports").
- No betting advice, no odds, no bookmaker mentions, no predictions.
- UK English (favourite, organise, side, pitch). No em dashes or en dashes joining clauses.
- Plain, direct, human news style. Answer the who/what/when in the first two sentences.
- Do not frame the story as African unless the sources name an African country, club or competition.
- Finish with one sentence saying the story is developing.

Return exactly this format and nothing else:
===META===
{"title": "headline, max 70 chars", "slug": "lowercase-hyphen-slug", "excerpt": "one sentence, max 150 chars", "tags": ["3 to 5 short tags"]}
===BLOG===
the article body in markdown (no H1, no headings needed)
===END==="""


def _extract(text: str, start: str, end: str) -> str:
    if start not in text:
        return ""
    chunk = text.split(start, 1)[1]
    return chunk.split(end, 1)[0].strip() if end in chunk else chunk.strip()


def _clean_json(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("```")[1]
        if s.startswith("json"):
            s = s[4:]
    return s.strip()


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80]


def _strip_outlet(title: str) -> str:
    """Google News titles end with ' - Outlet'; drop it for display."""
    return re.sub(r"\s+-\s+[^-]{2,30}$", "", title).strip()


def pick_story(items: list[dict], extra_covered: set[str] | None = None) -> list[dict]:
    """The freshest not-yet-covered item plus any other fresh items sharing
    at least two significant title words (same story, other outlets)."""
    covered = _load_covered_keys() | (extra_covered or set())
    lead = next((i for i in items if _headline_key(i["title"]) not in covered), None)
    if lead is None:
        return []

    def words(t: str) -> set[str]:
        return {w for w in re.findall(r"[a-z]{4,}", _strip_outlet(t).lower())}

    lead_words = words(lead["title"])
    group = [lead]
    for other in items:
        if other is lead or len(group) >= MAX_ITEMS_FOR_PROMPT:
            continue
        if len(lead_words & words(other["title"])) >= 2:
            group.append(other)
    return group


def write_article(group: list[dict]) -> dict | None:
    today = datetime.now(timezone.utc).strftime("%A, %d %B %Y")
    sources_text = "\n".join(
        f"- [{i['source']}] {_strip_outlet(i['title'])}: {i.get('description', '')[:400]}"
        for i in group
    )
    raw = ask(SYSTEM_PROMPT, f"TODAY: {today}\n\nREAL HEADLINES:\n{sources_text}", prefer_accuracy=True)
    meta_raw = _extract(raw, "===META===", "===BLOG===")
    body = _extract(raw, "===BLOG===", "===END===")
    if not meta_raw or len(body.split()) < MIN_BODY_WORDS:
        print("  ✗ LLM response missing sections or too short")
        return None
    try:
        meta = json.loads(_clean_json(meta_raw))
    except json.JSONDecodeError as e:
        print(f"  ✗ Meta JSON parse error: {e}")
        return None

    title = str(meta.get("title", "")).strip()
    if not title:
        return None
    now = datetime.now(timezone.utc)
    post = {
        "id": f"post-{now.strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}",
        "category": "sportnews",
        "title": title,
        "slug": _slugify(meta.get("slug") or title),
        "excerpt": str(meta.get("excerpt", ""))[:155],
        "body": body,
        "author": AUTHOR,
        "published_at": now.isoformat(),
        "image_color": "#7c3aed",
        "image_icon": "🗞️",
        "tags": meta.get("tags", []) if isinstance(meta.get("tags"), list) else [],
        "featured": False,
        "bookmaker_featured": "",
        "read_time": 2,
        "_sources": [i["source"] for i in group],
        "_source_items": [
            {"title": i["title"], "url": i["url"], "image": i.get("image", ""),
             "source": i["source"], "description": i.get("description", "")}
            for i in group
        ],
    }
    return post


# ── Social copy ───────────────────────────────────────────────────────────────

def _source_line(sources: list[str]) -> str:
    return f"📰 Source: {', '.join(dict.fromkeys(sources))}"


def build_telegram(post: dict) -> str:
    url = f"{SITE_URL}/blog/{post['slug']}/"
    return (f"🚨 {post['title']}\n\n{post['excerpt']}\n\n{_source_line(post['_sources'])}\n"
            f'📰 Full story: <a href="{url}">{post["title"]}</a>')


def build_facebook(post: dict) -> str:
    url = f"{SITE_URL}/blog/{post['slug']}/"
    return (f"🚨 {post['title']}\n\n{post['excerpt']}\n\n{_source_line(post['_sources'])}\n"
            f"📰 Full story: {url}\n\n{HASHTAGS}")


def build_instagram(post: dict) -> str:
    return (f"🚨 {post['title']}\n\n{post['excerpt']}\n\n{_source_line(post['_sources'])}\n"
            f"👉 Link in bio for the full story\n\n.\n.\n.\n{HASHTAGS}")


def build_twitter(post: dict) -> str:
    url = f"{SITE_URL}/blog/{post['slug']}/"
    return _trim_to_limit(f"🚨 {post['title']}\n\n{_source_line(post['_sources'])}\n👉 {url}\n\n#BreakingNews #SifuFinds")


def build_raw(item: dict, kind: str) -> str:
    title = _strip_outlet(item["title"])
    desc = item.get("description", "").replace("\xa0", " ").strip()
    # Google News descriptions just repeat the headline plus the outlet name.
    novel = desc and not desc.lower().startswith(title.lower()[:40])
    body = f"🚨 {title}\n\n" + (f"{desc[:220]}\n\n" if novel else "")
    body += f"📰 Source: {item['source']}\n"
    if kind == "telegram":
        return body + f'🔗 <a href="{item["url"]}">Read the full story</a>'
    if kind == "instagram":
        return body + f"👉 Link in bio for more\n\n.\n.\n.\n{HASHTAGS}"
    if kind == "twitter":
        return _trim_to_limit(body + f"🔗 {item['url']}\n\n#BreakingNews #SifuFinds")
    return body + f"🔗 {item['url']}\n\n{HASHTAGS}"


def _dispatch(post_image: str | None, local_image, texts: dict[str, str],
              flags: dict[str, bool]) -> dict[str, bool]:
    results: dict[str, bool] = {}
    if flags["telegram"]:
        if post_image or local_image:
            results["telegram"] = _post_with_retry("telegram", send_photo_to_channel, post_image or local_image, texts["telegram"])
        else:
            results["telegram"] = _post_with_retry("telegram", send_to_channel, texts["telegram"])
    if flags["facebook"]:
        results["facebook"] = _post_with_retry(
            "facebook", post_facebook, texts["facebook"],
            image_path=local_image if not post_image else None, image_url=post_image)
    if flags["instagram"]:
        results["instagram"] = _post_with_retry(
            "instagram", post_instagram, texts["instagram"], image_url=post_image or GENERIC_SOCIAL_IMAGE)
    if flags["twitter"]:
        results["twitter"] = _post_with_retry("twitter", post_twitter, texts["twitter"])
    for name, ok in results.items():
        print(f"{'✓ Posted to' if ok else '✗ Failed:'} {name}")
    return results


def _best_image(group: list[dict]) -> str | None:
    for i in group:
        if _usable_source_image(i.get("image", ""), i.get("title", "")):
            return i["image"]
    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False, **platforms: bool) -> tuple[dict | None, dict[str, bool]]:
    flags = {p: platforms.get(p, True) for p in ("telegram", "facebook", "instagram", "twitter")}
    log("breaking_post", "start", "running")

    items = fetch_breaking()
    group = pick_story(items)
    if not group:
        print("⚠ No fresh, uncovered breaking story this cycle.")
        log("breaking_post", "pick", "skipped", "no fresh story")
        return None, {}
    lead = group[0]
    print(f"📡 Breaking story: {_strip_outlet(lead['title'])} ({lead['source']}, {lead.get('age_hours', '?')}h old)")
    image = _best_image(group)

    existing = load_posts()
    post = None
    try:
        post = write_article(group)
    except AIProvidersExhausted as e:
        print(f"  ⚠ {e} — falling back to attributed headline repost")
        log("breaking_post", "generate", "ai_exhausted_fallback", str(e))

    if post is not None:
        violation = check_africa_framing(post["title"], post["slug"], post["body"])
        passed, fc_flags = fact_check_post(post)
        if violation or not passed:
            print(f"  ✗ Held back (framing={violation!r}, fact-check={fc_flags}) — using headline repost instead")
            post = None
        elif any(p["slug"] == post["slug"] for p in existing):
            post["slug"] = f"{post['slug']}-{post['published_at'][:10]}"

    if post is None:
        texts = {k: build_raw(lead, k) for k in ("telegram", "facebook", "instagram", "twitter")}
        print("\n" + texts["telegram"] + "\n")
        if dry_run:
            print("Dry run — nothing sent.")
            return None, {}
        results = _dispatch(image, None, texts, flags)
        if any(results.values()):
            _record_covered_keys({_headline_key(i["title"]) for i in group})
        return None, results

    feature = ensure_feature_image(post)
    if feature:
        post["feature_image"] = feature
    local_image = None if image else local_feature_image_path(post)
    texts = {"telegram": build_telegram(post), "facebook": build_facebook(post),
             "instagram": build_instagram(post), "twitter": build_twitter(post)}
    print(f"✓ Article ready: '{post['title']}'\n\n{post['body']}\n\n" + texts["telegram"] + "\n")

    if dry_run:
        discard_feature_image(post)
        print("Dry run — blog post NOT saved, nothing sent.")
        return post, {}

    post.pop("_source_items", None)
    sources = post.pop("_sources")
    save_posts([post] + existing)
    _record_covered_keys({_headline_key(i["title"]) for i in group})
    post["_sources"] = sources
    results = _dispatch(image, local_image, texts, flags)
    for name, ok in results.items():
        log("breaking_post", name, "success" if ok else "failed", post["title"])
    return post, results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Breaking Sport News Bot")
    parser.add_argument("--dry-run", action="store_true")
    for p in ("telegram", "facebook", "instagram", "twitter"):
        parser.add_argument(f"--no-{p}", dest=p, action="store_false")
    args = parser.parse_args()
    _, results = run(dry_run=args.dry_run, telegram=args.telegram, facebook=args.facebook,
                     instagram=args.instagram, twitter=args.twitter)
    if args.dry_run:
        sys.exit(0)
    if results and not any(results.values()):
        print("\n✗✗✗ Every requested platform failed — flagging as a real failure.")
        sys.exit(1)
    sys.exit(0)
