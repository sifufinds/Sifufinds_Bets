"""
Brand Discovery & Lifecycle Agent — Weekly

Two jobs, both run weekly (see .github/workflows/brand_discovery.yml):

  1. DISCOVER — search for African sports-betting brands not yet reviewed
     on sifufinds.com, run each candidate through a legitimacy research
     gate (official site reachable, reads as a real betting operator, has
     an African-market signal, isn't drowning in scam complaints), and
     only if it passes, write a full review blog post + a standalone
     bookmakers/<slug>/ page. Capped at MAX_NEW_BRANDS_PER_RUN per run —
     one well-researched brand a week beats several shallow ones.

  2. VERIFY — re-research every currently-active bookmaker for signs it
     has stopped operating. A brand only gets removed on a two-strike
     basis: flagged as suspected-defunct on one weekly run, then removed
     only if it's STILL suspected-defunct on a later run. This absorbs a
     temporarily-down site or a noisy single search result without an
     immediate, irreversible removal. "Removed" never means deleted — the
     bookmakers/<slug>/ page is replaced with a live discontinued notice
     (never a 404, per this repo's anti-404 rules) and the paired blog
     review gets an editor's note instead of being deleted outright.

Both jobs write to data/bookmaker_links.json (the single source of truth
gen_blog_post_pages.py reads for BOOKMAKER_LINKS/_BK_SLUG_TO_LINK) and to
blog/posts.json. Progress and decisions are tracked in
brand_discovery_state.json (committed, so nothing is re-researched or
re-flagged from scratch every run) and brand_discovery_changelog.json (a
human-readable audit trail of every add/reject/flag/remove).

Usage:
  python agent_brand_discovery.py                    # full weekly run (discover + verify)
  python agent_brand_discovery.py --discover          # only look for new brands
  python agent_brand_discovery.py --verify            # only check existing brands for closure
  python agent_brand_discovery.py --discover --dry-run  # research only, write nothing
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm import ask, ask_long
from config import SITE_URL
from utils.serp_research import fc_search, fc_scrape, research
from utils.bookmaker_page_template import render_bookmaker_page, render_discontinued_page
from utils.notify import send_email
from gen_blog_post_pages import slugify

# ── PATHS ──────────────────────────────────────────────────────────────────

BASE = Path(__file__).parent.parent.parent
BOOKMAKER_LINKS_PATH = BASE / "data" / "bookmaker_links.json"
BOOKMAKERS_DIR = BASE / "bookmakers"
POSTS_PATH = BASE / "blog" / "posts.json"
STATE_PATH = Path(__file__).parent / "brand_discovery_state.json"
CHANGELOG_PATH = Path(__file__).parent / "brand_discovery_changelog.json"

# ── TUNABLES ──────────────────────────────────────────────────────────────

MAX_NEW_BRANDS_PER_RUN = 1
MAX_CANDIDATES_EVALUATED_PER_RUN = 5
MAX_CHANGELOG_ENTRIES = 500
MIN_NEW_BRAND_SCORE = 3.3
MAX_NEW_BRAND_SCORE = 4.3

# Who gets the "brands added/removed this run" summary email. Overridable
# without touching source via a repo secret; defaults to the site owner.
NOTIFY_EMAIL = os.getenv("BRAND_DISCOVERY_NOTIFY_EMAIL", "kai.s.manyeh@gmail.com")

AFRICAN_COUNTRIES = [
    "Nigeria", "Kenya", "Ghana", "South Africa", "Tanzania", "Uganda",
    "Zambia", "Ethiopia", "Ivory Coast", "Cameroon", "Senegal", "Rwanda",
    "Zimbabwe", "Malawi", "Mozambique", "Angola", "DR Congo", "Botswana",
    "Namibia", "Egypt", "Morocco",
]

_LEGITIMACY_KEYWORDS = ("bet", "odds", "sportsbook", "wager", "casino", "stake", "punter", "gambling")
_SCAM_KEYWORDS = ("scam", "fraud", "not paying", "unlicensed", "ponzi", "rug pull", "stole my money", "blacklisted")
_AFRICAN_SIGNAL_KEYWORDS = (
    "m-pesa", "mpesa", "opay", "palmpay", "mtn momo", "airtel money", "ecocash",
    "naira", "₦", "ksh", "kes", "ghs", "gh₵", "zar",
) + tuple(c.lower() for c in AFRICAN_COUNTRIES)

_last_rejection_reason = "unknown"

# Every brand actually added or removed this run (dry-run additions/removals
# are never appended here) — drained into one summary email at the end of
# main(). Kept as a plain module-level list rather than threaded through
# every function signature since this script is a single-shot CLI process,
# not a long-lived service where that state could leak across runs.
_run_events: list[dict] = []


# ── LLM PROMPTS ───────────────────────────────────────────────────────────

_EXTRACT_BRAND_NAMES_SYSTEM = """You extract sports betting / iGaming operator brand names from search result snippets.

