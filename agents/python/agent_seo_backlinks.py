"""
SEO Backlink Outreach Agent — SifuFinds
Researches link targets, drafts personalised emails, finds contact addresses,
and sends outreach directly via SMTP.

White-hat only: guest posts, digital PR, resource pages, broken-link reclaim.

Workflow:
  1. --research  → AI discovers target sites + relevance scores
  2. --outreach  → AI drafts personalised email per pending opportunity
  3. --send      → Finds contact emails (Hunter.io or pattern fallback) and sends
  4. --content   → AI suggests link-bait content assets
  5. --status    → Full pipeline dashboard

Usage:
  python agent_seo_backlinks.py --research           # discover new targets
  python agent_seo_backlinks.py --outreach           # draft emails
  python agent_seo_backlinks.py --send               # find contacts + send
  python agent_seo_backlinks.py --all                # all phases
  python agent_seo_backlinks.py --dry-run --send     # preview sends without sending
  python agent_seo_backlinks.py --limit 10           # cap per run

Required env vars (agents/python/.env):
  SMTP_USER      — sender Gmail address (or any SMTP user)
  SMTP_PASS      — Gmail App Password (not your account password)
  SMTP_FROM_NAME — display name, e.g. "Kai at SifuFinds"

Optional:
  HUNTER_API_KEY — hunter.io key for accurate contact-email lookup (25 free/month)
  SMTP_HOST      — defaults to smtp.hostinger.com
  SMTP_PORT      — defaults to 465 (SSL)

State files (committed so CI tracks progress):
  backlink_opportunities.json   — discovered targets + relevance scores
  backlink_state.json           — per-domain outreach status + email drafts
"""

import argparse
import json
import os
import random
import re
import smtplib
import sys
import time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))
from llm import ask, ask_long
from utils.logger import log

# ── CONFIG ─────────────────────────────────────────────────────────────────────

SITE_URL   = "https://sifufinds.com"
SITE_NAME  = "SifuFinds"
SITE_DESC  = (
    "Africa's betting odds comparison site — covering 19 African countries "
    "with real-time odds from 19+ bookmakers, free bet alerts, and guides."
)

DEFAULT_RESEARCH_LIMIT = 15   # new opportunities per research run
DEFAULT_OUTREACH_LIMIT = 10   # emails generated per outreach run
DEFAULT_SEND_LIMIT     = 10   # emails sent per run (keep low to protect sender reputation)

