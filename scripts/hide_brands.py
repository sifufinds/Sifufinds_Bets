#!/usr/bin/env python3
"""HIDDEN BRANDS: strip every brand in data/hidden_brands.json from the live site.

Runs in deploy_hostinger.yml on the CI checkout right before the upload archive
is built. It rewrites the *deploy copy* only; never run --apply on your working
copy (it refuses to unless --root points somewhere else or --force is given).

    python3 scripts/hide_brands.py --apply            # CI: scrub the checkout in place
    python3 scripts/hide_brands.py --check            # exit 1 if anything is still visible
    python3 scripts/hide_brands.py --apply --root /tmp/site-copy   # local preview

What --apply does:
  * pages about a hidden brand (bookmakers/<brand>/..., or a <title>/<h1> naming
    one) become noindex redirect stubs to their parent section, get a 301 in
    .htaccess, and drop out of the sitemaps;
  * every other page loses the brand's cards, table columns/rows, FAQ items,
    sections, tags, links and sentences (scripts/hidden_brands_html.py);
  * JSON data files, window.X={...} data scripts, inline JS data lines,
    llms.txt/ai.txt are scrubbed the same way;
  * data/hidden_brands.json itself is removed from the deploy copy.
"""
from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hidden_brands_html import (Page, page_heading_mentions, resolve_href,  # noqa: E402
                                scrub_html, scrub_js, stub_html, visible_leaks)
from hidden_brands_lib import (CONFIG_PATH, ROOT, HiddenBrands, load_config,  # noqa: E402
                               scrub_json, scrub_json_strings, scrub_text)

# Mirrors EXCLUDE_DIRS in deploy_hostinger.yml's "Build deployment archive" step.
EXCLUDE_DIRS = {"agents", "scripts", "supabase", "firecrawl", "geo-content-writer",
                "node_modules", "__pycache__"}
TEXT_EXTS = {".html", ".json", ".js", ".xml", ".txt"}
CONFIG_REL = "data/hidden_brands.json"
HTACCESS_MARK = "# ── HIDDEN BRANDS (added at deploy by scripts/hide_brands.py) ──"
_WINDOW_JSON = re.compile(r"^(\s*window\.[\w$]+\s*=\s*)(.*?)(;?\s*)$", re.S)
_SAFE_PATH = re.compile(r"^[a-z0-9][a-z0-9/_-]*/$")


# ── file discovery ───────────────────────────────────────────────────────────

def deploy_files(root: Path) -> list[str]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        top = rel.split(os.sep)[0]
        if rel != "." and (top in EXCLUDE_DIRS or top.startswith(".")):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for f in filenames:
            if Path(f).suffix in TEXT_EXTS and " 2." not in f:
                out.append(posixpath.normpath(posixpath.join(rel.replace(os.sep, "/"), f)))
    return sorted(f for f in out if f != CONFIG_REL)


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8", errors="replace")


# ── stubs ────────────────────────────────────────────────────────────────────

def find_stubs(root: Path, html_files: list[str], hb: HiddenBrands) -> set[str]:
    """Site dirs ("blog/x/") whose index.html is about a hidden brand."""
    stubbed = set()
    for rel in html_files:
        if not rel.endswith("index.html") or rel == "index.html":
            continue
        d = rel[: -len("index.html")]
        if hb.mentions(d) or page_heading_mentions(_read(root, rel), hb):
            stubbed.add(d)
    return stubbed


def stub_target(d: str, stubbed: set[str], root: Path) -> str:
    parent = d
    while parent:
        parent = posixpath.dirname(parent.rstrip("/"))
        parent = parent + "/" if parent else ""
        if parent not in stubbed and (root / parent / "index.html").exists():
            return parent
    return ""


# ── per-file workers (run in a process pool) ─────────────────────────────────

_CTX: dict = {}


