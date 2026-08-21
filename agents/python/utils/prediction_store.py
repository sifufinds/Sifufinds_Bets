"""
utils/prediction_store.py — persistent record for the SifuFinds Prediction Agent.

Every prediction the agent generates is written once to data/sifu_predictions.json
and never edited again except to add grading fields (actual_score, actual_result,
points, correct_result, correct_score, btts_correct, over_2_5_correct, graded_at)
once the real match has finished — matching the spec's "never alter the original
prediction after kick-off" rule.

Grading uses ESPN's free public soccer scoreboard API (the same endpoint
update_leagues.py already relies on for African leagues) to look up the real
final score. If a competition has no known ESPN slug, or ESPN has no matching
event, the prediction is simply left ungraded rather than guessed.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = REPO_ROOT / "data" / "sifu_predictions.json"

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
_STATUS_FINAL = {"STATUS_FULL_TIME", "STATUS_FINAL"}

# No custom User-Agent on ESPN requests — its edge (site.api.espn.com) returns
# HTTP 403 for ANY explicitly-set User-Agent (custom or realistic-browser
# alike) while the default python-requests UA gets HTTP 200. Already
# documented and fixed once in update_leagues.py (see its SESSION comment) —
# reproduced live here too, so don't re-add one without re-verifying first.
SESSION = requests.Session()

# ESPN slugs used ONLY for post-match grading lookups (never for fixture
# discovery/invention). "serie a" is deliberately absent as a bare key —
# several countries use that name for their top flight, so it's resolved
# explicitly in resolve_espn_slug() the same way agent_accumulator_post.py's
# is_major_league() disambiguates it.
ESPN_SLUGS: dict[str, str] = {
    "premier league": "eng.1",
    "championship": "eng.2",
    "league one": "eng.3",
    "league two": "eng.4",
    "la liga": "esp.1",
    "bundesliga": "ger.1",
    "ligue 1": "fra.1",
    "eredivisie": "ned.1",
    "primeira liga": "por.1",
    "scottish premiership": "sco.1",
    "belgian pro league": "bel.1",
    "super lig": "tur.1",
    "süper lig": "tur.1",
    "greek super league": "gre.1",
    "saudi pro league": "ksa.1",
    "mls": "usa.1",
    "argentine primera": "arg.1",
    "primera division": "arg.1",
    "south african premiership": "rsa.1",
    "psl": "rsa.1",
    "npfl": "nig.1",
    "nigeria premier": "nig.1",
    "ghana premier league": "gha.1",
    "kenyan premier league": "ken.1",
    "kenya premier league": "ken.1",
    "champions league": "uefa.champions",
    "europa league": "uefa.europa",
    "conference league": "uefa.europa.conf",
    "caf champions league": "caf.champions",
    "caf confederation": "caf.confed",
    "afcon": "caf.nations",
    "world cup": "fifa.world",
}


def resolve_espn_slug(competition: str) -> str | None:
    comp = (competition or "").lower()
    if "italy serie a" in comp:
        return "ita.1"
    if "brazil serie a" in comp or "brasileirao" in comp:
        return "bra.1"
    if re.search(r"\bserie a\b", comp):
        return None  # ambiguous (e.g. "Ecuador Serie A") — don't guess
    for key, slug in ESPN_SLUGS.items():
        if key in comp:
            return slug
    return None


# Common club nicknames a data source may use that share zero tokens with
# ESPN's own team.displayName (a plain token-overlap match can't bridge these
# on its own — e.g. "Spurs" vs "Tottenham Hotspur" overlap on nothing). Found
# live: a real Brentford vs Spurs fixture failed to match ESPN's event at all
# without this, which would have silently broken both crest lookup AND
# post-match grading for that fixture, not just a cosmetic miss. Deliberately
# excludes ambiguous nicknames shared by more than one club (Reds, Blues).
_NICKNAME_EXPANSIONS: dict[str, str] = {
    "spurs": "tottenham hotspur",
    "wolves": "wolverhampton wanderers",
    "canaries": "norwich city",
    "hammers": "west ham united",
    "toffees": "everton",
    "saints": "southampton",
    "cherries": "bournemouth",
    "seagulls": "brighton hove albion",
    "magpies": "newcastle united",
    "foxes": "leicester city",
    "gunners": "arsenal",
    "citizens": "manchester city",
}


def _expand_nickname(name: str) -> str:
    return _NICKNAME_EXPANSIONS.get((name or "").strip().lower(), name)


def _tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", _expand_nickname(s).lower()))


def _team_match_score(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), 1)


def fetch_final_score(slug: str, home: str, away: str, ko_dt: datetime) -> tuple[int, int] | None:
    """Look up the real final score for a fixture via ESPN. Returns (home_goals,
    away_goals) or None if no confidently-matching finished event is found —
    never guesses a score."""
    for day_offset in (0, 1, -1, 2):
        date_str = (ko_dt + timedelta(days=day_offset)).strftime("%Y%m%d")
        try:
            r = SESSION.get(
                f"{ESPN_BASE}/{slug}/scoreboard",
                params={"dates": date_str}, timeout=15,
            )
            events = r.json().get("events", [])
        except Exception:
            continue

        for ev in events:
            status = (((ev.get("status") or {}).get("type") or {}).get("name")) or ""
            if status not in _STATUS_FINAL:
                continue
            comp = (ev.get("competitions") or [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) != 2:
                continue
            h = next((c for c in competitors if c.get("homeAway") == "home"), None)
            a = next((c for c in competitors if c.get("homeAway") == "away"), None)
            if not h or not a:
                continue
            h_name = ((h.get("team") or {}).get("displayName")) or ""
            a_name = ((a.get("team") or {}).get("displayName")) or ""

            straight = _team_match_score(home, h_name) + _team_match_score(away, a_name)
            swapped = _team_match_score(home, a_name) + _team_match_score(away, h_name)
            if max(straight, swapped) < 1.2:
                continue

            if straight >= swapped:
                return int(h.get("score", 0)), int(a.get("score", 0))
            return int(a.get("score", 0)), int(h.get("score", 0))
    return None


# ── Persistence ───────────────────────────────────────────────────────────────

def load_db() -> dict:
    if not DB_PATH.exists():
        return {"updated": None, "predictions": []}
    try:
        return json.loads(DB_PATH.read_text())
    except Exception:
        return {"updated": None, "predictions": []}


def save_db(db: dict) -> None:
    db["updated"] = datetime.now(timezone.utc).isoformat()
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2))


def make_id(home: str, away: str, competition: str = "", season: str = "") -> str:
    """Deterministic id for a real fixture. Deliberately NOT based on kick-off
    time: the same real match can be discovered with or without a known ko_utc
    depending on which data source happens to supply it on a given run (e.g.
    data/predictions.json alone often has none, while merging in
    data/matches_live.json adds a real one) — keying on ko_utc made the same
    match hash differently across runs, breaking dedup and risking a duplicate
    post. Competition + season + team names is stable across runs for the
    normal case (each pair meets once at home in a league season); a cup
    replay or two-legged tie between the same two sides is the one case this
    can't disambiguate, which is an accepted limitation, not silently wrong."""
    base = re.sub(r"[^a-z0-9]+", "-", f"{competition}-{home}-{away}-{season}".lower()).strip("-")
    return base or f"pred-{datetime.now(timezone.utc).timestamp():.0f}"