# ── SMTP CONFIG ────────────────────────────────────────────────────────────────
SMTP_HOST      = os.getenv("SMTP_HOST", "smtp.hostinger.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER      = os.getenv("SMTP_USER", "")
SMTP_PASS      = os.getenv("SMTP_PASS", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", f"SifuFinds Team")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")

# Seconds to wait between sends — avoids triggering spam filters
SEND_DELAY_MIN = 30
SEND_DELAY_MAX = 90

# Common contact email prefixes tried in order when Hunter returns nothing
CONTACT_PREFIXES = ["contact", "editor", "info", "hello", "advertise", "partnerships", "team"]

OPPORTUNITIES_FILE = Path(__file__).parent / "backlink_opportunities.json"
STATE_FILE         = Path(__file__).parent / "backlink_state.json"

# ── OPPORTUNITY NICHES ─────────────────────────────────────────────────────────
# Drives the research prompt — AI picks from these niches each run.

NICHES = [
    "African sports betting blogs",
    "iGaming and gambling industry media",
    "African football news sites",
    "African fintech and payments media",
    "Nigeria tech and startup blogs",
    "Kenya digital media and news",
    "South Africa sports media",
    "Africa general news and lifestyle",
    "Responsible gambling resource sites",
    "Sports prediction and statistics sites",
    "African cryptocurrency and finance blogs",
    "Digital marketing and affiliate marketing blogs",
]

LINK_TYPES = [
    "guest post",
    "resource page listing",
    "digital PR mention",
    "broken link replacement",
    "link insertion (contextual)",
    "partnership / collaboration",
]


# ── PROMPTS ───────────────────────────────────────────────────────────────────

_RESEARCH_SYSTEM = f"""You are an SEO link-building strategist for {SITE_NAME} ({SITE_URL}).
{SITE_DESC}

Target audience: sports bettors in Nigeria, Kenya, South Africa, Ghana, Uganda, Tanzania, and 14 other African countries.

Your task: identify high-quality, legitimate backlink opportunities. White-hat only.
Never suggest PBNs, link farms, paid link schemes, or spam tactics.

Respond ONLY with a JSON array. Each object:
{{
  "domain": "example.com",
  "site_name": "Human-readable name",
  "niche": "one of the niches given",
  "link_type": "guest post | resource page | digital PR | broken link | link insertion | partnership",
  "relevance_score": 8,        // 1-10 — how relevant to sifufinds.com audience
  "authority_estimate": "medium",  // low | medium | high — estimated domain strength
  "why_relevant": "1-2 sentences explaining the fit",
  "contact_approach": "brief note on how to find/approach them",
  "suggested_anchor": "natural anchor text idea"
}}

Return between 10 and 20 opportunities. Vary across link types and niches."""

_OUTREACH_SYSTEM = f"""You are a digital PR and outreach specialist for {SITE_NAME} ({SITE_URL}).
{SITE_DESC}

Write a personalised, professional outreach email for a backlink opportunity.
Tone: genuine, concise, non-spammy. Lead with value to the recipient, not your need.
Max 200 words. Subject line + body only. No placeholders like [NAME] — use "Hi there" or the site name.

Respond ONLY with valid JSON:
{{
  "subject": "email subject line",
  "body": "full email body"
}}"""

_CONTENT_SYSTEM = f"""You are a link-building content strategist for {SITE_NAME} ({SITE_URL}).
{SITE_DESC}

Suggest content assets specifically designed to attract high-quality editorial backlinks from:
- African sports and betting media
- iGaming industry publications
- African news sites and lifestyle blogs
- Finance and fintech sites covering Africa

Each asset should be realistic to produce and have a clear link-earning angle.

Return ONLY a JSON array of 10 content ideas:
{{
  "title": "Working title for the content",
  "content_type": "statistics page | guide | tool | research | comparison | infographic | data story",
  "primary_keyword": "target SEO keyword",
  "link_bait_angle": "why journalists or bloggers would link to this",
  "target_publications": ["type of site 1", "type of site 2"],
  "effort": "low | medium | high",
  "expected_links": "realistic estimate e.g. '5-15 links'"
}}"""


# ── STATE ─────────────────────────────────────────────────────────────────────

def _load_opportunities() -> list[dict]:
    if OPPORTUNITIES_FILE.exists():
        try:
            return json.loads(OPPORTUNITIES_FILE.read_text())
        except Exception:
            pass
    return []


def _save_opportunities(ops: list[dict]) -> None:
    OPPORTUNITIES_FILE.write_text(json.dumps(ops, indent=2))


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── RESEARCH ──────────────────────────────────────────────────────────────────

def run_research(limit: int = DEFAULT_RESEARCH_LIMIT, dry_run: bool = False) -> int:
    import random

    existing = _load_opportunities()
    existing_domains = {op["domain"] for op in existing}

    # Rotate niches so different ones are targeted each run
    niches_sample = random.sample(NICHES, min(4, len(NICHES)))
    link_types_sample = random.sample(LINK_TYPES, min(3, len(LINK_TYPES)))

    user_msg = (
        f"Find backlink opportunities for {SITE_URL} from these niches:\n"
        + "\n".join(f"- {n}" for n in niches_sample)
        + f"\n\nPrioritise these link types (but include others too):\n"
        + "\n".join(f"- {lt}" for lt in link_types_sample)
        + f"\n\nAlready tracked domains (skip these):\n"
        + ", ".join(list(existing_domains)[:40]) if existing_domains else ""
        + f"\n\nReturn {limit} new opportunities."
    )

    print(f"\n🔍 Researching backlink opportunities (niches: {', '.join(niches_sample)})...")

    try:
        raw = ask_long(_RESEARCH_SYSTEM, user_msg)
    except Exception as e:
        print(f"✗ LLM error during research: {e}")
        log("backlinks", "research", "error", str(e)[:120])
        return 0

    # Parse JSON from response
    ops = _parse_json_array(raw, "opportunity")
    if not ops:
        print("✗ Could not parse opportunities from LLM response")
        log("backlinks", "research", "parse_error", raw[:200])
        return 0

    # Deduplicate against existing
    new_ops = []
    for op in ops:
        domain = op.get("domain", "").lower().strip()
        if not domain or domain in existing_domains:
            continue
        op["domain"] = domain
        op["discovered_at"] = datetime.now(timezone.utc).isoformat()
        new_ops.append(op)
        existing_domains.add(domain)
        if len(new_ops) >= limit:
            break

    if dry_run:
        print(f"\n── DRY RUN: {len(new_ops)} opportunities found ──")
        for op in new_ops:
            score = op.get("relevance_score", "?")
            auth  = op.get("authority_estimate", "?")
            ltype = op.get("link_type", "?")
            print(f"  [{score}/10 · {auth} · {ltype}] {op['domain']} — {op.get('why_relevant','')[:80]}")
        return len(new_ops)

    all_ops = existing + new_ops
    _save_opportunities(all_ops)

    print(f"\n✓ Research complete — {len(new_ops)} new opportunities (total: {len(all_ops)})")
    log("backlinks", "research", "done", f"new:{len(new_ops)} total:{len(all_ops)}")
    return len(new_ops)


# ── OUTREACH ──────────────────────────────────────────────────────────────────

def run_outreach(limit: int = DEFAULT_OUTREACH_LIMIT, dry_run: bool = False) -> int:
    opportunities = _load_opportunities()
    state = _load_state()

    # Queue: opportunities with no outreach drafted yet
    pending = [
        op for op in opportunities
        if op.get("domain") and state.get(op["domain"], {}).get("status") in (None, "pending")
        and not state.get(op["domain"], {}).get("email_subject")
    ]

    # Prioritise by relevance score descending
    pending.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    pending = pending[:limit]

    if not pending:
        print("✓ No pending opportunities need outreach emails — run --research to add more.")
        return 0

    print(f"\n📧 Generating outreach emails for {len(pending)} opportunities...")
    generated = 0

    for op in pending:
        domain    = op["domain"]
        site_name = op.get("site_name", domain)
        link_type = op.get("link_type", "guest post")
        why       = op.get("why_relevant", "")

        user_msg = (
            f"Target site: {site_name} ({domain})\n"
            f"Link type: {link_type}\n"
            f"Why relevant: {why}\n"
            f"Suggested anchor: {op.get('suggested_anchor', '')}\n"
            f"Contact approach: {op.get('contact_approach', '')}\n"
            f"\nWrite a personalised outreach email on behalf of {SITE_NAME} ({SITE_URL})."
        )

        try:
            raw = ask(_OUTREACH_SYSTEM, user_msg)
        except Exception as e:
            print(f"  ✗ {domain}: LLM error — {e}")
            continue

        email = _parse_json_object(raw, "outreach")
        if not email or not email.get("subject"):
            print(f"  ✗ {domain}: could not parse email from response")
            continue

        record = state.get(domain, {})
        record.update({
            "domain":        domain,
            "site_name":     site_name,
            "link_type":     link_type,
            "relevance":     op.get("relevance_score", 0),
            "authority":     op.get("authority_estimate", "unknown"),
            "email_subject": email["subject"],
            "email_body":    email["body"],
            "status":        "pending",
            "drafted_at":    datetime.now(timezone.utc).isoformat(),
            "sent_at":       None,
            "followed_up_at": None,
            "response":      None,
            "acquired":      False,
            "notes":         "",
        })

        if dry_run:
            print(f"\n── DRY RUN: {domain} ──")
            print(f"  Subject: {email['subject']}")
            print(f"  Body preview: {email['body'][:200]}...")
        else:
            state[domain] = record
            print(f"  ✓ Drafted outreach for {site_name} ({domain})")

        generated += 1

    if not dry_run and generated:
        _save_state(state)

    print(f"\n✓ Outreach complete — {generated} emails drafted")
    log("backlinks", "outreach", "done", f"drafted:{generated}")
    return generated


# ── CONTENT STRATEGY ─────────────────────────────────────────────────────────

def run_content_strategy(dry_run: bool = False) -> int:
    print("\n💡 Generating link-bait content strategy...")

    user_msg = (
        f"Site: {SITE_NAME} ({SITE_URL})\n{SITE_DESC}\n\n"
        "Generate 10 content asset ideas specifically designed to earn editorial backlinks "
        "from African sports media, iGaming publications, and African news sites."
    )

    try:
        raw = ask_long(_CONTENT_SYSTEM, user_msg)
    except Exception as e:
        print(f"✗ LLM error: {e}")
        log("backlinks", "content", "error", str(e)[:120])
        return 0

    ideas = _parse_json_array(raw, "content idea")
    if not ideas:
        print("✗ Could not parse content ideas from LLM response")
        return 0

    if dry_run:
        print(f"\n── DRY RUN: {len(ideas)} content ideas ──")
    else:
        # Persist ideas into state so they're not lost
        state = _load_state()
        state["__content_ideas__"] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "ideas": ideas,
        }
        _save_state(state)

    print(f"\n📋 Content Strategy — {len(ideas)} link-bait ideas\n{'─'*55}")
    for i, idea in enumerate(ideas, 1):
        effort  = idea.get("effort", "?")
        links   = idea.get("expected_links", "?")
        ctype   = idea.get("content_type", "?")
        print(f"\n{i:2}. [{ctype}] {idea.get('title','')}")
        print(f"    Keyword:   {idea.get('primary_keyword','')}")
        print(f"    Link bait: {idea.get('link_bait_angle','')[:90]}")
        print(f"    Targets:   {', '.join(idea.get('target_publications',[])[:3])}")
        print(f"    Effort: {effort}  ·  Expected links: {links}")

    log("backlinks", "content", "done", f"ideas:{len(ideas)}")
    return len(ideas)


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

