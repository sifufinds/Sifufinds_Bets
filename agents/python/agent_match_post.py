"""
agent_match_post.py — Premium Match/Event Post Generator for SifuFinds

Given a match or event ("Team A vs Team B"), builds a premium social post for
Telegram, Facebook, Instagram, and X (Twitter), using ONLY verified data already
scraped into data/predictions.json / data/tips.json / data/live.json (never
invents stats, odds, bookmakers, or bonuses). Posts to Telegram immediately
using the same Telethon + bot-token pipeline as agent_telegram_offers.py.

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
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import log
from agent_telegram_offers import (
    BRANDS,
    AFFILIATE_BRANDS,
    _stars,
    send_to_channel,
    SITE_URL,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PRED_JSON = REPO_ROOT / "data" / "predictions.json"
TIPS_JSON = REPO_ROOT / "data" / "tips.json"
LIVE_JSON = REPO_ROOT / "data" / "live.json"

_BRAND_BY_NAME = {b["name"].lower(): b for b in BRANDS}

# Sports backed by data/live.json (ESPN feed) — no draw outcome
LIVE_JSON_SPORTS = {"basketball", "tennis", "cricket", "rugby"}
NO_DRAW_SPORTS = {"basketball", "tennis", "cricket", "rugby", "boxing", "ufc", "baseball"}

SPORT_META = {
    "football":   {"emoji": "⚽", "tag": "#Football", "label": "Match"},
    "basketball": {"emoji": "🏀", "tag": "#NBA #Basketball", "label": "Game"},
    "tennis":     {"emoji": "🎾", "tag": "#Tennis", "label": "Match"},
    "cricket":    {"emoji": "🏏", "tag": "#Cricket", "label": "Match"},
    "rugby":      {"emoji": "🏉", "tag": "#Rugby", "label": "Match"},
    "boxing":     {"emoji": "🥊", "tag": "#Boxing", "label": "Fight"},
    "ufc":        {"emoji": "🥋", "tag": "#UFC #MMA", "label": "Fight"},
    "casino":     {"emoji": "🎰", "tag": "#Casino #iGaming", "label": "Promo"},
    "other":      {"emoji": "🏆", "tag": "#SifuFinds", "label": "Event"},
}


# ── MATCH LOOKUP — FOOTBALL (predictions.json + tips.json) ───────────────────

def _split_teams(query: str) -> tuple[str, str]:
    parts = re.split(r"\s+(?:vs\.?|v\.?|against)\s+", query.strip(), maxsplit=1, flags=re.I)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return query.strip(), ""


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
            best = {
                "sport": "football",
                "source": "prediction",
                "home": pred.get("home", ""),
                "away": pred.get("away", ""),
                "competition": pred.get("competition", ""),
                "ko_display": pred.get("ko_display", ""),
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
                "ko_display": f"{tip.get('time','TBD')} · {tip.get('date','')}".strip(" ·"),
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
    "over25", "btts", "correct_score", "odds_via", "ko_display", "pick_label",
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
            best = {
                "sport": sport,
                "source": "live",
                "home": e.get("home", ""),
                "away": e.get("away", ""),
                "competition": e.get("league", ""),
                "ko_display": e.get("time", ""),
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
        odds_via = {"odds": price.strip(), "brand": args.odds_source or "see below"}
    return {
        "sport": args.sport,
        "source": "manual",
        "home": home,
        "away": away or "",
        "competition": args.competition or "",
        "ko_display": args.kickoff or "",
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


# ── STATS + PICK BUILDING ─────────────────────────────────────────────────────

def build_stats(m: dict) -> list[str]:
    stats: list[str] = []
    if m.get("confidence") is not None:
        stats.append(f"📈 Model confidence: {m['confidence']}%")
    if m.get("home_odds") or m.get("draw_odds") or m.get("away_odds"):
        if m["sport"] in NO_DRAW_SPORTS:
            stats.append(f"💹 Odds — {m['home']} {m.get('home_odds') or 'N/A'} · {m['away']} {m.get('away_odds') or 'N/A'}")
        else:
            stats.append(
                f"💹 1X2 odds — Home {m.get('home_odds') or 'N/A'} · "
                f"Draw {m.get('draw_odds') or 'N/A'} · Away {m.get('away_odds') or 'N/A'}"
            )
    if m.get("manual_odds"):
        for line in m["manual_odds"]:
            label, price = line.split(":", 1)
            stats.append(f"💹 {label.strip()}: {price.strip()}")
    if m.get("odds_via"):
        stats.append(f"💰 Best price found: {m['odds_via']['odds']} via {m['odds_via']['brand']}")
    if m.get("over25"):
        stats.append(f"⚽ Goals market lean: {m['over25']}")
    if m.get("btts"):
        stats.append(f"🥅 BTTS: {m['btts']}")
    if m.get("correct_score"):
        stats.append(f"🎯 Correct score lean: {m['correct_score']}")
    if m.get("competition"):
        stats.append(f"🏆 Competition: {m['competition']}")
    if m.get("ko_display"):
        time_label = "Kickoff" if m["sport"] in ("football", "basketball", "rugby") else "Start time"
        stats.append(f"🕒 {time_label}: {m['ko_display']}")
    return stats[:5] if len(stats) >= 3 else stats


def pick_cta_brand() -> dict:
    """Highest-rated brand with a real affiliate link — the only ones we push CTAs to."""
    return max(AFFILIATE_BRANDS, key=lambda b: b["stars"])


def build_preview(m: dict) -> str:
    home, away = m["home"], m.get("away") or ""
    comp = m.get("competition") or "this fixture"
    pick = m.get("pick_label") or "a tight contest"
    subject = f"{home} take on {away}" if away else home
    lines = [f"{subject} in {comp}."]
    if m.get("ko_display"):
        time_label = "Kick-off" if m["sport"] in ("football", "basketball", "rugby") else "Start time"
        lines.append(f"{time_label} is {m['ko_display']}.")
    lines.append(f"Our model leans towards {pick}." if pick != "a tight contest" else "")
    return " ".join(l for l in lines if l)


# ── PLATFORM FORMATTERS (generous spacing for mobile readability) ───────────

_REACT_PROMPT_TG = "💬 Tap a reaction below — 🔥 backing this pick · 🤔 not convinced · ❤️ love the analysis"
_REACT_PROMPT_FB = "💬 React below — 🔥 if you're backing this, 🤔 if you're not sure!"


def build_telegram_post(m: dict, cta: dict) -> str:
    meta = SPORT_META.get(m["sport"], SPORT_META["other"])
    stats_block = "\n\n".join(f"• {s}" for s in build_stats(m))
    matchup = f"{m['home']} vs {m['away']}" if m.get("away") else m["home"]
    title = f"{matchup} — {meta['label']} Preview & Best Bet"
    meta_line = m.get("competition", "")
    if m.get("ko_display"):
        meta_line += f" · {m['ko_display']}" if meta_line else m["ko_display"]

    return (
        f"🏆 <b>{title}</b>\n\n"
        f"{meta['emoji']} <b>{matchup}</b>\n"
        f"{meta_line}\n\n"
        f"{build_preview(m)}\n\n"
        f"📊 <b>Key Stats</b>\n\n"
        f"{stats_block}\n\n"
        f"🎯 <b>Best Betting Pick:</b> {m.get('pick_label') or 'See stats above'}\n\n"
        f"🏅 <b>Recommended Bookmaker:</b> {cta['name']} {_stars(cta['stars'])}\n"
        f"💰 {cta['welcome']}\n\n"
        f"🎁 Claim Bonus → <a href=\"{cta['url']}\">{cta['name']}</a>\n"
        f"✅ Place Bet → <a href=\"{cta['url']}\">{cta['name']}</a>\n\n"
        f"🌐 Visit <a href=\"{SITE_URL}\">SifuFinds.com</a> for more betting tips, "
        f"predictions, bookmaker reviews, and exclusive bonuses.\n\n"
        f"{_REACT_PROMPT_TG}\n\n"
        f"🔞 18+ | Gamble Responsibly"
    )


def build_facebook_post(m: dict, cta: dict) -> str:
    meta = SPORT_META.get(m["sport"], SPORT_META["other"])
    stats_block = "\n\n".join(f"✔️ {s}" for s in build_stats(m))
    matchup = f"{m['home']} vs {m['away']}" if m.get("away") else m["home"]

    return (
        f"🏆 {matchup} — {meta['label']} Preview & Best Bet\n\n"
        f"{build_preview(m)}\n\n"
        f"📊 Key Stats:\n\n{stats_block}\n\n"
        f"🎯 Best Betting Pick: {m.get('pick_label') or 'See stats above'}\n\n"
        f"🏅 Best Bookmaker: {cta['name']} ({_stars(cta['stars'])}) — {cta['welcome']}\n\n"
        f"🎁 Claim your bonus and place your bet: {cta['url']}\n\n"
        f"🌐 More tips, predictions, and bookmaker reviews at {SITE_URL}\n\n"
        f"{_REACT_PROMPT_FB}\n\n"
        f"🔞 18+ | Gamble Responsibly"
    )


def build_instagram_post(m: dict, cta: dict) -> str:
    meta = SPORT_META.get(m["sport"], SPORT_META["other"])
    stats_lines = "\n\n".join(f"🔹 {s}" for s in build_stats(m)[:4])
    matchup = f"{m['home']} vs {m['away']}" if m.get("away") else m["home"]
    hashtags = (
        f"#SifuFinds #BettingTips {meta['tag']} #AfricanBetting #SportsBetting "
        f"#{cta['name'].replace(' ', '')}"
    )
    return (
        f"🏆 {matchup}\n\n"
        f"{build_preview(m)}\n\n"
        f"{stats_lines}\n\n"
        f"🎯 Pick: {m.get('pick_label') or 'See stats above'}\n\n"
        f"🏅 Best odds via {cta['name']} — {cta['welcome']}\n\n"
        f"👉 Link in bio for the full breakdown + bonus\n"
        f"❤️🔥 Double-tap and drop a comment with your score prediction!\n\n"
        f"🔞 18+ | Gamble Responsibly\n"
        f".\n.\n.\n{hashtags}"
    )


def _tweet_len(text: str) -> int:
    url_pattern = re.compile(r"https?://\S+")
    count, last = 0, 0
    for mm in url_pattern.finditer(text):
        count += len(text[last:mm.start()]) + 23
        last = mm.end()
    count += len(text[last:])
    return count


def _trim_to_limit(text: str, limit: int = 280) -> str:
    lines = text.split("\n")
    while lines and _tweet_len("\n".join(lines)) > limit:
        words = lines[-1].split()
        if len(words) <= 1:
            lines.pop()
        else:
            lines[-1] = " ".join(words[:-1]) + "..."
    return "\n".join(lines)


def build_twitter_post(m: dict, cta: dict) -> str:
    meta = SPORT_META.get(m["sport"], SPORT_META["other"])
    matchup = f"{m['home']} vs {m['away']}" if m.get("away") else m["home"]
    tweet = (
        f"🏆 {matchup}\n\n"
        f"🎯 Pick: {m.get('pick_label') or 'Check the stats'}\n"
        f"💰 Best odds via {cta['name']}\n"
        f"🎁 {cta['welcome']}\n\n"
        f"👉 Claim bonus → {cta['url']}\n\n"
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

    telegram_text  = build_telegram_post(m, cta)
    facebook_text  = build_facebook_post(m, cta)
    instagram_text = build_instagram_post(m, cta)
    twitter_text   = build_twitter_post(m, cta)

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

    if args.telegram:
        if send_to_channel(telegram_text):
            log("match_post", "telegram", "success", m["home"])
            print("✓ Posted to Telegram.")
        else:
            log("match_post", "telegram", "failed", m["home"])
            print("✗ Telegram post failed — check TELEGRAM_BOT_TOKEN / session creds.")
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
    parser.add_argument("--dry-run", action="store_true", help="Preview only, send nothing")
    args = parser.parse_args()
    run(args)
