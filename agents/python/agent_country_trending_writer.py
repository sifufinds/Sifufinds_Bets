"""
Country Trending Writer Agent — turns genuinely country-specific trending
keyword gaps from agent_content_priority.py's queue into real, published,
country-focused blog posts, closing the loop agent_trending_keywords.py's
research alone never did.

Distinct from agent_priority_writer.py (evergreen "best betting sites
{country}" guides, no news angle) and from agent_sports_blog.py (pan-African
news, no country targeting): this agent is the country x trending
intersection — a real, fresh, country-specific story (sourced via
utils/news_fetcher.py's fetch_country_trending(), see that module's
docstring for why "trending in Kenya" now means a story actually trending
in Kenya, not a shared global headline cycled by country name), written
with that country's own bettors as the explicit audience and grounded in
that country's own real bookmaker/payment/regulator data (utils/site_data.py
— same source agent_priority_writer.py already trusts).

Only ever writes an item agent_content_priority.py marked writer_actionable:
that already excludes any story agent_sports_blog.py's pan-African pipeline
covered first (utils/story_dedup.py's shared registry — see
agent_content_priority.py's docstring). After a successful write, this
agent also RECORDS the story into that same shared registry, so
agent_sports_blog.py's future runs recognise it as covered too and the
duplicate-content risk is closed in both directions.

Usage:
    python agent_country_trending_writer.py                # next batch
    python agent_country_trending_writer.py --count 2
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))

from llm import ask, AIProvidersExhausted
from config import SITE_URL
from utils.serp_research import research
from utils.story_dedup import headline_key, load_covered_keys, record_covered_keys
from agent_fact_checker import check_post as fact_check_post
from agent_priority_writer import _country_block, _bookmaker_block, _COUNTRY_CODE_BY_NAME
from utils.title_content_match import check_africa_framing
from agent_sports_blog import (
    CATEGORIES, _extract, _clean_json, load_posts, save_posts,
    announce_to_facebook, discard_feature_image,
)

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from generate_blog_feature_image import ensure_feature_image

QUEUE_PATH = Path(__file__).parent / "content_priority_queue.json"
STATE_PATH = Path(__file__).parent / "country_trending_writer_state.json"
COUNT = 3

SYSTEM_PROMPT = f"""You are the Country Trending Desk for SifuFinds ({SITE_URL}), Africa's #1 betting comparison website.

YOUR JOB: Write a country-specific news/betting article about the ONE real, current story given to you, targeting the exact keyword and country given. The audience is bettors in that ONE country specifically, not "African bettors" generally — every angle, example, and recommendation should read as written for that country's market.

ACCURACY RULES — NON-NEGOTIABLE:
- Only write about the real story given to you below — do not invent scores, signings, transfers, or events beyond what the headline/snippet states
- Odds are the one exception to "don't invent numbers": always estimate odds in realistic ranges (1.30-12.00), always framed as illustrative market pricing (e.g. "odds are trading around 4.50 with Bet9ja"), never as a claimed fact
- NEVER invent a transfer fee, specific date, statistic, or direct quote not present in the source snippet — if it isn't given, write "undisclosed" or omit it rather than guess
- Attribute the story to its outlet by name at least once (shown in the source block below)
- Ground every bonus/bookmaker/payment-method fact ONLY in the REAL COUNTRY DATA and REAL BOOKMAKER DATA blocks provided — never invent a bookmaker name, bonus amount, or payment method not listed there
- Never claim a "guaranteed win", "risk-free bet", or anything that overstates a gambling outcome

BRAND VOICE:
- UK English throughout (favourite, colour, organise, licence as a noun — never US spellings)
- Confident, knowledgeable, street-smart analyst who clearly knows this specific country's betting market; vary sentence length deliberately; no formulaic AI openers ("In the world of...", "When it comes to..."); no repeated transition words (Furthermore/Moreover/Additionally)
- NEVER use em dashes or en dashes to join clauses — rewrite as separate sentences or commas instead
- Answer the core question in the first 2-3 sentences, in plain, quotable, self-contained language (this is read by AI answer engines, not just Google)

