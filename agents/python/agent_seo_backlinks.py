"""
SEO Backlink Outreach Agent — SifuFinds
Researches link targets, drafts personalised emails, finds contact addresses,
sends outreach, monitors the inbox for replies, and auto-responds.

White-hat only: guest posts, digital PR, resource pages, broken-link reclaim.

Workflow:
  1. --research  → AI discovers target sites + relevance scores
  2. --outreach  → AI drafts personalised email per pending opportunity
  3. --send      → Finds contact emails (Hunter.io or pattern fallback) and sends
  4. --inbox     → Reads inbox, detects replies, AI drafts + sends reply automatically
  5. --content   → AI suggests link-bait content assets
  6. --status    → Full pipeline dashboard

Usage:
  python agent_seo_backlinks.py --research           # discover new targets
  python agent_seo_backlinks.py --outreach           # draft emails
  python agent_seo_backlinks.py --send               # find contacts + send
  python agent_seo_backlinks.py --inbox              # check inbox + auto-reply
  python agent_seo_backlinks.py --all                # all phases
  python agent_seo_backlinks.py --dry-run --inbox    # preview replies without sending

Required env vars (agents/python/.env):
  SMTP_USER      — sending email address
  SMTP_PASS      — email password
  SMTP_FROM_NAME — display name, e.g. "SifuFinds Team"
  IMAP_HOST      — defaults to imap.hostinger.com
  IMAP_PORT      — defaults to 993

Optional:
  HUNTER_API_KEY — hunter.io key for contact-email lookup

State files (committed so CI tracks progress):
  backlink_opportunities.json   — discovered targets + relevance scores
  backlink_state.json           — per-domain outreach status, emails, replies
"""

import argparse
import email
import email.header
import imaplib
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
DEFAULT_SEND_LIMIT     = 5    # emails per run — daily hard cap enforced separately

# ── SMTP CONFIG ────────────────────────────────────────────────────────────────
SMTP_HOST      = os.getenv("SMTP_HOST", "smtp.hostinger.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", "465"))
IMAP_HOST      = os.getenv("IMAP_HOST", "imap.hostinger.com")
IMAP_PORT      = int(os.getenv("IMAP_PORT", "993"))
SMTP_USER      = os.getenv("SMTP_USER", "")
SMTP_PASS      = os.getenv("SMTP_PASS", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "SifuFinds Team")

# ── EMAIL SAFETY LIMITS ────────────────────────────────────────────────────────
# Sources: Google Postmaster Guidelines, Mailgun, Topo, Instantly 2026 benchmarks.
#
# Key findings:
#   - Spam complaint rate > 0.3%  → Google enforces hard block
#   - Hard bounce rate > 5%       → ESP throttles/suspends account
#   - New/cold inbox safe limit   → 20 emails/day max (warmed: 50)
#   - Inter-send delay            → 5–12 min randomised (human-like cadence)
#   - Send window                 → Mon–Fri 08:00–17:00 UTC only
#   - Role addresses (info@,contact@) → high complaint rate; use editorial contacts
#   - CAN-SPAM §7                 → physical address + opt-out in every email

DAILY_SEND_HARD_CAP   = 20    # absolute max emails per UTC calendar day
SEND_DELAY_MIN        = 300   # 5 min minimum between sends
SEND_DELAY_MAX        = 720   # 12 min maximum — randomised jitter
SEND_WINDOW_START_UTC = 8     # only send Mon–Fri 08:00–17:00 UTC
SEND_WINDOW_END_UTC   = 17

# Physical address required by CAN-SPAM §7 in every outgoing commercial email.
# Set SMTP_PHYSICAL_ADDRESS in .env to your real registered address.
SMTP_PHYSICAL_ADDRESS = os.getenv("SMTP_PHYSICAL_ADDRESS", "SifuFinds, P.O. Box, Nairobi, Kenya")

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

