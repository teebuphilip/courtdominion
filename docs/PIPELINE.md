# DBB2 Nightly Pipeline

How the automated betting pipeline works, end to end.

---

## Overview

Three GitHub Actions workflows run the full cycle every day:

| Workflow | Schedule | What it does |
|----------|----------|-------------|
| **Nightly Pipeline** | 2:00 PM ET | Collect stats, run engine, place bets |
| **Daily Grading** | 11:00 AM ET (next day) | Fetch closing lines, grade bets, update ledger |
| **Daily Bets** | Manual only | Emergency fallback (retired from schedule) |

```
2:00 PM ET                              7:00 PM ET             11:00 AM ET (next day)
    |                                       |                        |
    v                                       v                        v
[Nightly Pipeline]                    [Games start]           [Daily Grading]
 1. Collect NBA stats                                         1. Fetch closing lines (CLV)
 2. Run DBB2 engine                                           2. Grade yesterday's bets
 3. Generate projections                                      3. Update ledger + season summary
 4. Fetch odds from sportsbooks                               4. Commit results
 5. Place bets (sportsbook + Kalshi)
 6. Commit bet slips + projections
```

---

## Nightly Pipeline (`.github/workflows/nightly-pipeline.yml`)

Runs at **2:00 PM ET** daily, ~5 hours before NBA tip-offs.

### Step 1: Data Collection

Collects the current NBA season's game logs from the NBA Stats API.

- **Historical data** (2022-23 and 2023-24 seasons) is committed in `dbb2-engine/data_collection/historical/`. These seasons are over and never change. The workflow copies them into `raw_data/` at runtime.
- **Current season** (2024-25) is collected fresh each run using `collect_nba_season.py`. Takes ~5-10 minutes due to NBA API rate limits (fetches game logs + player info for ~500 players).
- No API key needed. The NBA Stats API is public.

```
dbb2-engine/data_collection/historical/     (committed, static)
  games_2022_23.csv                          ~25,900 rows
  games_2023_24.csv                          ~26,400 rows

dbb2-engine/raw_data/                        (created at runtime, gitignored)
  games_2022_23.csv                          copied from historical/
  games_2023_24.csv                          copied from historical/
  games_2024_25.csv                          collected fresh from NBA API
```

### Step 2: Run DBB2 Engine

Runs `python run_engine.py --game-day` which:

1. Loads the 3 most recent seasons of CSV data from `raw_data/`
2. Builds player baselines (weighted average: 50% current, 30% prior, 20% two prior)
3. Projects every stat (points, rebounds, assists, threes, steals, blocks)
4. Applies game-day adjustments (back-to-back, rest days, death spots, travel)
5. Exports `output/betting_contract.json` — the projection file the betting engine consumes

The engine auto-detects the current NBA season from today's date. If the current season CSV hasn't been collected yet, it falls back to the most recent available season.

### Step 3: Place Bets

Copies `betting_contract.json` to `betting-engine/data/projections/{date}.json`, then runs the betting pipeline:

1. **Check for games** — calls The Odds API to see if NBA games are scheduled. If no API key is set, assumes games are on (fail open).
2. **Sportsbook pipeline** — fetches player prop lines from The Odds API, compares against DBB2 projections, calculates EV (expected value), sizes bets using Kelly criterion.
3. **Kalshi pipeline** — fetches Kalshi event contract prices, compares against DBB2 implied probabilities, calculates EV.
4. **Budget cap** — sorts all bets by edge, allocates up to the daily limit ($5,000 default), best edge first.
5. **Outputs** — appends bets to `master_bets.csv`, generates bet slips in `data/bet_slips/`.

### Step 4: Commit

Commits projections and bet slips to the repo so grading can find them the next morning.

---

## Daily Grading (`.github/workflows/daily-grading.yml`)

Runs at **11:00 AM ET** the next day, after all games have finished and box scores are available.

### Step 1: Fetch Closing Lines (CLV)

Runs `clv_fetcher.py` to grab the final market prices from right before tip-off. This is the "closing line" — the sharpest, most efficient price the market produced.

- **Sportsbook CLV** = how many points the line moved in your favor. Example: you bet OVER 24.5, line closed at 25.5 = +1.0 CLV.
- **Kalshi CLV** = how much the YES price moved in your favor. Example: you bought YES at $0.55, closed at $0.63 = +0.08 CLV.
- Positive CLV means the model beat the market. If you consistently have positive CLV across 300+ bets, that's strong evidence of real edge.

### Step 2: Grade Bets

Runs `result_checker.py` which:

1. Fetches actual box scores from the NBA Stats API
2. Compares each bet's prediction against the actual result
3. Marks bets as WIN, LOSS, PUSH, or NO_ACTION (player didn't play)
4. Calculates P&L for each bet
5. Updates the ledger and generates the season summary report

### Step 3: Commit Results

Commits graded results, updated ledger, and season summary to the repo.

---

## Required Secrets

Set these in your GitHub repo under **Settings > Secrets and variables > Actions**:

| Secret | Required for | Where to get it |
|--------|-------------|-----------------|
| `ODDS_API_KEY` | Sportsbook odds + closing lines | https://the-odds-api.com/ (free tier: 500 req/month) |
| `KALSHI_API_KEY_ID` | Kalshi event contracts | https://kalshi.com/ (create account, request API access) |
| `KALSHI_PRIVATE_KEY` | Kalshi authentication | Generated when you create Kalshi API credentials |

**Without these secrets:** The pipeline still collects data and generates projections. The betting steps skip gracefully — no crash, no bets placed. You can add the keys later and everything will start working.

---

## Manual Triggers

You can run any workflow manually from the GitHub Actions tab or via CLI:

```bash
# Run the full nightly pipeline now
gh workflow run nightly-pipeline.yml

# Run with a specific season
gh workflow run nightly-pipeline.yml -f season=2024-25

# Skip data collection (use committed historical data only)
gh workflow run nightly-pipeline.yml -f skip_collection=true

# Grade a specific date
gh workflow run daily-grading.yml -f date=2026-02-15
```

---

## Local Development

To run the pipeline locally:

```bash
# Activate Python environment
source ~/venvs/cd39/bin/activate

# 1. Collect current season (skip if raw_data/ already has it)
cd ~/Documents/work/courtdominion/dbb2-engine
python data_collection/collect_nba_season.py --season 2024-25 --output raw_data/

# 2. Run engine
python run_engine.py --game-day

# 3. Copy projections to betting engine
DATE=$(date +%Y-%m-%d)
mkdir -p ../betting-engine/data/projections
cp output/betting_contract.json ../betting-engine/data/projections/${DATE}.json

# 4. Place bets (dry-run mode uses fixture data for odds)
cd ../betting-engine
python src/bet_placer.py --from-file data/projections/${DATE}.json --dry-run

# 5. Grade yesterday's bets
python src/result_checker.py --date $(date -v-1d +%Y-%m-%d)
```

---

## Key Files

| File | Purpose |
|------|---------|
| `dbb2-engine/data_collection/collect_nba_season.py` | Collects full season game logs from NBA Stats API |
| `dbb2-engine/data_collection/historical/*.csv` | Static historical season data (committed) |
| `dbb2-engine/run_engine.py` | Engine CLI: project + export |
| `dbb2-engine/engine/baseline.py` | Builds player baselines from CSV data |
| `dbb2-engine/engine/export_betting.py` | Exports `betting_contract.json` |
| `betting-engine/src/bet_placer.py` | Orchestrates daily betting (sportsbook + Kalshi) |
| `betting-engine/src/odds_ingestion.py` | Fetches odds + loads projections |
| `betting-engine/src/ev_calculator.py` | Calculates expected value for sportsbook bets |
| `betting-engine/src/kalshi_ev_calculator.py` | Calculates expected value for Kalshi bets |
| `betting-engine/src/kelly_sizer.py` | Sizes bets using Kelly criterion |
| `betting-engine/src/clv_fetcher.py` | Fetches closing lines, calculates CLV |
| `betting-engine/src/result_checker.py` | Grades bets against actual results |
| `betting-engine/config/settings.json` | All configuration (bankroll, odds API, Kalshi, thresholds) |

---

## Config Reference (`betting-engine/config/settings.json`)

Key settings that control betting behavior:

```
bankroll.starting_balance   $10,000    Total bankroll
bankroll.unit_size          $100       One unit
bankroll.daily_limit        $5,000     Max daily exposure

kelly.fraction              0.25       Quarter-Kelly (conservative)
kelly.min_units             0.5        Minimum bet size
kelly.max_units             5.0        Maximum bet size

ev.min_edge_pct             3.0        Minimum edge % to bet
ev.min_confidence           0.60       Minimum model confidence

clv.min_bets_for_avg_clv    20         Bets needed before showing CLV stats
```

---

## Troubleshooting

**Pipeline ran but no bets were placed**
- Check if `ODDS_API_KEY` is set as a GitHub Secret
- Check if there were NBA games that day (All-Star break, off days)
- Check the workflow logs for "No +EV bets found" (model didn't find edges)

**Data collection failed**
- NBA Stats API occasionally blocks requests. The script has built-in rate limiting (0.6s between requests) and retries. If it fails, trigger a manual re-run.

**Grading shows NO_ACTION for all bets**
- Box scores may not be available yet. The grading workflow runs at 11 AM ET, which should be late enough. If games ran very late (West Coast), some scores might be delayed.

**CLV columns are empty**
- The CLV fetcher needs API keys to fetch closing lines. Without keys, closing_line and clv stay empty in the CSV. Bets are still graded normally.
