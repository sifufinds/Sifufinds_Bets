"""
Sanity CMS Sync Agent
Pulls published `blogPost` documents from the Sanity project (studio at
../../studio-sifu-finds, sibling to this repo) and upserts them into
blog/posts.json using the exact same dict shape every other content agent
produces (see agent_sports_blog.py). This is a one-way, read-only sync —
Sanity is an authoring UI, not a new rendering path. Every SEO/compliance/
linking guard already wired into gen_blog_post_pages.py (dedupe_slugs,
sanitize_internal_links, JSON-LD, resources box, the 18+/BeGambleAware
footer, feature-image auto-generation) still runs unchanged, because the
output of this script is just more entries in the same posts.json array.

Drafts (Sanity doc IDs prefixed `drafts.`) are never synced — only
published documents reach the live site.

Usage:
  python3 agent_sanity_sync.py                # sync + write posts.json
  python3 agent_sanity_sync.py --dry-run       # show what would change, write nothing
  python3 agent_sanity_sync.py --then-generate  # also run gen_blog_post_pages.py --force after syncing

After a real (non-dry-run) sync, run:
  python3 gen_blog_post_pages.py --force
to regenerate the static HTML pages (or pass --then-generate to do both in one step).
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv(Path(__file__).parent / ".env")

from agent_sports_blog import load_posts, save_posts  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from generate_blog_feature_image import ensure_feature_image  # noqa: E402

SANITY_PROJECT_ID = os.getenv("SANITY_PROJECT_ID")
SANITY_DATASET = os.getenv("SANITY_DATASET", "production")
SANITY_API_TOKEN = os.getenv("SANITY_API_TOKEN")
SANITY_API_VERSION = "2024-01-01"

GROQ_QUERY = (
    '*[_type == "blogPost" && !(_id in path("drafts.**"))]'
    "{_id, _updatedAt, title, \"slug\": slug.current, excerpt, body, category, "
    "author, tags, featured, bookmakerFeatured, readTime, imageColor, imageIcon, "
    "publishedAt}"
)


def fetch_sanity_posts() -> list[dict]:
    if not (SANITY_PROJECT_ID and SANITY_API_TOKEN):
        raise RuntimeError(
            "SANITY_PROJECT_ID / SANITY_API_TOKEN not set — check agents/python/.env"
        )
    url = f"https://{SANITY_PROJECT_ID}.api.sanity.io/v{SANITY_API_VERSION}/data/query/{SANITY_DATASET}"
    resp = requests.get(
        url,
        params={"query": GROQ_QUERY},
        headers={"Authorization": f"Bearer {SANITY_API_TOKEN}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("result", [])


def _estimate_read_time(body_md: str) -> int:
    words = len(re.findall(r"\S+", body_md or ""))
    return max(3, round(words / 200))


def sanity_doc_to_post(doc: dict) -> dict | None:
    slug = doc.get("slug")
    title = doc.get("title")
    body = doc.get("body")
    if not (slug and title and body):
        return None
    return {
        "id": f"sanity-{doc['_id']}",
        "category": doc.get("category") or "football",
        "title": title,
        "slug": slug,
        "excerpt": doc.get("excerpt") or "",
        "body": body,
        "author": doc.get("author") or "SifuFinds Editorial Team",
        "published_at": doc.get("publishedAt")
        or datetime.now(timezone.utc).isoformat(),
        "image_color": doc.get("imageColor") or "#f2c464",
        "image_icon": doc.get("imageIcon") or "",
        "tags": doc.get("tags") or [],
        "featured": bool(doc.get("featured", False)),
        "bookmaker_featured": doc.get("bookmakerFeatured") or "",
        "read_time": doc.get("readTime") or _estimate_read_time(body),
    }


def sync(dry_run: bool = False) -> tuple[int, int]:
    sanity_docs = fetch_sanity_posts()
    posts = load_posts()
    by_id = {p.get("id"): i for i, p in enumerate(posts)}

    added, updated = 0, 0
    for doc in sanity_docs:
        new_post = sanity_doc_to_post(doc)
        if new_post is None:
            print(f"  ⚠  skipping Sanity doc {doc.get('_id')} — missing title/slug/body")
            continue

        existing_idx = by_id.get(new_post["id"])
        if existing_idx is None:
            if dry_run:
                print(f"  + would add: {new_post['title']!r} ({new_post['slug']})")
            else:
                feature_image = ensure_feature_image(new_post)
                if feature_image:
                    new_post["feature_image"] = feature_image
                posts.insert(0, new_post)
                by_id[new_post["id"]] = 0
            added += 1
        else:
            existing = posts[existing_idx]
            slug_changed = existing.get("slug") != new_post["slug"]
            if dry_run:
                print(f"  ~ would update: {new_post['title']!r} ({new_post['slug']})")
            else:
                feature_image = existing.get("feature_image")
                if slug_changed or not feature_image:
                    feature_image = ensure_feature_image(new_post)
                new_post["feature_image"] = feature_image
                posts[existing_idx] = new_post
            updated += 1

    if not dry_run and (added or updated):
        save_posts(posts)

    return added, updated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--then-generate",
        action="store_true",
        help="Run gen_blog_post_pages.py --force after a successful sync",
    )
    args = parser.parse_args()

    added, updated = sync(dry_run=args.dry_run)
    label = "Would sync" if args.dry_run else "Synced"
    print(f"  ✓  {label}: {added} new, {updated} updated")

    if args.then_generate and not args.dry_run and (added or updated):
        repo_root = Path(__file__).parent.parent.parent
        subprocess.run(
            [sys.executable, "gen_blog_post_pages.py", "--force"],
            cwd=repo_root,
            check=True,
        )


if __name__ == "__main__":
    main()