_OUTREACH_SYSTEM = f"""You are Kai, the founder of {SITE_NAME} ({SITE_URL}).
{SITE_DESC}

Write a short, genuine outreach email to another site about a collaboration or link opportunity.

TONE — this is the most important instruction:
- Sound like a real person writing to a colleague, not a marketer writing to a prospect.
- Friendly and natural, like a message you'd send to someone you've just discovered and genuinely respect.
- Conversational and easy to read — short sentences, plain words.
- Professional but not stiff or corporate.
- Written in UK English (colour not color, favourite not favorite, etc.).
- Absolutely zero AI-style phrases: do not write "I hope this email finds you well",
  "I wanted to reach out", "I came across your website", "mutually beneficial",
  "synergy", "leverage", "touch base", "exciting opportunity", "please don't hesitate",
  "I look forward to hearing from you", "as per my last email", or anything that sounds
  like it was generated. If you catch yourself writing any of these, rewrite the sentence.
- Start with something specific about THEIR site — a real observation, not a compliment.
  Reference the niche, a topic they cover, or the audience they serve.
- One clear, low-pressure ask. No pressure. No urgency.
- Sign off as "Kai" or "Kai, SifuFinds" — never "The Team" or any formal sign-off.

DELIVERABILITY RULES (non-negotiable — violations suspend the inbox):
1. Body under 100 words. Count every word. Be ruthless.
2. Plain text only. No bullet points, no dashes, no markdown, no HTML.
3. One link maximum — the site URL {SITE_URL} only. No other URLs.
4. No spam trigger words: free, guaranteed, winner, urgent, limited time, act now,
   click here, make money, no obligation, congratulations, selected.
5. Never "Dear Blogger", "Hi there", "To whom it may concern" — use their site name or "Hi [name]".
6. Subject line: 6–10 words, no ALL CAPS, no exclamation marks, nothing clickbaity.
   It must accurately describe what the email is about (CAN-SPAM rule).

WHAT GOOD LOOKS LIKE:
- Opens with a specific, genuine observation: "I've been reading [site name]'s coverage of [topic]..."
- Second paragraph: what you bring to the table in one or two plain sentences.
- Final sentence: a single, easy ask with no pressure.
- Whole thing reads like a human wrote it in five minutes, not an agency template.

Respond ONLY with valid JSON. Use \\n for line breaks — never literal newlines inside strings.
{{
  "subject": "short subject line here",
  "body": "Specific opener about their site.\\n\\nWhat you offer + your ask.\\n\\nCheers,\\nKai, SifuFinds"
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


# ── DELIVERABILITY SAFEGUARDS ─────────────────────────────────────────────────

def _load_suppressed() -> set[str]:
    """Load permanently suppressed addresses (hard bounces + unsubscribers)."""
    return set(_load_state().get("__suppressed__", []))


def _add_suppressed(email_addr: str) -> None:
    """Permanently suppress an address. Persisted across runs."""
    state = _load_state()
    suppressed = set(state.get("__suppressed__", []))
    suppressed.add(email_addr.lower().strip())
    state["__suppressed__"] = sorted(suppressed)
    _save_state(state)
    print(f"  🚫 Suppressed {email_addr} — will not receive future emails")


def _daily_send_count() -> int:
    """Count emails sent today (UTC calendar day) across all runs."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    state = _load_state()
    return sum(
        1 for key, rec in state.items()
        if not key.startswith("__") and rec.get("sent_at", "")[:10] == today
    )


def _within_send_window() -> bool:
    """
    Return True only Mon–Fri 08:00–17:00 UTC.
    Cold email sent at night or weekends has lower open/reply rates and
    higher spam complaint rates — both damage sender reputation.
    """
    now = datetime.now(timezone.utc)
    return (
        now.weekday() < 5  # 0=Mon … 4=Fri
        and SEND_WINDOW_START_UTC <= now.hour < SEND_WINDOW_END_UTC
    )


def _canspam_footer() -> str:
    """
    CAN-SPAM Act §7 requires every commercial email to include:
      - Physical mailing address of the sender
      - A clear, functional opt-out mechanism
      - Honest identification of the sender
    Penalty: up to $53,088 per individual email in violation.
    """
    return (
        "\n\n---\n"
        f"Kai Manyeh · {SITE_NAME} · {SITE_URL}\n"
        f"{SMTP_PHYSICAL_ADDRESS}\n\n"
        "You received this because our team identified your site as a potential "
        "editorial partner. This is a one-time outreach — we won't follow up "
        "more than once. To opt out permanently, reply with STOP in the subject line."
    )


