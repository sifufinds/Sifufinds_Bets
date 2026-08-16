"""
Fact Checker Agent — second-pass LLM review of a drafted blog post against
the real news source snippets that were used to write it, before the post
is ever appended to posts.json.

Accuracy in the content pipeline is otherwise 100% prompt-instruction based
(agent_sports_blog.py's SYSTEM_PROMPT says "don't invent anything") with no
independent verification step — this agent is that missing second pass.

Called from agent_sports_blog.generate_post() right before it returns a post,
so both agent_sports_blog.run() and agent_transfer_post.py (which imports
generate_post directly) are covered by a single integration point. On FLAG,
generate_post() returns None instead of the post — the same "nothing
publishable this run" signal already used for dedup/no-fresh-news skips
(see AGENT-KNOWLEDGE.md's agent_transfer_post.py "always exited 0" fix), so
a flagged draft never causes a false CI failure, it's just silently held
back and logged for review.

Usage (standalone, for manual spot-checks):
    python agent_fact_checker.py --slug <slug>   # re-check an existing post
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from llm import ask, AIProvidersExhausted
from utils.logger import log

FLAGS_PATH = Path(__file__).parent / "fact_check_flags.json"
POSTS_PATH = Path(__file__).parent.parent.parent / "blog" / "posts.json"

FACT_CHECK_SYSTEM_PROMPT = """You are a Fact Checker for an African sports betting news site. You will be given:
1. SOURCE SNIPPETS — real news headlines + short descriptions that were used to write a draft article.
2. DRAFT ARTICLE — the article body written from those sources.

Identify any specific factual claim in the draft — a score, statistic, transfer fee, direct quote, date, or named event outcome — that is NOT supported by, or contradicts, the source snippets.

DO NOT FLAG:
- General betting-market commentary, "expected to shorten/lengthen", or clearly-labelled analysis/opinion that names no specific number.
- A mention of a bookmaker by name with no price attached (e.g. "compare markets across Bet9ja and Sportybet").

DO FLAG:
- Any specific odds value (e.g. "4.50", "1.85", "5/1"), whether shown as a single number, a comparison table, or attributed to a named bookmaker (e.g. "Bet9ja is offering 4.50") — as of 2026-08-15 this site no longer publishes invented odds under any framing ("illustrative," "estimated," or otherwise). This site was previously caught publishing hundreds of fabricated odds tables under an "odds are exempt" policy; that policy is gone. A specific price reads as a factual claim to a reader regardless of how it's hedged in the surrounding prose, so it must trace back to the source snippets exactly like a transfer fee or a statistic — and since these source snippets almost never contain a live bookmaker price, in practice any specific odds number should be flagged.
- A transfer fee, date, or statistic stated as if confirmed, when it is not in the source snippets.
- A direct quote in quotation marks attributed to a real person, club, or "a representative" that does not appear in the source snippets — this is fabrication regardless of how plausible it sounds.
- Any score, event outcome, or named signing not present in the source snippets.

Respond with ONLY valid JSON, no markdown fences, no commentary:
{"verdict": "PASS", "flags": []}
or
{"verdict": "FLAG", "flags": ["<the exact unsupported claim, quoted from the draft>", ...]}

If every specific factual claim in the draft traces back to the source snippets, return PASS with an empty flags list.
"""


def _load_flags() -> list[dict]:
    if FLAGS_PATH.exists():
        try:
            return json.loads(FLAGS_PATH.read_text())
        except (OSError, json.JSONDecodeError):
            return []
    return []


def _save_flags(flags: list[dict]) -> None:
    FLAGS_PATH.write_text(json.dumps(flags[-500:], indent=2))


def _clean_json(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("```")[1]
        if s.startswith("json"):
            s = s[4:]
    return s.strip()


def check_post(post: dict) -> tuple[bool, list[str]]:
    """Return (passed, flags). passed=True means safe to publish.

    Reads source material from post["_source_items"] (title/description/
    source, populated by agent_sports_blog.generate_post()) — never the
    LLM's own draft as its own source, which would just rubber-stamp
    whatever it already wrote.
    """
    sources = post.get("_source_items", [])
    if not sources:
        # No source snippets to check against (e.g. a hand-written post) —
        # nothing to verify, not a failure.
        return True, []

    sources_block = "\n".join(
        f"- [{i.get('source', '')}] {i.get('title', '')}: {i.get('description', '')}"
        for i in sources
    )
    user_message = f"""SOURCE SNIPPETS:
{sources_block}

DRAFT ARTICLE:
{post.get('title', '')}

{post.get('body', '')}
"""

    try:
        raw = ask(FACT_CHECK_SYSTEM_PROMPT, user_message)
    except AIProvidersExhausted:
        # Fail safe, not fail open: if the checker itself can't run, don't
        # silently publish unchecked. Mirrors the existing convention where
        # an infra failure is distinct from "nothing to publish" — log it
        # loudly so the watchdog/retry nets can see this run needs another
        # attempt, but don't crash the whole content pipeline over a second
        # LLM call.
        log("fact_checker", "check_post", "provider_exhausted",
            f"could not fact-check '{post.get('slug', '')}' — AI providers exhausted")
        return False, ["AI providers exhausted — could not run fact-check this run"]
    except Exception as e:
        log("fact_checker", "check_post", "error", f"{post.get('slug', '')}: {e}")
        return False, [f"fact-checker error: {e}"]

    try:
        data = json.loads(_clean_json(raw))
    except json.JSONDecodeError:
        log("fact_checker", "check_post", "error",
            f"could not parse fact-checker response for '{post.get('slug', '')}': {raw[:200]}")
        return False, ["fact-checker response was not valid JSON"]

    flags = data.get("flags", []) or []
    passed = data.get("verdict") == "PASS" and not flags

    if not passed:
        entry = {
            "slug": post.get("slug", ""),
            "title": post.get("title", ""),
            "flags": flags,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        all_flags = _load_flags()
        all_flags.append(entry)
        _save_flags(all_flags)
        log("fact_checker", "check_post", "flagged",
            f"{post.get('slug', '')}: {len(flags)} flag(s) — held back, not published")
    else:
        log("fact_checker", "check_post", "pass", post.get("slug", ""))

    return passed, flags


def _load_posts() -> list[dict]:
    data = json.loads(POSTS_PATH.read_text())
    return data["posts"] if isinstance(data, dict) else data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", help="Re-check an existing post from posts.json by slug")
    args = parser.parse_args()

    if not args.slug:
        print("Nothing to do standalone without --slug — this agent is normally called "
              "inline from agent_sports_blog.generate_post(). Use --slug to spot-check "
              "an existing post.")
        return 0

    posts = _load_posts()
    post = next((p for p in posts if p.get("slug") == args.slug), None)
    if not post:
        print(f"No post found with slug '{args.slug}'")
        return 1

    passed, flags = check_post(post)
    if passed:
        print(f"✅ PASS — '{post['title']}'")
        return 0
    print(f"❌ FLAG — '{post['title']}'")
    for f in flags:
        print(f"  - {f}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
