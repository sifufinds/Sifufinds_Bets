"""
agent_match_post.py — Premium Match/Event Post Generator for SifuFinds

Given a match or event ("Team A vs Team B"), builds a premium social post for
Telegram, Facebook, Instagram, and X (Twitter), using ONLY verified data already
scraped into data/predictions.json / data/tips.json / data/live.json (never
invents stats, odds, bookmakers, or bonuses). Posts to Telegram immediately
using the same Telethon + bot-token pipeline as agent_telegram_offers.py.

Telegram layout is a compact tip-card (Date / League / Match / Kick off / Pick
/ Odds) modelled on the user-supplied reference screenshot (Eagle Predict's
channel), followed by SifuFinds' own bookmaker-recommendation + CTA block.
Each post is auto-numbered ("Football Tip 3") via a small daily counter in
match_post_state.json, reset at UTC midnight per sport.

Every post ends with a text engagement prompt inviting readers to react
(🔥/🤔/❤️). Telegram's *native* tap-to-react menu (the reaction bar seen under
other channels' posts) is a channel-wide setting the Bot API does not expose —
confirmed by testing: setChatAvailableReactions returns 404 even with the bot
as a full channel admin, while every other Bot API call (getChat, sendMessage,
etc.) succeeds with the same token. Turn it on once, manually, in the Telegram
app: SifuFinds channel → Edit → Reactions → enable (pick specific emoji or
"All Reactions") — after that one-time toggle, every post (including these)
will show the native reaction bar automatically.

Supported sports with an existing real data source (auto-lookup):
  football   → data/predictions.json + data/tips.json
  basketball, tennis, cricket, rugby → data/live.json (ESPN feed)

Sports with no scraper in this repo (boxing, ufc, casino, other) must be
posted with --manual + explicit real details — the script still refuses to
invent anything, it just can't look the event up itself.

Usage:
  python3 agent_match_post.py "Manchester United vs Arsenal"
  python3 agent_match_post.py "Lakers vs Celtics" --sport basketball
  python3 agent_match_post.py "Spain vs Argentina" --no-telegram   # preview only
  python3 agent_match_post.py "Real Madrid vs Barcelona" --dry-run # print, don't send
  python3 agent_match_post.py "Fury vs Usyk 2" --sport boxing --manual \\
      --competition "Undisputed Heavyweight Title" --kickoff "20:00 UTC, 21 Jul" \\
      --pick "Usyk on points" --odds "Usyk:1.80" --odds "Fury:2.05" --odds-source Betway
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import log
from utils.affiliate_links import masked_url, pick_cta, cta_html, cta_plain, promo_code_line, CTA_CLAIM_BONUS, CTA_BET_NOW
from utils.tweet_text import tweet_len as _tweet_len, trim_to_limit as _trim_to_limit
from agent_telegram_offers import (
    BRANDS,
    AFFILIATE_BRANDS,
    _stars,
    send_to_channel,
    SITE_URL,
)
from agent3_social import post_facebook, post_instagram
from agent_twitter_posts import _post_tweet as post_twitter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PRED_JSON = REPO_ROOT / "data" / "predictions.json"
TIPS_JSON = REPO_ROOT / "data" / "tips.json"
LIVE_JSON = REPO_ROOT / "data" / "live.json"
STATE_FILE = Path(__file__).parent / "match_post_state.json"
CTA_ROTATION_STATE_FILE = Path(__file__).parent / "cta_rotation_state.json"

_BRAND_BY_NAME = {b["name"].lower(): b for b in BRANDS}

# Sports backed by data/live.json (ESPN feed) — no draw outcome
LIVE_JSON_SPORTS = {"basketball", "tennis", "cricket", "rugby"}
NO_DRAW_SPORTS = {"basketball", "tennis", "cricket", "rugby", "boxing", "ufc", "baseball"}
NO_LEAGUE_SPORTS = {"boxing", "ufc", "casino", "other"}  # "Event:" instead of "League:"

SPORT_META = {
    "football":   {"emoji": "⚽", "tag": "#Football", "label": "Football"},
    "basketball": {"emoji": "🏀", "tag": "#NBA #Basketball", "label": "Basketball"},
    "tennis":     {"emoji": "🎾", "tag": "#Tennis", "label": "Tennis"},
    "cricket":    {"emoji": "🏏", "tag": "#Cricket", "label": "Cricket"},
    "rugby":      {"emoji": "🏉", "tag": "#Rugby", "label": "Rugby"},
    "boxing":     {"emoji": "🥊", "tag": "#Boxing", "label": "Boxing"},
    "ufc":        {"emoji": "🥋", "tag": "#UFC #MMA", "label": "UFC"},
    "casino":     {"emoji": "🎰", "tag": "#Casino #iGaming", "label": "Casino"},
    "other":      {"emoji": "🏆", "tag": "#SifuFinds", "label": "SifuFinds"},
}


# ── MATCH LOOKUP — FOOTBALL (predictions.json + tips.json) ───────────────────

def _split_teams(query: str) -> tuple[str, str]:
    parts = re.split(r"\s+(?:vs\.?|v\.?|against)\s+", query.strip(), maxsplit=1, flags=re.I)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return query.strip(), ""


def _split_combined(raw: str) -> tuple[str, str]:
    """Split a 'DATE · TIME'-style display string. Returns ('', raw) if there's
    no separator — never guesses which half is which."""
    if " · " in raw:
        a, b = raw.split(" · ", 1)
        return a.strip(), b.strip()
    return "", raw.strip()


def _tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def _team_match_score(query_team: str, candidate_team: str) -> float:
    qt, ct = _tokens(query_team), _tokens(candidate_team)
    if not qt or not ct:
        return 0.0
    overlap = len(qt & ct)
    return overlap / max(len(qt), 1)


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _best_prediction_match(home_q: str, away_q: str) -> tuple[dict | None, float]:
    best, best_score = None, 0.0
    for pred in _load_json(PRED_JSON).get("predictions", []):
        s = _team_match_score(home_q, pred.get("home", "")) + _team_match_score(away_q, pred.get("away", ""))
        s_swapped = _team_match_score(home_q, pred.get("away", "")) + _team_match_score(away_q, pred.get("home", ""))
        score = max(s, s_swapped)
        if score > best_score:
            best_score = score
            date_raw, time_raw = _split_combined(pred.get("ko_display", ""))
            best = {
                "sport": "football",
                "source": "prediction",
                "home": pred.get("home", ""),
                "away": pred.get("away", ""),
                "competition": pred.get("competition", ""),
                "ko_utc": pred.get("ko_utc"),
                "date_raw": date_raw,
                "time_raw": time_raw,
                "pick_label": pred.get("match_winner_label", ""),
                "confidence": pred.get("confidence"),
                "home_odds": pred.get("home_odds", ""),
                "draw_odds": pred.get("draw_odds", ""),
                "away_odds": pred.get("away_odds", ""),
                "over25": pred.get("over25", ""),
                "btts": pred.get("btts", ""),
                "correct_score": pred.get("correct_score", ""),
                "odds_via": None,
            }
    return best, best_score


def _best_tip_match(home_q: str, away_q: str) -> tuple[dict | None, float]:
    best, best_score = None, 0.0
    for tip in _load_json(TIPS_JSON).get("tips", []):
        th, ta = _split_teams(tip.get("match", ""))
        s = _team_match_score(home_q, th) + _team_match_score(away_q, ta)
        s_swapped = _team_match_score(home_q, ta) + _team_match_score(away_q, th)
        score = max(s, s_swapped)
        if score > best_score:
            best_score = score
            best = {
                "sport": "football",
                "source": "tip",
                "home": th,
                "away": ta,
                "competition": tip.get("league", ""),
                "ko_utc": None,
                "date_raw": tip.get("date", ""),
                "time_raw": tip.get("time", "TBD"),
                "pick_label": tip.get("pred", ""),
                "confidence": tip.get("conf"),
                "home_odds": "",
                "draw_odds": "",
                "away_odds": "",
                "over25": "",
                "btts": "",
                "correct_score": "",
                "odds_via": {"odds": tip.get("odds", ""), "brand": tip.get("via", "")},
            }
    return best, best_score


_MERGEABLE_FIELDS = [
    "confidence", "home_odds", "draw_odds", "away_odds",
    "over25", "btts", "correct_score", "odds_via",
    "ko_utc", "date_raw", "time_raw", "pick_label",
]


def find_football_match(query: str) -> dict | None:
    """Merge the richer of predictions.json / tips.json for the same real match
    rather than discarding whichever source scored lower."""
    home_q, away_q = _split_teams(query)

    pred_match, pred_score = _best_prediction_match(home_q, away_q)
    tip_match, tip_score = _best_tip_match(home_q, away_q)

    if pred_score < 1.2 and tip_score < 1.2:
        return None

    primary, secondary = (pred_match, tip_match) if pred_score >= tip_score else (tip_match, pred_match)
    secondary_score = tip_score if primary is pred_match else pred_score

    if secondary is not None and secondary_score >= 1.2:
        for field in _MERGEABLE_FIELDS:
            if not primary.get(field) and secondary.get(field):
                primary[field] = secondary[field]

    return primary


# ── MATCH LOOKUP — LIVE.JSON SPORTS (basketball, tennis, cricket, rugby) ─────

def find_live_json_match(query: str, sport: str) -> dict | None:
    """ESPN-fed events already carry real moneyline odds — never fabricated.
    Skips completed games (site-wide 'no stale matches' rule) and derives a
    pick from whichever side has the shorter odds, since live.json has no
    separate prediction model output the way football does."""
    home_q, away_q = _split_teams(query)
    best, best_score = None, 0.0

    for e in _load_json(LIVE_JSON).get("events", []):
        if e.get("key") != sport or e.get("complete"):
            continue
        s = _team_match_score(home_q, e.get("home", "")) + _team_match_score(away_q, e.get("away", ""))
        s_swapped = _team_match_score(home_q, e.get("away", "")) + _team_match_score(away_q, e.get("home", ""))
        score = max(s, s_swapped)
        if score > best_score:
            best_score = score
            h_odds, a_odds = e.get("h") or 0.0, e.get("a") or 0.0
            if h_odds and a_odds:
                pick_label = f"{e['home']} to win" if h_odds < a_odds else f"{e['away']} to win"
            else:
                pick_label = ""
            date_raw, time_raw = _split_combined(e.get("time", ""))
            best = {
                "sport": sport,
                "source": "live",
                "home": e.get("home", ""),
                "away": e.get("away", ""),
                "competition": e.get("league", ""),
                "ko_utc": None,
                "date_raw": date_raw,
                "time_raw": time_raw,
                "pick_label": pick_label,
                "confidence": None,
                "home_odds": h_odds or "",
                "draw_odds": "",
                "away_odds": a_odds or "",
                "over25": "",
                "btts": "",
                "correct_score": "",
                "odds_via": {"odds": h_odds or a_odds, "brand": e.get("hBk") or e.get("aBk") or ""}
                if (e.get("hBk") or e.get("aBk")) else None,
            }

    if best_score < 1.2:
        return None
    return best


def find_match(query: str, sport: str = "football") -> dict | None:
    if sport == "football":
        return find_football_match(query)
    if sport in LIVE_JSON_SPORTS:
        return find_live_json_match(query, sport)
    return None  # boxing / ufc / casino / other → use --manual


def build_manual_record(args: argparse.Namespace) -> dict:
    """Build a record from explicit, real facts supplied on the command line —
    used for sports with no scraper in this repo (boxing, UFC, casino, other)."""
    home, away = _split_teams(args.match)
    odds_via = None
    if args.odds:
        label, price = args.odds[0].split(":", 1)
        odds_via = {"odds": price.strip(), "brand": args.odds_source or ""}
    return {
        "sport": args.sport,
        "source": "manual",
        "home": home,
        "away": away or "",
        "competition": args.competition or "",
        "ko_utc": None,
        "date_raw": "",
        "time_raw": args.kickoff or "",
        "pick_label": args.pick or "",
        "confidence": None,
        "home_odds": "",
        "draw_odds": "",
        "away_odds": "",
        "over25": "",
        "btts": "",
        "correct_score": "",
        "odds_via": odds_via,
        "manual_odds": args.odds or [],
    }


# ── DATE/TIME + TIP NUMBERING ─────────────────────────────────────────────────

def format_date_time(m: dict) -> tuple[str, str]:
    """Return (DD/MM/YYYY, time display) from whatever the record carries.
    Never invents a date — returns '' for whichever half isn't available."""
    iso = m.get("ko_utc")
    if iso:
        try:
            dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y"), dt.strftime("%H:%M UTC")
        except Exception:
            pass

    time_display = m.get("time_raw", "")
    raw_date = m.get("date_raw", "")
    if raw_date:
        try:
            dt = datetime.strptime(raw_date, "%d %b %Y")
            return dt.strftime("%d/%m/%Y"), time_display
        except ValueError:
            pass
        try:
            dt = datetime.strptime(f"{raw_date} {datetime.now(timezone.utc).year}", "%d %b %Y")
            return dt.strftime("%d/%m/%Y"), time_display
        except ValueError:
            return raw_date, time_display
    return "", time_display


