#!/usr/bin/env bash
# Refuse to commit staged git conflict markers.
#
# Every bot workflow's push-retry loop does `git merge --no-edit origin/main
# || true` then `git add -A` + commit. A conflict the merge leaves behind is
# committed verbatim unless something regenerates the file first — and
# gen_blog_post_pages.py (without --force) skips pages that already exist, so
# a conflicted blog/*/index.html survives. 2026-09-26 incident: two such pages
# shipped `<<<<<<< HEAD` inside their JSON-LD, failing validate_site.py
# CHECK 3 and blocking every Hostinger deploy until fixed by hand.
#
# Run after `git add -A`, before `git commit`. Exits 1 (listing the files)
# if any staged file's content still contains a conflict marker line, so the
# job fails loudly and workflow_watchdog.yml retries it instead of shipping a
# poisoned commit. Only files changed in this commit are checked, and only
# their staged content (a commit that *removes* markers passes).
set -euo pipefail

changed="$(git diff --cached --name-only --diff-filter=ACMR)"
bad=""
if [ -n "$changed" ]; then
  bad="$(echo "$changed" | tr '\n' '\0' \
    | xargs -0 git grep --cached -I -l -E '^(<<<<<<<|>>>>>>>)( |$)' -- 2>/dev/null || true)"
fi
if [ -n "$bad" ]; then
  echo "❌ Refusing to commit — unresolved merge conflict markers in:" >&2
  echo "$bad" | sed 's/^/   /' >&2
  exit 1
fi
echo "✅ No conflict markers staged"
