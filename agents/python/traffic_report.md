# SifuFinds Traffic Report
**Period:** awaiting first run · **Generated:** –

> No data yet. Complete the 2-minute GoatCounter setup below, then trigger the workflow.

## Setup — 2 Minutes, No Credit Card

**Step 1 — Create free account**
Go to **goatcounter.com** → click Sign Up → enter email + password

**Step 2 — Add your site**
- Site code: type `sifufinds` (this becomes `sifufinds.goatcounter.com`)
- URL: `https://sifufinds.com`

**Step 3 — Get API token**
Settings (top right) → API tokens → Create token → copy it

**Step 4 — Add 2 GitHub secrets**
GitHub repo → Settings → Secrets → Actions → New secret:
- `GOATCOUNTER_SITE` = `sifufinds`
- `GOATCOUNTER_TOKEN` = your token from Step 3

**Step 5 — Trigger the workflow**
GitHub → Actions → "Traffic Report" → Run workflow

That's it. The report updates automatically every day at 07:00 UTC after that.

---

**Note on search impressions:** Once Google Search Console verifies your site
(the `google3a6a68be4020e715.html` file is already in the repo), check
https://search.google.com/search-console for keyword impressions and clicks.
No API needed — just log in and view the dashboard.
