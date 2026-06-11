#!/usr/bin/env python3
"""Automated SEO audit for sifufinds.com static site.

Checks:
  - Blog posts: title length, meta description length, H1 presence,
    FAQPage schema when FAQ content exists, BreadcrumbList schema,
    noindex posts having correct canonical_override
  - Key pages: H1 presence, meta description, og:image, canonical
  - Duplicate detection: flags posts with high title-token overlap
    that don't have canonical_override set

Usage:
  python3 scripts/seo_check.py              # audit only
  python3 scripts/seo_check.py --fix        # auto-fix safe issues
  python3 scripts/seo_check.py --report     # write report to seo-report.json
"""

import os, re, json, sys, argparse
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
POSTS_JSON = BASE / 'blog' / 'posts.json'
BLOG_DIR = BASE / 'blog'

# ── Severity constants ────────────────────────────────────────────────────────
CRITICAL = 'CRITICAL'
HIGH = 'HIGH'
MEDIUM = 'MEDIUM'
INFO = 'INFO'

issues = []

def issue(severity, check, slug_or_page, detail):
    issues.append({'severity': severity, 'check': check, 'page': slug_or_page, 'detail': detail})

# ── Load posts ────────────────────────────────────────────────────────────────
with open(POSTS_JSON) as f:
    raw = json.load(f)
posts = raw['posts'] if isinstance(raw, dict) else raw

# ── 1. Title length (10–60 chars) ─────────────────────────────────────────────
for p in posts:
    t = p.get('title', '')
    if len(t) > 60:
        issue(HIGH, 'title_length', p['slug'], f"Title {len(t)} chars (max 60): {t[:70]!r}")
    elif len(t) < 10:
        issue(HIGH, 'title_length', p['slug'], f"Title too short ({len(t)} chars)")

# ── 2. Meta description length (50–155 chars) ────────────────────────────────
for p in posts:
    exc = p.get('excerpt', '')
    if len(exc) > 155:
        issue(HIGH, 'meta_desc_length', p['slug'], f"Excerpt {len(exc)} chars (max 155)")
    elif len(exc) < 50:
        issue(MEDIUM, 'meta_desc_length', p['slug'], f"Excerpt too short ({len(exc)} chars)")

# ── 3. Check generated HTML files ─────────────────────────────────────────────
def read_html(slug):
    path = BLOG_DIR / slug / 'index.html'
    if path.exists():
        return path.read_text(errors='replace')
    return ''

def has_faq_content(body):
    """True if post body contains FAQ-like question patterns."""
    return bool(re.search(
        r'(\*\*[^*\n]+\?\*\*|^#{1,3}.*FAQ|^Q:|^Q\d\.|^###\s+\w.*\?)',
        body, re.MULTILINE | re.IGNORECASE
    ))

for p in posts:
    slug = p['slug']
    noindex = p.get('noindex', False)
    html = read_html(slug)
    if not html:
        issue(HIGH, 'missing_html', slug, 'No generated HTML file found — run gen_blog_post_pages.py')
        continue

    # 3a. H1 presence
    if '<h1' not in html.lower():
        issue(CRITICAL, 'missing_h1', slug, 'No H1 tag found in generated page')

    # 3b. FAQPage schema when FAQ content exists
    if not noindex and has_faq_content(p.get('body', '')):
        if '"FAQPage"' not in html:
            issue(MEDIUM, 'missing_faqpage_schema', slug, 'Post has FAQ content but no FAQPage JSON-LD')

    # 3c. BreadcrumbList schema
    if not noindex and '"BreadcrumbList"' not in html:
        issue(MEDIUM, 'missing_breadcrumb', slug, 'No BreadcrumbList JSON-LD found')

    # 3d. noindex posts must have canonical_override
    if noindex and not p.get('canonical_override'):
        issue(CRITICAL, 'noindex_without_canonical', slug,
              'Post is noindex but has no canonical_override — set canonical_override in posts.json')

    # 3e. Verify noindex HTML actually has correct robots meta
    if noindex:
        if 'content="noindex, follow"' not in html:
            issue(CRITICAL, 'noindex_not_in_html', slug,
                  'Post has noindex=true in posts.json but generated HTML still says index — regenerate')

# ── 4. Duplicate detection (high title-token overlap without noindex) ─────────
def title_tokens(t):
    return set(w.lower() for w in re.split(r'\W+', t) if len(w) >= 4)

# Terms so common in an African betting site that they carry no disambiguation signal
NICHE_STOPWORDS = {'2026','2025','2024','best','guide','tips','odds','review','africa',
                   'african','betting','sport','sports','news','football','latest',
                   'match','matches','preview','analysis','insights','prediction',
                   'predictions','results','league','world','today','2026'}

COUNTRY_TOKENS = {'nigeria','kenya','ghana','south','africa','tanzania','senegal',
                  'morocco','egypt','cameroon','uganda','zambia','ethiopia','zimbabwe',
                  'rwanda','malawi','mozambique','angola','congo','botswana','namibia'}

def are_siblings(s1, s2):
    d = title_tokens(s1) ^ title_tokens(s2)
    d -= NICHE_STOPWORDS
    return bool(d & COUNTRY_TOKENS)

