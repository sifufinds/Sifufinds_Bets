"""
RapidWombat Pull Agent
Pulls articles straight from the RapidWombat project API and imports each one
through agent_rapidwombat_import.import_article(), so every guard (thin-content
refusal, Africa-framing check, sanitising, idempotent upsert keyed on
`rapidwombat-<id>`) applies exactly as it does for webhook deliveries.

Drafts with no title/body are skipped. Already-imported articles are skipped
unless --update is passed.

Usage:
  python3 agent_rapidwombat_pull.py --dry-run
  python3 agent_rapidwombat_pull.py [--update] [--then-generate]

Needs RAPIDWOMBAT_API_KEY in agents/python/.env (gitignored). Never commit it.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv(Path(__file__).parent / ".env")

from agent_rapidwombat_import import ID_PREFIX, ArticleRejected, import_article  # noqa: E402

BASE_URL = "https://api.rapidwombat.com/api/integrations/project/articles/"
PAGE_SIZE = 100
TIMEOUT_SECS = 30
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _headers() -> dict:
    key = os.environ.get("RAPIDWOMBAT_API_KEY", "").strip()
    if not key:
        sys.exit("RAPIDWOMBAT_API_KEY is not set in agents/python/.env")
    return {"X-PROJECT-API-KEY": key, "Content-Type": "application/json"}


def list_article_ids(headers: dict) -> list[dict]:
    items, offset = [], 0
    while True:
        resp = requests.get(BASE_URL, headers=headers, timeout=TIMEOUT_SECS,
                            params={"limit": PAGE_SIZE, "offset": offset})
        resp.raise_for_status()
        page = resp.json().get("results", [])
        items.extend(page)
        if len(page) < PAGE_SIZE:
            return items
        offset += PAGE_SIZE


def fetch_article(headers: dict, article_id: str) -> dict:
    resp = requests.get(f"{BASE_URL}{article_id}/", headers=headers, timeout=TIMEOUT_SECS)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--update", action="store_true", help="re-import articles already in posts.json")
    parser.add_argument("--then-generate", action="store_true", help="run gen_blog_post_pages.py afterwards")
    args = parser.parse_args()

    from agent_sports_blog import load_posts
    have = {p.get("id") for p in load_posts()}
    headers = _headers()

    imported = skipped = rejected = 0
    for item in list_article_ids(headers):
        if f"{ID_PREFIX}{item['id']}" in have and not args.update:
            skipped += 1
            continue
        article = fetch_article(headers, item["id"])
        if not (article.get("title") or "").strip() or not (article.get("content") or "").strip():
            skipped += 1  # unfinished draft on the RapidWombat side
            continue
        try:
            import_article(article, dry_run=args.dry_run)
            imported += 1
        except ArticleRejected as exc:
            rejected += 1
            print(f"  ✗  {article['id']} rejected: {exc}")

    print(f"Done: {imported} {'would be ' if args.dry_run else ''}imported, {skipped} skipped, {rejected} rejected")
    if args.then_generate and imported and not args.dry_run:
        subprocess.run([sys.executable, "gen_blog_post_pages.py"], cwd=REPO_ROOT, check=True)


if __name__ == "__main__":
    main()
