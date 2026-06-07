"""
Agent 1 — Content Creator
Generates a blog post + social captions + SEO metadata every run.
Called by GitHub Actions 2x per day.
"""
import json
import random
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from llm import ask
from config import SITE_URL, BRAND_NAME, CONTENT_SLOTS, COUNTRIES, INSTAGRAM_HASHTAGS
from utils.football_api import get_todays_matches, get_best_odds
from utils.queue_manager import push
from utils.logger import log
from utils.serp_research import research, build_keyword

SYSTEM_PROMPT = """You are the Content Creator for SifuFinds (sifufinds.com), Africa's #1 betting comparison website covering 19 African countries.

BRAND VOICE: Confident, street-smart, African. Sound like a trusted friend who knows betting — not a corporate account. Use natural African English and occasional Pidgin/slang where it fits naturally (e.g., "This odds na fire!", "My guy, SifuFinds don find the best deal for you", "Eish, this bonus is too good to miss").

RULES:
- Every piece of content must have a CTA pointing to sifufinds.com
- Every piece of content must include: 18+ | Bet Responsibly | T&Cs Apply
- Never promise guaranteed wins
- Rotate bookmakers — never just one brand
- Keywords embedded naturally, never stuffed

Return your response in EXACTLY this format with the four sections separated by the markers shown. No extra text outside these sections.

===META===
{
  "title": "SEO title 50-60 chars",
  "slug": "url-slug-format",
  "meta_description": "150-160 char meta description with keyword and CTA",
  "h1": "exact H1 text",
  "primary_keyword": "exact primary keyword",
  "secondary_keywords": ["kw1", "kw2", "kw3"],
  "content_pillar": "odds|bonus|tips|casino|education|country",
  "target_country": "country name",
  "bookmaker_featured": "bookmaker name"
}
===BLOG===
Write the full blog post here in plain markdown (800-1000 words). Include H2 headings, a bookmaker comparison section, a CTA paragraph pointing to sifufinds.com, and a responsible gambling disclaimer at the bottom. No JSON — just plain text.
===SOCIAL===
{
  "telegram": "300-500 char casual message with emoji and CTA",
  "facebook": "150-250 word post, storytelling tone, with emoji",
  "instagram": "100-150 word caption with emoji",
  "hashtags": "#tag1 #tag2 [25 tags total, space separated]"
}
===END==="""


def run():
    log("agent1", "start", "running")
    print(f"[agent1] keyword target: {build_keyword(CONTENT_SLOTS[datetime.now(timezone.utc).day % len(CONTENT_SLOTS)], 'auto')}")

    today = datetime.now(timezone.utc).strftime("%A %d %B %Y")
    slot_index = datetime.now(timezone.utc).day % len(CONTENT_SLOTS)
    topic = CONTENT_SLOTS[slot_index]
    country = random.choice(COUNTRIES)
    hashtags = " ".join(random.sample(INSTAGRAM_HASHTAGS, 25))

    matches = get_todays_matches()
    odds = get_best_odds()

    # Auto-research: Firecrawl SERP + Apify competitor analysis
    keyword = build_keyword(topic, country["name"])
    serp_block = research(keyword, country["name"])

    user_message = f"""Today is {today}.

TOPIC FOR THIS SESSION: {topic}

FEATURED COUNTRY: {country['name']} (currency: {country['currency']}, popular bookmakers: {', '.join(country['bookmakers'])}, popular payments: {country['payment']})

TODAY'S MATCHES:
{matches}

CURRENT BEST ODDS:
{odds}

INSTAGRAM HASHTAGS TO USE: {hashtags}

SITE URL: {SITE_URL}

{serp_block}
Generate the full content package now. Return only valid JSON, nothing else."""

    try:
        raw = ask(SYSTEM_PROMPT, user_message)

        # Parse the four delimited sections
        def extract(text, start_marker, end_marker):
            try:
                start = text.index(start_marker) + len(start_marker)
                end = text.index(end_marker, start)
                return text[start:end].strip()
            except ValueError:
                return ""

        meta_raw  = extract(raw, "===META===", "===BLOG===")
        blog_body = extract(raw, "===BLOG===", "===SOCIAL===")
        social_raw = extract(raw, "===SOCIAL===", "===END===")

        # Clean code fences from JSON sections
        def clean_json(s):
            s = s.strip()
            if s.startswith("```"):
                s = s.split("```")[1]
                if s.startswith("json"):
                    s = s[4:]
            return s.strip()

        meta   = json.loads(clean_json(meta_raw))
        social = json.loads(clean_json(social_raw))

        content = {
            "blog": {
                "title":             meta.get("title", ""),
                "slug":              meta.get("slug", ""),
                "meta_description":  meta.get("meta_description", ""),
                "h1":                meta.get("h1", ""),
                "primary_keyword":   meta.get("primary_keyword", ""),
                "secondary_keywords":meta.get("secondary_keywords", []),
                "body":              blog_body,
            },
            "social": social,
            "metadata": {
                "content_pillar":   meta.get("content_pillar", ""),
                "target_country":   meta.get("target_country", ""),
                "bookmaker_featured":meta.get("bookmaker_featured", ""),
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "date": today,
        }

        push(content)
        log("agent1", "content_generated", "success", content["blog"]["title"])

        output_path = os.path.join(os.path.dirname(__file__), "latest_blog.json")
        with open(output_path, "w") as f:
            json.dump(content, f, indent=2)

        print(f"✓ Blog: {content['blog']['title']}")
        print(f"✓ Country: {content['metadata']['target_country']}")
        print(f"✓ Pillar: {content['metadata']['content_pillar']}")
        print(f"✓ Blog body: {len(blog_body)} chars")

    except json.JSONDecodeError as e:
        log("agent1", "parse_error", "failed", str(e))
        print(f"✗ JSON parse error: {e}")
        sys.exit(1)
    except Exception as e:
        log("agent1", "error", "failed", str(e))
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
