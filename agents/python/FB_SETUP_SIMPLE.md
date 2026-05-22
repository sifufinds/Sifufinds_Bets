# Facebook + Instagram Setup — Uses Your Existing Account
**Time: 20 minutes | Cost: $0 | No separate developer account**

The word "developer" sounds scary but this is literally just your Facebook account.
You log in with the same email and password you use every day.

---

## Part 1 — Facebook Page Token (10 minutes)

You need a Facebook **Page** (not a personal profile) to post as SifuFinds.
If you don't have one yet: facebook.com → Pages → Create Page → name it "SifuFinds".

### Get your Page Access Token:

1. Go to **developers.facebook.com**
2. Click **Log In** — use your normal Facebook email and password
3. Click **My Apps** → **Create App**
4. Choose **"Other"** → **"Business"** → Next
5. App name: `SifuFinds` → Your email → Create App
6. In your new app, find **"Tools"** in the left menu → **Graph API Explorer**
7. In the Explorer:
   - Top right dropdown: select your App (`SifuFinds`)
   - Click **"Generate Access Token"**
   - Tick these permissions: `pages_manage_posts`, `pages_read_engagement`, `instagram_basic`, `instagram_content_publish`
   - Click **Generate**
   - You'll be asked to log in with Facebook again → Allow
8. Copy the token shown — this is a **short-lived token** (expires in 1 hour)

### Make it long-lived (never expires):

9. Still in Graph API Explorer, change the URL to:
   ```
   GET https://graph.facebook.com/oauth/access_token
       ?grant_type=fb_exchange_token
       &client_id=YOUR_APP_ID
       &client_secret=YOUR_APP_SECRET
       &fb_exchange_token=PASTE_SHORT_TOKEN_HERE
   ```
   (Your App ID and Secret are in: App Dashboard → Settings → Basic)
10. Click **Submit** → copy the new long token from the response
11. This token lasts **60 days** — run this step again every 60 days

### Find your Page ID:
12. Go to your Facebook Page → **About** tab → scroll to bottom → **Page ID** (it's a number)

---

## Part 2 — Instagram Business Account (5 minutes)

1. On Instagram: **Settings → Account → Switch to Professional Account → Business** (free)
2. Connect it to your Facebook Page: **Settings → Linked Accounts → Facebook** → pick your Page

### Find your Instagram Account ID:
3. Go back to Graph API Explorer
4. In the URL field type: `me/accounts`
5. Click **Submit** — you'll see your Page in the results with an `id` field → copy it
6. Now type: `PAGE_ID?fields=instagram_business_account`
7. Submit → copy the `id` inside `instagram_business_account` — that's your Instagram Account ID

---

## Part 3 — Add to GitHub Secrets

Go to your GitHub repo → **Settings → Secrets and variables → Actions**

| Secret | Value |
|---|---|
| `FACEBOOK_PAGE_ID` | The Page ID number from Step 12 |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | The long-lived token from Step 10 |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | The IG account ID from Step 7 |

---

## Every 60 Days — Refresh Token (5 minutes)

Facebook long-lived tokens expire after 60 days. Set a calendar reminder.
Repeat Steps 9-10 and update the `FACEBOOK_PAGE_ACCESS_TOKEN` secret in GitHub.

Or: set up a Facebook webhook to auto-refresh (more advanced — ask when ready).

---

## That's It

The "developer" account IS your Facebook account. Same login. Same email. No payment.
The only difference is you enabled the developer tools feature inside your existing account.