def _check_body_word_count(body: str, domain: str) -> None:
    """Warn if email body exceeds recommended cold email length."""
    words = len(body.split())
    if words > 150:
        print(f"  ⚠  {domain}: email body is {words} words (target < 100) — consider shortening")


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

        niche      = op.get("niche", "")
        audience   = op.get("audience", "")
        anchor     = op.get("suggested_anchor", "")
        approach   = op.get("contact_approach", "")

        user_msg = (
            f"SITE YOU ARE WRITING TO:\n"
            f"  Name: {site_name}\n"
            f"  Domain: {domain}\n"
            f"  Niche / topic area: {niche or why}\n"
            f"  Their audience: {audience}\n"
            f"  Why this site is relevant to SifuFinds: {why}\n"
            f"\nLINK OPPORTUNITY:\n"
            f"  Type: {link_type}\n"
            f"  Suggested anchor text: {anchor}\n"
            f"  Suggested approach: {approach}\n"
            f"\nUSING THE DETAILS ABOVE, write a short personalised outreach email.\n"
            f"The opening sentence must reference something specific about their site "
            f"(their niche, their audience, or what they cover) — not a generic compliment.\n"
            f"Keep it under 100 words. UK English. Sound like a real person."
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


def _fix_json_newlines(text: str) -> str:
    """Escape literal newlines inside JSON string values so json.loads can parse them."""
    result = []
    in_string = False
    i = 0
    while i < len(text):
        c = text[i]
        if c == '\\' and i + 1 < len(text):
            result.append(c)
            result.append(text[i + 1])
            i += 2
            continue
        if c == '"':
            in_string = not in_string
            result.append(c)
        elif c == '\n' and in_string:
            result.append('\\n')
        elif c == '\r' and in_string:
            result.append('\\r')
        elif c == '\t' and in_string:
            result.append('\\t')
        else:
            result.append(c)
        i += 1
    return ''.join(result)


def _parse_json_object(text: str, label: str) -> dict:
    cleaned = text.strip()

    # Strip markdown fences
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                cleaned = part
                break

    # Attempt 1 — standard parse
    try:
        result = json.loads(cleaned)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Attempt 2 — fix unescaped newlines inside string values
    try:
        result = json.loads(_fix_json_newlines(cleaned))
        if isinstance(result, dict):
            return result
    except (json.JSONDecodeError, Exception):
        pass

    # Attempt 3 — regex extraction fallback for subject/body emails
    subject_m = re.search(r'"subject"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', cleaned, re.DOTALL)
    body_m    = re.search(r'"body"\s*:\s*"(.*?)(?<!\\)"(?:\s*[},]|\s*$)', cleaned, re.DOTALL)
    if subject_m and body_m:
        subject = subject_m.group(1).replace('\\"', '"')
        body    = body_m.group(1).replace('\\"', '"').replace('\\n', '\n')
        return {"subject": subject, "body": body}

    print(f"✗ Could not parse {label} JSON. Raw: {text[:300]}")
    return {}


# ── INBOX REPLY PROMPT ────────────────────────────────────────────────────────

_REPLY_SYSTEM = f"""You are Kai, the founder of {SITE_NAME} ({SITE_URL}).
{SITE_DESC}

Someone has replied to your outreach email. Write a natural, human reply that keeps
the conversation moving. Read their message carefully and respond to what they actually said.

TONE — exactly the same as the original outreach:
- Sound like a real person replying to a colleague, not a PR manager managing a pipeline.
- Friendly, warm, conversational. Short sentences. Plain words.
- Written in UK English (colour, favourite, whilst, etc.).
- No AI-style filler phrases: no "I hope this finds you well", "as per my previous email",
  "please don't hesitate to reach out", "I look forward to hearing from you",
  "many thanks for your prompt response", "kind regards". These read as robotic.
- Match the energy of their reply — if they're brief, be brief. If they're chatty, be a bit more relaxed.
- Never be pushy or salesy. If they said no, thank them genuinely and move on.

WHAT TO DO:
- If they're interested: thank them briefly, confirm the next practical step in plain language.
- If they asked a question: answer it directly and helpfully, no waffle.
- If they declined: be gracious, wish them well, leave the door open without being sycophantic.
- If they're on the fence: keep it simple, one clear next step, no pressure.

Keep it under 120 words. Every sentence should earn its place.

Respond ONLY with valid JSON:
{{
  "subject": "Re: <their subject>",
  "body": "your reply here"
}}"""


# ── IMAP INBOX MONITOR ────────────────────────────────────────────────────────

def _decode_header(value: str) -> str:
    parts = email.header.decode_header(value or "")
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)


