#!/usr/bin/env python3
"""GEO (Generative Engine Optimization) health guard for sifufinds.com.

Complements scripts/seo_check.py and scripts/check_indexability.py, which
cover classic SEO. This script guards the AI-search-specific signals that a
2026-07-26 GEO audit found broken in production with no automated check
behind them:

  1. robots.txt — every named bot group (AI crawlers, Bing, social unfurl
     bots, SEO audit tools, etc.) must carry the same internal-directory
     Disallow lines as the Googlebot group. A specific User-agent match
     overrides the wildcard `*` group entirely per robots.txt precedence,
     so a bare "Allow: /" silently exposes /agents/, /.github/, /.venv/,
     /firecrawl/, /geo-content-writer/ to that crawler.
  2. llms.txt — must exist, must not contain leftover edit residue
     (duplicate "Last Updated" blocks, stray "#" comment lines outside the
     Markdown structure), and must not reference a licensing domain that
     doesn't resolve.
  3. FAQ answers — a literal "A:"/"A." label leaking into visible text or
     FAQPage JSON-LD reads as broken to both readers and AI citation
     engines. gen_blog_post_pages.py now strips this at generation time;
     this is the regression guard for future content that reintroduces it.
  4. sitemap-blog.xml vs blog/posts.json — the blog sitemap must not
     balloon past what posts.json actually tracks (each post contributes
     at most 1 + len(locales) URLs). A 2026-07-26 audit found 305 orphaned
     blog directories being resubmitted to Google via a filesystem-walking
     sitemap generator; gen_sitemap.py now scopes to posts.json, this is
     the regression guard.

Usage:
  python3 scripts/geo_check.py              # audit only
  python3 scripts/geo_check.py --fix        # auto-fix safe issues (robots.txt, llms.txt)
  python3 scripts/geo_check.py --report     # write report to geo-report.json

Exit codes:
  0 — no CRITICAL issues
  1 — one or more CRITICAL issues
"""

import argparse
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
ROBOTS_PATH = BASE / 'robots.txt'
LLMS_PATH = BASE / 'llms.txt'
POSTS_JSON = BASE / 'blog' / 'posts.json'
SITEMAP_BLOG = BASE / 'sitemap-blog.xml'
BLOG_DIR = BASE / 'blog'
LOCALES = ['fr', 'de', 'es', 'pt', 'sw']

CRITICAL, HIGH, MEDIUM, INFO = 'CRITICAL', 'HIGH', 'MEDIUM', 'INFO'
issues = []


def issue(severity, check, page, detail):
    issues.append({'severity': severity, 'check': check, 'page': page, 'detail': detail})


INTERNAL_DISALLOW = [
    'Disallow: /agents/',
    'Disallow: /.github/',
    'Disallow: /.venv/',
    'Disallow: /firecrawl/',
    'Disallow: /geo-content-writer/',
]

# Groups intentionally exempt: the wildcard/Googlebot family already carries
# its own explicit Disallow set (some omit /firecrawl/ deliberately so
# Googlebot can read the noindex directive there), and "known bad bots" are
# fully blocked (Disallow: /) rather than scoped.
EXEMPT_UAS = {
    '*', 'Googlebot', 'Googlebot-Image', 'Googlebot-Video', 'Googlebot-News',
    'AdsBot-Google', 'AdsBot-Google-Mobile', 'Google-Extended',
    'Google-InspectionTool', 'MJ12bot', 'PetalBot',
}


def check_robots(fix: bool):
    if not ROBOTS_PATH.exists():
        issue(CRITICAL, 'robots_missing', 'robots.txt', 'robots.txt does not exist')
        return

    lines = ROBOTS_PATH.read_text(encoding='utf-8').split('\n')
    out = []
    i = 0
    patched = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = re.match(r'User-agent:\s*(\S+)', line)
        if m and m.group(1) not in EXEMPT_UAS:
            ua = m.group(1)
            if i + 1 < len(lines) and lines[i + 1].strip() == 'Allow: /':
                out.append(lines[i + 1])
                has_disallow = (i + 2 < len(lines)
                                 and lines[i + 2].strip().startswith('Disallow:'))
                if not has_disallow:
                    if fix:
                        out.extend(INTERNAL_DISALLOW)
                        patched += 1
                    else:
                        issue(HIGH, 'robots_ai_bot_exposed', 'robots.txt',
                              f"User-agent '{ua}' has bare 'Allow: /' with no internal-"
                              f"directory Disallow lines — per robots.txt precedence this "
                              f"exposes /agents/, /.github/, /.venv/ etc. to this crawler")
                i += 2
                continue
        i += 1

    if fix and patched:
        ROBOTS_PATH.write_text('\n'.join(out), encoding='utf-8')
        print(f"  ✅ FIX: patched {patched} robots.txt group(s) with missing internal Disallow lines")


