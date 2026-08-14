#!/usr/bin/env python3
"""Guard against anything that would stop Google (or other search engines) from
crawling and indexing sifufinds.com.

This exists because a single bad line — a stray `noindex`, a `Disallow: /`,
or a schema.org Event missing required fields — can silently de-list the
whole site or trigger Search Console errors (see the 2026-07-05 GSC "Events
structured data" incident fixed by hand; this script is the regression guard
so that class of bug is caught automatically going forward).

Checks:
  1. robots.txt has no catastrophic `Disallow: /` for `*` or Googlebot groups
  2. No unexpected `noindex` meta / X-Robots-Tag on pages that must stay indexable
  3. Every schema.org Event/SportsEvent (etc.) object has real `location` + `startDate`
     — objects missing them get downgraded to `Thing` with --fix (matches the
     manual fix applied on 2026-07-05)
  4. Sitemap URLs aren't accidentally covered by a robots.txt Disallow rule
  5. (--live) robots.txt and the homepage are actually reachable and don't
     block Googlebot in production

Usage:
    python3 scripts/check_indexability.py            # report only
    python3 scripts/check_indexability.py --fix      # auto-fix safe issues
    python3 scripts/check_indexability.py --live     # also probe the live site
    python3 scripts/check_indexability.py --report   # write indexability-report.json

Exit codes:
    0 — no CRITICAL issues
    1 — one or more CRITICAL issues (deploy should be blocked)
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://sifufinds.com"

CRITICAL = "CRITICAL"
WARN = "WARN"

# Directories never deployed to the live site (mirrors EXCLUDE_DIRS in
# .github/workflows/deploy_hostinger.yml) — not part of the public, indexable site.
NOT_DEPLOYED_DIRS = {
    "agents", "scripts", "supabase", "firecrawl", "geo-content-writer",
    "node_modules", ".git", ".github", ".venv", ".vscode",
    "__pycache__", ".firecrawl", ".claude",
}

# Pages that are intentionally noindex — do not "fix" these.
# The 23 legacy countries/<slug>/index.html entries are redirect stubs left behind
# by the 2026-08-09 rename to best-betting-in-<slug>/ (see
# gen_best_betting_pages.py + gen_country_redirect_stubs.py) — the real 301
# lives in .htaccess, these are noindex defense-in-depth only.
_RENAMED_COUNTRY_SLUGS = [
    "nigeria", "kenya", "ghana", "south-africa", "tanzania", "uganda",
    "zambia", "ethiopia", "ivory-coast", "cameroon", "senegal", "rwanda",
    "zimbabwe", "malawi", "mozambique", "angola", "dr-congo", "botswana",
    "namibia", "egypt", "morocco", "sierra-leone", "liberia",
]
INTENTIONAL_NOINDEX_FILES = {"404.html", "analytics.html"} | {
    f"countries/{slug}/index.html" for slug in _RENAMED_COUNTRY_SLUGS
}

EVENT_TYPES = {
    "Event", "SportsEvent", "MusicEvent", "BusinessEvent", "Festival",
    "SocialEvent", "TheaterEvent", "ScreeningEvent", "ExhibitionEvent",
}

issues: list[dict] = []


def issue(severity: str, check: str, page: str, detail: str) -> None:
    issues.append({"severity": severity, "check": check, "page": page, "detail": detail})


def _noindex_exclusions() -> set[str]:
    """Slugs/paths that are allowed to carry noindex."""
    excluded = set(INTENTIONAL_NOINDEX_FILES)
    posts_path = ROOT / "blog" / "posts.json"
    if posts_path.exists():
        try:
            data = json.loads(posts_path.read_text())
            posts = data["posts"] if isinstance(data, dict) else data
            for p in posts:
                if p.get("noindex") and p.get("slug"):
                    excluded.add(f"blog/{p['slug']}/index.html")
        except Exception:
            pass
    return excluded


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
                fpath = Path(dirpath) / fname
                yield fpath


# ── 1. robots.txt catastrophic block check ────────────────────────────────────

def check_robots_txt(fix: bool) -> None:
    print("\n── robots.txt ──")
    path = ROOT / "robots.txt"
    if not path.exists():
        issue(CRITICAL, "robots_missing", "robots.txt", "robots.txt does not exist — site may be fully blocked or unrestricted by accident")
        return

    content = path.read_text()
    lines = content.splitlines()

    current_agents: list[str] = []
    blocking_groups: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = re.match(r"User-agent:\s*(.+)", stripped, re.IGNORECASE)
        if m:
            agent = m.group(1).strip()
            # A blank line normally resets the group in strict robots.txt parsing,
            # but treating each User-agent line as starting a fresh group is safer here.
            current_agents = [agent]
            continue
        m = re.match(r"Disallow:\s*(.*)", stripped, re.IGNORECASE)
        if m:
            value = m.group(1).strip()
            if value == "/" and any(a in ("*", "Googlebot") for a in current_agents):
                blocking_groups.extend(current_agents)

    if blocking_groups:
        issue(CRITICAL, "robots_disallow_all", "robots.txt",
              f"Disallow: / found for agent(s) {sorted(set(blocking_groups))} — this blocks Google from crawling the entire site")
        if fix:
            # Remove any bare "Disallow: /" line that isn't scoped to a known
            # intentionally-blocked bot (MJ12bot/PetalBot use it deliberately).
            new_lines = []
            current_agents = []
            for line in lines:
                stripped = line.strip()
                m = re.match(r"User-agent:\s*(.+)", stripped, re.IGNORECASE)
                if m:
                    current_agents = [m.group(1).strip()]
                if re.match(r"Disallow:\s*/\s*$", stripped, re.IGNORECASE) and any(
                    a in ("*", "Googlebot") for a in current_agents
                ):
                    print(f"  FIX: removing catastrophic 'Disallow: /' for {current_agents}")
                    continue
                new_lines.append(line)
            path.write_text("\n".join(new_lines) + "\n")
    else:
        print("  OK  no 'Disallow: /' for * or Googlebot")

    if "Sitemap:" not in content:
        issue(WARN, "robots_no_sitemap", "robots.txt", "No Sitemap: directive found")
    else:
        print("  OK  Sitemap directive present")

    return  # noqa: parsed content also used by check_sitemap_vs_robots below


def _parse_disallowed_prefixes(content: str) -> list[str]:
    """Disallow prefixes that apply to '*' or Googlebot (the ones that matter for indexing)."""
    prefixes: list[str] = []
    current_agents: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        m = re.match(r"User-agent:\s*(.+)", stripped, re.IGNORECASE)
        if m:
            current_agents = [m.group(1).strip()]
            continue
        m = re.match(r"Disallow:\s*(.+)", stripped, re.IGNORECASE)
        if m and any(a in ("*", "Googlebot") for a in current_agents):
            value = m.group(1).strip()
            if value and value != "/":
                prefixes.append(value)
    return prefixes


# ── 2. noindex regression check ───────────────────────────────────────────────

def check_noindex(fix: bool) -> None:
    print("\n── noindex / X-Robots-Tag ──")
    excluded = _noindex_exclusions()
    found = 0

    for fpath in _iter_public_html():
        rel = str(fpath.relative_to(ROOT))
        if rel in excluded or fpath.name in INTENTIONAL_NOINDEX_FILES:
            continue
        try:
            html = fpath.read_text(errors="ignore")
        except OSError:
            continue
        m = re.search(r'<meta\s+name="robots"\s+content="([^"]*noindex[^"]*)"', html, re.IGNORECASE)
        if m:
            found += 1
            issue(CRITICAL, "unexpected_noindex", rel,
                  f'Unexpected noindex meta robots tag: content="{m.group(1)}"')
            if fix:
                new_html = re.sub(
                    r'<meta\s+name="robots"\s+content="[^"]*"',
                    '<meta name="robots" content="index, follow"',
                    html, count=1, flags=re.IGNORECASE,
                )
                fpath.write_text(new_html)
                print(f"  FIX: removed noindex from {rel}")

    if not found:
        print("  OK  no unexpected noindex tags on public pages")

    # X-Robots-Tag noindex header set sitewide via .htaccess
    htaccess = ROOT / ".htaccess"
    if htaccess.exists():
        content = htaccess.read_text()
        if re.search(r"X-Robots-Tag[^\n]*noindex", content, re.IGNORECASE):
            issue(CRITICAL, "x_robots_tag_noindex", ".htaccess",
                  "X-Robots-Tag header sets noindex — this can de-index the entire site")
        else:
            print("  OK  no sitewide X-Robots-Tag: noindex in .htaccess")


# ── 3. structured data Event regression guard ─────────────────────────────────

def check_event_schema(fix: bool) -> None:
    print("\n── Structured data: Event required fields ──")
    found = 0

    for fpath in _iter_public_html():
        rel = str(fpath.relative_to(ROOT))
        try:
            html = fpath.read_text(errors="ignore")
        except OSError:
            continue
        if not any(f'"@type": "{t}"' in html or f'"@type":"{t}"' in html for t in EVENT_TYPES):
            continue

        changed = False
        for m in re.finditer(r'\{"@type":\s*"(' + "|".join(EVENT_TYPES) + r')"[^{}]*\}', html):
            obj_text = m.group(0)
            has_location = '"location"' in obj_text
            has_start = '"startDate"' in obj_text
            if has_location and has_start:
                continue
            found += 1
            issue(CRITICAL, "event_missing_required_fields", rel,
                  f'{m.group(1)} object missing {"location" if not has_location else ""}'
                  f'{"+" if not has_location and not has_start else ""}'
                  f'{"startDate" if not has_start else ""}: {obj_text[:120]}')
            if fix:
                downgraded = re.sub(r'"@type":\s*"(' + "|".join(EVENT_TYPES) + r')"', '"@type": "Thing"', obj_text)
                # Thing doesn't define "sport" — strip it to keep the object schema-clean.
                downgraded = re.sub(r',\s*"sport":\s*"[^"]*"', '', downgraded)
                html = html.replace(obj_text, downgraded, 1)
                changed = True
                print(f"  FIX: downgraded unqualified {m.group(1)} → Thing in {rel}")

        if changed:
            fpath.write_text(html)

    if not found:
        print("  OK  every Event/SportsEvent object has location + startDate")


# ── 4. sitemap vs robots.txt cross-check ──────────────────────────────────────

def check_sitemap_vs_robots() -> None:
    print("\n── Sitemap vs robots.txt ──")
    robots_path = ROOT / "robots.txt"
    if not robots_path.exists():
        return
    disallowed_prefixes = _parse_disallowed_prefixes(robots_path.read_text())
    if not disallowed_prefixes:
        print("  OK  no path-specific Disallow rules to cross-check")
        return

    blocked_urls: list[tuple[str, str]] = []
    for sitemap_file in ROOT.glob("sitemap*.xml"):
        content = sitemap_file.read_text(errors="ignore")
        for loc in re.findall(r"<loc>([^<]+)</loc>", content):
            path = loc.replace(SITE_URL, "")
            for prefix in disallowed_prefixes:
                if path.startswith(prefix):
                    blocked_urls.append((loc, sitemap_file.name))

    if blocked_urls:
        for loc, sm in blocked_urls[:10]:
            issue(CRITICAL, "sitemap_url_disallowed", sm,
                  f"{loc} is listed in the sitemap but blocked by robots.txt")
        print(f"  FAIL {len(blocked_urls)} sitemap URL(s) blocked by robots.txt Disallow rules")
    else:
        print("  OK  no sitemap URLs are blocked by robots.txt")


# ── 5. live probe (optional, network required) ────────────────────────────────

def check_live() -> None:
    print("\n── Live probe (production) ──")
    try:
        req = urllib.request.Request(f"{SITE_URL}/robots.txt", headers={"User-Agent": "Googlebot"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            body = resp.read().decode(errors="ignore")
        if status != 200:
            issue(CRITICAL, "live_robots_unreachable", "robots.txt", f"Live robots.txt returned HTTP {status}")
        elif re.search(r"User-agent:\s*\*\s*\n\s*Disallow:\s*/\s*$", body, re.MULTILINE):
            issue(CRITICAL, "live_robots_blocks_all", "robots.txt", "Live robots.txt disallows all crawling")
        else:
            print(f"  OK  live robots.txt reachable ({status})")
    except Exception as e:
        print(f"  WARN could not reach live robots.txt: {e}")

    try:
        req = urllib.request.Request(f"{SITE_URL}/", headers={"User-Agent": "Googlebot"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            xrt = resp.headers.get("X-Robots-Tag", "")
        if status != 200:
            issue(CRITICAL, "live_home_unreachable", "/", f"Live homepage returned HTTP {status} to Googlebot UA")
        elif "noindex" in xrt.lower():
            issue(CRITICAL, "live_home_noindex_header", "/", f"Live homepage sends X-Robots-Tag: {xrt}")
        else:
            print(f"  OK  live homepage reachable to Googlebot UA ({status})")
    except Exception as e:
        print(f"  WARN could not reach live homepage: {e}")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()

    print("=" * 70)
    print("SifuFinds indexability guard — is anything stopping Google?")
    print("=" * 70)

    check_robots_txt(args.fix)
    check_noindex(args.fix)
    check_event_schema(args.fix)
    check_sitemap_vs_robots()
    if args.live:
        check_live()

    critical = [i for i in issues if i["severity"] == CRITICAL]
    warnings = [i for i in issues if i["severity"] == WARN]

    print("\n" + "=" * 70)
    print(f"Summary: {len(critical)} critical | {len(warnings)} warnings")
    if critical:
        print("\nCRITICAL issues (these can stop Google from indexing the site):")
        for i in critical:
            print(f"  ✗ [{i['check']}] {i['page']}: {i['detail']}")
    if warnings:
        print("\nWarnings:")
        for i in warnings:
            print(f"  ⚠ [{i['check']}] {i['page']}: {i['detail']}")
    print("=" * 70)

    if args.report:
        report_path = ROOT / "indexability-report.json"
        report_path.write_text(json.dumps({
            "critical": len(critical), "warnings": len(warnings), "issues": issues,
        }, indent=2))
        print(f"Report saved to {report_path.name}")

    if critical and not args.fix:
        print("\n❌ Fix these before deploying, or re-run with --fix to auto-heal safe issues.")
        return 1
    if critical and args.fix:
        # Re-run detection once more after fixes to confirm they actually resolved.
        issues.clear()
        check_robots_txt(False)
        check_noindex(False)
        check_event_schema(False)
        check_sitemap_vs_robots()
        still_critical = [i for i in issues if i["severity"] == CRITICAL]
        if still_critical:
            print(f"\n❌ {len(still_critical)} critical issue(s) could not be auto-fixed — manual review needed")
            for i in still_critical:
                print(f"  ✗ [{i['check']}] {i['page']}: {i['detail']}")
            return 1
        print("\n✅ All critical issues auto-fixed")
        return 0

    print("\n✅ Nothing is stopping Google from crawling/indexing the site")
    return 0


if __name__ == "__main__":
    sys.exit(main())
