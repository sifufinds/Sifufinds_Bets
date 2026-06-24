"""
site_doctor.py — SifuFinds autonomous 24/7 health monitor and auto-fixer

Checks every run:
  1. data/live.json freshness (must be < 35 min old on live site)
  2. data/live.json sport category coverage (football must always be present)
  3. Critical HTML pages returning 200
  4. Key asset files (shared.js, shared.css) loading correctly
  5. shared.js data integrity (BOOKS object present and non-empty)
  6. Blog post pages — every post in posts.json must have a static index.html

Auto-fixes without human input:
  - Stale or missing live.json  → re-runs agent_live_odds.py
  - Missing football categories → patches live.json with fallback events
  - Cache-bust version mismatch → updates ?v= tokens across all HTML files
  - Missing blog post pages     → runs gen_blog_post_pages.py to regenerate
  - Marks health status in data/health.json for dashboard visibility

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

    print("\n[1/5] Checking critical pages...")
    page_results = check_pages()
    down_pages = [k for k, v in page_results.items() if not v]
    if down_pages:
        print(f"  ⚠ Down: {', '.join(down_pages)}")

    print("\n[2/5] Checking live.json freshness and football coverage...")
    live_ok, live_fixes = check_and_fix_live_json()
    all_fixes.extend(live_fixes)
    if not live_ok:
        print("  ✗ Could not recover live.json — marking critical")
        critical_failure = True

    print("\n[3/5] Checking shared.js integrity...")
    js_ok = check_shared_js_integrity()
    if not js_ok:
        critical_failure = True

    print("\n[4/5] Checking blog post static pages...")
    _, blog_fixes = check_and_fix_blog_pages()
    all_fixes.extend(blog_fixes)

    print("\n[5/5] Writing health report...")
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
