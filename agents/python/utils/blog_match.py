"""
Finds a real blog/posts.json article to link from a Facebook post, so the
"read more" link points at actual site content instead of always the
homepage. Falls back to None when nothing fresh matches — callers then use
their existing generic link (bookmaker page, /tips/, etc.) rather than force
a bad match.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
POSTS_JSON = REPO_ROOT / "blog" / "posts.json"
BOOKMAKER_LINKS_JSON = REPO_ROOT / "data" / "bookmaker_links.json"
STATE_FILE = Path(__file__).parent.parent / "facebook_share_state.json"
SITE_URL = "https://sifufinds.com"

BONUS_CATEGORIES = {"bookmaker-guides", "country-guides"}
BONUS_KEYWORDS = ("bonus", "welcome offer", "free bet", "promo code")

TIPS_CATEGORIES = {"betting-tips"}
TIPS_KEYWORDS = ("tip", "predict", "acca", "accumulator")

COOLDOWN_DAYS = 10


def _load_posts() -> list[dict]:
    if not POSTS_JSON.exists():
        return []
    data = json.loads(POSTS_JSON.read_text())
    return data["posts"] if isinstance(data, dict) else data


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {"bonus": {}, "tips": {}}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"bonus": {}, "tips": {}}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _matches(post: dict, categories: set[str], keywords: tuple[str, ...]) -> bool:
    if post.get("category") in categories:
        return True
    haystack = " ".join([post.get("title", ""), *post.get("tags", [])]).lower()
    return any(kw in haystack for kw in keywords)


def find_matching_post(mode: str) -> dict | None:
    """mode: 'bonus' or 'tips'. Returns a post dict with a pre-built 'url', or None."""
    categories, keywords = (
        (BONUS_CATEGORIES, BONUS_KEYWORDS) if mode == "bonus" else (TIPS_CATEGORIES, TIPS_KEYWORDS)
    )

    posts = _load_posts()
    candidates = [p for p in posts if _matches(p, categories, keywords)]
    candidates.sort(key=lambda p: p.get("published_at", ""), reverse=True)

    state = _load_state()
    used = state.get(mode, {})
    now = datetime.now(timezone.utc)

    for post in candidates:
        slug = post.get("slug", "")
        last_used = used.get(slug)
        if last_used:
            days_since = (now - datetime.fromisoformat(last_used)).days
            if days_since < COOLDOWN_DAYS:
                continue
        post = dict(post)
        post["url"] = f"{SITE_URL}/blog/{slug}/"
        return post

    if candidates:
        # Everything is on cooldown — reuse the most recent match rather than
        # skip the slot; a slightly-repeated real post beats no link at all.
        post = dict(candidates[0])
        post["url"] = f"{SITE_URL}/blog/{post.get('slug', '')}/"
        return post

    return None


def mark_used(mode: str, slug: str) -> None:
    state = _load_state()
    state.setdefault(mode, {})[slug] = datetime.now(timezone.utc).isoformat()
    _save_state(state)


def bookmaker_review_url(brand_name: str) -> str | None:
    """Absolute /bookmakers/<slug>/ review page URL for a brand, if one exists."""
    if not BOOKMAKER_LINKS_JSON.exists():
        return None
    try:
        entries = json.loads(BOOKMAKER_LINKS_JSON.read_text())["bookmakers"]
    except Exception:
        return None
    name_lower = brand_name.lower()
    for entry in entries:
        if entry.get("status") != "active":
            continue
        if entry.get("brand_name", "").lower() == name_lower or entry.get("keyword", "") in name_lower:
            path = entry["href"].replace("../../", "/")
            return f"{SITE_URL}{path}"
    return None
