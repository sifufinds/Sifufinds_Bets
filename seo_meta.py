"""Shared <title> / meta-description length enforcement for every page generator.

Every generator in this repo used to hand-roll its own title/description
truncation (or none at all) — gen_blog_post_pages.py and gen_bk_reviews.py
each carried their own slightly different copy of seo_title(), and the other
~11 generators (gen_best_betting_pages.py, generate_country_pages.py,
gen_bookmaker_country_pages.py, gen_payment_country_pages.py,
gen_sport_country_pages.py, gen_guide_pages.py, gen_bonus_pages.py,
gen_all_cities.py, gen_city_pages.py, gen_payment_pages.py,
gen_wc2026_teams.py) built meta descriptions by unbounded f-string
concatenation with no length check at all. That gap let 313 pages across
every one of those generators ship a meta description over Google's 155-char
display limit — found only when scripts/seo_check.py's title/meta-desc check
was extended from blog-only to every deployed HTML file (technical SEO
audit, 2026-08-11). scripts/seo_check.py is the permanent guard that catches
a regression here; this module is the one place the fix itself lives, so
every current and future generator imports the same behaviour instead of
re-implementing (and re-breaking) it.

Usage:
    from seo_meta import seo_title, seo_meta_description
    title = seo_title(f"{name} Review 2026")
    desc = seo_meta_description(f"Full description of {name}...")
"""

from __future__ import annotations

from datetime import datetime, timezone


def current_month_year() -> str:
    """Return e.g. 'August 2026' — always the real date at call time.

    Single source of truth for every "Updated <Month Year>" / "Reviewed
    <Month Year>" freshness string across generators, so none of them can
    drift back into a hardcoded month that goes stale (found 2026-08-16:
    'June 2026' was still hardcoded in 6 generators, 238 deployed pages,
    two months after it was first written).
    """
    return datetime.now(timezone.utc).strftime("%B %Y")


def current_year() -> str:
    """Return e.g. '2026' — always the real year at call time."""
    return str(datetime.now(timezone.utc).year)


def current_iso_date() -> str:
    """Return e.g. '2026-08-16' — for dateModified fields with no real edit tracking."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def seo_title(title: str, max_len: int = 60, suffix: str = "| SifuFinds") -> str:
    """Return a <= max_len char <title> string with a '| SifuFinds'-style suffix.

    Prefers truncating at a ' — '/' - '/': '/' | ' separator that sits past
    35% of the title's length, so a short generic lead-in ("World Cup 2026:")
    never swallows the whole truncation and collapses many titles onto one
    identical <title> tag (confirmed live on ~85 of 236 posts, GEO/technical
    audit 2026-07-26). Falls back to clean word-boundary truncation with no
    ellipsis — a trailing "..." reads as a broken/cut-off title in search
    snippets (confirmed on ~43% of blog posts, technical SEO audit
    2026-08-11), and word-boundary truncation doesn't reintroduce the
    duplicate-title collapse since each title still truncates at a different
    point based on its own content.
    """
    full = f"{title} {suffix}"
    if len(full) <= max_len:
        return full
    best = None
    for sep in [" — ", " - ", ": ", " | "]:
        idx = title.find(sep)
        if idx > 10 and idx >= len(title) * 0.35:
            candidate = f"{title[:idx]} {suffix}"
            if len(candidate) <= max_len and (best is None or idx > best[0]):
                best = (idx, candidate)
    if best:
        return best[1]
    available = max_len - len(suffix) - 1
    truncated = title[:available].rsplit(" ", 1)[0]
    return f"{truncated} {suffix}"


def seo_meta_description(text: str, max_len: int = 155) -> str:
    """Clean word-boundary truncation to <= max_len chars, no ellipsis.

    Meant for meta descriptions (default 155, Google's display limit) and
    Open Graph descriptions (pass max_len=200-300, which social platforms
    tolerate before truncating themselves).
    """
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0].rstrip(".,;:—- ")
