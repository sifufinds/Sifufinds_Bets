# SifuFinds AI Agent System — Master Blueprint
**Version:** 1.0 | **Brand:** SifuFinds | **Market:** Africa (19 countries)
**Focus:** iGaming affiliate marketing — betting, casino, odds, tips

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR (Master Agent)                     │
│              Schedules + coordinates all 4 sub-agents               │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
      ┌────────────┼────────────┬────────────────┐
      ▼            ▼            ▼                ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐
│  AGENT 1 │ │  AGENT 2 │ │  AGENT 3 │ │     AGENT 4      │
│ Content  │ │   SEO    │ │ Social   │ │  Community       │
│ Creator  │ │Optimizer │ │ Media    │ │  Engagement      │
│          │ │          │ │ Manager  │ │  (Promotion)     │
└──────────┘ └──────────┘ └──────────┘ └──────────────────┘
      │            │            │                │
      └────────────┴────────────┴────────────────┘
                        │
              ┌─────────▼─────────┐
              │   SHARED OUTPUTS   │
              │  - Blog posts      │
              │  - Social captions │
              │  - SEO metadata    │
              │  - Image prompts   │
              │  - Comments/DMs    │
              └───────────────────┘
```

---

## Tech Stack — What You Need

### APIs to Set Up (Once)
| Purpose | Service | Cost | Link |
|---|---|---|---|
| AI brain | Claude API (Anthropic) | Pay per token | console.anthropic.com |
| Image generation | DALL-E 3 (OpenAI) | Pay per image | platform.openai.com |
| Facebook + Instagram posting | Meta Graph API | Free | developers.facebook.com |
| Telegram posting | Telegram Bot API | Free | core.telegram.org/bots |
| Twitter/X posting | X API v2 (Basic) | $100/mo | developer.twitter.com |
| SEO data | Google Search Console API | Free | search.google.com/search-console |
| Scheduling (cron) | GitHub Actions OR n8n (self-host) | Free | n8n.io |
| Odds data | The Odds API | Already have key | the-odds-api.com |
| Football data | Footballdata.io | Already have key | footballdata.io |

### Automation Layer Options (Pick One)
- **Option A — n8n (Recommended):** Self-hosted workflow automation, visual builder, free. Connects everything without code.
- **Option B — Make (Integromat):** Cloud-based, $9/mo starter. Easiest to learn.
- **Option C — Python scripts + GitHub Actions:** Free, most control, requires basic coding.

### Brand Voice (All Agents Must Follow)
- **Tone:** Confident, street-smart, African. Like a trusted friend who knows betting.
- **Language:** English primary. Mix Pidgin/slang naturally (e.g., "Guy, this odds na madness", "Bro, SifuFinds don do the research for you").
- **No:** Gambling addiction language, misleading odds, fake testimonials.
- **Always include:** Responsible gambling disclaimer on blog posts. "18+ only. Bet responsibly."
- **CTAs always point to:** sifufinds.com

---

## Agent Schedules at a Glance

| Agent | Runs | Times Per Day |
|---|---|---|
| Content Creator | Every 8 hours | 3x |
| SEO Optimizer | Daily at 3am | 1x |
| Social Media Manager | Every 4 hours | 6x |
| Community Engagement | Every 2 hours | 12x |
| Growth Planner | Weekly Sunday 03:00 | 1x |

**Total: 23 automated runs per cycle, 24/7, no human input needed after setup.**

---

## File Index

| File | Description |
|---|---|
| [agent1_content_creator.md](agent1_content_creator.md) | Full system prompt + workflow for content creation |
| [agent2_seo.md](agent2_seo.md) | Full system prompt + workflow for SEO |
| [agent3_social_media.md](agent3_social_media.md) | Full system prompt + workflow for social media |
| [agent4_engagement.md](agent4_engagement.md) | Full system prompt + workflow for community engagement |
| [agent5_plan.md](agent5_plan.md) | Full system prompt + workflow for growth planning |
| [orchestration.md](orchestration.md) | n8n workflow setup + scheduling guide |

---

## Platforms & Growth Targets

| Platform | Goal | Strategy |
|---|---|---|
| Telegram | Drive users to channel, share tips daily | Auto-post tips, odds, promos every 4h |
| X (Twitter) | Build brand authority, viral odds posts | Live match tweets, trending hashtags |
| Facebook | Largest African audience, community | Groups, Pages, Reels, Events |
| Instagram | Visual content, younger African bettors | Infographics, Stories, Reels |

---

## Core Content Pillars (All Agents Follow)

1. **Today's Best Odds** — real data from The Odds API
2. **Bookmaker Bonuses** — welcome offers, free bets, promos
3. **Match Predictions / Tips** — AFCON, EPL, CAF CL, NPFL, KPL, PSL
4. **Casino Promotions** — slots, live casino, jackpots
5. **Country-Specific Deals** — Nigeria (Bet9ja, BetKing), Kenya (Sportpesa), South Africa (Hollywoodbets, Supabets), Ghana, Tanzania, Uganda
6. **Educational Content** — "How to bet on X", "What is accumulator", "How to withdraw winnings"
