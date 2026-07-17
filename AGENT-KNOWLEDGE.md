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

### Code Patterns (2026-07-05) — Indexability self-healing
- New `scripts/check_indexability.py`: detects + auto-fixes (`--fix`) anything that could stop Google from crawling/indexing the site — catastrophic `Disallow: /` in robots.txt for `*`/Googlebot, unexpected `noindex` meta/X-Robots-Tag on public pages, schema.org Event objects missing required `location`/`startDate` (auto-downgrades to `Thing`, same fix pattern as the GSC incident above), and sitemap URLs accidentally blocked by robots.txt. Supports `--live` to probe production with a Googlebot UA, `--report` to write `indexability-report.json`.
- Wired in 3 places: (1) `deploy_hostinger.yml` runs it in detect-only mode as a hard pre-deploy gate (blocks deploy on CRITICAL, same tier as `validate_site.py`/`audit_titles.py`); (2) `daily_seo_doctor.yml` runs it with `--fix --live --report` before `seo_doctor.py` so regressions self-heal daily; (3) `site_monitor.yml` (hourly) does a fast live probe (robots.txt reachability/Disallow, homepage X-Robots-Tag) and triggers `daily_seo_doctor.yml` immediately via `gh workflow run` if Google is blocked, instead of waiting for the 06:00 UTC cron.
- Test fixtures confirmed all 3 detectors (robots disallow-all, unexpected noindex, Event missing fields) fire correctly and `--fix` resolves each one before committing this.
- Gotcha: GNU `grep -P`/`-z` for multi-line robots.txt parsing is not reliably portable (macOS BSD grep lacks `-P` entirely) — use a small inline `python3 -c` block instead, matching the pattern other steps in these workflows already use for JSON parsing.

### Errors to Never Repeat (2026-07-05) — duplicate blog slugs silently shadow content
- Found via `scripts/seo_check.py` flagging `missing_faqpage_schema` on 2 posts, which led to investigating why `--fix` wasn't correctly truncating 4 other long titles/excerpts — root cause was **3 pairs of posts in `blog/posts.json` sharing the same `slug`** (e.g. `world-cup-2026-updates` existed twice with completely different titles/bodies/ids).
- Why it's dangerous: `gen_blog_post_pages.py`'s generation loop writes `blog/<slug>/index.html` for every post in array order — the LAST array entry with a given slug wins, silently overwriting the earlier one's page. The earlier post's content becomes **completely unreachable at its own URL** even though it's still sitting in `posts.json` looking published. `seo_check.py --fix` also mutated the wrong duplicate (via a slug-keyed dict, which only keeps the last occurrence) because of this, which is how the bug was first noticed.
- How the 3 existing dupes were resolved: kept the higher-array-index entry (confirmed via `grep -o '<title>' blog/SLUG/index.html` that it was the one actually live) under the original slug; the shadowed lower-index entry got a new slug generated from its own title.
- **Permanent fix — `dedupe_slugs()` in `gen_blog_post_pages.py`**: runs at the very start of `main()`, before any page is generated. Detects any slug collision, keeps the slug on the array-last entry (the one that would win anyway), and renames every earlier duplicate to a fresh slug derived from its own title. Writes the fix back to `posts.json` automatically. This runs on every single `gen_blog_post_pages.py` invocation (manual, doctor, backfill, CI) — the bug class cannot recur unnoticed again.
- **Defense in depth** — `scripts/seo_check.py` now has a `duplicate_slug` CRITICAL check (independent of the generator) wired into the `deploy_hostinger.yml` pre-deploy gate, so even if `dedupe_slugs()` were ever removed or bypassed, the deploy would still block.
- Rule going forward: any time you add code that creates new blog posts (any `agent_*.py`, `merge_posts.py`, manual `posts.json` edits), do NOT assume slug uniqueness is guaranteed at creation time — always run `gen_blog_post_pages.py --force` afterward (it self-heals), and never disable/bypass `dedupe_slugs()`.