def _get_email_body(msg) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get("Content-Disposition"):
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    # Trim quoted history (lines starting with > or On ... wrote:)
    lines = []
    for line in body.splitlines():
        if line.startswith(">") or re.match(r"^On .{10,} wrote:$", line):
            break
        lines.append(line)
    return "\n".join(lines).strip()


def run_inbox_sync(dry_run: bool = False) -> int:
    """
    Connect to IMAP inbox, find unread emails, match against sent outreach,
    use AI to draft a reply, send it, and mark original as read.
    """
    if not SMTP_USER or not SMTP_PASS:
        print("✗ SMTP_USER / SMTP_PASS not set — cannot check inbox.")
        return 0

    state = _load_state()
    # Build lookup: sender email → domain record
    sent_map: dict[str, tuple[str, dict]] = {}
    for domain, rec in state.items():
        if domain.startswith("__"):
            continue
        sent_to = rec.get("sent_to", "")
        if sent_to and rec.get("sent_at") and not rec.get("replied"):
            sent_map[sent_to.lower()] = (domain, rec)

    print(f"\n📬 Checking inbox at {IMAP_HOST}...")

    try:
        imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        imap.login(SMTP_USER, SMTP_PASS)
        imap.select("INBOX")
    except Exception as e:
        print(f"✗ IMAP connection failed: {e}")
        log("backlinks", "inbox", "error", str(e)[:120])
        return 0

    _, msg_ids = imap.search(None, "UNSEEN")
    all_ids = msg_ids[0].split() if msg_ids[0] else []
    print(f"  {len(all_ids)} unread message(s)")

    replied = 0

    for uid in all_ids:
        try:
            _, data = imap.fetch(uid, "(RFC822)")
            raw = data[0][1]
            msg = email.message_from_bytes(raw)

            sender_raw  = msg.get("From", "")
            subject_raw = _decode_header(msg.get("Subject", ""))
            from_email  = re.search(r"[\w.+-]+@[\w.-]+\.\w+", sender_raw)
            from_email  = from_email.group(0).lower() if from_email else ""
            from_domain = from_email.split("@")[-1] if "@" in from_email else ""

            body = _get_email_body(msg)
            if not body:
                continue

            # ── Hard-bounce / MAILER-DAEMON detection ──────────────────────────
            # A bounce means the address is dead — suppress it immediately so we
            # never attempt to email it again.
            is_bounce = (
                "mailer-daemon" in sender_raw.lower()
                or "mail delivery" in subject_raw.lower()
                or "delivery status" in subject_raw.lower()
                or "undeliverable" in subject_raw.lower()
                or "delivery failed" in subject_raw.lower()
                or "failure notice" in subject_raw.lower()
                or "returned mail" in subject_raw.lower()
            )
            if is_bounce:
                # Extract the original recipient from the bounce body (best effort)
                bounce_targets = _EMAIL_RE.findall(body[:2000])
                suppressed_any = False
                for bt in bounce_targets:
                    bt_lower = bt.lower()
                    if bt_lower == SMTP_USER.lower():
                        continue  # skip our own address
                    # Only suppress addresses we actually sent to
                    if bt_lower in sent_map:
                        _add_suppressed(bt_lower)
                        domain_key = sent_map[bt_lower][0]
                        state[domain_key]["status"] = "hard_bounce"
                        suppressed_any = True
                if not suppressed_any and from_email:
                    # Fallback: suppress whatever bounced back to us
                    for sent_addr in list(sent_map.keys()):
                        if from_domain and from_domain in sent_addr:
                            _add_suppressed(sent_addr)
                            state[sent_map[sent_addr][0]]["status"] = "hard_bounce"
                imap.store(uid, "+FLAGS", "\\Seen")
                print(f"  🔴 Bounce detected from {sender_raw} — suppressed recipient(s)")
                log("backlinks", "inbox", "bounce", f"from:{sender_raw[:60]}")
                _save_state(state)
                continue

            # ── Opt-out / STOP detection ──────────────────────────────────────
            # If someone replies with STOP in the subject or body, honour it
            # immediately and never contact them again.
            is_stop = (
                subject_raw.strip().upper() == "STOP"
                or subject_raw.upper().startswith("STOP ")
                or re.search(r"\bstop\b|\bunsubscribe\b|\bremove me\b|\bopt.?out\b",
                             subject_raw + " " + body[:500], re.IGNORECASE)
            )
            if is_stop and from_email:
                _add_suppressed(from_email)
                if from_email in sent_map:
                    domain_key = sent_map[from_email][0]
                    state[domain_key]["status"] = "unsubscribed"
                    state[domain_key]["unsubscribed_at"] = datetime.now(timezone.utc).isoformat()
                imap.store(uid, "+FLAGS", "\\Seen")
                print(f"  🚫 Opt-out from {from_email} — suppressed permanently")
                log("backlinks", "inbox", "optout", f"from:{from_email}")
                _save_state(state)
                continue

            # Match against a domain we contacted — by exact sent_to or domain
            matched_domain, matched_rec = None, None
            if from_email in sent_map:
                matched_domain, matched_rec = sent_map[from_email]
            else:
                for domain, rec in state.items():
                    if not domain.startswith("__") and from_domain and from_domain in domain:
                        matched_domain, matched_rec = domain, rec
                        break

            print(f"\n  📩 From: {sender_raw}")
            print(f"     Subject: {subject_raw}")
            print(f"     Preview: {body[:120]}...")

            # Generate AI reply
            context = (
                f"Their reply:\n{body[:1000]}\n\n"
                f"Original subject we sent: {matched_rec.get('email_subject','') if matched_rec else subject_raw}\n"
                f"Their site: {matched_domain or from_domain}\n"
                f"Link type we proposed: {matched_rec.get('link_type','backlink') if matched_rec else 'backlink'}"
            )

            try:
                raw_reply = ask(_REPLY_SYSTEM, context)
            except Exception as e:
                print(f"  ✗ AI reply generation failed: {e}")
                continue

            reply_data = _parse_json_object(raw_reply, "reply")
            if not reply_data or not reply_data.get("body"):
                print(f"  ✗ Could not parse AI reply")
                continue

            reply_subject = reply_data.get("subject") or f"Re: {subject_raw}"
            reply_body    = reply_data["body"]

            if dry_run:
                print(f"\n  ── DRY RUN reply to {from_email} ──")
                print(f"  Subject: {reply_subject}")
                print(f"  Body:\n{reply_body}\n")
            else:
                try:
                    _send_smtp(from_email, reply_subject, reply_body)
                    # Mark original as read
                    imap.store(uid, "+FLAGS", "\\Seen")
                    print(f"  ✓ Replied to {from_email}")
                    log("backlinks", "inbox_reply", "sent", f"to:{from_email}")

                    # Update state
                    if matched_domain and matched_rec is not None:
                        matched_rec["replied"]      = True
                        matched_rec["replied_at"]   = datetime.now(timezone.utc).isoformat()
                        matched_rec["status"]       = "replied"
                        matched_rec["reply_from"]   = from_email
                        matched_rec["reply_preview"] = body[:300]
                        state[matched_domain]       = matched_rec

                    replied += 1
                except Exception as e:
                    print(f"  ✗ Failed to send reply to {from_email}: {e}")

        except Exception as e:
            print(f"  ✗ Error processing message {uid}: {e}")

    try:
        imap.logout()
    except Exception:
        pass

    if not dry_run and replied:
        _save_state(state)

    print(f"\n✓ Inbox sync complete — {replied} replies sent")
    log("backlinks", "inbox", "done", f"replied:{replied}")
    return replied


