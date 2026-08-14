#!/usr/bin/env python3
"""
SifuFinds Email Outreach Agent
Sends personalised outreach emails to the 101 identified backlink prospects
in backlink_opportunities.json.

Targets: sports news sites, betting guides, African football blogs.
Goal: get a mention/link from each site — either a citation in an existing
article or coverage of SifuFinds' free tools.

Requires GitHub secrets:
  OUTREACH_EMAIL_USER  — Gmail address to send from (e.g. kai.s.manyeh@gmail.com)
  OUTREACH_EMAIL_PASS  — Gmail App Password (not your main password)
                         Create at: myaccount.google.com/apppasswords

Usage:
  python agent_email_outreach.py             # send next batch (max 5/day)
  python agent_email_outreach.py --dry-run   # preview emails without sending
  python agent_email_outreach.py --limit 3   # send max 3 this run
"""
import argparse
import json
import os
import smtplib
import sys
import time
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

ROOT              = Path(__file__).resolve().parents[2]
PROSPECTS_FILE    = Path(__file__).parent / "backlink_opportunities.json"
STATE_FILE        = Path(__file__).parent / "email_outreach_state.json"

SENDER_EMAIL      = os.getenv("OUTREACH_EMAIL_USER", "kai.s.manyeh@gmail.com")
SENDER_NAME       = "Sifu Kai — SifuFinds"
SITE_URL          = "https://sifufinds.com"
TOOLS_URL         = f"{SITE_URL}/tools/"
PRESS_URL         = f"{SITE_URL}/press/"

# Max emails per run and per day total (stay under Gmail limits)
MAX_PER_RUN       = 5
MAX_PER_DAY       = 10
SMTP_HOST         = "smtp.gmail.com"
SMTP_PORT         = 587
DELAY_BETWEEN     = 8   # seconds between sends

# ── EMAIL TEMPLATES ────────────────────────────────────────────────────────────
# Keyed by link_type / niche from backlink_opportunities.json

TEMPLATES = {
    "digital PR": {
        "subject": "Data partnership idea — African sports betting statistics",
        "body": """\
Hi {site_name} team,

I run SifuFinds ({site_url}) — Africa's independent betting comparison platform covering
28 countries including Nigeria, Kenya, Ghana, South Africa and Tanzania.

I noticed {site_name} covers {niche} in Africa, and I think our verified data could be
useful to your readers.

What we have that might interest you:
• Live bookmaker bonus data across 28 African markets (updated daily)
• Country-by-country breakdown of licensed operators and regulators
• Free tools: odds calculator and parlay calculator built for African bettors

I'd love to contribute data or a quote for any future articles you're writing on
African sports betting — no charge, just happy to be cited as a source.

Our press kit is at: {press_url}

Is there a relevant piece coming up where our data would help?

Best regards,
Sifu Kai
SifuFinds — Africa's Betting Comparison
{site_url}
""",
    },

    "sports news": {
        "subject": "Free betting tools for your African football readers",
        "body": """\
Hi {site_name} team,

Big fan of your coverage of African football.

I built two free tools for African sports bettors that might be useful to link in your
betting-related articles:

1. Odds Calculator — converts decimal/fractional/American odds and calculates payouts
   in Nigerian Naira, Kenyan Shillings, Ghanaian Cedi and South African Rand.
   Link: {site_url}/tools/odds-calculator/

2. Parlay/Accumulator Calculator — add up to 20 legs, see combined odds and total payout.
   Link: {site_url}/tools/parlay-calculator/

Both are completely free, no signup required, and built specifically for African bettors
using Bet9ja, Betway, 1xBet and SportyBet.

If you're covering WC2026 betting guides or bookmaker roundups, I'd be happy to provide
data or a mention would be much appreciated.

Best,
Sifu Kai
SifuFinds ({site_url})
""",
    },

    "betting guide": {
        "subject": "Collaboration idea — SifuFinds x {site_name}",
        "body": """\
Hi {site_name} team,

I run SifuFinds ({site_url}), an independent betting comparison platform focused on
African markets — we cover 28 countries and compare 7+ licensed bookmakers.

I came across {site_name} while researching {niche} content and thought there might
be a good fit for cross-linking or data sharing.

What we offer:
• Verified bonus data updated daily
• Regulator and licensing information for every African market
• Free tools: {site_url}/tools/ (odds converter + parlay calculator)
• 296 expert articles on African betting

If you ever write about bookmakers available in Africa or need a reliable data source
for bonus comparisons, I'd love to be cited.

Equally happy to link to relevant {site_name} content from our own articles.

Cheers,
Sifu Kai
SifuFinds — Africa's Betting Comparison
{site_url}
""",
    },

    "default": {
        "subject": "SifuFinds — free African betting data & tools for your readers",
        "body": """\
Hi {site_name} team,

My name is Sifu Kai and I run SifuFinds ({site_url}), Africa's independent sports
betting comparison platform.

We cover 28 African countries with verified bookmaker bonuses, live odds, free daily
tips, and country-specific regulatory guides.

I also recently built two free tools that African bettors have found useful:
• Odds Calculator: {site_url}/tools/odds-calculator/
• Parlay/Accumulator Calculator: {site_url}/tools/parlay-calculator/

If any of this data would be useful to your audience, I'd genuinely appreciate a
mention or link in a relevant article. Happy to return the favour or provide data
for any pieces you're working on.

Press kit: {press_url}

Thanks for your time,
Sifu Kai
SifuFinds
{site_url}
""",
    },
}


