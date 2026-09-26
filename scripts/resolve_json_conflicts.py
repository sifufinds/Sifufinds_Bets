"""
Auto-resolve git merge conflicts in agent JSON state files.

Bot workflows share state files like agents/python/fact_check_flags.json and
covered_stories_state.json. When two bots write one concurrently, the
push-retry `git merge` conflicts on it. Before 2026-09-26 the markers were
committed verbatim; after assert_no_conflict_markers.sh was added the commit
is refused instead, which is safe but drops that run's new post (seen
2026-09-26 in agent_priority_content.yml on fact_check_flags.json).

This resolves those conflicts structurally instead of textually:
  - dict + dict  -> union of keys, shared keys merged recursively
  - list + list  -> union; records deduped by a shared id-like key
                    (id/slug/key/url/domain), plain values by equality
  - numbers      -> max (counters like `runs` only ever grow)
  - other scalar -> ours (this run's freshly written value)

Scope is deliberately limited to agents/python/*.json: those are
append/record-style state where a union is always correct. Live data
(data/*.json) and blog/posts.json (merge_posts.py owns it) are left alone;
an unparseable or out-of-scope conflict stays unresolved so
assert_no_conflict_markers.sh still blocks the commit loudly.

Run from the repo root right after `git merge`. Always exits 0.
"""
import json
import subprocess
import sys

SCOPE_PREFIX = "agents/python/"
ID_KEYS = ("id", "slug", "key", "url", "domain")


def _canon(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _record_key(items: list) -> str | None:
    """Return an id-like key every dict in `items` has, if there is one."""
    if not items or not all(isinstance(i, dict) for i in items):
        return None
    for key in ID_KEYS:
        if all(key in i for i in items):
            return key
    return None


def merge_values(ours, theirs):
    if isinstance(ours, dict) and isinstance(theirs, dict):
        merged = dict(theirs)
        for key, value in ours.items():
            merged[key] = merge_values(value, theirs[key]) if key in theirs else value
        return merged
    if isinstance(ours, list) and isinstance(theirs, list):
        key = _record_key(ours + theirs)
        ident = (lambda i: _canon(i[key])) if key else _canon
        ours_ids = {ident(i) for i in ours}
        # Keep theirs' order, drop entries ours supersedes, then append ours.
        return [i for i in theirs if ident(i) not in ours_ids] + ours
    both_numbers = all(
        isinstance(v, (int, float)) and not isinstance(v, bool) for v in (ours, theirs)
    )
    if both_numbers:
        return max(ours, theirs)
    return ours


def _stage(path: str, stage: int):
    raw = subprocess.check_output(["git", "show", f":{stage}:{path}"])
    return json.loads(raw.decode("utf-8"))


def unmerged_paths() -> list[str]:
    out = subprocess.check_output(["git", "diff", "--name-only", "--diff-filter=U"])
    return [p for p in out.decode("utf-8").splitlines() if p]


def resolve(path: str) -> bool:
    try:
        ours, theirs = _stage(path, 2), _stage(path, 3)
    except (subprocess.CalledProcessError, json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"  ⚠ left unresolved (can't read both sides): {path}: {e}")
        return False
    merged = merge_values(ours, theirs)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
        f.write("\n")
    subprocess.check_call(["git", "add", path])
    print(f"  ✓ resolved: {path}")
    return True


def main() -> None:
    targets = [
        p for p in unmerged_paths() if p.startswith(SCOPE_PREFIX) and p.endswith(".json")
    ]
    if not targets:
        print("No agent JSON state conflicts to resolve")
        return
    print(f"Resolving {len(targets)} agent JSON state conflict(s):")
    for path in targets:
        resolve(path)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never break the caller; the marker guard still runs
        print(f"resolve_json_conflicts.py error (non-fatal): {e}", file=sys.stderr)
