#!/usr/bin/env python3
"""One-time patch: point legacy (posts.json-orphaned) bookmaker review pages
at their new per-post OG image (scripts/generate_review_og_images.py) instead
of the sitewide generic og-image.png. Same reasoning as
backfill_legacy_resources.py — these pages are permanently frozen HTML that
gen_blog_post_pages.py --force can no longer reach.
"""
import glob
import os
import re

OG_DEFAULT = "https://sifufinds.com/assets/og-image.png"


def patch_file(path: str, slug: str) -> bool:
    if not os.path.exists(f"assets/og/{slug}.png"):
        return False
    html = open(path, encoding="utf-8").read()
    new_url = f"https://sifufinds.com/assets/og/{slug}.png"
    new_html = html.replace(OG_DEFAULT, new_url)
    if new_html == html:
        return False
    open(path, "w", encoding="utf-8").write(new_html)
    return True


def main():
    patched = 0
    for path in sorted(glob.glob("blog/*-review/index.html")):
        slug = path.split("/")[1]
        if patch_file(path, slug):
            patched += 1
            print(f"patched {path}")
    print(f"\n{patched} legacy review page(s) now use their own OG image")


if __name__ == "__main__":
    main()
