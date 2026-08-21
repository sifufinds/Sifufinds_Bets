"""
utils/prediction_game.py — crowd-vs-model prediction game.

Attaches a real Telegram poll (Home / Draw / Away) to a round's highest-
confidence fixture so followers can vote their own outcome, then once the
real result is known, closes the poll and compares the crowd's aggregate
vote against SifuFinds' own call and the real outcome.

Telegram channels only accept ANONYMOUS polls (confirmed live: sendPoll
returns "Bad Request: non-anonymous polls can't be sent to channel chats"
for is_anonymous=False on this channel) — so there is no way to see which
individual follower voted for what, and therefore no real per-follower
leaderboard is possible here. This module tracks the crowd's aggregate
accuracy over time instead (a real, honest metric: "the SifuFinds community
correctly called N% of match outcomes this season"), not invented per-user
scores. Purely additive: nothing here is required for agent_predictions.py's
one-way social posts to work, and every failure degrades to "no poll this
round" rather than blocking a post.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

from agent_telegram_offers import BOT_TOKEN, CHANNEL

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GAME_DB_PATH = REPO_ROOT / "data" / "prediction_game.json"
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _load() -> dict:
    if not GAME_DB_PATH.exists():
        return {"polls": {}}
    try:
        return json.loads(GAME_DB_PATH.read_text())
    except Exception:
        return {"polls": {}}


def _save(db: dict) -> None:
    GAME_DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2))


def send_prediction_poll(fixture_id: str, home: str, away: str) -> str | None:
    """Sends a real (anonymous — channels require it) Telegram poll for one
    fixture. Returns the poll's own id (used to close/grade it later) or None
    if the send failed/no bot token is configured."""
    if not BOT_TOKEN:
        return None
    options = [home, "Draw", away]
    try:
        resp = requests.post(f"{API_BASE}/sendPoll", json={
            "chat_id": CHANNEL,
            "question": f"⚽ Who wins? {home} vs {away}",
            "options": options,
            "is_anonymous": True,
        }, timeout=15)
        data = resp.json()
        if not data.get("ok"):
            print(f"✗ sendPoll failed: {data.get('description')}")
            return None
        message_id = data["result"]["message_id"]
        poll_id = data["result"]["poll"]["id"]
    except Exception as e:
        print(f"✗ sendPoll error: {e}")
        return None

    db = _load()
    db["polls"][poll_id] = {
        "fixture_id": fixture_id,
        "message_id": message_id,
        "home": home,
        "away": away,
        "options": options,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "graded": False,
    }
    _save(db)
    return poll_id


def close_and_grade_poll(fixture_id: str, actual_result: str, predicted_result: str) -> dict | None:
    """Closes this fixture's poll (via stopPoll, which returns the final
    aggregate vote counts — the only vote data a channel poll ever exposes)
    and compares the crowd's top pick against the real result and SifuFinds'
    own call. Returns None if there was no poll for this fixture, it's
    already graded, or no bot token is configured — always safe to call once
    per graded prediction without double-counting."""
    if not BOT_TOKEN:
        return None
    db = _load()
    poll_id, poll = next(
        ((pid, p) for pid, p in db["polls"].items()
         if p["fixture_id"] == fixture_id and not p.get("graded")),
        (None, None),
    )
    if poll is None:
        return None

    try:
        resp = requests.post(f"{API_BASE}/stopPoll", json={
            "chat_id": CHANNEL, "message_id": poll["message_id"],
        }, timeout=15)
        data = resp.json()
        if not data.get("ok"):
            print(f"✗ stopPoll failed: {data.get('description')}")
            return None
        options = data["result"]["options"]  # [{"text": ..., "voter_count": ...}, ...]
    except Exception as e:
        print(f"✗ stopPoll error: {e}")
        return None

    total_votes = sum(o["voter_count"] for o in options)
    result_labels = ["Home", "Draw", "Away"]
    crowd_pick = None
    if total_votes > 0:
        top_idx = max(range(len(options)), key=lambda i: options[i]["voter_count"])
        crowd_pick = result_labels[top_idx]

    crowd_correct = crowd_pick == actual_result if crowd_pick else None
    model_correct = predicted_result == actual_result

    poll["graded"] = True
    poll["total_votes"] = total_votes
    poll["crowd_pick"] = crowd_pick
    poll["crowd_correct"] = crowd_correct
    poll["model_correct"] = model_correct
    poll["actual_result"] = actual_result

    tally = db.setdefault("season_tally", {"crowd_correct": 0, "crowd_total": 0, "model_correct": 0, "model_total": 0})
    tally["model_total"] += 1
    tally["model_correct"] += int(model_correct)
    if crowd_pick is not None:
        tally["crowd_total"] += 1
        tally["crowd_correct"] += int(crowd_correct)

    _save(db)
    return {
        "poll_id": poll_id, "total_votes": total_votes, "crowd_pick": crowd_pick,
        "crowd_correct": crowd_correct, "model_correct": model_correct,
    }


def season_tally() -> dict:
    db = _load()
    return db.get("season_tally", {"crowd_correct": 0, "crowd_total": 0, "model_correct": 0, "model_total": 0})
