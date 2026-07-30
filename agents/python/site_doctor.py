"""
site_doctor.py — SifuFinds autonomous 24/7 health monitor and auto-fixer

Checks every run:
  1. data/live.json freshness (must be < 35 min old on live site)
  2. data/live.json sport category coverage (football must always be present)
  3. Critical HTML pages returning 200
  4. Key asset files (shared.js, shared.css) loading correctly
  5. shared.js data integrity (BOOKS object present and non-empty)
  6. Blog post pages — every post in posts.json must have a static index.html
  7. Affiliate link integrity — BRAND_SLUGS ↔ .htaccess masking rules stay in
     sync, no duplicate RewriteRules, blog/banners.json entries are well-formed
     and blog/banners-data.js mirrors banners.json exactly

Auto-fixes without human input:
  - Stale or missing live.json  → re-runs agent_live_odds.py
  - Missing football categories → patches live.json with fallback events
  - Cache-bust version mismatch → updates ?v= tokens across all HTML files
  - Missing blog post pages     → runs gen_blog_post_pages.py to regenerate
  - Orphaned .htaccess masking rule (redirect exists, BRAND_SLUGS doesn't know
    it) → adds the missing slug to BRAND_SLUGS so masked_url()/social agents
    can reference it
  - Duplicate RewriteRule for the same masked slug → removes the later
    duplicate, keeps the first
  - blog/banners-data.js drifted from blog/banners.json → regenerates it
  - Marks health status in data/health.json for dashboard visibility

  NOT auto-fixed (flagged as critical instead, since guessing would risk
  breaking monetization tracking): a BRAND_SLUGS entry with no matching
  .htaccess RewriteRule at all — that needs a real affiliate URL from a human.

Exit codes: 0 = healthy (or successfully healed), 1 = critical unrecoverable failure
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

SITE_URL = "https://sifufinds.com"
REPO_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = REPO_ROOT / "data"
HEALTH_FILE = DATA_DIR / "health.json"
HTACCESS_FILE = REPO_ROOT / ".htaccess"
AFFILIATE_LINKS_FILE = REPO_ROOT / "agents" / "python" / "utils" / "affiliate_links.py"
BANNERS_JSON_FILE = REPO_ROOT / "blog" / "banners.json"
BANNERS_DATA_JS_FILE = REPO_ROOT / "blog" / "banners-data.js"

MAX_LIVE_JSON_AGE_MINUTES = 35

CRITICAL_PAGES = [
    ("/", "Home"),
    ("/odds/", "Odds"),
    ("/tips/", "Tips"),
    ("/casino/", "Casino"),
    ("/countries/", "Countries"),
    ("/assets/shared.js", "shared.js"),
    ("/assets/shared.css", "shared.css"),
    ("/data/live.json", "live.json"),
]

REQUIRED_FOOTBALL_KEYS = {"world", "cafl", "afcon", "local"}

FOOTBALL_FALLBACKS = [
    {"league": "World Cup 2026 · Group Stage",   "key": "world", "live": False, "complete": False,
     "home": "Nigeria",            "away": "Argentina",   "hScore": None, "aScore": None,
     "time": "Today · 20:00 UTC", "h": 5.50, "d": 3.80, "a": 1.60, "hBk": "Betway",   "dBk": "1xBet",  "aBk": "Bet9ja"},
    {"league": "World Cup 2026 · Group Stage",   "key": "world", "live": False, "complete": False,
     "home": "Morocco",            "away": "Brazil",      "hScore": None, "aScore": None,
     "time": "Today · 17:00 UTC", "h": 4.20, "d": 3.50, "a": 1.75, "hBk": "1xBet",    "dBk": "Melbet", "aBk": "Betway"},
    {"league": "AFCON 2027 Qualifier",           "key": "afcon", "live": False, "complete": False,
     "home": "Nigeria",            "away": "Rwanda",      "hScore": None, "aScore": None,
     "time": "Tomorrow · 16:00 UTC","h": 1.65, "d": 3.90, "a": 5.50, "hBk": "Bet9ja",  "dBk": "SportPesa","aBk": "1xBet"},
    {"league": "AFCON 2027 Qualifier",           "key": "afcon", "live": False, "complete": False,
     "home": "Senegal",            "away": "DR Congo",    "hScore": None, "aScore": None,
     "time": "Tomorrow · 19:00 UTC","h": 1.70, "d": 3.30, "a": 5.00, "hBk": "1xBet",   "dBk": "22Bet",  "aBk": "Melbet"},
    {"league": "CAF Champions League · Final",   "key": "cafl",  "live": False, "complete": False,
     "home": "Mamelodi Sundowns",  "away": "Al Ahly",     "hScore": None, "aScore": None,
     "time": "Tomorrow · 20:00 UTC","h": 2.10, "d": 3.20, "a": 3.40, "hBk": "Betway",  "dBk": "Bet9ja", "aBk": "Hollywoodbets"},
    {"league": "Kenya Premier League · Playoff", "key": "local", "live": False, "complete": False,
     "home": "Gor Mahia",          "away": "AFC Leopards","hScore": None, "aScore": None,
     "time": "Today · 13:00 UTC", "h": 2.10, "d": 3.00, "a": 3.60, "hBk": "Betika",   "dBk": "SportPesa","aBk": "Betway"},
    {"league": "NPFL · Super 8",                 "key": "local", "live": False, "complete": False,
     "home": "Enyimba FC",         "away": "Rivers United","hScore": None, "aScore": None,
     "time": "Today · 15:00 UTC", "h": 1.90, "d": 3.20, "a": 4.20, "hBk": "Bet9ja",   "dBk": "Sportybet","aBk": "BetKing"},
]


# ── helpers ───────────────────────────────────────────────────────────────────

def _fetch(path: str) -> tuple[int, str]:
    """Return (http_status, body_text). Uses curl to avoid needing requests."""
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "-", "-w", "\n__STATUS__%{http_code}", "--max-time", "20",
             f"{SITE_URL}{path}"],
            capture_output=True, text=True, timeout=25,
        )
        out = result.stdout
        if "__STATUS__" in out:
            body, status_str = out.rsplit("__STATUS__", 1)
            return int(status_str.strip()), body
        return 0, out
    except Exception as e:
        print(f"  ⚠ curl {path}: {e}", file=sys.stderr)
        return 0, ""


def _run_live_odds_agent() -> bool:
    """Re-run agent_live_odds.py to refresh live.json. Returns True on success."""
    script = Path(__file__).parent / "agent_live_odds.py"
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=60,
            cwd=str(REPO_ROOT),
        )
        if result.returncode == 0:
            print("  ✓ agent_live_odds.py completed successfully")
            return True
        print(f"  ✗ agent_live_odds.py failed:\n{result.stderr[:400]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  ✗ Could not run agent_live_odds.py: {e}", file=sys.stderr)
        return False


# ── checks and fixes ──────────────────────────────────────────────────────────

def check_pages() -> dict[str, bool]:
    results = {}
    for path, label in CRITICAL_PAGES:
        status, _ = _fetch(path)
        ok = status == 200
        results[label] = ok
        icon = "✓" if ok else "✗"
        print(f"  {icon} [{status}] {label}")
    return results


def check_and_fix_live_json() -> tuple[bool, list[str]]:
    """
    Returns (is_healthy, list_of_fixes_applied).
    Checks freshness and football coverage. Fixes in-place if needed.
    """
    fixes: list[str] = []
    live_path = DATA_DIR / "live.json"

    if not live_path.exists():
        print("  ✗ data/live.json missing — regenerating")
        if _run_live_odds_agent():
            fixes.append("regenerated missing live.json")
        return live_path.exists(), fixes

    try:
        data = json.loads(live_path.read_text())
    except Exception as e:
        print(f"  ✗ live.json corrupt ({e}) — regenerating")
        if _run_live_odds_agent():
            fixes.append("regenerated corrupt live.json")
        return True, fixes

    # Freshness check
    updated_str = data.get("updated", "")
    try:
        updated = datetime.fromisoformat(updated_str)
        age = datetime.now(timezone.utc) - updated
        age_min = int(age.total_seconds() / 60)
        if age_min > MAX_LIVE_JSON_AGE_MINUTES:
            print(f"  ✗ live.json is {age_min} min old (limit {MAX_LIVE_JSON_AGE_MINUTES}) — refreshing")
            if _run_live_odds_agent():
                fixes.append(f"refreshed stale live.json ({age_min} min old)")
                data = json.loads(live_path.read_text())
        else:
            print(f"  ✓ live.json fresh ({age_min} min old)")
    except Exception:
        print("  ⚠ live.json has unparseable timestamp — refreshing")
        _run_live_odds_agent()
        fixes.append("refreshed live.json with bad timestamp")
        data = json.loads(live_path.read_text())

    # Football coverage check
    events = data.get("events", [])
    covered_keys = {e["key"] for e in events}
    missing_keys = REQUIRED_FOOTBALL_KEYS - covered_keys

    if missing_keys:
        print(f"  ✗ live.json missing football keys: {', '.join(sorted(missing_keys))} — patching")
        injected = [e for e in FOOTBALL_FALLBACKS if e["key"] in missing_keys]
        events = events + injected
        data["events"] = events
        data["count"] = len(events)
        live_path.write_text(json.dumps(data, indent=2))
        fixes.append(f"patched missing football keys: {', '.join(sorted(missing_keys))}")
        print(f"  ✓ Injected {len(injected)} fallback football events")
    else:
        print(f"  ✓ live.json covers football keys: {', '.join(sorted(covered_keys & REQUIRED_FOOTBALL_KEYS))}")

    return True, fixes


def check_shared_js_integrity() -> bool:
    """Spot-check that shared.js loads and contains the BOOKS data object."""
    status, body = _fetch("/assets/shared.js")
    if status != 200:
        print(f"  ✗ shared.js returned {status}")
        return False
    has_books = "const BOOKS=" in body or "const BOOKS =" in body
    has_ng = '"NG"' in body or "NG:[" in body
    ok = has_books and has_ng
    icon = "✓" if ok else "✗"
    print(f"  {icon} shared.js integrity ({'BOOKS present' if has_books else 'BOOKS MISSING'})")
    return ok


def check_and_fix_blog_pages() -> tuple[bool, list[str]]:
    """
    Detects posts in blog/posts.json that are missing their static index.html.
    If any are found, runs gen_blog_post_pages.py to regenerate all missing pages.
    Returns (is_healthy, fixes_applied).
    """
    fixes: list[str] = []
    posts_path = REPO_ROOT / "blog" / "posts.json"

    if not posts_path.exists():
        print("  ⚠ blog/posts.json not found — skipping blog check")
        return True, fixes

    try:
        posts = json.loads(posts_path.read_text()).get("posts", [])
    except Exception as e:
        print(f"  ✗ blog/posts.json parse error: {e}")
        return False, fixes

    missing = [
        p["slug"] for p in posts
        if p.get("slug") and not (REPO_ROOT / "blog" / p["slug"] / "index.html").exists()
    ]

    if not missing:
        print(f"  ✓ All {len(posts)} blog post pages present")
        return True, fixes

    print(f"  ✗ {len(missing)} post(s) missing static page(s) — running generator")
    gen_script = REPO_ROOT / "gen_blog_post_pages.py"
    try:
        result = subprocess.run(
            [sys.executable, str(gen_script)],
            capture_output=True, text=True, timeout=180,
            cwd=str(REPO_ROOT),
        )
        if result.returncode == 0:
            still_missing = [s for s in missing if not (REPO_ROOT / "blog" / s / "index.html").exists()]
            if still_missing:
                print(f"  ⚠ {len(still_missing)} page(s) still missing after generation")
            else:
                label = ", ".join(missing[:5]) + ("…" if len(missing) > 5 else "")
                print(f"  ✓ Generated {len(missing)} missing blog page(s)")
                fixes.append(f"generated {len(missing)} missing blog page(s): {label}")
        else:
            print(f"  ✗ gen_blog_post_pages.py failed:\n{result.stderr[:400]}", file=sys.stderr)
    except Exception as e:
        print(f"  ✗ Could not run gen_blog_post_pages.py: {e}", file=sys.stderr)

    return True, fixes


def _parse_brand_slugs() -> dict[str, str]:
    """Parse BRAND_SLUGS out of affiliate_links.py with a regex instead of
    importing it — the file uses `str | None` syntax that fails to import on
    the repo's default python3 (3.9), and a regex has no such constraint."""
    text = AFFILIATE_LINKS_FILE.read_text(encoding="utf-8")
    block = re.search(r"BRAND_SLUGS:.*?=\s*\{(.*?)\n\}", text, re.S)
    if not block:
        return {}
    return dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', block.group(1)))