def print_dashboard() -> None:
    opportunities = _load_opportunities()
    state         = _load_state()

    # Filter out meta keys
    domain_records = {k: v for k, v in state.items() if not k.startswith("__")}

    total_ops   = len(opportunities)
    total_draft = sum(1 for r in domain_records.values() if r.get("email_subject"))
    total_sent  = sum(1 for r in domain_records.values() if r.get("sent_at"))
    total_acq   = sum(1 for r in domain_records.values() if r.get("acquired"))
    total_pend  = total_ops - total_draft

    # Niche breakdown
    niche_counts: dict[str, int] = {}
    for op in opportunities:
        n = op.get("niche", "other")
        niche_counts[n] = niche_counts.get(n, 0) + 1

    # Link-type breakdown
    ltype_counts: dict[str, int] = {}
    for op in opportunities:
        lt = op.get("link_type", "other")
        ltype_counts[lt] = ltype_counts.get(lt, 0) + 1

    print(f"\n{'═'*55}")
    print(f"  {SITE_NAME} — Backlink Outreach Dashboard")
    print(f"{'═'*55}")
    print(f"  Opportunities discovered : {total_ops}")
    print(f"  Outreach drafted         : {total_draft}")
    print(f"  Emails sent (manual)     : {total_sent}")
    print(f"  Links acquired           : {total_acq}")
    print(f"  Pending research         : {total_pend}")

    if domain_records:
        # Status breakdown
        statuses: dict[str, int] = {}
        for r in domain_records.values():
            s = r.get("status", "pending")
            statuses[s] = statuses.get(s, 0) + 1
        print(f"\n  Outreach Status")
        print(f"  {'─'*30}")
        for status, count in sorted(statuses.items()):
            print(f"    {status:20} {count}")

    if niche_counts:
        print(f"\n  Top Niches")
        print(f"  {'─'*30}")
        for niche, count in sorted(niche_counts.items(), key=lambda x: -x[1])[:6]:
            print(f"    {niche[:32]:33} {count}")

    if ltype_counts:
        print(f"\n  Link Types")
        print(f"  {'─'*30}")
        for lt, count in sorted(ltype_counts.items(), key=lambda x: -x[1]):
            print(f"    {lt:32} {count}")

    # Content ideas
    content = state.get("__content_ideas__", {})
    if content:
        ideas = content.get("ideas", [])
        gen   = content.get("generated_at", "?")[:10]
        print(f"\n  Content Strategy: {len(ideas)} ideas (generated {gen})")

    # Top pending prospects by relevance
    pending_ops = [
        op for op in opportunities
        if not domain_records.get(op.get("domain", ""), {}).get("email_subject")
    ]
    pending_ops.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    if pending_ops:
        print(f"\n  Top Pending Targets (by relevance)")
        print(f"  {'─'*30}")
        for op in pending_ops[:8]:
            score = op.get("relevance_score", "?")
            auth  = op.get("authority_estimate", "?")
            print(f"    [{score}/10 · {auth:6}] {op.get('domain','')}")

    print(f"\n{'═'*55}\n")


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _parse_json_array(text: str, label: str) -> list:
    """Extract JSON array from LLM output that may be wrapped in markdown fences."""
    # Strip markdown fences
    cleaned = text.strip()
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("["):
                cleaned = part
                break

    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            # Some models wrap in {"opportunities": [...]} etc.
            for v in result.values():
                if isinstance(v, list):
                    return v
    except json.JSONDecodeError:
        pass

    print(f"✗ Could not parse {label} JSON. Raw: {text[:300]}")
    return []


