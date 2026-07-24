#!/usr/bin/env python3
"""One-time backfill: inject the social share bar (X/Facebook/LinkedIn/
Telegram + copy-link) into legacy blog posts whose slugs no longer exist in
blog/posts.json. posts.json is a rolling window (see backfill_legacy_resources.py,
patch_legacy_og_images.py); older static pages stay live and public but stop
receiving template upgrades from gen_blog_post_pages.py --force.

Purely additive: reads each page's own canonical <link> and og:title <meta>
to build the share bar (same build_share_bar() used for live posts), then
splices in the CSS block, the two share-bar placements (top + bottom of the
article), and the copyPostLink() JS helper.
"""
import glob
import re
import sys

sys.path.insert(0, '.')
import gen_blog_post_pages as g  # noqa: E402

SHARE_CSS = '''.share-bar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:14px 0;padding:10px 0;border-top:1px solid #eee;border-bottom:1px solid #eee}
.share-label{font-size:12px;font-weight:700;color:#666;margin-right:2px}
.share-btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-width:38px;height:38px;padding:0 12px;border-radius:8px;border:1px solid #e0e0e0;background:#fff;color:#111;font-size:14px;font-weight:800;text-decoration:none;cursor:pointer;transition:transform .15s,box-shadow .15s;line-height:1}
.share-btn:hover{transform:translateY(-1px);box-shadow:0 3px 10px rgba(0,0,0,.12)}
.share-x:hover{background:#000;color:#fff;border-color:#000}
.share-fb:hover{background:#1877f2;color:#fff;border-color:#1877f2}
.share-li:hover{background:#0a66c2;color:#fff;border-color:#0a66c2}
.share-tg:hover{background:#26a5e4;color:#fff;border-color:#26a5e4}
.share-copy{font-size:12px;padding:0 14px}
.share-copy.copied{background:#1a6b35;color:#fff;border-color:#1a6b35}
'''

COPY_JS = '''function copyPostLink(btn,url){
  const done=()=>{
    const orig=btn.textContent;
    btn.textContent='\\u2713 Copied!';
    btn.classList.add('copied');
    setTimeout(()=>{btn.textContent=orig;btn.classList.remove('copied');},2000);
  };
  if(navigator.clipboard&&window.isSecureContext){
    navigator.clipboard.writeText(url).then(done).catch(()=>{});
  }else{
    const ta=document.createElement('textarea');
    ta.value=url;ta.style.position='fixed';ta.style.opacity='0';
    document.body.appendChild(ta);ta.select();
    try{document.execCommand('copy');done();}catch(e){}
    document.body.removeChild(ta);
  }
}
'''


def extract_canonical_and_title(html: str) -> tuple[str, str]:
    canon_match = re.search(r'<link rel="canonical" href="([^"]*)">', html)
    canonical = canon_match.group(1) if canon_match else ''
    title_match = re.search(r'<meta property="og:title" content="([^"]*)">', html)
    title = title_match.group(1) if title_match else ''
    return canonical, title


def patch_file(path: str) -> str:
    html = open(path, encoding='utf-8').read()
    canonical, title = extract_canonical_and_title(html)
    if not canonical or not title:
        return 'SKIP (no canonical/title found)'

    changed = []

    if '.share-bar{' not in html:
        new_html = html.replace('</style>', f'{SHARE_CSS}</style>', 1)
        if new_html == html:
            return 'SKIP (no </style> found)'
        html = new_html
        changed.append('css')

    if 'class="share-bar"' not in html:
        share_html = g.build_share_bar(canonical, title)
        new_html = html.replace(
            '<article class="post-body"', f'{share_html}\n<article class="post-body"', 1
        )
        if new_html == html:
            return 'SKIP (no <article class="post-body"> found)'
        html = new_html
        new_html = html.replace('</article>', f'</article>\n{share_html}', 1)
        if new_html == html:
            return 'SKIP (no </article> found)'
        html = new_html
        changed.append('share-bar')

    if 'function copyPostLink' not in html:
        new_html = html.replace('function init(){', f'{COPY_JS}function init(){{', 1)
        if new_html == html:
            return 'SKIP (no function init(){ found)'
        html = new_html
        changed.append('copy-js')

    if changed:
        open(path, 'w', encoding='utf-8').write(html)
        return '+'.join(changed)
    return 'SKIP (nothing to do)'


def main():
    all_files = sorted(glob.glob('blog/*/index.html'))
    stats: dict[str, int] = {}
    for path in all_files:
        html = open(path, encoding='utf-8').read()
        if 'class="share-bar"' in html and 'function copyPostLink' in html:
            continue
        result = patch_file(path)
        stats[result] = stats.get(result, 0) + 1
        print(f'{result:35s} {path}')
    print('\n--- summary ---')
    for k, v in sorted(stats.items()):
        print(f'{v:4d}  {k}')


if __name__ == '__main__':
    main()
