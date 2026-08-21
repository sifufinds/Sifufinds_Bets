"""
Fabricated Content Fixer Agent — SifuFinds

On 2026-08-15/16, a manual audit (see AGENT-KNOWLEDGE.md) found that
agent_sports_blog.py's own SYSTEM_PROMPT — and two sibling prompts in
agent_fact_checker.py and agent_country_trending_writer.py — explicitly
instructed the LLM to invent betting odds under an "illustrative pricing"
carve-out. That carve-out is now removed from all three (same date), which
stops new fabricated posts, but ~596 already-published posts still carry
invented odds tables. This agent works through that backlog.

For each post still matching the fabricated-odds signature (a markdown
table with 4+ decimal-odds-shaped numbers next to 2+ known bookmaker
names):

1. Search for the post's real subject (free DuckDuckGo, no key/login) via
   utils.serp_research.fc_search().
2. If enough real, relevant source material comes back, rewrite the post
   with agent_fact_checker's now-corrected checker as a hard gate — a
   FLAGged rewrite is never published, it's held for retry.
3. If real grounding can't be found (common for posts about a specific
   past sporting event that's no longer live news), fall back to a
   deterministic strip: remove the fabricated odds table/numbers and add
   a dated correction note, without inventing anything to replace them.
   This mirrors the manual fix applied to the first 82 posts in this
   backlog — see AGENT-KNOWLEDGE.md's note that re-fabricating a
   retroactive number is not better than removing a bad one.

Progress is tracked in fabricated_fix_state.json (committed to the repo),
resumable batch pattern mirrors agent_content_backfill.py.

Usage:
    python agent_fabricated_content_fixer.py                  # next batch (default 100)
    python agent_fabricated_content_fixer.py --batch-size 5    # smaller batch (e.g. testing)
    python agent_fabricated_content_fixer.py --dry-run         # preview, write nothing
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from llm import ask_long, AIProvidersExhausted  # noqa: E402
from utils.logger import log  # noqa: E402
from utils.serp_research import fc_search  # noqa: E402
from utils.title_content_match import check_africa_framing  # noqa: E402
from agent_fact_checker import check_post  # noqa: E402
from agent_sports_blog import load_posts, save_posts  # noqa: E402
from seo_meta import strip_dangling_words  # noqa: E402

BASE = Path(__file__).parent.parent.parent
STATE_PATH = Path(__file__).parent / "fabricated_fix_state.json"
TRANSLATIONS_DIR = BASE / "blog" / "translations"
LOCALES = ["fr", "de", "es", "pt", "sw"]

BATCH_SIZE = 100
MAX_ATTEMPTS = 3
MIN_SOURCES_FOR_REWRITE = 3
# Leaves headroom inside a workflow's own job timeout for the regen/validate/
# commit steps that run after this script — see fabricated_content_fix.yml.
WALL_CLOCK_BUDGET_SECONDS = 3 * 60 * 60

ODDS_NUM_RE = re.compile(r"\b\d{1,2}\.\d{2}\b")
BOOKMAKER_RE = re.compile(
    r"\b(Bet9ja|Sportybet|SportyBet|Betway|1xBet|Hollywoodbets|Melbet|22Bet|Betika|BetKing)\b"
)
FILLER_TITLE_WORDS = re.compile(
    r"\b(Transfer News|Transfer Update|Transfer Window|Transfer Talk|Transfer Saga|"
    r"Transfer Roundup|Betting Guide|Betting Insights|Betting Tips|Roundup|Latest|"
    r"Confirmed|Correcting the Record|Update)\b",
    re.IGNORECASE,
)

DISCLAIMER = (
    "*18+ | Bet Responsibly | If gambling is affecting you or someone you know, "
    "contact BeGambleAware for free, confidential support. T&Cs apply.*"
)

FIXER_SYSTEM_PROMPT = f"""You are the Accuracy Desk for SifuFinds (sifufinds.com), Africa's #1 betting comparison website.

CONTEXT: The article below was previously found to contain a fabricated betting-odds table — invented decimal odds (e.g. "4.50") presented as if they were real prices. Your job is to rewrite the article using ONLY the real source snippets provided, removing every invented number and unverifiable claim.

