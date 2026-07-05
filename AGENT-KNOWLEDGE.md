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
| 2026-06-24 | 23 country pages had titles ending with `\|` (e.g. `...Bookmakers \|`) | Title template `f'...Licensed Bookmakers \| SifuFinds'` was 64–68 chars. `seo_title()` truncated at 60, cutting off `SifuFinds` and leaving a trailing `\|`. Fix: change template to `f'Best Betting Sites in {name} {YEAR} \| SifuFinds'` (44–51 chars). Applies to `generate_country_pages.py`, `gen_eg_ma.py`, `gen_sl_lr.py`, `gen_all_cities.py`. |
| 2026-06-24 | `analytics.html` showing as "Indexed, though blocked by robots.txt" in GSC | `robots.txt` blocked Googlebot from crawling it, so Google couldn't read the `noindex` meta tag in the page. Fix: remove `Disallow: /analytics.html` from Googlebot section — allow crawling so Google reads noindex and deindexes. Keep the `noindex` in the HTML. |
| 2026-06-24 | `firecrawl/apps/ui/ingestion-ui/index.html` accessible on GitHub Pages, showing in GSC as blocked-but-indexed | 3rd-party HTML file in `/firecrawl/` was reachable at `sifufinds.com/firecrawl/...` and blocked by robots.txt. Fix: added `<meta name="robots" content="noindex,nofollow">` to the file AND removed `/firecrawl/` from Googlebot disallow (main bot only) so Google can crawl and read the noindex. |
| 2026-06-24 | `tools/index.html` missing `<meta name="robots">` and `<meta property="og:url">` | Manually added both tags. All public pages must have robots meta and og:url. Check new pages with the audit script. |
| 2026-07-04 | 11 tracked directories (betting/rugby-betting/, bookmakers/, guides/, etc.) returned 403 because `Options -Indexes` is set and they had no `index.html` | Created proper SEO hub pages for all 11 directories + added `ErrorDocument 403 /404.html` to `.htaccess` as a safety net |
| 2026-07-04 | 52 absolute `https://sifufinds.com/SLUG` links in blog post bodies pointed to pages that don't exist (e.g. `/bet9ja-review`, `/responsible-gambling`, `/world-cup-2026`) | Added 52 `Redirect 301` rules to `.htaccess`. The auto-linker in `gen_blog_post_pages.py` uses correct relative paths — broken links came from raw markdown body text in `posts.json` with hardcoded wrong URLs. Use `.htaccess` redirects rather than regenerating all posts. |
| 2026-07-04 | `generate_country_pages.py`, `gen_city_pages.py`, `gen_payment_pages.py`, `gen_bk_reviews.py`, `gen_guide_pages.py`, `gen_bonus_pages.py` all had `<link rel="icon" href="assets/favicon.png">` in their `<head>` template — `assets/favicon.png` is a 1536×1024, 2.1MB PNG (never resized after export). All 23 live country pages were serving a 2.1MB "favicon" on every load — a huge mobile-data hit for an African-mobile-first audience. | Replaced with the standard 4-line favicon block used elsewhere on the site (`favicon.ico` + `favicon-32x32.png` + `favicon-16x16.png` + `apple-touch-icon.png`, all `?v=2`, absolute `/assets/...` paths) in all 6 generator templates, then reran `generate_country_pages.py --force`, `gen_eg_ma.py`, `gen_sl_lr.py` to flush the 23 live pages. Verify with `grep -rl 'assets/favicon\.png' --include="*.html" .` — must return nothing. **Never reference `assets/favicon.png` directly** — it's a source/export artifact, not a servable asset. |
| 2026-07-04 | `.htaccess` bundled `\.(json\|js\|css)$` under one `Cache-Control: no-cache, must-revalidate` rule. That forces a revalidation round-trip for `shared.js`/`shared.css` on *every single page view* even though they're already cache-busted via `?v=N` query strings bumped on every deploy — wasted latency on high-RTT mobile networks. | Split into two `FilesMatch` blocks: `^(shared\.js\|shared\.css)$` → `public, max-age=31536000, immutable` (safe because the `?v=N` query string, not the filename, is the freshness signal); everything else matching `\.json$` or the un-versioned `posts-data.js\|banners-data.js\|ticker-data.js` → stays `no-cache, must-revalidate` since those regenerate content without a version bump. **Do not blanket-apply long-cache to all `.js`/`.css`** — only the two versioned core-shell files qualify; `blog/*-data.js` files are not version-busted and would go stale for a year if cached long. |
| 2026-07-04 | `scripts/validate_site.py` Check 2 only recognized `Redirect 301 /path` (mod_alias) lines when building its "known redirect" allowlist. At some point `.htaccess` redirects were migrated to `RewriteRule ^slug/?$ /target [R=301,L]` (mod_rewrite) because plain `Redirect 301` wasn't firing on the live Hostinger/LiteSpeed host — this silently broke the validator, making it report all 52 legitimately-redirected links as broken. | Added a second regex to the redirect-scanning loop in `validate_site.py` that parses `RewriteRule ^slug/?$ /target [R=301...]` lines (strip trailing `/?` from the captured slug with `.rstrip("/?")` before rebuilding the target URL — the literal `?` in `/?$` is easy to accidentally capture into the slug and breaks matching). Whenever `.htaccess` redirect syntax changes, `validate_site.py`'s parser must be updated in the same change, or the pre-deploy gate silently stops working. |

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

