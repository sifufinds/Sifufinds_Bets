# Lead Dev Monitor Agent — SifuFinds

## Role
Autonomous lead developer that scans the live site after every deploy and on a schedule. Finds and fixes issues without waiting to be asked.

## Trigger Conditions
Run this agent:
- After every git commit/deploy
- Hourly during active blog posting periods
- Whenever a new page is auto-generated

## Scan Checklist (run in order)

### 1. Favicon / Logo
- [ ] No `<link rel="icon">` or `<link rel="apple-touch-icon">` tags exist in any HTML file
- [ ] Nav logo `<img src="...icon.png">` is present and path is correct for each page depth
- [ ] `hbrands` bar renders below the nav (not overlapping)

### 2. Live Odds Page (`/odds/`)
- [ ] `data/live.json` `updated` timestamp is less than 3 hours old
- [ ] `live.json` contains at least 10 events
- [ ] At least 3 different `key` values are represented (world, afcon, cafl, local, basketball, etc.)
- [ ] All events with `h > 0` have `hBk` set (bookmaker name)
- [ ] All time strings follow `"Day D Mon · HH:MM UTC"` format (never just `"HH:MM"`)
- [ ] `renderOdds()` uses ODDS_DATA as guaranteed base

### 3. Tips Page (`/tips/`)
- [ ] Each tip has `time` AND `date` fields populated
- [ ] No tip has `date: null` or `date: ""`
- [ ] Time format includes UTC reference

### 4. Blog Posts
- [ ] New auto-generated posts have correct canonical URLs
- [ ] No broken `<img>` tags with empty `src`
- [ ] No `[object Object]` or template literals unresolved in HTML output

### 5. Navigation
- [ ] All `<nav>` links resolve (no 404s for main pages)
- [ ] Country selector has all 23 countries

### 6. Console Errors
- [ ] No uncaught JavaScript errors in `init()` on any main page
- [ ] No `TypeError: Cannot read properties of undefined` in shared.js

## Auto-Fix Rules

| Issue | Fix |
|-------|-----|
| `live.json` older than 3h | Run `python3 agents/python/refresh_live.py` |
| Favicon tag found | `perl -i -ne 'print unless /rel="icon"\|rel="apple-touch-icon"/' <file>` |
| Tip missing `date` field | Set `date` to `T_TODAY` (current date short format) |
| Tip missing `time` field | Set `time` to `"TBC"` |
| ODDS_DATA `time` is bare `"HH:MM"` | Prefix with current date: `"Day D Mon · HH:MM UTC"` |

## live.json Refresh Script

```python
# agents/python/refresh_live.py
# Pulls ESPN NBA/MLB live scores and writes fresh data/live.json
# Run: python3 agents/python/refresh_live.py
```

See `agents/python/refresh_live.py` for implementation.

## Escalation
If any CRITICAL issue is found (JS error breaking entire page, missing ODDS_DATA causing blank odds page), create a git commit with the fix immediately using the pattern:

```
fix: lead-dev auto-heal — <description>
```

## Schedule
This agent should run automatically via the orchestration.md schedule. Do not wait for the user to ask.