def _parse_json_object(text: str, label: str) -> dict:
    cleaned = text.strip()
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                cleaned = part
                break

    try:
        result = json.loads(cleaned)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    print(f"✗ Could not parse {label} JSON. Raw: {text[:300]}")
    return {}


# ── CONTACT EMAIL DISCOVERY ───────────────────────────────────────────────────

def find_contact_email(domain: str) -> str | None:
    """
    Try Hunter.io first (most accurate). Fall back to guessing common prefixes.
    Returns the best email found, or None if nothing is available.
    """
    # 1. Hunter.io domain search
    if HUNTER_API_KEY:
        try:
            resp = requests.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": HUNTER_API_KEY, "limit": 5},
                timeout=10,
            )
            data = resp.json().get("data", {})
            emails = data.get("emails", [])
            if emails:
                # Prefer editorial/content-related roles
                editorial_roles = {"editor", "content", "writer", "seo", "marketing", "pr", "outreach"}
                for e in emails:
                    position = (e.get("position") or "").lower()
                    if any(r in position for r in editorial_roles):
                        return e["value"]
                return emails[0]["value"]
        except Exception as e:
            print(f"  [hunter] {domain}: {e}")

    # 2. Pattern fallback — most sites have at least contact@ or info@
    for prefix in CONTACT_PREFIXES:
        candidate = f"{prefix}@{domain}"
        # Basic MX-record check via a lightweight HEAD request (best-effort)
        try:
            r = requests.head(f"https://{domain}", timeout=6, allow_redirects=True)
            if r.status_code < 500:
                return candidate  # Site is alive — return first pattern
        except Exception:
            return candidate  # Can't reach site but return candidate anyway

    return None


