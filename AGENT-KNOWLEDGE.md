# SifuFinds — Agent Knowledge Base

> **Living document.** Every agent and Claude session must read this before starting work and append new learnings after completing significant tasks. Keep entries concise and specific — include the exact fix, not just the problem.

---

## How to Use This File

**On session start**: Read this entire file. Apply documented fixes. Do not repeat documented mistakes.

**On session end**: Append what you learned under the correct category below. Date every entry.

---

## Errors to Never Repeat

| Date | What Broke | What Fixed It |
|------|-----------|---------------|
| 2026-06-17 | `shared.js` was given `defer` attribute, causing blank pages everywhere | Remove `defer`. `shared.js` must be synchronous at bottom of `<body>` — inline `init()` runs immediately after it, so `defer` causes init to fire before shared.js loads |
| 2026-06-17 | Blog post H1 injected via JavaScript instead of static HTML | Always use static `<h1>` in the generated HTML. One H1 per page, in the markup, not JS |
| 2026-06-17 | Stale matches shown on odds/tips pages | Never use `date: T_TODAY` for matches — use `T_TMR` or `T_IN2`. Never hardcode `live: true` with fake scores |
| 2026-06-17 | CORS block on leagues page | Leagues data must be served from static JSON cache, not fetched cross-origin from external API |
| 2026-06-17 | `lastmod` dates wrong in sitemap | `gen_sitemap.py` uses `os.path.getmtime()` per file — let it run automatically rather than hardcoding dates |

---

## SEO Learnings

### Title & Meta Rules
- `seo_title()` in `gen_blog_post_pages.py` enforces ≤ 60 chars — always use it, never bypass
- Run `python3 scripts/audit_titles.py` after EVERY generator run — it must exit 0, no exceptions
- Meta descriptions: 50–155 chars, keyword + CTA, every page, no exceptions

### Schema
- Article + FAQPage JSON-LD are auto-generated — never skip the `body` field in `posts.json`
- Verify: `grep -c "@type.*Article" blog/SLUG/index.html` must return ≥ 1

### Resources Box
- Auto-injected after body by `build_resources_box()` — verify with `grep -c "resources-box" blog/SLUG/index.html` (must be 1)
- Uses `_TAG_COUNTRY`, `_BK_SLUG_TO_LINK`, `_SPORT_ORG` dicts — update these when adding countries/bookmakers

### Internal / External Auto-Links
- Country names + bookmaker names in body → auto-linked by `COUNTRY_LINKS`, `BOOKMAKER_LINKS`
- Authority names (FIFA, UEFA, AFCON, Premier League, NLRC…) → auto-linked to official sites
- First mention only is linked — mention early in the body

### Content That Outranks
- Exceed top-3 SERP average word count by ≥ 20%, minimum 1,000 words
- Always include a comparison table (Bet9ja vs SportyBet is the evergreen Nigeria matchup)
- FAQs answering ≥ 3 PAA questions (heading must be `## FAQ` or `## Frequently Asked Questions`)
- Primary keyword: in title, H1, first 100 words, and ≥ 2 H2s

---

## Code Patterns That Work

### Generator Pattern
```python
# Always run with --force after any generator logic change
python3 gen_blog_post_pages.py --force
```
Rebuilds all 65+ posts with new logic. Never skip this after changing the generator.

### Live Data Integration Pattern
```javascript
// All pages that render bookmakers must call fetchLiveData() before first render
Promise.all([waitForCountry(), fetchLiveData()]).then(([country, _]) => init(country));
```

### Path to `countries_live.json` (depth-dependent)
- Root: `data/countries_live.json`
- 1 level deep (`tips/`, `odds/`, `blog/`): `../data/countries_live.json`
- 2 levels deep (`countries/nigeria/`): `../../data/countries_live.json`

### Deploying New Bookmaker Review Page
1. Add page to `bookmakers/` directory
2. Add to `BOOKMAKER_LINKS` dict in `gen_blog_post_pages.py`
3. Add to `_BK_SLUG_TO_LINK` dict in `gen_blog_post_pages.py`
4. Run `python3 gen_blog_post_pages.py --force`

---

## Market Intelligence

### Nigeria / Bet9ja (as of June 2026)
- Bet9ja vs SportyBet is the defining Nigeria debate — always include both in Nigeria content
- Bet9ja wins: odds depth, live markets, African football breadth
- SportyBet wins: 300% welcome bonus (vs Bet9ja 170%), <5 min withdrawals (vs 24hrs), mobile UX
- Bet9ja's #1 weakness: withdrawal friction — PissedConsumer 3.8/5 (504 reviews), 36% recommend
- Main withdrawal complaints: weekend delays, ID verification blocking first withdrawal, bank name mismatches
- OPay and PalmPay are the fastest withdrawal methods for Bet9ja
- Nigerian bettors hold accounts on multiple platforms simultaneously — content must acknowledge this
- Community lives on X/Twitter and TikTok, NOT Reddit — always run `/last30days` with X enabled for Nigerian topics
- WC2026 (June–July 2026) is the biggest betting moment — Bet9ja offers accumulator insurance

