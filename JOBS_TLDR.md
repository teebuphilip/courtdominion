# Jobs TL;DR (One Page)

This is the quick schedule + purpose summary for all current GitHub Actions workflows.

## Active Scheduled Workflows

| Workflow | Schedule (UTC) | Schedule (ET) | What It Does |
|---|---:|---:|---|
| `daily-projections.yml` | `0 * * * *` (hourly) with gate | Runs only at **4:00 AM ET** | Refreshes current NBA season data from NBA.com, runs `dbb2-engine`, updates `dbb2-engine/output/*`, writes daily projection/risk snapshots into betting + exchange data folders, commits changes. |
| `exchange-engine-daily.yml` | `30 9 * * *` | **4:30 AM ET** (EST) / **5:30 AM ET** (EDT) | Runs exchange-engine daily pipeline, generates exchange bet outputs/slips/orders/ledger, commits changes. |
| `daily-grading.yml` | `0 16 * * *` | **11:00 AM ET** (EST) / **12:00 PM ET** (EDT) | Grades prior bets, updates ledgers/results/CSVs, then builds report pages (historical + today) and syncs generated HTML into `free-site/public/*`. |

## Manual / Fallback Workflows

| Workflow | Schedule | Status | What It Does |
|---|---|---|---|
| `nightly-pipeline.yml` | none (manual `workflow_dispatch`) | Legacy manual | End-to-end manual run: collect season data, run DBB2, run betting-engine placement, now includes Polymarket demo generation, commits outputs. |
| `daily-bets.yml` | none (manual `workflow_dispatch`) | Retired fallback | Legacy betting-only fallback workflow; now includes Polymarket demo generation if manually triggered. |

## Post-Grading Page Jobs (inside `daily-grading.yml`)

1. `build-historical-bet-page`  
Builds historical page artifact from ledgers/CSV data.

2. `build-todays-bet-page`  
Builds today page artifact from current-day bets.

3. `sync-free-site-pages`  
Runs after both page jobs succeed; copies/syncs generated pages into:
- `free-site/public/historical-bets.html`
- `free-site/public/todays-bets.html`

## Output Highlights

- DBB2 projections/risk snapshots: `dbb2-engine/output/*`, plus daily copies in betting/exchange data dirs.
- Betting slips + ledgers + CSVs: `betting-engine/data/*`
- Exchange slips + ledger: `exchange-engine/data/*`
- Generated web reports: `reports/web/*`
- Synced free-site pages: `free-site/public/historical-bets.html`, `free-site/public/todays-bets.html`
