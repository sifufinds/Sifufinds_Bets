#!/usr/bin/env python3
"""Regenerate sitemap.xml from scratch, crawling all index.html files."""

import os
import json
import re
from datetime import date, datetime

BASE    = os.path.dirname(os.path.abspath(__file__))
DOMAIN  = 'https://sifufinds.com'
TODAY   = date.today().isoformat()

_NOINDEX_RE = re.compile(r'<meta\s+name="robots"\s+content="[^"]*noindex', re.IGNORECASE)


def _is_noindex(index_html_path: str) -> bool:
    """True if the page's own <meta name="robots"> carries noindex.

    Redirect-stub pages (e.g. countries/<slug>/ after the 2026-08-09
    best-bonus-in-<slug>/ rename) are intentionally noindex — never submit
    those to Google via sitemap even though the file still physically
    exists (kept only so nested sub-pages retain a non-403 parent dir).
    """
    try:
        with open(index_html_path, encoding='utf-8', errors='ignore') as f:
            head = f.read(4000)
    except OSError:
        return False
    return bool(_NOINDEX_RE.search(head))


def file_lastmod(url: str) -> str:
    """Return the ISO date of the index.html for this URL, falling back to TODAY."""
    path = url.replace(DOMAIN, '').strip('/')
    candidates = [
        os.path.join(BASE, path, 'index.html'),
        os.path.join(BASE, path + '.html'),
    ]
    for fp in candidates:
        if os.path.exists(fp):
            return datetime.fromtimestamp(os.path.getmtime(fp)).strftime('%Y-%m-%d')
    return TODAY

# Directories to exclude from crawl
EXCLUDED_DIRS = {
    'agents', 'firecrawl', 'geo-content-writer', 'supabase',
    '.git', '.github', '.venv', '__pycache__', 'node_modules',
    '.claude', 'data',
}

# Priority and changefreq by URL pattern
def classify(url: str):
    path = url.replace(DOMAIN, '').strip('/')

    if path == '':
        return '1.0', 'daily'
    if path in ('tips', 'tips/', 'casino', 'casino/', 'odds', 'odds/', 'blog', 'blog/'):
        return '0.9', 'hourly'
    if path.startswith('tips/world-cup-2026'):
        return '0.9', 'daily'
    if path.startswith('blog/') and path.count('/') == 1:
        return '0.8', 'weekly'
    if path.startswith('countries/') and path.count('/') == 1:
        return '0.9', 'daily'
    if path.startswith('countries/') and path.count('/') == 2:
        # city page
        return '0.75', 'weekly'
    if path.startswith('bookmakers/') and path.count('/') == 1:
        # main bookmaker review
        return '0.85', 'weekly'
    if path.startswith('bookmakers/') and path.count('/') == 2:
        # bookmaker × country
        return '0.8', 'weekly'
    if path.startswith('betting/') and path.count('/') == 1:
        # payment method hub
        return '0.8', 'weekly'
    if path.startswith('betting/') and path.count('/') == 2:
        # payment × country or sport × country
        return '0.75', 'weekly'
    if path.startswith('guides/'):
        return '0.7', 'monthly'
    if path.startswith('bonuses/'):
        return '0.75', 'weekly'
    if path.startswith('casino/') or path.startswith('odds/'):
        return '0.7', 'daily'
    if path.startswith('about') or path.startswith('contact'):
        return '0.4', 'monthly'

    return '0.6', 'monthly'


