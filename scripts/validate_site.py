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
# else caught it. Root cause fixed in gen_blog_post_pages.py via json.dumps().
#
# Found again 2026-07-30 (schema SEO audit): the same manual/absent-escaping
# pattern was never propagated beyond gen_blog_post_pages.py — nine other
# generators (gen_all_cities.py, gen_bonus_pages.py, gen_bookmaker_country_
# pages.py, gen_city_pages.py, gen_guide_pages.py, gen_payment_country_pages.py,
# gen_payment_pages.py, gen_sport_country_pages.py, generate_country_pages.py)
# were still building FAQPage/HowTo JSON-LD with either `.replace('"', '\\"')`
# (misses newlines/backslashes) or zero escaping at all. All nine now build
# their JSON-LD via json.dumps(). This check parses every index.html site-wide
# (not just blog posts), so it already covers all of them — but the fix must
# stay in every generator, not just this file, or it silently regresses again.

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

# ── CHECK 4: feature-image tag-safety regression guard ──────────────────────
# Guards against a repeat of two 2026-07-27 incidents: (1) a Men's FIFA World
# Ranking post shipped live with a FIFA Women's World Cup 2023 tournament
# graphic as its feature image, because governing-body/competition tags
# (FIFA, AFCON, NBA...) and bare country tags (Morocco) were trusted as photo-
# search subjects with no way to know which of many unrelated tournaments/
# editions/genders they might resolve to; (2) a WAFCON post shipped with a
# men's Nigeria squad photo — "wafcon" wasn't blocked here, and even once
# blocked, a bare country tag like "Nigeria" still defaulted to the men's
# team with no post-level women's-context signal. See
# generate_blog_feature_image.py's _ORG_AND_COMPETITION_WORDS /
# _COMPETITION_STRUCTURE_WORDS / _post_is_womens_context and player_photo.py's
# _gender_mismatch / qualify_entity_query for the actual fixes — this check
# exists purely so a future edit to those filters that quietly reopens the
# gap (or over-tightens it) fails loudly here instead of shipping silently.

_KNOWN_RISKY_TAGS = [
    "FIFA", "UEFA", "CAF", "AFCON", "AFCON 2026", "NBA", "World Ranking",
    "African Cup of Nations", "Africa Cup of Nations", "T20 World Cup",
    "Women's T20 World Cup", "CAF Champions League", "Premier League",
    "Champions League", "Grand Slam", "Commonwealth Games", "US Open",
    "Queen's Club Championship", "County Championship", "World Cup Bracket",
    "EFL Trophy", "Six Nations", "Europa League", "WAFCON", "WSL", "NWSL",
    "UWCL", "Test matches", "Test series",
]
_KNOWN_SAFE_TAGS = [
    "Real Madrid", "Morocco", "Lakers", "Chelsea", "Super Eagles",
    "Marc Cucurella", "New York Knicks", "Cape Verde", "LeBron James",
    "Nigeria",
]


def check_feature_image_tag_safety() -> list[str]:
    # Deliberately imports feature_image_tag_filter.py, NOT
    # generate_blog_feature_image.py — the latter imports Pillow at module
    # level for the actual image compositing, and the deploy workflow that
    # runs this validator never installs any pip packages (this script was
    # always pure-stdlib by design). Importing generate_blog_feature_image
    # directly here crashed with ModuleNotFoundError: No module named 'PIL'
    # on every deploy run for several hours (2026-07-27) until caught — an
    # interim fix wrapped the import in try/except and skipped the check on
    # failure, which stopped the crash but made CHECK 4 a permanent no-op in
    # CI (Pillow is never going to appear there). The actual fix is this
    # import: feature_image_tag_filter.py needs nothing but `re`, so it
    # always succeeds and the guard actually runs.
    sys.path.insert(0, os.path.join(SITE_ROOT, "scripts"))
    from feature_image_tag_filter import (  # noqa: E402
        _looks_like_entity_candidate,
        _looks_like_womens_context,
    )

    problems = []
    for tag in _KNOWN_RISKY_TAGS:
        if _looks_like_entity_candidate(tag):
            problems.append(f"'{tag}' should be BLOCKED as a photo-search candidate but is now allowed")
    for tag in _KNOWN_SAFE_TAGS:
        if not _looks_like_entity_candidate(tag):
            problems.append(f"'{tag}' should be ALLOWED as a photo-search candidate but is now blocked")

    # Regression coverage for the 2026-07-27 WAFCON incident: a bare country
    # tag ('Nigeria') sitting alongside a women's-competition acronym
    # ('WAFCON') must be recognised as women's context so it resolves to the
    # correct national side instead of silently defaulting to the men's team.
    if not _looks_like_womens_context("2026 WAFCON Kicks Off in Morocco", "", "WAFCON", "Nigeria", "Morocco"):
        problems.append("a post tagged with 'WAFCON' should be detected as women's-football context but is not")
    if not _looks_like_womens_context("", "", "Women's Super League", "Chelsea"):
        problems.append("a post tagged with \"Women's Super League\" should be detected as women's-football context but is not")
    if _looks_like_womens_context("Nigeria vs Morocco AFCON preview", "", "AFCON", "Nigeria", "Morocco"):
        problems.append("a plain men's AFCON post should NOT be detected as women's-football context but is")
    return problems


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
                continue
            # Affiliate link masking form: RewriteRule ^slug/?$ "https://external-tracker..." [R=301,L,NC]
            # (see the "AFFILIATE LINK MASKING" block in .htaccess) — the target
            # is an external tracking URL, not a local page, but it's still a
            # real 301, so a blog/social link to https://sifufinds.com/<slug>
            # is not broken just because it doesn't resolve to on-site content.
            m = re.match(r'^\s*RewriteRule\s+\^(.+?)\$\s+"?https?://\S+?"?\s+\[R=30[12]', line)
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

    # Check 4 — feature-image tag-safety regression guard
    tag_safety_problems = check_feature_image_tag_safety()
    if tag_safety_problems:
        print(f"\n🚨 CHECK 4 FAILED — {len(tag_safety_problems)} feature-image tag-safety issue(s)\n")
        for p in tag_safety_problems:
            print(f"   ✗  {p}")
        print()
        print("   Fix: see generate_blog_feature_image.py's _ORG_AND_COMPETITION_WORDS /")
        print("   _COMPETITION_STRUCTURE_WORDS — a change there just broke a known-good")
        print("   or known-risky tag. (Separately, run")
        print("   `python3 scripts/audit_feature_images.py` periodically as a live-content")
        print("   heal — it flags posts whose tags still route to a risky candidate under")
        print("   the pre-2026-07-27 filter; not a blocking check since a post can be fully")
        print("   fixed on disk yet still trip that historical comparison.)\n")
        errors += len(tag_safety_problems)
    else:
        print("\n✅ CHECK 4 PASSED — feature-image tag-safety guard holds")

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