def already_predicted(record_id: str) -> bool:
    db = load_db()
    return any(p.get("id") == record_id for p in db.get("predictions", []))


def add_prediction(record: dict) -> bool:
    """Insert a new prediction record. Returns False without writing if this
    fixture was already predicted (its forecast is never overwritten once saved)."""
    db = load_db()
    preds = db.setdefault("predictions", [])
    if any(p.get("id") == record["id"] for p in preds):
        return False
    preds.append(record)
    save_db(db)
    return True


# ── Grading ───────────────────────────────────────────────────────────────────

def compute_grade(pred: dict, home_goals: int, away_goals: int) -> dict:
    actual_result = "Home" if home_goals > away_goals else ("Away" if away_goals > home_goals else "Draw")
    correct_result = pred.get("predicted_result") == actual_result
    correct_score = pred.get("predicted_score") == f"{home_goals}-{away_goals}"
    points = 3 if correct_score else (1 if correct_result else 0)

    btts_actual = "Yes" if (home_goals > 0 and away_goals > 0) else "No"
    btts_correct = (pred.get("btts") == btts_actual) if pred.get("btts") else None

    over_actual = "Yes" if (home_goals + away_goals) > 2 else "No"
    over_correct = (pred.get("over_2_5") == over_actual) if pred.get("over_2_5") else None

    return {
        "actual_score": f"{home_goals}-{away_goals}",
        "actual_result": actual_result,
        "correct_result": correct_result,
        "correct_score": correct_score,
        "btts_correct": btts_correct,
        "over_2_5_correct": over_correct,
        "points": points,
        "graded_at": datetime.now(timezone.utc).isoformat(),
    }


