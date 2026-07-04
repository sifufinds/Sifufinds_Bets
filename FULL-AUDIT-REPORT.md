# SifuFinds — Full SEO Audit Report
**Date:** 2026-06-15  
**Site:** https://sifufinds.com  
**Auditor:** Claude Code SEO Audit (seo-audit skill)  
**Total Pages Indexed in Sitemaps:** ~636  
**HTML Files on Disk:** 727  

---

## Overall SEO Health Score: **71 / 100**

| Category | Weight | Raw Score | Weighted |
|---|---|---|---|
| Technical SEO | 22% | 68/100 | 15.0 |
| Content Quality | 23% | 75/100 | 17.3 |
| On-Page SEO | 20% | 55/100 | 11.0 |
| Schema / Structured Data | 10% | 78/100 | 7.8 |
| Performance (CWV) | 10% | 77/100 | 7.7 |
| AI Search Readiness | 10% | 82/100 | 8.2 |
| Images | 5% | 80/100 | 4.0 |
| **TOTAL** | **100%** | — | **71.0** |

---

## Executive Summary

SifuFinds is a well-structured, technically solid static site targeting African sports betting markets. The core infrastructure is strong: HTTPS with HSTS preload, HTTP/2, a clean robots.txt, a 7-part sitemap index, robust security headers, and rich schema on every key page. The blog at 360 posts averaging 1,530 words shows serious content investment.

The score is held back by one systemic issue that cascades through the entire site: **557 pages have title tags longer than 60 characters**, severely limiting SERP click-through potential. Several high-traffic pages (homepage, blog index, casino) also lack an H1 tag in static HTML (relying on JS-injected content that crawlers may not index). Fixing these two issues alone could lift the score above 82.

### Top 5 Critical Issues
1. **557 page titles exceed 60 characters** — truncated in SERPs, hurts CTR across nearly every non-blog page
2. **Homepage, blog index, and casino page have no static H1** — JS-rendered H1 is crawl-risky
3. **Facebook Pixel & FB App ID placeholders unfilled** (`YOUR_PIXEL_ID`, `YOUR_FB_APP_ID`) — looks broken to Facebook crawlers
4. **8 blog posts have multiple H1 tags** — confuses crawlers about page topic
5. **Internal linking depth is shallow** — ~360 blog posts each carry only 1 content-deep internal link; Google cannot distribute PageRank efficiently

### Top 5 Quick Wins
1. **Trim 557 titles to ≤60 characters** — pattern-fix via script, high CTR impact
2. **Add static H1 to homepage, blog, and casino HTML** — one line each
3. **Replace Facebook placeholder values** — two-line fix in index.html
4. **Add `dateModified` per-page to sitemaps** using real file mtimes — trivial gen_sitemap.py update
5. **Expand blog internal linking** from 1 → 3–5 per post using related-article logic in gen_blog_post_pages.py

---

## 1. Technical SEO

### Crawlability & Indexability — 9/10
- ✅ robots.txt well-structured: AI crawlers (ChatGPT, Claude, Perplexity) explicitly allowed
- ✅ Rate limits applied to SEO scrapers (Ahrefs, SEMrush: 10s crawl delay) — smart
- ✅ MJ12bot and PetalBot blocked
- ✅ 7-part sitemap index (`sitemap.xml` → 7 child sitemaps, 636 URLs)
- ✅ Preferred host declared (`sifufinds.com` canonical domain)
- ✅ 8 sitemap declarations in robots.txt
- ⚠️ All `lastmod` dates are identical (`2026-06-15`) across 636 URLs — does not reflect actual file modification dates

### HTTP / Server — 9/10
- ✅ HTTP/2 live (`alt-svc: h3` also present — HTTP/3 QUIC enabled)
- ✅ `Cache-Control: public, max-age=300, stale-while-revalidate=86400`
- ✅ Hostinger CDN serving files
- ✅ `Last-Modified` and `ETag` headers present
- ✅ Content-type correctly `text/html`