NON-NEGOTIABLE RULES:
- NEVER invent an odds number, a transfer fee, a date, a statistic, or a quote. If a specific figure isn't in the REAL SOURCE SNIPPETS below, don't include it — write "undisclosed" or omit it rather than guess.
- NEVER include a betting-odds table or a specific price for any market. Describe the betting angle qualitatively instead, and point the reader to SifuFinds' own live sifufinds.com/odds/ page for the actual current price.
- Label every claim's certainty explicitly: "Confirmed" for something the sources report as done, "Reported" or "Unresolved" for something still being negotiated or unconfirmed.
- If the REAL SOURCE SNIPPETS don't actually cover the same subject as the ORIGINAL ARTICLE's title, say so honestly in the rewrite rather than forcing a connection that isn't there — a shorter, honest article beats a padded, disconnected one.
- NEVER title or frame the article as being about "Africa"/"African clubs"/an "African transfer window" unless the actual clubs, players, or league named in the sources are genuinely African. It is fine to write FOR African bettors; it is not fine to claim the story itself is African when it isn't.
- UK English throughout (favourite, colour, organise). No em/en dashes joining clauses. No formulaic AI openers ("In the world of...", "When it comes to...").
- Mention at least 2 African bookmakers by name where natural (e.g. "compare markets across Bet9ja and Sportybet"), never with a fabricated price attached.
- Title must be 60 characters or fewer.

OUTPUT FORMAT — respond with ONLY this JSON structure, no markdown fences, no commentary:
{{
  "title": "...",
  "excerpt": "150-200 char excerpt naming the real story",
  "tags": ["Tag1", "Tag2", "Tag3"],
  "body": "Full article in plain markdown. Use '## ' (two hashes, never three) for every section heading, matching this exact structure: a '**Last updated: <today's date>.**' opening line, a '## ' section with a Confirmed/Reported breakdown of what the sources actually say, a '## What This Means for Bettors' section with no invented odds, a '## Key Takeaways' bulleted list, a '## FAQ' section with 2-4 **Q: ...** / plain-answer pairs, the disclaimer line '{DISCLAIMER}', and a '## Sources' section listing the real outlets from the source snippets by name. End with ###END on its own line."
}}
"""


def _load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return {"fixed": {}, "skipped": {}, "runs": 0, "last_run": None}


def _save_state(state: dict) -> None:
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2))
    os.replace(tmp, STATE_PATH)


def _has_fabricated_odds_table(body: str) -> bool:
    table_lines = [l for l in body.split("\n") if l.strip().startswith("|")]
    table_text = "\n".join(table_lines)
    if not table_text:
        return False
    return len(ODDS_NUM_RE.findall(table_text)) >= 4 and len(BOOKMAKER_RE.findall(table_text)) >= 2


def find_fabricated_posts(posts: list[dict], state: dict) -> list[dict]:
    fixed = set(state.get("fixed", {}).keys())
    return [
        p for p in posts
        if p.get("slug") and p.get("slug") not in fixed and _has_fabricated_odds_table(p.get("body", ""))
    ]


def _search_query_for_post(post: dict) -> str:
    title = post.get("title", "")
    stripped = FILLER_TITLE_WORDS.sub("", title).strip(" :–-")
    query = stripped or title
    # Add sport/transfer context so the search doesn't drift off-topic for
    # very short remaining titles (e.g. just a surname).
    if len(query.split()) <= 2:
        query = f"{query} football transfer news"
    return query


def build_source_items(results: list[dict]) -> list[dict]:
    items = []
    for r in results:
        url = r.get("url", "")
        title = r.get("title", "")
        description = r.get("description", "")
        if not url or not title:
            continue
        items.append({
            "title": title,
            "url": url,
            "image": "",
            "source": urlparse(url).netloc.replace("www.", ""),
            "description": description,
        })
    return items


def _clean_json(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("```")[1]
        if s.startswith("json"):
            s = s[4:]
    return s.strip()


def strip_fabricated_numbers(post: dict) -> dict:
    """Deterministic fallback for when real grounding can't be found:
    remove the fabricated odds table(s) as whole blocks (header, separator,
    and every data row — not just the individual rows that happen to
    contain a number, which left an orphaned empty header behind in
    testing), add a dated correction note. Never invents anything to
    replace what's removed."""
    body = post["body"]
    lines = body.split("\n")

    # Group contiguous "|"-prefixed lines into table blocks first, then
    # decide per-block whether it's fabricated (any row has an odds-shaped
    # number) — a block-level decision avoids leaving a header with no rows.
    blocks: list[list[int]] = []  # each entry: list of line indices
    current: list[int] = []
    for i, line in enumerate(lines):
        if line.strip().startswith("|"):
            current.append(i)
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)

    label_re = re.compile(r"^\**\s*(odds|market)[\w\s]*\**$", re.IGNORECASE)
    remove_indices: set[int] = set()
    for block in blocks:
        block_text = "\n".join(lines[i] for i in block)
        if not ODDS_NUM_RE.search(block_text):
            continue
        remove_indices.update(block)
        # A bare label line ("**Odds Comparison Table**") directly above a
        # removed table would otherwise dangle with nothing under it.
        prev = block[0] - 1
        while prev >= 0 and lines[prev].strip() == "":
            prev -= 1
        if prev >= 0 and label_re.match(lines[prev].strip()):
            remove_indices.add(prev)

    new_lines = [line for i, line in enumerate(lines) if i not in remove_indices]
    body = "\n".join(new_lines)
    body = re.sub(r"\n{3,}", "\n\n", body)

    note = (
        f"\n\n*Correction, {datetime.now(timezone.utc).strftime('%d %B %Y')}: this article "
        "previously included a betting-odds table with specific prices that could not be "
        "verified against a real source. It has been removed rather than re-published. "
        "For current odds, compare live pricing on SifuFinds' odds page before betting — "
        "any number in an older article is likely already out of date.*"
    )
    new_post = dict(post)
    new_post["body"] = body.rstrip() + note
    new_post["updated_at"] = datetime.now(timezone.utc).isoformat()
    return new_post