def _tracked_blog_slugs() -> set[str]:
    """Every blog/<slug>/ directory that's actually current per posts.json.

    blog/ accumulates orphaned directories over time (renamed/removed posts,
    a 2026-06-05 merge-conflict incident that required restoring 183 posts)
    whose static HTML is never deleted. collect_urls() used to walk the
    filesystem blindly, so every one of those stale directories kept getting
    resubmitted to Google on every sitemap regen (305 confirmed stale
    directories found in a 2026-07-26 GEO/technical audit). Scoping the blog
    sitemap to posts.json's tracked slugs stops feeding crawlers content the
    site no longer considers current, without touching/deleting any files.
    """
    posts_path = os.path.join(BASE, 'blog', 'posts.json')
    try:
        with open(posts_path, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return set()

    locales = ['fr', 'de', 'es', 'pt', 'sw']
    slugs = set()
    for post in data.get('posts', []):
        slug = post.get('slug')
        if not slug:
            continue
        slugs.add(slug)
        slugs.update(f'{slug}-{lg}' for lg in locales)
    return slugs


def collect_urls():
    tracked_blog_slugs = _tracked_blog_slugs()
    urls = []
    for root, dirs, files in os.walk(BASE):
        # Prune excluded directories in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith('.')]

        if 'index.html' not in files:
            continue

        rel = os.path.relpath(root, BASE)
        if rel == '.':
            url = f'{DOMAIN}/'
        else:
            rel_norm = rel.replace(os.sep, '/')
            url = f'{DOMAIN}/{rel_norm}/'

        # Skip analytics, google verification pages
        if any(skip in url for skip in ['/analytics', '/google3', '/gen_', '/.', '/data/']):
            continue

        # Skip pages that carry their own noindex meta (e.g. redirect stubs).
        if _is_noindex(os.path.join(root, 'index.html')):
            continue

        # blog/<slug>/ must still be a real post — see _tracked_blog_slugs().
        if rel.startswith('blog' + os.sep) and rel != 'blog':
            blog_slug = rel[len('blog' + os.sep):].split(os.sep)[0]
            if tracked_blog_slugs and blog_slug not in tracked_blog_slugs:
                continue

        urls.append(url)

    return sorted(set(urls))


CHILD_SITEMAPS = [
    ('sitemap-core.xml',       lambda p: p in ('', 'tips', 'casino', 'odds', 'blog', 'countries',
                                                'bookmakers', 'betting', 'guides', 'bonuses',
                                                'about', 'contact')),
    ('sitemap-countries.xml',  lambda p: p.startswith('countries/')),
    ('sitemap-blog.xml',       lambda p: p.startswith('blog/') and p != 'blog'),
    ('sitemap-tips.xml',       lambda p: p.startswith('tips/')),
    ('sitemap-betting.xml',    lambda p: p.startswith('betting/') or p.startswith('bookmakers/')),
    ('sitemap-guides.xml',     lambda p: p.startswith('guides/') or p.startswith('bonuses/') or
                                         p.startswith('casino/')),
]


def _url_block(url: str) -> list[str]:
    priority, changefreq = classify(url)
    lastmod = file_lastmod(url)
    return [
        '  <url>',
        f'    <loc>{url}</loc>',
        f'    <lastmod>{lastmod}</lastmod>',
        f'    <changefreq>{changefreq}</changefreq>',
        f'    <priority>{priority}</priority>',
        '  </url>',
    ]


def build_child_sitemap(name: str, urls: list[str]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
        '',
        f'  <!-- {name} — auto-generated by gen_sitemap.py — {TODAY} — {len(urls)} URLs -->',
        '',
    ]
    for url in sorted(urls):
        lines.extend(_url_block(url))
    lines.append('</urlset>')
    return '\n'.join(lines)


def build_sitemap_index(child_names: list[str]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '',
        f'  <!-- Sitemap index — auto-generated by gen_sitemap.py — {TODAY} -->',
        '',
    ]
    for name in child_names:
        lines += [
            '  <sitemap>',
            f'    <loc>{DOMAIN}/{name}</loc>',
            f'    <lastmod>{TODAY}</lastmod>',
            '  </sitemap>',
        ]
    lines.append('</sitemapindex>')
    return '\n'.join(lines)


def main():
    urls = collect_urls()
    print(f'  Found {len(urls)} indexable URLs')

    # Assign each URL to its child sitemap bucket
    buckets: dict[str, list[str]] = {name: [] for name, _ in CHILD_SITEMAPS}
    overflow: list[str] = []
    for url in urls:
        path = url.replace(DOMAIN, '').strip('/')
        assigned = False
        for name, pred in CHILD_SITEMAPS:
            if pred(path):
                buckets[name].append(url)
                assigned = True
                break
        if not assigned:
            overflow.append(url)

    if overflow:
        buckets.setdefault('sitemap-other.xml', []).extend(overflow)

    # Write child sitemaps
    written_names = []
    for name, urls_in_bucket in buckets.items():
        if not urls_in_bucket:
            continue
        content = build_child_sitemap(name, urls_in_bucket)
        out_path = os.path.join(BASE, name)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)
        written_names.append(name)
        print(f'  ✓  {name} — {len(urls_in_bucket)} URLs')

    # Write sitemap index
    index_content = build_sitemap_index(written_names)
    index_path = os.path.join(BASE, 'sitemap.xml')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    print(f'  ✓  sitemap.xml (index) — {len(written_names)} child sitemaps, {len(urls)} total URLs')


if __name__ == '__main__':
    main()
