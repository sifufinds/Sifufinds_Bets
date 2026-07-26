#!/usr/bin/env python3
"""One-time backfill: swap the generic branded icon card for a real subject
photo on already-published posts that have a genuine player/team tag.

generate_blog_feature_image.py's ensure_feature_image() only generates an
image the first time (skips whenever assets/og/{slug}.png already exists),
so the real-photo feature added 2026-07-26 only ever applied to brand-new
posts going forward — every post published before that still has its
original icon-card image on disk. This script forces a regeneration for the
subset of existing posts where that's actually likely to be an improvement.

Deliberately stricter than generate_blog_feature_image.py's own
_looks_like_entity_candidate() filter used for new posts, in two ways —
bulk-regenerating 200+ live, already-public OG images is a one-time,
harder-to-quietly-revert operation than generating a fresh image for one
new post:

1. A first pass (strict_entity_candidates) excludes known countries
   (COUNTRY_LINKS) and bookmakers (BOOKMAKER_LINKS), plus a small curated
   list of tournament/organisation/generic-phrase tags observed in the
   actual tag data, before a post is even considered eligible.

2. A first backfill run (2026-07-26) that only applied filter #1 still
   produced real false positives: a post whose only eligible tag was a
   generic phrase ("Tactical Trends") got an unrelated stats-chart image,
   and a post tagged with excluded bookmakers still picked up a *different*
   bookmaker's logo, because the actual photo search fell through to the
   full unfiltered tag list instead of the vetted candidates. Root cause:
   a denylist of generic words can never be complete for free-text tags.
   Fixed at the source — generate_blog_feature_image.verified_entity_photo()
   now only accepts a candidate that Wikipedia's own page independently
   confirms is a real sports subject, then prefers a nicer/more current
   photo of that same confirmed name from the news/social tier, falling
   back to the Wikipedia image itself. This lives in the core pipeline (not
   just this backfill script) so every new post gets the same protection.

Posts with no verified candidate are left on their existing icon-card image
untouched.

Usage:
  python3 scripts/backfill_feature_photos.py            # dry run: list what would change
  python3 scripts/backfill_feature_photos.py --apply    # actually regenerate + save posts.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import gen_blog_post_pages as g  # noqa: E402
from generate_blog_feature_image import (  # noqa: E402
    OUT_DIR,
    _download_photo,
    _looks_like_entity_candidate,
    build_image_with_photo,
    verified_entity_photo,
)

POSTS_JSON = ROOT / "blog" / "posts.json"

_NON_ENTITY_TAGS = {
    "fifa", "uefa", "caf", "afcon", "nlrc", "bclb", "gca", "wcgrb",
    "begambleaware", "gambling therapy", "world ranking", "grand slam",
    "commonwealth games", "premier league", "champions league",
    "responsible gambling", "betting insights", "african bookmakers",
    "african sports bettors", "african para-athletes", "squad depth",
    "world cup 2026", "value bets", "group stage",
}


def _country_and_bookmaker_names() -> set[str]:
    names = {k.lower() for k in g.COUNTRY_LINKS}
    names |= {k.lower() for k in g._TAG_COUNTRY}
    names |= {kw.lower() for kw, _href, _title in g.BOOKMAKER_LINKS}
    return names


def strict_entity_candidates(post: dict, exclude: set[str], limit: int = 8) -> list[str]:
    """Same tag-sourced candidate list as generate_blog_feature_image's own
    _subject_candidates(), plus the two extra exclusion layers described in
    the module docstring above. This is still only a coarse pre-filter —
    verified_entity_photo() below is what actually confirms each candidate
    before it's ever used."""
    candidates: list[str] = []
    for tag in post.get("tags", []) or []:
        tag = (tag or "").strip()
        if not tag or tag in candidates:
            continue
        if not _looks_like_entity_candidate(tag):
            continue
        if tag.lower() in exclude:
            continue
        candidates.append(tag)
    return candidates[:limit]


def main() -> None:
    apply = "--apply" in sys.argv
    exclude = _country_and_bookmaker_names() | _NON_ENTITY_TAGS

    with open(POSTS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    posts = data.get("posts", [])

    eligible = [(p, strict_entity_candidates(p, exclude)) for p in posts]
    eligible = [(p, c) for p, c in eligible if c]
    print(f"{len(eligible)} of {len(posts)} posts have a real player/team tag candidate.\n")

    if not apply:
        for post, candidates in eligible:
            print(f"  {post['slug']:<55} {candidates}")
        print("\nDry run only — pass --apply to actually fetch photos and regenerate images.")
        return

    changed = 0
    skipped_no_photo = 0
    for i, (post, candidates) in enumerate(eligible, 1):
        slug = post["slug"]
        print(f"[{i}/{len(eligible)}] {slug} — trying {candidates}")
        photo = None
        for name in candidates:
            url = verified_entity_photo(name)
            if not url:
                continue
            photo = _download_photo(url)
            if photo is not None:
                break
        if photo is None:
            skipped_no_photo += 1
            print("    — no Wikipedia-verified subject found, leaving existing image as-is")
            continue
        img = build_image_with_photo(
            title=post.get("title", ""),
            category=post.get("category", ""),
            image_color=post.get("image_color", "#1a6b35"),
            photo=photo,
        )
        out_path = OUT_DIR / f"{slug}.png"
        img.save(out_path, "PNG", optimize=True)
        post["feature_image"] = f"/assets/og/{slug}.png"
        changed += 1
        print("    ✓ regenerated with a real subject photo")

    if changed:
        with open(POSTS_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Regenerated {changed} image(s). {skipped_no_photo} had a candidate tag but no photo found (left untouched).")


if __name__ == "__main__":
    main()