## Google Indexing Rules (Permanent — Apply to Every Page)

> Set 2026-06-24 after fixing 273 non-indexed / "Indexed, though blocked by robots.txt" issues.

### The Golden Rules
1. **Title ≤ 60 chars on every page.** Use `seo_title()`. Never put "Licensed Bookmakers" AND "SifuFinds" in the same title template — it will exceed 60 chars and seo_title() will truncate, leaving a trailing `|`.
2. **Never block Googlebot from pages that have `noindex` meta tags.** If a page has `noindex` in the HTML, Googlebot must be ALLOWED to crawl it so it can READ the noindex directive. Blocking it in robots.txt AND putting noindex in the page = Google keeps it indexed forever with "Indexed, though blocked by robots.txt" in GSC.
3. **Every page needs `<meta name="robots" content="index, follow ...">`, `<link rel="canonical">`, and `<meta name="description">`.** No exceptions for any public page.
4. **Every page must be in a sitemap.** Run `python3 gen_sitemap.py` after adding any new page. Verify with `grep 'SLUG' sitemap-blog.xml`.
5. **robots.txt pattern for pages with noindex:** Allow crawling in robots.txt → put noindex in the HTML. Google crawls, reads noindex, deindexes. Do NOT block + noindex simultaneously.

### Generator Title Template Rules
- `generate_country_pages.py`: ✅ Fixed to `f'Best Betting Sites in {name} {YEAR} | SifuFinds'` (44–51 chars)
- `gen_eg_ma.py` / `gen_sl_lr.py`: ✅ Inherit from `generate_country_pages.py` — auto-fixed
- `gen_all_cities.py`: ✅ Fixed to `f'Betting Sites in {city}, {country} 2026 | SifuFinds'`
- All blog generators: ✅ Use `seo_title()` correctly
- **When adding a new generator: NEVER put more than one `|` separator before `SifuFinds`. Total title length including suffix must be ≤ 60 chars for ALL possible inputs.**

### robots.txt Architecture (sifufinds.com)
```
User-agent: *          → blocks /agents/, /.github/, /.venv/, /firecrawl/, /geo-content-writer/, /analytics.html
User-agent: Googlebot  → Allow: / + blocks /agents/, /.github/, /.venv/, /geo-content-writer/ ONLY
                         (firecrawl and analytics.html are NOT blocked for Googlebot — they carry noindex in the HTML)
```
- `/firecrawl/apps/ui/ingestion-ui/index.html` has `<meta name="robots" content="noindex,nofollow">` ✅
- `/analytics.html` has `<meta name="robots" content="noindex,nofollow">` ✅
- Googlebot can crawl both → will read noindex → will remove from index

### Canonical Tag Rules
- Canonical must always point to the page's own URL (self-referencing)
- Exception: old/renamed slugs deliberately pointing to the new canonical slug is CORRECT
- 10 blog posts intentionally point to newer-slug canonicals — do NOT "fix" these, they are intentional de-duplication
- Check for broken canonicals with: `python3 -c "import os,re; [print(p) for root,_,fs in os.walk('blog') for p in [os.path.join(root,f) for f in fs if f=='index.html'] if (m:=re.search(r'canonical href=\"(https://sifufinds\.com[^\"]*)', open(p).read())) and m.group(1).rstrip('/').split('/')[-1] != root.split('/')[-1]]"`