def next_tip_number(sport: str) -> int:
    """Sequential daily counter per sport, e.g. 'Football Tip 3' — resets at
    UTC midnight, mirroring how reference tipster channels number their posts."""
    state = _load_json(STATE_FILE)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("date") != today:
        state = {"date": today, "counters": {}}
    counters = state.setdefault("counters", {})
    counters[sport] = counters.get(sport, 0) + 1
    STATE_FILE.write_text(json.dumps(state, indent=2))
    return counters[sport]


# ── PICK / ODDS LINES ─────────────────────────────────────────────────────────

def format_pick_line(m: dict) -> str:
    return f"✅ {m.get('pick_label') or 'See stats — no clear lean yet'}"


def format_odds_line(m: dict) -> str:
    if m.get("odds_via") and m["odds_via"].get("odds"):
        bk = (m["odds_via"].get("brand") or "").upper()
        price = m["odds_via"]["odds"]
        return f"✅ Odds @{price} on {bk}" if bk else f"✅ Odds @{price}"
    if m.get("manual_odds"):
        parts = []
        for line in m["manual_odds"]:
            label, price = line.split(":", 1)
            parts.append(f"{label.strip()} @{price.strip()}")
        return "✅ Odds: " + " · ".join(parts)
    if m.get("home_odds") or m.get("draw_odds") or m.get("away_odds"):
        if m["sport"] in NO_DRAW_SPORTS:
            return f"✅ Odds — {m['home']} {m.get('home_odds') or 'N/A'} · {m['away']} {m.get('away_odds') or 'N/A'}"
        return (
            f"✅ Odds — Home {m.get('home_odds') or 'N/A'} · "
            f"Draw {m.get('draw_odds') or 'N/A'} · Away {m.get('away_odds') or 'N/A'}"
        )
    return ""


