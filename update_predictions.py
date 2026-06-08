#!/usr/bin/env python3
"""
SifuKaii Predicts — predictz.com scraper.

Primary:  Firecrawl REST API (FIRECRAWL_API_KEY env var — GitHub Actions secret)
Local:    Firecrawl CLI (stored session — no env var needed)
Fallback: Apify rag-web-browser (APIFY_API_TOKEN env var)
Cache:    Previous predictions.json (last resort)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

URLS: dict[str, str] = {
    "main":  "https://www.predictz.com/predictions/",
    "btts":  "https://www.predictz.com/predictions/today/both-teams-to-score/",
    "ou25":  "https://www.predictz.com/predictions/today/over-under-25-goals/",
    "bw":    "https://www.predictz.com/predictions/today/both-teams-to-score-and-win/",
    "score": "https://www.predictz.com/predictions/today/correct-score/",
}

OUT_PATH = Path(__file__).parent / "data" / "predictions.json"

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

MATCH_LINK = re.compile(
    r"\[(.+?)\s+v\s+(.+?)\]\(https://www\.predictz\.com/predictions/(.+?)/(\d+)/",
    re.I,
)
MATCH_PREVIEW = re.compile(
    r"\[MATCH PREVIEW\]\(https://www\.predictz\.com/predictions/[^)]+/(\d+)/",
    re.I,
)
COMP_HEAD  = re.compile(r"^##\s*\[([^\]]+?)\s*Tips\]", re.I)
PRED_MAIN  = re.compile(r"^(Home|Away|Draw)\s+(\d+[-:]\d+(?:\s*\(\w+\))?)", re.I)
BTTS_PRED  = re.compile(r"^BTTS (Yes|No)$", re.I)
OU_PRED    = re.compile(r"^(Over|Under) 2\.5$", re.I)
BW_PRED    = re.compile(r"^(BTTS And Win|Did Not Win)", re.I)
SCORE_PRED = re.compile(r"^(\d+-\d+) Correct Score Odds$", re.I)
FANDUEL    = re.compile(r"^\[(\d+\.\d+)\]\(https://www\.predictz\.com/fanduel/", re.I)

# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------

def _scrape_firecrawl_rest(url: str, api_key: str) -> str:
    payload = json.dumps({
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,
    }).encode()
    req = urllib.request.Request(
        "https://api.firecrawl.dev/v1/scrape",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
    if not result.get("success"):
        raise RuntimeError(f"Firecrawl API error: {result}")
    return result.get("data", {}).get("markdown", "")


def _scrape_firecrawl_cli(url: str) -> str:
    candidates = [
        "firecrawl",
        os.path.expanduser("~/.nvm/versions/node/v24.15.0/bin/firecrawl"),
        os.path.expanduser("~/.nvm/versions/node/v22.0.0/bin/firecrawl"),
    ]
    bin_path = next(
        (c for c in candidates
         if os.path.isfile(c) or subprocess.run(
             ["which", c], capture_output=True
         ).returncode == 0),
        None,
    )
    if not bin_path:
        raise RuntimeError("firecrawl CLI not found")

    r = subprocess.run(
        [bin_path, "scrape", url, "--only-main-content"],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        raise RuntimeError(f"firecrawl CLI ({r.returncode}): {r.stderr[:200]}")
    return r.stdout


def _scrape_apify(url: str, token: str) -> str:
    payload = json.dumps({"query": url, "maxResults": 1}).encode()
    req = urllib.request.Request(
        f"https://api.apify.com/v2/acts/apify~rag-web-browser/runs?token={token}&waitSecs=90",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        run = json.loads(resp.read())

    dataset_id = (
        run.get("data", {}).get("defaultDatasetId")
        or run.get("defaultDatasetId")
    )
    if not dataset_id:
        raise RuntimeError(f"Apify: no dataset ID: {run}")

    items_url = (
        f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        f"?token={token}&clean=true"
    )
    with urllib.request.urlopen(items_url, timeout=30) as resp:
        items = json.loads(resp.read())

    if not items:
        raise RuntimeError("Apify: empty dataset")
    return items[0].get("markdown") or items[0].get("text") or ""


def scrape(url: str) -> str:
    """Try Firecrawl REST → CLI → Apify, in that order."""
    api_key    = os.environ.get("FIRECRAWL_API_KEY", "").strip()
    apify_tok  = os.environ.get("APIFY_API_TOKEN", "").strip()
    errors: list[str] = []

    if api_key:
        try:
            return _scrape_firecrawl_rest(url, api_key)
        except Exception as e:
            errors.append(f"firecrawl-rest: {e}")
            print(f"  [warn] firecrawl REST: {e}", file=sys.stderr)

    try:
        return _scrape_firecrawl_cli(url)
    except Exception as e:
        errors.append(f"firecrawl-cli: {e}")
        print(f"  [warn] firecrawl CLI: {e}", file=sys.stderr)

    if apify_tok:
        try:
            return _scrape_apify(url, apify_tok)
        except Exception as e:
            errors.append(f"apify: {e}")
            print(f"  [warn] apify: {e}", file=sys.stderr)

    raise RuntimeError(f"All scrapers failed for {url}: {'; '.join(errors)}")

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _lines(text: str) -> list[str]:
    return [l.strip() for l in text.splitlines()]


def _pred_map_before_preview(
    lines: list[str],
    pred_re: re.Pattern,
) -> dict[str, str]:
    """
    For pages where the prediction label appears before [MATCH PREVIEW].
    Scans back from each MATCH PREVIEW anchor to find the prediction.
    Returns {match_id: prediction_text}.
    """
    result: dict[str, str] = {}
    for i, line in enumerate(lines):
        mp_m = MATCH_PREVIEW.search(line)
        if not mp_m:
            continue
        match_id = mp_m.group(1)
        for j in range(i - 1, max(i - 20, -1), -1):
            prev = lines[j]
            if not prev:
                continue
            if COMP_HEAD.match(prev):
                break
            if pred_re.match(prev):
                result[match_id] = prev
                break
    return result

# ---------------------------------------------------------------------------
# Page parsers
# ---------------------------------------------------------------------------

def parse_main(text: str) -> dict[str, dict]:
    lines = _lines(text)
    pred_map = _pred_map_before_preview(lines, PRED_MAIN)

    results: dict[str, dict] = {}
    current_comp = ""

    for i, line in enumerate(lines):
        comp_m = COMP_HEAD.match(line)
        if comp_m:
            current_comp = comp_m.group(1).strip()
            continue

        ml = MATCH_LINK.match(line)
        if not ml:
            continue
        home, away, comp_slug, match_id = ml.groups()

        pred_raw = pred_map.get(match_id, "")
        pred_m = PRED_MAIN.match(pred_raw)
        outcome = score = wdw = ""
        if pred_m:
            side  = pred_m.group(1).capitalize()
            score = pred_m.group(2).strip()
            outcome = side
            wdw = {"home": "1", "away": "2", "draw": "X"}.get(side.lower(), "")

        # Forward scan for home / draw / away odds (FanDuel links)
        found: list[str] = []
        for j in range(i + 1, min(i + 40, len(lines))):
            fm = FANDUEL.match(lines[j])
            if fm:
                found.append(fm.group(1))
                if len(found) == 3:
                    break
            nxt = lines[j]
            if nxt and (
                MATCH_LINK.match(nxt)
                or MATCH_PREVIEW.search(nxt)
                or COMP_HEAD.match(nxt)
            ):
                break
        home_odds, draw_odds, away_odds = (found + ["", "", ""])[:3]

        results[match_id] = {
            "id":                match_id,
            "home":              home.strip(),
            "away":              away.strip(),
            "competition":       current_comp,
            "comp_slug":         comp_slug.strip("/"),
            "ko_display":        "Today",
            "ko_utc":            None,
            "match_winner":      outcome,
            "match_winner_label": f"{outcome} {score}".strip(),
            "wdw":               wdw,
            "home_odds":         home_odds,
            "draw_odds":         draw_odds,
            "away_odds":         away_odds,
            "btts":              "",
            "btts_win":          "",
            "over25":            "",
            "correct_score":     "",
            "source":            "predictz.com",
            "scraped_at":        datetime.now(timezone.utc).isoformat(),
        }

    return results


def parse_btts(text: str) -> dict[str, str]:
    lines = _lines(text)
    pred_map = _pred_map_before_preview(lines, BTTS_PRED)
    out: dict[str, str] = {}
    for line in lines:
        ml = MATCH_LINK.match(line)
        if not ml:
            continue
        match_id = ml.group(4)
        raw = pred_map.get(match_id, "")
        m = BTTS_PRED.match(raw)
        if m:
            out[match_id] = f"BTTS {m.group(1)}"
    return out


def parse_ou(text: str) -> dict[str, str]:
    lines = _lines(text)
    pred_map = _pred_map_before_preview(lines, OU_PRED)
    out: dict[str, str] = {}
    for line in lines:
        ml = MATCH_LINK.match(line)
        if not ml:
            continue
        match_id = ml.group(4)
        raw = pred_map.get(match_id, "")
        m = OU_PRED.match(raw)
        if m:
            out[match_id] = f"{m.group(1)} 2.5"
    return out


def parse_btts_win(text: str) -> dict[str, str]:
    lines = _lines(text)
    pred_map = _pred_map_before_preview(lines, BW_PRED)
    out: dict[str, str] = {}
    for line in lines:
        ml = MATCH_LINK.match(line)
        if not ml:
            continue
        match_id = ml.group(4)
        raw = pred_map.get(match_id, "")
        if raw:
            out[match_id] = raw
    return out


def parse_score(text: str) -> dict[str, str]:
    """Correct score appears AFTER [Team1 v Team2] on the correct score page."""
    lines = _lines(text)
    out: dict[str, str] = {}
    for i, line in enumerate(lines):
        ml = MATCH_LINK.match(line)
        if not ml:
            continue
        match_id = ml.group(4)
        for j in range(i + 1, min(i + 30, len(lines))):
            if not lines[j]:
                continue
            sm = SCORE_PRED.match(lines[j])
            if sm:
                out[match_id] = sm.group(1)
                break
            if (
                MATCH_LINK.match(lines[j])
                or MATCH_PREVIEW.search(lines[j])
                or COMP_HEAD.match(lines[j])
            ):
                break
    return out

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def load_cache() -> list[dict]:
    try:
        data = json.loads(OUT_PATH.read_text())
        return data.get("predictions", [])
    except Exception:
        return []

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    now_str = datetime.now(timezone.utc).isoformat()
    log: list[dict[str, Any]] = []

    raw: dict[str, str] = {}
    for page, url in URLS.items():
        try:
            print(f"[scraping] {page} …", file=sys.stderr)
            raw[page] = scrape(url)
            log.append({"page": page, "status": "ok", "ts": now_str})
            print(f"  [ok] {page} — {len(raw[page])} chars", file=sys.stderr)
        except Exception as exc:
            log.append({"page": page, "status": "error", "error": str(exc)[:200], "ts": now_str})
            print(f"  [fail] {page}: {exc}", file=sys.stderr)

    if "main" not in raw:
        print("[fallback] main scrape failed — using cache", file=sys.stderr)
        cache = load_cache()
        OUT_PATH.write_text(json.dumps({
            "updated":    now_str,
            "source":     "predictz.com (cache)",
            "count":      len(cache),
            "scrape_log": log,
            "predictions": cache,
        }, ensure_ascii=False, indent=2))
        return

    # Parse main page → base match records
    matches = parse_main(raw["main"])
    print(f"[parse] main → {len(matches)} matches", file=sys.stderr)

    # Enrich from specialty pages
    for page_key, parser_fn, field in [
        ("btts",  parse_btts,     "btts"),
        ("ou25",  parse_ou,       "over25"),
        ("bw",    parse_btts_win, "btts_win"),
        ("score", parse_score,    "correct_score"),
    ]:
        if page_key not in raw:
            continue
        n = 0
        for mid, val in parser_fn(raw[page_key]).items():
            if mid in matches:
                matches[mid][field] = val
                n += 1
        print(f"[parse] {page_key} → {n} enriched", file=sys.stderr)

    predictions = sorted(
        matches.values(),
        key=lambda p: (p.get("ko_utc") or "zzz", p["home"]),
    )

    OUT_PATH.write_text(json.dumps({
        "updated":     now_str,
        "source":      "predictz.com",
        "count":       len(predictions),
        "scrape_log":  log,
        "predictions": predictions,
    }, ensure_ascii=False, indent=2))

    print(f"[done] {len(predictions)} predictions written to {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