ARTICLE REQUIREMENTS:
- 700-950 words, grounded in the real story and real country data provided
- Explicitly name the target country multiple times and reference its real bookmakers/payment methods from the data given, not generic African examples
- Compare odds across at least 2 of the real bookmakers provided for this country
- Include a responsible gambling section (a real paragraph, not just a heading)
- Include a short "## FAQ" section with at least 3 "### "-level questions specific to this story and country, each answer a complete standalone paragraph
- End with a CTA paragraph mentioning {SITE_URL} as plain text — do NOT wrap it in a markdown link
- FINAL LINE must be exactly: *18+ | Bet Responsibly | T&Cs Apply*

FAQ FORMAT — EXACT, THIS IS A COMMON MISTAKE:
- Heading exactly: ## FAQ
- Each question is a heading starting with exactly "### " followed by your own question ending in "?" — no "Q:"/"A:" labels, no extra "#" characters anywhere on the heading line
- Answer is a plain paragraph directly under the heading, nothing else

LINKING RULES — NON-NEGOTIABLE:
- NEVER write a markdown link to any {SITE_URL}/<path> page
- The site automatically hyperlinks bookmaker names, country names, and key terms for you after you submit — only mention them in plain text, never link them yourself
- External links (regulators, FIFA, UEFA, CAF, etc.) are also auto-inserted — mention the name in plain text only

OUTPUT FORMAT — return EXACTLY this structure, nothing outside the markers:

===META===
{{
  "title": "Specific title referencing the real story AND the target country (max 80 chars)",
  "slug": "url-slug-format",
  "excerpt": "150-200 char excerpt naming the country and the real story",
  "tags": ["Tag1", "Tag2", "Tag3", "Tag4"],
  "bookmaker_featured": "top bookmaker name from the real data",
  "read_time": 5
}}
===BLOG===
[Full article in plain markdown, 700-950 words]
[Must include the ## FAQ section using the EXACT format above]
[Must include responsible gambling section]
[Final line: *18+ | Bet Responsibly | T&Cs Apply*]
===END==="""

MIN_WORD_COUNT = 600
MIN_FAQ_ENTRIES = 3
REQUIRED_FINAL_LINE = "*18+ | Bet Responsibly | T&Cs Apply*"

_BAD_FAQ_HEADING_RE = re.compile(r"^#{4,}\s", re.MULTILINE)
_QA_LABEL_RE = re.compile(r"^#{1,6}\s*[QA][:.]\s", re.MULTILINE)
_FAQ_QUESTION_RE = re.compile(r"^###\s+\S", re.MULTILINE)
_STRAY_HASH_IN_HEADING_RE = re.compile(r"^###\s+.*#", re.MULTILINE)


def _validate_body(body: str) -> list[str]:
    """Same deterministic quality gate shape as agent_priority_writer.py's
    _validate_body(), tuned for this agent's shorter news-style word count
    and FAQ requirement."""
    failures = []
    word_count = len(body.split())
    if word_count < MIN_WORD_COUNT:
        failures.append(f"only {word_count} words (minimum {MIN_WORD_COUNT})")
    if "## FAQ" not in body and "## Frequently Asked Questions" not in body:
        failures.append("no '## FAQ' section heading found")
    if len(_FAQ_QUESTION_RE.findall(body)) < MIN_FAQ_ENTRIES:
        failures.append(f"fewer than {MIN_FAQ_ENTRIES} '### ' FAQ question headings found")
    if _BAD_FAQ_HEADING_RE.search(body):
        failures.append("found a heading with 4+ '#' characters — FAQ questions must use exactly '### '")
    if _QA_LABEL_RE.search(body):
        failures.append("found a 'Q:'/'A:' label on a heading line — questions must be plain headings with no label")
    if _STRAY_HASH_IN_HEADING_RE.search(body):
        failures.append("found a stray '#' character inside a '### ' FAQ heading line")
    last_line = next((l.strip() for l in reversed(body.strip().splitlines()) if l.strip()), "")
    if last_line != REQUIRED_FINAL_LINE:
        failures.append(f"final line was '{last_line}', must be exactly '{REQUIRED_FINAL_LINE}'")
    return failures


def _load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return default


def generate_country_trending_post(item: dict) -> tuple[Optional[dict], str]:
    """Returns (post, reason) — same contract as
    agent_priority_writer.generate_priority_post(): post is None on
    failure, reason is a short machine-readable code so a GitHub Actions
    run's diagnostic detail survives after the ephemeral runner tears down
    (see that function's docstring for the incident this pattern fixed)."""
    country_name = item["country"]
    code = _COUNTRY_CODE_BY_NAME.get(country_name)
    if not code:
        print(f"  ✗ Unknown country code for '{country_name}' — skipping")
        return None, "unknown_country_code"

    country_block, _country_data = _country_block(code)
    bookmaker_block = _bookmaker_block(code)
    if not country_block or not bookmaker_block:
        print(f"  ✗ No real site data found for {country_name} — skipping (never inventing bookmaker facts)")
        return None, "no_site_data"

    source_headline = item.get("source_headline", "")
    if not source_headline:
        print(f"  ✗ No source headline on this trending item — skipping (never writing ungrounded content)")
        return None, "no_source_headline"

    print(f"  🔍 Running SERP research for '{item['keyword']}'...")
    serp_block = research(item["keyword"], country_name)

    source_block = (
        f"[{item.get('source_url', '')}] {source_headline}\n"
        f"{item.get('source_description', '')}"
    ).strip()

    user_message = f"""TARGET KEYWORD (must be the primary focus): {item['keyword']}
TARGET COUNTRY (write specifically for this market): {country_name}

THE REAL STORY (write about this specific story, nothing invented):
{source_block}

REAL COUNTRY DATA (use exactly, never invent):
{country_block}

REAL BOOKMAKER DATA (use exactly, never invent — these are the only bookmakers/offers you may reference):
{bookmaker_block}

{serp_block}

Write the article now, following every rule in the system prompt exactly."""

    try:
        meta = None
        blog_body = ""
        last_failures: list[str] = []
        current_message = user_message
        for attempt in range(1, 3):
            print(f"  🤖 Generating article with LLM (attempt {attempt}/2)...")
            raw = ask(SYSTEM_PROMPT, current_message)

            meta_raw = _extract(raw, "===META===", "===BLOG===")
            body_candidate = _extract(raw, "===BLOG===", "===END===", end_required=False)
            if not meta_raw or not body_candidate:
                print(f"  ✗ LLM response missing required sections")
                if attempt == 2:
                    return None, "missing_output_markers"
                current_message = user_message + "\n\nYour previous response was missing the ===META=== or ===BLOG=== markers. Return EXACTLY the structure specified, nothing else."
                continue

            failures = _validate_body(body_candidate)
            if not failures:
                meta = json.loads(_clean_json(meta_raw))
                blog_body = body_candidate
                break

            last_failures = failures
            print(f"  ⚠ Draft failed quality gate: {'; '.join(failures)}")
            if attempt == 2:
                print(f"  ✗ Still failing after retry — skipping this item rather than publishing a substandard article")
                return None, "quality_gate: " + "; ".join(failures)
            current_message = (
                user_message
                + "\n\nYour previous attempt failed these checks, fix ALL of them this time:\n"
                + "\n".join(f"- {f}" for f in failures)
            )

        if meta is None:
            return None, "quality_gate: " + "; ".join(last_failures) if last_failures else "unknown"
        cat_meta = CATEGORIES["betting"]

        post = {
            "id": f"post-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-trending-{code.lower()}",
            "category": "betting",
            "title": meta.get("title", ""),
            "slug": meta.get("slug", ""),
            "excerpt": meta.get("excerpt", ""),
            "body": blog_body.strip(),
            "author": cat_meta["author"],
            "published_at": datetime.now(timezone.utc).isoformat(),
            "image_color": cat_meta["color"],
            "image_icon": cat_meta["icon"],
            "tags": meta.get("tags", []) or [country_name, "Trending"],
            "featured": False,
            "bookmaker_featured": meta.get("bookmaker_featured", ""),
            "read_time": meta.get("read_time", 5),
            "_priority_keyword": item["keyword"],
            # Grounds the fact-checker (agent_fact_checker.check_post reads
            # this) and doubles as this agent's own dedup source — the same
            # shape agent_sports_blog.py already produces.
            "_source_items": [{
                "title": source_headline,
                "url": item.get("source_url", ""),
                "image": "",
                "source": item.get("source_url", "") or country_name,
                "description": item.get("source_description", ""),
            }],
        }
        feature_image = ensure_feature_image(post)
        if feature_image:
            post["feature_image"] = feature_image

        # Same title/content topic-match gate as agent_sports_blog.py — see
        # utils/title_content_match.py's docstring for the live "Transfer
        # Frenzy in Africa" incident this guards against.
        africa_violation = check_africa_framing(post["title"], post["slug"], post["body"])
        if africa_violation:
            print(f"  ✗ Title/content check held back this article: {africa_violation}")
            discard_feature_image(post)
            return None, "africa_framing: " + africa_violation

        passed, flags = fact_check_post(post)
        if not passed:
            print(f"  ✗ Fact-checker held back this article: {flags}")
            discard_feature_image(post)
            return None, "fact_check: " + "; ".join(flags)
        return post, ""

    except json.JSONDecodeError as e:
        print(f"  ✗ JSON parse error: {e}")
        return None, f"json_parse_error: {e}"
    except AIProvidersExhausted:
        raise
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None, f"error: {e}"


def run(count: int = COUNT) -> int:
    queue = _load_json(QUEUE_PATH, {"items": []})
    state = _load_json(STATE_PATH, {"posted": {}})
    posted = state.setdefault("posted", {})
    existing = load_posts()
    recent_titles = {p["title"].lower()[:40] for p in existing[:30]}
    covered_keys = load_covered_keys()

    candidates = []
    for item in queue.get("items", []):
        if item.get("source") != "trending" or not item.get("writer_actionable"):
            continue
        if item["keyword"] in posted:
            continue
        headline = item.get("source_headline", "")
        if headline and headline_key(headline) in covered_keys:
            # Covered by another agent (or an earlier cycle of this one)
            # since the queue was last built — never write a duplicate.
            posted[item["keyword"]] = {"skipped": "already_covered_since_queue_built"}
            continue
        candidates.append(item)

    if not candidates:
        print("Country Trending Writer — no un-actioned writer-actionable trending items in the queue. "
              "Run agent_content_priority.py first, or everything actionable is already written/covered.")
        state["posted"] = posted
        state["last_run"] = {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "candidates_available": 0,
            "attempted": 0,
            "written": 0,
            "attempts": [],
        }
        STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))
        return 0

    batch = candidates[:count]
    print(f"Country Trending Writer Agent — {len(candidates)} un-actioned trending item(s), writing {len(batch)} this run")

    new_posts = []
    written = 0
    attempts_log = []
    for item in batch:
        print(f"\n📝 [{item['country']}] {item['keyword']} (score {item['score']})")
        try:
            post, reason = generate_country_trending_post(item)
        except AIProvidersExhausted:
            # Same reasoning as agent_priority_writer.py's identical guard:
            # every remaining item in this batch would fail the same way,
            # so stop the batch early but still persist what we learned.
            print(f"  ✗ All LLM providers exhausted — stopping this batch early")
            attempts_log.append({"keyword": item["keyword"], "country": item["country"], "result": "failed", "reason": "AIProvidersExhausted"})
            break
        if post is None:
            attempts_log.append({"keyword": item["keyword"], "country": item["country"], "result": "failed", "reason": reason})
            continue

        title_key = post["title"].lower()[:40]
        if title_key in recent_titles:
            print(f"  ⚠ Similar title already exists — skipping")
            attempts_log.append({"keyword": item["keyword"], "country": item["country"], "result": "skipped", "reason": "similar_title_exists"})
            discard_feature_image(post)
            continue

        new_posts.append(post)
        recent_titles.add(title_key)
        posted[item["keyword"]] = {
            "slug": post["slug"],
            "posted_at": datetime.now(timezone.utc).isoformat(),
        }

        # Record into the SHARED story registry so agent_sports_blog.py's
        # future pan-African runs also recognise this story as covered —
        # closes the duplicate-content risk in both directions (see module
        # docstring).
        headline = item.get("source_headline", "")
        if headline:
            new_key = {headline_key(headline)}
            covered_keys |= new_key
            record_covered_keys(new_key)

        attempts_log.append({"keyword": item["keyword"], "country": item["country"], "result": "written", "slug": post["slug"]})
        written += 1
        print(f"  ✓ '{post['title']}'")
        if announce_to_facebook(post):
            print("  ✓ Announced on Facebook")

    if new_posts:
        save_posts(new_posts + existing)
        print(f"\n✅ Wrote {written} country trending post(s). Total in blog: {len(new_posts) + len(existing)}")
    else:
        print("\n⚠ No new posts written this run.")

    state["last_run"] = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "candidates_available": len(candidates),
        "attempted": len(batch),
        "written": written,
        "attempts": attempts_log,
    }
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=COUNT)
    args = parser.parse_args()
    return run(count=args.count)


if __name__ == "__main__":
    sys.exit(main())
