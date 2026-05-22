# Orchestration Blueprint — How All 5 Agents Run 24/7
**Tool: n8n (Recommended) | Alternative: Make (Integromat) | Advanced: Python + cron**

---

## Master 24-Hour Schedule

```
TIME (WAT) │ AGENT 1          │ AGENT 2        │ AGENT 3          │ AGENT 4
───────────┼──────────────────┼────────────────┼──────────────────┼──────────────────
00:00      │                  │                │ PUBLISH (night)  │ ENGAGE
02:00      │                  │                │                  │ ENGAGE
03:00      │                  │ SEO AUDIT      │                  │
04:00      │                  │                │ PUBLISH (early)  │ ENGAGE
06:00      │ GENERATE (AM)    │                │                  │ ENGAGE
08:00      │                  │                │ PUBLISH (AM)     │ ENGAGE
10:00      │                  │                │                  │ ENGAGE
12:00      │                  │                │ PUBLISH (noon)   │ ENGAGE
14:00      │ GENERATE (PM)    │                │                  │ ENGAGE
16:00      │                  │                │ PUBLISH (arvo)   │ ENGAGE
18:00      │                  │                │                  │ ENGAGE (+ DMs)
20:00      │                  │                │ PUBLISH (evening)│ ENGAGE
22:00      │ GENERATE (night) │                │                  │ ENGAGE
```

**Total agent invocations per day: 3 + 1 + 6 + 12 = 22 runs plus 1 weekly Growth Planner run (23 total cycle runs)**

---

## Setup Guide: n8n (Recommended — Free, Self-Hosted)

### Option 1: n8n Cloud (Easiest)
1. Sign up at n8n.io/cloud (~$20/mo starter)
2. No server needed — runs in their cloud
3. Import the workflow JSON below

### Option 2: n8n Self-Hosted (Free)
```bash
# Install n8n on your Mac/VPS
npm install n8n -g
n8n start

# Or via Docker (most stable for 24/7):
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n
```
Access at: http://localhost:5678

### Option 3: Make.com (Easiest for beginners)
- Sign up at make.com (free tier: 1000 ops/month)
- Use HTTP Request modules to call Claude API
- Drag-and-drop visual workflow builder

---

## n8n Workflow Structure

### Workflow 1: Agent 1 — Content Creator (Runs 3x/day)
```
[Cron Trigger: 06:00, 14:00, 22:00]
    ↓
[HTTP: GET /fixtures/today from footballdata.io]
    ↓
[HTTP: GET today's odds from The Odds API]
    ↓
[Function: Calculate rotation slot (AM/PM/Night) + day number]
    ↓
[HTTP: POST to Claude API with system prompt + live data injected]
    ↓
[Function: Parse Claude response → split into sections]
    ↓
[HTTP: POST image prompt to DALL-E 3 → get image URL]
    ↓
[Write: Save blog post to /blog/ folder as HTML file]
    ↓
[Write: Save social captions to queue file (JSON)]
    ↓
[Trigger: Webhook → Start Agent 2 (SEO)]
```

### Workflow 2: Agent 2 — SEO Optimizer (Triggered by Agent 1 + Daily 03:00)
```
[Webhook Trigger (from Agent 1) OR Cron Trigger: 03:00]
    ↓
[Read: Get new blog post content from queue]
    ↓
[HTTP: POST to Claude API with SEO system prompt + page content]
    ↓
[Function: Parse SEO report — extract title, meta, schema, links]
    ↓
[Write: Update HTML file — insert title tag, meta, schema JSON-LD]
    ↓
[Write: Log SEO report to seo_log.json]
    ↓
[IF: Day = Sunday → Generate keyword list for Agent 1's next week]
    ↓
[Write: Update Agent 1's content calendar queue]
```

