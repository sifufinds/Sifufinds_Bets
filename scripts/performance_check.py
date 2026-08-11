#!/usr/bin/env python3
"""Performance & Core Web Vitals guard for sifufinds.com.

No Lighthouse/PageSpeed automation existed anywhere in this repo before this
script (confirmed by grep during the 2026-07-30 agent-team roadmap audit).
Uses Google's free PageSpeed Insights API v5 (no API key required at the
check volume here — a PAGESPEED_API_KEY env var is honoured if set, for a
higher rate limit, but never required) against a small set of representative
LIVE pages, since Core Web Vitals are inherently measured against a real
deployed URL, not local generated HTML the way the other scripts/*.py
checkers work.

Targets match the CWV targets already documented in this repo's coding
standards: LCP < 2.5s, CLS < 0.1, FCP < 1.5s, TBT < 200ms (lab-data proxy for
INP, since INP field data needs more real-user traffic than this site
reliably has yet — see _extract_metrics()'s docstring).

This is a monitoring check, not a pre-deploy gate — deploy_hostinger.yml
pushes new content to the SAME live URLs this script measures, so probing
mid-deploy would just measure a race, not a real signal. Runs on its own
schedule instead (performance_check.yml). A single slow page (CRITICAL/WARN
on one metric) still exits 0 — that's a real CWV regression worth a human
looking at, not an infrastructure failure, and shouldn't fail the scheduled
job. But "0/N pages returned any data at all" (the ALL_PAGES case) is a
total pipeline failure, not a performance signal — confirmed live 2026-08-07
through at least 2026-08-11 (five straight days of HTTP 429 from PageSpeed's
free unauthenticated quota, no PAGESPEED_API_KEY secret configured) reporting
workflow "success" every single day because this always returned 0
regardless. Fixed 2026-08-11 (technical SEO audit): the ALL_PAGES case now
exits 1, so the scheduled job actually shows red and this repo's existing
auto-retry infrastructure (workflow_watchdog.yml / retry_failed.yml, which
already watches every workflow — see CLAUDE.md's Auto-Retry standing rule)
picks it up instead of it staying invisible in a log nobody opens.

Usage:
    python3 scripts/performance_check.py            # check + report
    python3 scripts/performance_check.py --report    # also write performance-report.json
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HISTORY_PATH = ROOT / "data" / "performance_history.json"
PAGESPEED_API_KEY = os.getenv("PAGESPEED_API_KEY", "")

CRITICAL = "CRITICAL"
WARN = "WARN"

# Targets from this repo's documented Core Web Vitals standards.
TARGETS = {
    "lcp_s": 2.5,
    "cls": 0.1,
    "fcp_s": 1.5,
    "tbt_ms": 200,
}
# A metric this far past target is worth blocking attention on (CRITICAL);
# anything past target but under this multiplier is WARN.
CRITICAL_MULTIPLIER = 1.6

# Representative pages, not every page — a Lighthouse run takes 15-30s each,
# so this stays small enough to run in a few minutes: homepage (heaviest
# traffic), one bookmaker review (template used by 20+ pages), one country
# page, one blog post, and the two core comparison tools.
CHECK_PAGES = {
    "homepage": "https://sifufinds.com/",
    "bookmaker_review": "https://sifufinds.com/bookmakers/bet9ja/",
    "country_page": "https://sifufinds.com/countries/nigeria/",
    "tips": "https://sifufinds.com/tips/",
    "odds": "https://sifufinds.com/odds/",
}

MAX_HISTORY_PER_PAGE = 90

issues: list[dict] = []


def issue(severity: str, page_key: str, detail: str) -> None:
    issues.append({"severity": severity, "page": page_key, "detail": detail})


def _fetch_pagespeed(url: str, strategy: str = "mobile") -> dict:
    params = {"url": url, "strategy": strategy, "category": "performance"}
    if PAGESPEED_API_KEY:
        params["key"] = PAGESPEED_API_KEY
    api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(api_url, headers={"User-Agent": "SifuFinds-Performance-Check/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _extract_metrics(data: dict) -> dict | None:
    """Pull LCP/CLS/FCP/TBT from Lighthouse lab data. TBT stands in for INP
    here — Lighthouse's lab environment can't measure real interaction
    latency, and this site doesn't yet have enough CrUX field traffic for
    INTERACTION_TO_NEXT_PAINT to be populated reliably in loadingExperience,
    so TBT (a lab-measurable proxy correlated with INP) is what's checked
    against the 200ms target instead."""
    audits = data.get("lighthouseResult", {}).get("audits", {})
    if not audits:
        return None
    try:
        return {
            "lcp_s": round(audits["largest-contentful-paint"]["numericValue"] / 1000, 2),
            "cls": round(audits["cumulative-layout-shift"]["numericValue"], 3),
            "fcp_s": round(audits["first-contentful-paint"]["numericValue"] / 1000, 2),
            "tbt_ms": round(audits["total-blocking-time"]["numericValue"], 0),
            "performance_score": round(data["lighthouseResult"]["categories"]["performance"]["score"] * 100),
        }
    except (KeyError, TypeError):
        return None


def _load_history() -> dict:
    if HISTORY_PATH.exists():
        try:
            return json.loads(HISTORY_PATH.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def _save_history(history: dict) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history, indent=2))


def check_page(page_key: str, url: str, history: dict) -> dict | None:
    print(f"  → {page_key} ({url})")
    try:
        data = _fetch_pagespeed(url)
    except (urllib.error.URLError, TimeoutError) as e:
        issue(WARN, page_key, f"PageSpeed API request failed: {e}")
        print(f"    ✗ request failed: {e}")
        return None

    metrics = _extract_metrics(data)
    if metrics is None:
        issue(WARN, page_key, "PageSpeed response missing expected Lighthouse audit fields")
        print("    ✗ could not extract metrics from response")
        return None

    print(f"    score={metrics['performance_score']} LCP={metrics['lcp_s']}s "
          f"CLS={metrics['cls']} FCP={metrics['fcp_s']}s TBT={metrics['tbt_ms']}ms")

    for metric_key, target in TARGETS.items():
        value = metrics[metric_key]
        if value <= target:
            continue
        severity = CRITICAL if value > target * CRITICAL_MULTIPLIER else WARN
        issue(severity, page_key, f"{metric_key}={value} exceeds target {target} ({url})")

    entry = {"date": datetime.now(timezone.utc).date().isoformat(), **metrics}
    history.setdefault(page_key, []).append(entry)
    history[page_key] = history[page_key][-MAX_HISTORY_PER_PAGE:]
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--pages", nargs="*", help="Subset of CHECK_PAGES keys to check (default: all)")
    args = parser.parse_args()

    print("=" * 70)
    print("SifuFinds Performance & Core Web Vitals guard")
    print("=" * 70)

    pages = {k: v for k, v in CHECK_PAGES.items() if not args.pages or k in args.pages}
    history = _load_history()

    checked = 0
    for page_key, url in pages.items():
        if check_page(page_key, url, history) is not None:
            checked += 1

    _save_history(history)

    # Total-outage escalation (added 2026-08-07): found live that this check
    # had been reporting workflow "success" every day for a full week
    # (2026-08-01 through 2026-08-07) while silently recording zero real
    # data — every one of the 5 pages hit HTTP 429 from Google's PageSpeed
    # API (no PAGESPEED_API_KEY secret configured, so requests run against
    # the free unauthenticated quota, which GitHub Actions' shared runner
    # IP pool exhausts easily). Each individual failure was only ever a WARN
    # per-page, indistinguishable in the log/history from "this one page had
    # a slow metric" — nothing escalated "0/5 pages produced any data at
    # all" to something a human would actually notice. That silent-failure
    # shape is exactly what this repo's error-handling rules exist to catch.
    total_outage = bool(pages) and checked == 0
    if total_outage:
        issue(
            CRITICAL,
            "ALL_PAGES",
            f"0/{len(pages)} pages returned any PageSpeed data this run — the monitor is "
            "producing zero real data, not just failing one metric. Most likely cause: no "
            "PAGESPEED_API_KEY secret configured, so requests run against Google's free "
            "unauthenticated quota and get rate-limited (429) by GitHub Actions' shared "
            "runner IPs. Fix: create a key at https://console.cloud.google.com "
            "(enable 'PageSpeed Insights API', free tier), then `gh secret set "
            "PAGESPEED_API_KEY`.",
        )

    critical = [i for i in issues if i["severity"] == CRITICAL]
    warnings = [i for i in issues if i["severity"] == WARN]

    print("\n" + "=" * 70)
    print(f"Summary: {len(critical)} critical | {len(warnings)} warnings")
    if critical:
        print("\nCRITICAL (well past target — worth investigating):")
        for i in critical:
            print(f"  ✗ [{i['page']}] {i['detail']}")
    if warnings:
        print("\nWarnings:")
        for i in warnings:
            print(f"  ⚠ [{i['page']}] {i['detail']}")
    print("=" * 70)

    if args.report:
        report_path = ROOT / "performance-report.json"
        report_path.write_text(json.dumps({
            "critical": len(critical), "warnings": len(warnings), "issues": issues,
        }, indent=2))
        print(f"Report saved to {report_path.name}")

    if not critical and not warnings:
        print("\n✅ All checked pages within Core Web Vitals targets")

    # A single slow-metric CRITICAL/WARN still exits 0 — that's a real CWV
    # regression for a human to look at, not an infra failure, and this is a
    # monitoring check, not a pre-deploy gate (see module docstring). But a
    # total outage (0/N pages returned any data) exits 1 so the scheduled
    # job goes red and this repo's auto-retry infrastructure catches it
    # instead of it silently reporting "success" every day (see ALL_PAGES
    # above, and CLAUDE.md's Auto-Retry standing rule).
    return 1 if total_outage else 0


if __name__ == "__main__":
    sys.exit(main())
