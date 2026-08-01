"""
Shared "already covered" story registry — used by every content-generating
agent (agent_sports_blog.py's general categories, agent_transfer_post.py's
dedicated transfers feed) to recognize when a still-fresh source headline is
about to be covered again under a fresh, differently-worded LLM-invented
title.

Extracted 2026-08-01 from agent_transfer_post.py, where this exact fix was
built and proven on 2026-07-30 (see headline_key()'s docstring for the real
incident) but only ever wired into the dedicated "transfers" category —
agent_sports_blog.py's own run() (football/sportnews/etc., what
breaking_news.yml actually runs 3x/day) still only compared the LLM's own
invented title against recent posts, which structurally cannot catch this
class of duplicate: two posts about the same real-world story almost never
share a title prefix, since the LLM writes fresh phrasing every time. Live
site scan on 2026-08-01 found 56 duplicate-content pairs across published
posts as a direct result — this shared registry closes that gap for every
caller, not just the transfers feed.

One shared state file (not one per agent) so a story covered by either
agent is recognized by both — the same rumour can plausibly surface in a
general "football" category run and the dedicated transfers feed within
the same day.
"""
import json
from pathlib import Path

STATE_PATH = Path(__file__).parent.parent / "covered_stories_state.json"
_MAX_KEYS = 500


def headline_key(title: str) -> str:
    """Normalized dedup key for a headline/title — lowercase, first 40 chars."""
    return title.lower()[:40]


def source_keys(post: dict) -> set[str]:
    """Normalized keys for every candidate source headline a generated post
    was actually built from (see generate_post()'s post["_source_items"])."""
    return {headline_key(i["title"]) for i in post.get("_source_items", []) if i.get("title")}


def load_covered_keys() -> set[str]:
    if STATE_PATH.exists():
        try:
            return set(json.loads(STATE_PATH.read_text()).get("posted_keys", []))
        except Exception:
            pass
    return set()


def record_covered_keys(keys: set[str]) -> None:
    if not keys:
        return
    state = {"posted_keys": []}
    if STATE_PATH.exists():
        try:
            state = json.loads(STATE_PATH.read_text())
        except Exception:
            pass
    existing = state.get("posted_keys", [])
    existing.extend(k for k in keys if k not in existing)
    state["posted_keys"] = existing[-_MAX_KEYS:]
    STATE_PATH.write_text(json.dumps(state, indent=2))