### Code Patterns (2026-07-05) — permanent SEO score fixes + content-depth backfill
- Root-caused and fixed the 7 HIGH title/meta-length issues from the `/last30days`-style SEO score check — turned out 4 of them were actually the duplicate-slug bug above (the audit was flagging the right slug but `--fix` patched the wrong duplicate object). After `dedupe_slugs()` ran, `seo_check.py --fix` correctly truncated all remaining offenders in one pass. Verify anytime with `python3 scripts/seo_check.py` — should be 0 critical / 0 high.
- **New `agents/python/agent_content_backfill.py`**: permanent, durable fix for "160/168 posts under 900 words, 113/168 missing FAQ section" — the single biggest drag on the site's SEO score. Each run: picks up to 4 posts (`BATCH_SIZE`) still below standard (featured posts prioritized), calls `research()` (Firecrawl+Apify, fails silently if keys are exhausted/unavailable) then `ask_long()` (Groq→Gemini→Claude fallback chain from `llm.py`) to expand the post to 1,000-1,400 words with a real `## FAQ` section (4 Q&As) and a comparison table, while preserving the original facts/voice. Validates the result with `gen_blog_post_pages.extract_faq_schema()` (the *exact* function that decides whether FAQPage schema gets generated) before accepting it — if the LLM's output doesn't actually produce valid schema or hit the word count, the attempt is rejected and retried next run (capped at 3 attempts via `agents/python/content_backfill_state.json`, which is git-committed so progress/attempt-counts persist across every session and CI run forever — this is the literal mechanism for "always remembered").
- Live-tested end-to-end on 2026-07-05: the pipeline logic (batch selection, retry/attempt tracking, graceful failure) all worked correctly, but the actual LLM call failed on every one of 4 test posts because the shared Groq/Gemini keys were already at their daily quota from the site's other content bots (`agent1_content.py`, `agent_sports_blog.py`, `breaking_news.yml` — these run many times a day on the same keys) and Firecrawl/Apify keys were rejecting with 402/403. This is expected, not a bug — the agent is designed to no-op safely on quota exhaustion and pick back up automatically on the next scheduled run once Groq's daily token quota resets at midnight UTC. `.github/workflows/content_backfill.yml` is scheduled for 00:15 UTC specifically to run right after that reset, ahead of the other bots.
- Gotcha: this repo's system Python is 3.9.6 locally (despite `.python-version` saying 3.13 and CI using 3.11) — `str | None` union-type annotations throw `TypeError` at import time on 3.9. Add `from __future__ import annotations` to any new `agents/python/*.py` script that uses PEP 604 union syntax (existing scripts like `agent_brand_scraper.py` already do this — follow that pattern).
- `blog/posts.json` had **168** posts as of this fix (not the ~104 "official" count noted on 2026-07-04 — that number is stale/was referring to a different subset; always get the live count via `json.load(open('blog/posts.json'))['posts']` rather than trusting a previously-recorded figure).

### Errors to Never Repeat (2026-07-06) — broken git retry pattern in CI bots
- `breaking_news.yml` and my new `content_backfill.yml` both used this push-retry pattern on conflict: `git reset --soft HEAD~1` → `git rebase FETCH_HEAD` → re-add → `commit --amend`. This reliably fails with `error: cannot rebase: you have unstaged changes` / `additionally, your index contains uncommitted changes` — confirmed via `gh run view --log-failed` on multiple real `breaking_news.yml` failures (e.g. run 28756070697, 2026-07-05T21:51). Root cause: after the soft reset stages the OLD commit's tree, the regeneration scripts (`gen_blog_post_pages.py`, `gen_sitemap.py`) that run next rewrite the working tree to something different from what's staged — `git rebase` refuses to start with a dirty index+worktree.
- **Fix**: replace the whole reset+rebase dance with a plain `git merge --no-edit origin/main || true` (merge, not rebase, has no clean-tree precondition), then run `merge_posts.py` + regenerate + `git add -A` + `git commit --allow-empty`. Any merge conflicts left in generated files (`blog/*/index.html`, `sitemap*.xml`) are moot because the regeneration step immediately overwrites them from scratch — matches the pattern that worked when resolving a real merge by hand earlier this session.
- Rule going forward: never use `git reset --soft` immediately followed by scripts that modify the working tree, then `git rebase` — rebase needs a clean tree at the moment it starts, full stop. If any other workflow is added with a "regenerate then push-retry" shape, use the merge pattern above, not reset+rebase.