Given a country and a list of search result titles/descriptions, return ONLY a JSON array of distinct betting operator brand names mentioned (e.g. ["Betika", "22Bet", "MSport"]). Rules:
- Only include names that are clearly sports betting / online casino operators, not news sites, review sites, or generic terms
- Do not include generic terms like "best betting sites" or "top bookmakers"
- Strip country/domain suffixes ("Kenya", ".com") unless they're genuinely part of the brand name
- Return [] if nothing qualifies
- Return ONLY the JSON array, nothing else"""

_BRAND_REVIEW_SYSTEM = f"""You are the Brand Research Desk for SifuFinds ({SITE_URL}), Africa's #1 independent betting comparison site. You are writing the FIRST review of a betting brand that has just passed an automated legitimacy check. You are reporting on it fairly and cautiously, not endorsing it.

ACCURACY RULES — NON-NEGOTIABLE:
- Use ONLY the research provided in the user message as your source of facts. Never invent a bonus amount, licence number, payment method, or any other specific figure that isn't in the research.
- Where a fact isn't confirmed by the research (e.g. exact bonus percentage), describe it qualitatively and tell the reader to verify current terms on the operator's own site. Never fabricate a specific number.
- This is a brand new listing with a limited track record. Be measured, not promotional — a cautious verdict is expected and correct.

VOICE — MANDATORY (write like a real UK-based sports journalist, not an LLM):
- UK English throughout: favourite not favorite, colour not color, organise not organize, side/squad not "team", full stops not periods
- NEVER use an em dash (—) or en dash (–) anywhere in the article, for any reason. Rewrite as separate sentences, commas, or parentheses instead. The article is checked mechanically for this and will be rejected if one appears.
- Vary sentence length, avoid formulaic openers ("In the world of...", "When it comes to..."), avoid repeating the same transition words
- Sound like a specific human wrote this, not a template being filled in

GEO (AI-answer-engine) RULES — MANDATORY:
- Answer "is this brand legitimate for African bettors?" directly in the first 2-3 sentences, in plain, quotable language
- Each FAQ answer must stand alone as a complete sentence needing no surrounding context
- Use the brand's full name and the primary country's full name on first mention

LINKING RULES — NON-NEGOTIABLE:
- NEVER write a markdown link to any {SITE_URL}/<path> page. The site auto-links bookmaker names, country names, and key terms after you submit — only mention them in plain text.
- Mention at least one existing African bookmaker by name for comparison context (Bet9ja, SportyBet, Betway, 1xBet, Hollywoodbets, SportPesa, or BetKing), and the primary country's name, in plain text only
- Mention at least one of FIFA, CAF, or AFCON in plain text only, so the site's external-authority auto-linker fires

