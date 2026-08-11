# SifuFinds Content & SEO Rulebook

## The SifuFinds Africa-First Ranking Framework

**Version:** 1.0
**Website:** sifufinds.com
**Purpose:** Create original, trustworthy, Africa-focused content that deserves to rank on Google and provides genuine value to readers.

**Read this in full before writing or substantially editing any blog post, country page, bookmaker review, or comparison page.** It sits alongside — and takes priority over — the mechanical SEO checklist in `CLAUDE.md`'s "Blog Post Creation — MANDATORY Research Protocol" section: that section tells you *how* to research and structure a post technically; this file tells you *why* a post deserves to exist at all and what makes it genuinely better than what's already ranking.

---

## 1. The SifuFinds Golden Rule

Every SifuFinds article must answer one question:

> **"What can SifuFinds tell the reader that the next ten Google results cannot?"**

If the answer is nothing, **do not publish the article yet.**

SifuFinds must never exist simply to rewrite information already available online.

Every article should contain something original:

* First-hand testing
* Local African knowledge
* Original comparisons
* Payment-method checks
* Country-specific information
* Original screenshots
* Original data
* Original tables
* Expert commentary
* Editorial scoring
* Personal observations
* Unique betting insights
* Clear explanations of confusing information

Google specifically recommends original information, research and analysis rather than simply rewriting existing sources.

---

## 2. The SifuFinds Content Mission

SifuFinds is not another generic betting affiliate website.

The editorial mission is:

> **Help African bettors find, understand and compare betting sites, bonuses, payment methods, odds and betting information through transparent, practical and locally relevant research.**

Every article must serve an African reader. That means asking:

* What country is this reader in?
* What currency do they use?
* How do they normally deposit?
* How do they withdraw?
* What sports do they follow?
* What local restrictions may apply?
* What would make this bookmaker useful or inconvenient for them?

---

## 3. Africa First, Not Africa as an Afterthought

Never take a generic UK, European or American betting article and simply replace a few words with "Africa."

Every African-focused article should consider South Africa, Nigeria, Kenya, Ghana, Uganda, Tanzania, Botswana, Zambia, Zimbabwe, Rwanda and other relevant African markets — but **never claim that a bookmaker operates in a country without verifying it.**

Do not assume:

* A website accessible from Kenya accepts Kenyan customers.
* A bookmaker supports KES because it accepts Kenya.
* A sportsbook accepts M-Pesa.
* A bookmaker accepts ZAR because South African users can access the site.
* A bonus is available to all African customers.
* A licence in one jurisdiction means the operator is locally licensed everywhere.

When information is uncertain, say:

> **"Check the operator's current terms and registration page before depositing."**

Honesty is more valuable than pretending to know.

---

## 4. Every Article Must Have a Clear Search Intent

Before writing, identify exactly what the user wants. Every article must have one primary intent:

* **Informational** — e.g. "What is a betting exchange?"
* **Commercial investigation** — e.g. "FairPari review"
* **Transactional** — e.g. "FairPari bonus"
* **Navigational** — e.g. "FairPari login"
* **Local/commercial** — e.g. "Best betting sites in Kenya"

Do not try to make one article rank for 50 unrelated search intents. One page should have **one dominant purpose**.

---

## 5. The One-Sentence Search Test

Before writing, complete this sentence:

> **"Someone searching for [keyword] wants to ______."**

Example: *Someone searching for **FairPari review** wants to know whether FairPari is legitimate, useful, safe and worth joining.*

The article must satisfy that need quickly.

---

## 6. The SifuFinds Search Gap Rule

Never begin with "Let's write a 2,000-word article about FairPari."

Begin with: **"What are the current top-ranking pages missing?"**

Research the first page of Google. Record:

* What they cover / don't cover
* What information is outdated or appears copied
* Which questions readers still have
* Which African countries they ignore
* Which payment methods they fail to explain
* Whether they actually tested anything
* Whether their bonus information is current
* Whether they disclose affiliate relationships
* Whether they provide original screenshots
* Whether they have meaningful comparisons

Then build SifuFinds around the gaps.

---

## 7. Never Copy the SERP

