"""
SifuFinds Traffic Report Agent — Google Analytics 4 + Search Console edition
Pulls page views, top pages, traffic sources, countries (GA4) and search
impressions/clicks/queries (Search Console) into one Markdown report so
Claude can read it in any session.

Setup (one-time, ~10 minutes):
  1. Google Cloud Console (console.cloud.google.com) → create/select a project
     → enable "Google Analytics Data API" and "Google Search Console API".
  2. IAM & Admin → Service Accounts → Create service account → Keys → Add key
     → JSON. Download the key file.
  3. GA4 (analytics.google.com) → Admin → Property Access Management → add
     the service account's email (looks like xxx@yyy.iam.gserviceaccount.com)
     as a Viewer.
  4. Search Console (search.google.com/search-console) → Settings → Users
     and permissions → Add user → paste the service account's email → Full
     (or Restricted) access.
  5. Set environment variables (locally in agents/python/.env, in CI as
     GitHub secrets):
       GA4_PROPERTY_ID           = 123456789          (numeric GA4 property ID)
       GSC_SITE_URL              = https://sifufinds.com/   (or sc-domain:sifufinds.com)
       GOOGLE_SERVICE_ACCOUNT_JSON = <paste the whole key file's JSON content>
     (CI can instead write the secret to a file and set
     GOOGLE_APPLICATION_CREDENTIALS to its path — both are supported here.)

Usage:
  python agent_traffic_report.py              # last 30 days
  python agent_traffic_report.py --days 7
  python agent_traffic_report.py --days 90
"""

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID", "").strip()
GSC_SITE_URL    = os.getenv("GSC_SITE_URL", "").strip()
SA_JSON_RAW     = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
SA_JSON_PATH    = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/webmasters.readonly",
]

REPORT_MD   = Path(__file__).parent / "traffic_report.md"
REPORT_JSON = Path(__file__).parent / "traffic_report.json"


def is_configured() -> bool:
    return bool(GA4_PROPERTY_ID and GSC_SITE_URL and (SA_JSON_RAW or SA_JSON_PATH))


def _property_name() -> str:
    return GA4_PROPERTY_ID if GA4_PROPERTY_ID.startswith("properties/") else f"properties/{GA4_PROPERTY_ID}"


def _credentials():
    from google.oauth2 import service_account

    if SA_JSON_PATH:
        return service_account.Credentials.from_service_account_file(SA_JSON_PATH, scopes=SCOPES)
    return service_account.Credentials.from_service_account_info(json.loads(SA_JSON_RAW), scopes=SCOPES)


def _date_range(days: int) -> tuple[str, str]:
    end   = date.today()
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()


# ── GA4 ────────────────────────────────────────────────────────────────────

def fetch_ga4(days: int, creds) -> dict:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy, RunReportRequest

    client = BetaAnalyticsDataClient(credentials=creds)
    start, end = _date_range(days)
    date_range = DateRange(start_date=start, end_date=end)

    def run(dimensions, metrics, order_metric=None, limit=25):
        try:
            req = RunReportRequest(
                property=_property_name(),
                dimensions=[Dimension(name=d) for d in dimensions],
                metrics=[Metric(name=m) for m in metrics],
                date_ranges=[date_range],
                limit=limit,
            )
            if order_metric:
                req.order_bys.append(OrderBy(metric=OrderBy.MetricOrderBy(metric_name=order_metric), desc=True))
            resp = client.run_report(req)
            rows = []
            for row in resp.rows:
                rec = {}
                for i, d in enumerate(dimensions):
                    rec[d] = row.dimension_values[i].value
                for i, m in enumerate(metrics):
                    rec[m] = row.metric_values[i].value
                rows.append(rec)
            return rows
        except Exception as e:
            print(f"[traffic] WARN: GA4 query {dimensions}/{metrics} failed — {e}", file=sys.stderr)
            return []

    daily     = run(["date"], ["screenPageViews"], limit=days + 1)
    pages     = run(["pagePath"], ["screenPageViews", "totalUsers"], order_metric="screenPageViews", limit=25)
    sources   = run(["sessionDefaultChannelGroup"], ["sessions"], order_metric="sessions", limit=15)
    countries = run(["country"], ["activeUsers"], order_metric="activeUsers", limit=15)
    totals    = run([], ["screenPageViews", "sessions", "totalUsers"], limit=1)

    daily.sort(key=lambda r: r.get("date", ""))
    return {"daily": daily, "pages": pages, "sources": sources, "countries": countries, "totals": totals}


# ── Search Console ───────────────────────────────────────────────────────────

def fetch_search_console(days: int, creds) -> dict:
    from googleapiclient.discovery import build

    service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    start, end = _date_range(days)

    def query(dimensions, row_limit=20):
        try:
            body = {"startDate": start, "endDate": end, "dimensions": dimensions, "rowLimit": row_limit}
            resp = service.searchanalytics().query(siteUrl=GSC_SITE_URL, body=body).execute()
            return resp.get("rows", [])
        except Exception as e:
            print(f"[traffic] WARN: Search Console query {dimensions} failed — {e}", file=sys.stderr)
            return []

    totals  = query([], row_limit=1)
    queries = query(["query"], row_limit=20)
    pages   = query(["page"], row_limit=20)
    return {"totals": totals, "queries": queries, "pages": pages}


