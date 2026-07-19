#!/usr/bin/env python3
"""One-time repair: legacy FAQPage JSON-LD blocks contain raw newline
characters inside "text"/"name" string values (pre-dates the json.dumps
fix in extract_faq_schema()), making the JSON-LD invalid and unparseable
by Google/AI crawlers. Collapses whitespace runs inside those string
values to a single space, matching what the generator now emits.
"""
import glob
import json
import re

FIELD_STRING = re.compile(r'("(?:text|name)":\s*")((?:[^"\\]|\\.)*)(")', re.S)
# description/headline breakage is a different root cause (unescaped literal
# quote marks inside a translated excerpt/title), not embedded newlines —
# needs proper re-escaping via json.dumps, not whitespace collapsing.
DESC_FIELD = re.compile(r'("description":\s*")(.*?)(",\n\s*"keywords")', re.S)
HEADLINE_FIELD = re.compile(r'("headline":\s*")(.*?)(",\n\s*"description")', re.S)


def collapse_ws(match: re.Match) -> str:
    prefix, value, suffix = match.groups()
    return prefix + re.sub(r'\s+', ' ', value).strip() + suffix


def reescape_quotes(match: re.Match) -> str:
    prefix, value, suffix = match.groups()
    # value currently has raw, un-escaped quote marks; json.dumps() re-escapes
    # correctly, then strip the extra pair of quotes json.dumps() itself adds.
    escaped = json.dumps(value)[1:-1]
    return prefix + escaped + suffix


def fix_file(path: str) -> bool:
    html = open(path, encoding='utf-8').read()
    m = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', html, re.S)
    if not m:
        return False
    block = m.group(2)
    try:
        json.loads(block)
        return False  # already valid
    except json.JSONDecodeError:
        pass
    fixed_block = FIELD_STRING.sub(collapse_ws, block)
    try:
        json.loads(fixed_block)
    except json.JSONDecodeError as e:
        print(f'STILL BROKEN after fix: {path} -> {e}')
        return False
    new_html = html[:m.start(2)] + fixed_block + html[m.end(2):]
    open(path, 'w', encoding='utf-8').write(new_html)
    return True


def main():
    fixed = 0
    still_broken = 0
    for f in sorted(glob.glob('blog/*/index.html')):
        html = open(f, encoding='utf-8').read()
        m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        if not m:
            continue
        try:
            json.loads(m.group(1))
            continue
        except json.JSONDecodeError:
            pass
        if fix_file(f):
            fixed += 1
        else:
            still_broken += 1
    print(f'fixed: {fixed}, still broken: {still_broken}')


if __name__ == '__main__':
    main()
