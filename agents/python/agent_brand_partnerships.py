#!/usr/bin/env python3
"""
SifuFinds Brand Partnership Outreach Agent

Reaches out to bookmakers SifuFinds already covers editorially (bonus tables,
country pages, blog posts) but has no commercial relationship with yet, i.e.
the link on our site points straight at the brand's own domain with no
affiliate tag. See brand_partnership_prospects.json for the researched list
and the reasoning behind each one.

The ask in every email is the same: a 30 percent revenue share on new
customers only (NNCO), in exchange for turning existing free exposure into
a tracked, paid relationship.

SAFETY GATE — read before running:
  * Default behaviour is always a dry run. Nothing is sent unless you pass
    --send or --test.
  * --send (a real bulk run against the prospect list) additionally refuses
    to run unless GREENLIGHT_FILE exists. That file is not created by this
    script. It only appears once a human deliberately creates it, e.g.:
        touch agents/python/brand_partnership_greenlight.flag
    Delete it again to re-close the gate.
  * --test EMAIL sends exactly one real email, for a single brand, straight
    to the address you give it. This does not require the greenlight file,
    since it is a one-off human-supervised check rather than outreach.

Usage:
  python agent_brand_partnerships.py                        # preview all, sends nothing
  python agent_brand_partnerships.py --brand Bet9ja          # preview one brand
  python agent_brand_partnerships.py --test you@example.com --brand Bet9ja
  python agent_brand_partnerships.py --send                  # real run, requires greenlight file
"""
from __future__ import annotations

import argparse
import json
import smtplib
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent / ".env")

PROSPECTS_FILE = Path(__file__).parent / "brand_partnership_prospects.json"
STATE_FILE = Path(__file__).parent / "brand_partnership_state.json"
GREENLIGHT_FILE = Path(__file__).parent / "brand_partnership_greenlight.flag"
FEATURED_LISTINGS_FILE = Path(__file__).parent.parent.parent / "data" / "featured_listings.json"

VALID_SLOT_PREFIXES = (
    "homepage_hero", "top_sportsbook", "featured_casino", "editors_pick",
    "category_sponsor:", "country_sponsor:", "newsletter_sponsor",
)

SITE_URL = "https://sifufinds.com"
SENDER_NAME = "Kai from SifuFinds"

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

COMMISSION_ASK = "30 percent revenue share on new customers only (NNCO)"

# Two openers and two closers, rotated by brand name so a batch of emails
# does not read as one mail merge with the brand name swapped in and out.
OPENERS = [
    "My name's Kai and I run SifuFinds, an independent betting comparison site covering 28 African countries.",
    "I'm Kai. I put together SifuFinds, a betting comparison site that now covers 28 countries across Africa.",
]

CLOSERS = [
    "If there's someone on the affiliate or partnerships side I should be speaking to, a pointer in the right direction would be appreciated. Happy to jump on a call, carry on over email, or you can message me directly on Telegram at @SifuKai, whichever's easier for you. Our channel's at t.me/sifufinds too if you want to see the kind of audience we're putting bookmakers in front of.\n\nThanks for your time.\n\nKai\nSifuFinds\n{site_url}\nTelegram: @SifuKai · t.me/sifufinds",
    "Let me know if there's a better contact for this on your end, or if you'd rather just reply here to get things moving. I'm also on Telegram as @SifuKai if that's quicker for you, and our channel's at t.me/sifufinds.\n\nCheers,\nKai\nSifuFinds\n{site_url}\nTelegram: @SifuKai · t.me/sifufinds",
]


@dataclass(frozen=True)
class Prospect:
    brand: str
    affiliate_program_name: str
    affiliate_portal: str
    contact_emails: tuple
    contact_form: str
    countries_featured_on_sifufinds: tuple
    current_commission_public: str
    angle: str
    status: str


def _load_prospects() -> list[Prospect]:
    if not PROSPECTS_FILE.exists():
        return []
    data = json.loads(PROSPECTS_FILE.read_text())
    return [
        Prospect(
            brand=p["brand"],
            affiliate_program_name=p["affiliate_program_name"],
            affiliate_portal=p["affiliate_portal"],
            contact_emails=tuple(p.get("contact_emails", [])),
            contact_form=p.get("contact_form", ""),
            countries_featured_on_sifufinds=tuple(p["countries_featured_on_sifufinds"]),
            current_commission_public=p.get("current_commission_public", ""),
            angle=p["angle"],
            status=p.get("status", "not_contacted"),
        )
        for p in data.get("prospects", [])
    ]


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"contacted": [], "log": []}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _format_countries(countries: tuple) -> str:
    if len(countries) == 1:
        return f"our {countries[0]} page"
    if len(countries) == 2:
        return f"our {countries[0]} and {countries[1]} pages"
    return "our " + ", ".join(countries[:-1]) + f" and {countries[-1]} pages"