def rewrite_post(post: dict, source_items: list[dict]) -> dict | None:
    sources_block = "\n".join(
        f"- [{s['source']}] {s['title']}: {s['description']}" for s in source_items
    )
    today = datetime.now(timezone.utc).strftime("%d %B %Y")
    user_message = f"""TODAY: {today}

ORIGINAL ARTICLE (contains fabricated odds — do not trust its numbers):
Title: {post.get('title', '')}
Category: {post.get('category', '')}

REAL SOURCE SNIPPETS (use ONLY these for facts):
{sources_block}

Rewrite this article now, following the system rules exactly."""

    try:
        raw = ask_long(FIXER_SYSTEM_PROMPT, user_message, prefer_accuracy=True)
    except AIProvidersExhausted as e:
        log("fabricated_fixer", "rewrite_post", "provider_exhausted", f"{post.get('slug', '')}: {e}")
        return None

    try:
        data = json.loads(_clean_json(raw))
    except json.JSONDecodeError:
        log("fabricated_fixer", "rewrite_post", "error", f"{post.get('slug', '')}: bad JSON from LLM")
        return None

    title = data.get("title", "").strip()
    body = data.get("body", "").strip()
    if not title or not body:
        return None
    if len(title) > 60:
        # No unconditional "..." here — that, plus a bare rsplit with no
        # stopword check, is exactly the bug that produced ~790 live titles
        # ending mid-thought ("...Man Utd's Rebuild, and") before this fix.
        # strip_dangling_words() is the shared, tested fix (seo_meta.py).
        title = strip_dangling_words(title[:60].rsplit(" ", 1)[0])
    if _has_fabricated_odds_table(body):
        log("fabricated_fixer", "rewrite_post", "still_fabricated",
            f"{post.get('slug', '')}: rewrite still contains an odds table, rejecting")
        return None

    new_post = dict(post)
    new_post["title"] = title
    raw_excerpt = data.get("excerpt", post.get("excerpt", ""))
    # A bare [:200] slice can land mid-word or mid-thought the same way the
    # title bug above did — route through the same word-boundary +
    # dangling-word-safe helper instead.
    new_post["excerpt"] = (
        strip_dangling_words(raw_excerpt[:200].rsplit(" ", 1)[0])
        if len(raw_excerpt) > 200 else raw_excerpt
    )
    new_post["tags"] = data.get("tags", post.get("tags", []))
    new_post["body"] = body
    new_post["_source_items"] = source_items
    new_post["_sources"] = [s["source"] for s in source_items[:5]]
    new_post["updated_at"] = datetime.now(timezone.utc).isoformat()
    wc = len(body.split())
    new_post["read_time"] = max(1, round(wc / 200))
    return new_post


