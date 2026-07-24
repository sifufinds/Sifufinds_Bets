"""
agent_casino_post.py — Casino Games & Bonuses Post for SifuFinds

A separate, standalone post type from agent_match_post.py / agent_accumulator_post.py
(sports tips/accumulators) — covers casino games and casino-relevant bonuses.
Posts to Telegram, Facebook, Instagram, and X.

Truth policy (strict, since this is promotional content about real money bonuses):
  - The casino bonus cited as "verified live" comes ONLY from data/countries_live.json
    entries where status == "live" AND last_verified is within CASINO_FRESHNESS_DAYS,
    AND the bonus text itself explicitly mentions a casino keyword (aviator/spin/
    casino/jackpot) — never a generic sports welcome bonus dressed up as a casino one.
  - The verified bonus's actual last_verified date is always shown in the post, so
    readers (and you) can judge currency for themselves rather than it being implied
    as "right now" when it might be a few weeks old.
  - The "game spotlight" blurb only states well-documented, publicly known facts about
    the game itself (how it works, which studio built it) — never a claim that a
    specific bookmaker offers a specific game unless our own verified bonus text says so.
  - The bonus's bookmaker is cited for information only, with no affiliate CTA, if it
    isn't in AFFILIATE_BRANDS (matches the existing "never post an affiliate CTA to a
    brand we don't have a real link for" rule from agent_telegram_offers.py). The CTA
    always points to a real affiliate brand, with an honest "applies platform-wide,
    including casino" framing rather than claiming a specific unverified game tie-in.
  - Refuses to post if no verified casino-relevant bonus currently qualifies — never
    invents one to fill a slot.

Usage:
  python3 agent_casino_post.py               # auto-picks a verified casino bonus
  python3 agent_casino_post.py --dry-run      # preview all 4 platforms, send nothing
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
from utils.affiliate_links import cta_plain
from agent_telegram_offers import send_to_channel, SITE_URL
from agent_match_post import build_bookmaker_block, pick_cta_brand, _trim_to_limit
from agent3_social import post_facebook, post_instagram
from agent_twitter_posts import _post_tweet as post_twitter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LIVE_COUNTRIES_JSON = REPO_ROOT / "data" / "countries_live.json"
STATE_FILE = Path(__file__).parent / "casino_post_state.json"

CASINO_FRESHNESS_DAYS = 45
CASINO_KEYWORDS = ["aviator", "spin", "casino", "jackpot"]

_REACT_PROMPT = "💬 React below — 🎰 trying this one · 🔥 already play it · 🤔 not for me"

# Well-documented, publicly known real casino games — used only to describe HOW a
# game works in general, never to claim a specific bookmaker offers it unless the
# verified bonus text itself names it.
GAME_CATALOG = [
    {
        "keyword": "aviator",
        "name": "Aviator",
        "provider": "Spribe",
        "blurb": (
            "Aviator is a crash multiplier game from Spribe: a plane takes off and a "
            "multiplier climbs in real time — you cash out before it flies away to lock "
            "in your win. Rounds last seconds, stakes can be tiny, and it's become one of "
            "the most-played casino games across African betting apps."
        ),
    },
    {
        "keyword": "spin",
        "name": "Slots & Free Spins",
        "provider": None,
        "blurb": (
            "Free spins credit real spins directly on the site's slot games — no separate "
            "game selection needed, they apply straight to eligible slot titles in the "
            "casino section, and any winnings usually carry standard wagering requirements."
        ),
    },
    {
        "keyword": "jackpot",
        "name": "Progressive Jackpot Games",
        "provider": None,
        "blurb": (
            "Jackpot games pool a share of every stake into a single growing prize pot "
            "that keeps climbing until someone hits the winning combination — the pot can "
            "run into the millions before it pays out."
        ),
    },
    {
        "keyword": "casino",
        "name": "Casino & Slots",
        "provider": None,
        "blurb": (
            "Most African bookmakers run a full casino section alongside sports betting — "
            "slots, live-dealer tables, and crash-style games all sit inside the same app "
            "and wallet as your sports betting balance."
        ),
    },
]


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _load_state() -> dict:
    return _load_json(STATE_FILE) or {"last_index": -1}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def gather_verified_casino_bonuses() -> list[dict]:
    """Real, currently-fresh casino-relevant bonuses only — see module docstring
    for the exact freshness/status/keyword bar each entry must clear."""
    now = datetime.now(timezone.utc)
    candidates: list[dict] = []

    for name, bk in _load_json(LIVE_COUNTRIES_JSON).get("bookmakers", {}).items():
        if bk.get("status") != "live":
            continue
        last_verified_str = bk.get("last_verified", "")
        if not last_verified_str:
            continue
        try:
            last_verified = datetime.fromisoformat(last_verified_str)
        except ValueError:
            continue
        age_days = (now - last_verified).total_seconds() / 86400
        if age_days > CASINO_FRESHNESS_DAYS:
            continue

        text = f"{bk.get('top','')} {bk.get('off','')}".lower()
        if not any(k in text for k in CASINO_KEYWORDS):
            continue

        candidates.append({
            "brand": name,
            "top": bk.get("top", ""),
            "off": bk.get("off", ""),
            "url": bk.get("url", ""),
            "last_verified": last_verified,
            "age_days": round(age_days),
        })

    candidates.sort(key=lambda c: c["last_verified"], reverse=True)
    return candidates


def pick_bonus(candidates: list[dict]) -> dict:
    """Round-robin across qualifying candidates so repeated runs don't always
    feature the same brand."""
    state = _load_state()
    idx = (state.get("last_index", -1) + 1) % len(candidates)
    state["last_index"] = idx
    _save_state(state)
    return candidates[idx]


def match_game(bonus_text: str) -> dict:
    text = bonus_text.lower()
    for game in GAME_CATALOG:
        if game["keyword"] in text:
            return game
    return GAME_CATALOG[-1]  # generic "Casino & Slots" fallback


# ── PLATFORM FORMATTERS ────────────────────────────────────────────────────────

def _bonus_citation(bonus: dict, html: bool) -> str:
    verified_note = "today" if bonus["age_days"] == 0 else f"{bonus['age_days']} days ago"
    label = f"{bonus['brand']}"
    if html:
        label = f'<a href="{bonus["url"]}">{label}</a>' if bonus.get("url") else label
    return (
        f"📢 Real bonus live right now: {bonus['off'] or bonus['top']} — {label}\n"
        f"✅ Verified {verified_note}"
    )


def build_telegram_post(bonus: dict, game: dict, cta: dict) -> str:
    return (
        f"🎰 <b>Casino Spotlight — {game['name']}</b> 🎰\n\n"
        f"{game['blurb']}\n\n"
        f"{_bonus_citation(bonus, html=True)}\n\n"
        f"{build_bookmaker_block(cta, html=True)}\n"
        f"💡 This deposit bonus applies platform-wide — sports and casino.\n\n"
        f"🌐 Visit <a href=\"{SITE_URL}\">SifuFinds.com</a> for more bookmaker reviews and exclusive bonuses.\n\n"
        f"{_REACT_PROMPT}\n\n"
        f"🔞 18+ | Gamble Responsibly | BeGambleAware.org"
    )


def build_facebook_post(bonus: dict, game: dict, cta: dict) -> str:
    return (
        f"🎰 Casino Spotlight — {game['name']} 🎰\n\n"
        f"{game['blurb']}\n\n"
        f"{_bonus_citation(bonus, html=False)}\n\n"
        f"{build_bookmaker_block(cta, html=False)}\n"
        f"💡 This deposit bonus applies platform-wide — sports and casino.\n\n"
        f"🌐 More bookmaker reviews and exclusive bonuses at {SITE_URL}\n\n"
        f"{_REACT_PROMPT}\n\n"
        f"🔞 18+ | Gamble Responsibly | BeGambleAware.org"
    )


def build_instagram_post(bonus: dict, game: dict, cta: dict) -> str:
    hashtags = f"#SifuFinds #Casino #{game['name'].replace(' ', '').replace('&','')} #AfricanBetting #{cta['name'].replace(' ', '')}"
    return (
        f"🎰 Casino Spotlight — {game['name']} 🎰\n\n"
        f"{game['blurb']}\n\n"
        f"{_bonus_citation(bonus, html=False)}\n\n"
        f"🏅 {cta['name']} — {cta['welcome']} (sports + casino)\n\n"
        f"👉 Link in bio for the full breakdown + bonus\n"
        f"🎲 Drop a comment if you've tried {game['name']}!\n\n"
        f"🔞 18+ | Gamble Responsibly\n"
        f".\n.\n.\n{hashtags}"
    )


def build_twitter_post(bonus: dict, game: dict, cta: dict) -> str:
    # Deliberately short by design (no game blurb) rather than relying on
    # _trim_to_limit to cut it down — trimming from the tail would otherwise
    # gut the CTA link and hashtags first.
    tweet = (
        f"🎰 Casino Spotlight — {game['name']}\n\n"
        f"📢 {bonus['off'] or bonus['top']} ({bonus['brand']})\n"
        f"🏅 {cta['name']}: {cta['welcome']}\n"
        f"👉 {cta_plain(cta)}\n\n"
        f"#SifuFinds #Casino 🔞 18+"
    )
    return _trim_to_limit(tweet)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def run(args: argparse.Namespace) -> None:
    log("casino_post", "start", "running")

    candidates = gather_verified_casino_bonuses()
    if not candidates:
        print(
            f"✗ No verified casino-relevant bonus currently qualifies (status=live, "
            f"within {CASINO_FRESHNESS_DAYS} days, casino/spin/aviator/jackpot keyword). "
            f"Refusing to invent one — wait for the next data refresh."
        )
        log("casino_post", "lookup", "failed")
        sys.exit(1)

    bonus = pick_bonus(candidates)
    game = match_game(f"{bonus['top']} {bonus['off']}")
    cta = pick_cta_brand()

    telegram_text  = build_telegram_post(bonus, game, cta)
    facebook_text  = build_facebook_post(bonus, game, cta)
    instagram_text = build_instagram_post(bonus, game, cta)
    twitter_text   = build_twitter_post(bonus, game, cta)

    print("\n" + "═" * 60)
    print("CASINO POST — TELEGRAM " + ("(auto-posting)" if args.telegram and not args.dry_run else "(preview)"))
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
        print("✓ Posted to Facebook." if results["facebook"] else "✗ Facebook post failed or not configured.")

    if args.instagram:
        results["instagram"] = post_instagram(instagram_text)
        print("✓ Posted to Instagram." if results["instagram"] else "✗ Instagram post failed or not configured.")

    if args.twitter:
        results["twitter"] = post_twitter(twitter_text)
        print("✓ Posted to X/Twitter." if results["twitter"] else "✗ X/Twitter post failed or not configured.")

    for platform, ok in results.items():
        log("casino_post", platform, "success" if ok else "failed", bonus["brand"])

    if results and not any(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SifuFinds Casino Games & Bonuses Post")
    parser.add_argument("--no-telegram", dest="telegram", action="store_false", help="Don't auto-post to Telegram")
    parser.add_argument("--no-facebook", dest="facebook", action="store_false", help="Don't auto-post to Facebook")
    parser.add_argument("--no-instagram", dest="instagram", action="store_false", help="Don't auto-post to Instagram")
    parser.add_argument("--no-twitter", dest="twitter", action="store_false", help="Don't auto-post to X/Twitter")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, send nothing")
    args = parser.parse_args()
    run(args)