def _build_email(prospect: Prospect) -> tuple[str, str]:
    rotation = sum(ord(c) for c in prospect.brand) % 2
    opener = OPENERS[rotation]
    closer = CLOSERS[rotation].format(site_url=SITE_URL)
    countries_line = _format_countries(prospect.countries_featured_on_sifufinds)

    subject = f"A proper partnership for {prospect.brand} on SifuFinds"

    body = f"""\
Hi there,

{opener}

I'll be straight with you. You already appear on {countries_line}, with a direct link straight through to your own site. {prospect.angle} None of that sends anything back to you commercially right now. It's free exposure, and it has been for a while.

We've been growing steadily. The site now runs over 200 articles, live bonus data that updates daily, and free tools like an odds calculator and an accumulator calculator that bettors actually use before picking a bookmaker. That traffic keeps building as we add more countries and more content, and you're already in front of a good share of it.

What I'd like to propose is straightforward. Instead of linking to you for nothing, we'd rather send you tracked signups under a proper arrangement, {COMMISSION_ASK}. You get paying customers you're not currently getting through us, and we get a fair return for referrals we're already generating.

{closer}"""

    return subject, body


def _connect_smtp() -> smtplib.SMTP:
    if SMTP_PORT == 465:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30)
    else:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        server.ehlo()
        server.starttls()
    server.login(SMTP_USER, SMTP_PASS)
    return server


def _send_email(to_email: str, subject: str, body: str) -> bool:
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS):
        print("  x SMTP credentials missing (check agents/python/.env)")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{SENDER_NAME} <{SMTP_USER}>"
        msg["To"] = to_email
        msg["Reply-To"] = SMTP_USER
        msg.attach(MIMEText(body, "plain"))

        with _connect_smtp() as server:
            server.sendmail(SMTP_USER, to_email, msg.as_string())

        print(f"  > sent to {to_email}")
        return True
    except Exception as exc:
        print(f"  x failed to send to {to_email}: {exc}")
        return False


def _select_prospects(prospects: list[Prospect], brand_filter: str | None) -> list[Prospect]:
    if not brand_filter:
        return prospects
    needle = brand_filter.strip().lower()
    return [p for p in prospects if needle in p.brand.lower()]


def preview(prospects: list[Prospect]) -> None:
    if not prospects:
        print("No matching prospects found.")
        return
    for prospect in prospects:
        subject, body = _build_email(prospect)
        print("=" * 72)
        print(f"BRAND: {prospect.brand}  (status: {prospect.status})")
        print(f"Contact: {prospect.contact_emails or prospect.contact_form}")
        print(f"Subject: {subject}")
        print("-" * 72)
        print(body)
    print("=" * 72)
    print(f"\n[DRY RUN] Previewed {len(prospects)} email(s). Nothing was sent.")


def run_test(prospects: list[Prospect], test_email: str, brand_filter: str | None) -> None:
    matches = _select_prospects(prospects, brand_filter)
    if not matches:
        print(f"No prospect matched --brand {brand_filter!r}. Nothing sent.")
        sys.exit(1)
    prospect = matches[0]
    subject, body = _build_email(prospect)
    print(f"[TEST SEND] {prospect.brand} -> {test_email}")
    success = _send_email(test_email, subject, body)
    if success:
        print("\n[DONE] Test email sent. No prospect state was changed; this does not count as real outreach.")
    else:
        sys.exit(1)


def run_send(prospects: list[Prospect], brand_filter: str | None) -> None:
    if not GREENLIGHT_FILE.exists():
        print("BLOCKED: real outreach is not greenlit yet.")
        print(f"Create {GREENLIGHT_FILE.name} in agents/python/ once you've reviewed and approved the emails, then re-run with --send.")
        sys.exit(1)

    state = _load_state()
    now = datetime.now(timezone.utc).isoformat()
    targets = _select_prospects(prospects, brand_filter)

    sent = 0
    for prospect in targets:
        if prospect.brand in state.get("contacted", []):
            print(f"- skipping {prospect.brand}, already contacted")
            continue
        if not prospect.contact_emails:
            print(f"- skipping {prospect.brand}, no verified contact email on file (use {prospect.contact_form})")
            continue

        subject, body = _build_email(prospect)
        to_email = prospect.contact_emails[0]
        print(f"[{prospect.brand}] sending to {to_email}")
        if _send_email(to_email, subject, body):
            state.setdefault("contacted", []).append(prospect.brand)
            state.setdefault("log", []).append({
                "brand": prospect.brand,
                "to": to_email,
                "subject": subject,
                "ts": now,
            })
            sent += 1

    _save_state(state)
    print(f"\n[DONE] Sent {sent} partnership email(s).")


# ── FEATURED LISTINGS MANAGEMENT ────────────────────────────────────────────
# The "Commercial Partnerships Manager" side of this agent: turning a closed
# deal (see the outreach flow above) into a live, transparently-labelled
# sponsored placement. data/featured_listings.json is the single source of
# truth — also read by utils/bookmaker_page_template.py (renders the
# "Featured Partner" badge on bookmaker review pages) and checked for
# transparent-criteria compliance by scripts/compliance_check.py.