indexed_posts = [p for p in posts if not p.get('noindex', False)]
for i, pa in enumerate(indexed_posts):
    # Strip stopwords before comparing — only flag posts that share 5+ *meaningful* tokens
    ta = title_tokens(pa['title']) - NICHE_STOPWORDS
    for pb in indexed_posts[i+1:]:
        tb = title_tokens(pb['title']) - NICHE_STOPWORDS
        shared = ta & tb
        if len(shared) >= 5 and not are_siblings(pa['title'], pb['title']):
            issue(MEDIUM, 'potential_duplicate', pa['slug'],
                  f"High title overlap ({len(shared)} meaningful tokens) with {pb['slug']!r} — consider noindex")

# ── 5. Key static pages audit ─────────────────────────────────────────────────
STATIC_CHECKS = [
    ('index.html', 'homepage'),
    ('tips/index.html', 'tips'),
    ('odds/index.html', 'odds'),
    ('countries/index.html', 'countries'),
    ('about/index.html', 'about'),
    ('blog/index.html', 'blog'),
]

for rel_path, label in STATIC_CHECKS:
    path = BASE / rel_path
    if not path.exists():
        issue(MEDIUM, 'missing_static_page', label, f'{rel_path} not found')
        continue
    html = path.read_text(errors='replace')

    if '<h1' not in html.lower():
        issue(HIGH, 'missing_h1', label, f'No H1 on {rel_path}')
    if '<meta name="description"' not in html:
        issue(HIGH, 'missing_meta_desc', label, f'No meta description on {rel_path}')
    if 'rel="canonical"' not in html:
        issue(HIGH, 'missing_canonical', label, f'No canonical link on {rel_path}')
    if 'og:image' not in html:
        issue(MEDIUM, 'missing_og_image', label, f'No og:image on {rel_path}')
    if 'shared.js' in html and 'shared.js" defer' in html:
        issue(CRITICAL, 'shared_js_defer', label, f'shared.js has defer attribute — BREAKS the page')

# ── 6. shared.js defer check across all HTML ──────────────────────────────────
for html_path in BASE.rglob('*.html'):
    try:
        content = html_path.read_text(errors='replace')
    except Exception:
        continue
    if re.search(r'shared\.js[^"]*"\s+defer', content):
        rel = str(html_path.relative_to(BASE))
        issue(CRITICAL, 'shared_js_defer', rel,
              'shared.js loaded with defer — will break page rendering')

# ── Report ────────────────────────────────────────────────────────────────────
by_severity = {CRITICAL: [], HIGH: [], MEDIUM: [], INFO: []}
for iss in issues:
    by_severity[iss['severity']].append(iss)

total = len(issues)
print(f"\n{'='*60}")
print(f"SifuFinds SEO Audit — {total} issues found")
print(f"{'='*60}")
for sev in [CRITICAL, HIGH, MEDIUM, INFO]:
    items = by_severity[sev]
    if items:
        print(f"\n[{sev}] {len(items)} issues")
        for iss in items[:20]:
            print(f"  • {iss['page']:50s}  {iss['check']}  {iss['detail'][:80]}")
        if len(items) > 20:
            print(f"    ... and {len(items)-20} more")

print(f"\n{'='*60}")
print(f"Summary: {len(by_severity[CRITICAL])} critical | "
      f"{len(by_severity[HIGH])} high | "
      f"{len(by_severity[MEDIUM])} medium | "
      f"{len(by_severity[INFO])} info")

# ── Write JSON report ──────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('--fix', action='store_true')
parser.add_argument('--report', action='store_true')
args, _ = parser.parse_known_args()

if args.report:
    report = {
        'date': __import__('datetime').date.today().isoformat(),
        'total': total,
        'by_severity': {k: len(v) for k, v in by_severity.items()},
        'issues': issues,
    }
    report_path = BASE / 'seo-report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to seo-report.json")

# ── Auto-fix: title truncation (safe) ─────────────────────────────────────────
if args.fix:
    fixed = 0
    slug_map = {p['slug']: p for p in posts}

    for iss in by_severity[HIGH]:
        if iss['check'] == 'title_length':
            slug = iss['page']
            p = slug_map.get(slug)
            if p and len(p.get('title', '')) > 60:
                original = p['title']
                truncated = original[:57].rsplit(' ', 1)[0] + '…'
                p['title'] = truncated
                print(f"  FIX title: {original[:70]!r} → {truncated!r}")
                fixed += 1
        elif iss['check'] == 'meta_desc_length':
            slug = iss['page']
            p = slug_map.get(slug)
            if p and len(p.get('excerpt', '')) > 155:
                original = p['excerpt']
                truncated = original[:152].rsplit(' ', 1)[0] + '…'
                p['excerpt'] = truncated
                print(f"  FIX excerpt [{slug[:40]}]: {len(original)} → {len(truncated)} chars")
                fixed += 1

    if fixed:
        if isinstance(raw, dict):
            raw['posts'] = posts
            out = raw
        else:
            out = posts
        with open(POSTS_JSON, 'w') as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print(f"\n{fixed} titles auto-fixed in posts.json")
        print("Re-run: python3 gen_blog_post_pages.py --force")
    else:
        print("\nNo auto-fixable issues found.")

# Exit with non-zero if any CRITICAL issues
if by_severity[CRITICAL]:
    sys.exit(1)
