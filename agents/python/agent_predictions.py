"""
agent_predictions.py — SifuFinds Football Prediction Agent (social content only,
no website page). Generates SifuFinds' own scored/probability prediction for
real, already-verified fixtures (never invents a fixture, injury, line-up, or
odds figure), tracks every prediction in data/sifu_predictions.json, grades
completed ones against real final scores, and builds platform-specific social
copy — Telegram, Facebook, Instagram and X are auto-posted using the same
integrations agent_match_post.py already uses; Threads, TikTok, LinkedIn and
YouTube have no posting API in this repo so their copy is printed for manual
posting.

Fixture source: data/predictions.json (predictz.com + forebet.com, refreshed by
update_predictions.py — real competitions/teams/kick-offs/odds, never invented
here). If a requested competition/round has no matching fixtures in the current
scrape window, this agent says so and predicts nothing rather than fabricate one.

Analysis: for each fixture, a short free web research pass (utils/serp_research
.research(), free-only, no Firecrawl) gathers real, sourced team-news snippets;
those notes plus the fixture's own real odds/kick-off are given to the free-tier
LLM chain (llm.ask(), Groq -> g4f -> Ollama, per this repo's no-paid-API rule) to
produce a probability split, predicted score, BTTS/O2.5 call, confidence and a
short write-up. If research turns up nothing or the LLM is unreachable, a
transparent odds-only fallback is used instead of guessing team-specific facts.

Usage:
  python3 agent_predictions.py "Premier League" --round "Gameweek 1"
  python3 agent_predictions.py "FA Cup" --round "Third Round" --days 10
  python3 agent_predictions.py --today                       # all major competitions, today
  python3 agent_predictions.py "Premier League" --dry-run     # preview only, nothing posted/saved
  python3 agent_predictions.py --grade                        # grade completed predictions
  python3 agent_predictions.py --stats                         # season accuracy report
  python3 agent_predictions.py --stats --competition "Premier League" --season "2025-26"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

from llm import ask
from utils.logger import log
from utils.serp_research import research
from utils.tweet_text import trim_to_limit as _trim_to_limit
from utils.prediction_store import (
    add_prediction, already_predicted, make_id,
    grade_pending, aggregate_stats,
)
from agent_accumulator_post import is_major_league
from agent_telegram_offers import send_to_channel, SITE_URL
from agent3_social import post_facebook, post_instagram
from agent_twitter_posts import _post_tweet as post_twitter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PRED_JSON = REPO_ROOT / "data" / "predictions.json"

DEFAULT_MAX_MATCHES = 8
DEFAULT_DAYS = 7


# ── Fixture discovery (real, already-scraped data only) ──────────────────────

def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _favourite_from_odds(home_odds, draw_odds, away_odds) -> str | None:
    def _f(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None
    prices = {"Home": _f(home_odds), "Draw": _f(draw_odds), "Away": _f(away_odds)}
    prices = {k: v for k, v in prices.items() if v}
    if not prices:
        return None
    return min(prices, key=prices.get)


# "Premier League" and "Serie A" are each used as the bare top-flight name by
# several countries in this data source (confirmed live: Egypt, Armenia,
# Northern Ireland and Hong Kong all scrape through as "<Country> Premier
# League" alongside England's) — the same ambiguity agent_accumulator_post.py's
# is_major_league() already had to disambiguate. A bare "Premier League" query
# means England's; a bare "Serie A" query is genuinely ambiguous (Italy vs
# Brazil) so it requires the country-qualified form instead of guessing.
def _competition_matches(filter_text: str, actual_competition: str) -> bool:
    f = filter_text.lower().strip()
    a = actual_competition.lower()
    if f == "premier league":
        return "england premier league" in a or a == "premier league"
    if f == "serie a":
        return "italy serie a" in a or "brazil serie a" in a
    return f in a


def list_fixtures(competition_filter: str | None, days: int, major_only: bool) -> list[dict]:
    """Real fixtures only, from data/predictions.json (predictz.com/forebet.com,
    refreshed independently by update_predictions.py). Never invents a match."""
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=days)
    out: list[dict] = []
    seen: set[str] = set()

    for pred in _load_json(PRED_JSON).get("predictions", []):
        comp = pred.get("competition", "")
        if competition_filter and not _competition_matches(competition_filter, comp):
            continue
        if major_only and not is_major_league(comp):
            continue

        ko_utc = pred.get("ko_utc")
        ko_dt = None
        if ko_utc:
            try:
                ko_dt = datetime.fromisoformat(ko_utc.replace("Z", "+00:00"))
            except Exception:
                ko_dt = None
        # predictz.com entries never carry a real ko_utc (documented upstream) —
        # they're inherently "today" since that's all that source scrapes, so
        # only apply the days-window filter when we actually have a timestamp.
        if ko_dt and (ko_dt < now - timedelta(minutes=90) or ko_dt > window_end):
            continue

        home, away = pred.get("home", ""), pred.get("away", "")
        key = f"{home.lower()}|{away.lower()}"
        if not home or not away or key in seen:
            continue
        seen.add(key)

        out.append({
            "home": home,
            "away": away,
            "competition": comp,
            "ko_utc": ko_utc,
            "ko_display": pred.get("ko_display", "Today"),
            "home_odds": pred.get("home_odds") or None,
            "draw_odds": pred.get("draw_odds") or None,
            "away_odds": pred.get("away_odds") or None,
            "odds_favourite": _favourite_from_odds(
                pred.get("home_odds"), pred.get("draw_odds"), pred.get("away_odds")
            ),
            "source_pick": pred.get("match_winner_label", ""),
            "source_over25": pred.get("over25", ""),
            "source_btts": pred.get("btts", ""),
            "source_correct_score": pred.get("correct_score", ""),
        })

    out.sort(key=lambda f: (f.get("ko_utc") or "zzz", f["home"]))
    return out


# ── Analysis (grounded LLM synthesis, honest odds-only fallback) ─────────────

SYSTEM_PROMPT = """You are the SifuFinds Football Prediction Agent, a UK-based \
football analyst writing for African and UK football fans. Use UK English \
(favourite, colour, organise, side/squad, boot, pitch, full stops).

