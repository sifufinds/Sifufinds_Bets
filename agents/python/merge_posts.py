"""
Merge posts.json from HEAD and FETCH_HEAD, deduplicating by ID.
Called by the breaking_news.yml workflow on push-retry to avoid losing posts.

2026-08-09 incident: load_posts_from_ref() used to swallow every read/parse
failure (bad git ref, conflict markers, invalid JSON) into an empty list,
and main() wrote the merge result unconditionally — including when that
meant writing {"posts": []} over an ~850-post file. This ran on every
breaking_news.yml push-retry, so it repeatedly stomped blog/posts.json
whenever `git show` hiccuped. Fixed to raise on a read failure (so the
calling workflow step fails loudly instead of silently corrupting state)
and to refuse to write a result much smaller than either input side.
"""
import json
import os
import subprocess
import sys


class RefReadError(RuntimeError):
    pass


def load_posts_from_ref(ref: str, path: str) -> list[dict]:
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{ref}:{path}"], stderr=subprocess.DEVNULL
        ).decode()
    except subprocess.CalledProcessError as e:
        raise RefReadError(f"git show {ref}:{path} failed: {e}") from e
    if "<<<<<<< " in raw:
        raise RefReadError(f"{ref}:{path} contains unresolved merge conflict markers")
    try:
        return json.loads(raw).get("posts", [])
    except json.JSONDecodeError as e:
        raise RefReadError(f"{ref}:{path} is not valid JSON: {e}") from e


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

    smallest_input = min(len(ours), len(theirs))
    if smallest_input >= 20 and len(merged) < smallest_input * 0.5:
        raise RuntimeError(
            f"Refusing to write: merged result ({len(merged)} posts) is far "
            f"smaller than the smaller input side ({smallest_input} posts) — "
            f"looks like data loss, not a real merge. ours={len(ours)} "
            f"theirs={len(theirs)}"
        )

    payload = {"posts": merged}

    tmp_path = "blog/posts.json.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, "blog/posts.json")

    js_tmp_path = "blog/posts-data.js.tmp"
    with open(js_tmp_path, "w", encoding="utf-8") as f:
        f.write(f"window.POSTS_DATA={json.dumps(payload, ensure_ascii=False)};\n")
    os.replace(js_tmp_path, "blog/posts-data.js")

    print(f"Merged {len(ours)} ours + {len(theirs)} remote = {len(merged)} unique posts")


if __name__ == "__main__":
    try:
        main()
    except RefReadError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
