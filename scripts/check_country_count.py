#!/usr/bin/env python3
"""Guard against "N African countries" style copy silently going stale
whenever a country is added to or removed from COUNTRY_DATA.

Why this exists: on 2026-08-14 the site was expanded from 23 to 33
countries. The sweep to update "23 African countries" copy site-wide was
done by hand across ~110 files and still missed several spots on a second
pass (assets/shared.js's About modal, a stat split across two HTML
elements in about/index.html and press/index.html, two un-wired stat
counters in countries/index.html) — proving hand-sweeping this class of
copy does not reliably converge. This script is the permanent, automated
replacement for that manual sweep, following the same
report-then---fix pattern as scripts/seo_check.py and
scripts/check_indexability.py elsewhere in this repo.

site_stats.py (repo root) is the single source of truth for the current
correct numbers, parsed live from assets/shared.js's COUNTRY_DATA — never
hardcode the country count in this script either.

Checks every deployed HTML file (same NOT_DEPLOYED_DIRS exclusion as
check_indexability.py) for a number immediately followed by "African
countries" / "countries" / "African markets" / "African Countries" /
"currencies", in both plain-text and split-across-elements form (e.g.
`<div>23</div>...<div>countries</div>`), and flags any that doesn't match
the current true count.

A stale count where the surrounding sentence also implies universal
licensed/bookmaker coverage ("licensed bookmakers in all N...", "available
in all N...") is flagged as CRITICAL and requires a human to reword the
sentence, not just swap the number — see CLAUDE.md's 2026-08-14 entry on
why a blind number swap made some claims newly false for the 6 countries
with zero bookmaker listings. Everything else is a safe number swap,
auto-fixed with --fix.

Blog posts (blog/<slug>/index.html) are historical/dated editorial content,
not live site-state copy, and are intentionally excluded — same policy as
the original manual sweep.

Usage:
    python3 scripts/check_country_count.py            # report only
    python3 scripts/check_country_count.py --fix      # auto-fix safe swaps

Exit codes:
    0 — no CRITICAL issues (or --fix resolved everything fixable)
    1 — one or more CRITICAL issues remain
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from site_stats import total_country_count  # noqa: E402

CRITICAL = "CRITICAL"
WARN = "WARN"

NOT_DEPLOYED_DIRS = {
    "agents", "scripts", "supabase", "firecrawl", "geo-content-writer",
    "node_modules", ".git", ".github", ".venv", ".vscode",
    "__pycache__", ".firecrawl", ".claude",
}

# Number immediately followed by one of these phrases, plain-text form.
_INLINE_RE = re.compile(
    r'\b(\d+)\s*(African countries|African Countries|African markets|'
    r'African Markets|African betting markets|African Betting Markets|'
    r'countries covered|Countries Covered|local currencies|Countries)\b'
)

# Number and label split across two HTML elements, e.g.
# <div class="stat-n">23</div><div class="stat-l">African countries</div>
_SPLIT_RE = re.compile(
    r'>(\d+)</(?:div|span)>\s*<[^>]+>\s*(African countries|countries covered|'
    r'local currencies|African markets|countries|currencies)\b',
    re.IGNORECASE,
)

# Sentence-level risk phrases: swapping the number alone isn't safe here,
# the claim needs a human to reword it (see module docstring).
_OVERCLAIM_RE = re.compile(
    r'licensed (bookmakers|operators)? ?(in|across) all|available in all',
    re.IGNORECASE,
)


def find_html_files():
    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if rel.parts and rel.parts[0] in NOT_DEPLOYED_DIRS:
            continue
        if len(rel.parts) >= 2 and rel.parts[0] == "blog":
            continue  # historical editorial content, not live site-state copy
        yield path


def check_file(path: Path, true_total: int, fix: bool):
    text = path.read_text(encoding="utf-8")
    orig = text
    issues = []

    for pattern in (_INLINE_RE, _SPLIT_RE):
        for m in pattern.finditer(orig):
            num = int(m.group(1))
            if num == true_total:
                continue
            # Tight window deliberately — HTML is dense with meta tags, and a
            # wider window pulls in an unrelated "SifuFinds" from a nearby
            # attribute (e.g. og:site_name) rather than the same sentence.
            start = max(0, m.start() - 50)
            context = orig[start:m.end()]
            # Only flag this as SifuFinds' own site-wide total if "SifuFinds"
            # actually appears in the same sentence — countless pages
            # legitimately state a DIFFERENT, unrelated "N African countries"
            # fact (M-Pesa's own footprint, a specific bookmaker's own market
            # count, etc.) and those must never be touched by this guard.
            if "sifufinds" not in context.lower():
                continue
            level = CRITICAL if _OVERCLAIM_RE.search(context) else WARN
            issues.append((level, num, m.group(0), context.strip()))

    if not issues:
        return issues

    if fix:
        for level, num, matched, _ in issues:
            if level == CRITICAL:
                continue  # needs human rewording, do not blind-swap
            text = text.replace(str(num), str(true_total), 1) if matched.startswith(str(num)) else text
            # Split-element form: replace just the number between the tags
            text = re.sub(
                rf'>{num}</(div|span)>(\s*<[^>]+>\s*(?:African countries|countries covered|local currencies|African markets|countries|currencies))',
                rf'>{true_total}</\1\2',
                text,
                count=1,
                flags=re.IGNORECASE,
            )
        if text != orig:
            path.write_text(text, encoding="utf-8")

    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args()

    true_total = total_country_count()
    print("=" * 70)
    print("SifuFinds country-count guard")
    print(f"Current true total: {true_total} countries (from COUNTRY_DATA)")
    print("=" * 70)

    critical_count = 0
    warn_count = 0

    for path in find_html_files():
        issues = check_file(path, true_total, args.fix)
        for level, num, matched, context in issues:
            rel = path.relative_to(ROOT)
            tag = "🔴 CRITICAL" if level == CRITICAL else "🟡 WARN"
            print(f"{tag}  {rel}: found '{num}' (expected {true_total}) — {matched!r}")
            if level == CRITICAL:
                critical_count += 1
                print(f"           context needs a reword, not just a number swap: ...{context}...")
            else:
                warn_count += 1

    print("=" * 70)
    if args.fix:
        print(f"Summary: {warn_count} safe swap(s) applied, {critical_count} need manual review")
    else:
        print(f"Summary: {warn_count} safe swap(s) pending, {critical_count} CRITICAL (need manual review)")
    print("=" * 70)

    if critical_count:
        print("❌ CRITICAL issues found — resolve manually, --fix will not touch these")
        return 1
    if warn_count and not args.fix:
        print("⚠️  Stale counts found — run with --fix to auto-correct")
        return 1
    print("✅ No stale country-count copy found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