### Workflow 3: Agent 3 — Social Media Manager (Runs every 4 hours)
```
[Cron Trigger: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00]
    ↓
[Read: Load next item from social media queue (from Agent 1)]
    ↓
[IF: Queue empty → Generate fallback content from evergreen backlog]
    ↓
[HTTP: POST to Claude API with Social Media system prompt]
    ↓
[Function: Parse response → split into 4 platform posts]
    ↓
[Parallel execution:]
    ├─ [HTTP: POST to Telegram Bot API → sendMessage]
    ├─ [HTTP: POST to X API v2 → create tweet]
    ├─ [HTTP: Upload image to Facebook → POST to Page feed]
    └─ [HTTP: Upload image to Instagram → Create + Publish media]
    ↓
[Write: Log to posting_log.json with timestamps]
    ↓
[IF: Error on any platform → Retry after 5 minutes → Log failure]
```

### Workflow 4: Agent 4 — Community Engagement (Runs every 2 hours)
```
[Cron Trigger: every 2 hours]
    ↓
[Function: Determine platform priority for this time slot]
    ↓
[HTTP: Fetch recent posts from target accounts via platform APIs]
    ↓
[Read: Load engagement_log.json to avoid duplicate comments]
    ↓
[HTTP: POST to Claude API with Engagement system prompt + recent posts]
    ↓
[Function: Parse comment queue]
    ↓
[Loop: For each comment in queue:]
    ├─ [IF platform = X → POST reply via X API]
    ├─ [IF platform = Facebook → POST comment via Graph API]
    ├─ [IF platform = Instagram → POST comment via Graph API]
    └─ [IF platform = Telegram → POST message via Bot API]
    ↓
[Write: Log all actions to engagement_log.json]
    ↓
[IF: Time = 18:00 → Run DM workflow]
```

---

### Workflow 5: Agent 5 — Growth Planner (Runs once weekly)
```
[Cron Trigger: Sunday 03:00 WAT]
    ↓
[Read: latest_blog.json, latest_seo.json, content_queue.json, engagement_queue.json]
    ↓
[HTTP: POST to Claude API with Growth Planner system prompt]
    ↓
[Parse: Weekly editorial calendar + campaign plan + keyword gap list]
    ↓
[Write: Save weekly_plan.json]
    ↓
[Write: Update Agent 1 / Agent 3 input queues if a new content calendar is suggested]
```

This weekly planning agent ensures the other agents stay aligned on high-value topics, keyword opportunities, and campaign timing.

---

## Environment Variables (Store in n8n Credentials)
```
CLAUDE_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHANNEL_ID=@YourChannel
FACEBOOK_PAGE_ID=...
FACEBOOK_PAGE_ACCESS_TOKEN=...
INSTAGRAM_BUSINESS_ACCOUNT_ID=...
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_TOKEN_SECRET=...
ODDS_API_KEY=...
FOOTBALL_API_KEY=fd_554baa8cfac7cfe33ba92edfbc00f3e2a179ba179f44ada9
```

---

## Claude API Call Template (Use in all n8n HTTP nodes)

```json
POST https://api.anthropic.com/v1/messages
Headers:
  x-api-key: {{$env.CLAUDE_API_KEY}}
  anthropic-version: 2023-06-01
  content-type: application/json

Body:
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 4096,
  "system": "{{PASTE AGENT SYSTEM PROMPT HERE}}",
  "messages": [
    {
      "role": "user",
      "content": "Run your workflow now. Here is today's data:\n\nDate: {{$now.format('DD MMMM YYYY')}}\nMatches today: {{$json.matches}}\nBest odds: {{$json.odds}}\nContent slot: {{$json.slot}}\nRotation day: {{$json.day}}"
    }
  ]
}
```

---

## Error Handling & Resilience

### If Claude API is Down
- n8n retries automatically (configure: max 3 retries, 5-minute delay)
- If all retries fail: Pull from evergreen content backlog
- Send error notification to your email/Telegram

