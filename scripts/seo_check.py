#!/usr/bin/env python3
"""Automated SEO audit for sifufinds.com static site.

Checks:
  - Blog posts: title length, meta description length, H1 presence,
    FAQPage schema when FAQ content exists, BreadcrumbList schema,
    noindex posts having correct canonical_override
  - Key pages: H1 presence, meta description, og:image, canonical
  - Duplicate detection: flags posts with high title-token overlap
    that don't have canonical_override set
  - Every deployed HTML page (not just blog): rendered <title>/meta
    description length, and duplicate <h1> tags — see section 7
  - Title/URL falsely claiming an African transfer/club story that the body
    never delivers (e.g. "Transfer Frenzy in Africa" about English clubs) —
    see section 4c

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

sys.path.insert(0, str(BASE))
from gen_blog_post_pages import extract_faq_schema  # noqa: E402
sys.path.insert(0, str(BASE / 'agents' / 'python'))
from utils.title_content_match import check_africa_framing  # noqa: E402

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

# ── 0. Duplicate slugs ─────────────────────────────────────────────────────────
# gen_blog_post_pages.py writes blog/<slug>/index.html in array order, so two
# posts sharing a slug silently collide — the later one overwrites the earlier
# one's page and its content becomes unreachable at its own URL. The generator
# now self-heals this (see dedupe_slugs() in gen_blog_post_pages.py), but this
# check exists as a permanent, independent tripwire in case that ever changes.
from collections import Counter
slug_counts = Counter(p.get('slug', '') for p in posts)
for slug, count in slug_counts.items():
    if slug and count > 1:
        issue(CRITICAL, 'duplicate_slug', slug,
              f"{count} posts share this slug — {count - 1} post(s) are silently shadowed and unreachable. "
              f"Run 'python3 gen_blog_post_pages.py --force' to auto-heal.")

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
    """True if the generator can actually extract FAQPage entries from this body.

    Delegates to extract_faq_schema() instead of a standalone regex so this
    check can never drift out of sync with what the generator emits — the old
    standalone regex flagged plain bold section headers ending in "?" (e.g.
    "**Fury Trilogy Ruled Out: What's Next for Usyk?**") as FAQ content even
    when there was no FAQ section at all, producing unfixable false positives.
    """
    return bool(extract_faq_schema(body))

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

    # 3f. Posts genuinely bylined to Sifu Kai must get Person schema, not
    # Organization — gen_blog_post_pages.py only assigns Person/#sifu-kai for
    # author == 'Sifu Kai' exactly (desk bylines like "Football Desk"
    # correctly get Organization, since attributing those to his named
    # identity would misrepresent authorship — that's not a defect).
    # Look for the JSON-LD author object specifically (`"author": {...`),
    # not the unrelated `<meta name="author" content="...">` tag that
    # appears earlier in every page and would otherwise be matched first.
    if not noindex and '"Article"' in html and p.get('author', '').strip() == 'Sifu Kai':
        m = re.search(r'"author":\s*\{[^}]*\}', html)
        if m and '"@type": "Person"' not in m.group(0):
            issue(HIGH, 'author_schema_org_not_person', slug,
                  'Post is bylined to Sifu Kai but author schema is not Person — check gen_blog_post_pages.py author_schema logic')

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

# ── 4b. Formulaic AI-tell openers (visibility only — not auto-fixable here) ──
# CLAUDE.md's Voice & Language Rules ban these outright. 68 of 540 posts
# (12.6%) had one as of the 2026-07-26 GEO audit. Not mechanically fixable
# (needs an LLM rewrite preserving facts) — agents/python/agent_content_backfill.py
# now queues these for its existing batched rewrite pipeline; this is just the
# tracking signal so the remaining count stays visible in every audit run.
_FORMULAIC_OPENER = re.compile(
    r"^(In the world of|When it comes to|In today's fast-paced|"
    r"The world of \w+ is always|As the |As we continue)", re.IGNORECASE)
_opener_hits = [p['slug'] for p in posts
                if _FORMULAIC_OPENER.search(p.get('body', '').strip().split('\n', 1)[0])]
if _opener_hits:
    issue(INFO, 'formulaic_opener', f'{len(_opener_hits)} posts',
          f"{len(_opener_hits)} posts still open with a banned formulaic phrase "
          f"(see CLAUDE.md Voice & Language Rules) — queued in "
          f"agent_content_backfill.py's rewrite pipeline, not auto-fixable here")

# ── 4c. Title/URL claims an African transfer/club story the body never
# delivers ("Transfer Frenzy in Africa" about West Ham/Sunderland/Chelsea/
# Newcastle, zero African clubs mentioned) — found 2026-08-16. Same
# deterministic check agent_sports_blog.py's generate_post() runs at
# generation time (utils/title_content_match.py); this is the permanent
# regression tripwire for anything that reaches posts.json through another
# path (manual edit, Sanity CMS sync, content_backfill rewrites).
for p in posts:
    violation = check_africa_framing(p.get('title', ''), p.get('slug', ''), p.get('body', ''))
    if violation:
        issue(CRITICAL, 'false_africa_framing', p['slug'], violation)

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
    if 'og:image:secure_url' in html:
        issue(HIGH, 'og_image_secure_url', label, f'Deprecated og:image:secure_url on {rel_path} — remove it')
    if 'og-image.png?v=' in html:
        issue(HIGH, 'og_image_versioned', label, f'Versioned ?v= suffix on og:image in {rel_path} — remove version string')
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

# ── 7. Site-wide title / meta-description length + duplicate H1 (every page
# type, not just blog) ─────────────────────────────────────────────────────────
# Checks #1/#2 above only ever read blog/posts.json — every non-blog template
# (bookmaker reviews, country pages, guides, tools...) hand-authors its own
# <title>/<meta name="description"> directly in a Python f-string with zero
# length enforcement. That gap let dozens of pages across every one of those
# generators ship a meta description over Google's 155-char display limit
# undetected (technical SEO audit, 2026-08-11; fixed at the source via the
# shared seo_meta.seo_meta_description() helper, this check is the permanent
# regression guard). This section walks every deployed HTML file directly
# (title/meta-desc regexed from the rendered page, not upstream JSON) so no
# template — present or future — can drift past these limits unnoticed.
#
# Duplicate <h1> is the same story: gen_blog_post_pages.py's markdown_to_html()
# used to render a body line starting with '# ' as a second <h1> (69 of 1209
# posts affected, one with 11), fixed the same day this check was added. The
# fix stops new duplicates; this check is the regression guard against it (or
# any other template) reintroducing the bug later.
NOT_DEPLOYED_DIRS = {
    'agents', 'scripts', 'supabase', 'firecrawl', 'geo-content-writer',
    'node_modules', '.git', '.github', '.venv', '.vscode',
    '__pycache__', '.firecrawl', '.claude',
}
# Blog posts are excluded from the title/meta-desc length re-check here (but
# not the H1 check below) — they're already covered by checks #1/#2 against
# their posts.json source, and re-checking the rendered HTML too would just
# double-report the same underlying issue under a different check name.
_TITLE_RE = re.compile(r'<title>([^<]*)</title>', re.IGNORECASE)
_DESC_RE = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"', re.IGNORECASE)

for html_path in BASE.rglob('*.html'):
    rel_parts = html_path.relative_to(BASE).parts
    if rel_parts and rel_parts[0] in NOT_DEPLOYED_DIRS:
        continue
    try:
        content = html_path.read_text(errors='replace')
    except Exception:
        continue
    rel = str(html_path.relative_to(BASE))

    # Skip noindex pages (redirect stubs, verification files) — a short/absent
    # description there is by design, not a bug.
    _robots_m = re.search(r'<meta\s+name="robots"[^>]*content="([^"]*)"', content)
    is_noindex = bool(_robots_m and 'noindex' in _robots_m.group(1).lower())

    if rel_parts[0] != 'blog' and not is_noindex:
        m = _TITLE_RE.search(content)
        if m and len(m.group(1)) > 60:
            issue(HIGH, 'title_length', rel, f"Title {len(m.group(1))} chars (max 60): {m.group(1)[:70]!r}")
        m = _DESC_RE.search(content)
        if m and len(m.group(1)) > 155:
            issue(HIGH, 'meta_desc_length', rel, f"Meta description {len(m.group(1))} chars (max 155)")

    h1_count = len(re.findall(r'<h1[\s>]', content, re.IGNORECASE))
    if h1_count > 1:
        issue(HIGH, 'duplicate_h1', rel, f"{h1_count} <h1> tags on one page (must be exactly 1)")

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
                # Clean word-boundary truncation, no ellipsis — a trailing "…"
                # bakes a broken-looking title into posts.json itself, which
                # then survives seo_title()'s own truncation untouched since
                # it's already short enough by the time that runs (technical
                # SEO audit, 2026-08-11 — same fix as seo_meta.seo_title()).
                truncated = original[:60].rsplit(' ', 1)[0]
                p['title'] = truncated
                print(f"  FIX title: {original[:70]!r} → {truncated!r}")
                fixed += 1
        elif iss['check'] == 'meta_desc_length':
            slug = iss['page']
            p = slug_map.get(slug)
            if p and len(p.get('excerpt', '')) > 155:
                original = p['excerpt']
                truncated = original[:155].rsplit(' ', 1)[0]
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
        # posts-data.js is the file://-protocol fallback copy of the same
        # data (see agent_sports_blog.save_posts()) — writing posts.json
        # alone here left it silently drifting out of sync on every daily
        # auto-heal run that actually fixed something (found 2026-08-01).
        payload = out if isinstance(out, dict) else {'posts': out}
        posts_data_js = POSTS_JSON.parent / 'posts-data.js'
        with open(posts_data_js, 'w', encoding='utf-8') as f:
            f.write(f"window.POSTS_DATA={json.dumps(payload, ensure_ascii=False)};\n")
        print(f"\n{fixed} titles auto-fixed in posts.json (+ posts-data.js)")
        print("Re-run: python3 gen_blog_post_pages.py --force")
    else:
        print("\nNo auto-fixable issues found.")

# Exit with non-zero if any CRITICAL issues
if by_severity[CRITICAL]:
    sys.exit(1)
