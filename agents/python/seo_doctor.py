#!/usr/bin/env python3
"""
SifuFinds SEO Doctor — Daily Auto-Healer
Runs daily via GitHub Actions. Checks and auto-fixes every SEO signal on the site.
Never exits with a failure code — it heals, reports, then exits 0.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from seo_meta import strip_dangling_words  # noqa: E402
TODAY = datetime.now(timezone.utc).strftime('%Y-%m-%d')
TODAY_ISO = datetime.now(timezone.utc).isoformat()
YEAR = datetime.now(timezone.utc).year

FIXES = []
WARNINGS = []

def log_fix(msg):
    print(f"  ✅ FIX: {msg}")
    FIXES.append(msg)

def log_warn(msg):
    print(f"  ⚠️  WARN: {msg}")
    WARNINGS.append(msg)

def log_info(msg):
    print(f"  ℹ️  {msg}")


# ── Helpers ──────────────────────────────────────────────────────────────────

def read(path):
    return Path(path).read_text(encoding='utf-8')

def write(path, content):
    Path(path).write_text(content, encoding='utf-8')

def truncate_title(t, max_len=60):
    """Trim to last full word boundary at or under max_len chars.

    Also runs strip_dangling_words() (seo_meta.py) — word-boundary
    truncation alone still allows a cut ending on a bare conjunction/
    preposition/possessive ("...Betting Tips Kenya: Best"), which is exactly
    as broken-looking as splitting a word in half. See that function's
    docstring for the full incident (2026-08-21).
    """
    if len(t) <= max_len:
        return t
    cut = t[:max_len].rsplit(' ', 1)[0]
    if '|' in cut:
        return strip_dangling_words(cut)
    return strip_dangling_words(cut.rstrip(' :-—|'))

def truncate_meta(m, max_len=160):
    if len(m) <= max_len:
        return m
    cut = m[:max_len - 1].rsplit(' ', 1)[0]
    return strip_dangling_words(cut.rstrip(' ,;.')) + '.'


# ── 1. Core HTML pages: title / meta / canonical / schema ────────────────────

CORE_PAGES = [
    ROOT / 'index.html',
    ROOT / 'blog' / 'index.html',
    ROOT / 'tips' / 'index.html',
    ROOT / 'odds' / 'index.html',
    ROOT / 'countries' / 'index.html',
    ROOT / 'casino' / 'index.html',
    ROOT / 'about' / 'index.html',
    ROOT / 'bookmakers' / 'index.html',
]

def check_core_pages():
    print("\n── Core pages ──")
    for page in CORE_PAGES:
        if not page.exists():
            continue
        html = read(page)
        changed = False
        rel = page.relative_to(ROOT)

        # Title length
        m = re.search(r'<title>(.*?)</title>', html)
        if m:
            title = m.group(1)
            if len(title) > 60:
                new_title = truncate_title(title)
                html = html.replace(f'<title>{title}</title>', f'<title>{new_title}</title>', 1)
                log_fix(f"{rel}: title trimmed {len(title)}→{len(new_title)} chars")
                changed = True

        # Meta description length
        m = re.search(r'(<meta name="description" content=")(.*?)(")', html)
        if m:
            desc = m.group(2)
            if len(desc) > 160:
                new_desc = truncate_meta(desc)
                html = html.replace(m.group(0), f'{m.group(1)}{new_desc}{m.group(3)}', 1)
                log_fix(f"{rel}: meta trimmed {len(desc)}→{len(new_desc)} chars")
                changed = True

        # dateModified in JSON-LD — update to today
        if '"dateModified"' in html:
            new_html = re.sub(
                r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})[^"]*"',
                f'"dateModified": "{TODAY}"',
                html
            )
            if new_html != html:
                html = new_html
                log_fix(f"{rel}: dateModified → {TODAY}")
                changed = True

        # Footer year
        if 'foot-yr' in html or f'© {YEAR - 1}' in html:
            updated = re.sub(r'© \d{4} SifuFinds', f'© {YEAR} SifuFinds', html)
            if updated != html:
                html = updated
                log_fix(f"{rel}: copyright year → {YEAR}")
                changed = True

        # Canonical tag present
        if '<link rel="canonical"' not in html:
            log_warn(f"{rel}: missing canonical tag")

        if changed:
            write(page, html)


# ── 2. Blog posts.json: thin content, FAQ, word counts ───────────────────────

def check_blog_posts():
    print("\n── Blog posts ──")
    posts_path = ROOT / 'blog' / 'posts.json'
    data = json.loads(read(posts_path))
    posts = data['posts']
    changed = False

    thin = []
    no_faq = []
    for post in posts:
        body = post.get('body', '')
        wc = len(body.split())
        if wc < 900:
            thin.append(post['slug'])
        if not re.search(r'##\s*.*?(?:FAQ|Frequently|Common Q)', body, re.IGNORECASE):
            no_faq.append(post['slug'])

    if thin:
        log_warn(f"{len(thin)} posts below 900 words: {', '.join(thin[:5])}{'...' if len(thin)>5 else ''}")
    else:
        log_info(f"All {len(posts)} posts meet 900+ word target ✓")

    if no_faq:
        log_warn(f"{len(no_faq)} posts missing FAQ section: {', '.join(no_faq[:5])}")
    else:
        log_info(f"All {len(posts)} posts have FAQ sections ✓")

    if changed:
        write(posts_path, json.dumps(data, indent=2, ensure_ascii=False))


# ── 3. Country HTML pages: title / meta / schema freshness ───────────────────

def check_country_pages():
    print("\n── Country pages ──")
    countries_dir = ROOT / 'countries'
    if not countries_dir.exists():
        return

    pages_fixed = 0
    for country_dir in sorted(countries_dir.iterdir()):
        page = country_dir / 'index.html'
        if not page.exists() or not country_dir.is_dir():
            continue
        html = read(page)
        changed = False

        m = re.search(r'<title>(.*?)</title>', html)
        if m and len(m.group(1)) > 65:
            new_title = truncate_title(m.group(1), 65)
            html = html.replace(f'<title>{m.group(1)}</title>', f'<title>{new_title}</title>', 1)
            changed = True

        m = re.search(r'(<meta name="description" content=")(.*?)(")', html)
        if m and len(m.group(2)) > 160:
            new_desc = truncate_meta(m.group(2))
            html = html.replace(m.group(0), f'{m.group(1)}{new_desc}{m.group(3)}', 1)
            changed = True

        if '"dateModified"' in html:
            new_html = re.sub(
                r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})[^"]*"',
                f'"dateModified": "{TODAY}"',
                html
            )
            if new_html != html:
                html = new_html
                changed = True

        if changed:
            write(page, html)
            pages_fixed += 1

    if pages_fixed:
        log_fix(f"Country pages: fixed {pages_fixed} pages (title/meta/dateModified)")
    else:
        log_info("Country pages: all clean ✓")


# ── 4. Generated blog post HTML: alt text, dateModified ──────────────────────

def check_blog_html():
    print("\n── Blog HTML pages ──")
    blog_dir = ROOT / 'blog'
    pages_fixed = 0
    missing_alt = []

    for post_dir in sorted(blog_dir.iterdir()):
        page = post_dir / 'index.html'
        if not page.exists() or not post_dir.is_dir():
            continue
        html = read(page)
        changed = False

        # dateModified freshness: update if > 30 days old
        m = re.search(r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})', html)
        if m:
            try:
                mod_date = datetime.strptime(m.group(1), '%Y-%m-%d')
                age_days = (datetime.now() - mod_date).days
                if age_days > 30:
                    new_html = re.sub(
                        r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})[^"]*"',
                        f'"dateModified": "{TODAY}"',
                        html
                    )
                    if new_html != html:
                        html = new_html
                        changed = True
            except ValueError:
                pass

        # Flag images without alt text
        imgs_no_alt = re.findall(r'<img(?![^>]*alt=)[^>]*>', html)
        if imgs_no_alt:
            missing_alt.append(str(post_dir.name))

        if changed:
            write(page, html)
            pages_fixed += 1

    if pages_fixed:
        log_fix(f"Blog HTML: refreshed dateModified on {pages_fixed} stale pages")
    else:
        log_info("Blog HTML: dateModified all current ✓")

    if missing_alt:
        log_warn(f"Images missing alt text in {len(missing_alt)} posts: {', '.join(missing_alt[:5])}")


# ── 5. robots.txt ────────────────────────────────────────────────────────────

def check_robots():
    print("\n── robots.txt ──")
    robots_path = ROOT / 'robots.txt'
    if not robots_path.exists():
        log_warn("robots.txt missing")
        return
    content = read(robots_path)
    # Ensure sitemap is present
    if 'Sitemap:' not in content:
        content += '\nSitemap: https://sifufinds.com/sitemap.xml\n'
        write(robots_path, content)
        log_fix("robots.txt: added Sitemap directive")
    else:
        log_info("robots.txt: OK ✓")


# ── 6. llms.txt freshness ────────────────────────────────────────────────────

def check_llms():
    print("\n── llms.txt ──")
    llms_path = ROOT / 'llms.txt'
    if not llms_path.exists():
        log_warn("llms.txt missing — AI search readiness impacted")
        return
    content = read(llms_path)
    original = content

    # Update the Last Updated date
    content = re.sub(r'## Last Updated\n\d{4}-\d{2}-\d{2}', f'## Last Updated\n{TODAY}', content)

    # Keep the blog post count honest — this went stale for months (claimed
    # 309 while posts.json actually had 236, then 540) with nothing catching
    # it (GEO audit finding, 2026-07-26).
    posts_path = ROOT / 'blog' / 'posts.json'
    if posts_path.exists():
        try:
            post_count = len(json.loads(read(posts_path)).get('posts', []))
            content = re.sub(r'Full blog post index \(\d+ posts, XML sitemap\)',
                              f'Full blog post index ({post_count} posts, XML sitemap)', content)
        except json.JSONDecodeError:
            pass

    if content != original:
        write(llms_path, content)
        log_fix(f"llms.txt: Last Updated → {TODAY}, blog post count refreshed")
    else:
        log_info("llms.txt: present and current ✓")


# ── 7. sitemap.xml freshness ─────────────────────────────────────────────────

def check_sitemap():
    print("\n── Sitemap ──")
    sitemap_path = ROOT / 'sitemap.xml'
    if not sitemap_path.exists():
        log_warn("sitemap.xml missing")
        return
    content = read(sitemap_path)
    # Check if any lastmod entries are stale (>7 days for core pages)
    dates_found = re.findall(r'<lastmod>(\d{4}-\d{2}-\d{2})</lastmod>', content)
    if dates_found:
        oldest = min(dates_found)
        try:
            age = (datetime.now() - datetime.strptime(oldest, '%Y-%m-%d')).days
            if age > 7:
                log_warn(f"Sitemap: oldest lastmod is {oldest} ({age} days ago) — regenerating")
                return True  # signal need to regenerate
        except ValueError:
            pass
    log_info("Sitemap: present ✓")
    return False


# ── 8. Regenerate blog HTML + sitemap ────────────────────────────────────────

def regenerate():
    print("\n── Regenerating ──")
    gen_script = ROOT / 'gen_blog_post_pages.py'
    if gen_script.exists():
        result = subprocess.run(
            [sys.executable, str(gen_script), '--force'],
            cwd=str(ROOT),
            capture_output=True, text=True
        )
        if result.returncode == 0:
            last_line = [l for l in result.stdout.strip().split('\n') if l.strip()][-1] if result.stdout.strip() else ''
            log_fix(f"Blog HTML regenerated: {last_line}")
        else:
            log_warn(f"gen_blog_post_pages.py error: {result.stderr[:200]}")

    sitemap_script = ROOT / 'gen_sitemap.py'
    if sitemap_script.exists():
        result = subprocess.run(
            [sys.executable, str(sitemap_script)],
            cwd=str(ROOT),
            capture_output=True, text=True
        )
        if result.returncode == 0:
            last_line = [l for l in result.stdout.strip().split('\n') if l.strip()][-1] if result.stdout.strip() else ''
            log_fix(f"Sitemap regenerated: {last_line}")
        else:
            log_warn(f"gen_sitemap.py error: {result.stderr[:200]}")


# ── 9. Schema integrity spot-check ───────────────────────────────────────────

def check_schema():
    print("\n── Schema spot-check ──")
    issues = 0
    check_files = [
        ROOT / 'index.html',
        ROOT / 'blog' / 'index.html',
        ROOT / 'tips' / 'index.html',
    ]
    for page in check_files:
        if not page.exists():
            continue
        html = read(page)
        schemas = re.findall(r'"@type"\s*:\s*"([^"]+)"', html)
        rel = page.relative_to(ROOT)
        if not schemas:
            log_warn(f"{rel}: no schema found")
            issues += 1
        else:
            log_info(f"{rel}: schema types: {', '.join(set(schemas))[:80]}")
    if not issues:
        log_info("Schema spot-check: passed ✓")


# ── 10. Health report ────────────────────────────────────────────────────────

def write_health_report():
    health_path = ROOT / 'data' / 'seo_health.json'
    health_path.parent.mkdir(exist_ok=True)
    report = {
        'date': TODAY,
        'fixes_applied': len(FIXES),
        'warnings': len(WARNINGS),
        'fixes': FIXES,
        'warnings_list': WARNINGS,
        'status': 'healthy' if len(WARNINGS) == 0 else 'warnings',
    }
    write(health_path, json.dumps(report, indent=2))
    log_info(f"Health report written: data/seo_health.json")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"╔══════════════════════════════════════════════╗")
    print(f"║  SifuFinds SEO Doctor — {TODAY}  ║")
    print(f"╚══════════════════════════════════════════════╝")

    check_robots()
    check_llms()
    check_core_pages()
    check_country_pages()
    check_blog_posts()
    check_schema()
    need_sitemap_regen = check_sitemap()
    check_blog_html()

    # Always regenerate to keep everything fresh
    regenerate()

    # Ping all major crawlers so Google/Bing/Yandex learn about fresh content immediately
    ping_script = Path(__file__).parent / 'crawler_ping.py'
    if ping_script.exists():
        print("\n── Crawler Ping ──")
        result = subprocess.run(
            [sys.executable, str(ping_script)],
            cwd=str(ROOT),
            capture_output=True, text=True
        )
        if result.returncode == 0:
            log_fix("Crawler pings sent (Google, Bing, Yandex)")
            print(result.stdout.strip())
        else:
            log_warn(f"Crawler ping error: {result.stderr[:200]}")

    write_health_report()

    print(f"\n{'═'*50}")
    print(f"  Fixes applied: {len(FIXES)}")
    print(f"  Warnings:      {len(WARNINGS)}")
    print(f"  Status:        {'✅ Healthy' if not WARNINGS else '⚠️  Warnings (see above)'}")
    print(f"{'═'*50}")

    # Always exit 0 — healer, not alerter
    sys.exit(0)


if __name__ == '__main__':
    main()
