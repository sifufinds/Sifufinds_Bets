"""
Agent 2 — SEO Optimizer
Reads the latest blog from Agent 1, returns SEO improvements + schema markup.
Called by GitHub Actions daily at 03:00 UTC.
"""
import json
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from llm import ask
from config import SITE_URL
from utils.logger import log

SYSTEM_PROMPT = """You are the SEO Optimizer for SifuFinds (sifufinds.com), Africa's #1 betting comparison site targeting 19 African countries.

Your job: analyse each new blog post and return an optimised SEO package.

TARGET KEYWORDS by country:
- Nigeria: "best betting sites in Nigeria", "Bet9ja bonus", "betting tips Nigeria today", "NPFL predictions"
- Kenya: "best betting sites in Kenya", "Sportpesa bonus", "KPL predictions", "free bets Kenya"
- South Africa: "best betting sites South Africa", "Hollywoodbets promo", "PSL predictions", "sports betting SA"
- Ghana: "best betting sites in Ghana", "betting tips Ghana"
- Pan-Africa: "African betting sites", "AFCON predictions", "CAF Champions League tips", "best odds Africa"

SEO RULES:
- Title: 50-60 chars, primary keyword near front
- Meta: 150-160 chars, include keyword + "Compare at SifuFinds"
- Minimum 3 internal links per post
- Each post needs Article schema + FAQPage schema (with 3 relevant Q&As)
- hreflang tag for the target country

Return ONLY valid JSON in this exact format:

{
  "title_tag": "optimised title tag 50-60 chars",
  "meta_description": "optimised meta 150-160 chars with keyword",
  "h1": "optimised H1 with primary keyword",
  "recommended_h2s": ["H2 one", "H2 two", "H2 three", "H2 four"],
  "primary_keyword": "exact keyword",
  "keyword_density_note": "brief note on keyword placement",
  "internal_links": [
    {"anchor": "anchor text", "href": "/page/"},
    {"anchor": "anchor text 2", "href": "/page2/"},
    {"anchor": "anchor text 3", "href": "/page3/"}
  ],
  "article_schema": {},
  "faq_schema": {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {"@type": "Question", "name": "question 1?", "acceptedAnswer": {"@type": "Answer", "text": "answer 1"}},
      {"@type": "Question", "name": "question 2?", "acceptedAnswer": {"@type": "Answer", "text": "answer 2"}},
      {"@type": "Question", "name": "question 3?", "acceptedAnswer": {"@type": "Answer", "text": "answer 3"}}
    ]
  },
  "hreflang_tag": "<link rel='alternate' hreflang='en-XX' href='https://sifufinds.com/...' />",
  "seo_score": 85,
  "issues": ["any problems found"],
  "new_keyword_opportunities": [
    {"keyword": "keyword", "intent": "transactional", "content_idea": "brief idea"}
  ]
}"""


def run():
    log("agent2", "start", "running")

    blog_path = os.path.join(os.path.dirname(__file__), "latest_blog.json")
    if not os.path.exists(blog_path):
        log("agent2", "no_content", "skipped", "latest_blog.json not found")
        print("No blog content to optimise yet — Agent 1 must run first.")
        return

    with open(blog_path) as f:
        content = json.load(f)

    blog = content.get("blog", {})
    meta = content.get("metadata", {})
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    user_message = f"""Optimise this blog post for SEO:

Title: {blog.get('title')}
Slug: {blog.get('slug')}
H1: {blog.get('h1')}
Primary keyword: {blog.get('primary_keyword')}
Secondary keywords: {', '.join(blog.get('secondary_keywords', []))}
Target country: {meta.get('target_country')}
Content pillar: {meta.get('content_pillar')}
Date published: {today}
Site URL: {SITE_URL}

Blog body (first 500 chars):
{blog.get('body', '')[:500]}

Generate the full SEO package. Return only valid JSON, nothing else."""

    try:
        raw = ask(SYSTEM_PROMPT, user_message)

        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        seo = json.loads(raw)

        # Add Article schema with today's date
        seo["article_schema"] = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": seo.get("h1", blog.get("h1")),
            "datePublished": today,
            "dateModified": today,
            "author": {"@type": "Organization", "name": "SifuFinds"},
            "publisher": {
                "@type": "Organization",
                "name": "SifuFinds",
                "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/assets/logo.png"},
            },
        }

        output_path = os.path.join(os.path.dirname(__file__), "latest_seo.json")
        with open(output_path, "w") as f:
            json.dump(seo, f, indent=2)

        log("agent2", "seo_generated", "success", seo.get("primary_keyword", ""))
        print(f"✓ SEO score: {seo.get('seo_score')}/100")
        print(f"✓ Primary keyword: {seo.get('primary_keyword')}")
        print(f"✓ Keyword opportunities found: {len(seo.get('new_keyword_opportunities', []))}")

        if seo.get("issues"):
            print(f"⚠ Issues: {', '.join(seo['issues'])}")

    except json.JSONDecodeError as e:
        log("agent2", "parse_error", "failed", str(e))
        print(f"✗ JSON parse error: {e}")
        sys.exit(1)
    except Exception as e:
        log("agent2", "error", "failed", str(e))
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