def _load_prospects() -> list[dict]:
    if not PROSPECTS_FILE.exists():
        return []
    try:
        return json.loads(PROSPECTS_FILE.read_text())
    except Exception:
        return []


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"contacted": [], "daily_sends": {}, "queue_index": 0}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _already_contacted(domain: str, state: dict) -> bool:
    return domain in state.get("contacted", [])


def _daily_send_count(state: dict) -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return state.get("daily_sends", {}).get(today, 0)


def _increment_daily(state: dict) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    state.setdefault("daily_sends", {})[today] = _daily_send_count(state) + 1


def _pick_template(prospect: dict) -> dict:
    link_type = prospect.get("link_type", "").lower()
    niche = prospect.get("niche", "").lower()
    if link_type in TEMPLATES:
        return TEMPLATES[link_type]
    if "sport" in niche:
        return TEMPLATES["sports news"]
    if "betting" in niche or "gambling" in niche:
        return TEMPLATES["betting guide"]
    return TEMPLATES["default"]


def _build_email(prospect: dict) -> tuple[str, str]:
    tmpl = _pick_template(prospect)
    ctx = {
        "site_name": prospect.get("site_name", prospect.get("domain", "your site")),
        "site_url": SITE_URL,
        "press_url": PRESS_URL,
        "niche": prospect.get("niche", "sports"),
        "domain": prospect.get("domain", ""),
    }
    subject = tmpl["subject"].format(**ctx)
    body    = tmpl["body"].format(**ctx)
    return subject, body


def _guess_contact_email(domain: str) -> str:
    """Generate best-guess contact email for a domain."""
    return f"editor@{domain}"


def _send_email(to_email: str, subject: str, body: str, dry_run: bool = False) -> bool:
    password = os.getenv("OUTREACH_EMAIL_PASS", "")
    if not password and not dry_run:
        print("  ✗ OUTREACH_EMAIL_PASS not set")
        return False

    if dry_run:
        print(f"  [DRY RUN] To: {to_email}")
        print(f"  Subject: {subject}")
        print(f"  Body preview: {body[:300].strip()}...")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg["To"]      = to_email
        msg["Reply-To"] = SENDER_EMAIL
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.login(SENDER_EMAIL, password)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())

        print(f"  ✓ Sent → {to_email}")
        return True
    except Exception as e:
        print(f"  ✗ Failed → {to_email}: {e}")
        return False


def run(dry_run: bool = False, limit: int = MAX_PER_RUN) -> None:
    prospects = _load_prospects()
    state     = _load_state()
    now       = datetime.now(timezone.utc).isoformat()

    if not prospects:
        print("✗ No prospects found in backlink_opportunities.json")
        sys.exit(1)

    daily_sent = _daily_send_count(state)
    if daily_sent >= MAX_PER_DAY and not dry_run:
        print(f"Daily limit reached ({daily_sent}/{MAX_PER_DAY}). Skipping.")
        sys.exit(0)

    sent_this_run = 0
    idx = state.get("queue_index", 0)

    # Cycle through prospects starting from where we left off
    for i in range(len(prospects)):
        if sent_this_run >= limit:
            break
        if daily_sent + sent_this_run >= MAX_PER_DAY and not dry_run:
            break

        prospect = prospects[(idx + i) % len(prospects)]
        domain   = prospect.get("domain", "")

        if _already_contacted(domain, state) and not dry_run:
            continue

        # Skip low-relevance prospects
        if prospect.get("relevance_score", 5) < 6:
            continue

        to_email = _guess_contact_email(domain)
        subject, body = _build_email(prospect)

        print(f"\n[{i+1}] {domain} (relevance: {prospect.get('relevance_score', '?')})")
        success = _send_email(to_email, subject, body, dry_run=dry_run)

        if success and not dry_run:
            state.setdefault("contacted", []).append(domain)
            state.setdefault("outreach_log", []).append({
                "domain": domain,
                "to": to_email,
                "subject": subject,
                "ts": now,
            })
            _increment_daily(state)
            sent_this_run += 1
            time.sleep(DELAY_BETWEEN)
        elif dry_run:
            sent_this_run += 1

    state["queue_index"] = (idx + sent_this_run) % len(prospects)
    _save_state(state)

    print(f"\n[DONE] Sent {sent_this_run} emails this run ({daily_sent + sent_this_run}/{MAX_PER_DAY} today)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Email Outreach Agent")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    parser.add_argument("--limit", type=int, default=MAX_PER_RUN, help="Max emails this run")
    args = parser.parse_args()
    run(dry_run=args.dry_run, limit=args.limit)