def format_extra_lines(m: dict) -> list[str]:
    """A couple of optional extra ✅ lines when the data has them — capped so
    the card stays as compact as the reference, not a wall of stats."""
    lines: list[str] = []
    if m.get("confidence") is not None:
        lines.append(f"✅ Confidence: {m['confidence']}%")
    if m.get("over25"):
        lines.append(f"✅ Goals: {m['over25']}")
    if m.get("btts"):
        lines.append(f"✅ {m['btts']}")
    return lines[:2]


def _load_cta_rotation_state() -> dict:
    if CTA_ROTATION_STATE_FILE.exists():
        try:
            return json.loads(CTA_ROTATION_STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_index": -1}


def pick_cta_brand() -> dict:
    """Round-robins through every brand with a real affiliate link — the only
    ones we push CTAs to — so accumulator, match-tip, and casino posts rotate
    across all partner brands over time. Previously `max(AFFILIATE_BRANDS,
    key=lambda b: b["stars"])`, which always resolved to the same brand since
    Python's max() keeps the first entry on a tie: whichever brand happened to
    be listed first in agent_telegram_offers.BRANDS at the top star rating
    (1xBet) won every single post, so most partner brands never actually
    appeared here even after being added. Mirrors the oldest-first round-robin
    agent_telegram_offers._next_brand() already uses for the welcome-bonus
    rotation, in its own state file since this covers a different set of post
    types on a different cadence."""
    state = _load_cta_rotation_state()
    n = len(AFFILIATE_BRANDS)
    idx = (state.get("last_index", -1) + 1) % n
    state["last_index"] = idx
    CTA_ROTATION_STATE_FILE.write_text(json.dumps(state, indent=2))
    return AFFILIATE_BRANDS[idx]


def build_bookmaker_block(cta: dict, html: bool) -> str:
    """Trust bar (real licence/withdrawal/cash-out facts from BRANDS, never invented)
    plus a dual-path CTA — new vs. already-registered readers convert differently,
    a standard affiliate-marketing pattern, not just one generic 'click here' link.
    Both CTAs use the masked sifufinds.com/<brand> link, never the raw affiliate
    tracking URL (see utils/affiliate_links.py)."""
    def b(s: str) -> str:
        return f"<b>{s}</b>" if html else s

    trust_bits = [cta["licence"]]
    if cta.get("instant_withdrawal"):
        trust_bits.append("⚡ instant withdrawals")
    if cta.get("cashout"):
        trust_bits.append("💸 cash-out available")
    trust_line = " · ".join(trust_bits)

    claim_link = cta_html(cta, label=CTA_CLAIM_BONUS) if html else cta_plain(cta, label=CTA_CLAIM_BONUS)
    bet_link = cta_html(cta, label=CTA_BET_NOW) if html else cta_plain(cta, label=CTA_BET_NOW)

    block = (
        f"🏅 {b(cta['name'])} {_stars(cta['stars'])} — {cta['tag']}\n"
        f"🛡 {trust_line}\n"
        f"💰 {b(cta['welcome'])}\n\n"
        f"🎁 New here? {claim_link}\n"
        f"✅ Already registered? {bet_link}"
    )

    promo_line = promo_code_line(cta["name"], html=html)
    if promo_line:
        block += f"\n🎟 {promo_line}"

    return block


# ── TIP CARD (shared structure, HTML for Telegram / plain for other platforms) ─

def build_tip_card(m: dict, tip_num: int, html: bool) -> str:
    meta = SPORT_META.get(m["sport"], SPORT_META["other"])
    date_display, time_display = format_date_time(m)
    matchup = f"{m['home']} - {m['away']}" if m.get("away") else m["home"]
    comp_label = "Event" if m["sport"] in NO_LEAGUE_SPORTS else "League"

    def b(s: str) -> str:
        return f"<b>{s}</b>" if html else s

    title = f"{meta['label']} Tip {tip_num}"
    lines = [f"{meta['emoji']} {b(title)} {meta['emoji']}", ""]
    if date_display:
        lines.append(f"{b('Date:')} {date_display}")
    if m.get("competition"):
        lines.append(f"{b(comp_label + ':')} {m['competition']}")
    lines.append(f"{b('Match:')} {matchup}")
    if time_display:
        lines.append(f"{b('Kick off:')} {time_display}")
    lines.append("")
    lines.append(format_pick_line(m))
    odds_line = format_odds_line(m)
    if odds_line:
        lines.append(odds_line)
    lines.extend(format_extra_lines(m))
    return "\n".join(lines)


# ── PLATFORM FORMATTERS (generous spacing for mobile readability) ───────────

_REACT_PROMPT_TG = "💬 Tap a reaction below — 🔥 backing this pick · 🤔 not convinced · ❤️ love the analysis"
_REACT_PROMPT_FB = "💬 React below — 🔥 if you're backing this, 🤔 if you're not sure!"


def build_telegram_post(m: dict, cta: dict, tip_num: int) -> str:
    meta = SPORT_META.get(m["sport"], SPORT_META["other"])
    card = build_tip_card(m, tip_num, html=True)
    return (
        f"{card}\n\n"
        f"{build_bookmaker_block(cta, html=True)}\n\n"
        f"🌐 Visit <a href=\"{SITE_URL}\">SifuFinds.com</a> for more {meta['label'].lower()} tips, "
        f"predictions, bookmaker reviews, and exclusive bonuses.\n\n"
        f"{_REACT_PROMPT_TG}\n\n"
        f"🔞 18+ | Gamble Responsibly"
    )


def build_facebook_post(m: dict, cta: dict, tip_num: int) -> str:
    meta = SPORT_META.get(m["sport"], SPORT_META["other"])
    card = build_tip_card(m, tip_num, html=False)
    return (
        f"{card}\n\n"
        f"{build_bookmaker_block(cta, html=False)}\n\n"
        f"🌐 More tips, predictions, and bookmaker reviews at {SITE_URL}\n\n"
        f"{_REACT_PROMPT_FB}\n\n"
        f"🔞 18+ | Gamble Responsibly"
    )


def build_instagram_post(m: dict, cta: dict, tip_num: int) -> str:
    meta = SPORT_META.get(m["sport"], SPORT_META["other"])
    card = build_tip_card(m, tip_num, html=False)
    hashtags = (
        f"#SifuFinds #BettingTips {meta['tag']} #AfricanBetting #SportsBetting "
        f"#{cta['name'].replace(' ', '')}"
    )
    return (
        f"{card}\n\n"
        f"{build_bookmaker_block(cta, html=False)}\n\n"
        f"👉 Link in bio for the full breakdown + bonus\n"
        f"❤️🔥 Double-tap and drop a comment with your score prediction!\n\n"
        f"🔞 18+ | Gamble Responsibly\n"
        f".\n.\n.\n{hashtags}"
    )




def build_twitter_post(m: dict, cta: dict, tip_num: int) -> str:
    meta = SPORT_META.get(m["sport"], SPORT_META["other"])
    matchup = f"{m['home']} vs {m['away']}" if m.get("away") else m["home"]
    tweet = (
        f"{meta['emoji']} {meta['label']} Tip {tip_num}: {matchup}\n\n"
        f"{format_pick_line(m)}\n"
        f"{format_odds_line(m)}\n\n"
        f"🎁 {cta['name']}: {cta['welcome']}\n"
        f"👉 {cta_plain(cta)}\n\n"
        f"#SifuFinds {meta['tag']} 🔞 18+"
    )
    return _trim_to_limit(tweet)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def run(args: argparse.Namespace) -> None:
    log("match_post", "start", "running", args.match)

    if args.manual:
        m = build_manual_record(args)
    else:
        m = find_match(args.match, sport=args.sport)

    if not m:
        print(
            f"✗ No verified data found for '{args.match}' (sport: {args.sport}).\n"
            f"  Refusing to invent stats, odds, or a bookmaker recommendation.\n"
            f"  Either wait for the next data refresh, or re-run with --manual and "
            f"pass real details via --competition/--kickoff/--pick/--odds."
        )
        log("match_post", "lookup", "failed", args.match)
        sys.exit(1)

    cta = pick_cta_brand()
    tip_num = next_tip_number(args.sport)

    telegram_text  = build_telegram_post(m, cta, tip_num)
    facebook_text  = build_facebook_post(m, cta, tip_num)
    instagram_text = build_instagram_post(m, cta, tip_num)
    twitter_text   = build_twitter_post(m, cta, tip_num)

    print("\n" + "═" * 60)
    print("TELEGRAM (auto-posting)" if args.telegram and not args.dry_run else "TELEGRAM (preview)")
    print("═" * 60)
    print(telegram_text)
    print("\n" + "─" * 60)
    print("FACEBOOK (copy/paste)")
    print("─" * 60)
    print(facebook_text)
    print("\n" + "─" * 60)
    print("INSTAGRAM (copy/paste)")
    print("─" * 60)
    print(instagram_text)
    print("\n" + "─" * 60)
    print("X / TWITTER (copy/paste)")
    print("─" * 60)
    print(twitter_text)
    print("═" * 60 + "\n")

    if args.dry_run:
        print("Dry run — nothing sent.")
        return

    results: dict[str, bool] = {}

    if args.telegram:
        results["telegram"] = send_to_channel(telegram_text)
        print("✓ Posted to Telegram." if results["telegram"] else "✗ Telegram post failed — check TELEGRAM_BOT_TOKEN / session creds.")

    if args.facebook:
        results["facebook"] = post_facebook(facebook_text)
        print("✓ Posted to Facebook." if results["facebook"] else "✗ Facebook post failed or not configured (see agents/python/SETUP.md Step 3).")

    if args.instagram:
        results["instagram"] = post_instagram(instagram_text)
        print("✓ Posted to Instagram." if results["instagram"] else "✗ Instagram post failed or not configured (see agents/python/SETUP.md Step 3).")

    if args.twitter:
        results["twitter"] = post_twitter(twitter_text)
        print("✓ Posted to X/Twitter." if results["twitter"] else "✗ X/Twitter post failed or not configured (needs TWITTER_SESSION or X_USERNAME+X_PASSWORD in .env).")

    for platform, ok in results.items():
        log("match_post", platform, "success" if ok else "failed", m["home"])

    if results and not any(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Premium Match/Event Post Generator")
    parser.add_argument("match", type=str, help='Match/event query, e.g. "Manchester United vs Arsenal"')
    parser.add_argument(
        "--sport", default="football",
        choices=["football", "basketball", "tennis", "cricket", "rugby", "boxing", "ufc", "casino", "other"],
        help="Sport/vertical (default: football)",
    )
    parser.add_argument("--manual", action="store_true", help="Supply real details manually instead of auto-lookup")
    parser.add_argument("--competition", type=str, default="", help="Manual mode: league/event name")
    parser.add_argument("--kickoff", type=str, default="", help="Manual mode: kickoff/start time")
    parser.add_argument("--pick", type=str, default="", help="Manual mode: the betting pick")
    parser.add_argument("--odds", action="append", default=[], help='Manual mode: "Label:Price", repeatable')
    parser.add_argument("--odds-source", type=str, default="", help="Manual mode: bookmaker the odds came from")
    parser.add_argument("--no-telegram", dest="telegram", action="store_false", help="Don't auto-post to Telegram")
    parser.add_argument("--no-facebook", dest="facebook", action="store_false", help="Don't auto-post to Facebook")
    parser.add_argument("--no-instagram", dest="instagram", action="store_false", help="Don't auto-post to Instagram")
    parser.add_argument("--no-twitter", dest="twitter", action="store_false", help="Don't auto-post to X/Twitter")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, send nothing")
    args = parser.parse_args()
    run(args)