### GSC "Indexed, though blocked by robots.txt" Fix
- This appears when: URL is blocked in robots.txt BUT Google found it via links → can't read noindex
- Fix: ALLOW Googlebot to crawl the page so it reads noindex → Google deindexes it over next few crawl cycles
- Never rely on robots.txt alone to deindex a page — Google keeps known URLs indexed even when blocked

### Sitemap Health
- Total URLs as of 2026-07-04: **776** across 7 child sitemaps (added 11 new hub pages)
- sitemap-core.xml: 8 | sitemap-countries.xml: 106 | sitemap-blog.xml: 408
- sitemap-tips.xml: 51 | sitemap-betting.xml: 181 | sitemap-guides.xml: 12 | sitemap-other.xml: 6
- Run `python3 gen_sitemap.py` to regenerate — it auto-detects all public index.html files
- Excluded dirs in gen_sitemap.py: agents, firecrawl, geo-content-writer, supabase, .git, .github, .venv, __pycache__, node_modules, .claude, data

---

### 403/404 Architecture Rules (set 2026-07-04)
- **Every public directory MUST have an `index.html`** — `Options -Indexes` returns 403 for any directory without one
- **New section/category directories**: always create a hub `index.html` before adding child pages
- **Redirect broken internal links via `.htaccess`** using `Redirect 301 /old-path /correct/path/` — faster than regenerating 400+ blog posts
- **`.htaccess` ErrorDocument fallback**: `ErrorDocument 403 /404.html` and `ErrorDocument 404 /404.html` catch any missed directories
- **52 redirect rules** now in `.htaccess` covering bookmaker aliases, tips, guides, responsible gambling, odds, sport sections, WC2026/AFCON aliases

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

### Code Patterns (2026-07-04)
- **Mandatory backlink/reference on every blog post**: `build_resources_box()` in `gen_blog_post_pages.py` now always injects a reference/backlink to `https://bettingbrainiac.com/african-betting-sites/` alongside the existing BeGambleAware link. This is guaranteed on every post — do not remove it. Verify with `grep -c "bettingbrainiac.com/african-betting-sites" blog/SLUG/index.html` (should be ≥ 1). Rule documented in `CLAUDE.md` Step 4 / resources-box sections.
- Note: `blog/*/index.html` has ~408 directories on disk but `posts.json` only tracks 104 as "official" posts — the other ~300 are legacy/orphaned dirs not touched by the generator. Only the 104 in `posts.json` get resources-box/backlink updates on `--force` rebuild.

### Errors to Never Repeat (2026-07-05)
| What | Fix |
|------|-----|
| Google Search Console flagged "Events structured data" errors — `SportsEvent` JSON-LD items missing required `location`/`startDate` (critical) and `organizer`/`offers`/`image`/`performer`/`eventStatus` (non-critical) on `odds/index.html`, `tips/index.html`, `tips/world-cup-2026/index.html`, `tips/afcon/index.html`, `tips/caf-champions-league/index.html` | Only mark something up as `SportsEvent`/`Event` when it has a real, accurate single `location` + `startDate` (e.g. FIFA World Cup 2026 has known host countries + dates — kept as `SportsEvent` and completed with `eventStatus`, `eventAttendanceMode`, `organizer`, `image`). For ongoing/recurring competitions with no single date or venue (CAF Champions League, English Premier League, AFCON qualifying) — do NOT use `SportsEvent`/`Event` type at all, since Google explicitly says not to mark up events you don't have accurate date/location data for. Use plain `"@type": "Thing"` instead. |
| Rule going forward | Before adding any `@type` that is `Event` or an Event subtype (`SportsEvent`, `MusicEvent`, `Festival`, etc.) to JSON-LD anywhere on the site, it MUST include real `location` and `startDate`. If you can't state a real single date/venue, don't use the Event type — use `Thing` instead. Check with: `grep -rlE '"@type"\s*:\s*"(SportsEvent\|Event\|MusicEvent\|BusinessEvent\|Festival)"' --include="*.html" .` and verify each hit has `location` + `startDate`. |

*Last updated: 2026-07-05 by Claude Code*
