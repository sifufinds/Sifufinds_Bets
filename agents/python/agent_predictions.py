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

Fixture source: merged from data/predictions.json (predictz.com + forebet.com)
and data/matches_live.json (football-data.org/ESPN, real kick-off dates days
ahead — what makes a whole gameweek visible before it's played). Never
invented here. If a requested competition/round has no matching fixtures in
the current window, this agent says so and predicts nothing rather than
fabricate one.

Analysis: for each fixture, a short free web research pass (utils/serp_research
.research(), free-only, no Firecrawl) gathers real, sourced team-news snippets;
those notes plus the fixture's own real odds/kick-off are given to the free-tier
LLM chain (llm.ask(), Groq -> g4f -> Ollama, per this repo's no-paid-API rule) to
produce a probability split, predicted score, BTTS/O2.5 call, confidence and a
short write-up. If research turns up nothing or the LLM is unreachable, a
transparent odds-only fallback is used instead of guessing team-specific facts.

Telegram posts also carry: a branded image with every fixture's real club
crest (utils/gameweek_card.py, ESPN's own CDN) next to the predicted score,
and a real Telegram poll (utils/prediction_game.py) on the round's strongest
pick so followers can vote — graded against the actual result once the match
finishes, tracking crowd-vs-model accuracy over the season (--game-tally).

Usage:
  python3 agent_predictions.py "Premier League" --round "Gameweek 1"
  python3 agent_predictions.py "FA Cup" --round "Third Round" --days 10
  python3 agent_predictions.py --today                       # all major competitions, today
  python3 agent_predictions.py "Premier League" --dry-run     # preview only, nothing posted/saved
  python3 agent_predictions.py --grade                        # grade completed predictions + polls
  python3 agent_predictions.py --stats                         # season accuracy report
  python3 agent_predictions.py --stats --competition "Premier League" --season "2025-26"
  python3 agent_predictions.py --game-tally                     # crowd-vs-model poll accuracy
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

from llm import ask
from utils.logger import log
from utils.serp_research import research
from utils.tweet_text import trim_to_limit as _trim_to_limit
from utils.gameweek_card import build_gameweek_card
from utils.prediction_game import send_prediction_poll, close_and_grade_poll, season_tally
from utils.prediction_store import (
    add_prediction, already_predicted, make_id,
    grade_pending, aggregate_stats,
    resolve_espn_slug, ESPN_BASE, SESSION, _expand_nickname,
)
from agent_accumulator_post import is_major_league
from agent_telegram_offers import send_to_channel, send_photo_to_channel, SITE_URL
from agent3_social import post_facebook, post_instagram
from agent_twitter_posts import _post_tweet as post_twitter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PRED_JSON = REPO_ROOT / "data" / "predictions.json"
LIVE_JSON = REPO_ROOT / "data" / "matches_live.json"

DEFAULT_MAX_MATCHES = 10
DEFAULT_DAYS = 7

_STALE_LIVE_STATUSES = {"FINISHED", "POSTPONED", "CANCELLED", "AWARDED", "SUSPENDED"}
_MERGE_FIELDS = [
    "ko_utc", "ko_display", "home_odds", "draw_odds", "away_odds",
    "odds_favourite", "source_pick", "source_over25", "source_btts", "source_correct_score",
]


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


def _tokens(s: str) -> set[str]:
    # Shares prediction_store's nickname table (Spurs/Wolves/etc.) so a real
    # fixture can't match here (predictions.json <-> matches_live.json merge)
    # but then fail the same club's ESPN crest/grading lookup for the same
    # reason, or vice versa.
    return set(re.findall(r"[a-z0-9]+", _expand_nickname(s).lower()))


def _team_match_score(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), 1)


def _merge_fixture_lists(primary: list[dict], secondary: list[dict]) -> list[dict]:
    """Merge two independently-real fixture lists describing the same real
    matches rather than picking one source and discarding the other's fields —
    same pattern as agent_match_post.find_football_match()."""
    merged: list[dict] = []
    used_secondary: set[int] = set()

    for p in primary:
        best_j, best_score = None, 0.0
        for j, s in enumerate(secondary):
            if j in used_secondary:
                continue
            score = _team_match_score(p["home"], s["home"]) + _team_match_score(p["away"], s["away"])
            if score > best_score:
                best_score, best_j = score, j
        if best_j is not None and best_score >= 1.2:
            s = secondary[best_j]
            used_secondary.add(best_j)
            combined = dict(p)
            for field in _MERGE_FIELDS:
                if not combined.get(field) and s.get(field):
                    combined[field] = s[field]
            merged.append(combined)
        else:
            merged.append(p)

    for j, s in enumerate(secondary):
        if j not in used_secondary:
            merged.append(s)

    return merged


def _fixtures_from_predictions_json(competition_filter: str | None, days: int, major_only: bool) -> list[dict]:
    """Real fixtures from data/predictions.json (predictz.com/forebet.com,
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


def _fixtures_from_live_json(competition_filter: str | None, days: int, major_only: bool) -> list[dict]:
    """Real, dated fixtures from data/matches_live.json (football-data.org/ESPN,
    refreshed independently by update_leagues.py for the /leagues/ page). Unlike
    predictions.json, these carry a genuine kick-off timestamp for matches days
    out, which is what actually makes a full gameweek's fixture list visible
    ahead of time rather than only "today". compName values here are already
    single, unambiguous competition names (this source's own competition IDs
    disambiguate country, unlike predictz.com's scraped free-text headers), so
    no _competition_matches() disambiguation is needed for this source."""
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=days)
    out: list[dict] = []
    seen: set[str] = set()

    for matches in _load_json(LIVE_JSON).get("byDate", {}).values():
        for m in matches:
            if m.get("status") in _STALE_LIVE_STATUSES:
                continue
            comp = m.get("compName", "")
            if competition_filter and competition_filter.lower() not in comp.lower():
                continue
            if major_only and not is_major_league(comp):
                continue

            ko_dt = None
            utc_date = m.get("utcDate")
            if utc_date:
                try:
                    ko_dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
                except Exception:
                    ko_dt = None
            if ko_dt and (ko_dt < now - timedelta(minutes=90) or ko_dt > window_end):
                continue

            home, away = m.get("home", ""), m.get("away", "")
            key = f"{home.lower()}|{away.lower()}"
            if not home or not away or key in seen:
                continue
            seen.add(key)

            out.append({
                "home": home,
                "away": away,
                "competition": comp,
                "ko_utc": ko_dt.isoformat() if ko_dt else None,
                "ko_display": f"{m.get('date', '')} · {m.get('time', '')}".strip(" ·"),
                "home_odds": None,
                "draw_odds": None,
                "away_odds": None,
                "odds_favourite": None,
                "source_pick": "",
                "source_over25": "",
                "source_btts": "",
                "source_correct_score": "",
            })

    out.sort(key=lambda f: (f.get("ko_utc") or "zzz", f["home"]))
    return out


def list_fixtures(competition_filter: str | None, days: int, major_only: bool) -> list[dict]:
    """Real fixtures only, merged from data/predictions.json (odds + third-party
    tipster picks) and data/matches_live.json (real kick-off dates days ahead,
    which is what makes a whole gameweek visible rather than only "today").
    Never invents a fixture."""
    from_predictions = _fixtures_from_predictions_json(competition_filter, days, major_only)
    from_live = _fixtures_from_live_json(competition_filter, days, major_only)
    fixtures = _merge_fixture_lists(from_live, from_predictions)
    fixtures.sort(key=lambda f: (f.get("ko_utc") or "zzz", f["home"]))
    return fixtures


# ── Real club crests (ESPN's own CDN — never a guessed/placeholder URL) ──────

_espn_events_cache: dict[tuple[str, str], list[dict]] = {}


def _espn_events_for(slug: str, date_str: str) -> list[dict]:
    key = (slug, date_str)
    if key in _espn_events_cache:
        return _espn_events_cache[key]
    try:
        r = SESSION.get(f"{ESPN_BASE}/{slug}/scoreboard", params={"dates": date_str}, timeout=15)
        events = r.json().get("events", [])
    except Exception:
        events = []
    _espn_events_cache[key] = events
    return events


def enrich_crests(records: list[dict]) -> None:
    """Attach real home_crest/away_crest image URLs from ESPN's own CDN
    (mutates records in place). Leaves both fields absent when no confidently-
    matching ESPN event is found for a competition/date — never guesses a
    crest for the wrong club."""
    for r in records:
        slug = resolve_espn_slug(r.get("competition", ""))
        ko = r.get("ko_utc")
        if not slug or not ko:
            continue
        try:
            ko_dt = datetime.fromisoformat(ko.replace("Z", "+00:00"))
        except Exception:
            continue

        for offset in (0, 1, -1, 2):
            date_str = (ko_dt + timedelta(days=offset)).strftime("%Y%m%d")
            matched = False
            for ev in _espn_events_for(slug, date_str):
                comp = (ev.get("competitions") or [{}])[0]
                competitors = comp.get("competitors", [])
                if len(competitors) != 2:
                    continue
                h = next((c for c in competitors if c.get("homeAway") == "home"), None)
                a = next((c for c in competitors if c.get("homeAway") == "away"), None)
                if not h or not a:
                    continue
                h_team, a_team = h.get("team", {}), a.get("team", {})
                h_name, a_name = h_team.get("displayName", ""), a_team.get("displayName", "")
                straight = _team_match_score(r["home"], h_name) + _team_match_score(r["away"], a_name)
                swapped = _team_match_score(r["home"], a_name) + _team_match_score(r["away"], h_name)
                if max(straight, swapped) < 1.2:
                    continue
                if straight >= swapped:
                    r["home_crest"], r["away_crest"] = h_team.get("logo"), a_team.get("logo")
                else:
                    r["home_crest"], r["away_crest"] = a_team.get("logo"), h_team.get("logo")
                matched = True
                break
            if matched:
                break


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
        "id": make_id(fixture["home"], fixture["away"], fixture["competition"], season),
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

_DISCLAIMER = "🔞 18+ | Gamble responsibly"
_LONG_DISCLAIMER = "🔞 18+ | Predictions are analysis and opinion, not guaranteed outcomes. Gamble responsibly."


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _round_title(competition: str, round_label: str) -> str:
    return f"SifuFinds {competition} Predictions" + (f" — {round_label}" if round_label else "")


def _round_label_or(round_label: str, fallback: str = "this round") -> str:
    return round_label if round_label else fallback


def _dominant_score(records: list[dict], threshold: float = 0.6) -> tuple[str, int, int] | None:
    """Detect the funny-but-real case where the model landed on the same
    scoreline for most or all of a round (typical of the odds-neutral fallback
    firing across a whole batch — a real live batch came back 9 draws out of
    10, not literally all 10) so the copy can lean into it honestly instead of
    pretending every pick is independently bold. Returns (score, count, total)
    once at least `threshold` of the round shares one scoreline, else None."""
    if len(records) < 2:
        return None
    counts = Counter(r["predicted_score"] for r in records)
    score, n = counts.most_common(1)[0]
    total = len(records)
    if n > 1 and n / total >= threshold:
        return score, n, total
    return None


def _dominant_hook(dom: tuple[str, int, int]) -> str:
    score, n, total = dom
    if n == total:
        return f"Our model is calling {score} in EVERY GAME"
    return f"{n} of our {total} picks this round are ALL calling {score}"


def _dominant_strongest_joke(dom: tuple[str, int, int]) -> str:
    score, n, total = dom
    if n == total:
        return f"Apparently… ALL OF THEM! 🤷‍♂️😂 Yes... we're predicting {n} {score}s in a row!"
    return f"Apparently… {n} OF THEM! 🤷‍♂️😂 Yes... {n} of our {total} picks are all {score}!"


def _hashtags_for(competition: str, round_label: str) -> str:
    tags = [f"#{competition.replace(' ', '')}"]
    if round_label:
        tags.append(f"#{re.sub(r'[^A-Za-z0-9]', '', round_label)}")
    tags += ["#FootballPredictions", "#SifuFinds", "#Football"]
    return " ".join(tags)


def build_telegram_caption(records: list[dict], competition: str, round_label: str) -> str:
    """Short, fun caption sent WITH the gameweek card image — the image
    itself already shows every fixture's score and confidence, so this stays
    a hook, not a repeat of that data."""
    round_upper = round_label.upper() if round_label else "THIS ROUND"
    dom = _dominant_score(records)
    title = f"⚽🔥 SIFUFINDS {competition.upper()} PREDICTIONS: {round_upper}! 🔥⚽"

    if dom:
        hook = f"{_dominant_hook(dom)} 😭😂 Do you agree, or is SifuFinds about to get cooked below? 🔥"
    else:
        hook = "Bold calls, tight matches, and one pick we're genuinely backing 👀"

    return f"{title}\n\n{hook}"


def build_telegram_post(records: list[dict], competition: str, round_label: str) -> str:
    """Short follow-up text sent after the card image and the poll — a pure
    call to action, since the fixtures/scores already live in the image."""
    return "\n".join([
        "👇 NOW IT'S YOUR TURN!",
        "",
        "Forget our predictions for a second...",
        "",
        "🔥 Who wins?",
        "🤝 Who draws?",
        "💥 Who pulls off the upset?",
        "🎯 What's your exact score?",
        "",
        f"Drop your {_round_label_or(round_label)} predictions in the comments! 👇",
        "",
        "Let's see who knows their football! ⚽",
        "",
        f"🌐 <a href=\"{SITE_URL}\">SifuFinds.com</a>",
        "",
        _DISCLAIMER,
        "",
        _hashtags_for(competition, round_label),
    ])


def build_facebook_post(records: list[dict], competition: str, round_label: str) -> str:
    round_upper = round_label.upper() if round_label else "THIS ROUND"
    dom = _dominant_score(records)
    best = pick_best(records)

    lines = [f"⚽🔥 SIFUFINDS {competition.upper()} PREDICTIONS: {round_upper}! 🔥⚽", ""]
    if dom:
        lines += [
            f"{_dominant_hook(dom)} 😭",
            "Bold, or about to get cooked in the comments? You decide 👇",
        ]
    else:
        lines += ["Who wins this round? Here's what our model is calling 👇"]
    lines.append("")

    for r in records:
        lines.append(f"{r['home']} {r['predicted_score']} {r['away']}  ({r['confidence']}% confidence)")

    lines.append("")
    if dom:
        lines.append(f"⭐ Our \"strongest\" pick? {_dominant_strongest_joke(dom)}")
    else:
        lines.append(f"⭐ Strongest pick: {best['home']} {best['predicted_score']} {best['away']} ({best['confidence']}%)")
    lines.append("")
    lines.append("👀 What's YOUR prediction? Drop your scores in the comments.")
    lines.append("")
    lines.append(f"🌐 {SITE_URL}")
    lines.append("")
    lines.append(_DISCLAIMER)
    lines.append("")
    lines.append(_hashtags_for(competition, round_label))
    return "\n".join(lines)


def build_instagram_post(records: list[dict], competition: str, round_label: str) -> str:
    round_upper = round_label.upper() if round_label else "THIS ROUND"
    dom = _dominant_score(records)

    body = [f"⚽ SIFUFINDS {competition.upper()} PREDICTIONS: {round_upper} 🔥", ""]
    if dom:
        body.append(f"Plot twist: {_dominant_hook(dom).lower()} 😭👀")
        body.append("")
    for r in records:
        body.append(f"{r['home']} {r['predicted_score']} {r['away']}")
    body.append("")
    body.append("❤️🔥 Double-tap and drop a comment with your score prediction!")
    body.append("")
    body.append(_DISCLAIMER)
    body.append(".\n.\n.")
    body.append(_hashtags_for(competition, round_label) + " #Predictions")
    return "\n".join(body)


def build_twitter_post(records: list[dict], competition: str, round_label: str) -> str:
    round_upper = round_label.upper() if round_label else "this round"
    dom = _dominant_score(records)
    lines = [f"⚽🔥 SifuFinds {competition} predictions: {round_upper}!", ""]
    if dom:
        lines.append(f"😭 {_dominant_hook(dom)}. Bold or cooked? 👀")
        lines.append("")
    for r in records[:5]:
        lines.append(f"{r['home']} {r['predicted_score']} {r['away']}")
    lines.append("")
    lines.append("What's your score prediction? 👇")
    lines.append(f"{_hashtags_for(competition, round_label)} {_DISCLAIMER}")
    return _trim_to_limit("\n".join(lines))


def build_threads_post(records: list[dict], competition: str, round_label: str) -> str:
    dom = _dominant_score(records)
    best = pick_best(records)
    round_upper = round_label.upper() if round_label else "this round"
    if dom:
        return (
            f"⚽ SifuFinds {competition} predictions: {round_upper} 👀\n\n"
            f"Plot twist: {_dominant_hook(dom).lower()} 😭\n\n"
            f"Bold, or about to get cooked in the comments? Drop your own scores below 👇\n\n"
            f"{_hashtags_for(competition, round_label)}"
        )
    return (
        f"⚽ SifuFinds {competition} predictions: {round_upper} 👀\n\n"
        f"Our strongest lean: {best['home']} {best['predicted_score']} {best['away']} "
        f"({best['confidence']}% confidence).\n\n"
        f"Full set of picks on the SifuFinds channel — what's your score? 👇\n\n"
        f"{_hashtags_for(competition, round_label)}"
    )


def build_tiktok_script(records: list[dict], competition: str, round_label: str) -> str:
    best = pick_best(records)
    biggest = pick_biggest(records)
    dom = _dominant_score(records)
    title = _round_title(competition, round_label)
    hook = (
        f"\"Okay so {_dominant_hook(dom).lower()} this round... are we cooked, or onto something?\""
        if dom else
        f"\"Here's what SifuFinds is calling for {competition}{' ' + round_label if round_label else ''}...\""
    )
    return (
        f"[TIKTOK SCRIPT — {title}]\n\n"
        f"HOOK: {hook}\n\n"
        f"BODY:\n"
        + "\n".join(f"- {r['home']} vs {r['away']}: {r['predicted_score']}, {r['confidence']}% confidence" for r in records[:5])
        + f"\n\nBIGGEST GAME: {biggest['home']} vs {biggest['away']} — {biggest['predicted_score']}\n"
        f"STRONGEST PICK: {best['home']} vs {best['away']} — {best['confidence']}% confidence\n\n"
        f"CTA: \"Comment your own score prediction. Let's see who actually knows football. Follow for more.\"\n"
        f"{_LONG_DISCLAIMER}"
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
        # Not a failure exit: on a scheduled run, "nothing in the window today"
        # is a normal, frequent outcome (off-season, mid-week gap), not an
        # error — exiting 1 here would falsely trip this repo's auto-retry-on-
        # failure watchdog every time there's simply no fresh fixture yet.
        return

    fixtures = fixtures[: args.max_matches]
    season = args.season or f"{datetime.now(timezone.utc).year}-{str(datetime.now(timezone.utc).year + 1)[-2:]}"

    records: list[dict] = []
    for fx in fixtures:
        rid = make_id(fx["home"], fx["away"], fx["competition"], season)
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
    enrich_crests(records)
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
        card_path = None
        try:
            card_path = build_gameweek_card(
                records,
                title=f"SIFUFINDS {comp_label.upper()}",
                subtitle=(f"PREDICTIONS: {args.round.upper()}" if args.round else "PREDICTIONS"),
            )
        except Exception as exc:
            print(f"  [warn] gameweek card image failed, posting text-only: {exc}")

        photo_ok = True
        if card_path:
            caption = build_telegram_caption(records, comp_label, args.round or "")
            photo_ok = send_photo_to_channel(str(card_path), caption)

        results["telegram"] = photo_ok and send_to_channel(telegram_text)
        print("✓ Posted to Telegram." if results["telegram"] else "✗ Telegram post failed.")

        poll_target = pick_best(records)
        poll_id = send_prediction_poll(poll_target["id"], poll_target["home"], poll_target["away"]) if results["telegram"] else None
        print(
            f"✓ Prediction poll live for {poll_target['home']} vs {poll_target['away']}."
            if poll_id else "✗ Prediction poll not sent (no bot token, or send failed)."
        )
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
        poll_result = close_and_grade_poll(p["id"], p["actual_result"], p["predicted_result"])
        if poll_result and poll_result["total_votes"]:
            crowd_mark = "✅" if poll_result["crowd_correct"] else "❌"
            model_mark = "✅" if poll_result["model_correct"] else "❌"
            print(
                f"   🎮 Poll ({poll_result['total_votes']} votes): "
                f"crowd said {poll_result['crowd_pick']} {crowd_mark} | "
                f"SifuFinds said {p['predicted_result']} {model_mark}"
            )
            send_to_channel(
                f"🎮 RESULT: {p['home']} {p['actual_score']} {p['away']}\n\n"
                f"👥 The crowd voted {poll_result['crowd_pick']} {crowd_mark}\n"
                f"🤖 SifuFinds called {p['predicted_result']} {model_mark}\n\n"
                f"Who's got the sharper eye this season? 👀"
            )
    log("predictions", "grade", "success", f"{len(graded)} graded")


def run_stats(args: argparse.Namespace) -> None:
    stats = aggregate_stats(competition=args.competition, season=args.season)
    if stats.get("total_graded", 0) == 0:
        scope = args.competition or "all competitions"
        print(f"No graded predictions yet for {scope}" + (f", season {args.season}" if args.season else "") + ".")
        return
    print(json.dumps(stats, indent=2))


def run_game_tally(_: argparse.Namespace) -> None:
    tally = season_tally()
    if not tally.get("model_total"):
        print("No graded polled fixtures yet — the tally fills in once a polled fixture is graded.")
        return
    crowd_pct = round(100 * tally["crowd_correct"] / tally["crowd_total"], 1) if tally["crowd_total"] else None
    model_pct = round(100 * tally["model_correct"] / tally["model_total"], 1)
    print("🎮 SifuFinds Prediction Game — Crowd vs Model\n")
    print(f"🤖 SifuFinds: {tally['model_correct']}/{tally['model_total']} correct ({model_pct}%)")
    if crowd_pct is not None:
        print(f"👥 The crowd: {tally['crowd_correct']}/{tally['crowd_total']} correct ({crowd_pct}%)")


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
    parser.add_argument("--game-tally", dest="game_tally", action="store_true", help="Print the crowd-vs-model prediction game tally")
    parser.set_defaults(telegram=True, facebook=True, instagram=True, twitter=True)
    args = parser.parse_args()

    if args.grade:
        run_grade(args)
        return
    if args.stats:
        run_stats(args)
        return
    if args.game_tally:
        run_game_tally(args)
        return
    if not args.competition and not args.today:
        parser.error("Provide a competition (e.g. \"Premier League\") or use --today")
    run_generate(args)


if __name__ == "__main__":
    main()