### Errors to Never Repeat (2026-07-06) — iCloud Drive sync creates " 2"-suffixed duplicate files mid-session
- This repo lives at `~/Desktop/Sifu Finds`, which is iCloud Drive-synced. Rapid programmatic file writes (e.g. `gen_blog_post_pages.py --force` rewriting 170+ HTML files in one script run) trigger iCloud's conflict-resolution behavior, which silently creates `filename 2.ext` duplicate copies alongside the real file — confirmed by finding `agents/python/agent_content_backfill 2.py`, an exact duplicate of a file created moments earlier in the same session, plus hundreds more throughout `.venv/` (gitignored, harmless) and several inside tracked blog/workflow paths (not harmless — these got swept into a `git add -A` and briefly committed to the repo before being caught and reverted).
- **Never blindly `git add -A` without checking `git status` for stray `* 2.*` files first** in this repo (or any iCloud-synced working directory). Check with: `find . -name "* 2.*" -not -path "./.git/*" -not -path "./.venv/*"` — should always return empty; if not, diff each against its non-suffixed counterpart (they're consistently stale/identical snapshots, never unique content) and delete.
- Longer-term fix worth considering (not applied — infra choice, not code): move the working copy out of iCloud Drive sync scope, or add `~/Desktop/Sifu Finds` to iCloud's sync-exclusion list, to stop this from recurring every session.

### Errors to Never Repeat (2026-07-06) — dead author-schema check in seo_check.py
- `scripts/seo_check.py`'s `author_schema_org_not_person` check did `html.split('"author"')[1][:150]` to find the JSON-LD author type — but the FIRST `"author"` occurrence on every page is the unrelated `<meta name="author" content="...">` tag (appears in `<head>`, before any JSON-LD), so the check was silently looking at the wrong substring on every single post and could never actually fire. Confirmed via direct `.split()` test showing it captured the meta tag's content attribute, not `{"@type": "Organization", ...}`.
- This is NOT the same as "author should always be Person" — `gen_blog_post_pages.py`'s `author_schema` logic (~line 1452) deliberately assigns `Person`/`#sifu-kai` schema ONLY when a post's `author` field is exactly `'Sifu Kai'`; every "desk" byline (Football Desk, Cricket Desk, etc. — currently **100% of all 174 posts**, since none are bylined to Sifu Kai literally) correctly gets `Organization` schema instead, to avoid misattributing desk-written content to his named identity. Fixed the check to only flag a REAL regression: post's `author` field says `'Sifu Kai'` but the generated schema isn't `Person` — found via `re.search(r'"author":\s*\{[^}]*\}', html)` (the JSON-LD object specifically, not the meta tag) checked against `p.get('author')`. Verified: 0 false positives against current site (no posts are bylined to Sifu Kai yet), and a synthetic test confirms it correctly flags a Person→Organization regression when one exists.
- Rule going forward: never string-match on a bare field name like `"author"` to locate a specific JSON-LD property when the same string can appear elsewhere on the page (meta tags, visible bylines, etc.) — anchor the regex/search to the actual JSON-LD shape (e.g. `"author":\s*\{`) so it can't collide with unrelated occurrences.
- Content strategy note (not a defect, an opportunity): 0/174 posts are bylined to the real named author "Sifu Kai" — all use generic desk bylines. Named, checkable authorship with a bio generally strengthens E-E-A-T and AI-citation (GEO) trust signals more than an organizational desk credit. Worth considering for at least the flagship/cornerstone posts.

### Code Patterns (2026-07-06) — named authorship (E-E-A-T) byline correction
- Acted on the "0/174 posts bylined to Sifu Kai" opportunity noted above. Read `about/index.html`'s actual bio first (`Sifu Kai is SifuFinds' founder and lead betting analyst... personally reviews every top-tier bookmaker... verifies bonus terms directly with operators... particular expertise... mobile money betting flows (OPay, PalmPay, M-Pesa)... deep specialisation in Nigerian, Kenyan, and West African markets`) to identify which EXISTING posts already fall genuinely within his stated scope, rather than mass-relabeling arbitrary content (which would itself be a form of misattribution in the other direction, and could read as E-E-A-T gaming to Google rather than genuine signal).
- Reassigned exactly 10 posts whose desk byline was a country/region/strategy desk matching his bio 1:1 (bookmaker bonus/withdrawal guides, mobile-money payment guides, bookmaker head-to-head comparisons, accumulator strategy, country betting-site guides for Nigeria/Kenya/Ghana/Tanzania) from `SifuFinds Nigeria Desk` / `SifuFinds Kenya Desk` / `SifuFinds Ghana Desk` / `SifuFinds East Africa Desk` / `SifuFinds Africa Desk` / `SifuFinds Betting Strategy Desk` → `Sifu Kai`, in **both** places: the live data (`blog/posts.json`) and the source seed templates (`gen_blog_post_pages.py`'s `NEW_POSTS` list, so the fix isn't lost if that list is ever the source of truth again). Verified all 10 correctly get `"@type": "Person"` schema after regeneration, and the (now-fixed, see earlier entry) `author_schema_org_not_person` check in `seo_check.py` stays silent (no false positives).
- Left every genuinely out-of-scope desk alone (Football/Sport News/Basketball/Tennis/Cricket/Rugby/Boxing/F1/iGaming/World Cup desks — these cover beats outside his stated specialization and attributing them to him personally would be dishonest, exactly the scenario the original `author_schema` code comment in `gen_blog_post_pages.py` warns against).
- Fixed at the source too: `agents/python/agent_sports_blog.py`'s `CATEGORIES["betting"]["author"]` was `"SifuFinds Analytics"` (0 posts published under it yet) — changed to `"Sifu Kai"` since betting strategy/analytics is explicitly his stated beat, so all future posts in that category get correct Person schema automatically without needing another retroactive pass.
- Rule going forward: when assigning "Sifu Kai" as author (vs. a desk), the content must actually match his stated bio scope in `about/index.html` (bookmaker reviews/verification, mobile money payment guides, Nigeria/Kenya/West Africa country content, betting strategy/accumulators, AFCON futures, CAF Champions League). If his bio scope changes, this fix must be re-evaluated — don't just keep adding categories to his byline without checking the bio still supports it.

### Errors to Never Repeat (2026-07-06) — content backfill attempt-counter penalized infrastructure failures
- `agent_content_backfill.py`'s retry-cap logic incremented the same `attempts` counter whether the LLM call outright failed (quota/rate-limit exhaustion) OR the LLM returned content that failed our word-count/FAQ validation. Ran the agent 3 times today (once via a manually-triggered CI run, twice locally) and the same 4 featured posts hit every single provider in the fallback chain (`Groq 70B → Groq 8B → Gemini flash-lite → Gemini flash`, no Claude — key still not configured) and failed all 3 times purely on quota exhaustion, not content quality — which meant they hit `MAX_ATTEMPTS=3` and got **permanently benched** from the queue despite the LLM never actually having a fair shot at producing a valid expansion.
- Fixed: an outright LLM call failure (`_expand_post` returns `None`) no longer increments `attempts` — only a call that succeeds but produces output failing our own validation (word count < 1000 or no extractable FAQ schema) counts against the 3-attempt budget. Reset the 4 wrongly-penalized posts' attempt counts to 0 in `content_backfill_state.json` so they re-enter the queue.
- Root blocker is still unresolved and outside what I can fix in code: shared Groq/Gemini keys are apparently saturated most of the day by the site's other content bots (`agent1_content`, `agent_sports_blog`, `breaking_news` — several runs/day each), and there's still no `ANTHROPIC_API_KEY` secret configured for the fallback chain's third tier. Until one of those changes, expect most backfill runs to genuinely fix 0 posts — that's now at least tracked correctly (not silently exhausting the retry budget) rather than being a second, compounding problem.

### Errors to Never Repeat (2026-07-12) — deploy silently blocked 3 days by AI-hallucinated internal links
- The live site received **zero deploys from 2026-07-09T10:24 UTC to 2026-07-12** — 3 days, ~100+ consecutive `deploy_hostinger.yml` failures, all in ~15-20s (fast-fail at the validation step). Root cause: `agent_sports_blog.py`'s LLM output occasionally hardcodes a markdown link to a `sifufinds.com/<path>` that doesn't exist (e.g. `[African Bookmakers](https://sifufinds.com/african-bookmakers)`, `[Sports News](https://sifufinds.com/sports-news)`) — `scripts/validate_site.py` CHECK 2 correctly flagged these as broken links and blocked deploy exactly as designed, but **nothing ever fixed the broken links**, so the same 4 posts blocked every single deploy attempt for 3 days straight while `breaking_news.yml` kept committing more content to `posts.json` that never reached production. Found via `gh run list --workflow=deploy_hostinger.yml` (100 straight failures) + `gh api .../runs?page=2` to find the last success, then `gh run view <id> --log` on a failing run to see the exact CHECK 2 output.
- Compounding factor: my local checkout was 6 days behind `origin/main` (`git log` showed a stale HEAD) — always `git fetch origin main && git merge-base --is-ancestor HEAD origin/main` before diagnosing "why hasn't X happened" on this repo; the live state only lives on `origin/main`/production, never assume local `blog/posts.json` reflects reality without fetching first.
- **Immediate fix**: added 4 `.htaccess` `RewriteRule` 301s (`african-bookmakers→/bookmakers/`, `african-leagues→/leagues/`, `football-betting-nigeria→/countries/nigeria/`, `sports-news→/blog/`) so the backlog could deploy right away, then manually triggered `gh workflow run deploy_hostinger.yml` to flush 3 days of queued posts to production immediately (confirmed live at `sifufinds.com/blog/posts.json` afterward).
- **Permanent fix** (the actual "make sure this doesn't happen again"): added `sanitize_internal_links()` to `gen_blog_post_pages.py`, called from `main()` right after `dedupe_slugs()` (same self-healing pattern — runs on every `--force` invocation, writes the fix back to `posts.json` automatically). It regexes every post body for `[text](https://sifufinds.com/path)`, and if `path` doesn't resolve to a real `index.html`/`.html` file AND isn't covered by an `.htaccess` redirect (parses `.htaccess` with the exact same regex `scripts/validate_site.py` uses, so the two never disagree), it strips the markdown link down to plain text. This means a future hallucinated internal link can never block deploy again — no more manual `.htaccess` patching required. Also tightened `agent_sports_blog.py`'s `SYSTEM_PROMPT` with an explicit "LINKING RULES — NON-NEGOTIABLE" section forbidding the writer from emitting any internal markdown link at all (the auto-linker in `gen_blog_post_pages.py` — `COUNTRY_LINKS`/`BOOKMAKER_LINKS`/`CORE_LINKS`/resources box — already handles this correctly from plain-text mentions, so the LLM never needed to hand-write these links in the first place).
- Added a row to the SEO self-healing table in `CLAUDE.md` for this guard category, per the standing rule that any new SEO issue class must get a permanent automated check + a table entry, not just a one-off manual patch.
- Rule going forward: `validate_site.py` blocking deploy is *working as intended* — the actual bug was that there was no automated remediation path when it fired, only a comment telling a human to fix `.htaccess` by hand. Any future "pre-deploy gate blocks X" pattern needs a corresponding auto-fix step (like `sanitize_internal_links()` here, or `check_indexability.py --fix` for indexability) — a validator with no auto-fix is a guaranteed multi-day outage waiting to happen the next time nobody's watching CI.
- Separately noticed (not yet fixed, needs a human decision): `agent_sports_blog.py`'s LLM fallback chain (`llm.py`) hits `"All AI providers exhausted"` regularly — Groq's free daily token quota (TPD) gets used up by the volume of scheduled runs (`breaking_news.yml` alone does 4 `generate_post()` calls × 3 runs/day = 12/day, plus `content_backfill.yml` on the same keys), and the Gemini fallback then fails because billing isn't enabled on that Google Cloud project. `ANTHROPIC_API_KEY` (tier 3 in the fallback chain, already coded and working in `llm.py`) has **no secret configured** in the repo (`gh secret list` confirms it's absent) — this has been a known gap since at least 2026-07-06 (see backfill entry above) and is outside what code alone can fix; needs the user to either add a funded `ANTHROPIC_API_KEY` secret, enable billing on the Gemini project, or reduce scheduled generation volume to fit Groq's free daily cap.
- Also noticed: this project's `.claude/settings.json` has a `Stop` hook that auto-commits (`git add <allowlisted dirs> && git commit -m "deploy: ..."`) and pushes on every session end — but its `git add` allowlist does **not** include `.htaccess`, `gen_blog_post_pages.py`, `gen_sitemap.py`, or `sitemap*.xml`. Any fix touching those files must be committed manually — don't rely on the Stop hook to pick them up.

### Code Patterns (2026-07-13) — new Brand Discovery & Lifecycle Agent (weekly)
- Built `agents/python/agent_brand_discovery.py` + `.github/workflows/brand_discovery.yml` (Mondays 03:30 UTC) to close two gaps that turned out not to exist anywhere in the codebase despite there already being `agent_brand_scraper.py` (daily bonus-copy updater for 11 hardcoded brands) and `agent_brand_reviews.py` (LLM-only review generator for 19 hardcoded brands, no live research, disconnected from `bookmakers/`): **(1)** nothing discovered brands not yet on the site, **(2)** nothing detected or removed brands that had stopped operating. Confirmed via `grep -rE "defunct|closed|inactive|remove|deprecat|shut ?down|ceased|delist|blacklist" agents/python/ scripts/` returning zero relevant hits before building this.
- **Scope decision (asked the user directly, don't re-litigate without cause)**: adds are fully autonomous (research → write → commit → deploy, no human gate) but capped at `MAX_NEW_BRANDS_PER_RUN = 1` per week by design, one well-researched brand beats several shallow ones. Removals are two-strike: flagged as suspected-defunct on one run, only actually removed if still suspected-defunct on a **later** run (naturally ~1 week apart since the job is weekly) — absorbs a temporarily-down site or one noisy search result without an irreversible action. New brands get a review page + blog post only, deliberately NOT wired into the `BOOKS` live-odds/affiliate-CTA object in `assets/shared.js` (~370 hand-maintained entries across 23 country pages), since the agent has no way to verify SifuFinds actually has a real affiliate/tracking relationship with a brand it just discovered — inserting a fake "claim bonus" CTA for an unverified brand would be dishonest and is out of scope. That reconciliation (this agent's brands vs. `BRAND_REGISTRY` in `agent_brand_scraper.py` vs. the 19-brand dict in `agent_brand_reviews.py` vs. `BOOKS`) was explicitly left undone — those three systems remain disconnected; this agent only reads them for name-collision checks, never writes to them.
- **Refactor that made safe automated add/remove possible**: extracted the previously-hardcoded `BOOKMAKER_LINKS` / `_BK_SLUG_TO_LINK` Python literals in `gen_blog_post_pages.py` into `data/bookmaker_links.json` (single source of truth, loaded at import time via `_load_bookmaker_entries()`, filtered to `status=='active'` rows only). Verified byte-for-byte identical output to the old hardcoded literals before/after the refactor. This matters because the alternative (an unattended weekly script regex-editing a live `.py` source file's list literal) is exactly the kind of fragile hack that, one bad edit, breaks the whole site generator — a JSON read/write is atomic and trivially validated instead.
- **"Full and proper research" is a real multi-step gate, not an LLM guessing**, in `research_candidate()`: (1) Firecrawl-find the official domain, (2) Firecrawl-scrape it and require betting-related keywords present, (3) require an African-market signal (country name, local currency, or local payment method like M-Pesa/OPay/MTN MoMo) in either the homepage or search snippets, (4) a reputation search for scam/fraud/unlicensed language with a hard reject threshold (≥3 hits across results). Only a candidate passing all four gets an LLM content-generation pass. Failed candidates are recorded in `brand_discovery_state.json["rejected_candidates"]` with the reason, so the same rejected name isn't re-researched every week.
- **Content generation reuses the project's real content rules as a hard validator, not just prompt text**: `_validate_content()` mechanically rejects any draft containing an em/en dash (—/–), under 1,000 words, missing a `## FAQ` heading, missing a markdown table, or containing a hand-written internal `sifufinds.com` markdown link (the exact failure class documented in the 2026-07-12 entry below) — with up to one retry that appends the specific rejection reason to the prompt before giving up for the week. Ratings/scores are LLM-proposed but **clamped in Python** to `[3.3, 4.3]` (`_clamp_score()`) regardless of what the model outputs, since a brand-new, one-week-old listing has no business getting an inflated 4.9 like the long-standing hand-reviewed pages — the bookmaker page template also renders "🆕 New Listing — Under Ongoing Review" instead of "✅ Recommended", and the CTA links straight to the plain official site (no `rel="sponsored"`, since there's no real affiliate relationship to disclose).
- **Removal never deletes or 404s anything**: `_remove_brand()` sets `status: "removed"` in `data/bookmaker_links.json` (row and evidence trail kept, just stops being linked from new content), overwrites `bookmakers/<slug>/index.html` with a live `noindex` "no longer operating" notice via `render_discontinued_page()` in the new `agents/python/utils/bookmaker_page_template.py`, and prepends an editor's note to the paired blog post's body rather than deleting the post. Matches this repo's existing hard anti-404 stance (see the 403/404 section in `CLAUDE.md`) applied to a new, riskier automated-removal context.
- **Extra safety gate specific to this workflow**: unlike the other content bots which self-heal silently, `brand_discovery.yml` runs `scripts/validate_site.py --strict` and only commits/pushes/triggers deploy if it exits 0 — skips the commit entirely (not a hard workflow failure, just no-op) if it doesn't, since this is the one agent that publishes genuinely new, previously-unreviewed pages every run and the 2026-07-12 incident below already showed what "validator blocks, nothing auto-recovers" looks like for 3 days when nobody's watching.
- Added `brand_discovery.yml` to both `workflow_watchdog.yml`'s event-driven retry list (with its case-statement mapping) and `retry_failed.yml`'s 30-minute polling list, per the project's standing auto-retry rule that every workflow must be covered by both.
- Gotcha confirmed again: this repo's local Python is 3.9.6, so `agent_brand_discovery.py` and `bookmaker_page_template.py` both start with `from __future__ import annotations` — verified by actually running `python3 agent_brand_discovery.py --help` locally (not just assuming it would work) before considering the file done.
- New public wrappers `fc_search()`/`fc_scrape()` added to `utils/serp_research.py` (thin delegates to the existing private `_fc_search`/`_fc_scrape`) so this agent's legitimacy/liveness checks reuse the same authenticated Firecrawl plumbing instead of a third reimplementation of API-key handling and error suppression.
- Note for whoever wires up secrets: `gen_blog_post_pages.py` is **not** in `.claude/settings.json`'s Stop-hook auto-commit allowlist (only `data/`, `agents/python/`, `.github/workflows/`, `bookmakers/`, `blog/`, etc. are) — a future session editing that file (as this one did, for the `BOOKMAKER_LINKS` refactor) needs to commit it manually, the Stop hook will silently skip it otherwise. Same applies to any other root-level `.py`/`.html` file.

### Market Intelligence + Code Patterns (2026-07-13) — Brand Partnership Outreach Agent
- **Found a real, quantifiable monetisation gap by reading `assets/shared.js`'s `AFFILIATE_DOMAINS` list against the `BOOKS` entries**: only 1xBet, Melbet, BetWinner, Paripesa and TicTacBets currently route through a tracked affiliate domain (`reffpa.com`, `refpa3665.com`, `combodef.com`, `bwredir.com`, `trackrt.tictacbets.co.za`). Bet9ja, SportyBet, BetKing, Betway (6 countries), Betika and SportPesa all link straight to the brand's own domain with zero tracking, despite getting full bonus-table placement and editorial coverage across 1 to 6 country pages each. That gap is the entire basis for the new outreach agent, don't rebuild this analysis from scratch next time, just recheck `AFFILIATE_DOMAINS` vs `BOOKS` for anything that's changed.
- Built `agents/python/agent_brand_partnerships.py` + `agents/python/brand_partnership_prospects.json` (7 researched prospects: Bet9ja, SportyBet, BetKing, Betway Africa, Betika, SportPesa, Hollywoodbets), each with a real affiliate-programme name, contact email/portal found via WebSearch/WebFetch, and a brand-specific "angle" sentence describing exactly where and how we already feature them for free. Pitch is a flat 30% NNCO (new customer only) revenue share ask.
- **Real contact emails vs. dead ends**: got working direct addresses for Bet9ja (`affiliatesupport@bet9ja.com`), Betway Africa (`support@betwaypartnersafrica.com`, `manager@betwaypartnersafrica.com`) and SportPesa (`care@sportpesa.com`, general support only). SportyBet, BetKing and Hollywoodbets only exposed a contact form or an application flow through WebFetch, no direct inbox, likely require actually submitting the form or getting a real address by other means before a bulk send, `run_send()` skips any prospect with an empty `contact_emails` list rather than guessing an address (learned from `agent_email_outreach.py`'s `_guess_contact_email()` = `editor@{domain}` pattern being a low-confidence guess, didn't want to repeat that for a partnership pitch where a wrong guess bounces or looks careless).
- **Hard safety gate pattern for "build it but don't send yet" requests**: default run with no flags is always dry-run/preview, `--test EMAIL --brand X` sends exactly one real email to a human-supplied address without touching prospect state (for review), and `--send` (the real bulk run) refuses outright unless `agents/python/brand_partnership_greenlight.flag` exists, a file this script never creates itself. This is a stronger gate than a `--dry-run`-flag-defaults-to-false pattern since it needs a deliberate, separate file-creation step to ever fire for real, not just remembering to add or omit one flag.
- **Human-voice email pattern that survived a self-review pass**: first draft repeated the same fact twice ("sitting in our bonus tables" stated generically, then the per-brand `angle` field restated "we already run it top of the homepage bonus table"), read like a mail-merge artifact. Fixed by rewriting the whole email to address the brand as "you" throughout instead of third person, and trimming the generic sentence so only the specific `angle` sentence carries the concrete detail. Also rotate between 2 opener/closer phrasings keyed on `sum(ord(c) for c in brand) % 2` so a batch of 7 emails doesn't read as one template with the brand name swapped, worth doing this any time one script sends near-identical emails to multiple real recipients.
- Confirmed (again) that this repo's Stop hook auto-commits and pushes on session end using an allowlist that includes `agents/python/`, this swept my new agent files into an unrelated concurrent session's `deploy: 2026-07-13 13:34 UTC` commit alongside `agent_brand_discovery.py` and translation shard work. Nothing was pushed to `origin` during this session (`ahead 1` locally only), but a future session should check `git log -1` right after finishing work if multiple agents/sessions might be touching this repo at once, the Stop hook doesn't scope commits per-session.

### Errors to Never Repeat (2026-07-17) — brand discovery's first live run flagged 4 real bookmakers as defunct
- First real (non-dry-run) run of `agent_brand_discovery.py` (triggered manually, since the permanent Monday cron hadn't fired yet) added/removed nothing, but the `--verify` phase flagged **4 of the 7 real, definitely-still-operating bookmakers** (Bet9ja, SportyBet, 1xBet Africa, BetKing) as strike-1 suspected-defunct in a single pass. Root cause was two-fold: (1) the run's Groq 70B tier was rate-limited almost immediately, pushing every classification onto the weaker Groq 8B fallback; (2) a genuine Firecrawl timeout on an unrelated candidate that run showed scrape flakiness is real and not rare. Reading the actual evidence text the model returned made the failure modes obvious: SportyBet's "official site is unreachable" was very likely a misread scrape timeout (SportyBet is a large, clearly-active pan-African operator), 1xBet Africa's evidence cited a Uganda closure and a Ukraine regulator action, i.e. news about *other* 1xBet-branded regional entities, not the African brand under review, and BetKing's own evidence sentence said "not a direct confirmation" yet the model still returned `status: suspected_defunct` for it, ignoring its own hedge. Caught this by actually reading `gh run view --log` output line by line after triggering a manual run, not just checking the workflow's green checkmark. **A green CI run is not proof the agent's decisions were correct** — this run "succeeded" in the CI sense while producing bad classifications for 4/7 brands.
- Because removal is two-strike, this was one more noisy weekly run away from wrongly publishing "no longer operating" notices over 4 real bookmaker pages and prepending false "stopped operating" editor's notes to their blog reviews. Cleared all 4 flags from `agents/python/brand_discovery_state.json` immediately (`defunct_flags: {}`) before the next scheduled run could complete the second strike.
- **Permanent fixes in `agent_brand_discovery.py`** (not just "got lucky this time, hope it doesn't happen again"):
  1. `_check_liveness()` now retries the official-site scrape once before concluding "unreachable" — a single Firecrawl timeout is treated as retryable noise, not evidence.
  2. `_LIVENESS_SYSTEM` prompt now explicitly warns that brands like 1xBet/Betwinner/Melbet/22Bet operate as many separate regional entities under one name, and that evidence about a different country's entity doesn't count against the African operator under review.
  3. Added a **deterministic Python-side backstop**, not just a prompt instruction: if the model's own evidence string contains hedge language (`"might be"`, `"not a direct confirmation"`, `"unclear if"`, etc. — see `_HEDGE_PHRASES`), the verdict is forced back to `active` regardless of what `status` field the model returned. This is the same "mechanically validate LLM output, don't just trust the prompt" pattern already used in `_validate_content()` for the content-generation path — a weaker fallback-tier model has now been observed, in production, ignoring an explicit "don't flag hedged evidence" instruction, so the check needed to move from the prompt into code.
- **Separate, lower-severity bug found and fixed in the same pass**: `load_known_brand_names()` only normalized-compared candidate names against each registry entry's `brand_name` field ("1xBet Africa" → `1xbetafrica`), never the `keyword` field ("1xbet"). A discovered candidate "1XBET" normalizes to `1xbet`, which matches the keyword but not the brand_name, so it was never recognized as a duplicate of the already-listed brand and got run through the full research gate as if new (rejected only because of an unrelated African-market-signal miss, not because of the collision). Fixed by unioning both fields into the known-name set.
- **Process lesson on the delivery mechanism, not the agent logic**: the user asked for "a run tomorrow." Scheduled it via a one-time `RemoteTrigger` cloud-agent routine (`run_once_at`) whose prompt was "run `gh workflow run brand_discovery.yml`". The routine's `last_fired_at`/`ended_reason: run_once_fired` showed it fired on time, but `gh run list --workflow=brand_discovery.yml` showed **zero runs ever** — the cloud agent's attempt to invoke `gh` never actually reached GitHub (most likely no GitHub CLI auth in that sandboxed environment; the routine tool gives no run-log visibility to diagnose further). User reported "i didn't get this" days later. Recovered by just running `gh workflow run` directly from the already-authenticated local/session `gh` CLI instead of routing through an unverified cloud-agent hop, and confirmed it worked with `gh run list` immediately after (`in_progress` within seconds). Rule going forward: for "trigger X via `gh`" one-off asks, prefer running `gh` directly from a tool that's already proven authenticated in-session (checked earlier the same session with `gh secret list`/`gh workflow list`) over delegating through a fresh cloud environment whose auth state is unverified and whose execution is not inspectable after the fact. If a cloud-agent routine is used for this kind of task anyway, verify with `gh run list` (or equivalent ground truth) shortly after the scheduled fire time rather than trusting the routine's own "fired successfully" status, since that only confirms the routine's prompt was dispatched, not that its actions inside the sandbox succeeded.

*Last updated: 2026-07-17 by Claude Code*
