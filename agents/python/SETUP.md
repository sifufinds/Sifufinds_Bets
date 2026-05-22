# SifuFinds Agent System — Setup Guide
**Total cost: $0/month | Time to set up: ~2 hours**

---

## What You're Getting
14 automated runs per day, plus one weekly growth planning run, all in the cloud on GitHub's servers:
- **Agent 1** (Content Creator): 2x/day → blog post + social captions
- **Agent 2** (SEO): 1x/day → optimises every blog post
- **Agent 3** (Social Media): 4x/day → posts to Telegram, Facebook, Instagram
- **Agent 4** (Engagement): 4x/day → generates comments for African betting communities
- **Agent 5** (Growth Planner): 1x/week → weekly editorial calendar + campaign planning

---

## Step 1 — Get Your Free Groq Key (2 minutes, just Google sign-in)

1. Go to **groq.com**
2. Click **"Sign in with Google"** — uses your existing Google account, no new account
3. Once logged in: click **API Keys** → **Create API Key**
4. Copy the key — it looks like `gsk_...`

That's the AI brain. Free forever. No payment. No developer account. Just your Google login.

---

## Step 2 — Set Up Telegram (5 minutes, your phone number only)

No bot. No developer account. Just your Telegram account.

1. Go to **my.telegram.org** — log in with your phone number (same as Telegram app)
2. Click **"API Development Tools"** → fill in any app name → **Create Application**
3. You get: `App api_id` (a number) and `App api_hash` (a string) → copy both
4. Run the agent once locally (Step 6 below) — it will text your phone, you enter the code once
5. After that it runs automatically forever, no phone needed

---

## Step 3 — Set Up Facebook + Instagram (20 minutes, your Facebook login)

See [FB_SETUP_SIMPLE.md](FB_SETUP_SIMPLE.md) for exact steps.
Short version: go to developers.facebook.com → log in with YOUR Facebook → enable developer tools → get a token.
It's the same account. Same email. No payment.

