"""
agent_accumulator_post.py — Weekend/Weekday 5-Fold Accumulator Post for SifuFinds

Builds a "WEEKEND ACCUMULATOR" or "WEEKDAY ACCUMULATOR" 5-fold post from real
picks already scraped into data/tips.json / data/predictions.json (never
invents a match, pick, or price) and posts it to Telegram immediately. This is
a separate, standalone post from agent_match_post.py's single-match cards —
run it a few times a day once football season is underway, independently of
per-match requests.

Selection: takes the 5 highest-confidence real picks that carry a real,
attributed price, deduplicated by match, restricted to the Premier League,
the rest of the world's top ~10 leagues, African leagues, and major
international/continental competitions (see ALLOWED_LEAGUE_KEYWORDS) — never
a random lower-tier league just because it had a high-confidence tip.
Refuses to post (no invented 6th leg, no falling back to a smaller league)
if fewer than 5 qualifying picks exist — e.g. deep off-season.

Usage:
  python3 agent_accumulator_post.py                  # auto weekend/weekday by UTC day
  python3 agent_accumulator_post.py --type weekend
  python3 agent_accumulator_post.py --type weekday --dry-run
  python3 agent_accumulator_post.py --stake 2000     # ₦ stake used for the example return
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import log
from utils.blog_match import find_matching_post, mark_used
from utils.social_image import build_social_image, brand_color
from utils.affiliate_links import cta_plain
from agent_telegram_offers import send_to_channel, SITE_URL
from agent_match_post import build_bookmaker_block, pick_cta_brand, _trim_to_limit
from agent3_social import post_facebook, post_instagram
from agent_twitter_posts import _post_tweet as post_twitter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PRED_JSON = REPO_ROOT / "data" / "predictions.json"
TIPS_JSON = REPO_ROOT / "data" / "tips.json"

FOLD_COUNT = 5
LEG_EMOJI = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]

_REACT_PROMPT = "💬 React below — 🔥 backing this acca · 🤔 risky one · ❤️ love the analysis"

# Only pick legs from the Premier League, the rest of the world's top ~10
# leagues, African leagues, and major continental/international competitions —
# never a random lower-tier league just because it happened to have a
# high-confidence tip that day.
ALLOWED_LEAGUE_KEYWORDS = [
    # Top European/world leagues — "serie a" is deliberately NOT a bare keyword:
    # several countries (Ecuador, etc.) also name their top flight "Serie A",
    # so only Italy's and Brazil's are allowed explicitly (see is_major_league()).
    "premier league", "la liga", "bundesliga", "ligue 1",
    "eredivisie", "primeira liga", "pro league", "liga mx", "mls",
    "super lig", "süper lig",
    # African leagues
    "npfl", "nigeria premier", "kenyan premier", "kenya premier",
    "ghana premier", "egyptian premier", "egypt premier",
    "caf champions league", "caf confederation",
    "afcon", "africa cup of nations",
    # Major international/continental competitions
    "champions league", "europa league", "conference league",
    "world cup", "copa america", "copa libertadores", "copa sudamericana",
]

# Reject anything that's clearly a reserve/lower-division fixture even if it
# happens to contain an otherwise-allowed keyword (e.g. "Germany Bundesliga Div 5").
_EXCLUDE_KEYWORDS = ["div 2", "div 3", "div 4", "div 5", "div 6", "reserve", "u21", "u23", "u19", "youth"]


def is_major_league(competition: str) -> bool:
    comp = (competition or "").lower()
    if any(x in comp for x in _EXCLUDE_KEYWORDS):
        return False
    if "italy serie a" in comp or "brazil serie a" in comp:
        return True
    return any(k in comp for k in ALLOWED_LEAGUE_KEYWORDS)


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _wdw_odds(pred: dict) -> float | None:
    """Map a predictions.json record's declared winner side to its own real odds."""
    side_field = {"1": "home_odds", "2": "away_odds", "X": "draw_odds"}.get(pred.get("wdw", ""))
    raw = pred.get(side_field) if side_field else None
    try:
        return float(raw) if raw else None
    except ValueError:
        return None


