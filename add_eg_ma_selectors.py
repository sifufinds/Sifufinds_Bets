#!/usr/bin/env python3
"""Add Egypt and Morocco to all country selector dropdowns in HTML files."""

import os, re

BASE = os.path.dirname(os.path.abspath(__file__))

EG_MA_OPTIONS = """\
      <option value="EG">🇪🇬 Egypt · EGP</option>
      <option value="MA">🇲🇦 Morocco · MAD</option>"""

# The anchor line that immediately precedes the Namibia option (last in current list)
AFTER_NA = '      <option value="NA">🇳🇦 Namibia · NAD</option>'

# collect all html files
html_files = []
for root, dirs, files in os.walk(BASE):
    # skip hidden dirs and venv
    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules',)]
    for f in files:
        if f.endswith('.html'):
            html_files.append(os.path.join(root, f))

updated = 0
skipped = 0

for path in sorted(html_files):
    with open(path, encoding='utf-8') as f:
        content = f.read()

    if 'value="EG"' in content:
        skipped += 1
        continue

    if AFTER_NA not in content:
        skipped += 1
        continue

    new_content = content.replace(
        AFTER_NA,
        AFTER_NA + '\n' + EG_MA_OPTIONS
    )
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    rel = os.path.relpath(path, BASE)
    print(f'  ✓  {rel}')
    updated += 1

print(f'\n✅ Updated {updated} files, skipped {skipped}')