def clear_stale_translations(slug: str) -> list[str]:
    """A translation-cache entry for this slug (if any) was translated from
    the fabricated body — remove it rather than leave a fabricated variant
    live in another locale. gen_blog_post_pages.py already skips generating
    a locale page for a slug with no entry, so this just means that locale
    variant temporarily doesn't exist until a real translation pass covers
    it again — safer than a wrong one staying live indefinitely."""
    cleared = []
    for locale in LOCALES:
        path = TRANSLATIONS_DIR / f"{locale}.json"
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if slug in data:
            del data[slug]
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            cleared.append(locale)
    return cleared


def process_post(post: dict, state: dict, dry_run: bool) -> str:
    """Returns one of: 'fixed_rewrite', 'fixed_strip', 'skipped'."""
    slug = post["slug"]
    query = _search_query_for_post(post)
    try:
        results = fc_search(query, limit=8)
    except Exception as e:
        log("fabricated_fixer", "process_post", "search_error", f"{slug}: {e}")
        results = []

    source_items = build_source_items(results)
    usable = [s for s in source_items if s["description"]]

    new_post = None
    mode = None
    if len(usable) >= MIN_SOURCES_FOR_REWRITE:
        candidate = rewrite_post(post, usable)
        if candidate is not None:
            violation = check_africa_framing(candidate["title"], slug, candidate["body"])
            if violation:
                log("fabricated_fixer", "process_post", "africa_framing_violation", f"{slug}: {violation}")
                candidate = None
        if candidate is not None:
            passed, flags = check_post(candidate)
            if passed:
                new_post = candidate
                mode = "fixed_rewrite"
            else:
                log("fabricated_fixer", "process_post", "fact_check_flag", f"{slug}: {flags}")

    if new_post is None:
        new_post = strip_fabricated_numbers(post)
        mode = "fixed_strip"

    if dry_run:
        print(f"  [dry-run] {slug} -> {mode}")
        print(f"    title: {new_post['title']}")
        return mode

    post.clear()
    post.update(new_post)
    cleared = clear_stale_translations(slug)
    if cleared:
        log("fabricated_fixer", "process_post", "translations_cleared", f"{slug}: {cleared}")

    entry = state["fixed"].setdefault(slug, {})
    entry["mode"] = mode
    entry["fixed_at"] = datetime.now(timezone.utc).isoformat()
    return mode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    start = time.monotonic()
    state = _load_state()
    posts = load_posts()
    posts_by_slug = {p["slug"]: p for p in posts if p.get("slug")}

    candidates = find_fabricated_posts(posts, state)
    print(f"Fabricated-odds backlog: {len(candidates)} posts remaining")
    if not candidates:
        print("Nothing to do.")
        state["runs"] = state.get("runs", 0) + 1
        state["last_run"] = datetime.now(timezone.utc).isoformat()
        if not args.dry_run:
            _save_state(state)
        return 0

    batch = candidates[: args.batch_size]
    rewritten = stripped = 0

    for i, post in enumerate(batch, start=1):
        if time.monotonic() - start > WALL_CLOCK_BUDGET_SECONDS:
            print(f"Wall-clock budget reached after {i - 1} posts — stopping early, will resume next run")
            break
        print(f"[{i}/{len(batch)}] {post['slug']}")
        try:
            mode = process_post(post, state, args.dry_run)
        except Exception as e:
            log("fabricated_fixer", "main", "post_error", f"{post.get('slug', '')}: {e}")
            print(f"  ERROR: {e}")
            continue
        if mode == "fixed_rewrite":
            rewritten += 1
        elif mode == "fixed_strip":
            stripped += 1

    print(f"Done: {rewritten} full rewrites, {stripped} strip-only fixes")
    state["runs"] = state.get("runs", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()

    if not args.dry_run and (rewritten or stripped):
        save_posts(posts)
        _save_state(state)
        print("Saved posts.json and state file.")
    elif args.dry_run:
        print("[dry-run] nothing written")

    remaining = len(candidates) - rewritten - stripped
    print(f"Remaining after this run: ~{remaining}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