### Content Tone
- Lead with real bettor voices, not press releases — cite actual community complaints and wins
- Use local payment names: OPay, PalmPay, M-Pesa, MTN MoMo (never "e-wallets")
- Currency context mandatory: ₦ Nigeria · KSh Kenya · GH₵ Ghana · R South Africa
- 18+ / Responsible Gambling disclaimer at bottom of every post — no exceptions

---

## Research Intelligence

### Before Writing Any Content
1. `/firecrawl-search` — SERP recon on target keyword + 2–3 variations
2. `/firecrawl-scrape` — top 5 ranking pages for structure, word count, H2/H3, tables, FAQs
3. `apify/rag-web-browser` — semantic clusters, LSI terms, related questions
4. `apify/google-search-scraper` — People Also Ask for target keyword
5. `/last30days [topic]` — what the community is saying RIGHT NOW (Reddit, X, YouTube, TikTok)

### Research Sources Quality Ranking
- Community intelligence: X/Twitter > TikTok > Reddit > YouTube (for African betting topics)
- Regulatory intel: NLRC (Nigeria), BCLB (Kenya), GCA (Ghana), WCGRB (South Africa)
- Odds/stats: live API preferred; never show stale/hardcoded odds

---

## Agent Behavior Rules

### Every Agent Must
- Check this file (`AGENT-KNOWLEDGE.md`) before starting significant work
- Run `python3 scripts/audit_titles.py` after any generator run
- Never add `defer` to `shared.js` for any reason
- Never hardcode stale match data — use future-safe date variables
- Always include `fetchLiveData()` on new bookmaker pages
- Append learnings to this file before ending the session

### When Something Breaks
1. Check "Errors to Never Repeat" table above first
2. Check CLAUDE.md CRITICAL sections
3. Verify `grep -r 'shared\.js.*defer' --include="*.html" .` returns empty
4. Verify `grep -c '<h1' page/index.html` returns 1 per page

---

## Scheduled Routines

| Routine | Frequency | Script |
|---------|-----------|--------|
| Live data update | Every 5 hours | `update_countries.py` (GitHub Actions) |
| Failed workflow retry | 10-min delay (event) + 30-min safety net | `workflow_watchdog.yml`, `retry_failed.yml` |
| Sitemap regeneration | After new pages | `gen_sitemap.py` |

---

---

## 2026-06-22 — Live Football Data Integration (ESPN + FD)

### ESPN Unofficial API — What Works
- Base: `https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard?dates=YYYYMMDD`
- No auth required; use `User-Agent: Mozilla/5.0` header to avoid blocks
- Working slugs confirmed today: `rsa.1` (PSL), `gha.1`, `ken.1`, `uga.1`, `zim.1`, `zam.1`, `fifa.world`
- HTTP 400 slugs (ESPN doesn't cover them): `nig.1`, `tan.1`, `eth.1`, `mar.1`, `egy.1`, `caf.afcon`, `caf.cl`, `caf.cc`
- Clock field is in seconds (e.g. 5400.0 = 90 min FT). For live minute: `int(clock // 60)` doesn't work directly — use `shortDetail` like `"45'"` for in-play minute instead
- ESPN may be 1-2 minutes ahead of FD on status updates (shows FINISHED while FD still shows IN_PLAY)

### football-data.org Free Tier Constraints
- 100 req/day hard limit — throttle to max 1 call per 25 min in code
- `/v4/matches?dateFrom=&dateTo=` returns all accessible competitions in one call
- FD `minute` field is often `None` even when match is live (API lag) — ESPN enrichment fills this gap
- Free tier competitions: WC (2000), UCL (2001), PL (2021), La Liga (2014), Bundesliga (2002), Serie A (2019), Ligue 1 (2015), Eredivisie (2003), Primeira Liga (2017), Championship (2016), Brasileirao (2013)

### Merge Pattern (FD primary + ESPN supplement)
```python
# Dedup key: (homeNorm, awayNorm, date_str) — normalize with re.sub(r"[^a-z0-9]","",name.lower())
# Enrich: score + minute from ESPN if FD is lagging
# Status sync: upgrade SCHEDULED→LIVE and demote stale LIVE→FINISHED using ESPN
# Old JSON entries lack homeNorm/awayNorm — compute on-the-fly before indexing
```

### GitHub Actions Scheduling Pattern
- 5-min ESPN-only patch during peak hours (cron `*/5 9-23 * * *`) → uses no FD quota
- 30-min full update all hours (cron `*/30 * * * *`) → FD self-throttles internally
- Detect 5-min vs 30-min run: `[ "$((MINUTE % 30))" != "0" ]` in bash
- `concurrency: cancel-in-progress: true` prevents job pile-up

### Errors to Never Repeat (2026-06-22)
| What | Fix |
|------|-----|
| KeyError 'homeNorm' on existing JSON entries | Always check/compute `homeNorm`/`awayNorm` before merge, not just on fresh FD matches |
| Live match shown as IN_PLAY after final whistle | Sync ESPN FINISHED → override FD IN_PLAY in merge |
| ESPN clock = 5400.0 → minute = 90, not 5400 | Divide by 60: `int(float(clock) / 60)` capped at 120 |

*Last updated: 2026-06-22 by Claude Code*