### If a Social Media API Fails
- Log the failed post to `failed_queue.json`
- Retry at next scheduled slot
- Never skip a post — it goes back to the queue

### Backlog System (For Gaps + API Failures)
Agent 1 generates 3 posts per day. Keep a rolling backlog of 21 posts (7 days).
- If a slot has no fresh content → pull from backlog
- Backlog is stored as `content_backlog.json` in the `/agents/` folder

### Rate Limits to Watch
| Platform | Rate Limit | n8n Solution |
|---|---|---|
| X API (Basic) | 1500 tweets/month | Track monthly count; pause at 1400 |
| Facebook Graph | 200 calls/hour/user | Well within limits |
| Instagram Graph | 200 calls/hour | Well within limits |
| Telegram | 30 messages/second | No issue |
| Claude API | Based on plan | claude-sonnet-4-6 handles volume |
| DALL-E 3 | Tier-based | 3 images/day = very safe |

---

## One-Time Setup Checklist

### Step 1: APIs & Credentials (2-3 hours)
- [ ] Create Anthropic account → Get Claude API key → console.anthropic.com
- [ ] Create OpenAI account → Get API key (for DALL-E 3) → platform.openai.com
- [ ] Create Facebook App → Get Page Access Token → developers.facebook.com
- [ ] Connect Instagram Business Account to Facebook App
- [ ] Create Telegram Bot → Get token via @BotFather → Add bot as admin to your channel
- [ ] Apply for X Developer account → Get API keys (Basic plan: $100/mo)

### Step 2: Install n8n (30 minutes)
- [ ] Install Docker Desktop on your Mac
- [ ] Run the n8n Docker command above
- [ ] Open http://localhost:5678
- [ ] Add all credentials under Settings > Credentials

### Step 3: Create Workflows in n8n (2-4 hours)
- [ ] Create Workflow 1 (Agent 1 — Content Creator)
- [ ] Create Workflow 2 (Agent 2 — SEO)
- [ ] Create Workflow 3 (Agent 3 — Social Media)
- [ ] Create Workflow 4 (Agent 4 — Engagement)
- [ ] Test each workflow manually before activating

### Step 4: Join Communities (1 hour, one-time)
- [ ] Join 10-15 African betting Facebook Groups
- [ ] Note group IDs and add to n8n config
- [ ] Join relevant Telegram groups
- [ ] Find target Reddit/Quora threads

### Step 5: Activate & Monitor (Day 1)
- [ ] Activate all 4 workflows in n8n
- [ ] Watch first 24 hours manually
- [ ] Check logs in n8n Executions tab
- [ ] Verify posts appear on all platforms
- [ ] After 24h: Leave it to run

---

## Cost Estimate (Monthly)

| Service | Plan | Cost/month |
|---|---|---|
| Claude API (Sonnet) | ~22 calls/day × 30 = 660 calls | ~$15-25 |
| DALL-E 3 | 3 images/day × 30 = 90 images | ~$4 |
| X API | Basic plan | $100 |
| n8n | Self-hosted (Docker) | Free |
| Server for n8n (if not using your Mac) | DigitalOcean $6/mo VPS | $6 |
| **TOTAL** | | **~$130-135/month** |

*X/Twitter API is the biggest cost. If budget is tight, skip X and focus on Telegram + Facebook + Instagram (which are free to post to). You can add X later.*

---

## Reporting Dashboard (Weekly)
Every Sunday at 08:00 WAT, run a reporting workflow:
```
[Cron: Sunday 08:00]
    ↓
[Read: posting_log.json + engagement_log.json + seo_log.json]
    ↓
[HTTP: POST to Claude with all logs → ask for weekly summary report]
    ↓
[HTTP: POST report to your Telegram (personal DM via bot)]
```

Claude generates a plain-English weekly report:
- Posts published vs target
- Platforms up/down
- Top performing content types
- SEO pages added
- Engagement actions taken
- Recommendations for next week
