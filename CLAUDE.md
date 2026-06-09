# SifuFinds — Project Instructions

## STANDING RULE — Auto-Retry on Failure

**Any job, run, agent, or task that fails must be automatically retried after 5–15 minutes. No exceptions.**

- GitHub Actions: covered by `workflow_watchdog.yml` (event-driven, 10-min delay) and `retry_failed.yml` (30-min safety net). Both watch all 17 workflows.
- Local tasks / scripts: re-run the failed command after a short wait. If a git push fails, retry up to 3 times before stopping.
- Never leave a failed job unaddressed. If a retry also fails, flag it and keep retrying on schedule.

## Stack
Static HTML site targeting African sports betting markets. Blog posts live in `blog/posts.json`; static pages are generated via `gen_blog_post_pages.py`.

## Blog Post Creation — MANDATORY Research Protocol

**Every time a blog post is created or written**, run the full SEO research workflow below using BOTH Firecrawl AND Apify before writing a single word of content. No exceptions.

### Step 1 — SERP Recon with Firecrawl (firecrawl-search)
- Search for the exact target keyword + 2–3 variations
- Capture the top 10 organic results (titles, URLs, meta descriptions)
- Note any featured snippets, PAA boxes, or video carousels

### Step 2 — Competitor Page Scrape with Firecrawl (firecrawl-scrape)
- Scrape the top 5 ranking pages
- Extract: word count, H2/H3 structure, tables, FAQs, schema types used, internal link patterns
- Note the average word count — our post must exceed it by at least 20%

### Step 3 — Deep SERP & Keyword Data with Apify
- Run `apify/rag-web-browser` on the target keyword to surface semantic clusters, LSI terms, and related questions
- Run `apify/google-search-scraper` (or equivalent) to pull "People Also Ask" and related searches for the keyword
- Identify content gaps: topics the top pages cover that our draft doesn't

### Step 4 — Write the Post
Only after completing Steps 1–3, draft the post with:
- **Title tag**: ≤ 60 chars, keyword-first
- **Meta description**: ≤ 155 chars, includes keyword + CTA
- **H1**: matches title intent, includes primary keyword
- **H2/H3 structure**: mirrors or improves on competitor heading architecture
- **Word count**: exceeds top-3 average by ≥ 20%
- **Tables**: include at least one comparison table (odds, bookmakers, methods)
- **FAQs section**: answer the PAA questions found in Step 3
- **Internal links**: 3–5 links to relevant existing SifuFinds pages
- **Schema**: Article + FAQPage JSON-LD
- **CTA**: bookmaker affiliate link with country-specific currency context

### Step 5 — Pre-Publish SEO Checklist
- [ ] Primary keyword in title, H1, first 100 words, and at least 2 H2s
- [ ] Secondary/LSI keywords distributed naturally throughout
- [ ] Word count > top-3 SERP average + 20%
- [ ] At least one table
- [ ] FAQs section answering ≥ 3 PAA questions
- [ ] 3–5 internal links to existing blog posts or country pages
- [ ] Article + FAQPage schema in the HTML
- [ ] Mobile-readable (no wall-of-text paragraphs > 3 sentences)
- [ ] 18+ / Responsible Gambling disclaimer at bottom

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
Whenever updating `data/countries_live.json` manually, ALWAYS use both Firecrawl AND Apify:
1. **Firecrawl scrape** bookmaker promo pages (e.g. `bet9ja.com/register`, `1xbet.com/en/promo`)
2. **Apify `rag-web-browser`** — query `"best betting sites [Country] 2026 bonus"` for top 5 priority countries (NG, KE, ZA, GH, TZ)
3. Update `data/countries_live.json` with verified bonus amounts, `status: "live"`, `source`, and `last_verified` timestamp

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
