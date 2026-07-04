#!/usr/bin/env python3
"""Audit <title> tag lengths across all HTML files.

Usage:
    python3 scripts/audit_titles.py            # report only
    python3 scripts/audit_titles.py --fix      # report + patch violations in-place
    python3 scripts/audit_titles.py --max 55   # custom max length (default 60)

Exit code:
    0 — all titles within limit
    1 — violations found (useful for CI)
"""

import argparse
import html as html_module
import os
import re
import sys

MAX_LEN = 60
SUFFIX = "| SifuFinds"
SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".github",
             "agents", "firecrawl", "geo-content-writer"}


def seo_title(title: str, max_len: int = MAX_LEN) -> str:
    """Trim title to ≤ max_len chars with '| SifuFinds' suffix."""
    full = f"{title} {SUFFIX}"
    if len(full) <= max_len:
        return full
    for sep in [" — ", " - ", ": ", " | "]:
        idx = title.find(sep)
        if idx > 10:
            candidate = f"{title[:idx]} {SUFFIX}"
            if len(candidate) <= max_len:
                return candidate
    available = max_len - len(SUFFIX) - 2
    truncated = title[:available].rsplit(" ", 1)[0]
    return f"{truncated}… {SUFFIX}"


def strip_to_content(raw_title: str) -> str:
    """Strip '| SifuFinds' and any trailing pipe sections to get the core content."""
    t = raw_title.strip()
    for brand in [" | SifuFinds", "| SifuFinds"]:
        if t.endswith(brand):
            t = t[: -len(brand)].rstrip()
            break
    if " | " in t:
        t = t[: t.index(" | ")]
    return t.strip()


def iter_html_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in filenames:
            if fname.endswith(".html"):
                yield os.path.join(dirpath, fname)


def audit(max_len: int, fix: bool) -> list[tuple[int, str, str, str]]:
    """Return list of (length, path, current_title, fixed_title) for violations."""
    violations = []
    for path in iter_html_files(SITE_ROOT):
        try:
            content = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        m = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
        if not m:
            continue
        raw = html_module.unescape(m.group(1)).strip()
        if len(raw) <= max_len:
            continue
        content_part = strip_to_content(raw)
        fixed = seo_title(content_part, max_len)
        violations.append((len(raw), path, raw, fixed))
        if fix:
            patched = content.replace(m.group(0), f"<title>{fixed}</title>", 1)
            open(path, "w", encoding="utf-8").write(patched)
    return sorted(violations, reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit <title> tag lengths.")
    parser.add_argument("--fix", action="store_true", help="Patch violations in-place")
    parser.add_argument("--max", type=int, default=MAX_LEN, dest="max_len",
                        help=f"Max title length (default {MAX_LEN})")
    args = parser.parse_args()

    violations = audit(args.max_len, args.fix)
    rel = lambda p: os.path.relpath(p, SITE_ROOT)

    if not violations:
        print(f"✓ All titles are ≤ {args.max_len} chars — no issues found.")
        sys.exit(0)

    action = "FIXED" if args.fix else "VIOLATION"
    print(f"{'[' + action + ']':12}  {'LEN':>3}  PATH")
    print("-" * 80)
    for length, path, current, fixed in violations:
        print(f"{'[' + action + ']':12}  {length:>3}  {rel(path)}")
        print(f"  Current : {current}")
        if args.fix:
            print(f"  Fixed   : {fixed}")
        else:
            print(f"  Proposed: {fixed}")
        print()

    total = len(violations)
    verb = "patched" if args.fix else "found"
    print(f"{'─' * 80}")
    print(f"{total} title violation(s) {verb}.")

    if not args.fix:
        print("Run with --fix to patch in-place.")
        sys.exit(1)


if __name__ == "__main__":
    main()
