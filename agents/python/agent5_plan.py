"""
Agent 5 — Growth Planner
Generates a weekly editorial and social campaign plan from recent content, SEO signals, and queue state.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from llm import ask
from config import SITE_URL, BRAND_NAME, CONTENT_SLOTS, COUNTRIES
from utils.logger import log

SYSTEM_PROMPT = """You are the Growth Planner and Editorial Strategist for SifuFinds (sifufinds.com), Africa's #1 betting comparison website.

Your job is to create a high-impact weekly plan that turns recent content, SEO signals, and community engagement into a clear editorial calendar, social campaign schedule, and keyword growth plan.

Focus on African sports bettors across Nigeria, Kenya, South Africa, Ghana, Tanzania, Uganda, Zambia, Zimbabwe, Cameroon, Senegal, Ivory Coast and other key markets.

Return ONLY valid JSON in this exact format:
{
  "weekly_editorial_calendar": [
    {
      "day": "Sunday",
      "publish_time": "06:00 WAT",
      "content_pillar": "Match Prediction and Tips",
      "topic": "...",
      "country_focus": "...",
      "primary_keyword": "...",
      "format": "..."
    }
  ],
  "weekly_social_campaigns": [
    {
      "campaign_name": "...",
      "focus": "...",
      "platform_priority": ["Telegram", "X", "Facebook", "Instagram"],
      "call_to_action": "..."
    }
  ],
  "keyword_gap_opportunities": [
    {
      "keyword": "...",
      "intent": "...",
      "content_idea": "..."
    }
  ],
  "platform_priorities": {
    "Telegram": "...",
    "X": "...",
    "Facebook": "...",
    "Instagram": "..."
  },
  "growth_actions": ["..."],
  "planning_notes": ["..."]
}
"""

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "weekly_plan.json")


def load_json(file_name):
    path = os.path.join(os.path.dirname(__file__), file_name)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def _top_gap_keywords(data: dict, limit: int = 10) -> list[str]:
    """Most recently researched evergreen keywords SifuFinds doesn't yet
    rank for, from agent_keyword_research.py's persisted backlog."""
    opportunities = data.get("opportunities", {})
    gaps = [
        (k, v.get("checked_at", ""))
        for k, v in opportunities.items()
        if not v.get("sifufinds_ranks")
    ]
    gaps.sort(key=lambda pair: pair[1], reverse=True)
    return [k for k, _ in gaps[:limit]]


def _top_trending(data: dict, limit: int = 10) -> list[dict]:
    """Most recently checked trending keyword pairings from
    agent_trending_keywords.py's news-driven backlog."""
    trending = data.get("trending", {})
    items = sorted(trending.values(), key=lambda e: e.get("checked_at", ""), reverse=True)
    return items[:limit]


def clean_response(raw_text):
    text = raw_text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
    if text.lower().startswith("json"):
        idx = text.find("{")
        if idx != -1:
            text = text[idx:]
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return text.strip()


def run():
    log("agent5", "start", "running")

    latest_blog = load_json("latest_blog.json")
    latest_seo = load_json("latest_seo.json")
    content_queue = load_json("content_queue.json")
    engagement_queue = load_json("engagement_queue.json")
    keyword_opportunities = load_json("keyword_opportunities.json")
    trending_keywords = load_json("trending_keywords.json")

    gap_keywords = _top_gap_keywords(keyword_opportunities)
    trending_items = _top_trending(trending_keywords)
    gap_block = "\n".join(f"- {k}" for k in gap_keywords) or "None researched yet"
    trending_block = "\n".join(
        f"- \"{t['primary_keyword']}\" ({t['country']}, from: {t['source_headline'][:70]})"
        for t in trending_items
    ) or "None researched yet"

    top_countries = ", ".join([country["name"] for country in COUNTRIES])
    queue_summary = {
        "blog_items": len(content_queue.get("blog", [])) if isinstance(content_queue, dict) else 0,
        "social_items": len(content_queue.get("social", [])) if isinstance(content_queue, dict) else 0,
        "engagement_topics": len(engagement_queue.get("topics", [])) if isinstance(engagement_queue, dict) else 0,
    }

    user_message = f"""Create a weekly Growth Plan for SifuFinds.

Site: {SITE_URL}
Brand: {BRAND_NAME}
Top countries: {top_countries}
Content rotation slots: {', '.join(CONTENT_SLOTS)}

Latest blog summary:
Title: {latest_blog.get('blog', {}).get('title', 'N/A')}
Slug: {latest_blog.get('blog', {}).get('slug', 'N/A')}
Content pillar: {latest_blog.get('metadata', {}).get('content_pillar', 'N/A')}
Primary keyword: {latest_seo.get('primary_keyword', 'N/A')}
SEO score: {latest_seo.get('seo_score', 'N/A')}

Queue summary:
Blog items queued: {queue_summary['blog_items']}
Social items queued: {queue_summary['social_items']}
Engagement topics: {queue_summary['engagement_topics']}

Real keyword research (agent_keyword_research.py) — evergreen money keywords SifuFinds does NOT yet rank for:
{gap_block}

Real trending keyword research (agent_trending_keywords.py) — current news-driven keyword opportunities across our 28 African markets:
{trending_block}

Use the recent content, SEO signals, and community priorities to propose:
- a 7-day editorial calendar — base topics and primary_keyword fields on the real keyword research above wherever relevant, rather than inventing keywords from scratch
- 3 social campaigns for the upcoming week
- 5 keyword gap opportunities — draw these from the real backlog above, don't just repeat generic ideas
- platform priorities for Telegram, X, Facebook, and Instagram
- 3 growth actions and planning notes

Return only valid JSON, nothing else."""

    try:
        raw = ask(SYSTEM_PROMPT, user_message)
        cleaned = clean_response(raw)
        plan = json.loads(cleaned)

        with open(OUTPUT_PATH, "w") as f:
            json.dump(plan, f, indent=2)

        log("agent5", "plan_generated", "success", plan.get("weekly_editorial_calendar", [{}])[0].get("topic", ""))
        print("✓ Weekly Growth Plan generated and saved to weekly_plan.json")

        if plan.get("growth_actions"):
            print(f"Growth actions: {len(plan['growth_actions'])}")
        if plan.get("keyword_gap_opportunities"):
            print(f"Keyword opportunities: {len(plan['keyword_gap_opportunities'])}")

    except json.JSONDecodeError as e:
        log("agent5", "parse_error", "failed", str(e))
        print(f"✗ JSON parse error: {e}")
        sys.exit(1)
    except Exception as e:
        log("agent5", "error", "failed", str(e))
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
