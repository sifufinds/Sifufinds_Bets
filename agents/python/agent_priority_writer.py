"""
Priority Writer Agent — turns the highest-priority writer-actionable
keyword gaps from agent_content_priority.py's queue into real, published,
SEO-optimised evergreen guide posts.

Closes the loop that was missing until 2026-08-02: keyword-gap research
alone never turned into scheduled content (agent5_plan.py's weekly
calendar was the closest thing, but nothing consumed it automatically).
This agent is deliberately NOT a reuse of agent_sports_blog.py's engine —
that engine is news-grounded ("only write about stories explicitly listed
in the provided headlines", enforced as a hard rule) and has no angle for
an evergreen commercial keyword like "best betting sites Nigeria 2026",
which has no news event behind it. This agent grounds itself instead in
the real per-country bookmaker/bonus/regulator data already embedded in
assets/shared.js (via utils/site_data.py — the same data the site itself
renders to visitors) plus free SERP competitor research
(utils/serp_research.research()), following the exact protocol already
documented in CLAUDE.md's "Blog Post Creation — MANDATORY Research
Protocol". Reuses agent_sports_blog.py's storage/image/fact-check
machinery rather than duplicating it.

Usage:
    python agent_priority_writer.py                # write the next N queue items
    python agent_priority_writer.py --count 2
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

from llm import ask_long, AIProvidersExhausted
from config import SITE_URL
from utils.serp_research import research
from utils.site_data import load_country_data, load_bookmakers
from agent_fact_checker import check_post as fact_check_post
from agent_content_priority import EVERGREEN_CONTENT_TYPES
from utils.title_content_match import check_africa_framing
from agent_sports_blog import (
    CATEGORIES, _extract, _clean_json, load_posts, save_posts, announce_to_facebook,
)

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from generate_blog_feature_image import ensure_feature_image

QUEUE_PATH = Path(__file__).parent / "content_priority_queue.json"
STATE_PATH = Path(__file__).parent / "priority_writer_state.json"
COUNT = 3

_COUNTRY_CODE_BY_NAME = {
    "Nigeria": "NG", "Kenya": "KE", "Ghana": "GH", "South Africa": "ZA",
    "Tanzania": "TZ", "Uganda": "UG", "Zambia": "ZM", "Ethiopia": "ET",
    "Ivory Coast": "CI", "Cameroon": "CM", "Senegal": "SN", "Rwanda": "RW",
    "Zimbabwe": "ZW", "Malawi": "MW", "Mozambique": "MZ", "Angola": "AO",
    "DR Congo": "CD", "Botswana": "BW", "Namibia": "NA", "Egypt": "EG",
    "Morocco": "MA", "Sierra Leone": "SL", "Liberia": "LR",
}

GUIDE_ANGLE_BRIEFS = {
    "best_sites": (
        "Write a 'best betting sites in {country}' comparison guide. Rank the "
        "REAL bookmakers provided below by welcome offer, licensing, and payment "
        "support. Help a reader pick the right one for their needs."
    ),
    "best_bonus": (
        "Write a 'best betting bonus in {country}' guide focused specifically on "
        "welcome bonuses and promo codes. Compare the REAL bonus terms provided "
        "below, explain wagering requirements in plain language, and note which "
        "bonus suits which type of bettor."
    ),
    "how_to_bet": (
        "Write a beginner's step-by-step 'how to bet online in {country}' guide: "
        "choosing a licensed bookmaker from the REAL options below, registering, "
        "depositing via the REAL local payment methods provided, placing a first "
        "bet, understanding odds formats, and withdrawing winnings safely."
    ),
    "safest_apps": (
        "Write a 'safest betting apps in {country}' guide focused on legitimacy "
        "and safety: licensing/regulation (use the REAL regulator provided), the "
        "REAL bookmaker names provided, secure payment methods, and red flags to "
        "avoid with unlicensed operators."
    ),
}

SYSTEM_PROMPT = f"""You are the Betting Guide Writer for SifuFinds ({SITE_URL}), Africa's #1 betting comparison website.

