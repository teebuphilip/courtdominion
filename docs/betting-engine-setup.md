# Betting Engine Setup Guide

## 1. API Keys You Need

You need **3 keys** from **2 providers**:

### A. The Odds API (sportsbook lines)
- **What:** `ODDS_API_KEY`
- **Sign up:** https://the-odds-api.com
- **Free tier:** 500 requests/month (plenty for daily use)
- **Used for:** Fetching live sportsbook lines from DraftKings, FanDuel, BetMGM

### B. Kalshi (prediction market prices)
- **What:** Two things — a **Key ID** and a **Private Key** (RSA keypair)
- **Sign up:** https://kalshi.com → create account → go to **Settings > API**
- **Steps to generate:**
  1. Log into Kalshi
  2. Go to Settings > API Keys
  3. Click "Create API Key"
  4. Kalshi gives you:
     - `API Key ID` — a string like `abc123-def456-...`
     - `Private Key` — downloads as a `.pem` file
  5. Save the `.pem` file locally at `betting-engine/config/kalshi_private_key.pem` (already gitignored)

| Secret Name | Provider | Value |
|-------------|----------|-------|
| `ODDS_API_KEY` | The Odds API | Your API key string |
| `KALSHI_API_KEY_ID` | Kalshi | The Key ID string from Settings > API |
| `KALSHI_PRIVATE_KEY` | Kalshi | The **full contents** of the `.pem` file (see below) |

---

## 2. Where to Put Them (GitHub Secrets)

All 3 go into **GitHub repo secrets** so the Actions workflows can use them.

### Steps:
1. Go to your repo: `https://github.com/teebuphilip/courtdominion`
2. Click **Settings** (top nav)
3. Left sidebar: **Secrets and variables > Actions**
4. Click **New repository secret** for each:

| Name | Value |
|------|-------|
| `ODDS_API_KEY` | Paste your Odds API key |
| `KALSHI_API_KEY_ID` | Paste the Kalshi Key ID |
| `KALSHI_PRIVATE_KEY` | Paste the **entire contents** of the `.pem` file (including `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----` lines) |

### For the Kalshi private key specifically:
Open the `.pem` file in a text editor, select all, copy, and paste the entire thing into the secret value field. It should look like:
```
-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASC...
... (multiple lines) ...
-----END PRIVATE KEY-----
```

### Local development:
For running locally (not in GitHub Actions), you can either:
- Set env vars: `export ODDS_API_KEY=your_key` (add to `~/.zshrc`)
- Or put the Odds API key in `config/settings.json` under `odds_api.api_key`
- Put the Kalshi `.pem` file at `config/kalshi_private_key.pem`

---

## 3. Cron Jobs Guide (GitHub Actions)

You have **2 automated workflows** that run daily:

### Morning Bets (`daily-bets.yml`)

| | |
|---|---|
| **Schedule** | Every day at **4:00 PM ET** (9:00 PM UTC) |
| **What it does** | Generates today's bet slip |
| **Trigger** | Automatic (cron) or manual (workflow_dispatch) |

**Pipeline:**
1. Checks if NBA games are scheduled today (via Odds API)
2. If yes, runs `bet_placer.py` which:
   - Fetches DBB2 projections + sportsbook odds → calculates sportsbook EV + Kelly sizing
   - Fetches Kalshi markets → calculates Kalshi EV + Kelly sizing
   - Combines all bets, sorts by edge, applies $5K daily budget cap
   - Appends to `data/bets/master_bets.csv`
   - Generates bet slip (JSON + Markdown + terminal)
3. Commits bet slips + master CSV to the repo

**If no games today:** Skips everything, no commit.

### Night Grading (`daily-grading.yml`)

| | |
|---|---|
| **Schedule** | Every day at **11:00 AM ET** (4:00 PM UTC) |
| **What it does** | Grades yesterday's bets against actual box scores |
| **Trigger** | Automatic (cron) or manual (with optional date input) |

**Pipeline:**
1. Checks if a bet slip exists for the date being graded
2. If yes, runs `result_checker.py` which:
   - Fetches actual NBA box scores from stats.nba.com
   - Grades each bet: WIN / LOSS / PUSH / NO_ACTION
   - Calculates payouts (sportsbook: American odds, Kalshi: binary)
   - Updates ledger (bankroll, P&L, win rate, ROI)
   - Updates master CSV with results
   - Generates season summary at `reports/season_summary.md`
3. Commits results, ledger, CSV, and season summary

**If no bet slip for that date:** Skips everything, no commit.

### Manual Triggers

Both workflows support **workflow_dispatch** — you can run them manually:

1. Go to your repo > **Actions** tab
2. Click the workflow name in the left sidebar
3. Click **Run workflow**
4. For grading, you can optionally enter a specific date (e.g., `2026-02-14`)

### Timing Rationale

```
4:00 PM ET — Bets generated (games typically start 7pm ET, lines are set by 4pm)
     |
     v
  [NBA games play out that evening]
     |
     v
11:00 AM ET (next day) — Bets graded (box scores available by morning)
```

### Monitoring

After the workflows run, check:
- **Bet slips:** `betting-engine/data/bet_slips/{date}.json`
- **Results:** `betting-engine/data/results/{date}.json`
- **Master CSV:** `betting-engine/data/bets/master_bets.csv`
- **Ledger:** `betting-engine/data/ledger.json`
- **Season summary:** `betting-engine/reports/season_summary.md`
- **Markdown ledger:** `betting-engine/data/ledger_history.md`

All of these get committed to the repo automatically, so you can track everything in git history.

### If Something Goes Wrong

- Check the **Actions** tab for workflow run logs
- Common issues:
  - `ODDS_API_KEY` not set → game check fails silently, skips betting
  - `KALSHI_PRIVATE_KEY` not set → Kalshi pipeline skips, sportsbook still runs
  - No NBA games → workflow skips (this is expected on off-days)
  - Rate limits → Kalshi has 0.5s delay between requests built in