Rules:
- Do not sound robotic or generic. Vary sentence length. Never join clauses \
with an em dash or en dash.
- Use only the real facts given to you below (the fixture, its real market \
odds if present, and the research notes). Never invent a specific injury, \
line-up, transfer, or statistic that isn't in those notes. If the notes are \
thin or empty, reason from general football logic (recent identity of the \
sides, competition context, home advantage) and say plainly that specific \
team news wasn't available, rather than making something up.
- Never guarantee a result or use phrases like "sure thing" or "guaranteed". \
This is analysis and opinion, not a certainty.
- Confidence must reflect how solid the actual evidence is - do not default \
to a high number just because one side looks stronger on paper.
- Respond with ONLY a single JSON object and nothing else (no markdown \
fences, no commentary before or after it), with exactly these keys:
{"home_win_pct": <int>, "draw_pct": <int>, "away_win_pct": <int>, \
"predicted_score": "<int>-<int>", "btts": "Yes" or "No", \
"over_2_5": "Yes" or "No", "confidence": <int 50-95>, \
"analysis": "<2 to 4 sentences>"}
The three percentages must sum to 100.
"""


def _build_user_message(fixture: dict, research_notes: str) -> str:
    lines = [
        f"Competition: {fixture['competition']}",
        f"Fixture: {fixture['home']} vs {fixture['away']}",
        f"Kick-off: {fixture.get('ko_display', 'unknown')}",
    ]
    if fixture.get("home_odds") or fixture.get("draw_odds") or fixture.get("away_odds"):
        lines.append(
            "Real market odds - Home: {} Draw: {} Away: {}".format(
                fixture.get("home_odds") or "n/a",
                fixture.get("draw_odds") or "n/a",
                fixture.get("away_odds") or "n/a",
            )
        )
    if fixture.get("source_pick"):
        lines.append(
            f"Note: a third-party tipster site's public pick for this match is "
            f"\"{fixture['source_pick']}\" - treat this as one outside opinion, "
            f"not fact, and form your own independent view."
        )
    lines.append("")
    lines.append("Research notes (real, sourced web snippets - may be empty):")
    lines.append(research_notes.strip() if research_notes else "(no research notes available for this match)")
    return "\n".join(lines)


def _parse_llm_json(raw: str) -> dict | None:
    if not raw:
        return None
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except Exception:
        return None

    try:
        h, d, a = int(data["home_win_pct"]), int(data["draw_pct"]), int(data["away_win_pct"])
        conf = int(data["confidence"])
        score = str(data["predicted_score"]).strip()
        btts = str(data.get("btts", "")).strip().capitalize()
        over = str(data.get("over_2_5", "")).strip().capitalize()
        analysis = str(data.get("analysis", "")).strip()
    except (KeyError, ValueError, TypeError):
        return None

    if abs((h + d + a) - 100) > 3:
        return None
    if not re.match(r"^\d+-\d+$", score):
        return None
    if not (50 <= conf <= 100):
        return None
    if btts not in ("Yes", "No"):
        btts = ""
    if over not in ("Yes", "No"):
        over = ""

    predicted_result = max([("Home", h), ("Draw", d), ("Away", a)], key=lambda t: t[1])[0]
    return {
        "home_win_pct": h, "draw_pct": d, "away_win_pct": a,
        "predicted_score": score, "predicted_result": predicted_result,
        "btts": btts, "over_2_5": over, "confidence": conf, "analysis": analysis,
    }


def _fallback_prediction(fixture: dict) -> dict:
    """Honest degraded mode when the LLM is unreachable or returns something
    unparseable — derives a prediction from the fixture's own real market odds
    (implied probability) instead of inventing anything, and is labelled as
    such. If there are no odds either, returns a low-confidence neutral guess."""
    def _implied(o):
        try:
            return 1.0 / float(o)
        except (TypeError, ValueError, ZeroDivisionError):
            return None

    probs = {
        "Home": _implied(fixture.get("home_odds")),
        "Draw": _implied(fixture.get("draw_odds")),
        "Away": _implied(fixture.get("away_odds")),
    }
    if all(v is not None for v in probs.values()):
        total = sum(probs.values())
        pct = {k: round(100 * v / total) for k, v in probs.items()}
        drift = 100 - sum(pct.values())
        pct["Home"] += drift
        favourite = max(pct, key=pct.get)
        score = {"Home": "2-1", "Away": "1-2", "Draw": "1-1"}[favourite]
        return {
            "home_win_pct": pct["Home"], "draw_pct": pct["Draw"], "away_win_pct": pct["Away"],
            "predicted_score": score, "predicted_result": favourite,
            "btts": "", "over_2_5": "", "confidence": 55,
            "analysis": (
                "Automated fallback based on the real market odds available for this "
                "fixture (the analysis model was unreachable for this run)."
            ),
        }
    return {
        "home_win_pct": 40, "draw_pct": 27, "away_win_pct": 33,
        "predicted_score": "1-1", "predicted_result": "Draw",
        "btts": "", "over_2_5": "", "confidence": 50,
        "analysis": (
            "No market odds or research were available for this fixture at "
            "generation time, so this is a low-confidence holding prediction."
        ),
    }


def analyze_match(fixture: dict, use_research: bool = True) -> dict:
    notes = ""
    if use_research:
        try:
            notes = research(f"{fixture['home']} vs {fixture['away']} preview team news")
        except Exception:
            notes = ""

    raw = ""
    try:
        raw = ask(SYSTEM_PROMPT, _build_user_message(fixture, notes))
    except Exception:
        raw = ""

    parsed = _parse_llm_json(raw)
    return parsed if parsed is not None else _fallback_prediction(fixture)


# ── Prediction record ─────────────────────────────────────────────────────────

def build_record(fixture: dict, parsed: dict, round_label: str, season: str) -> dict:
    return {
        "id": make_id(fixture["home"], fixture["away"], fixture.get("ko_utc")),
        "competition": fixture["competition"],
        "season": season,
        "round": round_label,
        "home": fixture["home"],
        "away": fixture["away"],
        "ko_utc": fixture.get("ko_utc"),
        "ko_display": fixture.get("ko_display", ""),
        "odds_favourite": fixture.get("odds_favourite"),
        "predicted_score": parsed["predicted_score"],
        "predicted_result": parsed["predicted_result"],
        "home_win_pct": parsed["home_win_pct"],
        "draw_pct": parsed["draw_pct"],
        "away_win_pct": parsed["away_win_pct"],
        "confidence": parsed["confidence"],
        "btts": parsed.get("btts", ""),
        "over_2_5": parsed.get("over_2_5", ""),
        "analysis": parsed.get("analysis", ""),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "actual_score": None,
        "actual_result": None,
        "correct_result": None,
        "correct_score": None,
        "btts_correct": None,
        "over_2_5_correct": None,
        "points": None,
        "graded_at": None,
    }


def confidence_band(conf: int) -> str:
    if conf >= 90:
        return "Exceptional"
    if conf >= 80:
        return "Very High"
    if conf >= 70:
        return "High"
    if conf >= 60:
        return "Medium"
    return "Low"


def pick_best(records: list[dict]) -> dict:
    return max(records, key=lambda r: r["confidence"])


_COMP_PRIORITY = [
    "world cup", "champions league", "premier league", "la liga",
    "italy serie a", "bundesliga", "ligue 1", "afcon", "caf champions league",
]


def pick_biggest(records: list[dict]) -> dict:
    def rank(r: dict) -> int:
        comp = r["competition"].lower()
        for i, kw in enumerate(_COMP_PRIORITY):
            if kw in comp:
                return i
        return len(_COMP_PRIORITY)
    return min(records, key=rank)


def pick_upset(records: list[dict]) -> dict | None:
    candidates = [
        r for r in records
        if r.get("odds_favourite") and r["odds_favourite"] != r["predicted_result"]
    ]
    return min(candidates, key=lambda r: r["confidence"]) if candidates else None


# ── Social copy builders ──────────────────────────────────────────────────────

_DISCLAIMER = "🔞 18+ | Predictions are analysis and opinion, not guaranteed outcomes. Gamble responsibly."


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _round_title(competition: str, round_label: str) -> str:
    return f"SifuFinds {competition} Predictions" + (f" — {round_label}" if round_label else "")


def build_telegram_post(records: list[dict], competition: str, round_label: str) -> str:
    title = _round_title(competition, round_label)
    lines = [f"⚽ <b>{_escape(title)}</b>", ""]
    for r in records:
        lines.append(f"🔹 <b>{_escape(r['home'])} vs {_escape(r['away'])}</b>")
        lines.append(f"   Predicted: {r['predicted_score']} ({r['predicted_result']} win)")
        lines.append(f"   Confidence: {r['confidence']}% ({confidence_band(r['confidence'])})")
        extras = []
        if r.get("btts"):
            extras.append(f"BTTS: {r['btts']}")
        if r.get("over_2_5"):
            extras.append(f"O2.5: {r['over_2_5']}")
        if extras:
            lines.append("   " + " · ".join(extras))
        lines.append("")

    best = pick_best(records)
    lines.append(f"⭐ Strongest prediction: {best['home']} vs {best['away']} — {best['predicted_score']} ({best['confidence']}%)")
    upset = pick_upset(records)
    if upset:
        lines.append(f"⚠️ Potential upset: {upset['home']} vs {upset['away']} — our lean differs from the market favourite")
    lines.append("")
    lines.append("💬 What's your prediction? Drop your scores below 👇")
    lines.append("")
    lines.append(f"🌐 <a href=\"{SITE_URL}\">SifuFinds.com</a>")
    lines.append("")
    lines.append(_DISCLAIMER)
    return "\n".join(lines)


def build_facebook_post(records: list[dict], competition: str, round_label: str) -> str:
    title = _round_title(competition, round_label)
    lines = [f"🔥 {title} are here!", "", "Who wins this round?", ""]
    for r in records:
        lines.append(f"{r['home']} {r['predicted_score']} {r['away']}  ({r['confidence']}% confidence)")
    lines.append("")
    lines.append("👀 What's YOUR prediction? Drop your scores in the comments.")
    lines.append("")
    lines.append(f"🌐 {SITE_URL}")
    lines.append("")
    lines.append(_DISCLAIMER)
    lines.append("")
    lines.append(f"#FootballPredictions #SifuFinds #{competition.replace(' ', '')}")
    return "\n".join(lines)


def build_instagram_post(records: list[dict], competition: str, round_label: str) -> str:
    title = _round_title(competition, round_label)
    body = [f"⚽ {title}", ""]
    for r in records:
        body.append(f"{r['home']} {r['predicted_score']} {r['away']}")
    body.append("")
    body.append("❤️🔥 Double-tap and drop a comment with your score prediction!")
    body.append("")
    body.append(_DISCLAIMER)
    body.append(".\n.\n.")
    hashtags = f"#SifuFinds #FootballPredictions #{competition.replace(' ', '')} #Football #Predictions"
    body.append(hashtags)
    return "\n".join(body)


def build_twitter_post(records: list[dict], competition: str, round_label: str) -> str:
    title = _round_title(competition, round_label)
    lines = [f"⚽ {title}", ""]
    for r in records[:5]:
        lines.append(f"{r['home']} {r['predicted_score']} {r['away']}")
    lines.append("")
    lines.append("What's your score prediction? 👇")
    lines.append(f"#SifuFinds #{competition.replace(' ', '')} 🔞18+")
    return _trim_to_limit("\n".join(lines))


def build_threads_post(records: list[dict], competition: str, round_label: str) -> str:
    best = pick_best(records)
    title = _round_title(competition, round_label)
    return (
        f"{title} 👀\n\n"
        f"Our strongest lean: {best['home']} {best['predicted_score']} {best['away']} "
        f"({best['confidence']}% confidence).\n\n"
        f"Full set of picks on the SifuFinds channel — what's your score? 👇\n\n"
        f"#SifuFinds #Football"
    )


def build_tiktok_script(records: list[dict], competition: str, round_label: str) -> str:
    best = pick_best(records)
    biggest = pick_biggest(records)
    title = _round_title(competition, round_label)
    return (
        f"[TIKTOK SCRIPT — {title}]\n\n"
        f"HOOK: \"Here's what SifuFinds is calling for {competition}{' ' + round_label if round_label else ''}...\"\n\n"
        f"BODY:\n"
        + "\n".join(f"- {r['home']} vs {r['away']}: {r['predicted_score']}, {r['confidence']}% confidence" for r in records[:5])
        + f"\n\nBIGGEST GAME: {biggest['home']} vs {biggest['away']} — {biggest['predicted_score']}\n"
        f"STRONGEST PICK: {best['home']} vs {best['away']} — {best['confidence']}% confidence\n\n"
        f"CTA: \"Drop your score prediction in the comments. Follow for more.\"\n"
        f"{_DISCLAIMER}"
    )


def build_linkedin_post(records: list[dict], competition: str, round_label: str) -> str:
    stats = aggregate_stats(competition=competition)
    title = _round_title(competition, round_label)
    track_line = (
        f"Season so far: {stats['result_accuracy_pct']}% result accuracy across "
        f"{stats['total_graded']} graded predictions."
        if stats.get("total_graded") else
        "Tracking every prediction's accuracy over the season."
    )
    noun = "prediction" if len(records) == 1 else "predictions"
    return (
        f"{title}\n\n"
        f"SifuFinds published {len(records)} data-driven {noun} for this round, "
        f"combining team form, market odds and match context. {track_line}\n\n"
        f"{SITE_URL}"
    )


def build_youtube_content(records: list[dict], competition: str, round_label: str) -> str:
    title = _round_title(competition, round_label)
    yt_title = title[:100]
    description_lines = [
        f"SifuFinds' predictions for {competition}{' ' + round_label if round_label else ''}.",
        "",
    ] + [f"{r['home']} {r['predicted_score']} {r['away']}" for r in records] + [
        "", "Predictions are analysis and opinion, not guaranteed outcomes. 18+ Gamble responsibly.",
        f"More at {SITE_URL}",
    ]
    script_lines = [f"Welcome back to SifuFinds. Let's get into our {competition} predictions."]
    for r in records:
        script_lines.append(
            f"{r['home']} against {r['away']}: we're calling {r['predicted_score']}, "
            f"{confidence_band(r['confidence']).lower()} confidence at {r['confidence']} percent."
        )
    script_lines.append("That's the round. Let us know your own predictions in the comments.")
    return (
        f"TITLE: {yt_title}\n\n"
        f"DESCRIPTION:\n" + "\n".join(description_lines) + "\n\n"
        f"SHORT-FORM SCRIPT:\n" + "\n".join(script_lines)
    )


# ── Modes ─────────────────────────────────────────────────────────────────────

def run_generate(args: argparse.Namespace) -> None:
    competition = args.competition
    major_only = args.today or args.major_only
    fixtures = list_fixtures(competition, args.days, major_only)

    if not fixtures:
        scope = competition or "major competitions"
        print(f"✗ No verified fixtures found for {scope} in the current data window (next {args.days} day(s)).")
        print("  Refusing to invent a fixture. Try again once data/predictions.json has a refresh, or widen --days.")
        log("predictions", "generate", "no_fixtures", competition or "today")
        sys.exit(1)

    fixtures = fixtures[: args.max_matches]
    season = args.season or f"{datetime.now(timezone.utc).year}-{str(datetime.now(timezone.utc).year + 1)[-2:]}"

    records: list[dict] = []
    for fx in fixtures:
        rid = make_id(fx["home"], fx["away"], fx.get("ko_utc"))
        if already_predicted(rid):
            print(f"  [skip] already predicted: {fx['home']} vs {fx['away']}")
            continue
        print(f"  [analysing] {fx['home']} vs {fx['away']} ({fx['competition']}) ...")
        parsed = analyze_match(fx, use_research=not args.no_research)
        record = build_record(fx, parsed, args.round or "", season)
        record["odds_favourite"] = fx.get("odds_favourite")
        records.append(record)
        if not args.dry_run:
            add_prediction(record)

    if not records:
        print("✗ Every matching fixture was already predicted previously — nothing new to generate.")
        log("predictions", "generate", "all_already_predicted", competition or "today")
        return

    comp_label = competition or "Football"
    telegram_text = build_telegram_post(records, comp_label, args.round or "")
    facebook_text = build_facebook_post(records, comp_label, args.round or "")
    instagram_text = build_instagram_post(records, comp_label, args.round or "")
    twitter_text = build_twitter_post(records, comp_label, args.round or "")
    threads_text = build_threads_post(records, comp_label, args.round or "")
    tiktok_text = build_tiktok_script(records, comp_label, args.round or "")
    linkedin_text = build_linkedin_post(records, comp_label, args.round or "")
    youtube_text = build_youtube_content(records, comp_label, args.round or "")

    sections = [
        ("TELEGRAM (auto-posting)" if args.telegram and not args.dry_run else "TELEGRAM (preview)", telegram_text),
        ("FACEBOOK (auto-posting)" if args.facebook and not args.dry_run else "FACEBOOK (preview)", facebook_text),
        ("INSTAGRAM (auto-posting)" if args.instagram and not args.dry_run else "INSTAGRAM (preview)", instagram_text),
        ("X / TWITTER (auto-posting)" if args.twitter and not args.dry_run else "X / TWITTER (preview)", twitter_text),
        ("THREADS (copy/paste — no auto-post integration configured)", threads_text),
        ("TIKTOK SCRIPT (copy/paste — no auto-post integration configured)", tiktok_text),
        ("LINKEDIN (copy/paste — post sparingly, not every round)", linkedin_text),
        ("YOUTUBE (copy/paste — title/description/script)", youtube_text),
    ]
    print("\n" + "═" * 60)
    for header, text in sections:
        print(header)
        print("─" * 60)
        print(text)
        print("─" * 60 + "\n")

    if args.dry_run:
        print("Dry run — nothing saved or posted.")
        return

    results: dict[str, bool] = {}
    if args.telegram:
        results["telegram"] = send_to_channel(telegram_text)
        print("✓ Posted to Telegram." if results["telegram"] else "✗ Telegram post failed.")
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
        log("predictions", platform, "success" if ok else "failed", comp_label)
    log("predictions", "generate", "success", f"{comp_label} ({len(records)} fixtures)")


def run_grade(_: argparse.Namespace) -> None:
    graded = grade_pending()
    if not graded:
        print("No predictions were ready to grade (either none pending, or results not yet confirmed on ESPN).")
        log("predictions", "grade", "none_pending", "")
        return
    print(f"Graded {len(graded)} prediction(s):\n")
    for p in graded:
        mark = "✅" if p["correct_score"] else ("🟡" if p["correct_result"] else "❌")
        print(
            f"{mark} {p['home']} {p['actual_score']} {p['away']} "
            f"(predicted {p['predicted_score']}, {p['points']} pt)"
        )
    log("predictions", "grade", "success", f"{len(graded)} graded")


def run_stats(args: argparse.Namespace) -> None:
    stats = aggregate_stats(competition=args.competition, season=args.season)
    if stats.get("total_graded", 0) == 0:
        scope = args.competition or "all competitions"
        print(f"No graded predictions yet for {scope}" + (f", season {args.season}" if args.season else "") + ".")
        return
    print(json.dumps(stats, indent=2))


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="SifuFinds Football Prediction Agent")
    parser.add_argument("competition", nargs="?", default=None, help='e.g. "Premier League", "FA Cup"')
    parser.add_argument("--round", type=str, default="", help='e.g. "Gameweek 1", "Third Round"')
    parser.add_argument("--season", type=str, default="", help='e.g. "2025-26"')
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help="Fixture lookahead window in days")
    parser.add_argument("--max-matches", type=int, default=DEFAULT_MAX_MATCHES, dest="max_matches")
    parser.add_argument("--today", action="store_true", help="All major competitions, no competition filter")
    parser.add_argument("--major-only", action="store_true", dest="major_only", help="Restrict to major/African leagues")
    parser.add_argument("--no-research", action="store_true", dest="no_research", help="Skip free web research, odds-only analysis")
    parser.add_argument("--no-telegram", dest="telegram", action="store_false")
    parser.add_argument("--no-facebook", dest="facebook", action="store_false")
    parser.add_argument("--no-instagram", dest="instagram", action="store_false")
    parser.add_argument("--no-twitter", dest="twitter", action="store_false")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    parser.add_argument("--grade", action="store_true", help="Grade completed predictions against real results")
    parser.add_argument("--stats", action="store_true", help="Print season/competition accuracy report")
    parser.set_defaults(telegram=True, facebook=True, instagram=True, twitter=True)
    args = parser.parse_args()

    if args.grade:
        run_grade(args)
        return
    if args.stats:
        run_stats(args)
        return
    if not args.competition and not args.today:
        parser.error("Provide a competition (e.g. \"Premier League\") or use --today")
    run_generate(args)


if __name__ == "__main__":
    main()
