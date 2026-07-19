#!/usr/bin/env python3
"""Pre-deploy site validator — catches 403/404 issues before they reach production.

Checks:
  1. Public directories without index.html  → would 403 with Options -Indexes
  2. Broken absolute internal links          → would 404 on the live site
  3. Invalid JSON-LD structured data         → schema silently unparseable by Google/AI crawlers

Usage:
    python3 scripts/validate_site.py            # report only
    python3 scripts/validate_site.py --strict   # exit 1 on any warning too

Exit codes:
    0 — all checks pass
    1 — one or more errors (deploy should be blocked)
"""

import json
import os
import re
import sys

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directories that intentionally have no index.html (data, assets, tooling)
SKIP_DIRS = {
    ".git", ".venv", ".github", ".claude",
    "__pycache__", "node_modules",
    "agents", "firecrawl", "geo-content-writer", "supabase",
    "data", "assets", "scripts", "brands",
    "translations",  # blog/translations/ — build-time source JSON, never a served page
}


def get_git_tracked_dirs(root: str) -> set[str]:
    import subprocess
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, cwd=root
        )
        tracked_dirs: set[str] = set()
        for line in result.stdout.splitlines():
            parts = line.split("/")
            for i in range(1, len(parts)):
                tracked_dirs.add("/".join(parts[:i]))
        return tracked_dirs
    except Exception:
        return set()


# ── CHECK 1: directories without index.html ──────────────────────────────────

def find_missing_index(root: str) -> list[str]:
    tracked_dirs = get_git_tracked_dirs(root)
    missing = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        if rel == ".":
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
            continue
        parts = set(rel.split("/"))
        if parts & SKIP_DIRS:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        # Only check directories that git actually tracks (ignores empty/untracked local dirs)
        if rel not in tracked_dirs:
            continue
        if "index.html" not in filenames:
            missing.append(rel)
    return sorted(missing)


# ── CHECK 2: broken absolute internal links ───────────────────────────────────

def find_broken_links(root: str) -> dict[str, list[str]]:
    broken: dict[str, list[str]] = {}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in filenames:
            if fname != "index.html":
                continue
            fpath = os.path.join(dirpath, fname)
            rel_src = os.path.relpath(fpath, root)
            try:
                content = open(fpath, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue

            for m in re.findall(r'href="(https://sifufinds\.com/[^"#?]+)', content):
                target = m.rstrip("/")
                rel_path = target.replace("https://sifufinds.com/", "").rstrip("/")
                if not rel_path:
                    continue
                index_file = os.path.join(root, rel_path, "index.html")
                html_file = os.path.join(root, rel_path + ".html")
                if not os.path.exists(index_file) and not os.path.exists(html_file):
                    broken.setdefault(target, []).append(rel_src)

    return broken


# ── CHECK 3: invalid JSON-LD ────────────────────────────────────────────────────
# Found 2026-07-19: extract_faq_schema() left raw newlines un-escaped inside FAQ
# answer text, and title/excerpt were interpolated into JSON-LD without escaping
# quote characters — both produced JSON-LD that silently failed to parse (~20%
# of blog posts were affected) while the page itself rendered fine, so nothing
# else caught it. Root cause fixed in gen_blog_post_pages.py via json.dumps();
# this check exists so a future regression can't hide the same way again.

def find_invalid_jsonld(root: str) -> dict[str, str]:
    invalid: dict[str, str] = {}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in filenames:
            if fname != "index.html":
                continue
            fpath = os.path.join(dirpath, fname)
            rel_src = os.path.relpath(fpath, root)
            try:
                content = open(fpath, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue

            for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.S):
                block = block.strip()
                if not block:
                    continue
                try:
                    json.loads(block)
                except json.JSONDecodeError as e:
                    invalid[rel_src] = str(e)
                    break

    return invalid


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main() -> None:
    strict = "--strict" in sys.argv
    errors = 0
    warnings = 0

    print("=" * 70)
    print("SifuFinds pre-deploy validation")
    print("=" * 70)

    # Check 1 — missing index.html
    missing = find_missing_index(SITE_ROOT)
    if missing:
        print(f"\n🚨 CHECK 1 FAILED — {len(missing)} public director(ies) have no index.html")
        print("   These will return 403 Forbidden on the live server.\n")
        for d in missing:
            print(f"   ✗  {d}/")
        print()
        print("   Fix: create a hub index.html for each directory above,")
        print("   or add it to SKIP_DIRS in scripts/validate_site.py if intentional.\n")
        errors += len(missing)
    else:
        print("\n✅ CHECK 1 PASSED — all public directories have index.html")

    # Check 2 — broken internal links
    broken = find_broken_links(SITE_ROOT)

    # Filter out links that are handled by .htaccess 301 redirects
    htaccess_path = os.path.join(SITE_ROOT, ".htaccess")
    redirect_targets: set[str] = set()
    try:
        for line in open(htaccess_path):
            m = re.match(r'^\s*Redirect\s+30[12]\s+(/\S+)', line)
            if m:
                redirect_targets.add("https://sifufinds.com" + m.group(1).rstrip("/"))
                continue
            # mod_rewrite form: RewriteRule ^old-slug/?$ /new/path/ [R=301,L]
            m = re.match(r'^\s*RewriteRule\s+\^(.+?)\$\s+(/\S+?)\s+\[R=30[12]', line)
            if m:
                slug = m.group(1).rstrip("/?")
                redirect_targets.add("https://sifufinds.com/" + slug.lstrip("/"))
    except OSError:
        pass

    real_broken = {t: srcs for t, srcs in broken.items()
                   if t not in redirect_targets}

    if real_broken:
        print(f"\n🚨 CHECK 2 FAILED — {len(real_broken)} broken internal link(s) with no redirect\n")
        for target in sorted(real_broken):
            sources = real_broken[target]
            print(f"   ✗  {target}")
            for src in sources[:2]:
                print(f"         ← {src}")
            if len(sources) > 2:
                print(f"         ← (+{len(sources)-2} more)")
        print()
        print("   Fix: add a 'Redirect 301 /path /correct/path/' rule to .htaccess,")
        print("   or create the missing page, or fix the link in posts.json + regenerate.\n")
        errors += len(real_broken)
    elif broken:
        covered = len(broken) - len(real_broken)
        print(f"\n✅ CHECK 2 PASSED — {covered} broken link(s) covered by .htaccess redirects")
    else:
        print("\n✅ CHECK 2 PASSED — no broken internal links found")

    # Check 3 — invalid JSON-LD
    invalid_jsonld = find_invalid_jsonld(SITE_ROOT)
    if invalid_jsonld:
        print(f"\n🚨 CHECK 3 FAILED — {len(invalid_jsonld)} page(s) have invalid JSON-LD\n")
        for src, err in sorted(invalid_jsonld.items())[:15]:
            print(f"   ✗  {src}")
            print(f"         {err}")
        if len(invalid_jsonld) > 15:
            print(f"   … (+{len(invalid_jsonld) - 15} more)")
        print()
        print("   Fix: ensure all JSON-LD string values are built with json.dumps(),")
        print("   never manual .replace('\"', '\\\\\"') — that misses newlines and re-runs.\n")
        errors += len(invalid_jsonld)
    else:
        print("\n✅ CHECK 3 PASSED — all JSON-LD blocks are valid")

    # Summary
    print("=" * 70)
    if errors == 0:
        print("✅ All checks passed — safe to deploy.")
        sys.exit(0)
    else:
        print(f"❌ {errors} error(s) found — fix before deploying.")
        sys.exit(1)


if __name__ == "__main__":
    main()