**Facebook:**
1. Go to **developers.facebook.com** → Create App → choose "Business"
2. Add "Facebook Login" and "Pages API" products
3. Go to your Facebook Page → Settings → Page Access Tokens → generate a long-lived token
4. Save your **Page ID** (from your Page's About section) and the **Access Token**

**Instagram:**
1. Your Instagram must be a **Business Account** (free to convert — Settings → Account → Switch to Professional)
2. Connect it to your Facebook Page (Settings → Linked Accounts)
3. In your Facebook App, find your Instagram Business Account ID (Tools → Graph API Explorer → `GET /me/accounts`)

---

## Step 4 — Create GitHub Repository (10 minutes)

1. Go to **github.com** → New repository → name it `sifufinds-agents`
2. Make it **Public** (required for free GitHub Actions minutes)
3. Clone it to your Mac:
   ```bash
   git clone https://github.com/YOURUSERNAME/sifufinds-agents.git
   ```
4. Copy all files from the `agents/python/` folder into the repo root
5. Move the `.github/` folder to the repo root as well
6. Push to GitHub:
   ```bash
   git add .
   git commit -m "Initial agent setup"
   git push
   ```

**Folder structure in your GitHub repo should look like:**
```
sifufinds-agents/
├── .github/
│   └── workflows/
│       ├── agent1_content.yml
│       ├── agent2_seo.yml
│       ├── agent3_social.yml
│       ├── agent4_engagement.yml
│       └── agent5_plan.yml
├── agent1_content.py
├── agent2_seo.py
├── agent3_social.py
├── agent4_engagement.py
├── agent5_plan.py
├── config.py
├── llm.py
├── requirements.txt
└── utils/
    ├── football_api.py
    ├── logger.py
    └── queue_manager.py
```

---

## Step 5 — Add Your Secrets to GitHub (10 minutes)

In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**

Add these one by one:

| Secret Name | Value | Required? |
|---|---|---|
| `GROQ_API_KEY` | Your Groq key from groq.com | **YES — start here** |
| `TELEGRAM_API_ID` | Number from my.telegram.org | Yes |
| `TELEGRAM_API_HASH` | String from my.telegram.org | Yes |
| `TELEGRAM_SESSION_STRING` | Generated on first local run | Yes (after Step 6) |
| `TELEGRAM_CHANNEL_USERNAME` | @YourChannelUsername | Yes |
| `FACEBOOK_PAGE_ID` | Your Page ID | Yes |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | Long-lived page token | Yes |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Your IG account ID | Yes |
| `FOOTBALL_API_KEY` | `fd_554baa8cfac7cfe33ba92edfbc00f3e2a179ba179f44ada9` | Already have it |
| `ODDS_API_KEY` | Your Odds API key | Optional |

---

## Step 6 — Test Each Agent Manually (20 minutes)

In your GitHub repo: **Actions → [Agent name] → Run workflow → Run workflow**

Do this for each agent, in order:
1. Run Agent 1 first → check it completes without errors
2. Run Agent 2 → check it reads Agent 1's output
3. Run Agent 3 → check posts appear on Telegram/Facebook/Instagram
4. Run Agent 4 → check engagement_queue.json is created

If any fail: click the failed run → read the error log → it'll tell you exactly what's wrong.

---

## Step 7 — Activate Automatic Schedule

The agents run automatically once you push the `.github/workflows/` files to GitHub. No extra step needed. GitHub reads the `cron:` schedule in each YAML file and runs them automatically.

**Daily schedule (WAT):**
- 03:00 — Agent 2 SEO audit
- 06:00 — Agent 1 creates content + Agent 4 engages
- 07:00 — Agent 3 posts to social media
- 08:00 — Agent 4 engages
- 10:00 — Agent 4 engages
- 11:00 — Agent 3 posts
- 12:00 — Agent 4 engages
- 15:00 — Agent 1 creates content + Agent 4 engages
- 16:00 — Agent 3 posts + Agent 4 engages
- 17:00 — Agent 3 posts
- 19:00 — Agent 4 engages
- 20:00 — Agent 3 posts + Agent 4 engages

---

## Your 15-Minute Daily Task (Optional But Recommended)

The agents handle everything automatically. But to maximise growth, spend 15 mins/day on:

1. **Read `engagement_queue.json`** → manually post the 5 generated comments on Facebook/Instagram/Reddit (Facebook API restricts commenting on other pages)
2. **Post the Quora answer** → paste Agent 4's answer on Quora.com
3. **Check the log** → GitHub Actions → see which runs succeeded

That's it. Everything else is fully automated.

---

## Monthly Cost Breakdown

| Service | Cost |
|---|---|
| Gemini API (free tier: 1M tokens/day) | **$0** |
| GitHub Actions (public repo: 2000 min/month) | **$0** |
| Telegram Bot API | **$0** |
| Facebook/Instagram Graph API | **$0** |
| Footballdata.io (existing free key) | **$0** |
| **TOTAL** | **$0** |

---

## Troubleshooting

**Agent fails with "JSON parse error"**
→ Gemini occasionally returns markdown-wrapped JSON. The code strips this, but if it still fails, run the workflow again — it'll work on retry.

**Facebook/Instagram posts not appearing**
→ Your Page Access Token expires. Generate a new long-lived token at developers.facebook.com and update the GitHub Secret.

**GitHub Actions not running on schedule**
→ GitHub pauses scheduled workflows after 60 days of repo inactivity. Fix: push any commit to the repo to reactivate. Or click "Run workflow" manually.

**Telegram bot not posting**
→ Make sure the bot is an Admin on your channel with "Post Messages" permission.
-----BEGIN RSA PUBLIC KEY-----
MIIBCgKCAQEAyMEdY1aR+sCR3ZSJrtztKTKqigvO/vBfqACJLZtS7QMgCGXJ6XIR
yy7mx66W0/sOFa7/1mAZtEoIokDP3ShoqF4fVNb6XeqgQfaUHd8wJpDWHcR2OFwv
plUUI1PLTktZ9uW2WE23b+ixNwJjJGwBDJPQEQFBE+vfmH0JP503wr5INS1poWg/
j25sIWeYPHYeOrFp/eXaqhISP6G+q2IeTaWTXpwZj4LzXq5YOpk4bYEQ6mvRq7D1
aHWfYmlEGepfaYR8Q0YqvvhYtMte3ITnuSJs171+GDqpdKcSwHnd6FudwGO4pcCO
j4WcDuXc2CTHgH8gFTNhp/Y8/SpDOhvn9QIDAQAB
