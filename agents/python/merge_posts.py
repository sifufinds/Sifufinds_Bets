"""
Merge posts.json from HEAD and FETCH_HEAD, deduplicating by ID.
Called by the breaking_news.yml workflow on push-retry to avoid losing posts.
"""
import json
import subprocess
import sys


def load_posts_from_ref(ref: str, path: str) -> list[dict]:
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{ref}:{path}"], stderr=subprocess.DEVNULL
        ).decode()
        if "<<<<<<< " in raw:
            return []
        return json.loads(raw).get("posts", [])
    except Exception:
        return []


def main() -> None:
    ours = load_posts_from_ref("HEAD", "blog/posts.json")
    theirs = load_posts_from_ref("FETCH_HEAD", "blog/posts.json")

    seen: set[str] = set()
    merged: list[dict] = []
    for p in ours + theirs:
        if p["id"] not in seen:
            seen.add(p["id"])
            merged.append(p)
    merged.sort(key=lambda p: p.get("published_at", ""), reverse=True)

    payload = {"posts": merged}

    with open("blog/posts.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    with open("blog/posts-data.js", "w", encoding="utf-8") as f:
        f.write(f"window.POSTS_DATA={json.dumps(payload, ensure_ascii=False)};\n")

    print(f"Merged {len(ours)} ours + {len(theirs)} remote = {len(merged)} unique posts")


if __name__ == "__main__":
    main()
