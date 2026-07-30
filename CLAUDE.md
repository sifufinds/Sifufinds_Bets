# SifuFinds — Project Instructions

## STANDING RULE — Agent Intelligence & Self-Learning

**Every agent and Claude session must read `AGENT-KNOWLEDGE.md` before starting work and update it after completing significant tasks.**

### On Start (MANDATORY)
- Read `AGENT-KNOWLEDGE.md` in full before any significant task
- Check **"Errors to Never Repeat"** first — do not re-make documented mistakes
- Apply all documented code patterns and market intelligence

### On Completion (MANDATORY)
- Append new learnings to `AGENT-KNOWLEDGE.md` before ending the session
- Capture: bugs fixed, patterns that worked, research findings, market insights, errors avoided
- Date every entry. Keep it specific — exact fix, not just the problem.
- Categories: SEO Learnings · Code Patterns · Market Intelligence · Errors to Never Repeat

### Memory Tools (use proactively)
- `/claude-mem:learn-codebase` — after significant codebase changes
- `/claude-mem:knowledge-agent` — query stored memory before deep research tasks
- `/claude-mem:standup` — summarize what was accomplished across recent sessions
- `/claude-mem:make-plan` — use stored knowledge to plan the next session

### What Counts as a Learning Worth Capturing
- A bug found and fixed (especially if it could recur)
- A generator/code pattern that worked and should be reused
- A research finding that changes content strategy
- A market insight about African betting audiences
- A mistake that caused a deployment issue, blank page, or broken feature
- A tool or command that saved significant time

---

## STANDING RULE — Auto-Retry on Failure

**Any job, run, agent, or task that fails must be automatically retried after 5–15 minutes. No exceptions.**

- GitHub Actions: covered by `workflow_watchdog.yml` (event-driven, 10-min delay) and `retry_failed.yml` (30-min safety net). Both watch all 17 workflows.
- Local tasks / scripts: re-run the failed command after a short wait. If a git push fails, retry up to 3 times before stopping.
- Never leave a failed job unaddressed. If a retry also fails, flag it and keep retrying on schedule.

## STANDING RULE — Always Commit and Push (added 2026-07-24)

**Every code/content change made by Claude Code (or any agent) in this repo must be committed and pushed immediately, without asking the user for confirmation first.** The user has explicitly authorized this — do not wait for a prompt to commit, and do not leave work sitting uncommitted "for review."

- Write a clear commit message per the format in `git-workflow.md` (type: description), stage only the files actually touched, commit, and push to `main` right away.
- This repo also has a separate automated deploy pipeline that periodically commits/pushes on its own (visible as `deploy: <timestamp> UTC` commits in the log) — that pipeline is independent infrastructure, not a substitute for committing your own work the moment it's done. Don't rely on it to pick up your changes; commit them yourself.
- Still follow the existing git-safety rules: never force-push, never skip hooks, never amend a shared commit, and warn before anything destructive — this rule only removes the "ask before every commit/push" step for normal forward changes, it does not authorize destructive git operations.

## STANDING RULE — SEO Health Is Continuously Self-Healing (added 2026-07-05)

**Nothing about SEO health is a one-time fix. Every category below has a permanent, automated guard so it never silently regresses.**

