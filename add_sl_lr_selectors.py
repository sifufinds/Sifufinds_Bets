#!/usr/bin/env python3
"""Add Sierra Leone and Liberia to all country selector dropdowns."""

import os

BASE = os.path.dirname(os.path.abspath(__file__))

SL_LR_OPTIONS = """\
      <option value="SL">🇸🇱 Sierra Leone · Le SLL</option>
      <option value="LR">🇱🇷 Liberia · $ LRD</option>"""

AFTER_MA = '      <option value="MA">🇲🇦 Morocco · MAD</option>'

html_files = []
for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules',)]
    for f in files:
        if f.endswith('.html'):
            html_files.append(os.path.join(root, f))

updated = skipped = 0
for path in sorted(html_files):
    with open(path, encoding='utf-8') as f:
        content = f.read()
    if 'value="SL"' in content:
        skipped += 1
        continue
    if AFTER_MA not in content:
        skipped += 1
        continue
    new_content = content.replace(AFTER_MA, AFTER_MA + '\n' + SL_LR_OPTIONS)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'  ✓  {os.path.relpath(path, BASE)}')
    updated += 1

print(f'\n✅ Updated {updated} files, skipped {skipped}')