# ── Report builder ───────────────────────────────────────────────────────────

def build_report(days: int, ga4: dict, gsc: dict) -> str:
    today = date.today().isoformat()
    start = (date.today() - timedelta(days=days)).isoformat()

    totals = ga4["totals"][0] if ga4["totals"] else {}
    pv      = int(totals.get("screenPageViews", 0))
    sessions = int(totals.get("sessions", 0))
    users   = int(totals.get("totalUsers", 0))

    gsc_totals = gsc["totals"][0] if gsc["totals"] else {}
    clicks      = round(gsc_totals.get("clicks", 0))
    impressions = round(gsc_totals.get("impressions", 0))
    ctr         = round(gsc_totals.get("ctr", 0) * 100, 2)
    position    = round(gsc_totals.get("position", 0), 1)

    lines = [
        "# SifuFinds Traffic Report",
        f"**Period:** {start} → {today} ({days} days)  ·  **Generated:** {today}",
        f"**Source:** Google Analytics 4 + Search Console · sifufinds.com",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Page Views (GA4) | {pv:,} |",
        f"| Sessions (GA4) | {sessions:,} |",
        f"| Users (GA4) | {users:,} |",
        f"| Avg Views/Day | {round(pv / max(days, 1)):,} |",
        f"| Search Clicks (GSC) | {clicks:,} |",
        f"| Search Impressions (GSC) | {impressions:,} |",
        f"| Search CTR | {ctr}% |",
        f"| Avg Search Position | {position} |",
        "",
    ]

    if ga4["pages"]:
        lines += ["## Top Pages (GA4)", "", "| Page | Views | Users |", "|------|-------|-------|"]
        for p in ga4["pages"]:
            lines.append(f"| {p.get('pagePath', '/')} | {int(p.get('screenPageViews', 0)):,} | {int(p.get('totalUsers', 0)):,} |")
        lines += [""]

    if ga4["sources"]:
        lines += ["## Traffic Sources (GA4)", "", "| Channel | Sessions |", "|---------|----------|"]
        for s in ga4["sources"]:
            lines.append(f"| {s.get('sessionDefaultChannelGroup', 'Unknown')} | {int(s.get('sessions', 0)):,} |")
        lines += [""]

    if ga4["countries"]:
        lines += ["## Countries (GA4)", "", "| Country | Users |", "|---------|-------|"]
        for c in ga4["countries"]:
            lines.append(f"| {c.get('country', 'Unknown')} | {int(c.get('activeUsers', 0)):,} |")
        lines += [""]

    if gsc["queries"]:
        lines += ["## Top Search Queries (Search Console)", "", "| Query | Clicks | Impressions | CTR | Avg Position |", "|-------|--------|--------------|-----|--------------|"]
        for q in gsc["queries"]:
            keys = q.get("keys", ["–"])
            lines.append(
                f"| {keys[0]} | {round(q.get('clicks', 0)):,} | {round(q.get('impressions', 0)):,} | "
                f"{round(q.get('ctr', 0) * 100, 1)}% | {round(q.get('position', 0), 1)} |"
            )
        lines += [""]

    daily = ga4["daily"][-14:] if len(ga4["daily"]) > 14 else ga4["daily"]
    if daily:
        lines += ["## Daily Trend (last 14 days, GA4)", "", "| Date | Views |", "|------|-------|"]
        for d in daily:
            lines.append(f"| {d.get('date', '–')} | {int(d.get('screenPageViews', 0)):,} |")
        lines += [""]

    lines += [
        "---",
        f"*Auto-generated by agent_traffic_report.py · GA4 property {GA4_PROPERTY_ID} · GSC {GSC_SITE_URL}*",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    if not is_configured():
        print(
            "[traffic] GA4_PROPERTY_ID / GSC_SITE_URL / GOOGLE_SERVICE_ACCOUNT_JSON not fully set — "
            "skipping (not a failure). See the setup steps in this file's docstring."
        )
        sys.exit(0)

    creds = _credentials()

    print(f"[traffic] Fetching last {args.days} days from GA4 ({GA4_PROPERTY_ID}) and Search Console ({GSC_SITE_URL})…")

    ga4 = fetch_ga4(args.days, creds)
    gsc = fetch_search_console(args.days, creds)

    if not ga4["totals"] and not gsc["totals"]:
        sys.exit("ERROR: Both GA4 and Search Console returned no data — check property/site IDs and that the service account has been granted access to both.")

    report = build_report(args.days, ga4, gsc)
    raw = {"days": args.days, "ga4": ga4, "search_console": gsc}

    REPORT_MD.write_text(report, encoding="utf-8")
    REPORT_JSON.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    total_pv = int(ga4["totals"][0].get("screenPageViews", 0)) if ga4["totals"] else 0
    print(f"[traffic] {total_pv:,} page views · {len(ga4['pages'])} pages · {len(gsc['queries'])} search queries")
    print(f"[traffic] Saved → {REPORT_MD.name}")
    print("\n" + report)


if __name__ == "__main__":
    main()