# ── SMTP SEND ─────────────────────────────────────────────────────────────────

def _send_smtp(to_email: str, subject: str, body: str) -> bool:
    """Send a plain-text email. Returns True on success."""
    if not SMTP_USER or not SMTP_PASS:
        raise RuntimeError(
            "SMTP_USER and SMTP_PASS must be set in agents/python/.env to send emails.\n"
            "For Gmail: create an App Password at https://myaccount.google.com/apppasswords"
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"]      = to_email
    msg["Reply-To"] = SMTP_USER
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Port 465 = direct SSL; port 587 = STARTTLS
    if SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())

    return True


def run_send(limit: int = DEFAULT_SEND_LIMIT, dry_run: bool = False) -> int:
    """
    Find contact emails for all outreach-drafted opportunities and send the emails.
    Only processes records with status='pending' that have an email draft.
    """
    state = _load_state()

    # Queue: drafted but not yet sent
    pending = [
        (domain, rec) for domain, rec in state.items()
        if not domain.startswith("__")
        and rec.get("email_subject")
        and rec.get("status") == "pending"
        and not rec.get("sent_at")
    ]

    # Highest relevance first
    pending.sort(key=lambda x: x[1].get("relevance", 0), reverse=True)
    pending = pending[:limit]

    if not pending:
        print("✓ No drafted outreach ready to send — run --outreach first.")
        return 0

    print(f"\n📤 Sending outreach to {len(pending)} targets (limit: {limit})...")
    sent = 0

    for domain, rec in pending:
        subject = rec.get("email_subject", "")
        body    = rec.get("email_body", "")

        if not subject or not body:
            print(f"  ✗ {domain}: no email draft — run --outreach first")
            continue

        # Find contact email
        print(f"  🔍 {domain}: finding contact email...")
        contact = find_contact_email(domain)
        if not contact:
            print(f"  ✗ {domain}: could not determine contact email — skipping")
            rec["status"] = "no_contact"
            state[domain] = rec
            continue

        if dry_run:
            print(f"\n── DRY RUN: {domain} → {contact} ──")
            print(f"  Subject: {subject}")
            print(f"  Body:\n{body[:300]}{'...' if len(body) > 300 else ''}\n")
            sent += 1
            continue

        try:
            _send_smtp(contact, subject, body)
            rec["sent_to"]  = contact
            rec["sent_at"]  = datetime.now(timezone.utc).isoformat()
            rec["status"]   = "sent"
            state[domain]   = rec
            print(f"  ✓ Sent to {contact} ({domain})")
            sent += 1
            log("backlinks", "send", "success", f"domain:{domain} to:{contact}")
        except RuntimeError as e:
            # Config error — stop immediately, no point retrying other domains
            print(f"\n✗ SMTP not configured: {e}")
            log("backlinks", "send", "config_error", str(e)[:120])
            break
        except Exception as e:
            print(f"  ✗ {domain}: send failed — {e}")
            rec["status"] = "send_error"
            rec["send_error"] = str(e)[:120]
            state[domain] = rec
            log("backlinks", "send", "error", f"domain:{domain} err:{str(e)[:80]}")

        if sent < len(pending):
            delay = random.uniform(SEND_DELAY_MIN, SEND_DELAY_MAX)
            print(f"  ⏱  Waiting {delay:.0f}s before next send...")
            time.sleep(delay)

    if not dry_run:
        _save_state(state)

    print(f"\n✓ Send run complete — {sent} emails sent")
    log("backlinks", "send_run", "done", f"sent:{sent}")
    return sent