def grade_pending(min_hours_after_kickoff: int = 3, max_age_days: int = 6) -> list[dict]:
    """Grade every ungraded prediction whose kickoff is safely in the past.
    Predictions older than max_age_days without a confirmed result stay
    ungraded rather than being guessed at indefinitely."""
    db = load_db()
    now = datetime.now(timezone.utc)
    graded: list[dict] = []

    for p in db.get("predictions", []):
        if p.get("actual_result") is not None:
            continue
        ko = p.get("ko_utc")
        if not ko:
            continue
        try:
            ko_dt = datetime.fromisoformat(ko.replace("Z", "+00:00"))
        except Exception:
            continue
        age = now - ko_dt
        if age < timedelta(hours=min_hours_after_kickoff) or age > timedelta(days=max_age_days):
            continue

        slug = resolve_espn_slug(p.get("competition", ""))
        if not slug:
            continue
        result = fetch_final_score(slug, p.get("home", ""), p.get("away", ""), ko_dt)
        if result is None:
            continue
        p.update(compute_grade(p, *result))
        graded.append(p)

    if graded:
        save_db(db)
    return graded


# ── Stats ─────────────────────────────────────────────────────────────────────

def aggregate_stats(competition: str | None = None, season: str | None = None) -> dict:
    db = load_db()
    preds = [p for p in db.get("predictions", []) if p.get("actual_result") is not None]
    if competition:
        preds = [p for p in preds if competition.lower() in (p.get("competition") or "").lower()]
    if season:
        preds = [p for p in preds if p.get("season") == season]

    total = len(preds)
    if total == 0:
        return {"total_graded": 0, "competition": competition, "season": season}

    correct_results = sum(1 for p in preds if p.get("correct_result"))
    exact_scores = sum(1 for p in preds if p.get("correct_score"))
    btts_graded = [p for p in preds if p.get("btts_correct") is not None]
    ou_graded = [p for p in preds if p.get("over_2_5_correct") is not None]

    return {
        "total_graded": total,
        "competition": competition,
        "season": season,
        "result_accuracy_pct": round(100 * correct_results / total, 1),
        "exact_score_pct": round(100 * exact_scores / total, 1),
        "btts_accuracy_pct": (
            round(100 * sum(1 for p in btts_graded if p["btts_correct"]) / len(btts_graded), 1)
            if btts_graded else None
        ),
        "over_under_accuracy_pct": (
            round(100 * sum(1 for p in ou_graded if p["over_2_5_correct"]) / len(ou_graded), 1)
            if ou_graded else None
        ),
        "average_confidence": round(sum(p.get("confidence", 0) for p in preds) / total, 1),
        "total_points": sum(p.get("points") or 0 for p in preds),
    }