### Security Headers — 9.5/10
- ✅ `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- ✅ `Content-Security-Policy` (detailed, restricts inline scripts with explicit allowlist)
- ✅ `X-Content-Type-Options: nosniff`
- ✅ `X-XSS-Protection: 1; mode=block`
- ✅ `Referrer-Policy: strict-origin-when-cross-origin`
- ✅ `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()`
- ⚠️ `X-Frame-Options: SAMEORIGIN` — should be `DENY` for a comparison site with no embedded frames
- ⚠️ CSP includes `'unsafe-inline'` in `script-src` — necessary for current architecture but worth moving to nonces long-term

### Canonical Tags — 10/10
- ✅ Every audited page has `rel="canonical"` pointing to its own canonical URL
- ✅ hreflang `en` + `x-default` on homepage

### Redirects — Not tested (no redirect chains detected in header checks)

---

## 2. Content Quality

### Blog — 7.5/10
- ✅ **360 blog posts** — substantial content moat
- ✅ Average word count: **1,530 words** — solid for a comparison niche
- ✅ Zero posts under 600 words
- ⚠️ **26 posts under 1,000 words** — border-line thin for competitive keywords
- ⚠️ **Internal linking depth:** Most posts have only 1 content-level internal link
- ✅ Every post has a `<noscript>` fallback table — good for crawlers
- ⚠️ Some blog post H1s repeat across posts (news-style posts use generic titles)

### Country Pages — 8.5/10
- ✅ **28 country pages + 78 city pages** = 106 location pages
- ✅ Each country page has WebPage + BreadcrumbList + FAQPage schema
- ✅ Per-country payment method and bonus content (non-templated)
- ✅ Sierra Leone (smallest) has 1,633 words — no thin country pages
- ⚠️ City-level pages may be low-content (not fully audited)

### E-E-A-T Signals — 7/10
- ✅ Author named ("Sifu Kai") in schema and meta
- ✅ Advertiser disclosure visible inline
- ✅ 18+ and Responsible Gambling disclaimers on every page
- ✅ Regulatory bodies cited by name (NLRC, BCLB, GCA, WCGRB)
- ⚠️ No visible author bio page
- ⚠️ No "About" page link in main navigation (it's accessible at `/about/` but not nav-linked)
- ⚠️ No editorial review dates visible to users

---

## 3. On-Page SEO

### Title Tags — 3/10 (critical failure)
- ✅ Core pages (homepage, blog, odds, tips, casino, countries) all ≤60 chars — good
- ❌ **557 pages exceed 60 characters** — truncated in Google SERPs
  - Worst offenders: `/bookmakers/1xbet-africa/index.html` at **99 chars**
  - Pattern: `/betting/mtn-momo-betting-sites/south-africa/` at **86 chars**
  - Virtually every bookmaker sub-page and payment-method sub-page is over limit

### H1 Tags — 5/10
- ❌ **Homepage (`/`):** No static H1 in HTML — H1 is JS-injected (`id="hero-h1"`)
- ❌ **Blog index (`/blog/`):** No static H1
- ❌ **Casino page (`/casino/`):** No static H1
- ❌ **Tables page (`/tables/`):** No static H1
- ❌ **8 blog posts have multiple H1 tags** — confuses topic signals
- ✅ Country pages, tips page, odds page have correct H1s in static HTML

### Meta Descriptions — 10/10
- ✅ All core pages have meta descriptions
- ✅ All descriptions within 50–155 characters
- ✅ Keywords naturally included with CTAs ("Updated daily", "Compare", "Free tips")

### Unfilled Placeholders — CRITICAL
- ❌ `fbq('init','YOUR_PIXEL_ID')` in index.html — Facebook Pixel never fires
- ❌ `<meta property="fb:app_id" content="YOUR_FB_APP_ID">` — invalid Open Graph tag

---

## 4. Schema / Structured Data

### Homepage — 9/10
- ✅ `WebSite` with `SearchAction` (Sitelinks Searchbox eligible)
- ✅ `Organization` with logo, areaServed (23 countries), sameAs (7 social profiles)
- ✅ `FAQPage` with 6 well-written Q&As
- ✅ `OnlineBusiness` (note: not a standard Schema.org type — use `LocalBusiness` or just `Organization`)
- ✅ `WebPage` with Speakable specification
- ✅ Breadcrumb on WebPage

### Country Pages — 9/10
- ✅ WebPage + BreadcrumbList + FAQPage schema on every country page
- ✅ Country-specific FAQs (legal status, payment methods, highest bonus)

### Blog Posts — 6/10
- ⚠️ Sample blog post (`world-cup-2026-odds-analysis`) has no Article JSON-LD in static HTML — schema may be JS-rendered
- ⚠️ Without Article schema, posts miss `datePublished`, `author`, `headline` rich result eligibility
- ✅ Blog posts do have strong heading structure (H1, multiple H2, H3)

### Bookmaker Pages — 5/10
- ⚠️ `/bookmakers/1xbet-africa/` and similar pages likely missing `Review` or `ItemList` schema (not individually verified — based on pattern)

---

## 5. Performance (CWV Estimates)

### Assets — 8/10
- ✅ `shared.js`: 217KB raw → **~38.5KB gzipped** (well under 150KB budget)
- ✅ `shared.css`: 30KB raw → **~6.4KB gzipped** (well under 30KB budget)
- ✅ GTM loads `async`
- ✅ Facebook Pixel deferred to `window.load` event
- ✅ `fetchpriority="high"` on logo (above-fold LCP candidate)
- ✅ `content-visibility: auto` on below-fold sections (CLS/INP optimization)
- ✅ `preload` hints for shared.js and shared.css
- ✅ `preconnect` to GTM, GA, and ipapi.co

### Potential Issues
- ⚠️ No font preloads declared — Google Fonts loads via CSS, may delay FCP
- ⚠️ `ipapi.co` geolocation fetch on every page load adds network RTT before personalization renders
- ⚠️ 9 script blocks in `<head>` — GTM inline + FB Pixel inline + 3 JSON-LD blocks before CSS

### HTTP/3 
- ✅ QUIC (`h3=":443"`) advertised — best possible protocol for mobile-first African audience

---

## 6. AI Search Readiness

### Score: 82/100 — Strong
- ✅ `/llms.txt` present and well-structured (site description, content areas, citation guidance)
- ✅ Speakable schema on homepage (`cssSelector: ["h1", "h2", ".hero-headline", ".hero-sub"]`)
- ✅ AI crawlers explicitly allowed in robots.txt: ChatGPT-User, ClaudeBot, PerplexityBot, Googlebot, Bingbot
- ✅ Organization `sameAs` with 7 social profiles — good entity disambiguation
- ✅ `knowsAbout` property in Organization schema (Sports Betting, AFCON, WC2026, etc.)
- ✅ FAQPage schema on homepage and all country pages — high citability
- ⚠️ llms.txt could include update cadence for each content type (currently partial)
- ⚠️ No `/llms-full.txt` with structured Q&A dataset for AI citation training

---

## 7. Sitemap Quality

### Overall: 8/10
| Sitemap | URLs | Freq | Priority |
|---|---|---|---|
| sitemap-core.xml | 8 | hourly/monthly | 0.4–1.0 |
| sitemap-blog.xml | 330 | weekly | 0.8 |
| sitemap-countries.xml | 106 | daily/weekly | 0.75–0.9 |
| sitemap-betting.xml | 174 | weekly | 0.75–0.85 |
| sitemap-guides.xml | 12 | weekly/monthly | 0.7–0.75 |
| sitemap-tips.xml | 1 | — | — |
| sitemap-other.xml | 5 | monthly | 0.6 |

- ✅ Well-organized 7-part index — crawl budget optimized
- ✅ High-priority pages (countries: 0.9, odds: 0.9) signal correctly
- ⚠️ All `lastmod` dates are `2026-06-15` for all 636 URLs — stale/inaccurate
- ⚠️ `sitemap-tips.xml` appears to contain only 1 URL
- ⚠️ No `sitemap-bookmakers.xml` — bookmaker profile pages may not be in any sitemap

---

## 8. Images

### Score: 80/100
- ✅ Homepage: **zero images missing alt text**
- ✅ All images have explicit `width` and `height` attributes (prevents CLS)
- ✅ `loading="lazy"` on below-fold images
- ✅ `loading="eager"` + `fetchpriority="high"` on logo (above-fold)
- ⚠️ OG image (`/assets/og-image.png`) not verified for size optimization
- ⚠️ Logo images in sidebar ads use `loading="lazy"` — correct, since ads appear only on wide viewports

---

## 9. Backlinks

### Score: N/A (no data available)
- Common Crawl 2026-06 index not yet published
- No Moz or Bing API credentials configured
- No Ahrefs/SEMrush integration available
- **Recommendation:** Run a free Moz DA check or configure Bing Webmaster Tools for baseline backlink data

---

## Appendix: Sitemap URL Counts
- Total sitemapped URLs: ~636
- Total HTML files on disk: 727
- Gap (~91 files): Likely includes tools, press, analytics, and some betting sub-pages not in sitemaps