def gather_candidates() -> list[dict]:
    """Real picks only: match, pick label, real price, real bookmaker, confidence."""
    candidates: list[dict] = []
    seen: set[str] = set()

    for tip in _load_json(TIPS_JSON).get("tips", []):
        match = tip.get("match", "")
        key = match.lower()
        if not match or key in seen:
            continue
        try:
            odds = float(tip.get("odds", 0))
        except ValueError:
            continue
        conf = tip.get("conf")
        if odds <= 1.01 or not conf:
            continue
        if not is_major_league(tip.get("league", "")):
            continue
        seen.add(key)
        candidates.append({
            "match": match,
            "pick": tip.get("pred", ""),
            "odds": odds,
            "via": tip.get("via", ""),
            "confidence": conf,
            "competition": tip.get("league", ""),
        })

    for pred in _load_json(PRED_JSON).get("predictions", []):
        match = f"{pred.get('home','')} vs {pred.get('away','')}"
        key = match.lower()
        conf = pred.get("confidence")
        odds = _wdw_odds(pred)
        if key in seen or not conf or not odds or odds <= 1.01:
            continue
        if not is_major_league(pred.get("competition", "")):
            continue
        seen.add(key)
        candidates.append({
            "match": match,
            "pick": pred.get("match_winner_label", ""),
            "odds": odds,
            "via": "",
            "confidence": conf,
            "competition": pred.get("competition", ""),
        })

    candidates.sort(key=lambda c: c["confidence"], reverse=True)
    return candidates


def pick_legs(candidates: list[dict], n: int = FOLD_COUNT) -> list[dict]:
    return candidates[:n]


def _compute_totals(legs: list[dict], stake: int) -> tuple[float, int, int]:
    total_odds = 1.0
    for leg in legs:
        total_odds *= leg["odds"]
    total_odds = round(total_odds, 2)
    returns = round(stake * total_odds)
    avg_conf = round(sum(leg["confidence"] for leg in legs) / len(legs))
    return total_odds, returns, avg_conf


def _title(acc_type: str) -> str:
    return "WEEKEND ACCUMULATOR" if acc_type == "weekend" else "WEEKDAY ACCUMULATOR"


def build_telegram_post(legs: list[dict], acc_type: str, stake: int, cta: dict) -> str:
    total_odds, returns, avg_conf = _compute_totals(legs, stake)
    leg_lines = "\n".join(
        f"{LEG_EMOJI[i]} {leg['match']} - {leg['pick']}" for i, leg in enumerate(legs)
    )

    return (
        f"🎉 <b>{_title(acc_type)}</b> — Turn ₦{stake:,} into ₦{returns:,} 🎉\n\n"
        f"<b>{len(legs)}-Fold @ {total_odds}</b>\n\n"
        f"{leg_lines}\n\n"
        f"<b>Stake:</b> ₦{stake:,} → <b>Returns:</b> ₦{returns:,}\n\n"
        f"🧠 <b>Why this combo:</b> our {len(legs)} highest-confidence picks today, "
        f"{avg_conf}% average model confidence\n"
        f"⚠️ Higher risk than a single bet — every leg must win for the accumulator to pay out\n\n"
        f"{build_bookmaker_block(cta, html=True)}\n\n"
        f"🌐 Visit <a href=\"{SITE_URL}\">SifuFinds.com</a> for more accas, tips, and bookmaker bonuses.\n\n"
        f"{_REACT_PROMPT}\n\n"
        f"🔞 18+ | Gamble Responsibly | BeGambleAware.org"
    )


def build_facebook_post(legs: list[dict], acc_type: str, stake: int, cta: dict, link: str = SITE_URL) -> str:
    total_odds, returns, avg_conf = _compute_totals(legs, stake)
    leg_lines = "\n".join(
        f"{LEG_EMOJI[i]} {leg['match']} - {leg['pick']}" for i, leg in enumerate(legs)
    )
    return (
        f"🎉 {_title(acc_type)} — Turn ₦{stake:,} into ₦{returns:,} 🎉\n\n"
        f"{len(legs)}-Fold @ {total_odds}\n\n"
        f"{leg_lines}\n\n"
        f"Stake: ₦{stake:,} → Returns: ₦{returns:,}\n\n"
        f"🧠 Why this combo: our {len(legs)} highest-confidence picks today, {avg_conf}% average model confidence\n"
        f"⚠️ Higher risk than a single bet — every leg must win for the accumulator to pay out\n\n"
        f"{build_bookmaker_block(cta, html=False)}\n\n"
        f"🌐 Full breakdown → {link}\n\n"
        f"{_REACT_PROMPT}\n\n"
        f"🔞 18+ | Gamble Responsibly | BeGambleAware.org"
    )


def build_instagram_post(legs: list[dict], acc_type: str, stake: int, cta: dict) -> str:
    total_odds, returns, avg_conf = _compute_totals(legs, stake)
    leg_lines = "\n".join(
        f"{LEG_EMOJI[i]} {leg['match']} - {leg['pick']}" for i, leg in enumerate(legs)
    )
    hashtags = "#SifuFinds #Accumulator #BettingTips #AfricanBetting #SportsBetting #" + cta["name"].replace(" ", "")
    return (
        f"🎉 {_title(acc_type)} — Turn ₦{stake:,} into ₦{returns:,} 🎉\n\n"
        f"{len(legs)}-Fold @ {total_odds}\n\n"
        f"{leg_lines}\n\n"
        f"🧠 {avg_conf}% average model confidence · ⚠️ every leg must win\n\n"
        f"👉 Link in bio for the full breakdown + bonus\n"
        f"❤️🔥 Double-tap if you're backing this acca!\n\n"
        f"🔞 18+ | Gamble Responsibly\n"
        f".\n.\n.\n{hashtags}"
    )