YOUR JOB: Write an authoritative, evergreen, SEO-optimised guide targeting the exact keyword and country given to you. This is commercial/informational content, not news — ground every bonus/bookmaker fact ONLY in the REAL BOOKMAKER DATA block provided. Never invent bonus amounts, promo codes, or bookmaker names not listed there.

ACCURACY RULES — NON-NEGOTIABLE:
- Only state bonus amounts, promo terms, and bookmaker names exactly as given in the REAL BOOKMAKER DATA block below
- Never claim a "guaranteed win", "risk-free bet", or anything that overstates a gambling outcome
- Always note that wagering requirements/T&Cs apply and the offer requires 18+
- Compare at least 3 of the real bookmakers provided — never promote just one

BRAND VOICE:
- UK English throughout (favourite, colour, organise, licence as a noun — never US spellings)
- Confident, knowledgeable, street-smart African analyst; vary sentence length deliberately; no formulaic AI openers ("In the world of...", "When it comes to..."); no repeated transition words (Furthermore/Moreover/Additionally)
- NEVER use em dashes or en dashes to join clauses — rewrite as separate sentences or commas instead
- Answer the core question in the first 2-3 sentences, in plain, quotable, self-contained language (this is read by AI answer engines, not just Google)

ARTICLE REQUIREMENTS — LENGTH IS A HARD REQUIREMENT, NOT A SUGGESTION:
- The article body MUST be at least 1200 words of substantial prose. Count as you write. A short listicle is a FAILED response — write full paragraphs under every heading, not just bullet points. Cover: an introduction that directly answers the keyword's intent, a detailed comparison section, a "how to choose" section weighing the real trade-offs between the bookmakers given, a step-by-step section relevant to the guide angle, licensing/regulation, payment methods, and responsible gambling — each of these is its own paragraph or more, not one line.
- At least one markdown comparison table (bookmaker name / top offer / min deposit / payment methods)
- Mention the country's real payment methods and regulator/licensing body given below at least once
- Include a responsible gambling section (a real paragraph, not just a heading)
- End with a short CTA paragraph mentioning {SITE_URL} as plain text — do NOT wrap it in a markdown link
- FINAL LINE of the article must be exactly: *18+ | Bet Responsibly | T&Cs Apply*

FAQ SECTION — EXACT FORMAT REQUIRED, THIS IS A COMMON MISTAKE, FOLLOW IT PRECISELY:
- Start the section with exactly: ## FAQ
- Each question is a heading line starting with exactly three "#" characters and one space, then YOUR OWN question about this specific topic, ending in "?" — nothing else on that line
- Never put "#" characters anywhere else on a heading line. Never write two heading markers on one line, never write a "#" character inside the question text itself
- Do NOT prefix the question with "Q:" or the answer with "A:" — write the question as a heading and the answer as a plain paragraph directly under it, nothing else
- Include at least 4 questions specific to this keyword/country/angle, each answer a complete, standalone paragraph (2-3 sentences)
- FORMAT TEMPLATE (structure only — write your own real question and answer, do not reuse this wording):
  ### <your own question here, one sentence, ending in a question mark>
  <your own two-to-three sentence answer here>
- WRONG (never do this): "#### Q: Is it safe..." or "**Q:** Is it safe..." or "### ### Is it safe..." — these are all mistakes that break the page

LINKING RULES — NON-NEGOTIABLE:
- NEVER write a markdown link to any {SITE_URL}/<path> page
- The site automatically hyperlinks bookmaker names, country names, and key terms for you after you submit — only mention them in plain text, never link them yourself
- External links (regulators, FIFA, UEFA, CAF, etc.) are also auto-inserted — mention the name in plain text only

OUTPUT FORMAT — return EXACTLY this structure, nothing outside the markers:

