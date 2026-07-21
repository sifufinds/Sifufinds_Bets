"""
agent_match_post.py — Premium Match Post Generator for SifuFinds

Given a football match ("Team A vs Team B"), builds a premium social post for
Telegram, Facebook, Instagram, and X (Twitter), using ONLY verified data already
scraped into data/predictions.json / data/tips.json / data/live.json (never
invents stats, odds, bookmakers, or bonuses). Posts to Telegram immediately
using the same Telethon + bot-token pipeline as agent_telegram_offers.py.

Usage:
  python3 agent_match_post.py "Manchester United vs Arsenal"
  python3 agent_match_post.py "Spain vs Argentina" --no-telegram   # preview only
  python3 agent_match_post.py "Real Madrid vs Barcelona" --dry-run # print, don't send
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


# ── MATCH LOOKUP ──────────────────────────────────────────────────────────────

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


def find_match(query: str) -> dict | None:
    """Search predictions.json and tips.json for a real match record.
    Returns a normalised dict or None if nothing verified is found — never fabricates.
    When the same match is found in both files, merges in whichever fields the
    higher-scoring record is missing (odds/confidence/via-bookmaker) rather than
    discarding the richer of the two."""
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


# ── STATS + PICK BUILDING ─────────────────────────────────────────────────────

def build_stats(m: dict) -> list[str]:
    stats: list[str] = []
    if m.get("confidence") is not None:
        stats.append(f"📈 Model confidence: {m['confidence']}%")
    if m.get("home_odds") or m.get("draw_odds") or m.get("away_odds"):
        stats.append(
            f"💹 1X2 odds — Home {m.get('home_odds') or 'N/A'} · "
            f"Draw {m.get('draw_odds') or 'N/A'} · Away {m.get('away_odds') or 'N/A'}"
        )
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
        stats.append(f"🕒 Kickoff: {m['ko_display']}")
    return stats[:5] if len(stats) >= 3 else stats


def pick_cta_brand() -> dict:
    """Highest-rated brand with a real affiliate link — the only ones we push CTAs to."""
    return max(AFFILIATE_BRANDS, key=lambda b: b["stars"])


def build_preview(m: dict) -> str:
    home, away, comp = m["home"], m["away"], m.get("competition") or "this fixture"
    pick = m.get("pick_label") or "a tight contest"
    lines = [f"{home} take on {away} in {comp}."]
    if m.get("ko_display"):
        lines.append(f"Kick-off is {m['ko_display']}.")
    lines.append(f"Our model leans towards {pick}.")
    return " ".join(lines)


# ── PLATFORM FORMATTERS ────────────────────────────────────────────────────────

def build_telegram_post(m: dict, cta: dict) -> str:
    stats_block = "\n".join(f"• {s}" for s in build_stats(m))
    title = f"{m['home']} vs {m['away']} — Match Preview & Best Bet"
    return (
        f"🏆 <b>{title}</b>\n"
        f"⚽ <b>{m['home']} vs {m['away']}</b>\n"
        f"{m.get('competition','')}"
        + (f" · {m['ko_display']}" if m.get("ko_display") else "") + "\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{build_preview(m)}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Key Stats</b>\n{stats_block}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Best Betting Pick:</b> {m.get('pick_label','See stats above')}\n"
        f"🏅 <b>Recommended Bookmaker:</b> {cta['name']} {_stars(cta['stars'])}\n"
        f"💰 {cta['welcome']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 Claim Bonus → <a href=\"{cta['url']}\">{cta['name']}</a>\n"
        f"✅ Place Bet → <a href=\"{cta['url']}\">{cta['name']}</a>\n\n"
        f"🌐 Visit <a href=\"{SITE_URL}\">SifuFinds.com</a> for more betting tips, "
        f"predictions, bookmaker reviews, and exclusive bonuses.\n\n"
        f"🔞 18+ | Gamble Responsibly"
    )


def build_facebook_post(m: dict, cta: dict) -> str:
    stats_block = "\n".join(f"✔️ {s}" for s in build_stats(m))
    return (
        f"🏆 {m['home']} vs {m['away']} — Match Preview & Best Bet\n\n"
        f"{build_preview(m)}\n\n"
        f"📊 Key Stats:\n{stats_block}\n\n"
        f"🎯 Best Betting Pick: {m.get('pick_label','See stats above')}\n"
        f"🏅 Best Bookmaker: {cta['name']} ({_stars(cta['stars'])}) — {cta['welcome']}\n\n"
        f"🎁 Claim your bonus and place your bet: {cta['url']}\n\n"
        f"🌐 More tips, predictions, and bookmaker reviews at {SITE_URL}\n"
        f"🔞 18+ | Gamble Responsibly"
    )


def build_instagram_post(m: dict, cta: dict) -> str:
    stats_lines = "\n".join(f"🔹 {s}" for s in build_stats(m)[:4])
    hashtags = (
        "#SifuFinds #BettingTips #FootballTips #AfricanBetting #SportsBetting "
        f"#{cta['name'].replace(' ', '')}"
    )
    return (
        f"🏆 {m['home']} vs {m['away']}\n\n"
        f"{build_preview(m)}\n\n"
        f"{stats_lines}\n\n"
        f"🎯 Pick: {m.get('pick_label','See stats above')}\n"
        f"🏅 Best odds via {cta['name']} — {cta['welcome']}\n\n"
        f"👉 Link in bio for the full breakdown + bonus\n"
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
    tweet = (
        f"🏆 {m['home']} vs {m['away']}\n\n"
        f"🎯 Pick: {m.get('pick_label','Check the stats')}\n"
        f"💰 Best odds via {cta['name']}\n"
        f"🎁 {cta['welcome']}\n\n"
        f"👉 Claim bonus → {cta['url']}\n\n"
        f"#SifuFinds #BettingTips 🔞 18+"
    )
    return _trim_to_limit(tweet)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def run(query: str, send_telegram: bool = True, dry_run: bool = False) -> None:
    log("match_post", "start", "running", query)

    m = find_match(query)
    if not m:
        print(
            f"✗ No verified match data found for '{query}' in predictions.json / tips.json.\n"
            f"  Refusing to invent stats, odds, or a bookmaker recommendation.\n"
            f"  Wait for the next data refresh, or provide the league/kickoff so it can be "
            f"looked up manually."
        )
        log("match_post", "lookup", "failed", query)
        sys.exit(1)

    cta = pick_cta_brand()

    telegram_text  = build_telegram_post(m, cta)
    facebook_text  = build_facebook_post(m, cta)
    instagram_text = build_instagram_post(m, cta)
    twitter_text   = build_twitter_post(m, cta)

    print("\n" + "═" * 60)
    print("TELEGRAM (auto-posting)" if send_telegram and not dry_run else "TELEGRAM (preview)")
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

    if dry_run:
        print("Dry run — nothing sent.")
        return

    if send_telegram:
        if send_to_channel(telegram_text):
            log("match_post", "telegram", "success", f"{m['home']} vs {m['away']}")
            print("✓ Posted to Telegram.")
        else:
            log("match_post", "telegram", "failed", f"{m['home']} vs {m['away']}")
            print("✗ Telegram post failed — check TELEGRAM_BOT_TOKEN / session creds.")
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Premium Match Post Generator")
    parser.add_argument("match", type=str, help='Match query, e.g. "Manchester United vs Arsenal"')
    parser.add_argument("--no-telegram", action="store_true", help="Don't auto-post to Telegram")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, send nothing")
    args = parser.parse_args()
    run(args.match, send_telegram=not args.no_telegram, dry_run=args.dry_run)