# ── CONTACT EMAIL DISCOVERY ───────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", re.IGNORECASE)

# Pages most likely to contain a contact email — checked in order
_CONTACT_PATHS = [
    "/contact", "/contact-us", "/about", "/about-us",
    "/write-for-us", "/contribute", "/advertise", "/advertise-with-us",
    "/partnerships", "/submit-guest-post",
]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; SifuFindsBot/1.0; "
        "+https://sifufinds.com/contact)"
    )
}

# Email prefixes tried if scraping finds nothing — ordered by deliverability.
# editorial/named prefixes first (lower spam score), generic role addresses last.
_PATTERN_PREFIXES = [
    "editor", "editorial", "news", "content",
    "hello", "team", "info", "contact",
]

# Generic role addresses that are spam-filtered more aggressively — deprioritised.
_GENERIC_PREFIXES = {"contact", "info", "hello", "team"}

# Domains we never want to return (spam traps, generic providers, etc.)
_SKIP_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "example.com"}


def _scrape_emails_from_url(url: str) -> list[str]:
    try:
        r = requests.get(url, headers=_HEADERS, timeout=8, allow_redirects=True)
        if r.status_code >= 400:
            return []
        found = _EMAIL_RE.findall(r.text)
        # Strip tracking pixels and image filenames that look like emails
        return [
            e.lower() for e in found
            if "." in e.split("@")[-1]
            and not e.endswith((".png", ".jpg", ".gif", ".svg"))
            and e.split("@")[-1] not in _SKIP_DOMAINS
        ]
    except Exception:
        return []


