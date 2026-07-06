"""
Agent — Content Depth Backfill

Legacy blog posts written before the current CLAUDE.md content standard
(1,000+ words, mandatory FAQ section, comparison table) never got backfilled.
This agent works through that backlog a small batch at a time, every run,
forever — so "expand thin/no-FAQ posts" doesn't depend on anyone remembering
to do it by hand.

Progress is durable: agents/python/content_backfill_state.json tracks which
slugs have already been successfully expanded (so they're never reprocessed)
and how many attempts a stubborn post has had (so a post the LLM can't fix
after 3 tries is skipped, not retried forever, but stays visible in the
state file for manual follow-up).

Called by .github/workflows/content_backfill.yml on a schedule.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from llm import ask_long
from utils.serp_research import research
from gen_blog_post_pages import extract_faq_schema  # reuse the exact schema validation logic

POSTS_JSON = REPO_ROOT / "blog" / "posts.json"
STATE_PATH = Path(__file__).parent / "content_backfill_state.json"

MIN_WORDS = 1000          # CLAUDE.md content standard
BATCH_SIZE = 4             # posts expanded per run — keeps quality + API usage in check
MAX_ATTEMPTS = 3           # give up on a post after this many failed expansions

SYSTEM_PROMPT = """You are the Content Editor for SifuFinds (sifufinds.com), Africa's #1 betting comparison website.

You are EXPANDING an existing, already-published blog post to meet the current content standard. You are NOT rewriting it from scratch — preserve the original facts, tone, keyword focus, and any specific matches/teams/odds mentioned. Add depth, not filler.

REQUIREMENTS for the returned post body:
- Total length: 1000-1400 words of substantive markdown
- Keep the original opening paragraph(s) essentially intact
- Add real analytical depth: context, comparisons, what it means for bettors, relevant stats
- If the post doesn't already have a markdown comparison table (a table using | and --- syntax), add one relevant to the topic (e.g. odds comparison, bookmaker features, or key stats)
- End with a "## FAQ" heading followed by exactly 4 question/answer pairs in this exact format (this is required for schema.org markup — follow it precisely):

## FAQ

**Question text ending in a question mark?**
Answer as one or two plain sentences, no markdown formatting inside.

**Another question?**
Answer.

- Naturally mention at least one African country name (Nigeria, Kenya, Ghana, South Africa, Tanzania, Uganda, Zambia, etc.) and one bookmaker name (Bet9ja, SportyBet, Betway, 1xBet, Hollywoodbets, 22Bet, Melbet) if not already present — these trigger internal auto-linking, do not make it feel forced
- Never promise guaranteed wins
- Include a responsible-gambling-appropriate tone (the disclaimer itself is injected automatically, don't add your own)

Return ONLY the final markdown body. No preamble, no explanation, no code fences, no meta-commentary — just the post body starting from its first paragraph."""


def _word_count(text: str) -> int:
    return len(text.split())


def _has_table(md: str) -> bool:
    return "|" in md and "---" in md


def _load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            pass
    return {"processed": {}, "attempts": {}, "runs": 0}


def _save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2))


def _needs_expansion(post: dict) -> bool:
    body = post.get("body", "")
    if _word_count(body) < MIN_WORDS:
        return True
    if not extract_faq_schema(body):
        return True
    return False


def _pick_batch(posts: list, state: dict) -> list:
    candidates = []
    for post in posts:
        slug = post.get("slug", "")
        if not slug or slug in state["processed"]:
            continue
        if state["attempts"].get(slug, 0) >= MAX_ATTEMPTS:
            continue
        if _needs_expansion(post):
            candidates.append(post)

    # Prioritize featured posts, then most recently published (most relevant to
    # current traffic), so the highest-impact posts get fixed first.
    candidates.sort(
        key=lambda p: (not p.get("featured", False), p.get("published_at", "")),
        reverse=False,
    )
    candidates.sort(key=lambda p: p.get("featured", False), reverse=True)
    return candidates[:BATCH_SIZE]


def _expand_post(post: dict) -> str | None:
    keyword = post.get("title", "")
    country = ""
    for tag in post.get("tags", []):
        if tag.lower() in ("nigeria", "kenya", "ghana", "south africa", "tanzania", "uganda", "zambia"):
            country = tag
            break

    research_block = ""
    try:
        research_block = research(keyword, country)
    except Exception as e:
        print(f"    (research unavailable: {e})")

    user_message = f"""ORIGINAL POST TITLE: {post.get('title')}
TAGS: {', '.join(post.get('tags', []))}
FEATURED BOOKMAKER: {post.get('bookmaker_featured', 'none specified')}

ORIGINAL BODY TO EXPAND:
---
{post.get('body', '')}
---

{research_block}

Expand this post now per the system instructions. Return only the final markdown body."""

    try:
        new_body = ask_long(SYSTEM_PROMPT, user_message)
        return new_body.strip()
    except Exception as e:
        print(f"    ✗ LLM call failed: {e}")
        return None


def run() -> int:
    if not POSTS_JSON.exists():
        print("blog/posts.json not found — nothing to do")
        return 0

    data = json.loads(POSTS_JSON.read_text())
    posts = data["posts"] if isinstance(data, dict) else data

    state = _load_state()
    state["runs"] = state.get("runs", 0) + 1

    total_needing = sum(1 for p in posts if _needs_expansion(p))
    batch = _pick_batch(posts, state)

    print(f"Content backfill — {total_needing} post(s) still below standard, processing {len(batch)} this run")

    fixed = 0
    for post in batch:
        slug = post["slug"]
        words_before = _word_count(post.get("body", ""))
        print(f"  → {slug} ({words_before} words)")

        new_body = _expand_post(post)
        if not new_body:
            state["attempts"][slug] = state["attempts"].get(slug, 0) + 1
            print(f"    ✗ expansion failed (attempt {state['attempts'][slug]}/{MAX_ATTEMPTS})")
            continue

        words_after = _word_count(new_body)
        has_faq = bool(extract_faq_schema(new_body))

        if words_after < MIN_WORDS or not has_faq:
            state["attempts"][slug] = state["attempts"].get(slug, 0) + 1
            print(f"    ✗ result still short of standard (words={words_after}, faq_schema={has_faq}) "
                  f"— attempt {state['attempts'][slug]}/{MAX_ATTEMPTS}")
            continue

        post["body"] = new_body
        state["processed"][slug] = {
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "words_before": words_before,
            "words_after": words_after,
        }
        fixed += 1
        print(f"    ✓ expanded {words_before} → {words_after} words, FAQPage schema present")

    if fixed:
        payload = {"posts": posts} if isinstance(data, dict) else posts
        POSTS_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    _save_state(state)

    remaining = total_needing - fixed
    print(f"\n{'─'*60}")
    print(f"Fixed this run: {fixed}/{len(batch)} attempted")
    print(f"Remaining in backlog: {remaining}")
    print(f"{'─'*60}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
