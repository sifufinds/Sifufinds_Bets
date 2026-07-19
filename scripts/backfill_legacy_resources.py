#!/usr/bin/env python3
"""One-time backfill: inject resources-box + reviewedBy schema into legacy blog
posts whose slugs no longer exist in blog/posts.json (posts.json is a rolling
window; older static pages stay live per validate_site.py but stop receiving
template upgrades from gen_blog_post_pages.py --force).

Purely additive: never touches existing body prose, only appends the
resources box before </article> and splices a reviewedBy field into the
existing Article JSON-LD. Metadata (tags/category/bookmaker) is read back
from each page's own <meta> tags and body text, not invented.
"""
import glob
import re
import sys

sys.path.insert(0, '.')
import gen_blog_post_pages as g  # noqa: E402

REVIEWED_BY = (
    '"reviewedBy": {"@type": "Person", "@id": "https://sifufinds.com/about/#sifu-kai", '
    '"name": "Sifu Kai", "jobTitle": "Lead Betting Analyst & Editor-in-Chief", '
    '"url": "https://sifufinds.com/about/"},'
)


def extract_post_meta(html: str) -> dict:
    kw_match = re.search(r'<meta name="keywords" content="([^"]*)">', html)
    tags = [t.strip() for t in kw_match.group(1).split(',')] if kw_match else []

    cat_match = re.search(r'<meta property="article:section" content="([^"]*)">', html)
    category = cat_match.group(1) if cat_match else 'football'

    body_lower = html.lower()
    bookmaker_featured = ''
    for kw in g._BK_SLUG_TO_LINK:
        if kw in body_lower:
            bookmaker_featured = kw
            break

    return {'tags': tags, 'category': category, 'bookmaker_featured': bookmaker_featured}


def patch_file(path: str) -> str:
    html = open(path, encoding='utf-8').read()
    changed = []

    if 'resources-box' not in html:
        post_meta = extract_post_meta(html)
        resources_html = g.build_resources_box(post_meta)
        new_html = html.replace('</article>', f'{resources_html}\n</article>', 1)
        if new_html == html:
            return 'SKIP (no </article> found)'
        html = new_html
        changed.append('resources-box')

    if '"reviewedBy"' not in html:
        author_pattern = re.compile(
            r'("author":\s*\{"@type":\s*"Organization"[^}]*\},)'
        )
        new_html, n = author_pattern.subn(rf'\1 {REVIEWED_BY}', html, count=1)
        if n:
            html = new_html
            changed.append('reviewedBy')

    if changed:
        open(path, 'w', encoding='utf-8').write(html)
        return '+'.join(changed)
    return 'SKIP (nothing to do)'


def main():
    all_files = sorted(glob.glob('blog/*/index.html'))
    stats: dict[str, int] = {}
    for path in all_files:
        html = open(path, encoding='utf-8').read()
        if 'resources-box' in html and '"reviewedBy"' in html:
            continue
        if '"@id": "https://sifufinds.com/about/#sifu-kai"' in html and 'resources-box' in html:
            continue
        result = patch_file(path)
        stats[result] = stats.get(result, 0) + 1
        print(f'{result:35s} {path}')
    print('\n--- summary ---')
    for k, v in sorted(stats.items()):
        print(f'{v:4d}  {k}')


if __name__ == '__main__':
    main()