# ── MARK COMMANDS (manual update helpers) ─────────────────────────────────────

def mark_sent(domain: str) -> None:
    state = _load_state()
    if domain not in state:
        print(f"✗ Domain '{domain}' not in outreach state. Run --outreach first.")
        return
    state[domain]["sent_at"]  = datetime.now(timezone.utc).isoformat()
    state[domain]["status"]   = "sent"
    _save_state(state)
    print(f"✓ Marked {domain} as sent.")


def mark_acquired(domain: str, notes: str = "") -> None:
    state = _load_state()
    if domain not in state:
        print(f"✗ Domain '{domain}' not in state. Add it first via --outreach.")
        return
    state[domain]["acquired"]    = True
    state[domain]["status"]      = "acquired"
    state[domain]["acquired_at"] = datetime.now(timezone.utc).isoformat()
    if notes:
        state[domain]["notes"] = notes
    _save_state(state)
    print(f"✓ Marked {domain} as ACQUIRED link! 🎉")
    log("backlinks", "acquired", "success", f"domain:{domain}")


def mark_rejected(domain: str, notes: str = "") -> None:
    state = _load_state()
    if domain not in state:
        state[domain] = {"domain": domain}
    state[domain]["status"] = "rejected"
    if notes:
        state[domain]["notes"] = notes
    _save_state(state)
    print(f"✓ Marked {domain} as rejected.")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def run(
    do_research:  bool = False,
    do_outreach:  bool = False,
    do_send:      bool = False,
    do_content:   bool = False,
    dry_run:      bool = False,
    limit:        int  = DEFAULT_RESEARCH_LIMIT,
) -> None:
    log("backlinks", "start", "running")

    if do_research:
        run_research(limit=limit, dry_run=dry_run)

    if do_outreach:
        run_outreach(limit=limit, dry_run=dry_run)

    if do_send:
        run_send(limit=limit, dry_run=dry_run)

    if do_content:
        run_content_strategy(dry_run=dry_run)

    print_dashboard()
    log("backlinks", "done", "success")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds SEO Backlink Outreach Agent")
    parser.add_argument("--research",  action="store_true", help="Discover new backlink opportunities")
    parser.add_argument("--outreach",  action="store_true", help="Generate outreach emails for pending targets")
    parser.add_argument("--send",      action="store_true", help="Find contact emails and send outreach directly")
    parser.add_argument("--content",   action="store_true", help="Generate link-bait content strategy")
    parser.add_argument("--status",    action="store_true", help="Print pipeline dashboard and exit")
    parser.add_argument("--all",       action="store_true", help="Run all phases (research + outreach + send + content)")
    parser.add_argument("--dry-run",   action="store_true", help="Preview output without saving or sending")
    parser.add_argument("--limit",     type=int, default=DEFAULT_RESEARCH_LIMIT,
                        help=f"Max opportunities per run (default: {DEFAULT_RESEARCH_LIMIT})")
    parser.add_argument("--mark-acquired", metavar="DOMAIN", help="Mark a domain as acquired backlink")
    parser.add_argument("--mark-rejected", metavar="DOMAIN", help="Mark a domain as rejected/declined")
    parser.add_argument("--notes",     metavar="TEXT",   default="", help="Notes for mark commands")
    args = parser.parse_args()

    if args.mark_acquired:
        mark_acquired(args.mark_acquired, args.notes)
        sys.exit(0)
    if args.mark_rejected:
        mark_rejected(args.mark_rejected, args.notes)
        sys.exit(0)

    if args.status:
        print_dashboard()
        sys.exit(0)

    do_research = args.research or args.all
    do_outreach = args.outreach or args.all
    do_send     = args.send     or args.all
    do_content  = args.content  or args.all

    if not any([do_research, do_outreach, do_send, do_content]):
        # Default: full pipeline
        do_research = do_outreach = do_send = True

    run(
        do_research=do_research,
        do_outreach=do_outreach,
        do_send=do_send,
        do_content=do_content,
        dry_run=args.dry_run,
        limit=args.limit,
    )