def build_twitter_post(legs: list[dict], acc_type: str, stake: int, cta: dict) -> str:
    total_odds, returns, _ = _compute_totals(legs, stake)
    tweet = (
        f"🎉 {_title(acc_type)} — Turn ₦{stake:,} into ₦{returns:,}\n\n"
        f"{len(legs)}-Fold @ {total_odds} on {cta['name']}\n"
        f"👉 {cta_plain(cta)}\n\n"
        f"#SifuFinds #Accumulator 🔞 18+"
    )
    return _trim_to_limit(tweet)


def run(args: argparse.Namespace) -> None:
    log("accumulator", "start", "running", args.type)

    acc_type = args.type
    if acc_type == "auto":
        acc_type = "weekend" if datetime.now(timezone.utc).weekday() >= 5 else "weekday"

    candidates = gather_candidates()
    legs = pick_legs(candidates, FOLD_COUNT)

    if len(legs) < FOLD_COUNT:
        print(
            f"✗ Only {len(legs)}/{FOLD_COUNT} qualifying real picks found (need confidence + a real "
            f"attributed price on each). Refusing to invent a leg to fill the accumulator — "
            f"wait for the next data refresh."
        )
        log("accumulator", "lookup", "failed", f"{len(legs)}/{FOLD_COUNT}")
        sys.exit(1)

    cta = pick_cta_brand()

    # Prefer a real tips/predictions blog post as the "read more" link over
    # the generic homepage — falls back cleanly when nothing fresh matches.
    tips_post = find_matching_post("tips")
    facebook_link = tips_post["url"] if tips_post else SITE_URL

    telegram_text  = build_telegram_post(legs, acc_type, args.stake, cta)
    facebook_text  = build_facebook_post(legs, acc_type, args.stake, cta, link=facebook_link)
    instagram_text = build_instagram_post(legs, acc_type, args.stake, cta)
    twitter_text   = build_twitter_post(legs, acc_type, args.stake, cta)

    print("\n" + "═" * 60)
    print(f"{acc_type.upper()} ACCUMULATOR — TELEGRAM " + ("(auto-posting)" if args.telegram and not args.dry_run else "(preview)"))
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
        total_odds, returns, avg_conf = _compute_totals(legs, args.stake)
        image_path = build_social_image(
            headline=f"{_title(acc_type)} — {len(legs)}-Fold @ {total_odds}",
            tag="Today's Betting Tips",
            color_hex=brand_color(cta["name"]),
            subtext=f"{avg_conf}% average model confidence",
            out_name="tips_card.png",
        )
        results["facebook"] = post_facebook(facebook_text, image_path=image_path)
        if results["facebook"] and tips_post:
            mark_used("tips", tips_post["slug"])
        print("✓ Posted to Facebook." if results["facebook"] else "✗ Facebook post failed or not configured (see agents/python/FB_SETUP_SIMPLE.md).")

    if args.instagram:
        results["instagram"] = post_instagram(instagram_text)
        print("✓ Posted to Instagram." if results["instagram"] else "✗ Instagram post failed or not configured (see agents/python/SETUP.md Step 3).")

    if args.twitter:
        results["twitter"] = post_twitter(twitter_text)
        print("✓ Posted to X/Twitter." if results["twitter"] else "✗ X/Twitter post failed or not configured (needs TWITTER_SESSION or X_USERNAME+X_PASSWORD in .env).")

    for platform, ok in results.items():
        log("accumulator", platform, "success" if ok else "failed", acc_type)

    if results and not any(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Weekend/Weekday 5-Fold Accumulator Post")
    parser.add_argument("--type", choices=["auto", "weekend", "weekday"], default="auto",
                         help="Accumulator label (default: auto-detect from current UTC day)")
    parser.add_argument("--stake", type=int, default=1000, help="Example stake in ₦ used for the return calc (default: 1000)")
    parser.add_argument("--no-telegram", dest="telegram", action="store_false", help="Don't auto-post to Telegram")
    parser.add_argument("--no-facebook", dest="facebook", action="store_false", help="Don't auto-post to Facebook")
    parser.add_argument("--no-instagram", dest="instagram", action="store_false", help="Don't auto-post to Instagram")
    parser.add_argument("--no-twitter", dest="twitter", action="store_false", help="Don't auto-post to X/Twitter")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, send nothing")
    args = parser.parse_args()
    run(args)