| Category | Guard | Runs |
|---|---|---|
| Google indexability (robots.txt, noindex, Event schema, sitemap/robots conflicts) | `scripts/check_indexability.py --fix` | Pre-deploy gate (blocking) + daily auto-heal + hourly live probe |
| Duplicate blog slugs (silently shadows/overwrites another post's page — see Errors to Never Repeat below) | `dedupe_slugs()` in `gen_blog_post_pages.py` (auto-fixes every run) + `scripts/seo_check.py` (CRITICAL tripwire) | Every `gen_blog_post_pages.py --force` run + pre-deploy gate + daily auto-heal |
| Title/meta length | `scripts/seo_check.py --fix` | Daily auto-heal (`daily_seo_doctor.yml`) |
| Thin content (<1,000 words) / missing FAQ section | `agents/python/agent_content_backfill.py` — expands a batch of legacy posts per run, tracked in `agents/python/content_backfill_state.json` so progress is never lost | Daily (`content_backfill.yml`, 00:15 UTC) |
| AI-hallucinated internal blog links (blog writer invents a `sifufinds.com/<path>` that doesn't exist → `scripts/validate_site.py` CHECK 2 fails → **blocks every deploy** until fixed, as happened 2026-07-09 to 2026-07-12, 3 days with zero new posts reaching the live site) | `sanitize_internal_links()` in `gen_blog_post_pages.py` (auto-strips any markdown link to a `sifufinds.com` path that isn't a real page or `.htaccess` redirect, converting it to plain text — auto-fixes every run) + `SYSTEM_PROMPT` in `agents/python/agent_sports_blog.py` now forbids the writer from emitting internal markdown links at all | Every `gen_blog_post_pages.py --force` run + pre-deploy gate |
| Invalid JSON-LD (manual quote/newline escaping instead of `json.dumps()` silently breaks `<script type="application/ld+json">` — page renders fine, schema is just unparseable to Google/AI crawlers; found 2026-07-19 affecting ~20% of posts, then found again 2026-07-30 still present in 10 of the 11 other page generators — the 2026-07-19 fix only ever landed in `gen_blog_post_pages.py`, this table's claim of a global fix was itself the gap) | All JSON-LD string interpolation in every `gen_*.py`/`generate_*.py` page generator (`gen_blog_post_pages.py`, `gen_all_cities.py`, `gen_bk_reviews.py`, `gen_bonus_pages.py`, `gen_bookmaker_country_pages.py`, `gen_city_pages.py`, `gen_guide_pages.py`, `gen_payment_country_pages.py`, `gen_payment_pages.py`, `gen_sport_country_pages.py`, `generate_country_pages.py`) goes through `json.dumps()`, never manual `.replace('"', '\\"')` and never bare f-string interpolation into a JSON string context | Every generator's own run + `scripts/validate_site.py` CHECK 3 (pre-deploy gate, blocking, parses every `index.html` site-wide — not just blog posts) |
| Wrong/mismatched blog feature images (governing-body/competition tags like FIFA/AFCON/NBA/WAFCON/WSL have no single stable photo across editions/genders; a bare country tag defaults to the men's side with no way to know a post is about a women's tournament; a lone unblocked format word like "test" (cricket) lets a generic tag slip through as a photo-search candidate; accent mismatches silently reject good photo matches leaving only coincidental — sometimes badly wrong — ones; found 2026-07-27 when a Men's FIFA World Ranking post shipped with a FIFA Women's World Cup graphic, and again the same day when a WAFCON post shipped a men's Nigeria squad photo and a Women's T20 World Cup post shipped a men's Test cricket photo) | `_ORG_AND_COMPETITION_WORDS` (now includes `wafcon`/`wsl`/`nwsl`/`uwcl`) / `_COMPETITION_STRUCTURE_WORDS` (now includes `test`) in `scripts/feature_image_tag_filter.py` block org/competition/format tags outright; `qualify_entity_query(name, womens_context=)` + `_gender_mismatch()` in `agents/python/utils/player_photo.py` stop bare country tags resolving to the wrong side, driven by `feature_image_tag_filter._looks_like_womens_context()` scanning the whole post (title+excerpt+tags) so a signal carried by one tag (`WAFCON`) correctly qualifies a *different* candidate tag (`Nigeria`); `_fold_accents()` + `_looks_like_product_shot()` stop accent-mismatches surfacing merchandise photos instead of the actual subject | Every feature-image generation + `scripts/validate_site.py` CHECK 4 (pre-deploy gate, blocking, tag-safety + women's-context regression list) + `scripts/audit_feature_images.py` (manual/periodic live-content heal — not a blocking gate, see AGENT-KNOWLEDGE.md 2026-07-27 entries for why; 31 pre-existing suspects still open as of 2026-07-27, mostly predating this fix — run `--regenerate` and spot-check results) |

**Do not hand-patch an SEO issue and call it done.** If you fix something in this list manually, also check whether the corresponding automated guard caught it — if it didn't, that guard has a bug and needs fixing so the same issue can't recur silently. If a new category of SEO issue is found, add a permanent automated check for it here, in one of the scripts above, and add a row to this table.

## STANDING RULE — Compliance Is Continuously Self-Healing (added 2026-07-30)

**The same "never a one-time fix" principle applies to legal/trust-critical content, not just SEO.** `scripts/compliance_check.py` guards: every blog post carries an 18+/BeGambleAware disclaimer, no page or agent template ships overstated gambling-outcome language ("guaranteed win", "risk-free bet", etc. — deliberately excludes accurate mechanics language like Cash Out's genuine "guaranteed profit before the final leg settles"), masked affiliate links carry `rel="sponsored"` (brand slugs read live from `.htaccess`'s AFFILIATE LINK MASKING block so the check can't drift out of sync), and every active Featured Listings placement declares a transparent `criteria_note`. Runs as a blocking pre-deploy gate step in `deploy_hostinger.yml`, same position as `seo_check.py`. If a new compliance category is found, extend `scripts/compliance_check.py` rather than hand-patching a single page.

## STANDING RULE — Affiliate Link & Banner Integrity Is Continuously Self-Healing (added 2026-07-30)

**The masked-URL affiliate system (`sifufinds.com/<brand>` → real tracking link) and the banner-ad system (`blog/banners.json`) have a permanent, automated guard so they never silently drift or 404.**

`check_and_fix_affiliate_links()` in `agents/python/site_doctor.py` (step 5/6, runs every 15 minutes via `.github/workflows/site_doctor.yml`, same 24/7 cron that already heals live.json/blog pages) checks and auto-heals:

| Issue | Guard behaviour |
|---|---|
| A brand in `BRAND_SLUGS` (`agents/python/utils/affiliate_links.py`) has no matching `RewriteRule` in the `.htaccess` AFFILIATE LINK MASKING block — masked link would 404 | **Not auto-fixed** (no real affiliate URL to guess) — flagged critical in the doctor's log/exit code so a human adds the real tracking URL |
| `.htaccess` has a working masking `RewriteRule` that `BRAND_SLUGS` doesn't know about | Auto-adds the slug to `BRAND_SLUGS` so `masked_url()` and the social-posting agents can reference it |
| Duplicate `RewriteRule` for the same masked slug | Auto-removes the later duplicate, keeps the first |
| `blog/banners.json` entry missing required fields for its type (`raw` needs `raw_html`+`url`; card needs `url`+`bg`+`logo_abbr`) | **Not auto-fixed** (can't safely invent ad copy/creative) — flagged critical |
| `blog/banners-data.js` drifted from `blog/banners.json` | Auto-regenerated from `banners.json` (deterministic mirror, same as `agent_brand_scraper.py`'s `_save_banners()`) |

Fixes are committed by the existing `site_doctor.yml` workflow (its commit step stages `.htaccess` and `agents/python/utils/affiliate_links.py` alongside `data/`/`blog/`) and pushed immediately, then trigger a redeploy the same as every other doctor fix. If you add a new bookmaker's affiliate link or a new raw banner ad by hand, this guard will pick it up on its next 15-minute run — no separate step needed. If a new category of affiliate/banner issue is found, extend `check_and_fix_affiliate_links()` rather than hand-patching, so it can't recur silently.

## Stack
Static HTML site targeting African sports betting markets. Blog posts live in `blog/posts.json`; static pages are generated via `gen_blog_post_pages.py`.

## Blog Post Creation — MANDATORY Research Protocol

**Every time a blog post is created or written**, run the full SEO research workflow below before writing a single word of content. No exceptions.

### Crawl agent is free-first (added 2026-07-18 — do not burn Firecrawl credits)
`agents/python/utils/serp_research.py` is the crawl agent all blog/content agents call for research (`research()`, `fc_search()`, `fc_scrape()`). It runs a **combined free pipeline with no login and no API key**, and never touches Firecrawl/Apify credits automatically:
- **Search**: `html.duckduckgo.com/html` (plain requests + BeautifulSoup, reliable) combined with the `ddgs` library (richer results when it works — it has a known intermittent SSL bug on some Python/LibreSSL builds, non-fatal, silently skipped on failure), deduplicated by URL, ad-click redirects filtered out.
- **Scrape**: `trafilatura` direct-fetch first; if content comes back under 300 chars (JS-rendered/blocked page), falls back to **Jina AI Reader** (`https://r.jina.ai/<url>`, free, no key/login, handles JS rendering).
- **PAA/FAQ hints**: derived locally from the free search snippets (question-pattern extraction) instead of Apify RAG.
- Firecrawl and Apify code paths still exist but are gated behind `SIFU_ALLOW_PAID_CRAWL=1` — unset (the default), they never fire, so a normal research run costs **zero Firecrawl/Apify credits**. Only set that env var deliberately if the free pipeline is genuinely insufficient for a specific run.
- This is handled entirely inside the crawl agent — do not ask for approval per-request to use the free tools, and do not manually reach for the `firecrawl` skill for routine blog/content research now that this exists. Reserve manual Firecrawl skill usage for one-off tasks outside the agent pipeline where the user explicitly wants Firecrawl.

### Step 1 — SERP Recon (free: DuckDuckGo, combined engines)
- Search for the exact target keyword + 2–3 variations
- Capture the top 8–10 organic results (titles, URLs, meta descriptions)
- Note any featured snippets or PAA-style phrasing in the snippets

### Step 2 — Competitor Page Scrape (free: trafilatura + Jina Reader fallback)
- Scrape the top 3–5 ranking pages
- Extract: word count, H2/H3 structure, tables
- Note the average word count — our post must exceed it by at least 20%

### Step 3 — PAA / Content Gaps (free: derived from search snippets)
- Question-pattern hints pulled from the free search snippets surface likely PAA/FAQ targets
- Identify content gaps: topics the top pages cover that our draft doesn't

### Step 4 — Write the Post
Only after completing Steps 1–3, draft the post with:
- **Title tag**: ≤ 60 chars, keyword-first — the `seo_title()` function in `gen_blog_post_pages.py` enforces this automatically
- **Meta description**: ≤ 155 chars, includes keyword + CTA
- **H1**: one static H1 only — matches title intent, includes primary keyword. Never inject H1 via JavaScript only.
- **H2/H3 structure**: mirrors or improves on competitor heading architecture. Never use more than one H1 per page.
- **Word count**: exceeds top-3 average by ≥ 20%, minimum 1,000 words
- **Tables**: include at least one comparison table (odds, bookmakers, methods)
- **FAQs section**: answer the PAA questions found in Step 3 (minimum 3 Q&As)
- **Internal links (auto)**: mention country names (Nigeria, Kenya, Ghana…) and bookmaker names (Bet9ja, SportyBet, Betway, Hollywoodbets, 1xBet, BetKing…) naturally in the body — the generator auto-links the first occurrence to country guides and bookmaker review pages. Also use "betting tips", "live odds", "odds calculator" to trigger core page links.
- **External links (auto)**: mention FIFA, UEFA, AFCON, CAF, Premier League, Champions League, World Cup 2026, NBA, Bundesliga, Serie A, Ligue 1, La Liga, NLRC, BCLB, GCA, WCGRB, BeGambleAware, or Gambling Therapy — the generator auto-links the first mention to the official authority site with `target="_blank" rel="noopener noreferrer"`.
- **Resources box (guaranteed)**: every post gets a "📌 Useful Resources" panel injected automatically after the body. It always contains: up to 2 country page links (from `tags`), 1 bookmaker review link (from `bookmaker_featured`), 1 core page link (tips/odds), 1 external sport-authority link (from `category`), a reference/backlink to [BettingBrainiac — African Betting Sites](https://bettingbrainiac.com/african-betting-sites/), and BeGambleAware. You do not need to add these manually.
- **BettingBrainiac reference (mandatory, guaranteed on every post)**: cite `https://bettingbrainiac.com/african-betting-sites/` as a website reference/backlink on every blog post going forward. This is auto-injected by `build_resources_box()` — no manual action needed, but never remove or override it.
- **Schema**: Article + FAQPage JSON-LD are generated automatically by `gen_blog_post_pages.py` — do not skip the `body` field in `posts.json`
- **CTA**: bookmaker affiliate link with country-specific currency context

### Voice & Language Rules — MANDATORY for Every Post (added 2026-07-12)
Every blog post must read as if written by a real UK-based sports journalist, not an LLM. This applies whether the post is written by a human, Claude, or one of the automated agents (`agent_sports_blog.py`, `agent_content_backfill.py`).

- **UK English throughout**: favourite not favorite, colour not color, organise not organize, side/squad not "team" every time, "boot" not "cleat", "pitch" not "field", "kit" not "jersey", full stops not periods, single quotes as the default. Spell-check every post against UK spelling before publishing.
- **No dashes joining words as an AI tell**: do not use em dashes or en dashes to connect clauses (e.g. "the striker — who scored twice — impressed"). Rewrite as separate sentences, commas, or parentheses instead. This is one of the most obvious AI writing tells and readers/Google both penalise it.
- **Sound human, not generated**: vary sentence length deliberately (mix short punchy sentences with longer ones), avoid formulaic openers ("In the world of...", "When it comes to...", "In today's fast-paced..."), avoid stock transition words used repeatedly ("Furthermore", "Moreover", "Additionally"), avoid symmetrical three-item lists in every paragraph, avoid ending every section with a neat summary sentence. Real football writing has opinions, mild tangents, and rhythm — not uniform paragraph shapes.
- **No AI-detectable patterns**: don't over-hedge ("it could be argued that", "some might say"), don't stack adjectives, don't repeat the exact same sentence structure across FAQ answers, don't use the same 2-3 sentence openers across posts. Read the draft back and cut anything that sounds like a template being filled in.
- **Still 100% accurate**: none of the above licenses inventing facts, scores, transfers, or quotes. Every named event still must come from real research (Steps 1-3). Human-sounding and factually grounded are not in tension.

### GEO (Generative Engine Optimisation) Rules — MANDATORY for Every Post (added 2026-07-12)
Every post must also be structured to get cited by AI answer engines (Google AI Overviews, ChatGPT, Perplexity, Bing Copilot), not just rank in classic SERPs:

- **Answer the core question in the first 2-3 sentences** of the article, in plain, quotable, self-contained language — don't bury the direct answer under scene-setting.
- **Write extractable passages**: each FAQ answer and each key stat/odds callout should stand alone as a complete sentence that makes sense with zero surrounding context, since AI engines lift isolated passages.
- **Use clear declarative statements for facts and numbers** (odds, dates, scorelines) rather than vague qualifiers, so they're easy for a model to cite precisely.
- **Keep the FAQ section genuinely structured** (`## FAQ` heading, one `###`-level question per entry, one direct answer per entry) since this is what both FAQPage schema and AI crawlers parse most reliably.
- **Named-entity precision**: use full correct names for people, teams, and competitions on first mention (e.g. "Jude Bellingham", "World Cup 2026", not "the midfielder" or "the tournament") so entity-matching engines can ground the passage correctly.

### Step 5 — Pre-Publish SEO Checklist
- [ ] Primary keyword in title, H1, first 100 words, and at least 2 H2s
- [ ] Secondary/LSI keywords distributed naturally throughout
- [ ] Word count > top-3 SERP average + 20% (min 1,000 words)
- [ ] At least one comparison table
- [ ] FAQs section answering ≥ 3 PAA questions (use `## FAQ` or `## Frequently Asked Questions` heading)
- [ ] Body text mentions at least 2 country names or bookmaker names so internal auto-linker fires
- [ ] Body text mentions at least 1 authority term (FIFA, UEFA, AFCON, Premier League, NLRC…) so external auto-linker fires
- [ ] After generation, verify resources box present: `grep -c "resources-box" blog/SLUG/index.html` (should be 1)
- [ ] Verify BettingBrainiac backlink present: `grep -c "bettingbrainiac.com/african-betting-sites" blog/SLUG/index.html` (should be ≥ 1)
- [ ] Run `python3 scripts/audit_titles.py` — must exit 0 after page generation
- [ ] Article + FAQPage schema generated automatically — verify with `grep -c "@type.*Article" blog/SLUG/index.html` (should be ≥ 1)
- [ ] Mobile-readable (no wall-of-text paragraphs > 3 sentences)
- [ ] 18+ / Responsible Gambling disclaimer at bottom
- [ ] UK English spelling throughout (favourite, colour, organise…) — no US spellings
- [ ] No em/en dashes joining clauses — rewrite as separate sentences or commas
- [ ] Sentence length varies; no formulaic AI openers or repeated transition words
- [ ] Direct, quotable answer to the core question appears in the first 2-3 sentences (GEO)

### SEO Rules That Apply to Every Page (Not Just Blog Posts)
- **Titles**: always ≤ 60 chars. Use `seo_title()` in every generator. Run `python3 scripts/audit_titles.py` after any generator run — it must exit 0.
- **One H1 per page**: static HTML, never JS-only. Check with `grep -c '<h1' page/index.html` — must be 1.
- **Meta descriptions**: every page needs one, 50–155 chars, keyword + CTA.
- **Sitemaps**: regenerate with `python3 gen_sitemap.py` after adding new pages. The generator uses per-file `os.path.getmtime()` — `lastmod` dates are accurate automatically.
- **shared.js**: NEVER add `defer`. It must stay synchronous at bottom of `<body>`.
- **New pages with bookmakers**: always add `fetchLiveData()` before first render.
- **Internal links auto-generated by**: `COUNTRY_LINKS`, `BOOKMAKER_LINKS`, `TOOL_LINKS`, `CORE_LINKS` in `gen_blog_post_pages.py`. To add a new bookmaker review page: (1) add to `bookmakers/` directory, (2) add entry to `BOOKMAKER_LINKS` and `_BK_SLUG_TO_LINK` in the generator.
- **External links auto-generated by**: `EXTERNAL_LINKS` table + `inject_external_links()` in `gen_blog_post_pages.py`. To add a new authority source: add a tuple to `EXTERNAL_LINKS`.
- **Resources box auto-generated by**: `build_resources_box()` in `gen_blog_post_pages.py`. It uses `_TAG_COUNTRY`, `_BK_SLUG_TO_LINK`, and `_SPORT_ORG` — update those dicts when adding new countries, bookmakers, or sport categories. It also always includes a backlink to `https://bettingbrainiac.com/african-betting-sites/` — do not remove this entry.
- **After any generator change**: always run `python3 gen_blog_post_pages.py --force` to rebuild all 65+ posts with the new logic.
- **No Facebook Pixel placeholders**: if no real Pixel ID exists, remove the `fbq()` init and `fb:app_id` meta entirely.
- **Pre-deploy validator**: run `python3 scripts/validate_site.py` before every commit that adds pages or directories. It must exit 0. It checks: (1) every public git-tracked directory has an `index.html` (prevents 403), (2) all absolute `sifufinds.com/` internal links resolve or have a .htaccess redirect (prevents 404). This also runs automatically on every GitHub deploy and will block the deploy if it fails.

## CRITICAL — Preventing 403 and 404 Errors (MANDATORY)

**Every directory must have an `index.html`.** With `Options -Indexes` in `.htaccess`, any directory without `index.html` returns 403 Forbidden on Apache/Hostinger.

- **When creating a new section directory** (e.g. `betting/esports/`): create `index.html` first, before adding any child pages.
- **When adding a new bookmaker review**: add to `bookmakers/`, add to `BOOKMAKER_LINKS` and `_BK_SLUG_TO_LINK` in the generator, run `--force`.
- **Broken internal links**: the blog post bodies in `posts.json` sometimes contain hardcoded absolute `https://sifufinds.com/SLUG` links that may not resolve. Fix by adding a `Redirect 301 /old-slug /correct/path/` to `.htaccess`. Run the validator after to confirm.
- **Validator command**: `python3 scripts/validate_site.py` — exit 0 = safe, exit 1 = block deploy.

## STANDING RULE — Affiliate Link Masking & CTA Wording (added 2026-07-24)

**Every affiliate link shared on any social platform (Telegram, Facebook, Instagram, X) must be a masked, branded URL wrapped in a CTA — never the raw affiliate tracking URL, and never a bare "click here" or the brand name as the link text.**

- **Masked URL**: `https://sifufinds.com/<brand>` (e.g. `https://sifufinds.com/1xbet`) — clean and trustworthy-looking, no tracking parameters visible. 301-redirects to the real affiliate URL via the `AFFILIATE LINK MASKING` block in `.htaccess`.
- **CTA wording**: one of `BET NOW`, `CLAIM BONUS NOW`, `FREE BETS` — chosen automatically to match the actual offer (no-deposit/free-bet copy → `FREE BETS`; deposit-match/bonus copy → `CLAIM BONUS NOW`; otherwise → `BET NOW`). Never invent a CTA that overstates the offer.
- **Single source of truth**: `agents/python/utils/affiliate_links.py` — `masked_url()`, `pick_cta()`, `cta_html()` (real `<a href>` hyperlink for Telegram's HTML parse mode), `cta_plain()` (`CTA → url` text for platforms that can't render custom anchor text: Facebook captions, X, Instagram).
- **Facebook posts always carry hashtags.** Every `post_facebook()` call site must include hashtags in the message body itself (Graph API doesn't accept a separate hashtags field) — this is enforced in `agent3_social.py`, `agent3_social_telethon.py` (the one actually wired into `agents/python/.github/workflows/agent3_social.yml`), `agent_telegram_offers.py`, `agent_match_post.py`, `agent_casino_post.py`, and `agent_accumulator_post.py`.
- **Adding a new bookmaker brand**: add its slug to `BRAND_SLUGS` in `utils/affiliate_links.py` AND add the matching `RewriteRule ^<slug>/?$ "<real-url>" [R=301,L,NC]` to the `AFFILIATE LINK MASKING` block in `.htaccess` in the same change — the two must stay in sync or the masked link 404s. If an existing brand's affiliate URL changes (e.g. `affiliate` flips from `False` to `True` in `agent_telegram_offers.py`'s `BRANDS`), update its `.htaccess` rule at the same time.
- Do not hand-patch one social agent and call it done — if you touch how affiliate links or CTAs are rendered, check `agent_telegram_offers.py`, `agent_match_post.py` (`build_bookmaker_block`, shared by match/casino/accumulator posts), `agent_casino_post.py`, `agent_accumulator_post.py`, `agent_twitter_posts.py`, and both `agent3_social*.py` files for the same pattern.

## Content Focus
- African betting markets: Nigeria, Kenya, Ghana, South Africa, Tanzania, Uganda, Zambia, Ethiopia, Ivory Coast, Cameroon, Senegal, Rwanda, Zimbabwe, Malawi, Mozambique, Angola, DR Congo, Botswana, Namibia, Egypt, Morocco
- Bookmakers: Bet9ja, SportyBet, Betway, 1xBet, Hollywoodbets, 22Bet, Melbet
- Payment methods: OPay, PalmPay, M-Pesa, MTN MoMo, Airtel Money, EcoCash, bank transfer
- Sports: Football (premier focus), basketball, cricket, tennis, WC2026, AFCON

## CRITICAL — No Stale Matches (MANDATORY for ALL Pages)

**Every match, tip, and odds entry shown on the site must be upcoming or live. Never show already-played matches.**

### Rules
- **Never show a match that has already kicked off by more than 90 minutes** (90-minute grace covers halftime)
- **Never show a `complete: true` match** on the odds or tips pages
- **Always show date AND time** on every tip card and odds match card (e.g. "Today · 20:00 UTC", "Tomorrow · 16:00 UTC", "10 Jun · 15:00 UTC")

### Implementation
Both `tips/index.html` and `odds/index.html` have `_isPastKo(timeStr, graceMins)` and `_parseKoMs(timeStr)` helpers that filter stale matches. `renderTips()` and `renderOdds()` both apply this filter before rendering.

**When updating static fallback data** in `assets/shared.js`:
- `TIPS` array: always use `date: T_TMR` or `date: T_IN2` for upcoming matches — **never `date: T_TODAY` for a match that might already have been played**
- `ODDS_DATA` array: use `time: 'Today · HH:MM UTC'` or `time: 'Tomorrow · HH:MM UTC'` format — the filter parses and removes past entries automatically
- **Never hardcode a `live: true` entry with a fake score** in static data — fake live scores become stale immediately

### Time format conventions
- Today same-day upcoming: `'Today · 20:00 UTC'`
- Tomorrow: `'Tomorrow · 16:00 UTC'`
- Specific future date: `'10 Jun · 15:00 UTC'`
- Never use old `${T_TODAY} HH:MM` template literal format — it doesn't parse correctly

## CRITICAL — Real-Time Live Data (MANDATORY for ALL Pages)

**Every page on SifuFinds is a live comparison site. All pages must always show real-time data.**

### Architecture
- `data/countries_live.json` — live bookmaker offer cache (updated every 5 hours by GitHub Actions)
- `update_countries.py` — scheduled Python updater; run manually with `python3 update_countries.py`
- GitHub Actions: `.github/workflows/update_countries_live.yml` — runs every 5 hours

### Live Data Research Protocol (for manual updates)
Whenever updating `data/countries_live.json` manually, use the free crawl agent (`agents/python/utils/serp_research.py` — `fc_search()` / `fc_scrape()`, see the free-first crawl agent note above):
1. **Search + scrape** bookmaker promo pages (e.g. `bet9ja.com/register`, `1xbet.com/en/promo`) via `fc_scrape()` (trafilatura + Jina Reader fallback, no key/login)
2. **Search** `"best betting sites [Country] 2026 bonus"` via `fc_search()` (DuckDuckGo, no key/login) for top 5 priority countries (NG, KE, ZA, GH, TZ)
3. Update `data/countries_live.json` with verified bonus amounts, `status: "live"`, `source`, and `last_verified` timestamp
4. Firecrawl/Apify are only used if `SIFU_ALLOW_PAID_CRAWL=1` is deliberately set and the free pipeline came back empty — don't reach for them by default

### Page Integration Pattern
All pages use `fetchLiveData()` (or `patchBooksFromLive()`) to patch `BOOKS[code]` before rendering:
- `index.html` — `Promise.all([waitForCountry(), fetchLiveData()])`
- `tips/index.html` — same pattern
- `odds/index.html` — adds `patchBooksFromLive()` to its existing parallel fetch
- `countries/index.html` — full `fetchLiveData()` that also patches `COUNTRY_DATA._liveCount`
- `countries/*/index.html` (23 country pages) — `fetchLiveData().then(init).catch(init)`

When adding ANY new page that renders bookmakers, add `fetchLiveData()` that fetches `data/countries_live.json` and patches the `BOOKS` object before first render.

### Path to `countries_live.json`
- Root pages (`index.html`): `data/countries_live.json`
- One level deep (`tips/`, `odds/`, `blog/`, `countries/`): `../data/countries_live.json`
- Two levels deep (`countries/nigeria/`): `../../data/countries_live.json`

## STANDING RULE — Multi-Source Scraping, Firecrawl-Last (added 2026-07-24)

**No agent may depend on Firecrawl as its primary or only data source. Firecrawl credits are a shared, limited resource (we've run out more than once) — every scraper must try free sources first and only fall back to Firecrawl when free sources genuinely can't get the data.**

This was enforced after `agent_multi_scrape.py` (runs every **15 minutes, 24/7**, 6 sites) and `agent_scrape_tips.py`/`agent_firecrawl_odds.py` were found calling Firecrawl exclusively with zero free fallback — that one 15-min workflow alone was burning ~10 Firecrawl scrapes every 15 minutes (~960/day) before this fix.

### Two free-first pipelines exist — use the right one

| Use case | Module | Fallback behaviour |
|---|---|---|
| Blog/content research (SERP, competitor pages, PAA) — `agent_sports_blog.py`, `agent1_content.py`, `agent_brand_discovery.py` | `agents/python/utils/serp_research.py` (`research()`, `fc_search()`, `fc_scrape()`) | Firecrawl/Apify fallback is **opt-in only** — gated behind `SIFU_ALLOW_PAID_CRAWL=1`. Guarantees zero Firecrawl cost per run unless a human deliberately flips the flag. |
| Live odds/scores/tips scraping — `agent_multi_scrape.py`, `agent_scrape_tips.py`, `agent_firecrawl_odds.py` | `agents/python/utils/free_scrape.py` (`scrape()`) | Firecrawl fires **automatically as a last resort per-URL**, no flag needed — these agents feed live, user-facing data on a 15-min cron, so a hard opt-in gate would silently starve live odds instead of just costing credits. Free layers (trafilatura + Jina Reader) still absorb the large majority of calls. |

Both pipelines follow the same priority order underneath:
1. **Search**: DuckDuckGo (`html.duckduckgo.com/html` + `ddgs` library combined, deduplicated) — free, no key/login.
2. **Scrape**: `trafilatura` direct fetch first; **Jina AI Reader** (`https://r.jina.ai/<url>`, free, no key, renders JS) fallback when content comes back under ~300 chars.
3. **News-specific**: `agents/python/utils/news_fetcher.py` layers DuckDuckGo News → Google News RSS → direct site RSS (BBC Sport, ESPN, Sky Sports, The Guardian, 90min, TalkSport, Mirror Football, Independent Football) for cross-checked, multi-source freshness before any blog post is written. Reuters, Football365, and Goal.com no longer publish public RSS feeds (verified 401/404 as of 2026-07-24) — the four alternatives above cover the same ground and are checked for liveness before being relied on again.
4. **Firecrawl**: last resort only, per the table above.

### Rules for any new/modified scraping agent
- Never call the Firecrawl API/CLI/SDK directly as the first attempt. Route through `utils/free_scrape.py` (live data) or `utils/serp_research.py` (research/content).
- If a target site is JS-heavy (SPA), try Jina Reader before reaching for Firecrawl — it renders JS for free and covers most cases (Sofascore, Flashscore, OddsPortal, Predictz all work through it).
- Never add a new paid scraping/data service. If free + Jina Reader genuinely can't get a site (hard anti-bot wall, login-gated), that is a legitimate case for the existing Firecrawl fallback — don't build a workaround, just let it fall through.
- If you add a new hourly/frequent-cron scraping agent, default it to the `utils/free_scrape.py` pattern (auto Firecrawl fallback, not the opt-in flag) since frequent crons are exactly the credit-burn risk this rule exists to prevent.

## CRITICAL — shared.js Must Never Have `defer`

**NEVER add `defer` to the `<script src="...shared.js...">` tag on any page.**

Every page loads `shared.js` at the bottom of `<body>` just before the inline `init()` call. `defer` causes the browser to execute deferred scripts *after* all inline scripts, so `init()` runs before `shared.js` has loaded — making `waitForCountry`, `BOOKS`, `H()`, and every other shared function undefined. The result is a completely blank page: no bookmakers, no blog posts, no tips, no data of any kind.

- Correct: `<script src="assets/shared.js?v=7"></script>`
- **BROKEN**: `<script src="assets/shared.js?v=7" defer></script>`

`shared.js` is already at the bottom of `<body>` so it does not block above-the-fold rendering. It must remain synchronous. Any SEO or performance audit that suggests adding `defer` here is wrong — do not apply it.

If you ever need to verify: run `grep -r 'shared\.js.*defer' --include="*.html" .` — the result must be empty.

## File Conventions
- Blog posts go in `blog/posts.json` under the `posts` array
- Each post needs: `category`, `title`, `slug`, `excerpt`, `body` (markdown), `author`, `image_color`, `image_icon`, `tags`, `featured`, `bookmaker_featured`, `read_time`, `id`, `published_at`
- After updating `posts.json`, run `python3 gen_blog_post_pages.py` to generate the static HTML files

---

## Research Intelligence — Apply to All Content

### /last30days Skill
Run `/last30days [topic]` before writing ANY blog post, country page, or email campaign to surface what the community is actually saying right now. The skill searches Reddit, X, YouTube, TikTok, Instagram, HN, Polymarket, and GitHub in parallel. Results are stored in `~/Documents/Last30Days/`.

**Setup**: skill is installed at `~/.claude/skills/last30days` (v3.3.2). Keys configured in `~/last30days-skill/skills/last30days/.env`. To unlock X/Twitter: System Settings → Privacy & Security → Full Disk Access → add Terminal.

### Nigeria / Bet9ja Intelligence (last updated June 8 2026)
- **Bet9ja vs SportyBet** is the defining Nigeria betting debate — Bet9ja wins on odds/live markets/African football depth; SportyBet wins on welcome bonus (300% vs 170%), withdrawal speed (<5 min vs 24 hrs), and mobile app UX
- **Bet9ja's #1 weakness**: withdrawal friction — PissedConsumer 3.8 stars (504 reviews), 36% recommend; main complaints are weekend delays, ID verification blocking first withdrawal, bank name mismatches; OPay and PalmPay process fastest
- **Multi-booking is standard**: Nigerian bettors hold accounts on multiple platforms; content should acknowledge this reality
- **WC2026** (June–July 2026): biggest betting moment for the Nigerian market; Bet9ja offers accumulator insurance; Polymarket has Nigeria at 6.8% to draw Portugal
- **Community pulse lives on X/Twitter and TikTok**, not Reddit — always run `/last30days` with X enabled for Nigerian topics
- **Bet9ja X**: @Bet9jaOfficial (primary), @Bet9jaHelp (support)

### Content Tone Rules for African Betting Markets
- Lead with what the community says, not press releases — cite real bettors, real complaints, real wins
- Always include a comparison table when covering bookmakers (Bet9ja vs SportyBet is the evergreen matchup)
- Use local payment method names (OPay, PalmPay, M-Pesa, MTN MoMo) — not generic "e-wallets"
- Currency context is mandatory: ₦ for Nigeria, KSh for Kenya, GH₵ for Ghana, R for South Africa
- 18+ / Responsible Gambling disclaimer at the bottom of every piece — no exceptions