Google is not asking for another version of what already exists. SifuFinds must not: rewrite competitors sentence-by-sentence, copy bookmaker descriptions, paraphrase another affiliate site's review, combine several competitor articles into one, copy bonus descriptions, copy operator FAQs, or copy provider descriptions.

Google specifically warns against content that simply stitches together existing sources without adding substantial value.

---

## 8. The 30% Originality Rule

For commercial reviews, aim for at least **30% genuinely original editorial material**. Ideally, much more.

Original material can include: SifuFinds testing, SifuFinds ratings, SifuFinds screenshots, country tables, payment testing, withdrawal observations, betting-market checks, original pros and cons, comparison tables, editorial verdicts, local-market analysis.

Do not treat 30% as a Google requirement — it is a **SifuFinds internal quality threshold**. The goal is not a percentage; the goal is to make the article impossible to replace with a generic AI-generated rewrite.

---

## 9. First-Hand Experience Is a SifuFinds Priority

Whenever possible, test what you write about. For bookmaker reviews, test: registration, country availability, verification, deposit process, payment methods, betting markets, live betting, bonus activation, withdrawal process, customer support, mobile experience.

Record what happened. If something wasn't tested, don't imply that it was. Use labels such as **SifuFinds Tested**, **Verified August 2026**, **Checked on mobile**, **Payment method verified**, **Bonus checked on [date]**.

Google specifically identifies first-hand expertise and explaining how content was produced as useful signals of trust and quality.

---

## 10. SifuFinds Review Scorecard

Every bookmaker review should use a consistent scoring system:

| Category | Weight |
| --- | ---: |
| Sports & Markets | 20% |
| Odds & Betting Experience | 15% |
| Payments | 15% |
| Withdrawals | 15% |
| Bonuses | 10% |
| Mobile Experience | 10% |
| Customer Support | 5% |
| Licensing & Trust | 5% |
| African Market Fit | 5% |

**Total: 100%.** The final rating is calculated from the category scores. Do not give every bookmaker 4.5/5 just because it looks good — ratings must reflect actual differences.

