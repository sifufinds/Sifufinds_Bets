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

## STANDING RULE — No Paid, Billing-Gated, or Signup/API-Key LLM Fallbacks (added 2026-08-10)

**Every LLM call in this repo must resolve through free, open-source, no-signup, no-API-key tools only, aside from the pre-existing Groq key.** The user explicitly rejected adding an `ANTHROPIC_API_KEY` (or any other paid/keyed fallback) to fix an LLM-reliability gap: "i don't want any of this just free open sources that don't require sign up or API."

- `agents/python/llm.py`'s fallback chain is Groq (already-configured, free-tier, the one pre-existing keyed dependency — not a new one) → g4f (free, open-source, no signup, `github.com/xtekky/gpt4free`) → local Ollama (free, open-weight, no signup). No Claude, Gemini, OpenAI, or any other paid/billing-gated/signup-API tier may be added back as a fallback tier. If all three tiers are exhausted, generation fails loudly (`AIProvidersExhausted`) — that is the accepted tradeoff, not a bug to fix by reaching for a keyed API.
- Do not re-suggest adding a paid API key to solve a future content-pipeline reliability problem in this repo. If Groq + g4f + Ollama genuinely can't cover a case, the fix is a better free/open-source tier (a new g4f provider, a different open-weight Ollama model, smarter tier-ordering like `prefer_accuracy`) — not a new signup-gated dependency.
- This does not apply to `GEMINI_API_KEY`'s unrelated, currently-inactive use in `agents/python/utils/social_image.py` for opt-in AI image generation (`SIFU_ALLOW_AI_IMAGES=1`, never enabled in any workflow as of 2026-08-10) — that's a distinct feature from the LLM text-fallback chain this rule governs. If that feature is ever actually turned on, revisit whether it should be re-scoped under this same no-paid-API policy at that time.
- See AGENT-KNOWLEDGE.md's 2026-08-10 "STANDING POLICY" entry for the full incident history (a 3-day transfer-news content blackout) that led to `llm.py` needing a fallback fix in the first place, and exactly what was removed/kept.

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
| Title/meta length, duplicate `<h1>` (scope gap found 2026-08-11: the length checks only ever read `blog/posts.json`'s `title`/`excerpt` fields — every non-blog template hand-authored its own `<title>`/`<meta name="description">` directly in a Python f-string with zero enforcement, which let all 7 `bookmakers/*/index.html` pages ship 174-293 char descriptions, then ~310 more across every other generator once the guard's scope was actually widened to check the rendered HTML of every page type. Separately, `gen_blog_post_pages.py`'s `markdown_to_html()` rendered a body `# ` line as `<h1>` instead of `<h2>`, producing 2+ `<h1>` tags on 69 of 1209 posts) | `scripts/seo_check.py --fix` (posts.json-sourced, blog only) **+** `scripts/seo_check.py` section 7 (added 2026-08-11 — walks every deployed HTML file directly, checks rendered `<title>`/meta-desc length and `<h1>` count for every page type, not just blog) + `seo_meta.py` (new shared `seo_title()`/`seo_meta_description()` — no ellipsis, clean word-boundary truncation — wired into every `gen_*.py`/`generate_*.py` generator so the fix can't drift out of sync between them the way two separate copies of `seo_title()` already had) | Daily auto-heal (`daily_seo_doctor.yml`) + every generator's own run + pre-deploy gate |
| Thin content (<1,000 words) / missing FAQ section | `agents/python/agent_content_backfill.py` — expands a batch of legacy posts per run, tracked in `agents/python/content_backfill_state.json` so progress is never lost | Daily (`content_backfill.yml`, 00:15 UTC) |
| AI-hallucinated internal blog links (blog writer invents a `sifufinds.com/<path>` that doesn't exist → `scripts/validate_site.py` CHECK 2 fails → **blocks every deploy** until fixed, as happened 2026-07-09 to 2026-07-12, 3 days with zero new posts reaching the live site) | `sanitize_internal_links()` in `gen_blog_post_pages.py` (auto-strips any markdown link to a `sifufinds.com` path that isn't a real page or `.htaccess` redirect, converting it to plain text — auto-fixes every run) + `SYSTEM_PROMPT` in `agents/python/agent_sports_blog.py` now forbids the writer from emitting internal markdown links at all | Every `gen_blog_post_pages.py --force` run + pre-deploy gate |
| Invalid JSON-LD (manual quote/newline escaping instead of `json.dumps()` silently breaks `<script type="application/ld+json">` — page renders fine, schema is just unparseable to Google/AI crawlers; found 2026-07-19 affecting ~20% of posts, then found again 2026-07-30 still present in 10 of the 11 other page generators — the 2026-07-19 fix only ever landed in `gen_blog_post_pages.py`, this table's claim of a global fix was itself the gap) | All JSON-LD string interpolation in every `gen_*.py`/`generate_*.py` page generator (`gen_blog_post_pages.py`, `gen_all_cities.py`, `gen_bk_reviews.py`, `gen_bonus_pages.py`, `gen_bookmaker_country_pages.py`, `gen_city_pages.py`, `gen_guide_pages.py`, `gen_payment_country_pages.py`, `gen_payment_pages.py`, `gen_sport_country_pages.py`, `generate_country_pages.py`, `gen_best_bonus_pages.py`) goes through `json.dumps()`, never manual `.replace('"', '\\"')` and never bare f-string interpolation into a JSON string context | Every generator's own run + `scripts/validate_site.py` CHECK 3 (pre-deploy gate, blocking, parses every `index.html` site-wide — not just blog posts) |
| Wrong/mismatched blog feature images (governing-body/competition tags like FIFA/AFCON/NBA/WAFCON/WSL have no single stable photo across editions/genders; a bare country tag defaults to the men's side with no way to know a post is about a women's tournament; a lone unblocked format word like "test" (cricket) lets a generic tag slip through as a photo-search candidate; accent mismatches silently reject good photo matches leaving only coincidental — sometimes badly wrong — ones; found 2026-07-27 when a Men's FIFA World Ranking post shipped with a FIFA Women's World Cup graphic, and again the same day when a WAFCON post shipped a men's Nigeria squad photo and a Women's T20 World Cup post shipped a men's Test cricket photo) | `_ORG_AND_COMPETITION_WORDS` (now includes `wafcon`/`wsl`/`nwsl`/`uwcl`) / `_COMPETITION_STRUCTURE_WORDS` (now includes `test`) in `scripts/feature_image_tag_filter.py` block org/competition/format tags outright; `qualify_entity_query(name, womens_context=)` + `_gender_mismatch()` in `agents/python/utils/player_photo.py` stop bare country tags resolving to the wrong side, driven by `feature_image_tag_filter._looks_like_womens_context()` scanning the whole post (title+excerpt+tags) so a signal carried by one tag (`WAFCON`) correctly qualifies a *different* candidate tag (`Nigeria`); `_fold_accents()` + `_looks_like_product_shot()` stop accent-mismatches surfacing merchandise photos instead of the actual subject | Every feature-image generation + `scripts/validate_site.py` CHECK 4 (pre-deploy gate, blocking, tag-safety + women's-context regression list) + `scripts/audit_feature_images.py` (manual/periodic live-content heal — not a blocking gate, see AGENT-KNOWLEDGE.md 2026-07-27 entries for why; 31 pre-existing suspects still open as of 2026-07-27, mostly predating this fix — run `--regenerate` and spot-check results) |

| Homepage geo-redirect firing on every visitor unconditionally, including Googlebot's JS-render wave (an unmatched country code or a failed/timed-out `ipapi.co` lookup fell back to redirecting to `/best-betting-in-nigeria/` anyway, contradicting `/`'s own canonical tag and this rule's earlier documented claim that crawlers "never match... and render normally" — found 2026-08-11, that claim was never actually implemented) | `index.html`'s head script only redirects on an actual `MAP[code]` match now; unmatched/failed detection renders the generic homepage in place, same as `waitForCountry()` (`assets/shared.js`) already does on every other page — no user-agent branching (that would be a sneaky-redirect/cloaking pattern, not a fix) | Runs on every homepage load — no separate check script, this is a one-time code fix. If touching this script again, verify with `grep -n 'MAP\[code\]' index.html` that `go(code)` is never called for a code outside `MAP` |
| Missing/incomplete image `alt` text on the LCP-priority element (every blog post's `.post-hero-img` — `fetchpriority="high"`, the page's actual LCP candidate — shipped `alt=""` on all ~900 posts with a feature image) | `gen_blog_post_pages.py`'s hero `<img>` now uses `alt="{html.escape(title)}"` instead of `alt=""` | Every `gen_blog_post_pages.py --force` run |
| Trust/compliance pages with no crawlable URL (Responsible Gambling existed only as content injected into a JS modal — `openPage('responsible')` in `shared.js` — with zero real `<a href>` anywhere site-wide and no sitemap entry, unlike `/about/`, `/contact/`, `/privacy/`, `/terms/` which are all real indexable pages) | `responsible/index.html` (real page, same template as `terms/`/`about/`), added to sitemap via `gen_sitemap.py`'s auto-discovery. `onclick="openPage('responsible')"` switched to real `<a href=".../responsible/">` in all 13 generators that emit it plus every already-generated page site-wide (2026-08-11, same day as the page was added — 0/1539 pages with the old pattern remain) | One-time content fix — no recurring guard. If a new generator ever adds its own "Responsible Gambling" link, it should link to the real page from the start, not reach for `openPage('responsible')` |
| Stale "Updated/Reviewed \<Month Year\>" freshness stamps and `2026`-literal year branding (found 2026-08-16: `MONTH_YEAR = 'June 2026'` was hardcoded in `generate_country_pages.py`/`gen_best_betting_pages.py`, plus a bare `'Updated June 2026.'`/`'Reviewed June 2026'` string in `gen_sport_country_pages.py`, `gen_payment_country_pages.py`, `gen_bookmaker_country_pages.py`, and `gen_bk_reviews.py` — none of it tied to the real date, so every one of the 238 pages these 6 generators produce (plus 3 more via `gen_more_reviews.py`, which reuses `gen_bk_reviews.py`'s template function) was stuck showing "June 2026" two months on, first flagged by the user seeing it on `best-betting-in-kenya/`. Four more hand-authored pages with no generator — `bookmakers/bet9ja/index.html`, `press/index.html`, and two `guides/*/index.html` pages — carried the same hardcoded string with no fix path at all) | `seo_meta.py`'s `current_month_year()`/`current_year()`/`current_iso_date()` are the one shared source of truth; every one of the 6 generators now computes `YEAR`/`MONTH_YEAR` from these at import time instead of a hardcoded literal, and every literal `2026` in a title/H1/H2/meta/OG/Twitter/JSON-LD string in those files was swapped for `{YEAR}` (JSON-LD `datePublished` deliberately excluded — it's a fixed historical fact, not a freshness signal, unlike `dateModified` which now uses `{TODAY_ISO}`). The 4 hand-authored pages got a one-time manual date bump instead (no generator owns them, so they have no self-healing path yet — if any of them is ever migrated into a generator, e.g. `bet9ja` into `gen_bk_reviews.py`'s brand list, this class of bug cannot recur for it; until then a future stale-date sweep needs to check these 4 by hand again) | Daily auto-heal (`daily_seo_doctor.yml`'s new "Refresh freshness dates" step re-runs all 7 generators daily — a no-op except on the day the month/year actually rolls over) + every generator's own run |
| Stale "N African countries" copy after a country is added/removed (found 2026-08-14 after the 23→33 country expansion: a hand-swept fix across ~110 files still missed `assets/shared.js`'s own About-modal text, a stat split across two HTML elements in `about/index.html` and `press/index.html`, two un-wired stat counters in `countries/index.html`, a functional (not just cosmetic) 23-country list in `agents/python/utils/countries.py` that keyword/content agents iterate over, and a completely separate, much older "21 Countries" reference in `index.html` that predated even the 23-country era — proving a manual sweep does not reliably converge on this class of copy) | Three-layer fix, permanent: **(1)** `site_stats.py` (repo root) parses `COUNTRY_DATA` out of `assets/shared.js` live — `total_country_count()` (33, every country incl. restricted markets) and `promotable_country_count()` (28, excludes `restricted:true` markets — use this number for any claim implying commercial bookmaker coverage, never `total_country_count()`, or the claim goes newly false for the 6 countries with zero bookmakers). **(2)** Every generator that emits "N African countries" copy (`gen_bonus_pages.py`, `gen_guide_pages.py`, `gen_payment_pages.py`, `gen_bookmaker_country_pages.py`) imports `TOTAL_COUNTRIES = total_country_count()` and f-string-interpolates it instead of hardcoding a number — re-running the generator after a country is added is enough, no manual sweep needed. `assets/shared.js`'s own `PAGE_CONTENT.about` modal template-literal-interpolates `${Object.keys(COUNTRY_DATA).length}` directly, so it's correct with zero maintenance forever. `countries/index.html`'s two stat counters are computed client-side from `COUNTRY_DATA` in `init()` the same way. **(3)** `scripts/check_country_count.py --fix` (wired into `deploy_hostinger.yml`'s pre-deploy gate, blocking, and `daily_seo_doctor.yml`'s auto-heal) catches everything the first two layers can't reach — hand-authored pages with no generator (`index.html`, `about/`, `press/`, `contact/`, `countries/index.html`, per-bookmaker review pages like `bookmakers/1xbet-africa/index.html`). It only flags a number when "SifuFinds" appears in the same sentence (a bookmaker's own footprint claim like "M-Pesa is used in 7 countries" or "1xBet covers 25 countries" is a different, legitimate fact and must never be touched), and separates safe number-swaps (auto-fixed) from claims that couple the count to a licensing/"available in all" claim (flagged CRITICAL, needs a human reword — see `bookmakers/1xbet-africa/index.html`'s "25 of the 33 African countries SifuFinds covers" fix for the pattern to follow, not a blind number swap) | Pre-deploy gate (blocking) + daily auto-heal + every generator's own run |
| Title/URL claims a topic the content never delivers — specifically, a "transfers" post titled/slugged as an African transfer/club story ("Transfer Frenzy in Africa", "Africa's Top Transfer Stories", a slug like `...-african-clubs-...`) whose body names zero real African country, league, or competition, i.e. it's actually European/global club news mislabelled as African (found 2026-08-16 — user-reported live example: `/blog/transfer-frenzy-in-africa-.../` was entirely about West Ham, Sunderland, Chelsea and Newcastle; a same-day repo-wide audit found 7 more live instances of the identical pattern, some from the original LLM generation and some stale slugs left over from an earlier fact-check correction pass that fixed the title/body but never renamed the URL to match) | `agents/python/utils/title_content_match.py`'s `check_africa_framing()` — deterministic (not LLM-based: the failure is a checkable fact, not a judgement call) regex+word-list check requiring BOTH an explicit "story is African" claim in the title/slug (never triggered by legitimate audience framing like "for African bettors"/"African punters") AND a genuine absence of any real African country name, demonym ("Nigerian striker"), league, or competition anywhere in the body. Wired into `agent_sports_blog.py`'s `generate_post()` as a new gate alongside the existing fact-checker — a violation holds the draft back the same way a fact-check FLAG does (nothing publishable this run, not a crash). `SYSTEM_PROMPT` also hardened with an explicit non-negotiable rule + WRONG/RIGHT example matching this exact incident, so the LLM is instructed not to produce this framing in the first place, not just filtered after the fact. The 8 live posts found in the 2026-08-16 audit were retitled/re-slugged with 301 redirects added to `.htaccess` | `scripts/seo_check.py` section 4c (pre-deploy gate, blocking, scans every post in `blog/posts.json` — catches a violation reaching posts.json through ANY path, not just `agent_sports_blog.py`, e.g. Sanity CMS sync or a manual edit) + `agent_sports_blog.py`'s generation-time gate on every run |

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

## STANDING RULE — AI Agent Team Roadmap (added 2026-07-30, corrected same day after a full re-audit)

The business side of SifuFinds maps to a target org chart (Strategy / SEO & GEO / Content / Product & UX / Data & Monitoring / Technical roles, plus Featured Listings monetization). This table is the single source of truth for which role maps to which script — **check here before assuming a role needs to be built; the first version of this table wrongly listed two already-existing agents as "Phase 2, doesn't exist yet."**

| Role | Status | Fulfilled by |
|---|---|---|
| CMO Agent | ✅ Built Phase 2 | `agents/python/agent5_plan.py` ("Growth Planner" — weekly editorial/social plan from content+SEO+queue state). Was dead code (never scheduled) until `.github/workflows/agent5_plan.yml` was added, weekly Monday 05:00 UTC |
| Affiliate Growth Manager | ✅ Covered | `agent_brand_partnerships.py`'s outreach flow (turns organic bookmaker mentions into 30% NNCO revenue-share deals) |
| Commercial Partnerships Manager | ✅ Covered | `agent_brand_partnerships.py` (outreach) + `--manage-listings`/`--add-listing`/`--remove-listing` (Featured Listings, added Phase 1) |
| Technical SEO Agent | ✅ Covered | `scripts/seo_doctor.py` (daily auto-heal) + `scripts/check_indexability.py` (pre-deploy gate) |
| GEO Optimisation Agent | ✅ Covered | `scripts/geo_check.py` — AI-crawler robots.txt access, llms.txt validity, and more, run via `seo_geo_biweekly.yml` |
| Keyword Research Agent | ✅ Built Phase 2, extended 2026-08-01, made genuinely country-specific 2026-08-08 | `agents/python/agent_keyword_research.py` (evergreen money keywords, resumable batches of seed keywords × all 23 countries via `utils/countries.py` — was only 6 countries via `config.COUNTRIES` until 2026-08-01) + `agents/python/agent_trending_keywords.py` (trending keywords researched PER COUNTRY via `utils/news_fetcher.py`'s `fetch_country_trending()` — a live DuckDuckGo search with the country's own name embedded in the query, plus that country's dedicated local-outlet RSS feed where one exists (Nigeria/Kenya/Ghana/South Africa), pan-African feeds as fallback for the rest. Fixed 2026-08-08: previously fetched ONE shared global topic pool and cycled it across countries via `topics[i % len(topics)]`, so "trending in Kenya" was frequently the exact same story as "trending in Nigeria" — see that module's docstring). Both use `utils/serp_research.py`'s free search, persist to `keyword_opportunities.json`/`trending_keywords.json`, scheduled via `agent_keyword_research.yml`/`agent_trending_keywords.yml` (the latter now covers all 23 countries every run — bumped `BATCH_SIZE` 10→23 and workflow timeout 10→30min, since country-scoped research makes no LLM calls so there's no per-run cost pressure to ration it). Output is fed into `agent5_plan.py`'s weekly editorial-calendar prompt so real keyword gaps drive blog/news/guide topics instead of the LLM inventing them, **and** (2026-08-02) into `agents/python/agent_content_priority.py`, which ranks every unranked gap by country tier × content type into `content_priority_queue.json`. Evergreen gaps feed `agent_priority_writer.py`; trending gaps now feed **`agents/python/agent_country_trending_writer.py`** (new 2026-08-08) — writes a real, country-targeted post grounded in that country's own bookmaker/payment data (`utils/site_data.py`) plus the actual trending story, but ONLY when `utils/story_dedup.py`'s shared covered-story registry shows `breaking_news.yml`'s pan-African pipeline hasn't already covered that exact headline (previously EVERY trending gap was hardcoded `writer_actionable: False` for this reason — now it's conditional, since country-scoped research surfaces stories that pipeline never touches at all). Both writers run in the same `agent_priority_content.yml` loop, every 2 hours, closing the loop from "gap found" to "post published" for both evergreen and trending content |
| Internal Linking Agent | ✅ Covered | `gen_blog_post_pages.py`'s static-table linkers: `COUNTRY_LINKS`/`BOOKMAKER_LINKS`/`TOOL_LINKS`/`CORE_LINKS`/`BONUS_LINKS`/`COMPARISON_LINKS` + `inject_contextual_links()`/`build_resources_box()`/`_pick_news_context_links()` (news→bonus/comparison linking added Phase 1) |
| Schema & Structured Data Agent | ✅ Covered | `json.dumps()`-based JSON-LD generation across every `gen_*.py` generator + `scripts/validate_site.py` CHECK 3 (blocking gate, parses every page's structured data) |
| Sportsbook Review Writer | ⚠️ Covered but fragmented | `agent_brand_reviews.py` — see brand-data duplication note below. (`agent_brand_discovery.py` was removed 2026-08-03 after its defunct-brand verification falsely marked 5 major, definitely-still-operating brands — Bet9ja, SportyBet, Betway Africa, Hollywoodbets, 1xBet Africa — as discontinued on hallucinated/hedged evidence; see AGENT-KNOWLEDGE.md "Errors to Never Repeat") |
| Casino Review Writer | ❌ Missing | `agent_casino_post.py` only writes social/blog posts about casino bonuses, not per-casino review pages |
| Bonus Content Writer | ⚠️ Partially covered 2026-08-02 | `gen_bonus_pages.py` itself is still static/hand-authored, but `agent_priority_writer.py`'s `best_bonus` guide angle now auto-writes blog posts targeting "best betting bonus {country} 2026" keywords — see Keyword Research Agent row |
| Betting Guide Writer | ⚠️ Partially covered 2026-08-02 | `gen_guide_pages.py` itself is still static/hand-authored, but `agent_priority_writer.py` now auto-writes evergreen blog-post guides for `best_sites`/`how_to_bet`/`safest_apps` angles targeting real keyword gaps, grounded in the site's own real per-country bookmaker data (`utils/site_data.py`) rather than a hardcoded brand list — sidesteps the brand-data-consolidation blocker below since it reads `assets/shared.js`'s existing COUNTRY_DATA/BOOKS directly instead of adding a fourth hardcoded brand schema. A dedicated `gen_guide_pages.py`-style templated page type is still missing; this is blog-post-shaped coverage of the same search intent, not a new page type |
| Gambling News Writer | ✅ Covered | `agent_sports_blog.py` (football/basketball/tennis/cricket/rugby/boxing/f1/betting/sportnews categories, scheduled via `breaking_news.yml`) + `agent_transfer_post.py` (dedicated transfer-news feed) |
| Country Localisation Specialist (European Portuguese) | ✅ Built Phase 1 | `agents/python/agent_translate.py --locale pt` |
| Country Localisation Specialist (French) | ✅ Covered | `agents/python/agent_translate.py --locale fr` (France French, not Canadian) — `blog/translations/fr.json` already had 168 manually-populated entries pre-Phase-1, agent now keeps it topped up against posts.json growth |
| Country Localisation Specialist (Spanish) | ✅ Built Phase 1 | `agents/python/agent_translate.py --locale es` (Spain Spanish, not Latin American) — `blog/translations/es.json` had zero entries before Phase 1, hreflang/OG-locale (`es_ES`) plumbing in `gen_blog_post_pages.py` was ready and unused until now |
| Country Localisation Specialist (German) | ✅ Covered | `agents/python/agent_translate.py --locale de` — `blog/translations/de.json` already had 168 manually-populated entries pre-Phase-1, agent now keeps it topped up against posts.json growth |
| Country Localisation Specialist (general) | ✅ Built Phase 1 | `agents/python/agent_translate.py` (generalised across fr/de/es/pt/sw — omit `--locale` to auto-pick whichever has the biggest untranslated backlog) |
| Fact Checker | ✅ Built Phase 1 | `agents/python/agent_fact_checker.py`, wired into `agent_sports_blog.generate_post()` |
| Compliance Reviewer | ✅ Built Phase 1 | `scripts/compliance_check.py`, blocking pre-deploy gate |
| UX Optimisation Agent | ❌ Missing | No agent; needs live GA4/session data as an input first |
| CRO Agent | ❌ Missing | No agent; same GA4 dependency |
| Landing Page Optimisation Agent | ❌ Missing | No agent; same GA4 dependency |
| SERP Monitoring Agent | ✅ Built Phase 2 | `agents/python/agent_serp_monitor.py` — tracks rank position over time for a watchlist of bookmaker-review + evergreen-comparison keywords in `serp_rank_history.json`, flags a REGRESSION (5+ position drop or falls out of top 10) to `serp_regressions.json`, scheduled via `agent_serp_monitor.yml` |
| Competitor Monitoring Agent | ❌ Missing | No agent |
| Affiliate Offer Monitoring Agent | ⚠️ Substantially covered | `agent_brand_scraper.py` — daily scrape verifying/updating live welcome bonuses/promo codes/free bets per brand, confidence-gated writes (`CONFIDENCE_THRESHOLD`), preserves last-known-good value on a failed/suspicious scrape. Scope gap: writes to `brands/data.json`/`blog/banners.json`, doesn't cross-check `bookmakers/<slug>/index.html` review-page copy or `bonuses/` page copy specifically |
| Broken Link & QA Agent | ✅ Covered | `scripts/validate_site.py` (pre-deploy gate) + `agents/python/site_doctor.py` (24/7 live-HTTP auto-heal) |
| Front-end Developer Agent | N/A | Maps to ad hoc Claude Code sessions in this repo, not a cron job |
| Back-end Developer Agent | N/A | Same — no script needed |
| Performance & Core Web Vitals Agent | ✅ Built Phase 2 | `scripts/performance_check.py` — Google PageSpeed Insights API v5 (free, no key required) against 5 representative live pages, checks against this repo's documented CWV targets (LCP<2.5s/CLS<0.1/FCP<1.5s/TBT<200ms as an INP lab-proxy), tracks `data/performance_history.json`. Monitoring check, not a pre-deploy gate (see the script's own docstring for why probing the live site mid-deploy wouldn't be meaningful) — scheduled daily via `performance_check.yml` |

**Phase 2 shipped 2026-07-30**: Keyword Research Agent, SERP Monitoring Agent, and Performance & CWV Agent were all built same-day as Phase 1 — none had a GA4-data or brand-data-consolidation dependency blocking them, matching the priority order this table originally called out. `agent5_plan.py` (CMO Agent) was also wired into a real schedule for the first time. Casino Review Writer / Bonus Content Writer / Betting Guide Writer remain the next priority and were blocked on consolidating brand-fact data first: `gen_bk_reviews.py`, `agent_brand_reviews.py`, and `agent_telegram_offers.py`'s `BRANDS` list each hardcoded their own overlapping schema for the same brands, with `data/bookmaker_links.json` the only real source of truth (link/status metadata only, no review copy). **Phase 1 of the fix shipped 2026-08-11**: `data/bookmakers.json` now exists as that one canonical schema — see the "Sifufinds Testing Database" standing rule below. It is a structural consolidation only (no new research performed); those three writers still need to be repointed at it before this blocker is fully cleared.

**Phase 3 (needs another dependency first)**: UX Optimisation / CRO / Landing Page Optimisation agents (need GA4 data wired in — see the 2026-07-26 GA4/Search Console entry above); Competitor Monitoring Agent; off-page/visual-regression extensions to Broken Link & QA; locale expansion beyond `pt` to `es`/`sw` (same `agent_translate.py`, just point `--locale` at them) and to non-blog pages (country/bonus/guide pages have zero translation infrastructure today, unlike blog posts).

**Featured Listings rendering scope note**: the sponsored badge currently only renders on `bookmakers/<slug>/index.html` pages generated via `bookmaker_page_template.py` (a pure function, safe to extend and test in isolation). Broader placements (`homepage_hero`, listing tables on `index.html`/`countries/*/index.html`) are NOT yet wired up — those pages each define their own inline `fetchLiveData()`-style script rather than sharing logic through `assets/shared.js`, and bookmaker cards have no stable `data-*` attribute to hook a badge onto. Wiring those slots safely needs either touching every page's inline script individually (higher regression risk) or first centralizing bookmaker-card rendering into `shared.js` — treat that as its own prerequisite task, not a quick addition. (A paid "🔥 Top Offers" strip driven by `country_sponsor:<slug>:<position>` listings was built and shipped to all 23 country pages on 2026-08-08, then removed the next day at the user's request in favour of just showing more of the existing organic "⭐ Top Picks" grid — see AGENT-KNOWLEDGE.md for the full story before rebuilding anything similar.)

## STANDING RULE — Sanity CMS Is an Authoring UI, Not a New Rendering Path (added 2026-08-14)

**Sanity exists to give a human editor a nicer place to write blog posts than hand-editing `blog/posts.json`. It does not replace `gen_blog_post_pages.py` or bypass any of its guards.** Added after a same-day incident where 39 stray sync-conflict duplicate files (`blog/fairpari-review/index 2.html` etc. — the classic macOS/iCloud "file already exists" pattern, since this repo lives under `~/Desktop`, which iCloud Drive syncs) had been silently blocking every Hostinger deploy for hours via `audit_titles.py`'s duplicate-`<title>` check. That specific failure had nothing to do with content-authoring tooling — it was fixed by deleting the 39 duplicates (verified zero unique content in each before removal) — but the underlying ask ("stop blogs from failing") was still worth addressing by making authoring less error-prone than hand-editing raw JSON.

### Architecture
This site is static HTML generated by Python, not Next.js — so unlike Sanity's typical "Studio + Next.js app" quickstart, there is no app for Sanity to render through directly. Instead:

1. **`studio-sifu-finds/`** — a Sanity Studio project, deliberately created as a **sibling** folder to this repo (`~/Desktop/studio-sifu-finds/`, alongside `~/Desktop/Sifu Finds/`), not nested inside it. It's a separate Node/TypeScript project with its own git history (currently un-initialized) and is NOT part of this repo. Schema: `studio-sifu-finds/schemaTypes/blogPost.ts` — field-for-field matches what `gen_blog_post_pages.py` consumes (title, slug, excerpt, body-as-plain-markdown, category, author, tags, featured, bookmakerFeatured, readTime, imageColor, imageIcon, publishedAt). Body is deliberately plain markdown, not Portable Text — the site's `markdown_to_html()` already handles FAQ-schema extraction, internal/external auto-linking, and the resources box; Portable Text would mean rebuilding all of that against a different content model for no benefit.
2. **`agents/python/agent_sanity_sync.py`** — the one-way, read-only sync. Queries Sanity's GROQ HTTP API for published `blogPost` documents (`!(_id in path("drafts.**"))` — Sanity's built-in draft/publish workflow means an editor can save a draft without it ever reaching the live site), converts each into the exact dict shape every other content agent produces (mirrors `agent_sports_blog.py`'s post-dict shape), and upserts into `blog/posts.json` via the same `load_posts()`/`save_posts()` pair `agent_sports_blog.py` already uses — inheriting that module's atomic-write-plus-size-sanity-check protection against the 2026-08-09 data-loss class of bug for free, rather than reimplementing JSON I/O. Matching key is a stable synthetic id (`sanity-<sanity-doc-_id>`), so re-running the sync is idempotent (upserts in place, never duplicates) — verified live 2026-08-14 with a throwaway test document (created in Sanity → synced → generated a valid page with correct JSON-LD/resources-box/disclaimer → re-synced with 0 duplication → deleted from Sanity, posts.json, and the generated page as cleanup).
3. Because the sync script's only output is more entries in `blog/posts.json`, **every existing standing rule in this file still applies automatically and unmodified**: `dedupe_slugs()`, `sanitize_internal_links()`, JSON-LD via `json.dumps()`, the resources box + BettingBrainiac backlink, the 18+/BeGambleAware footer, feature-image auto-generation (`ensure_feature_image()`), SEO title/meta length checks, `scripts/validate_site.py`, `scripts/compliance_check.py`. A Sanity-authored post gets zero special treatment or exemption from any of it. It still needs to satisfy `CONTENT-RULEBOOK.md` (word count, real research, no fabricated facts) — the CMS only changes where an editor types, not what's required of the content.

### Running it
```bash
cd agents/python
python3 agent_sanity_sync.py --dry-run       # preview without writing
python3 agent_sanity_sync.py                  # sync into blog/posts.json
python3 agent_sanity_sync.py --then-generate  # sync + run gen_blog_post_pages.py --force in one step
```
No scheduled workflow runs this automatically yet — as of 2026-08-14 it's a manual/on-demand step. If recurring automation is added later (a `sanity_sync.yml` on the same commit-and-push pattern as `content_backfill.yml`), it needs `SANITY_PROJECT_ID`/`SANITY_DATASET`/`SANITY_API_TOKEN` added as GitHub Actions secrets first.

### Credentials
`SANITY_PROJECT_ID` / `SANITY_DATASET` / `SANITY_API_TOKEN` live in **both** `.env` (repo root) and `agents/python/.env` — this repo has two separate gitignored `.env` files (`config.py`'s bare `load_dotenv()` resolves relative to cwd; most individual agents, including this one, explicitly load `Path(__file__).parent / ".env"` from `agents/python/`), so a credential only added to one is invisible to scripts that load the other. Both are gitignored (`.gitignore` covers `.env`, `.env.*`, `*.env`); `.env.example` at the repo root carries placeholders only. The token currently in use has broad (Editor-level, from `sanity login`) permissions since it was also used to scaffold the Studio — a Viewer-scoped token would be more appropriate for a read-only sync script if a dedicated one is issued later.

## STANDING RULE — Sifufinds Testing Database (added 2026-08-11)

**The site's moat is first-hand African betting data, not word count.** Per the Sifufinds Africa-First Ranking Framework (below), a generic "Best Betting Sites in Kenya" page is replaceable by any AI-generated competitor. A verified brand × country table — availability, currency, payment methods, minimum deposit, withdrawal method/time, football markets, licence, Africa Fit score — is not, because it requires either real research per market or real testing, and most competitor affiliate sites do neither.

### `data/bookmakers.json` is the canonical source
Built by `scripts/build_bookmakers_db.py`, keyed `brands.<slug>.countries.<ISO code>`. Re-run the script (it always rebuilds from scratch, never accumulates stale merges) whenever the input sources below change. **Phase 1 (shipped 2026-08-11) is consolidation only** — it merged four previously-overlapping, disagreeing sources into one file and one schema; it did not perform any new research or testing.

| Input | What it contributed |
|---|---|
| `agents/python/agent_brand_reviews.py`'s `BRANDS` (19 brands) | Founded/HQ, global (not per-country) payment/licence/min-deposit claims |
| `agents/python/agent_telegram_offers.py`'s `BRANDS` | Cross-check copy of the above (kept separately since the two lists can drift) |
| `brands/data.json` (`agent_brand_scraper.py` output) | Freshest daily-scraped bonus copy, already confidence-scored |
| `gen_bk_reviews.py`'s `BOOKMAKERS` (3 brands) | The richest source — genuinely country-specific payment lists for its single-country entries (e.g. SportPesa's Kenya-only `M-Pesa, Airtel Money, Equitel, USSD *644#`), not a generalised claim |
| `data/bookmaker_links.json` | Real `official_url` and review-page `status` (the only field this file was ever the source of truth for) |
| `agents/python/utils/affiliate_links.py`'s `BRAND_SLUGS` | Canonical slug for every brand, including the 6 that have an affiliate link but no editorial content yet (fairpari, rasbet, mebet, tictacbet, betxchange, bettabets) |
| `generate_country_pages.py`'s `COUNTRIES` | `countries_reference` block: currency, symbol, regulator, and each country's general online-payment rails (a country fact, never promoted into a per-bookmaker claim) |

### The verification-status model (do not skip this when adding data)
Every fact in the file carries a `status`, on a strict honesty ladder — never skip a rung:
- `not_yet_researched` / `not_tested` — genuinely empty, nobody has checked yet. This is the default and is not a bug to silently fill in with a guess.
- `claimed` — asserted by past editorial content, carried forward, not independently checked in this migration.
- `documented` — carried from research that was genuinely country-specific and unambiguous (a single-country brand's global claim, or `gen_bk_reviews.py`'s per-country payment list). Still not lab-verified.
- `verified` — cross-checked against the operator's own current page + at least one independent source (Section 51 of the rulebook below: primary source + independent source).
- `tested` — an actual SifuFinds first-hand test was performed (registration, deposit, withdrawal timed, etc.) and the result recorded. **Never mark anything `tested` without a real human having done it** — this is rule #21 of the Sifufinds rulebook (no fake reviews) and the single most important honesty constraint on this whole database.

### The single-country vs multi-country rule (why most `payment_methods` fields are still empty)
`build_bookmakers_db.py` only promotes a brand's global claims into a specific country's record when that brand operates in exactly one country — there's no ambiguity about which market a claim describes. For multi-country brands (most of them — e.g. Sportybet's claimed list mixes Nigeria's OPay with Kenya's M-Pesa across 6 countries with one flat array), the claim stays at brand level under `multi_country_claims`, tagged `unverified_multi_country_claim`, and every one of that brand's per-country rows starts genuinely empty. Do not "fix" this by copying the brand-level claim into every country row — that reintroduces exactly the cross-country generalisation error Section 3 and Section 13 of the rulebook below warn against. The correct fix is real per-country research, one market at a time.

### Next steps (not yet built — this is the roadmap, not a promise of completion)
1. **Repoint the writers.** `gen_bk_reviews.py`, `agent_brand_reviews.py`, and `agent_telegram_offers.py` should read from `data/bookmakers.json` instead of their own hardcoded `BRANDS`/`BOOKMAKERS` lists, so a fact only needs updating in one place. Not done yet — this migration only built the target file, it didn't cut over the consumers, precisely to avoid rewiring several live-page generators and a cron-scheduled agent in the same pass as designing the schema.
2. **A real per-country research pass** to move `sportybet`-style multi-country claims from `unverified_multi_country_claim` to genuine per-country `documented`/`verified` rows — starting with whichever country/brand combination is highest-traffic.
3. **A first-hand testing workflow** for the fields that can only ever reach `tested` via an actual human (withdrawal time observed, registration friction, support response quality) — there is currently no tooling for this at all; it needs a human tester and a place to record results, not an agent.
4. Only once real country-level data exists does it make sense to compute `review_scorecard` (Section 10 below) and `africa_fit` (Section 11) scores — both are present in the schema today as `null`-valued skeletons, not fabricated numbers.

## Stack
Static HTML site targeting African sports betting markets. Blog posts live in `blog/posts.json`; static pages are generated via `gen_blog_post_pages.py`.

## Blog Post Creation — MANDATORY Research Protocol

**Read `CONTENT-RULEBOOK.md` in full before writing or substantially editing any blog post, country page, bookmaker review, or comparison page — added 2026-08-11, this is a standing rule, not a one-off read.** It's the SifuFinds Africa-First Ranking Framework: 75 rules on why an article deserves to exist (the Golden Rule test — "what can SifuFinds tell the reader that the next ten Google results cannot?"), honest verification labelling, no thin/duplicated country pages, no fake first-hand-testing claims, the Africa Fit score and review scorecard methodology, and the 10-point pre-publish quality gate. The mechanical SEO checklist below (research steps, title/meta length, schema, internal-linking tables) tells you *how* to execute technically; `CONTENT-RULEBOOK.md` tells you *whether the article is worth writing at all* and governs when the two are in tension — e.g. its Section 44 ("don't write to a word count") supersedes this file's "minimum 1,000 words" line below: satisfy the reader's question fully, don't pad to hit a number.

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

## STANDING RULE — Brands With a Real Affiliate Link Are Always Top-of-List + Featured (added 2026-08-07)

**Every bookmaker in `assets/shared.js`'s `BOOKS` object whose `url` points at a real affiliate-tracking domain (not the brand's own homepage) must sit at the top of its country's array, and be included in `HEADER_BRANDS` (the site-wide "🔥 Featured" bar).** This is a permanent rule, not a one-off cleanup — apply it every time a brand's `url` is changed from a placeholder homepage link to a real tracking link, and every time a new affiliate deal is onboarded.

### Why this is mechanically what "top of list" and "featured" mean on this site
- `BOOKS[cty]` array order **is** the default rank. `sortBooks()` in every `countries/<slug>/index.html` defaults to `s==='default'`, which returns the array as-is — position 1 in the array renders as `#1` on the country page. `renderFeatCards()` in `index.html` takes `BOOKS[cty].slice(0,5)` for the homepage "Featured" cards. There is no separate per-country "featured" flag to set — array position **is** the mechanism.
- `HEADER_BRANDS` (near the bottom of `assets/shared.js`, rendered by `renderBrandsBar()`) is the site-wide "🔥 Featured" bar shown in the header on every page. It is a flat list, not per-country — add any affiliate brand here regardless of which country it targets.
- Known real affiliate-tracking domains currently in use (a brand's `url` matching any of these — not its own `www.brandname.tld` homepage — is what makes it "affiliate-linked"): `reffpa.com`, `refpa3665.com`, `bwredir.com`, `1212fghnna.com`, `combodef.com`, `goaffnk.com`, `trackrt.tictacbets.co.za`, `track.trkbxa.click`, `track.bettapartners.co.za`, `lb-aff.com` (Linebet, added 2026-08-14), `trk.playbet.net` (Playbet, added 2026-08-14). Add new tracking domains to this list as new affiliate networks are onboarded. Note: `assets/shared.js`'s own `AFFILIATE_DOMAINS` array (used by `isAffiliate()` for click-tracking analytics) is the code-level twin of this list and must stay in sync with it — `lb-aff.com` was added here on 2026-08-14 but missed in `AFFILIATE_DOMAINS` until caught and fixed the same day while onboarding Playbet.

### Full checklist when adding or changing any brand's real affiliate link
1. `assets/shared.js` — update the `url` field on that brand's `BOOKS[cty]` entry (this is what the "Claim →" / "Bet Now →" buttons actually link to), then move that entry to the **front** of its country's array (stable: keep existing affiliate brands' relative order, then this one, then the rest as-is — don't reshuffle brands that weren't touched).
2. `assets/shared.js` `HEADER_BRANDS` — add the brand (or move it to the front) so it appears in the "🔥 Featured" header bar.
3. `agents/python/utils/affiliate_links.py` `BRAND_SLUGS` — register the brand's slug so `masked_url()`/social-agent CTAs work.
4. `.htaccess` `AFFILIATE LINK MASKING` block — add the matching `RewriteRule ^<slug>/?$ "<real-affiliate-url>" [R=301,L,NC]`. Must stay in sync with `BRAND_SLUGS` or the masked link 404s.
5. The ABBR→domain map (`assets/shared.js`, ~line 720, e.g. `'BTB':'bettabets.co.za'`) should point at the brand's **own** domain for logo-fetching purposes — never the tracking-redirect domain. Only add/update this if the brand is new; it's unrelated to the affiliate `url` field.
6. Bump `?v=N` on every `shared.js?v=` / `shared.css` reference site-wide (see the 2026-07-31 "Rotating 3-Brand Offer Popup" rule below for the exact file list — currently ~1,487 `.html` files + 7 Python generators) since `shared.js` changed.
7. Re-run `python3 scripts/validate_site.py` and `python3 scripts/compliance_check.py` — both must exit clean before committing.

**Scope note**: this rule reorders a country's bookmaker list by affiliate status only for brands that actually carry a real tracking link — it does not mean every organic (non-affiliate) listing gets pushed down arbitrarily beyond that. When multiple affiliate brands exist in one country, preserve their existing relative order among themselves rather than re-ranking them against each other without a specific reason to.

**This rule applies to `CASINOS` (also in `assets/shared.js`, powers `/casino/`'s "Featured Casino Picks" grid and full listing) the same way it applies to `BOOKS`** — same array-order-is-rank mechanism (`renderFeatCasinos()` in `casino/index.html` takes `CASINOS.slice(0,8)`), same stable affiliate-first partition. `CASINOS` is one flat list, not per-country (there are no per-country `/casino/<slug>/` pages), so there's no `HEADER_BRANDS`-style second list to keep in sync for it. Found 2026-08-08: `CASINOS` had drifted to organic-brands-first (1xBet Casino/Melbet Casino, the only two with real tracking URLs among 8 entries, sitting at positions 5-6, invisible in the old 4-card featured slice) — this was missed in the original 2026-08-07 pass because the rule as first written only named `BOOKS`. Re-check any other flat brand arrays that get the same `.slice(0,N)` "Featured" treatment when auditing this rule in future — `BOOKS`/`HEADER_BRANDS`/`CASINOS` is the known set as of this date, not necessarily exhaustive forever.

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

## STANDING RULE — Geo Homepage Routing (added 2026-07-31, retargeted 2026-08-09)

**Every visitor to the bare `/` URL is routed straight to their own country's page as their homepage.** A visitor detected as Kenya lands on `/best-betting-in-kenya/`, a visitor detected as Ghana lands on `/best-betting-in-ghana/`, and so on for all 23 supported countries — including Nigeria (`/best-betting-in-nigeria/`). This is a client-side redirect (the site is static, no server-side GeoIP available on Hostinger) implemented as an inline `<script>` at the very top of `index.html`'s `<head>` — before `assets/shared.js` loads — so it fires before paint on repeat visits.

**2026-08-09 history**: this rule originally routed to `/countries/<slug>/`. A same-day rename moved that page's content to `/best-bonus-in-<slug>/` (bonus-focused framing) and briefly made *that* the redirect target too, which collapsed two conceptually distinct pages — "the country's general home page" and "the country's bonus comparison page" — into one. Fixed later the same day by restoring the general page as its own distinct page at `/best-betting-in-<slug>/` (via `gen_best_betting_pages.py`, reusing `generate_country_pages.py`'s `COUNTRIES` data) and repointing this redirect there. `/best-bonus-in-<slug>/` (via `generate_country_pages.py`) remains a separate, bonus-focused sibling page — the two cross-link to each other (a "🎁 Best Bonus Sites in {Country}" callout on the betting page, a "{Country} Bonuses" footer link back) but are never the same URL.

### How it works
- Reuses the existing geo-IP infrastructure already in `assets/shared.js` (`ipapi.co`, 2 s timeout, `localStorage['sf_cty']`) rather than duplicating it — the head script sets the exact same `sf_cty` key, so when `shared.js` loads later in `<body>` its own `_geoFetch` IIFE sees `localStorage` already populated and skips a second network call.
- On a **first visit**, the redirect fires after the (capped, ~2 s max) `ipapi.co` lookup resolves. On **every return visit**, it fires instantly from `localStorage` before the page paints.
- Detection failure or an unmapped/non-African country both fall back to the same default the rest of the site already uses (`NG` → `/best-betting-in-nigeria/`) — there is no special-cased "stay on the generic homepage" path; this keeps the contract identical to `waitForCountry()` elsewhere and avoids a first-visit/return-visit behavioural split.
- **Escape hatches** (so internal links and QA aren't broken by the redirect): `?cty=XX` on `/` (the same param the footer's country quick-switch links already use) skips the redirect so the generic pan-African homepage can render with a specific country's data; `?intl=1` forces the generic homepage regardless of detected country.
- The generic `index.html` content itself is unchanged and still renders normally for search-engine crawlers (which almost always resolve to non-African IPs and therefore never match the redirect map) and for anyone using an escape hatch.
- `/countries/<slug>/` (the old pre-2026-08-09 URL) still exists as a noindex redirect-stub + `.htaccess` 301, both now pointing at `/best-betting-in-<slug>/` — kept only because `/countries/<slug>/<city>/` sub-pages still live in that same directory tree and need a non-403 parent.

### Country code → page slug map
Lives inline in `index.html`'s head script (kept intentionally duplicated from `_SUPPORTED_CTYS` in `shared.js` rather than shared, since the whole point is to run *before* `shared.js` loads):
`NG→nigeria, KE→kenya, GH→ghana, ZA→south-africa, TZ→tanzania, UG→uganda, ZM→zambia, ET→ethiopia, CI→ivory-coast, CM→cameroon, SN→senegal, RW→rwanda, ZW→zimbabwe, MW→malawi, MZ→mozambique, AO→angola, CD→dr-congo, BW→botswana, NA→namibia, EG→egypt, MA→morocco, SL→sierra-leone, LR→liberia`

**When adding a new country**: add it to `_SUPPORTED_CTYS` in `shared.js` (as already documented), to `BOOKS`/`COUNTRY_DATA`, to `COUNTRIES` in `generate_country_pages.py` (the single source of truth `gen_best_betting_pages.py` also imports from), generate its `best-betting-in-<slug>/index.html` via `gen_best_betting_pages.py` and its `best-bonus-in-<slug>/index.html` via `generate_country_pages.py`, **and** add the matching `CODE:'slug'` entry to the `MAP` object in `index.html`'s head redirect script — these must all stay in sync or that country's visitors will silently fall through to the Nigeria default instead of their own page.

## STANDING RULE — Rotating 3-Brand Offer Popup (added 2026-07-31)

**Every landing page shows a popup of 3 bookmaker offers after a visitor has been on the page for 30 seconds, and the 3 brands shown are re-shuffled every time so they keep changing.** Implemented once, site-wide, in `assets/shared.js` (`showOfferPopup()` + `_pickRandomOffers()` + `_offerCard()`, styled by `.offer-popup*`/`.op-*` rules in `assets/shared.css`) — not per-page — so it automatically covers every page that loads `shared.js`, including all 23 country homepages, without touching individual page files.

### Behaviour
- `setTimeout(showOfferPopup, 30000)` fires 30 s after `shared.js` parses on any page.
- Shows once per browser tab per session (`sessionStorage['sf_offer_popup_shown']`) — it does not re-fire on every subsequent page navigation within the same tab, to avoid being spammy while still satisfying "30 seconds on a landing page" for a fresh visit.
- Picks the visitor's current country via `getCurrentCountry()`, Fisher-Yates shuffles that country's `BOOKS[cty]` list, and takes the first 3 — a different combination is very likely on the next session/page since most countries carry well over 3 listed bookmakers (exceptions: Ethiopia and DR Congo currently only have 2 bookmakers listed each, so the popup silently does not fire for those two countries until more are added — this is intentional, never show fewer than 3 offers than promised).
- Reuses the site's existing `.fc`/`.fc-img`/`.fc-body`/`.fc-off`/`.gbtn` card markup (the same template `renderFeatCards()` already uses on the homepage) rather than inventing new card markup, and the same `rel="noopener noreferrer sponsored"` + direct `b.url` link convention every other bookmaker card on the site already uses.
- Carries a mandatory 18+/BeGambleAware disclaimer line, consistent with the compliance rule above — do not remove it if this function is ever touched.
- Guards against double-showing over an already-open `#cmp-modal` or `#page-modal`.

### If you touch this
- Don't add a per-page trigger — the whole point is one function in `shared.js` reaching every page. If a new page type needs different behaviour (e.g. no popup at all), gate it inside `showOfferPopup()`, don't duplicate the timer elsewhere.
- If you change the 30 s delay or the once-per-session gating, update `_OFFER_POPUP_DELAY_MS` / `_OFFER_POPUP_SS` in `shared.js`, not a magic number inline.
- Bump the `?v=` query param on `assets/shared.js`/`assets/shared.css` (see below) whenever this function changes, or cached copies on already-visited pages won't pick it up.

### `?v=` cache-busting on `shared.js`/`shared.css` must cover every page
Every page includes `assets/shared.js?v=N` / `assets/shared.css?v=N` so a version bump invalidates cached copies everywhere at once. As of 2026-07-31 this covers **every** HTML page including the 23 `countries/<slug>/index.html` pages and their generator `generate_country_pages.py` — those 23 pages and their generator were previously missing the `?v=` param entirely (found while wiring up this popup, since country pages are now the actual homepage for most visitors and needed the update to land reliably). When bumping the version after any `shared.js`/`shared.css` change: bump it in **every** `.html` file site-wide (currently ~1,470+ files) **and** in every Python generator that hardcodes the tag (`gen_sport_country_pages.py`, `gen_payment_country_pages.py`, `gen_all_cities.py`, `gen_bookmaker_country_pages.py`, `gen_blog_post_pages.py`, `generate_country_pages.py`, `gen_best_betting_pages.py`, `agents/python/utils/bookmaker_page_template.py`) so future regenerated pages don't revert to a stale version number. (`gen_best_bonus_pages.py`, previously listed here, no longer exists as a separate file — its output got folded into `generate_country_pages.py` during the 2026-08-09 rename; `gen_best_betting_pages.py` is its 2026-08-09 sibling/replacement for the general country page.)

## STANDING RULE — Firecrawl Scoped Exclusively to tips/odds/leagues (added 2026-08-09, supersedes the opt-in gate below)

**Firecrawl may only ever be used by the pipelines feeding `sifufinds.com/tips/`, `sifufinds.com/odds/`, and `sifufinds.com/leagues/`. Every other Firecrawl call site in the repo must be permanently disabled, not just defaulted off.**

| Pipeline | Feeds | Firecrawl status |
|---|---|---|
| `agent_scrape_tips.py`, `agent_firecrawl_odds.py`, `agent_multi_scrape.py`, `agent_live_odds.py` (via `agents/python/utils/free_scrape.py`) | tips/odds pages (`data/tips.json`, `data/predictions.json`, `data/live.json`) | **Allowed** — free-first, Firecrawl last-resort per-URL (unchanged) |
| `update_predictions.py` (direct Firecrawl+Apify, no free fallback — see its own workflow comment for why) | tips page (`data/predictions.json`) | **Allowed**, already scoped correctly — feeds the tips page |
| `update_leagues.py` | leagues page (`data/matches_live.json`) | Currently uses FD API + ESPN only, zero Firecrawl calls — **allowed to add Firecrawl here in future** if FD/ESPN ever prove insufficient, not required to |
| Blog/content research — `agent_sports_blog.py`, `agent1_content.py`, `agent_content_backfill.py`, `agent_priority_writer.py`, `agent_country_trending_writer.py`, `agent_trending_keywords.py` (via `agents/python/utils/serp_research.py`) | blog posts, not tips/odds/leagues | **Hard-disabled** — `ALLOW_PAID_CRAWL` is a hardcoded `False` in `serp_research.py`, not env-driven. The old `SIFU_ALLOW_PAID_CRAWL=1` opt-in escape hatch is gone; setting that env var no longer does anything |
| `update_countries.py` (feeds `data/countries_live.json` — homepage, all 23 country pages, etc.) | not tips/odds/leagues | **Disabled** — its `agents/python/utils/free_scrape.py` call now passes `allow_firecrawl=False` (new param on `scrape()`, default `True` for the allowed pipelines above) |

`FIRECRAWL_API_KEY` was also removed from the env blocks of the now-disabled workflows (`agent_priority_content.yml`, `breaking_news.yml`, `content_backfill.yml`, `transfer_news.yml`, `update_countries_live.yml`) so the key isn't sitting unused in jobs that can no longer call it.

**If you add a new scraper that needs a Firecrawl fallback**: it must feed tips, odds, or leagues. Anything else routes through `free_scrape.scrape(..., allow_firecrawl=False)` or `serp_research`'s free-only functions. Do not add a new opt-in env var as a workaround — the point of this rule is that no flag can re-enable it outside the three allowed pipelines.

## STANDING RULE — Multi-Source Scraping, Firecrawl-Last (added 2026-07-24, narrowed 2026-08-09 — see rule above)

**No agent may depend on Firecrawl as its primary or only data source. Firecrawl credits are a shared, limited resource (we've run out more than once) — every scraper must try free sources first and only fall back to Firecrawl when free sources genuinely can't get the data.**

This was enforced after `agent_multi_scrape.py` (runs every **15 minutes, 24/7**, 6 sites) and `agent_scrape_tips.py`/`agent_firecrawl_odds.py` were found calling Firecrawl exclusively with zero free fallback — that one 15-min workflow alone was burning ~10 Firecrawl scrapes every 15 minutes (~960/day) before this fix.

### Two free-first pipelines exist — use the right one

| Use case | Module | Fallback behaviour |
|---|---|---|
| Blog/content research (SERP, competitor pages, PAA) — `agent_sports_blog.py`, `agent1_content.py` | `agents/python/utils/serp_research.py` (`research()`, `fc_search()`, `fc_scrape()`) | Firecrawl/Apify is **hard-disabled** (2026-08-09) — always runs free-only regardless of any env var. See the scope rule above. |
| Live odds/scores/tips scraping — `agent_multi_scrape.py`, `agent_scrape_tips.py`, `agent_firecrawl_odds.py` | `agents/python/utils/free_scrape.py` (`scrape()`, `allow_firecrawl=True` — the default) | Firecrawl fires **automatically as a last resort per-URL**, no flag needed — these agents feed live, user-facing data on a 15-min cron, so a hard opt-in gate would silently starve live odds instead of just costing credits. Free layers (trafilatura + Jina Reader) still absorb the large majority of calls. |
| Anything else calling `free_scrape.scrape()` (e.g. `update_countries.py`) | `agents/python/utils/free_scrape.py` with `allow_firecrawl=False` | Free layers only (trafilatura + Jina Reader) — Firecrawl call is skipped entirely regardless of `FIRECRAWL_API_KEY`. |

Both pipelines follow the same priority order underneath:
1. **Search**: DuckDuckGo (`html.duckduckgo.com/html` + `ddgs` library combined, deduplicated) — free, no key/login.
2. **Scrape**: `trafilatura` direct fetch first; **Jina AI Reader** (`https://r.jina.ai/<url>`, free, no key, renders JS) fallback when content comes back under ~300 chars.
3. **News-specific**: `agents/python/utils/news_fetcher.py` layers DuckDuckGo News → Google News RSS → direct site RSS (BBC Sport, ESPN, Sky Sports, The Guardian, 90min, TalkSport, Mirror Football, Independent Football) for cross-checked, multi-source freshness before any blog post is written. Reuters, Football365, and Goal.com no longer publish public RSS feeds (verified 401/404 as of 2026-07-24) — the four alternatives above cover the same ground and are checked for liveness before being relied on again.
4. **Firecrawl**: last resort only, per the table above, and only for the three allowed pipelines.

### Rules for any new/modified scraping agent
- Never call the Firecrawl API/CLI/SDK directly as the first attempt. Route through `utils/free_scrape.py` (live data) or `utils/serp_research.py` (research/content).
- Firecrawl usage of any kind is scoped to tips/odds/leagues — see the scope rule above before wiring up a new Firecrawl fallback anywhere else.
- If a target site is JS-heavy (SPA), try Jina Reader before reaching for Firecrawl — it renders JS for free and covers most cases (Sofascore, Flashscore, OddsPortal, Predictz all work through it).
- Never add a new paid scraping/data service. If free + Jina Reader genuinely can't get a site (hard anti-bot wall, login-gated) on one of the three allowed pipelines, that is a legitimate case for the existing Firecrawl fallback — don't build a workaround, just let it fall through.
- If you add a new hourly/frequent-cron scraping agent for tips/odds/leagues, default it to the `utils/free_scrape.py` pattern (auto Firecrawl fallback, not an opt-in flag) since frequent crons are exactly the credit-burn risk this rule exists to prevent. For anything else, pass `allow_firecrawl=False`.

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