def _init_worker(root: str, stubbed: frozenset[str], hb: HiddenBrands) -> None:
    _CTX.update(root=Path(root), hb=hb, stubbed=stubbed)


def _scrub_file(rel: str) -> tuple[str, bool]:
    root, hb = _CTX["root"], _CTX["hb"]
    src = _read(root, rel)
    new = None
    if rel.endswith(".html"):
        new = scrub_html(src, Page(rel, hb, _CTX["stubbed"]))
    elif hb.mentions(src):
        new = _scrub_data_file(rel, src, hb)
    if new is not None and new != src:
        (root / rel).write_text(new, encoding="utf-8")
        return rel, True
    return rel, False


def _check_file(rel: str) -> tuple[str, list[str]]:
    root, hb = _CTX["root"], _CTX["hb"]
    src = _read(root, rel)
    if rel.endswith(".html"):
        return rel, visible_leaks(src, Page(rel, hb, _CTX["stubbed"]))
    if rel.endswith(".js"):
        if _WINDOW_JSON.match(src) and hb.mentions(src):
            return rel, ["data script"]
        return rel, ["js data line"] if scrub_js(src, hb) != src else []
    return rel, [m.group(0) for m in hb.regex.finditer(src)][:5] if hb.mentions(src) else []


def _scrub_data_file(rel: str, src: str, hb: HiddenBrands) -> str | None:
    if rel.endswith(".json"):
        try:
            data = json.loads(src)
        except json.JSONDecodeError:  # broken/partial file: clean strings, then lines
            fixed = scrub_json_strings(src, hb)
            return _scrub_lines(fixed, hb) if hb.mentions(fixed) else fixed
        compact = "\n" not in src.strip()
        return json.dumps(scrub_json(data, hb), ensure_ascii=False,
                          indent=None if compact else 2) + ("" if compact else "\n")
    if rel.endswith(".js"):
        m = _WINDOW_JSON.match(src)
        if m:
            try:
                data = json.loads(m.group(2))
                return m.group(1) + json.dumps(scrub_json(data, hb), ensure_ascii=False) + m.group(3)
            except json.JSONDecodeError:
                pass
        return scrub_js(src, hb)
    if rel.endswith(".txt"):
        return _scrub_lines(src, hb)
    return None  # .xml is handled by filter_sitemaps


def _scrub_lines(src: str, hb: HiddenBrands) -> str:
    kept = []
    for line in src.split("\n"):
        clean = scrub_text(line, hb) if hb.mentions(line) else line
        if hb.mentions(clean):  # e.g. a table row with no sentence to cut
            continue
        if clean.strip() or not line.strip():
            kept.append(clean)
    return "\n".join(kept)


# ── sitemaps / .htaccess ─────────────────────────────────────────────────────

def filter_sitemaps(root: Path, files: list[str], stubbed: set[str], hb: HiddenBrands) -> int:
    removed = 0
    for rel in (f for f in files if f.endswith(".xml")):
        src = _read(root, rel)

        def keep(m: re.Match) -> str:
            nonlocal removed
            loc = re.search(r"<loc>\s*(.*?)\s*</loc>", m.group(0), re.S)
            path = resolve_href(loc.group(1), "") if loc else None
            if (loc and hb.mentions(loc.group(1))) or path in stubbed:
                removed += 1
                return ""
            return m.group(0)

        new = re.sub(r"[ \t]*<url>.*?</url>\s*?\n?", keep, src, flags=re.S)
        if new != src:
            (root / rel).write_text(new, encoding="utf-8")
    return removed