*(This is the exact weighting scheme implemented in `data/bookmakers.json`'s `review_scorecard` field per brand — see the "Sifufinds Testing Database" standing rule in `CLAUDE.md`. Every category is currently `null` pending real per-category testing; do not fill these in from a vibe.)*

---

## 11. Africa Fit Score

SifuFinds' own unique metric — 🌍 **SifuFinds Africa Fit** — rated 1 to 5 based on: African country availability, local currencies, local payment methods, mobile accessibility, African sports coverage, local customer support, local promotions, withdrawal convenience, local regulatory considerations.

Example: **SifuFinds Africa Fit: 4.5/5**

This is much more meaningful for an African reader than a generic "overall rating."

*(Implemented as `africa_fit` per brand-per-country in `data/bookmakers.json`, with the same 9 dimensions as its breakdown. Currently `null`/`not_yet_scored` everywhere — do not compute a score until the underlying per-country facts are actually researched.)*

---

## 12. Country-Specific Information Must Be Verified

For country-specific pages, create a verification table:

| Information | Status |
| --- | --- |
| Country accepted | Verified / Unverified |
| Local currency | Verified / Unverified |
| Deposit method | Verified / Unverified |
| Withdrawal method | Verified / Unverified |
| Local licence | Verified / Unverified |
| Bonus eligibility | Verified / Unverified |
| Minimum deposit | Verified / Unverified |

Never turn "probably" into "yes." If something is unknown: **"Not independently verified. Check the operator directly before depositing."**

*(`data/bookmakers.json` implements a five-rung version of this — `not_yet_researched` / `not_tested` → `claimed` → `documented` → `verified` → `tested` — see `CLAUDE.md`. Use that exact ladder, not a binary verified/unverified flag, when writing or updating a fact in that file.)*

---

## 13. Payment Methods Are a Core SEO Differentiator

Generic affiliate sites say "FairPari supports several payment methods." SifuFinds goes further — explain what actually matters to African readers, per country:

* **South Africa**: ZAR, EFT, bank cards, local banking options, crypto, e-wallets
* **Kenya**: KES, M-Pesa, Airtel Money, cards, e-wallets, crypto
* **Nigeria**: NGN, bank transfer, cards, local payment providers, e-wallets, crypto
* **Ghana**: GHS, Mobile Money, cards, bank transfer
* **Other markets**: research the payment methods actually relevant to that country

**Never claim a payment method is supported without verification.**

---

## 14. Don't Just Review the Bonus

A bonus should never dominate the article. For every bonus, explain: amount, minimum deposit, wagering requirement, minimum odds, maximum stake, maximum winnings, expiry, eligible markets, eligible games, country restrictions, withdrawal conditions.

Then answer: **"Is this actually a good bonus?"** — that is the useful part.

---

## 15. Never Use a Bonus as the Only CTA

Don't write "Get €1,000 now!" Instead: **"Check the current FairPari offer and read the terms before depositing."**

The CTA must encourage an informed decision. This keeps SifuFinds editorial rather than looking like a bonus-selling website.

---

## 16. Every Commercial Article Needs a Verdict

Never finish with "Overall, FairPari is a great betting site." Instead answer: Who is it good for? Who should avoid it? What is its biggest strength? What is its biggest weakness? What should readers check before signing up? Which African country is it best suited to? Is there a better alternative?

The verdict must be useful even if the reader never clicks the affiliate link.

---

## 17. SifuFinds Must Be Willing to Say No

A bookmaker doesn't have to receive a positive review. If payment options are poor, say it. If withdrawals are slow, say it. If the bonus isn't competitive, say it. If local availability is unclear, say it. Trust compounds.

---

## 18. Authorship Must Be Clear

Every substantial article should have: author, author bio, publication date, last updated date, review methodology, relevant expertise, affiliate disclosure.

Example: **Written by SifuFinds Editorial Team. Reviewed by [Name], Betting & iGaming Editor. Last verified: 11 August 2026.**

---

## 19. Add a "How We Review" Section

Every major commercial page should link to a permanent **How SifuFinds Reviews Betting Sites** page explaining: what you test, how you score, how often you update, how you verify bonuses/payment methods, how you assess withdrawals, how licensing is checked, how affiliate relationships work.

---

## 20. Affiliate Disclosure Must Be Transparent

Example: **"Affiliate disclosure: SifuFinds may receive a commission if you register or make a qualifying transaction through some links on this page. This does not influence our editorial rating or review."**

Do not hide the disclosure at the bottom of a 3,000-word article. Put it where readers can see it.

---

## 21. No Fake Reviews

Never claim "We deposited €500 and withdrew €1,200" unless somebody actually did it. Never invent withdrawal times, support conversations, payment tests, betting results, account experiences, screenshots, bonuses, or customer service experiences. **If you haven't tested it, say you haven't tested it.**

This is the single most important rule when populating `data/bookmakers.json` — never mark a field `tested` without a real human having done it.

---

## 22. Screenshots Are Evidence

Where practical, include original screenshots (registration, betting interface, bonus, payment methods, withdrawal page, mobile interface, country selector, account verification, customer support), not decoration. Every screenshot should answer a question and carry a descriptive caption.

---

## 23. Use Original Tables

Tables for bookmaker comparisons, payment methods, country availability, currencies, bonus terms, sports coverage, withdrawal times, minimum deposits, betting limits, licensing. Tables should contain useful information, not keyword stuffing.

---

## 24. Primary Keyword Rule

One primary keyword per article, appearing naturally in: SEO title, H1, introduction, one or more relevant H2s, meta description, URL where appropriate, image alt text where genuinely descriptive. Don't force it into every paragraph.

---

## 25. Secondary Keywords Should Be Topics, Not Repetitions

Instead of repeating "FairPari review," cover related concepts: FairPari bonus, FairPari withdrawal, FairPari payment methods, FairPari sports betting, FairPari casino, FairPari mobile betting, Is FairPari legit?, FairPari Kenya, FairPari South Africa.

---

## 26. Never Keyword Stuff

Bad: *"FairPari review is a FairPari sportsbook review of the FairPari sportsbook. In this FairPari review, we review FairPari betting..."*

Good: *"FairPari combines sports betting, live markets and casino gaming in one account. For African bettors, however, payment options and country availability are more important than the headline welcome bonus."*

Write naturally.

---

## 27. H1 Rule

One H1 only. Example: **FairPari Review 2026: Bonus, Sports Betting, Casino & Payments.** Don't stack keywords in the H1.

---

## 28. Introduction Rule

The first 100 words must answer: What is this? Who is it for? What will the reader learn? What makes SifuFinds different? Don't waste it on "Online betting has become increasingly popular..." — start with the answer.

---

## 29. The 30-Second Test

A reader should understand within 30 seconds: what the bookmaker is, whether it is relevant to them, our rating, main strengths, main weakness, whether it is available in their country, where to check the current offer. If they have to scroll through 1,000 words to discover this, the article fails.

---

## 30. Use the "Answer First" Format

For important questions, e.g. **Is FairPari legit?** — **Short answer:** FairPari operates under a Curaçao gaming licence, but players should check the regulatory requirements and availability that apply in their country. Then explain.

---

## 31. Every Article Should Have a Content Map

For long articles, include a table of contents: Quick verdict, Key facts, Bonus, Sportsbook, Live betting, Casino, Payments, Withdrawals, Country availability, Safety & licensing, Mobile experience, Pros & cons, Alternatives, Final verdict, FAQ.

---

## 32. Use FAQs for Real Questions

Don't create FAQs purely for SEO. Use questions people genuinely ask (Is FairPari legit? Is FairPari available in Kenya? Can I use M-Pesa? Can I withdraw in KES? Does FairPari accept South African players? What is the FairPari bonus? How long do FairPari withdrawals take?) and answer them clearly.

---

## 33. Don't Abuse FAQ Schema

Only use structured data where the content is genuinely visible and eligible. Never create hidden FAQ content purely to gain search visibility.

---

## 34. Internal Links Must Have a Purpose

Every article should contain relevant internal links, but don't force 30 links into a page. Every link should help the reader continue their research.

---

## 35. Use Descriptive Anchor Text

Bad: "Click here" / "Read more." Good: "best betting sites in Kenya" / "our FairPari payment methods guide." Anchor text should tell the reader what they'll find.

---

## 36. Build Topical Clusters

Don't publish random articles — build content hubs. Example: FairPari Review (pillar) with supporting articles for Bonus, Promo Code, Withdrawal, Payment Methods, Login, Casino, Sports Betting, Mobile, South Africa, Kenya, Nigeria — connected naturally.

---

## 37. Country Hubs Are Critical for SifuFinds

Build country authority: Best Betting Sites, Betting Bonuses, Football Betting, Live Betting, Mobile Betting, and per-brand reviews, per country. Repeat for Nigeria, Kenya, Ghana, Uganda, Tanzania, Botswana, Zambia, Zimbabwe, Rwanda — but only build pages where meaningful country-specific information actually exists.

---

## 38. Don't Create 20 Country Pages With the Same Text

**Extremely important.** Never take "FairPari Review South Africa" and swap the country name for Kenya, Nigeria, Ghana, Uganda — that creates thin, repetitive pages. Every country article needs unique currency, payment methods, local regulation, availability, local betting preferences, local sports, country-specific bonus eligibility, withdrawal options, local alternatives.

Google explicitly warns against scaled content that produces many low-value pages and thin affiliate content that merely reproduces merchant information.

---

## 39. Every Country Page Needs a Local Angle

Don't write "FairPari Kenya Review" and talk about FairPari generally. Write "FairPari Kenya Review: M-Pesa, KES, Bonus & Withdrawal Guide" and actually investigate Kenya eligibility, KES, M-Pesa, Airtel Money, Kenyan betting regulations, football interests, local alternatives.

---

## 40. Competitor Comparisons Must Be Fair

Compare the same criteria for both sides (sports, football, live betting, bonus, payments, withdrawal, mobile, casino, African availability, overall). Never manipulate a comparison because one company pays a higher affiliate commission.

---

## 41. Never Rank a Bookmaker Based on Commission

The editorial ranking must be independent of affiliate payout. The user comes first.

---

## 42. Affiliate Links Should Be Contextual

Don't put affiliate buttons after every paragraph. Recommended: 1 CTA near the top, 1 after the main evaluation, 1 near the conclusion. Additional links only where useful.

---

## 43. CTA Must Match Search Intent

Review → "Check FairPari's latest offer." Bonus article → "Claim the current FairPari bonus." Comparison → "Compare FairPari and Betway." Country page → "See the best betting sites available in Kenya." Don't use the same CTA everywhere.

---

## 44. Don't Write to a Word Count

SifuFinds has **no rule** saying every article must be 2,500 words. Write until the user's question has been properly answered. A useful 1,200-word article beats a 4,000-word article full of repetition. Google explicitly states it has no preferred word count. (This supersedes the "minimum 1,000 words" line in `CLAUDE.md`'s mechanical checklist where the two are in tension — satisfy the reader's question fully; do not pad to hit a number.)

---

## 45. Every Paragraph Must Earn Its Place

During editing ask: "Would the reader miss anything if this paragraph disappeared?" If no, delete it.

---

## 46. Short Paragraphs

1–4 sentences, clear headings, bullets, tables, short explanations. Avoid enormous blocks of text.

---

## 47. Write Like a Human

Confident, friendly, direct, knowledgeable, African, practical, honest. Avoid "In today's rapidly evolving digital landscape...", "It is worth noting that...", "Whether you are a seasoned bettor or a complete beginner..." and repetitive AI-style introductions.

---

## 48. Use UK English

favourite, licence, organisation, optimise, centre, programme. Do not randomly switch between US and UK spelling. (Matches `CLAUDE.md`'s existing "Voice & Language Rules" section — this is the same requirement, restated here for completeness.)

---

## 49. Never Use Fake Authority

Don't write "Our experts tested 100 bookmakers" unless SifuFinds actually did. Don't say "According to our research" unless research was genuinely conducted. Don't claim "SifuFinds recommends" unless the editorial team actually reviewed the product. Trust is more valuable than impressive-sounding copy.

---

## 50. Source Important Facts

Cite licensing, regulations, gambling laws, bonus terms, payment information, operator ownership, official statistics, major product claims. Prefer primary sources:

* Licensing: **Regulator > operator > reputable industry source > affiliate site**
* Bonuses: **Operator's current terms > third-party source**
* Laws: **Government/regulator > news site > blog**

---

## 51. Don't Trust One Source

For important commercial claims, aim for **primary source + independent source**. Example: FairPari licence = Curaçao Gaming Control Board + independent review. This makes the article more reliable.

---

## 52. Date-Sensitive Information Must Have a Date

Bonuses, promotions, payment methods, licensing, country availability, odds, minimum deposits, withdrawal times — include "Last checked: August 2026" or "Verified: 11 August 2026."

---

## 53. Update Content, Don't Just Change the Date

Never change "Updated: 2026" if the content hasn't actually been reviewed. Google specifically warns against changing dates merely to make pages appear fresh when the content hasn't substantially changed. When updating: recheck bonus, payment methods, licence, availability, screenshots, links, rankings, facts — then update the date.

---

## 54. Create an Update Log

For major pages: **Last updated: 11 August 2026. What changed: Updated FairPari payment methods, bonus information and country availability.** This builds transparency.

---

## 55. Images Must Add Value

Don't use random stock photos. For bookmaker reviews, prioritise original screenshots (interface, mobile, payment options, bonus page, country selector, sports markets, original comparison graphics). Alt text should describe the image naturally — not "FairPari review FairPari bonus FairPari betting FairPari casino" but "FairPari sportsbook football betting interface on mobile."

---

## 56. Don't Hide Important Information Below Ads

The reader should see the answer before popups, affiliate banners, newsletter boxes, sticky ads, casino promotions. Google recommends an overall good page experience.

---

## 57. Mobile First

Before publishing, check: does the table fit? Are buttons easy to click? Are paragraphs readable? Are images compressed? Is the CTA obvious? Does the page load quickly? Are ads covering the content? Most SifuFinds readers discover content on mobile.

---

## 58. Technical SEO Check

One H1, SEO title, meta description, clean URL, canonical URL, indexable page, internal links, relevant external references, descriptive image alt text, mobile-friendly layout, fast loading, breadcrumbs where appropriate, XML sitemap inclusion, no accidental noindex, no broken links. (Enforced mechanically today by `scripts/seo_check.py`, `scripts/check_indexability.py`, `scripts/validate_site.py` — see `CLAUDE.md`'s SEO standing rule table.)

---

## 59. Title Rule

**Brand/topic + intent + useful differentiator + year where relevant.** Example: "FairPari Review 2026: Bonus, Payments, Sports Betting & Safety." Better for Africa: "FairPari Africa Review 2026: Bonus, Payments & Country Availability." Avoid exaggerated or misleading clickbait titles.

---

## 60. Meta Description Rule

Sell the **answer**, not simply repeat the title. Example: "FairPari review for African bettors covering sports betting, bonuses, payment methods, withdrawals, country availability, licensing and mobile betting."

---

## 61. URL Rule

Short, descriptive, lowercase, permanent, easy to understand. Good: `/fairpari-review/`. Bad: `/best-online-betting-site-fairpari-review-bonus-casino-africa-2026/`.

---

## 62. Don't Change URLs Without a Reason

URLs should be stable. If a URL must change, implement a permanent redirect and update internal links. (Matches `CLAUDE.md`'s "no stale/broken internal links" and `.htaccess` redirect conventions.)

---

## 63. Content Should Be Built for Search + AI

Structure content so search systems and AI answer engines can easily understand who/what/where/when/why/how: answer questions clearly, use structured headings, give direct answers, provide original data, show evidence, explain methodology. (Matches `CLAUDE.md`'s existing GEO rules section.)

---

## 64. SifuFinds "First-Hand Proof" Rule

Whenever SifuFinds tests something, show proof: "Tested: FairPari mobile registration." "Checked: FairPari cashier." "Tested: Customer support." "Verified: FairPari licence." "Checked: Bonus terms." This is the major differentiator between SifuFinds and mass-produced affiliate websites.

---

## 65. AI Can Assist, But AI Cannot Be the Editor

AI may help with research organisation, outlines, keyword clustering, first drafts, grammar, content gaps, formatting, FAQs — but AI must never be the final authority. Human editorial review is mandatory. Every AI-assisted article must be checked for facts, sources, dates, country information, payment methods, legal claims, bonus terms, originality, tone, repetition.

Using AI to mass-produce low-value pages for search manipulation falls under scaled content abuse — this repo's own standing rule against "no mass-produced country pages" (rule 67 below) exists specifically to prevent that.

---

## 66. The "No AI Sludge" Rule

Delete phrases such as: "In today's digital landscape," "In the ever-evolving world," "Whether you're a seasoned...," "It's important to note," "Let's dive in," "At the end of the day," "A game-changer," "Seamless experience," "Robust platform," "Cutting-edge," "In conclusion" — unless genuinely appropriate. SifuFinds should sound like an experienced editor talking to a real bettor. (Matches `CLAUDE.md`'s existing "no formulaic AI openers" voice rule.)

---

## 67. No Mass-Produced Country Pages

Never generate 50 countries × 10 bookmakers × 2,000 words just because there are keywords available. Every page must have enough unique information to justify existing. Google specifically identifies large-scale production of low-value pages as a spam risk.

---

## 68. Content Quality Gate

Before publishing, the editor must answer: **Originality** — did we add information competitors don't have? **Experience** — did we test anything ourselves? **Accuracy** — can we prove our claims? **Local relevance** — does this genuinely help African readers? **Trust** — would we trust this article ourselves? **Commercial neutrality** — would we still publish this review if there were no affiliate commission? **Search intent** — does it fully answer what the searcher wants? **UX** — can a reader find the answer quickly?

If the answer to two or more is **No**, don't publish.

---

## 69. The SifuFinds 10-Point Pre-Publish Score

Score every article out of 10:

| Category | Score |
| --- | ---: |
| Search intent | /10 |
| Originality | /10 |
| African relevance | /10 |
| First-hand experience | /10 |
| Accuracy | /10 |
| E-E-A-T | /10 |
| SEO structure | /10 |
| Internal linking | /10 |
| UX/readability | /10 |
| Affiliate transparency | /10 |

**Publishing threshold:** 90–100 Publish · 80–89 Improve · 70–79 Major revision · Below 70 Do not publish.

---

## 70. SifuFinds Content Quality Tiers

* 🟢 **Tier 1: Flagship** — original research + testing + screenshots + local data (e.g. Best Betting Sites in Kenya, FairPari Kenya Review, M-Pesa Betting Sites)
* 🟡 **Tier 2: Expert Guide** — strong research + original analysis + useful comparisons (e.g. How betting odds work, What is an accumulator?)
* 🟠 **Tier 3: Supporting Content** — useful but narrower (e.g. FairPari login, FairPari payment methods)
* 🔴 **Tier 4: Do Not Publish** — thin, duplicated, AI-generated or keyword-only pages

---

## 71. SifuFinds Content Pyramid

Build content in this order: **Level 1 — Country Authority** (SA, Nigeria, Kenya, Ghana, Uganda, Tanzania, Botswana, Zambia, Zimbabwe, Rwanda) → **Level 2 — Category Authority** (betting sites, bonuses, football, live betting, casino, esports, payment methods) → **Level 3 — Operator Reviews** → **Level 4 — Comparisons** ("X vs Y") → **Level 5 — Supporting Questions** (bonuses, login, withdrawals, payments, mobile, promo codes).

---

## 72. SifuFinds Must Own the "Local Answer"

Generic sites answer "What is FairPari?" — SifuFinds answers "What does FairPari mean for a bettor in Kenya?" Generic sites answer "What is the FairPari bonus?" — SifuFinds answers "Can a Kenyan bettor actually claim the FairPari bonus, and how can they deposit and withdraw?" That's the SifuFinds difference.

---

## 73. SifuFinds' Unique Editorial Formula

**Global information × African context × Local payment information × First-hand experience × Original comparison × Transparent rating × Honest verdict.**

---

## 74. The "Would I Bookmark This?" Test

Before publishing, ask: "If Google disappeared tomorrow, would someone still bookmark this page?" If no, improve it.

---

## 75. The Final SifuFinds Rule

Never ask "How do we make this rank?" Ask **"How do we make this the best answer available to an African bettor?"** Then apply SEO. The order is: **Help the reader → Add original value → Prove what you claim → Localise for Africa → Structure the information → Optimise for search → Make the next action clear → Update it when facts change.**

---

## SifuFinds Master Content Prompt

Every future SifuFinds article should follow this instruction:

> Write for SifuFinds.com using the SifuFinds Africa-First Ranking Framework. The article must be written primarily for African readers, not search engines. Identify the primary search intent before writing. Provide original information, analysis and useful local context. Never copy, spin, paraphrase or reproduce competitor content. Never invent statistics, testing, screenshots, payment methods, bonuses, licensing information, withdrawal times, country availability or customer experiences. Verify important commercial and regulatory claims using reliable sources, prioritising official sources. Clearly distinguish between verified information, third-party information and information that could not be independently confirmed. Where relevant, investigate country-specific availability, currencies, payment methods, withdrawal methods, regulations and local alternatives. Do not assume that an international bookmaker is legally or commercially available throughout Africa. Use UK English. Write naturally and conversationally. Avoid generic AI phrases, filler, repetition and keyword stuffing. Use one primary keyword and relevant secondary topics naturally. Optimise the SEO title, meta description, URL, H1, H2s, internal links and image alt text without forcing keywords. Answer important questions directly before providing detailed explanations. Use useful tables, comparison boxes, pros and cons and concise summaries where appropriate. Include first-hand testing wherever available. Include a transparent SifuFinds rating and explain how the rating was calculated. Include the SifuFinds Africa Fit score where relevant. Include author information, publication date, last verified date and affiliate disclosure. Never rank or recommend an operator based on affiliate commission. Affiliate links must never influence editorial ratings. Never create thin country pages by simply replacing the country name. Every country page must contain genuinely local information. Do not create content purely because a keyword has search volume. Every article must provide a clear reason for existing. The article should leave the reader feeling that they have learned enough to make a more informed decision without needing to immediately search for another article. Before publication, score the article against the SifuFinds 10-point quality system. Do not publish if the article does not meet the SifuFinds quality threshold.
>
> **The SifuFinds standard is simple: be more useful, more transparent and more locally relevant than the pages already ranking.**

---

## SifuFinds Editorial Mantra

**Don't write what Google already knows. Write what African bettors still need to know.**

**SifuFinds = Africa-first + Original research + First-hand experience + Local payments + Honest reviews + Transparent affiliate content.**