def find_contact_email(domain: str) -> str | None:
    """
    100% free contact discovery:
      1. Scrape /contact, /about, /write-for-us etc. for real email addresses
      2. Fall back to common prefix patterns (contact@, editor@, info@, …)
    No paid API required.
    """
    base = f"https://{domain}"

    # Check the homepage first, then dedicated contact paths
    all_found: list[str] = _scrape_emails_from_url(base)
    for path in _CONTACT_PATHS:
        if all_found:
            break
        all_found.extend(_scrape_emails_from_url(base + path))

    if all_found:
        # 1st priority: specific named/editorial addresses (highest deliverability)
        editorial_keywords = ["editor", "content", "write", "guest", "seo", "marketing", "pr", "outreach", "news"]
        for e in all_found:
            if any(k in e for k in editorial_keywords):
                return e
        # 2nd priority: anything that isn't a generic role address
        non_generic = [e for e in all_found if not any(e.startswith(p + "@") for p in _GENERIC_PREFIXES)]
        if non_generic:
            return non_generic[0]
        # Last resort: first scraped address (generic role is still better than a guess)
        return all_found[0]

    # Pattern fallback — try editorial prefixes before generic ones
    # We check if the site is reachable first; if not, still return best-guess
    site_alive = False
    try:
        r = requests.head(base, headers=_HEADERS, timeout=6, allow_redirects=True)
        site_alive = r.status_code < 500
    except Exception:
        pass

    # Always return a guess — editorial prefix is less likely to be spam-filtered
    # than contact@ which is a well-known honeypot on many sites
    return f"{_PATTERN_PREFIXES[0]}@{domain}"


# ── SMTP SEND ─────────────────────────────────────────────────────────────────