def add_redirects(root: Path, redirects: dict[str, str]) -> None:
    ht = root / ".htaccess"
    if not redirects or not ht.exists():
        return
    lines = [HTACCESS_MARK]
    for d, target in sorted(redirects.items()):
        if _SAFE_PATH.match(d) and (not target or _SAFE_PATH.match(target)):
            lines.append(f"RedirectMatch 301 ^/{d[:-1]}/?$ /{target}")
    src = ht.read_text(encoding="utf-8")
    if HTACCESS_MARK not in src:
        ht.write_text(src.rstrip("\n") + "\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


# ── config drift (shared.js runtime filter must match the JSON) ──────────────

def config_drift(root: Path, hb: HiddenBrands) -> list[str]:
    js = (root / "assets" / "shared.js").read_text(encoding="utf-8")
    problems = []
    for const, expected in (("HIDDEN_BRAND_PATTERNS", list(hb.patterns)),
                            ("HIDDEN_BRAND_DOMAINS", list(hb.domains))):
        m = re.search(rf"const {const}=(\[[^\]]*\]);", js)
        if not m:
            problems.append(f"assets/shared.js has no {const}")
            continue
        found = json.loads(m.group(1).replace("'", '"'))
        if found != expected:
            problems.append(f"assets/shared.js {const} {found} != data/hidden_brands.json {expected}")
    return problems


# ── main ─────────────────────────────────────────────────────────────────────

def run_apply(root: Path, hb: HiddenBrands) -> None:
    files = deploy_files(root)
    html_files = [f for f in files if f.endswith(".html")]
    stubbed = find_stubs(root, html_files, hb)
    redirects = {d: stub_target(d, stubbed, root) for d in stubbed}
    for d, target in redirects.items():
        (root / d / "index.html").write_text(stub_html(target), encoding="utf-8")
    todo = [f for f in files if f[: -len("index.html")] not in stubbed or not f.endswith("index.html")]
    with Pool(initializer=_init_worker, initargs=(str(root), frozenset(stubbed), hb)) as pool:
        changed = sum(ok for _, ok in pool.imap_unordered(_scrub_file, todo, chunksize=16))
    dropped = filter_sitemaps(root, files, stubbed, hb)
    add_redirects(root, redirects)
    print(f"hidden brands: {len(hb.names)} brands | {len(stubbed)} pages redirected | "
          f"{changed} files scrubbed | {dropped} sitemap URLs dropped")


def run_check(root: Path, hb: HiddenBrands) -> int:
    problems = config_drift(root, hb)
    files = deploy_files(root)
    with Pool(initializer=_init_worker, initargs=(str(root), frozenset(), hb)) as pool:
        results = [r for r in pool.imap_unordered(_check_file, files, chunksize=16) if r[1]]
    for rel, leaks in sorted(results):
        problems.append(f"{rel}: {len(leaks)} mention(s), e.g. {leaks[0]}")
    for p in problems[:60]:
        print(f"  ✗ {p}")
    if problems:
        print(f"hidden brands: {len(problems)} problem(s) — brands would be visible on the live site")
        return 1
    print(f"hidden brands: OK — none of {len(hb.names)} hidden brands visible in {len(files)} files")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true", help="scrub the deploy copy in place")
    mode.add_argument("--check", action="store_true", help="fail if any hidden brand is visible")
    ap.add_argument("--root", type=Path, default=ROOT, help="site copy to process (default: repo)")
    ap.add_argument("--force", action="store_true", help="allow --apply on the repo outside CI")
    args = ap.parse_args()
    root = args.root.resolve()
    cfg = root / CONFIG_PATH.relative_to(ROOT)
    hb = load_config(cfg if cfg.exists() else CONFIG_PATH)
    if args.apply:
        if root == ROOT and not os.environ.get("CI") and not args.force:
            print("refusing to --apply on the working copy outside CI (it rewrites files). "
                  "Use --root <copy> or --force.", file=sys.stderr)
            return 2
        run_apply(root, hb)
        status = run_check(root, hb)
        # The list itself must not be published at /data/hidden_brands.json.
        (root / CONFIG_PATH.relative_to(ROOT)).unlink(missing_ok=True)
        return status
    return run_check(root, hb)


if __name__ == "__main__":
    sys.exit(main())
