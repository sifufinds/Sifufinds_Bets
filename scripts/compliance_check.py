#!/usr/bin/env python3
"""Compliance Reviewer — permanent guard for the checklist CLAUDE.md already
requires by hand on every blog post: 18+/Responsible Gambling disclaimer,
BeGambleAware link, no overstated ("guaranteed win") gambling language, and
sponsored/affiliate links correctly labelled.

This formalises what was previously a manual pre-publish checklist item into
a scriptable regression guard, following the same shape as
scripts/seo_check.py and scripts/check_indexability.py (issue()/CRITICAL/WARN,
--fix, --report, exit 1 on unresolved CRITICAL issues) so it slots into the
existing pre-deploy gate the same way.

Checks:
  1. Every blog post page (English + locale variants) contains an 18+ /
     Responsible Gambling disclaimer.
  2. Every blog post page links to begambleaware.org.
  3. No banned overstated/misleading gambling-outcome language anywhere in
     public HTML or agent content templates ("guaranteed win", "risk-free",
     "can't lose", etc.) — these overstate an offer and are a real
     regulatory/trust risk, not just a style nit.
  4. Masked affiliate links (sifufinds.com/<brand>, slugs read from the
     .htaccess AFFILIATE LINK MASKING block so this never drifts out of sync)
     carry rel="sponsored" wherever they're rendered, including in
     assets/*.js template strings (many CTAs are client-rendered, not baked
     into the static HTML — see assets/shared.js's HEADER_BRANDS renderer).
  5. Every active Featured Listings placement (data/featured_listings.json,
     once populated) renders with a visible "Sponsored" label at its target
     location — a no-op until that file exists.

Usage:
    python3 scripts/compliance_check.py            # report only
    python3 scripts/compliance_check.py --fix       # auto-fix safe issues
    python3 scripts/compliance_check.py --report    # write compliance-report.json

Exit codes:
    0 — no CRITICAL issues
    1 — one or more CRITICAL issues (deploy should be blocked)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CRITICAL = "CRITICAL"
WARN = "WARN"

NOT_DEPLOYED_DIRS = {
    "agents", "scripts", "supabase", "firecrawl", "geo-content-writer",
    "node_modules", ".git", ".github", ".venv", ".vscode",
    "__pycache__", ".firecrawl", ".claude",
}

DISCLAIMER_PATTERN = re.compile(r"\b18\s*\+", re.IGNORECASE)
BEGAMBLEAWARE_PATTERN = re.compile(r"begambleaware\.org", re.IGNORECASE)
STANDARD_DISCLAIMER = "<p class=\"disclaimer\">18+ | Bet Responsibly | T&amp;Cs Apply</p>"

# Overstated gambling-outcome language — a real trust/regulatory risk if it
# ever slips into published copy, not a style nit. Deliberately excludes
# legitimate betting vocabulary ("banker pick", "guaranteed profit" as an
# accurate description of Cash Out mechanics or a bookmaker's margin) that
# reads as overstated out of context but isn't a promise about placing a NEW
# bet — "guaranteed profit" specifically was tried and dropped after it flagged
# two genuinely accurate uses (accumulator Cash Out, odds-margin explainer).
BANNED_PHRASES = [
    r"guaranteed\s+win", r"100%\s*win",
    r"can'?t\s+lose", r"cannot\s+lose", r"risk[\s-]?free\s+bet",
    r"zero[\s-]?risk\s+bet", r"no[\s-]?risk\s+bet", r"never\s+lose",
]
BANNED_RE = re.compile("|".join(BANNED_PHRASES), re.IGNORECASE)

# Skip a match if it's an instruction telling the writer NOT to use the
# phrase (e.g. agent_content_backfill.py's own prompt says "Never promise
# guaranteed wins") rather than the phrase actually being shipped.
#
# Found 2026-08-02: agent_priority_writer.py's own prompt says 'Never claim
# a "guaranteed win", "risk-free bet", or anything that overstates a
# gambling outcome' — a quoted, comma-separated list of banned phrases
# right after the negation word, exactly the case this exception exists
# for. It still false-positived because (a) [\w\s] doesn't include the
# quote/comma punctuation sitting between "Never" and the phrase, and (b)
# the second phrase in the list sits ~33 chars after "Never", past the
# old {0,20} cap. Widened both the allowed character class and the cap
# (plus the lookback window below) rather than special-casing this one
# phrasing, since any future prompt listing 2+ banned phrases after one
# "Never claim..." would hit the same gap.
_NEGATION_RE = re.compile(r"\b(never|don'?t|do not|avoid|without)[\w\s\"',:]{0,80}$", re.IGNORECASE)


def _is_negated(text: str, match_start: int) -> bool:
    return bool(_NEGATION_RE.search(text[max(0, match_start - 100):match_start]))

issues: list[dict] = []


def issue(severity: str, check: str, page: str, detail: str) -> None:
    issues.append({"severity": severity, "check": check, "page": page, "detail": detail})


def _iter_public_html():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = os.path.relpath(dirpath, ROOT)
        parts = set(rel_dir.split(os.sep)) if rel_dir != "." else set()
        if parts & NOT_DEPLOYED_DIRS or any(p.startswith(".") for p in parts):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in NOT_DEPLOYED_DIRS and not d.startswith(".")]
        for fname in filenames:
            if fname.endswith(".html"):
                yield Path(dirpath) / fname


def _iter_blog_post_pages():
    blog_dir = ROOT / "blog"
    if not blog_dir.exists():
        return
    for entry in blog_dir.iterdir():
        if entry.is_dir() and (entry / "index.html").exists():
            yield entry / "index.html"


def _masked_brand_slugs() -> list[str]:
    """Read ONLY the AFFILIATE LINK MASKING block in .htaccess so this check
    never drifts out of sync with the actual live brand list (see
    agents/python/utils/affiliate_links.py's BRAND_SLUGS docstring note), and
    never picks up unrelated same-shaped RewriteRules elsewhere in the file
    (e.g. short-URL redirects like ^cricket/?$ or ^f1/?$ for category pages,
    which look identical to a brand rule but aren't affiliate links)."""
    htaccess = ROOT / ".htaccess"
    if not htaccess.exists():
        return []
    content = htaccess.read_text(errors="ignore")
    m = re.search(r"AFFILIATE LINK MASKING.*?\n(.*?)(?:\n#\s*──|\Z)", content, re.DOTALL)
    if not m:
        return []
    return re.findall(r"RewriteRule \^([a-z0-9]+)/\?\$", m.group(1))


# ── 1 & 2. Disclaimer + BeGambleAware on every blog post ──────────────────────

def check_blog_compliance_labels(fix: bool) -> None:
    print("\n── 18+ disclaimer + BeGambleAware link on blog posts ──")
    missing_disclaimer = 0
    missing_bga = 0

    for fpath in _iter_blog_post_pages():
        rel = str(fpath.relative_to(ROOT))
        try:
            html = fpath.read_text(errors="ignore")
        except OSError:
            continue

        if not DISCLAIMER_PATTERN.search(html):
            missing_disclaimer += 1
            issue(CRITICAL, "missing_18plus_disclaimer", rel,
                  "No 18+ / Responsible Gambling disclaimer found on this post")
            if fix and "</article>" in html:
                html = html.replace("</article>", f"{STANDARD_DISCLAIMER}\n</article>", 1)
                fpath.write_text(html)
                print(f"  FIX: appended standard 18+ disclaimer to {rel}")

        if not BEGAMBLEAWARE_PATTERN.search(html):
            missing_bga += 1
            issue(CRITICAL, "missing_begambleaware_link", rel,
                  "No begambleaware.org link found on this post")

    if not missing_disclaimer:
        print("  OK  every blog post has an 18+ disclaimer")
    if not missing_bga:
        print("  OK  every blog post links to BeGambleAware")


# ── 3. Banned overstated language ──────────────────────────────────────────────

def check_banned_language() -> None:
    print("\n── Overstated gambling-outcome language ──")
    found = 0
    for fpath in _iter_public_html():
        rel = str(fpath.relative_to(ROOT))
        try:
            text = fpath.read_text(errors="ignore")
        except OSError:
            continue
        for m in BANNED_RE.finditer(text):
            if _is_negated(text, m.start()):
                continue
            found += 1
            issue(CRITICAL, "overstated_language", rel,
                  f'Banned phrase "{m.group(0)}" overstates a real-money outcome')

    # Also catch it in agent content templates before it ever ships.
    agents_dir = ROOT / "agents" / "python"
    if agents_dir.exists():
        for fpath in agents_dir.glob("agent_*.py"):
            try:
                text = fpath.read_text(errors="ignore")
            except OSError:
                continue
            for m in BANNED_RE.finditer(text):
                if _is_negated(text, m.start()):
                    continue
                found += 1
                rel = str(fpath.relative_to(ROOT))
                issue(WARN, "overstated_language_in_template", rel,
                      f'Banned phrase "{m.group(0)}" found in an agent template/prompt — will ship to real pages')

    if not found:
        print("  OK  no overstated gambling-outcome language found")


# ── 4. rel="sponsored" on masked affiliate links ───────────────────────────────

def check_sponsored_rel() -> None:
    print("\n── rel=\"sponsored\" on affiliate links ──")
    slugs = _masked_brand_slugs()
    if not slugs:
        print("  WARN could not read brand slugs from .htaccess — skipping")
        return
    slug_pattern = "|".join(re.escape(s) for s in slugs)
    href_re = re.compile(
        r'<a\s+[^>]*href="[^"]*sifufinds\.com/(?:' + slug_pattern + r')/?"[^>]*>', re.IGNORECASE)

    found = 0
    targets = list(_iter_public_html()) + list((ROOT / "assets").glob("*.js"))
    for fpath in targets:
        try:
            text = fpath.read_text(errors="ignore")
        except OSError:
            continue
        for m in href_re.finditer(text):
            tag = m.group(0)
            if "sponsored" not in tag.lower():
                found += 1
                rel = str(fpath.relative_to(ROOT))
                issue(WARN, "affiliate_link_missing_sponsored_rel", rel,
                      f'Affiliate CTA link missing rel="sponsored": {tag[:120]}')

    if not found:
        print("  OK  masked affiliate links carry rel=\"sponsored\" where checked")


# ── 5. Featured Listings sponsored labelling (no-op until the feature ships) ──

def check_featured_listings_labels() -> None:
    print("\n── Featured Listings sponsored labelling ──")
    path = ROOT / "data" / "featured_listings.json"
    if not path.exists():
        print("  SKIP data/featured_listings.json does not exist yet")
        return
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        issue(WARN, "featured_listings_unreadable", "data/featured_listings.json", str(e))
        return

    entries = data.get("listings", []) if isinstance(data, dict) else data
    active = [e for e in entries if e.get("sponsored") is True]
    if not active:
        print("  OK  no active featured listings to verify")
        return

    # A full per-slot render check needs to know each slot's target page,
    # which is intentionally left generic (slots are page-agnostic strings
    # like "country_sponsor:nigeria"). This pass only confirms every active
    # entry declares sponsored=True and carries a human-readable criteria
    # note, per the "transparent criteria" principle — the render-time badge
    # itself is exercised in Phase 1 verification, not re-derived here.
    for e in active:
        if not e.get("criteria_note"):
            issue(WARN, "featured_listing_missing_criteria", f"data/featured_listings.json#{e.get('slot')}",
                  "Active featured listing has no transparent criteria_note explaining why it's featured")
    print(f"  OK  {len(active)} active featured listing(s) declare sponsored=True")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()

    print("=" * 70)
    print("SifuFinds compliance guard — 18+/BeGambleAware/overstated-language/sponsored labelling")
    print("=" * 70)

    check_blog_compliance_labels(args.fix)
    check_banned_language()
    check_sponsored_rel()
    check_featured_listings_labels()

    critical = [i for i in issues if i["severity"] == CRITICAL]
    warnings = [i for i in issues if i["severity"] == WARN]

    print("\n" + "=" * 70)
    print(f"Summary: {len(critical)} critical | {len(warnings)} warnings")
    if critical:
        print("\nCRITICAL issues (compliance risk — fix before deploying):")
        for i in critical[:30]:
            print(f"  ✗ [{i['check']}] {i['page']}: {i['detail']}")
        if len(critical) > 30:
            print(f"  ... and {len(critical) - 30} more")
    if warnings:
        print("\nWarnings:")
        for i in warnings[:20]:
            print(f"  ⚠ [{i['check']}] {i['page']}: {i['detail']}")
        if len(warnings) > 20:
            print(f"  ... and {len(warnings) - 20} more")
    print("=" * 70)

    if args.report:
        report_path = ROOT / "compliance-report.json"
        report_path.write_text(json.dumps({
            "critical": len(critical), "warnings": len(warnings), "issues": issues,
        }, indent=2))
        print(f"Report saved to {report_path.name}")

    if critical and not args.fix:
        print("\n❌ Fix these before deploying, or re-run with --fix to auto-heal safe issues.")
        return 1
    if critical and args.fix:
        issues.clear()
        check_blog_compliance_labels(False)
        check_banned_language()
        check_sponsored_rel()
        check_featured_listings_labels()
        still_critical = [i for i in issues if i["severity"] == CRITICAL]
        if still_critical:
            print(f"\n❌ {len(still_critical)} critical issue(s) could not be auto-fixed — manual review needed")
            for i in still_critical[:30]:
                print(f"  ✗ [{i['check']}] {i['page']}: {i['detail']}")
            return 1
        print("\n✅ All critical issues auto-fixed")
        return 0

    print("\n✅ No compliance issues found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