STRUCTURE — MANDATORY:
- 1,000+ words
- Include a markdown comparison table (this brand's offer against at least 2 rival bookmakers on bonus/payments/markets)
- Include a "## FAQ" heading with at least 3 "###"-level questions, each with a direct, self-contained answer
- End with the exact line: *18+ | Bet Responsibly | T&Cs Apply*

OUTPUT FORMAT — return EXACTLY this structure, nothing outside the markers:

===FACTS===
{{
  "rating": 3.8,
  "score_bonus": 3.8, "score_odds": 3.8, "score_payments": 3.8, "score_app": 3.8, "score_licensing": 3.5,
  "licensing_status": "one sentence on what the research shows about licensing, or that it is unconfirmed",
  "welcome_bonus_summary": "one sentence, qualitative if the exact figure is not confirmed by research",
  "payment_methods": ["...", "..."],
  "pros": ["...", "...", "..."],
  "cons": ["...", "...", "..."],
  "faqs": [{{"q": "...", "a": "..."}}, {{"q": "...", "a": "..."}}, {{"q": "...", "a": "..."}}],
  "verdict_paragraph": "2-3 sentence measured verdict for the bookmaker page",
  "blog_title": "max 80 chars",
  "blog_slug": "url-slug-format",
  "blog_excerpt": "150-200 chars",
  "tags": ["BrandName", "PrimaryCountry"],
  "read_time": 6
}}
===BLOG===
[Full article in plain markdown, 1000+ words, following every rule above]
===END==="""

_LIVENESS_SYSTEM = """You assess whether a specific sports betting brand's operation in its primary African market is still running, from search results about it.

Respond with ONLY one JSON object: {"status": "active" or "suspected_defunct", "evidence": "one sentence citing what you found"}.

Default to "active" unless there is clear, specific evidence of closure (a news article about THIS operator's site shutting down, a licence being revoked, or the operator publicly announcing it stopped operating). An unreachable official website is a real signal but should be described accurately in the evidence field, not overstated.

CRITICAL — brands like 1xBet, Betwinner, Melbet, and 22Bet operate as many separate regional entities/licensees worldwide under the same name. A closure, lawsuit, or regulatory action reported for the brand in a DIFFERENT country, or against a similarly-named but distinct company, is NOT evidence this operator's African market presence has closed. Only count evidence that specifically names the brand's operation in or serving its primary African market.

If your evidence sentence contains hedging language ("might be", "could be related to", "possibly", "not a direct confirmation", "unclear if"), that means the evidence is NOT clear and specific — you must return "active" in that case, never "suspected_defunct". Do not guess or assume closure just because search results are sparse or mention the brand name in an unrelated context."""


# ── PARSING HELPERS (same marker format as agent_sports_blog.py) ──────────

def _extract(text: str, start: str, end: str, end_required: bool = True) -> str:
    try:
        s = text.index(start) + len(start)
        try:
            e = text.index(end, s)
            return text[s:e].strip()
        except ValueError:
            return "" if end_required else text[s:].strip()
    except ValueError:
        return ""


def _clean_json(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("```")[1]
        if s.startswith("json"):
            s = s[4:]
    return s.strip()


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


# ── STATE / CHANGELOG ────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"known_brand_names": [], "rejected_candidates": {}, "defunct_flags": {}, "runs": 0}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def _log_change(event_type: str, slug: str, name: str, evidence) -> None:
    log = []
    if CHANGELOG_PATH.exists():
        try:
            log = json.loads(CHANGELOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            log = []
    log.insert(0, {
        "type": event_type,
        "slug": slug,
        "brand_name": name,
        "at": datetime.now(timezone.utc).isoformat(),
        "evidence": evidence,
    })
    CHANGELOG_PATH.write_text(json.dumps(log[:MAX_CHANGELOG_ENTRIES], indent=2, ensure_ascii=False), encoding="utf-8")


def load_known_brand_names() -> set[str]:
    entries = _load_bookmaker_entries()
    # Match on BOTH the registry keyword ("1xbet") and the display brand_name
    # ("1xBet Africa") — a discovered candidate like "1XBET" normalizes to
    # "1xbet", which matches the keyword but not "1xbetafrica", so checking
    # brand_name alone let an already-listed brand get re-evaluated as new.
    known = {_normalize_name(e["keyword"]) for e in entries}
    known |= {_normalize_name(e.get("brand_name", e["keyword"])) for e in entries}
    state = load_state()
    known |= {_normalize_name(n) for n in state.get("known_brand_names", [])}
    known |= {_normalize_name(n) for n in state.get("rejected_candidates", {}).keys()}
    return known


def _remember_known_brand(name: str) -> None:
    state = load_state()
    names = set(state.get("known_brand_names", []))
    names.add(name)
    state["known_brand_names"] = sorted(names)
    save_state(state)


def _reject_candidate(name: str, reason: str) -> None:
    state = load_state()
    state.setdefault("rejected_candidates", {})[name] = {
        "reason": reason,
        "rejected_at": datetime.now(timezone.utc).isoformat(),
    }
    save_state(state)
    _log_change("rejected", _normalize_name(name), name, evidence=reason)


# ── data/bookmaker_links.json I/O ────────────────────────────────────────

def _load_bookmaker_entries() -> list[dict]:
    with open(BOOKMAKER_LINKS_PATH, encoding="utf-8") as f:
        return json.load(f).get("bookmakers", [])


def _save_bookmaker_entries(entries: list[dict]) -> None:
    with open(BOOKMAKER_LINKS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    data["bookmakers"] = entries
    with open(BOOKMAKER_LINKS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _unique_slug(base_slug: str) -> str:
    existing = {e["keyword"] for e in _load_bookmaker_entries()}
    if base_slug not in existing and not (BOOKMAKERS_DIR / base_slug).exists():
        return base_slug
    i = 2
    while f"{base_slug}-{i}" in existing or (BOOKMAKERS_DIR / f"{base_slug}-{i}").exists():
        i += 1
    return f"{base_slug}-{i}"


# ── blog/posts.json I/O (mirrors agent_sports_blog.py's save_posts) ──────

def load_posts() -> list[dict]:
    if POSTS_PATH.exists():
        try:
            with open(POSTS_PATH, encoding="utf-8") as f:
                return json.load(f).get("posts", [])
        except Exception:
            return []
    return []


def save_posts(posts: list[dict]) -> None:
    payload = {"posts": posts}
    with open(POSTS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    js_path = POSTS_PATH.parent / "posts-data.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(f"window.POSTS_DATA={json.dumps(payload, ensure_ascii=False)};\n")


# ── DISCOVERY ─────────────────────────────────────────────────────────────

def discover_candidate_names(count: int = MAX_CANDIDATES_EVALUATED_PER_RUN) -> list[tuple[str, str]]:
    """Search a rotating set of African countries for betting-brand mentions,
    extract candidate names via LLM, and filter out anything already known
    or previously rejected. Returns (name, country) tuples, order preserved."""
    week_seed = datetime.now(timezone.utc).isocalendar()[1]
    countries = [AFRICAN_COUNTRIES[(week_seed + i) % len(AFRICAN_COUNTRIES)] for i in range(3)]
    known = load_known_brand_names()
    year = datetime.now(timezone.utc).year
    candidates: list[tuple[str, str]] = []
    seen_norm: set[str] = set()

    for country in countries:
        results = fc_search(f"new online sports betting site {country} {year} licence", limit=6)
        if not results:
            continue
        snippet_block = "\n".join(f"- {r.get('title', '')}: {r.get('description', '')}" for r in results)
        raw = ask(_EXTRACT_BRAND_NAMES_SYSTEM, f"Country: {country}\n\nSearch results:\n{snippet_block}")
        try:
            names = json.loads(_clean_json(raw))
        except Exception:
            continue
        if not isinstance(names, list):
            continue
        for n in names:
            n = str(n).strip()
            if not n or len(n) > 40:
                continue
            norm = _normalize_name(n)
            if norm in known or norm in seen_norm:
                continue
            seen_norm.add(norm)
            candidates.append((n, country))

    return candidates[:count]


def _pick_official_url(name: str, results: list[dict]) -> str:
    norm = _normalize_name(name)
    for r in results:
        url = r.get("url", "")
        if norm and norm in _normalize_name(url):
            return url
    return results[0].get("url", "") if results else ""


def research_candidate(name: str, country: str) -> dict | None:
    """Full legitimacy research gate for one candidate. Returns a facts dict
    ready for content generation if every check passes, else None (the
    reason is left in the module-level _last_rejection_reason)."""
    global _last_rejection_reason

    site_results = fc_search(f"{name} betting official site", limit=5)
    official_url = _pick_official_url(name, site_results)
    if not official_url:
        _last_rejection_reason = "no discoverable official site"
        return None

    homepage_md = fc_scrape(official_url)
    if len(homepage_md) < 200:
        _last_rejection_reason = f"official site {official_url} unreachable or returned near-empty content"
        return None

    homepage_lower = homepage_md.lower()
    if not any(k in homepage_lower for k in _LEGITIMACY_KEYWORDS):
        _last_rejection_reason = "official site content doesn't read as a betting/casino operator"
        return None

    snippet_text = " ".join(r.get("description", "") for r in site_results).lower()
    if not any(k in homepage_lower or k in snippet_text for k in _AFRICAN_SIGNAL_KEYWORDS):
        _last_rejection_reason = "no African market signal found (country name, local currency, or local payment method)"
        return None

    rep_results = fc_search(f"{name} review complaints withdrawal", limit=6)
    rep_text = " ".join(f"{r.get('title', '')} {r.get('description', '')}" for r in rep_results).lower()
    scam_hits = sum(1 for k in _SCAM_KEYWORDS if k in rep_text)
    if scam_hits >= 3:
        _last_rejection_reason = f"reputation check found {scam_hits} scam/fraud signals across search results"
        return None

    research_block = research(f"{name} review {country}", country)
    evidence_urls = [r.get("url") for r in (site_results + rep_results) if r.get("url")][:8]

    return {
        "brand_name": name,
        "official_url": official_url,
        "primary_country": country,
        "homepage_excerpt": homepage_md[:2000],
        "research_block": research_block,
        "evidence_urls": evidence_urls,
    }


# ── CONTENT GENERATION ───────────────────────────────────────────────────

def _clamp_score(value) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        v = (MIN_NEW_BRAND_SCORE + MAX_NEW_BRAND_SCORE) / 2
    return round(min(max(v, MIN_NEW_BRAND_SCORE), MAX_NEW_BRAND_SCORE), 1)


def _validate_content(body: str, facts: dict) -> tuple[bool, str]:
    word_count = len(body.split())
    if word_count < 1000:
        return False, f"body is only {word_count} words, needs 1000+"
    if "—" in body or "–" in body:
        return False, "body contains an em dash or en dash — rewrite using separate sentences or commas instead"
    if not re.search(r"^##\s*(FAQ|Frequently Asked Questions)", body, re.MULTILINE | re.IGNORECASE):
        return False, "missing a '## FAQ' or '## Frequently Asked Questions' heading"
    if "|" not in body or "---" not in body:
        return False, "missing a markdown comparison table"
    if re.search(r"\[([^\]]+)\]\(https://sifufinds\.com/", body):
        return False, "body must not contain hand-written internal markdown links to sifufinds.com — mention names in plain text only"
    required = ("faqs", "pros", "cons", "welcome_bonus_summary", "rating", "verdict_paragraph")
    missing = [k for k in required if not facts.get(k)]
    if missing:
        return False, f"FACTS JSON missing required keys: {', '.join(missing)}"
    if len(facts.get("faqs", [])) < 3:
        return False, "FACTS.faqs needs at least 3 Q&A entries"
    return True, ""


def generate_brand_content(gate: dict) -> dict | None:
    name = gate["brand_name"]
    country = gate["primary_country"]
    user_message = f"""BRAND: {name}
PRIMARY AFRICAN MARKET: {country}
OFFICIAL SITE: {gate['official_url']}

RESEARCH — excerpt from the operator's own homepage:
{gate['homepage_excerpt']}

{gate['research_block']}

Write the review now, following every rule in the system prompt exactly."""

    for _attempt in range(2):
        raw = ask_long(_BRAND_REVIEW_SYSTEM, user_message)
        facts_raw = _extract(raw, "===FACTS===", "===BLOG===")
        blog_body = _extract(raw, "===BLOG===", "===END===", end_required=False)

        if not facts_raw or not blog_body:
            user_message += "\n\nYour previous response was missing the ===FACTS===/===BLOG===/===END=== markers. Follow the exact output format this time."
            continue
        try:
            facts = json.loads(_clean_json(facts_raw))
        except json.JSONDecodeError:
            user_message += "\n\n===FACTS=== must be valid JSON. Fix and resend the FULL output."
            continue

        ok, reason = _validate_content(blog_body, facts)
        if not ok:
            user_message += f"\n\nYour previous draft was rejected: {reason}. Fix this specific issue and resend the FULL output again."
            continue

        facts["blog_body_markdown"] = blog_body.strip()
        return facts

    return None


def add_brand(gate: dict, facts: dict, dry_run: bool) -> None:
    name = gate["brand_name"]
    slug = _unique_slug(slugify(name))
    facts["slug"] = slug
    facts["brand_name"] = name
    facts["official_url"] = gate["official_url"]
    facts["primary_country"] = gate["primary_country"]
    facts["rating"] = _clamp_score(facts.get("rating"))
    for key in ("score_bonus", "score_odds", "score_payments", "score_app", "score_licensing"):
        facts[key] = _clamp_score(facts.get(key, facts["rating"]))

    if dry_run:
        print(f"  [dry-run] Would add {name} ({slug}) — rating {facts['rating']}")
        return

    page_dir = BOOKMAKERS_DIR / slug
    page_dir.mkdir(parents=True, exist_ok=True)
    (page_dir / "index.html").write_text(render_bookmaker_page(facts), encoding="utf-8")

    entries = _load_bookmaker_entries()
    entries.append({
        "keyword": slug,
        "brand_name": name,
        "href": f"../../bookmakers/{slug}/",
        "anchor_title": f"{name} review",
        "resource_label": f"{name} Review",
        "status": "active",
        "official_url": gate["official_url"],
        "discovered_by": "agent_brand_discovery",
        "added_at": datetime.now(timezone.utc).isoformat(),
    })
    _save_bookmaker_entries(entries)

    year = datetime.now(timezone.utc).year
    post = {
        "id": f"post-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}",
        "category": "igaming",
        "title": facts.get("blog_title") or f"{name} Review {year} — Bonus, Odds & Payment Methods",
        "slug": facts.get("blog_slug") or f"{slug}-review",
        "excerpt": (facts.get("blog_excerpt") or "")[:200],
        "body": facts["blog_body_markdown"],
        "author": "iGaming Desk",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "image_color": "#0055a4",
        "image_icon": "\U0001f3ae",
        "tags": facts.get("tags") or [name, gate["primary_country"]],
        "featured": False,
        "bookmaker_featured": slug,
        "read_time": facts.get("read_time", 6),
    }
    posts = load_posts()
    posts.insert(0, post)
    save_posts(posts)

    _log_change("added", slug, name, evidence=gate["evidence_urls"])
    _remember_known_brand(name)
    _run_events.append({
        "type": "added",
        "brand_name": name,
        "country": gate["primary_country"],
        "rating": facts["rating"],
        "blog_url": f"{SITE_URL}/blog/{post['slug']}/",
        "page_url": f"{SITE_URL}/bookmakers/{slug}/",
    })
    print(f"  ✓ Added {name} ({slug}) — blog post '{post['title']}' + bookmakers/{slug}/")


def run_discovery(dry_run: bool) -> None:
    print("\U0001f50e Brand Discovery — searching for African betting brands not yet on SifuFinds...")
    candidates = discover_candidate_names()
    if not candidates:
        print("  No new candidate names surfaced this run.")
        return

    added = 0
    for name, country in candidates:
        if added >= MAX_NEW_BRANDS_PER_RUN:
            break

        global _last_rejection_reason
        _last_rejection_reason = "unknown"
        print(f"  Researching candidate: {name} ({country})...")
        gate = research_candidate(name, country)
        if gate is None:
            print(f"  ✗ Rejected {name}: {_last_rejection_reason}")
            if not dry_run:
                _reject_candidate(name, _last_rejection_reason)
            continue

        facts = generate_brand_content(gate)
        if facts is None:
            print(f"  ✗ {name} passed research but content generation failed validation twice — will retry next run")
            continue

        add_brand(gate, facts, dry_run)
        added += 1

    if added == 0:
        print("  No candidate passed the full research gate this run.")


# ── DEFUNCT VERIFICATION (two-strike) ────────────────────────────────────

_HEDGE_PHRASES = (
    "might be", "may be", "could be", "possibly", "not a direct confirmation",
    "unclear if", "unclear whether", "not confirmed", "unconfirmed",
    "appears to be associated", "seems to be related",
)


def _check_liveness(name: str, official_url: str) -> tuple[str, str]:
    reachable = True
    if official_url:
        # A single Firecrawl timeout/empty response is common transient
        # noise (seen firsthand: a 25s read timeout on an unrelated
        # candidate in the same run that flagged 4 real, still-operating
        # bookmakers as suspected-defunct). One retry before concluding
        # "unreachable" avoids treating a network hiccup as evidence of
        # closure.
        md = fc_scrape(official_url)
        if len(md) <= 200:
            md = fc_scrape(official_url)
        reachable = len(md) > 200

    signal_results = fc_search(f"{name} shut down OR closed OR ceased operations OR licence revoked", limit=5)
    signal_text = "\n".join(f"- {r.get('title', '')}: {r.get('description', '')}" for r in signal_results)

    if not reachable and not signal_results:
        return "suspected_defunct", f"official site {official_url} unreachable/empty after 2 attempts and no recent search coverage found"

    raw = ask(_LIVENESS_SYSTEM, f"BRAND: {name}\nOFFICIAL SITE REACHABLE: {reachable}\n\nSEARCH RESULTS:\n{signal_text or '(none found)'}")
    try:
        verdict = json.loads(_clean_json(raw))
        status = str(verdict.get("status", "active")).lower()
        evidence = str(verdict.get("evidence", ""))[:300]
    except Exception:
        status, evidence = "active", "liveness classification failed — defaulting to active to avoid a false removal"

    if status not in ("active", "suspected_defunct"):
        status = "active"

    # Deterministic backstop: don't just trust the model followed the
    # "hedged evidence means active" instruction in the prompt — a weaker
    # fallback-tier model (Groq 8B, reached when the 70B tier is
    # rate-limited) has already been observed returning suspected_defunct
    # with self-hedging evidence text in production. Force it back to
    # active if the evidence reads as uncertain, regardless of what status
    # field the model actually returned.
    if status == "suspected_defunct" and any(p in evidence.lower() for p in _HEDGE_PHRASES):
        status = "active"
        evidence = f"evidence was hedged/uncertain, treated as active: {evidence}"

    if not reachable and status == "active":
        status, evidence = "suspected_defunct", evidence or f"official site {official_url} unreachable after 2 attempts"
    return status, evidence


def _remove_brand(entry: dict, evidence: str) -> None:
    slug = entry["keyword"]
    name = entry.get("brand_name", slug)

    entries = _load_bookmaker_entries()
    for e in entries:
        if e["keyword"] == slug:
            e["status"] = "removed"
            e["removed_at"] = datetime.now(timezone.utc).isoformat()
            e["removal_evidence"] = evidence
    _save_bookmaker_entries(entries)

    page_dir = BOOKMAKERS_DIR / slug
    page_dir.mkdir(parents=True, exist_ok=True)
    (page_dir / "index.html").write_text(render_discontinued_page(slug, name, evidence), encoding="utf-8")

    posts = load_posts()
    note_added = False
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for post in posts:
        if post.get("bookmaker_featured") == slug and "no longer operating" not in post.get("body", "").lower():
            note = f"**Editor's note ({today}):** {name} appears to have stopped operating. This review is kept for reference only, do not deposit with {name}.\n\n"
            post["body"] = note + post.get("body", "")
            note_added = True
    if note_added:
        save_posts(posts)

    _log_change("removed", slug, name, evidence=evidence)
    _run_events.append({
        "type": "removed",
        "brand_name": name,
        "evidence": evidence,
        "page_url": f"{SITE_URL}/bookmakers/{slug}/",
    })
    print(f"  ✓ Removed {name} ({slug}) — page replaced with discontinued notice, blog post annotated")


def verify_existing_brands(dry_run: bool) -> None:
    entries = _load_bookmaker_entries()
    state = load_state()
    changed = False

    for entry in entries:
        if entry.get("status") != "active":
            continue
        slug = entry["keyword"]
        name = entry.get("brand_name", slug)
        print(f"  Checking: {name}...")
        verdict, evidence = _check_liveness(name, entry.get("official_url", ""))
        flags = state.setdefault("defunct_flags", {})

        if verdict == "active":
            if slug in flags:
                print(f"  ✓ {name} recovered — clearing prior defunct flag")
                del flags[slug]
                changed = True
            continue

        if slug not in flags:
            flags[slug] = {
                "first_flagged_at": datetime.now(timezone.utc).isoformat(),
                "evidence": evidence,
                "runs_flagged": 1,
            }
            changed = True
            _log_change("flagged", slug, name, evidence=evidence)
            print(f"  ⚠ {name} flagged as suspected defunct (strike 1): {evidence}")
            continue

        flags[slug]["runs_flagged"] += 1
        flags[slug]["evidence"] = evidence
        changed = True
        print(f"  ⚠ {name} still suspected defunct (strike {flags[slug]['runs_flagged']}): {evidence}")

        if flags[slug]["runs_flagged"] >= 2:
            if dry_run:
                print(f"  [dry-run] Would remove {name} ({slug}) — two-strike confirmed")
            else:
                _remove_brand(entry, evidence)
            del flags[slug]

    if changed and not dry_run:
        save_state(state)


# ── NOTIFICATION ──────────────────────────────────────────────────────────

def _send_run_summary_email() -> None:
    """Email NOTIFY_EMAIL a summary of every brand added/removed this run.
    No-op if nothing changed (dry runs, or a run where every candidate was
    rejected and every active brand stayed active never send anything) —
    "always email me the brands you add or remove" means never skip it
    when something happened, not a weekly empty inbox ping."""
    if not _run_events:
        return

    added = [e for e in _run_events if e["type"] == "added"]
    removed = [e for e in _run_events if e["type"] == "removed"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subject = f"SifuFinds Brand Discovery — {len(added)} added, {len(removed)} removed ({today})"

    lines = [f"Weekly brand discovery run — {today} UTC", ""]

    if added:
        lines.append(f"ADDED ({len(added)}):")
        for e in added:
            lines.append(f"  • {e['brand_name']} ({e['country']}) — rating {e['rating']}/5")
            lines.append(f"    Review: {e['blog_url']}")
            lines.append(f"    Page:   {e['page_url']}")
        lines.append("")

    if removed:
        lines.append(f"REMOVED ({len(removed)}):")
        for e in removed:
            lines.append(f"  • {e['brand_name']}")
            lines.append(f"    Evidence: {e['evidence']}")
            lines.append(f"    Page: {e['page_url']} (now shows a discontinued notice, kept live, not deleted)")
        lines.append("")

    lines.append("— SifuFinds Brand Discovery Agent (agents/python/agent_brand_discovery.py)")
    send_email(NOTIFY_EMAIL, subject, "\n".join(lines))


# ── CLI ───────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="SifuFinds Weekly Brand Discovery & Lifecycle Agent")
    parser.add_argument("--discover", action="store_true", help="Search for and research new brands")
    parser.add_argument("--verify", action="store_true", help="Re-verify existing brands for signs of closure")
    parser.add_argument("--dry-run", action="store_true", help="Research only, write nothing")
    args = parser.parse_args()

    if not args.discover and not args.verify:
        args.discover = args.verify = True

    state = load_state()
    state["runs"] = state.get("runs", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    if args.discover:
        run_discovery(args.dry_run)
    if args.verify:
        print("\n\U0001fa7a Brand Verification — checking active bookmakers for signs of closure...")
        verify_existing_brands(args.dry_run)

    _send_run_summary_email()


if __name__ == "__main__":
    main()
