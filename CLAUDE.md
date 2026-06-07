# SifuFinds — Project Instructions

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

## File Conventions
- Blog posts go in `blog/posts.json` under the `posts` array
- Each post needs: `category`, `title`, `slug`, `excerpt`, `body` (markdown), `author`, `image_color`, `image_icon`, `tags`, `featured`, `bookmaker_featured`, `read_time`, `id`, `published_at`
- After updating `posts.json`, run `python3 gen_blog_post_pages.py` to generate the static HTML files
