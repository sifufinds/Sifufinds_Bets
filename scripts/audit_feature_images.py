#!/usr/bin/env python3
"""Find posts whose feature image was likely generated from a governing-
body/competition tag (FIFA, UEFA, AFCON, "World Ranking", ...) before
generate_blog_feature_image.py's _ORG_AND_COMPETITION_WORDS blocklist existed
(added 2026-07-27 after a live post showed a "FIFA Women's World Cup 2023"
tournament graphic on a Men's World Ranking article — see that module's
docstring for the full incident).

A tag reaching the old, looser filter doesn't guarantee it was the tag that
actually produced the current image (an earlier, legitimate tag in the same
post's tag list may have already resolved a photo first) — so this script
also inspects the PNG itself: build_image() (icon-card fallback) always
paints a solid white rounded-rectangle card at a fixed position, while
build_image_with_photo() never does (it's a full-bleed photo), so sampling
that one pixel cheaply tells photo-mode from icon-mode with no network calls.
Only photo-mode images with a newly-blocked tag as their *first* candidate
are flagged — that combination is what the incident actually looked like.

Usage:
  python3 scripts/audit_feature_images.py              # list suspects
  python3 scripts/audit_feature_images.py --regenerate  # also rebuild them
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from generate_blog_feature_image import (  # noqa: E402
    OUT_DIR,
    _GENERIC_TAG_WORDS,
    _looks_like_entity_candidate,
    generate_feature_image,
)

POSTS_JSON = ROOT / "blog" / "posts.json"

# The card build_image() always draws: rounded rect at (90, 145)-(430, 485).
# Sample well inside it — pure/near-white there means icon-mode.
_CARD_PROBE_POINT = (260, 300)
_WHITE_THRESHOLD = 245


def is_photo_mode(png_path: Path) -> bool:
    try:
        img = Image.open(png_path).convert("RGB")
    except Exception:
        return False
    r, g, b = img.getpixel(_CARD_PROBE_POINT)
    return not (r >= _WHITE_THRESHOLD and g >= _WHITE_THRESHOLD and b >= _WHITE_THRESHOLD)


def _old_looks_like_entity_candidate(name: str) -> bool:
    """Reproduces the pre-2026-07-27 filter (generic words only, no
    org/competition blocklist) so we can diff old vs new candidate lists."""
    words = [w for w in re.split(r"\s+", name.strip()) if w]
    if not words:
        return False
    normalized = {re.sub(r"[^a-z]", "", w.lower()) for w in words}
    return not normalized <= _GENERIC_TAG_WORDS


def _first_candidate(post: dict, filt) -> str | None:
    for tag in post.get("tags", []) or []:
        tag = (tag or "").strip()
        if tag and filt(tag):
            return tag
    return None


def find_suspects(posts: list[dict]) -> list[dict]:
    suspects = []
    for post in posts:
        slug = post.get("slug")
        if not slug:
            continue
        png_path = OUT_DIR / f"{slug}.png"
        if not png_path.exists() or not is_photo_mode(png_path):
            continue
        old_first = _first_candidate(post, _old_looks_like_entity_candidate)
        new_first = _first_candidate(post, _looks_like_entity_candidate)
        if old_first and old_first != new_first:
            suspects.append({"post": post, "slug": slug, "risky_tag": old_first})
    return suspects


def find_all_photo_mode(posts: list[dict]) -> list[dict]:
    """Every post whose current image is photo-mode, regardless of which tag
    produced it — used for a full site resweep after a structural pipeline
    fix (accent-folding, product-shot filtering) that isn't tied to any one
    tag, so the tag-diff heuristic in find_suspects() can't target it."""
    out = []
    for post in posts:
        slug = post.get("slug")
        if not slug:
            continue
        png_path = OUT_DIR / f"{slug}.png"
        if png_path.exists() and is_photo_mode(png_path):
            out.append({"post": post, "slug": slug, "risky_tag": None})
    return out


def main() -> None:
    regenerate = "--regenerate" in sys.argv
    full_sweep = "--all-photo-mode" in sys.argv

    with open(POSTS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    posts = data.get("posts", [])

    if full_sweep:
        suspects = find_all_photo_mode(posts)
        print(f"{len(suspects)} photo-mode image(s) out of {len(posts)} posts (full sweep).\n")
    else:
        suspects = find_suspects(posts)
        print(f"{len(suspects)} suspect image(s) out of {len(posts)} posts.\n")
        for s in suspects:
            print(f"  {s['slug']:<65} risky tag: {s['risky_tag']!r}")

    if not regenerate or not suspects:
        if not regenerate:
            print("\nDry run only — pass --regenerate to rebuild these images.")
        return

    print()
    changed = 0
    for i, s in enumerate(suspects, 1):
        slug = s["slug"]
        (OUT_DIR / f"{slug}.png").unlink(missing_ok=True)
        url = generate_feature_image(s["post"])
        if url:
            s["post"]["feature_image"] = url
            changed += 1
            print(f"  [{i}/{len(suspects)}] ✓ regenerated {slug}")
        else:
            print(f"  [{i}/{len(suspects)}] ⚠ failed to regenerate {slug}")
        if i % 20 == 0:
            with open(POSTS_JSON, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    with open(POSTS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Regenerated {changed} of {len(suspects)} image(s).")


if __name__ == "__main__":
    main()
