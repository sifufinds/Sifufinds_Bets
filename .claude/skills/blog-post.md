---
name: blog-post
description: >
  Create SEO-optimised blog posts for SifuFinds using Firecrawl + Apify to
  research the SERP before writing. Invoke with: /blog-post <keyword or topic>
version: 1.0.0
---

# Blog Post Creation — SifuFinds

## Overview

Every post requires a full SERP and competitor research pass using **both**
Firecrawl and Apify before a single word of content is written. The workflow
below is mandatory — skip nothing.

---

## Workflow

### Phase 1 — SERP Recon (Firecrawl)

```
firecrawl_search("<primary keyword>", limit=10)
firecrawl_search("<keyword> best bookmakers <country>", limit=5)
firecrawl_search("<keyword> tips odds 2026", limit=5)
```

Capture from results:
- Top 10 URLs and their titles
- Meta description patterns (what angle do they lead with?)
- Any featured snippet / PAA / video carousels visible in snippets

---

### Phase 2 — Competitor Content Scrape (Firecrawl)

```
firecrawl_scrape([url1, url2, url3, url4, url5])
```

For each page extract and note:
| Signal | What to check |
|--------|--------------|
| Word count | Target average + 20% minimum |
| H2 / H3 headings | Copy the structure, then improve it |
| Tables | Types used (odds tables, method tables, comparison tables) |
| FAQs | Questions covered |
| Internal links | Anchor text patterns |
| Schema | Article, FAQPage, BreadcrumbList? |
| CTA placement | Where do they push affiliate links? |

---

### Phase 3 — Semantic & PAA Research (Apify)

Run the Apify RAG web browser and/or Google search scraper on the keyword:

- Pull "People Also Ask" questions — these become the FAQ section
- Pull "Related searches" — these become H2s or LSI keywords to weave in
- Identify content gaps: topics in the top 5 that none of our existing posts cover

---

### Phase 4 — Write the Post

Only after Phases 1–3 are complete. Fill every field below:

```json
{
  "category": "betting-tips | bookmaker-review | payment | world-cup | guide",
  "title": "<≤60 chars, keyword-first>",
  "slug": "<kebab-case, keyword-first>",
  "excerpt": "<≤155 chars, keyword + value proposition>",
  "body": "<full markdown — see structure below>",
  "author": "SifuFinds <Country/Topic> Desk",
  "image_color": "#<hex matching team/topic colour>",
  "image_icon": "<single emoji>",
  "tags": ["<primary keyword>", "<country>", "<sport>", "<bookmaker>"],
  "featured": false,
  "bookmaker_featured": "<main bookmaker mentioned>",
  "read_time": <estimated minutes>
}
```

#### Body Structure (markdown)

```markdown
<Intro paragraph — primary keyword in first 100 words, 2–3 sentences max>

## <H2 — mirrors top competitor heading or improves on it>

<Content>

## <H2 from PAA or gap analysis>

<Odds table or comparison table>

| Market | Bookmaker A | Bookmaker B | Bookmaker C |
|--------|------------|------------|------------|
| ...    | ...        | ...        | ...        |

## Step-by-Step Guide / How to <Action>

### Step 1: ...
### Step 2: ...
### Step 3: ...

## FAQs

### <PAA question 1>
<Answer — 2–4 sentences>

### <PAA question 2>
<Answer>

### <PAA question 3>
<Answer>

*18+ | Bet Responsibly | T&Cs Apply*
```

---

### Phase 5 — Pre-Publish SEO Checklist

Run through every item before appending to `posts.json`:

- [ ] Primary keyword in: title, H1, first 100 words, ≥ 2 H2s
- [ ] Word count ≥ top-3 SERP average + 20%
- [ ] ≥ 1 odds/comparison table
- [ ] FAQs section answers ≥ 3 PAA questions
- [ ] 3–5 internal links to existing SifuFinds pages (use `/blog/slug` paths)
- [ ] Country-specific currency/payment context (₦ NGN, KSh KES, GH₵ GHS, etc.)
- [ ] Bookmaker affiliate anchor text natural, not keyword-stuffed
- [ ] 18+ responsible gambling disclaimer at end
- [ ] `slug` is unique — check `blog/posts.json` for duplicates

---

### Phase 6 — Publish

1. Append the JSON object to the `posts` array in `blog/posts.json`
2. Run `python3 gen_blog_post_pages.py` to generate the static HTML file
3. Confirm `blog/<slug>/index.html` was created

---

## Target Markets

Nigeria (₦), Kenya (KSh), Ghana (GH₵), South Africa (R), Tanzania (TSh),
Uganda (USh), Zambia (ZK), Ethiopia (Br), Ivory Coast/Senegal/Cameroon (CFA),
Rwanda (RWF), Zimbabwe (USD), Egypt (EGP), Morocco (MAD), DR Congo (CDF),
Angola (AOA), Botswana (BWP), Namibia (NAD), Malawi (MWK), Mozambique (MZN)

## Target Bookmakers

Bet9ja, SportyBet, Betway, 1xBet, Hollywoodbets, 22Bet, Melbet, Parimatch,
BetKing, NairaBet, MSport, MozzartBet

## Payment Methods to Cover

OPay, PalmPay, M-Pesa, MTN MoMo, Airtel Money, EcoCash, Flutterwave,
Paystack, bank transfer, Visa/Mastercard