def check_llms_txt(fix: bool):
    if not LLMS_PATH.exists():
        issue(CRITICAL, 'llms_txt_missing', 'llms.txt', 'llms.txt does not exist')
        return

    text = LLMS_PATH.read_text(encoding='utf-8')
    changed = False

    # Leftover edit residue: a stray "#" comment line outside normal Markdown
    # structure, most often trailing "# Previous ... was here" artifacts.
    stray_comments = re.findall(r'^#[^\n]*was here[^\n]*$', text, re.MULTILINE)
    if stray_comments:
        if fix:
            for sc in stray_comments:
                text = text.replace(f'\n{sc}', '').replace(sc, '')
            changed = True
        else:
            issue(HIGH, 'llms_txt_residue', 'llms.txt',
                  f'{len(stray_comments)} stray edit-residue comment line(s) found')

    last_updated_blocks = re.findall(r'^## Last Updated\s*$', text, re.MULTILINE)
    if len(last_updated_blocks) > 1:
        issue(HIGH, 'llms_txt_duplicate_section', 'llms.txt',
              f'{len(last_updated_blocks)} "## Last Updated" sections found — should be exactly 1')

    license_domains = re.findall(r'License:.*?(https?://[^\s\)]+)', text)
    for domain in license_domains:
        issue(MEDIUM, 'llms_txt_unverified_license_link', 'llms.txt',
              f'llms.txt references a license URL ({domain}) — verify it resolves '
              f'before relying on it; a dead license link is worse than no claim')

    if changed:
        LLMS_PATH.write_text(text, encoding='utf-8')
        print("  ✅ FIX: stripped stray edit-residue line(s) from llms.txt")


def check_faq_answer_labels():
    """Regression guard: a leaked 'A:'/'A.' label in FAQ answers (fixed
    2026-07-26 in gen_blog_post_pages.py's extract_faq_schema + body_md
    preprocessing) reads as broken to citation engines."""
    if not BLOG_DIR.exists():
        return
    pattern = re.compile(r'"acceptedAnswer":\s*\{"@type":\s*"Answer",\s*"text":\s*"A[:.]\s')
    for post_dir in BLOG_DIR.iterdir():
        if not post_dir.is_dir():
            continue
        index = post_dir / 'index.html'
        if not index.exists():
            continue
        try:
            html = index.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        if pattern.search(html):
            issue(HIGH, 'faq_answer_label_leak', str(post_dir.relative_to(BASE)),
                  'FAQPage JSON-LD acceptedAnswer.text starts with a literal "A:" label')


def check_sitemap_blog_scope():
    """Regression guard for the 2026-07-26 orphaned-directory sitemap bloat
    (305 stale blog/ dirs were being resubmitted to Google)."""
    if not (SITEMAP_BLOG.exists() and POSTS_JSON.exists()):
        return
    with open(POSTS_JSON, encoding='utf-8') as f:
        data = json.load(f)
    posts = data.get('posts', [])

    tracked_slugs = set()
    for p in posts:
        slug = p.get('slug')
        if slug:
            tracked_slugs.add(slug)
            tracked_slugs.update(f'{slug}-{lg}' for lg in LOCALES)

    sitemap_text = SITEMAP_BLOG.read_text(encoding='utf-8')
    urls = re.findall(r'<loc>https://sifufinds\.com/blog/([^/<]+)/</loc>', sitemap_text)
    orphaned = [u for u in urls if u not in tracked_slugs]
    if orphaned:
        issue(HIGH, 'sitemap_orphaned_blog_urls', 'sitemap-blog.xml',
              f'{len(orphaned)} URL(s) in sitemap-blog.xml have no matching entry in '
              f'blog/posts.json — re-run gen_sitemap.py (should self-heal; if this '
              f'persists, gen_sitemap.py\'s posts.json scoping has regressed)')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fix', action='store_true')
    parser.add_argument('--report', action='store_true')
    args = parser.parse_args()

    print("=" * 70)
    print("SifuFinds GEO health check — AI-search readiness signals")
    print("=" * 70)

    check_robots(args.fix)
    check_llms_txt(args.fix)
    check_faq_answer_labels()
    check_sitemap_blog_scope()

    by_severity = {CRITICAL: [], HIGH: [], MEDIUM: [], INFO: []}
    for iss in issues:
        by_severity[iss['severity']].append(iss)

    print()
    for sev in [CRITICAL, HIGH, MEDIUM, INFO]:
        if not by_severity[sev]:
            continue
        print(f"[{sev}] {len(by_severity[sev])} issue(s)")
        for iss in by_severity[sev]:
            print(f"  • {iss['page']}  {iss['check']}  {iss['detail']}")
        print()

    print("=" * 70)
    print(f"Summary: {len(by_severity[CRITICAL])} critical | "
          f"{len(by_severity[HIGH])} high | {len(by_severity[MEDIUM])} medium | "
          f"{len(by_severity[INFO])} info")
    print("=" * 70)

    if args.report:
        with open(BASE / 'geo-report.json', 'w', encoding='utf-8') as f:
            json.dump({'issues': issues}, f, indent=2)

    if not issues:
        print("\n✅ No GEO health issues found")
    elif not by_severity[CRITICAL]:
        print("\n✅ No CRITICAL GEO issues — see HIGH/MEDIUM items above")

    sys.exit(1 if by_severity[CRITICAL] else 0)


if __name__ == '__main__':
    main()