def _send_smtp(to_email: str, subject: str, body: str) -> bool:
    """
    Send a plain-text email with CAN-SPAM footer and List-Unsubscribe header.
    Raises RuntimeError for config errors or suppressed recipients.
    """
    # Suppression gate — never email hard-bounced or opted-out addresses
    if to_email.lower().strip() in _load_suppressed():
        raise RuntimeError(f"{to_email} is in suppression list — skipping")

    if not SMTP_USER or not SMTP_PASS:
        raise RuntimeError(
            "SMTP_USER and SMTP_PASS must be set in agents/python/.env to send emails.\n"
            "For Gmail: create an App Password at https://myaccount.google.com/apppasswords"
        )

    # Append CAN-SPAM-required footer to every outgoing email
    full_body = body.rstrip() + _canspam_footer()

    msg = MIMEMultipart("alternative")
    msg["Subject"]          = subject
    msg["From"]             = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"]               = to_email
    msg["Reply-To"]         = SMTP_USER
    # RFC 2369 List-Unsubscribe — honoured by Gmail, Outlook, Apple Mail
    msg["List-Unsubscribe"] = f"<mailto:{SMTP_USER}?subject=STOP>"
    msg.attach(MIMEText(full_body, "plain", "utf-8"))

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

    # ── Deliverability safety gates ────────────────────────────────────────────

    # Gate 1: Send window — Mon–Fri 08:00–17:00 UTC only
    if not dry_run and not _within_send_window():
        now_utc = datetime.now(timezone.utc)
        print(
            f"\n⏰ Outside send window ({now_utc.strftime('%A %H:%M UTC')}).\n"
            f"   Outreach emails are sent Mon–Fri 08:00–17:00 UTC only.\n"
            f"   This prevents night/weekend sends which raise spam complaint rates.\n"
            f"   Skipping send — try again during business hours."
        )
        log("backlinks", "send", "outside_window", now_utc.isoformat())
        return 0

    # Gate 2: Daily hard cap — prevents inbox suspension
    already_sent_today = _daily_send_count() if not dry_run else 0
    remaining_today = DAILY_SEND_HARD_CAP - already_sent_today
    if not dry_run and remaining_today <= 0:
        print(
            f"\n🛑 Daily send cap reached ({DAILY_SEND_HARD_CAP} emails/day).\n"
            f"   Already sent {already_sent_today} emails today (UTC).\n"
            f"   Cap resets at midnight UTC. This limit protects inbox reputation."
        )
        log("backlinks", "send", "daily_cap_reached", f"sent_today:{already_sent_today}")
        return 0

    # Honour the daily cap even within this run
    effective_limit = min(limit, remaining_today) if not dry_run else limit

    print(f"\n📤 Sending outreach to {min(len(pending), effective_limit)} targets "
          f"(limit: {effective_limit}, daily remaining: {remaining_today})...")
    sent = 0

    for domain, rec in pending:
        if sent >= effective_limit:
            break

        subject = rec.get("email_subject", "")
        body    = rec.get("email_body", "")

        if not subject or not body:
            print(f"  ✗ {domain}: no email draft — run --outreach first")
            continue

        # Warn on long email bodies
        _check_body_word_count(body, domain)

        # Find contact email
        print(f"  🔍 {domain}: finding contact email...")
        contact = find_contact_email(domain)
        if not contact:
            print(f"  ✗ {domain}: could not determine contact email — skipping")
            rec["status"] = "no_contact"
            state[domain] = rec
            continue

        # Skip suppressed addresses
        if contact.lower() in _load_suppressed():
            print(f"  🚫 {domain}: {contact} is suppressed (bounced/unsubscribed) — skipping")
            rec["status"] = "suppressed"
            state[domain] = rec
            continue

        if dry_run:
            print(f"\n── DRY RUN: {domain} → {contact} ──")
            print(f"  Subject: {subject}")
            print(f"  Body preview ({len(body.split())} words):\n{body[:300]}{'...' if len(body) > 300 else ''}\n")
            sent += 1
            continue

        try:
            _send_smtp(contact, subject, body)
            rec["sent_to"]  = contact
            rec["sent_at"]  = datetime.now(timezone.utc).isoformat()
            rec["status"]   = "sent"
            state[domain]   = rec
            _save_state(state)  # Save after every send so crashes don't lose progress
            print(f"  ✓ Sent to {contact} ({domain})")
            sent += 1
            log("backlinks", "send", "success", f"domain:{domain} to:{contact}")
        except RuntimeError as e:
            err = str(e)
            if "suppression list" in err:
                print(f"  🚫 {domain}: {err}")
                rec["status"] = "suppressed"
            else:
                # Config error — stop immediately, no point retrying
                print(f"\n✗ SMTP error: {err}")
                log("backlinks", "send", "config_error", err[:120])
                _save_state(state)
                break
            state[domain] = rec
        except Exception as e:
            print(f"  ✗ {domain}: send failed — {e}")
            rec["status"] = "send_error"
            rec["send_error"] = str(e)[:120]
            state[domain] = rec
            log("backlinks", "send", "error", f"domain:{domain} err:{str(e)[:80]}")

        if sent < effective_limit and sent < len(pending):
            delay = random.uniform(SEND_DELAY_MIN, SEND_DELAY_MAX)
            print(f"  ⏱  Waiting {delay/60:.1f} min before next send...")
            time.sleep(delay)

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
    do_inbox:     bool = False,
    do_content:   bool = False,
    dry_run:      bool = False,
    limit:        int  = DEFAULT_RESEARCH_LIMIT,
) -> None:
    log("backlinks", "start", "running")

    # Always check inbox first so replies are handled before new sends go out
    if do_inbox:
        run_inbox_sync(dry_run=dry_run)

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
    parser.add_argument("--inbox",     action="store_true", help="Check inbox for replies and auto-respond")
    parser.add_argument("--content",   action="store_true", help="Generate link-bait content strategy")
    parser.add_argument("--status",    action="store_true", help="Print pipeline dashboard and exit")
    parser.add_argument("--all",       action="store_true", help="Run all phases")
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
    do_inbox    = args.inbox    or args.all
    do_content  = args.content  or args.all

    if not any([do_research, do_outreach, do_send, do_inbox, do_content]):
        # Default: full pipeline including inbox
        do_research = do_outreach = do_send = do_inbox = True

    run(
        do_research=do_research,
        do_outreach=do_outreach,
        do_send=do_send,
        do_inbox=do_inbox,
        do_content=do_content,
        dry_run=args.dry_run,
        limit=args.limit,
    )