def _load_listings() -> dict:
    if FEATURED_LISTINGS_FILE.exists():
        try:
            return json.loads(FEATURED_LISTINGS_FILE.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return {"listings": []}


def _save_listings(data: dict) -> None:
    FEATURED_LISTINGS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _is_active(entry: dict, now: datetime) -> bool:
    if entry.get("sponsored") is not True:
        return False
    starts_at = entry.get("starts_at")
    ends_at = entry.get("ends_at")
    if starts_at and datetime.fromisoformat(starts_at.replace("Z", "+00:00")) > now:
        return False
    if ends_at and datetime.fromisoformat(ends_at.replace("Z", "+00:00")) < now:
        return False
    return True


def list_listings() -> None:
    data = _load_listings()
    now = datetime.now(timezone.utc)
    entries = data.get("listings", [])
    if not entries:
        print("No Featured Listings on record.")
        return
    for e in entries:
        status = "ACTIVE" if _is_active(e, now) else "expired/scheduled"
        print(f"  [{status:18}] {e.get('slot')} -> {e.get('brand_slug')} (ends {e.get('ends_at', 'MISSING — invalid')})")
        print(f"      criteria: {e.get('criteria_note', '(missing — required)')}")


def add_listing(slot: str, brand_slug: str, ends_at: str, criteria_note: str,
                starts_at: str | None = None, force: bool = False) -> int:
    if not any(slot == p or slot.startswith(p) for p in VALID_SLOT_PREFIXES):
        print(f"❌ Unknown slot '{slot}' — must be one of {VALID_SLOT_PREFIXES}")
        return 1
    if not criteria_note:
        print("❌ --criteria is required — every sponsored placement must state why this brand holds it "
              "(CLAUDE.md: 'Editor's Pick (with transparent criteria)')")
        return 1
    try:
        datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
    except ValueError:
        print(f"❌ --ends '{ends_at}' is not a valid ISO 8601 timestamp — no open-ended placements allowed")
        return 1

    data = _load_listings()
    entries = data.get("listings", [])
    now = datetime.now(timezone.utc)
    occupant = next((e for e in entries if e.get("slot") == slot and _is_active(e, now)), None)
    if occupant and not force:
        print(f"❌ Slot '{slot}' is already held by '{occupant.get('brand_slug')}' until {occupant.get('ends_at')} "
              f"— pass --force to replace it")
        return 1

    entries = [e for e in entries if e.get("slot") != slot]
    entries.append({
        "slot": slot, "brand_slug": brand_slug, "sponsored": True,
        "starts_at": starts_at, "ends_at": ends_at, "criteria_note": criteria_note,
    })
    data["listings"] = entries
    _save_listings(data)
    print(f"✅ '{brand_slug}' now holds slot '{slot}' until {ends_at}")
    return 0


def remove_listing(slot: str) -> int:
    data = _load_listings()
    entries = data.get("listings", [])
    remaining = [e for e in entries if e.get("slot") != slot]
    if len(remaining) == len(entries):
        print(f"No listing found for slot '{slot}'")
        return 1
    data["listings"] = remaining
    _save_listings(data)
    print(f"✅ Removed listing for slot '{slot}'")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Brand Partnership Outreach Agent")
    parser.add_argument("--brand", help="Only target prospects whose name contains this text")
    parser.add_argument("--test", metavar="EMAIL", help="Send one real email for a single brand to this address")
    parser.add_argument("--send", action="store_true", help="Real bulk run (requires the greenlight file)")

    parser.add_argument("--manage-listings", action="store_true", help="List all Featured Listings and their status")
    parser.add_argument("--add-listing", action="store_true", help="Add/replace a Featured Listing (needs --slot/--brand-slug/--ends/--criteria)")
    parser.add_argument("--remove-listing", metavar="SLOT", help="Remove any Featured Listing occupying this slot")
    parser.add_argument("--slot", help="Slot name, e.g. top_sportsbook or country_sponsor:nigeria")
    parser.add_argument("--brand-slug", help="Brand slug for --add-listing")
    parser.add_argument("--starts", help="ISO 8601 start timestamp (omit for immediately active)")
    parser.add_argument("--ends", help="ISO 8601 end timestamp (required for --add-listing)")
    parser.add_argument("--criteria", help="Transparent reason this brand holds the slot (required for --add-listing)")
    parser.add_argument("--force", action="store_true", help="Replace an already-occupied slot")
    args = parser.parse_args()

    if args.manage_listings:
        list_listings()
        sys.exit(0)
    if args.add_listing:
        if not (args.slot and args.brand_slug and args.ends and args.criteria):
            print("❌ --add-listing requires --slot, --brand-slug, --ends, and --criteria")
            sys.exit(1)
        sys.exit(add_listing(args.slot, args.brand_slug, args.ends, args.criteria, args.starts, args.force))
    if args.remove_listing:
        sys.exit(remove_listing(args.remove_listing))

    all_prospects = _load_prospects()
    if not all_prospects:
        print("No prospects found in brand_partnership_prospects.json")
        sys.exit(1)

    if args.test:
        run_test(all_prospects, args.test, args.brand)
    elif args.send:
        run_send(all_prospects, args.brand)
    else:
        preview(_select_prospects(all_prospects, args.brand))
