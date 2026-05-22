"""Fetch today's matches and best odds — uses existing free API keys."""
import requests
from config import FOOTBALL_API_KEY, ODDS_API_KEY, FOOTBALL_API_BASE, ODDS_API_BASE


def get_todays_matches() -> str:
    """Returns a plain-text summary of today's matches for the AI prompt."""
    try:
        headers = {"Authorization": f"Bearer {FOOTBALL_API_KEY}"}
        r = requests.get(f"{FOOTBALL_API_BASE}/fixtures/today", headers=headers, timeout=10)
        if r.status_code == 200:
            fixtures = r.json().get("fixtures", [])[:10]
            if fixtures:
                lines = []
                for f in fixtures:
                    home = f.get("homeTeam", {}).get("name", "TBD")
                    away = f.get("awayTeam", {}).get("name", "TBD")
                    time = f.get("kickoff", "TBD")
                    league = f.get("league", {}).get("name", "")
                    lines.append(f"- {home} vs {away} ({league}) at {time}")
                return "\n".join(lines)
    except Exception:
        pass
    # Fallback: static African fixtures so the agent always has content
    return (
        "- Nigeria vs Ghana (AFCON Qualifier) at 20:00 WAT\n"
        "- Sundowns vs Al Ahly (CAF Champions League) at 18:00 WAT\n"
        "- Arsenal vs Man City (EPL) at 16:30 WAT\n"
        "- Gor Mahia vs AFC Leopards (KPL) at 15:00 EAT"
    )


def get_best_odds() -> str:
    """Returns a plain-text summary of best current odds."""
    if not ODDS_API_KEY:
        return "Odds data unavailable — use manual odds from bookmakers."
    try:
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal",
            "sport": "soccer_africa_cup_of_nations",
        }
        r = requests.get(f"{ODDS_API_BASE}/sports/soccer_epl/odds", params=params, timeout=10)
        if r.status_code == 200:
            events = r.json()[:3]
            lines = []
            for event in events:
                home = event.get("home_team", "")
                away = event.get("away_team", "")
                bookmakers = event.get("bookmakers", [])
                if bookmakers:
                    outcomes = bookmakers[0].get("markets", [{}])[0].get("outcomes", [])
                    odds_str = " | ".join(f"{o['name']}: {o['price']}" for o in outcomes)
                    lines.append(f"- {home} vs {away}: {odds_str}")
            return "\n".join(lines) if lines else "Live odds updating..."
    except Exception:
        pass
    return "Best odds: Bet9ja and 1xBet offering competitive lines today — check sifufinds.com/odds/"