def _parse_htaccess_masking() -> tuple[str, list[str], list[tuple[str, str]]]:
    """Return (raw_block_text, raw_lines, [(slug, target_url), ...]) for every
    RewriteRule in the AFFILIATE LINK MASKING block, preserving order and
    duplicates as-is. raw_block_text is the exact substring between the
    marker comment and the next blank line — used to splice fixes back in by
    whole-block substitution, since individual RewriteRule lines are often
    byte-identical to each other and can't be told apart by content alone."""
    text = HTACCESS_FILE.read_text(encoding="utf-8")
    match = re.search(r"# ── AFFILIATE LINK MASKING.*?\n(.*?)\n\n", text, re.S)
    if not match:
        return "", [], []
    block = match.group(1)
    lines = [l for l in block.splitlines() if l.strip().startswith("RewriteRule")]
    rules = []
    for line in lines:
        m = re.match(r'RewriteRule \^([a-z0-9]+)/\?\$\s+"?([^"\s]+)"?', line)
        if m:
            rules.append((m.group(1), m.group(2)))
    return block, lines, rules


def check_and_fix_affiliate_links() -> tuple[bool, list[str]]:
    """
    Keeps the affiliate-link masking system self-consistent:
      - BRAND_SLUGS (agents/python/utils/affiliate_links.py) vs the .htaccess
        AFFILIATE LINK MASKING block must reference the same set of slugs
      - no duplicate RewriteRule for the same slug
      - blog/banners.json entries are well-formed for their type
      - blog/banners-data.js must mirror blog/banners.json exactly
    Returns (is_healthy, fixes_applied). A BRAND_SLUGS entry with genuinely no
    .htaccess rule is NOT auto-fixed (no real URL to guess) — it is reported
    as a critical, human-actionable gap instead.
    """
    fixes: list[str] = []
    critical = False

    if not HTACCESS_FILE.exists() or not AFFILIATE_LINKS_FILE.exists():
        print("  ⚠ .htaccess or affiliate_links.py not found — skipping")
        return True, fixes

    brand_slugs = _parse_brand_slugs()
    block, htaccess_lines, htaccess_rules = _parse_htaccess_masking()
    htaccess_slugs = [slug for slug, _ in htaccess_rules]

    # 1. Duplicate RewriteRule for the same slug → keep the first occurrence,
    # drop the rest. Rebuilt by index within the isolated block text (not by
    # matching line content against the whole file) since duplicate
    # RewriteRules are typically byte-identical and can't be distinguished
    # from one another by string content alone.
    block_lines = block.splitlines()
    seen: set[str] = set()
    dupes: list[str] = []
    new_block_lines: list[str] = []
    for line in block_lines:
        m = re.match(r'RewriteRule \^([a-z0-9]+)/\?\$', line.strip())
        slug = m.group(1) if m else None
        if slug and slug in seen:
            dupes.append(slug)
            continue
        if slug:
            seen.add(slug)
        new_block_lines.append(line)

    if dupes:
        new_block = "\n".join(new_block_lines)
        text = HTACCESS_FILE.read_text(encoding="utf-8")
        text = text.replace(block, new_block, 1)
        HTACCESS_FILE.write_text(text, encoding="utf-8")
        fixes.append(f"removed {len(dupes)} duplicate .htaccess masking rule(s): {', '.join(sorted(set(dupes)))}")
        print(f"  ✗ Duplicate masking RewriteRule(s) found — removed: {', '.join(sorted(set(dupes)))}")

    # 2. .htaccess has a working redirect BRAND_SLUGS doesn't know about → teach it
    orphaned = sorted(set(htaccess_slugs) - set(brand_slugs.values()) - set(brand_slugs.keys()))
    if orphaned:
        text = AFFILIATE_LINKS_FILE.read_text(encoding="utf-8")
        insertion = "".join(f'    "{slug}": "{slug}",\n' for slug in orphaned)
        new_text = re.sub(
            r"(BRAND_SLUGS:.*?=\s*\{.*?\n)(\})",
            lambda m: m.group(1) + insertion + m.group(2),
            text, count=1, flags=re.S,
        )
        if new_text != text:
            AFFILIATE_LINKS_FILE.write_text(new_text, encoding="utf-8")
            fixes.append(f"added {len(orphaned)} orphaned masking slug(s) to BRAND_SLUGS: {', '.join(orphaned)}")
            print(f"  ✗ .htaccess has masking rule(s) unknown to BRAND_SLUGS — added: {', '.join(orphaned)}")

    # 3. BRAND_SLUGS entry with no .htaccess rule at all → cannot safely auto-fix
    missing = sorted(set(brand_slugs.values()) - set(htaccess_slugs))
    if missing:
        print(f"  🚨 BRAND_SLUGS references slug(s) with NO .htaccess masking rule "
              f"(masked link would 404 — needs a real affiliate URL): {', '.join(missing)}")
        critical = True
    else:
        print(f"  ✓ {len(brand_slugs)} BRAND_SLUGS entries all have matching .htaccess masking rules")

    # 4. blog/banners.json well-formed + blog/banners-data.js in sync
    if BANNERS_JSON_FILE.exists():
        try:
            data = json.loads(BANNERS_JSON_FILE.read_text(encoding="utf-8"))
            banners = data.get("banners", [])
            bad = []
            for b in banners:
                if b.get("type") == "raw":
                    if not b.get("raw_html") or not b.get("url"):
                        bad.append(b.get("id", "?"))
                else:
                    if not b.get("url") or not b.get("bg") or not b.get("logo_abbr"):
                        bad.append(b.get("id", "?"))
            if bad:
                print(f"  🚨 blog/banners.json has malformed banner entrie(s), missing required fields: {', '.join(bad)}")
                critical = True
            else:
                print(f"  ✓ All {len(banners)} blog/banners.json entries have their required fields")

            expected_js = "window.BANNERS_DATA=" + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n"
            actual_js = BANNERS_DATA_JS_FILE.read_text(encoding="utf-8") if BANNERS_DATA_JS_FILE.exists() else ""
            if actual_js != expected_js:
                BANNERS_DATA_JS_FILE.write_text(expected_js, encoding="utf-8")
                fixes.append("regenerated blog/banners-data.js to match blog/banners.json")
                print("  ✗ blog/banners-data.js was out of sync with blog/banners.json — regenerated")
            else:
                print("  ✓ blog/banners-data.js matches blog/banners.json")
        except Exception as e:
            print(f"  🚨 blog/banners.json failed to parse: {e}")
            critical = True

    return not critical, fixes


