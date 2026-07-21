"""
agent_accumulator_post.py — Weekend/Weekday 5-Fold Accumulator Post for SifuFinds

Builds a "WEEKEND ACCUMULATOR" or "WEEKDAY ACCUMULATOR" 5-fold post from real
picks already scraped into data/tips.json / data/predictions.json (never
invents a match, pick, or price) and posts it to Telegram immediately. This is
a separate, standalone post from agent_match_post.py's single-match cards —
run it a few times a day once football season is underway, independently of
per-match requests.

Selection: takes the 5 highest-confidence real picks that carry a real,
attributed price, deduplicated by match. Refuses to post (no invented 6th
leg) if fewer than 5 qualifying picks exist — e.g. deep off-season.

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
from agent_telegram_offers import AFFILIATE_BRANDS, _stars, send_to_channel, SITE_URL

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PRED_JSON = REPO_ROOT / "data" / "predictions.json"
TIPS_JSON = REPO_ROOT / "data" / "tips.json"

FOLD_COUNT = 5
LEG_EMOJI = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]

_REACT_PROMPT = "💬 React below — 🔥 backing this acca · 🤔 risky one · ❤️ love the analysis"


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


def pick_cta_brand() -> dict:
    return max(AFFILIATE_BRANDS, key=lambda b: b["stars"])


def build_telegram_post(legs: list[dict], acc_type: str, stake: int, cta: dict) -> str:
    total_odds = 1.0
    for leg in legs:
        total_odds *= leg["odds"]
    total_odds = round(total_odds, 2)
    returns = round(stake * total_odds)

    leg_lines = "\n".join(
        f"{LEG_EMOJI[i]} {leg['match']} - {leg['pick']}" for i, leg in enumerate(legs)
    )

    title = "WEEKEND ACCUMULATOR" if acc_type == "weekend" else "WEEKDAY ACCUMULATOR"

    return (
        f"🎉 <b>{title}</b> 🎉\n\n"
        f"<b>{len(legs)}-Fold @ {total_odds}</b>\n\n"
        f"{leg_lines}\n\n"
        f"<b>Stake:</b> ₦{stake:,} → <b>Returns:</b> ₦{returns:,}\n\n"
        f"🏅 <b>Bookmaker:</b> {cta['name']} {_stars(cta['stars'])}\n"
        f"⚡ Place this accumulator at <a href=\"{cta['url']}\">{cta['name']}</a> and get best odds guaranteed!\n\n"
        f"🌐 Visit <a href=\"{SITE_URL}\">SifuFinds.com</a> for more accas, tips, and bookmaker bonuses.\n\n"
        f"{_REACT_PROMPT}\n\n"
        f"🔞 18+ | Gamble Responsibly | BeGambleAware.org"
    )


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
    telegram_text = build_telegram_post(legs, acc_type, args.stake, cta)

    print("\n" + "═" * 60)
    print(f"{acc_type.upper()} ACCUMULATOR — TELEGRAM " + ("(auto-posting)" if args.telegram and not args.dry_run else "(preview)"))
    print("═" * 60)
    print(telegram_text)
    print("═" * 60 + "\n")

    if args.dry_run:
        print("Dry run — nothing sent.")
        return

    if args.telegram:
        if send_to_channel(telegram_text):
            log("accumulator", "telegram", "success", acc_type)
            print("✓ Posted to Telegram.")
        else:
            log("accumulator", "telegram", "failed", acc_type)
            print("✗ Telegram post failed — check TELEGRAM_BOT_TOKEN / session creds.")
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Weekend/Weekday 5-Fold Accumulator Post")
    parser.add_argument("--type", choices=["auto", "weekend", "weekday"], default="auto",
                         help="Accumulator label (default: auto-detect from current UTC day)")
    parser.add_argument("--stake", type=int, default=1000, help="Example stake in ₦ used for the return calc (default: 1000)")
    parser.add_argument("--no-telegram", dest="telegram", action="store_false", help="Don't auto-post to Telegram")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, send nothing")
    args = parser.parse_args()
    run(args)