===META===
{{
  "title": "Specific title targeting the exact keyword given (max 80 chars)",
  "slug": "url-slug-format",
  "excerpt": "150-200 char excerpt naming the country and promising a real comparison",
  "tags": ["Tag1", "Tag2", "Tag3", "Tag4"],
  "bookmaker_featured": "top bookmaker name from the real data",
  "read_time": 6
}}
===BLOG===
[Full article in plain markdown, at least 1200 words]
[Must include the comparison table]
[Must include the ## FAQ section using the EXACT format above — ### headings, no Q:/A: labels]
[Must include responsible gambling section]
[Final line: *18+ | Bet Responsibly | T&Cs Apply*]
===END==="""


def _load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return default


def _bookmaker_block(code: str, limit: int = 6) -> str:
    bookmakers = load_bookmakers().get(code, [])
    top = sorted(bookmakers, key=lambda b: b.get("stars", 0), reverse=True)[:limit]
    lines = []
    for b in top:
        lines.append(
            f"- {b.get('name')}: {b.get('off')} (top: {b.get('top')}, min stake/deposit: "
            f"{b.get('min')}, licence: {b.get('lic')}, payments: {', '.join(b.get('pms', []))}) "
            f"— {b.get('terms')}"
        )
    return "\n".join(lines)


MIN_WORD_COUNT = 1000
MIN_FAQ_ENTRIES = 3
REQUIRED_FINAL_LINE = "*18+ | Bet Responsibly | T&Cs Apply*"

_BAD_FAQ_HEADING_RE = re.compile(r"^#{4,}\s", re.MULTILINE)
_QA_LABEL_RE = re.compile(r"^#{1,6}\s*[QA][:.]\s", re.MULTILINE)
_FAQ_QUESTION_RE = re.compile(r"^###\s+\S", re.MULTILINE)
# Found live 2026-08-02: the model copied the prompt's FAQ example question
# verbatim, including its own "### " marker, producing "### ### Is it safe
# to bet..." — a doubled marker that neither of the two checks above catch
# (it's still exactly 3 leading hashes, and it's not a Q:/A: label). Any
# stray "#" anywhere else on a "### " heading line is the same class of bug.
_STRAY_HASH_IN_HEADING_RE = re.compile(r"^###\s+.*#", re.MULTILINE)


def _validate_body(body: str) -> list[str]:
    """Deterministic quality gate — an LLM undershooting a word-count
    instruction or misusing a heading level (both observed live in this
    agent's first real run: a 453-word draft, and "#### Q:" leaking as
    literal visible text because the page renderer only processes
    ###-level FAQ headings) is common enough that prompting alone can't be
    trusted. Returns a list of failure reasons; empty means it passed."""
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
        failures.append("found a stray '#' character inside a '### ' FAQ heading line (e.g. a doubled '### ### question' marker) — the heading must contain only the question text after '### '")
    last_line = next((l.strip() for l in reversed(body.strip().splitlines()) if l.strip()), "")
    if last_line != REQUIRED_FINAL_LINE:
        failures.append(f"final line was '{last_line}', must be exactly '{REQUIRED_FINAL_LINE}'")
    return failures


def _country_block(code: str) -> tuple[str, dict]:
    data = load_country_data().get(code, {})
    if not data:
        return "", data
    block = (
        f"Country: {data.get('name')}\n"
        f"Currency: {data.get('currency')} ({data.get('symbol')})\n"
        f"Regulator: {data.get('regulator')}\n"
        f"Popular payment methods: {', '.join(data.get('payments', []))}\n"
        f"Popular leagues bettors follow: {', '.join(data.get('leagues', []))}"
    )
    return block, data


def generate_priority_post(item: dict) -> tuple[Optional[dict], str]:
    """Returns (post, reason). post is None on failure; reason is always a
    short machine-readable code so callers can persist *why* nothing was
    written — agent_log.json is gitignored (real log store is the Supabase
    mirror in utils/logger.py, not this repo), so a GitHub Actions run's
    diagnostic detail was otherwise invisible after the runner tore down
    (see AGENT-KNOWLEDGE.md 2026-08-02 for the live debugging that found
    this the hard way)."""
    country_name = item["country"]
    code = _COUNTRY_CODE_BY_NAME.get(country_name)
    if not code:
        print(f"  ✗ Unknown country code for '{country_name}' — skipping")
        return None, "unknown_country_code"

    country_block, country_data = _country_block(code)
    bookmaker_block = _bookmaker_block(code)
    if not country_block or not bookmaker_block:
        print(f"  ✗ No real site data found for {country_name} — skipping (never inventing bookmaker facts)")
        return None, "no_site_data"

    print(f"  🔍 Running SERP research for '{item['keyword']}'...")
    serp_block = research(item["keyword"], country_name)

    angle_brief = GUIDE_ANGLE_BRIEFS.get(item["guide_angle"], "").format(country=country_name)

    user_message = f"""TARGET KEYWORD (must be the primary focus): {item['keyword']}
TARGET COUNTRY: {country_name}

YOUR ANGLE: {angle_brief}

REAL COUNTRY DATA (use exactly, never invent):
{country_block}

REAL BOOKMAKER DATA (use exactly, never invent — these are the only bookmakers/offers you may reference):
{bookmaker_block}

{serp_block}

Write the guide now, following every rule in the system prompt exactly."""

    try:
        meta = None
        blog_body = ""
        last_failures: list[str] = []
        current_message = user_message
        for attempt in range(1, 3):
            print(f"  🤖 Generating guide with LLM (attempt {attempt}/2)...")
            # prefer_accuracy=True since 2026-08-21 — see agent_sports_blog.py's
            # generate_post() for the full incident (Groq retired its two
            # previous default models; the current free replacements invent
            # specific odds/stats noticeably more often across every writer,
            # not just transfers).
            raw = ask_long(SYSTEM_PROMPT, current_message, prefer_accuracy=True)

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
                print(f"  ✗ Still failing after retry — skipping this item rather than publishing a substandard guide")
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
            "id": f"post-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{item['guide_angle']}",
            "category": "betting",
            "title": meta.get("title", ""),
            "slug": meta.get("slug", ""),
            "excerpt": meta.get("excerpt", ""),
            "body": blog_body.strip(),
            "author": cat_meta["author"],
            "published_at": datetime.now(timezone.utc).isoformat(),
            "image_color": cat_meta["color"],
            "image_icon": cat_meta["icon"],
            "tags": meta.get("tags", []) or [country_name, "Betting Guide"],
            "featured": False,
            "bookmaker_featured": meta.get("bookmaker_featured", ""),
            "read_time": meta.get("read_time", 6),
            "_priority_keyword": item["keyword"],
        }
        feature_image = ensure_feature_image(post)
        if feature_image:
            post["feature_image"] = feature_image

        # Same title/content topic-match gate as agent_sports_blog.py — see
        # utils/title_content_match.py's docstring for the live "Transfer
        # Frenzy in Africa" incident this guards against. Low-risk for this
        # writer specifically (every guide is already anchored to a real
        # country_name), but cheap and deterministic, so applied uniformly
        # across every content-writing agent rather than assumed safe here.
        africa_violation = check_africa_framing(post["title"], post["slug"], post["body"])
        if africa_violation:
            print(f"  ✗ Title/content check held back this article: {africa_violation}")
            return None, "africa_framing: " + africa_violation

        # No _source_items — evergreen guides aren't grounded in news
        # headlines, so check_post() trivially passes (see its own
        # docstring: "nothing to verify" is not a failure). Real-fact
        # grounding here comes from the REAL BOOKMAKER DATA block above,
        # not from a fact-check pass against source snippets.
        passed, flags = fact_check_post(post)
        if not passed:
            print(f"  ✗ Fact-checker held back this article: {flags}")
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


def _core_phrase(keyword: str) -> str:
    lowered = keyword.lower()
    for substring, *_rest in EVERGREEN_CONTENT_TYPES:
        if substring in lowered:
            return substring
    return ""


def _already_covered(item: dict, existing_posts: list[dict]) -> bool:
    """True if an existing post (published before this pipeline existed, or
    by this pipeline on an earlier run) already substantially targets the
    same country + keyword angle. Found live during this agent's first real
    run: a legacy post already existed at slug "best-betting-sites-nigeria-
    2026" that agent_content_priority.py's SERP check correctly flagged as
    "SifuFinds doesn't rank for this exact query", but nothing checked
    whether SifuFinds already had a PAGE for it before queuing a fresh
    write — would have produced a near-duplicate and recreated the exact
    56-duplicate-title-pairs bug fixed 2026-08-01 (see
    utils/story_dedup.py, built for the news-post case; this is the
    evergreen-post equivalent check)."""
    phrase = _core_phrase(item["keyword"])
    country = item["country"].lower()
    if not phrase:
        return False
    phrase_words = phrase.split()
    for p in existing_posts:
        haystack = f"{p.get('title', '')} {p.get('slug', '')}".lower().replace("-", " ")
        if country in haystack and all(w in haystack for w in phrase_words):
            return True
    return False


def run(count: int = COUNT) -> int:
    queue = _load_json(QUEUE_PATH, {"items": []})
    state = _load_json(STATE_PATH, {"posted": {}})
    posted = state.setdefault("posted", {})
    existing = load_posts()

    candidates = []
    for item in queue.get("items", []):
        if not item.get("writer_actionable") or item["keyword"] in posted:
            continue
        if _already_covered(item, existing):
            posted[item["keyword"]] = {"skipped": "already_covered_by_existing_post"}
            continue
        candidates.append(item)

    if not candidates:
        print("Priority Writer — no un-actioned writer-actionable items in the queue. "
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
    print(f"Priority Writer Agent — {len(candidates)} un-actioned priority item(s), writing {len(batch)} this run")

    new_posts = []
    written = 0
    attempts_log = []
    for item in batch:
        print(f"\n📝 [{item['country']}] {item['keyword']} (score {item['score']})")
        try:
            post, reason = generate_priority_post(item)
        except AIProvidersExhausted:
            # generate_priority_post() deliberately re-raises this (copied
            # from agent_sports_blog.py's pattern, where an uncaught infra
            # failure propagating to script exit lets the retry
            # infrastructure notice and retry the whole workflow run) — but
            # this loop had no try/except around the call, so every single
            # cycle since this agent existed crashed silently here before
            # ever reaching the state write below. Confirmed live 2026-08-02:
            # four consecutive real cycles all committed only
            # content_priority_queue.json, with zero diagnostic trace,
            # because the crash happened before `state["last_run"]` could
            # ever be set. Every remaining item in this batch would fail
            # identically (all providers are exhausted, not just this one
            # item), so stop the batch here rather than retry each — but
            # still fall through to persist what we learned.
            print(f"  ✗ All LLM providers exhausted — stopping this batch early")
            attempts_log.append({"keyword": item["keyword"], "country": item["country"], "result": "failed", "reason": "AIProvidersExhausted"})
            break
        if post is None:
            attempts_log.append({"keyword": item["keyword"], "country": item["country"], "result": "failed", "reason": reason})
            continue
        new_posts.append(post)
        posted[item["keyword"]] = {
            "slug": post["slug"],
            "posted_at": datetime.now(timezone.utc).isoformat(),
        }
        attempts_log.append({"keyword": item["keyword"], "country": item["country"], "result": "written", "slug": post["slug"]})
        written += 1
        print(f"  ✓ '{post['title']}'")
        if announce_to_facebook(post):
            print("  ✓ Announced on Facebook")

    if new_posts:
        save_posts(new_posts + existing)
        print(f"\n✅ Wrote {written} priority guide(s). Total in blog: {len(new_posts) + len(existing)}")
    else:
        print("\n⚠ No new guides written this run.")

    # agent_log.json (utils/logger.py) is gitignored — its real durable
    # store is a Supabase mirror this workflow has no access to inspect
    # after the fact, so a run's diagnostic detail was otherwise invisible
    # once the ephemeral GitHub Actions runner tore down (confirmed live
    # 2026-08-02: three consecutive zero-output cycles with no way to tell
    # *why* without waiting hours for the full job log to become
    # available). last_run persists here instead, in a file that IS
    # committed every cycle regardless of outcome.
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