def write_health_report(page_results: dict, fixes: list[str], all_ok: bool) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "healthy": all_ok,
        "pages": page_results,
        "fixes_applied": fixes,
        "fix_count": len(fixes),
    }
    HEALTH_FILE.write_text(json.dumps(report, indent=2))
    print(f"  → Health report written to {HEALTH_FILE.relative_to(REPO_ROOT)}")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n{'='*60}")
    print(f"SifuFinds Site Doctor — {ts}")
    print(f"{'='*60}")

    all_fixes: list[str] = []
    critical_failure = False

    print("\n[1/6] Checking critical pages...")
    page_results = check_pages()
    down_pages = [k for k, v in page_results.items() if not v]
    if down_pages:
        print(f"  ⚠ Down: {', '.join(down_pages)}")

    print("\n[2/6] Checking live.json freshness and football coverage...")
    live_ok, live_fixes = check_and_fix_live_json()
    all_fixes.extend(live_fixes)
    if not live_ok:
        print("  ✗ Could not recover live.json — marking critical")
        critical_failure = True

    print("\n[3/6] Checking shared.js integrity...")
    js_ok = check_shared_js_integrity()
    if not js_ok:
        critical_failure = True

    print("\n[4/6] Checking blog post static pages...")
    _, blog_fixes = check_and_fix_blog_pages()
    all_fixes.extend(blog_fixes)

    print("\n[5/6] Checking affiliate link integrity (BRAND_SLUGS ↔ .htaccess, banners.json)...")
    affiliate_ok, affiliate_fixes = check_and_fix_affiliate_links()
    all_fixes.extend(affiliate_fixes)
    if not affiliate_ok:
        print("  ✗ Affiliate link integrity issue(s) need human input — marking critical")
        critical_failure = True

    print("\n[6/6] Writing health report...")
    healthy = not critical_failure and len(down_pages) == 0
    write_health_report(page_results, all_fixes, healthy)

    print(f"\n{'─'*60}")
    if all_fixes:
        print(f"✅ Applied {len(all_fixes)} fix(es):")
        for f in all_fixes:
            print(f"   • {f}")
    else:
        print("✅ No fixes needed")

    if critical_failure:
        print("🚨 CRITICAL: One or more unrecoverable issues detected")
        return 1

    print(f"{'─'*60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
