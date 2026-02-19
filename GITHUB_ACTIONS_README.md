# GitHub Actions README

This file explains, in plain English, exactly how GitHub Actions is set up in this repository for:

- `dbb2-engine`
- `betting-engine`
- `exchange-engine`

## Daily Operator Cheat Sheet (One Page)

Use this when you want the shortest possible path.

1. Open GitHub repo -> `Actions`.
2. Check these workflows are green today:
   - `Daily DBB2 Projections`
   - `Daily Grading`
   - `Exchange Engine Daily`
3. If one is red, click it and open the failed step log.
4. Most common cause is missing/invalid secret.
5. Check secrets in:
   - `Settings` -> `Secrets and variables` -> `Actions`
6. Required secrets to verify:
   - `ODDS_API_KEY`
   - `KALSHI_API_KEY_ID`
   - `KALSHI_PRIVATE_KEY`
   - `DBB2_API_URL`
   - `NOVIG_ODDS_URL`
   - `PROPHETX_ODDS_URL`
7. After fixing secrets, go back to failed run -> `Re-run jobs`.
8. To run manually right now:
   - `Actions` -> choose workflow -> `Run workflow` -> pick `main` -> run.
9. To verify outputs were committed, check latest commit files changed under:
   - `dbb2-engine/output/`
   - `betting-engine/data/`
   - `exchange-engine/data/`
10. Ignore `Daily Bets (RETIRED...)` unless you intentionally need emergency fallback.

If you only read one section first, read:

- `Quick Start`
- `Workflow Map`
- `Secrets You Must Set`

## Quick Start

If you want to manually run a workflow right now:

1. Open your GitHub repo page.
2. Click `Actions`.
3. Click one of these workflows:
   - `Daily DBB2 Projections`
   - `Daily Grading`
   - `Nightly Pipeline (Legacy Manual)`
   - `Exchange Engine Daily`
4. Click `Run workflow`.
5. Pick branch (usually `main`).
6. Click the green `Run workflow` button.
7. Wait for completion and open logs if needed.

## Workflow Map

Current workflow files in this repo:

- `.github/workflows/daily-projections.yml`
- `.github/workflows/daily-bets.yml`
- `.github/workflows/daily-grading.yml`
- `.github/workflows/nightly-pipeline.yml`
- `.github/workflows/exchange-engine-daily.yml`

### What each one is for

- `daily-projections.yml`
  - Primary scheduled projections refresh.
  - Runs DBB2 engine and copies contract into betting-engine projections folder.
- `daily-bets.yml`
  - Marked as **RETIRED** in the workflow name/comments.
  - Kept as manual fallback only.
- `daily-grading.yml`
  - Grades previous bets, updates results + ledger + reports.
- `nightly-pipeline.yml`
  - Legacy/manual “collect + project + bet” end-to-end run for DBB2 + betting engine.
- `exchange-engine-daily.yml`
  - Separate daily run for exchange engine only.

## Engine-to-Workflow Ownership

### DBB2 engine workflows

- Main: `daily-projections.yml`
- Also used by legacy manual pipeline: `nightly-pipeline.yml`

### Betting engine workflows

- Main grading workflow: `daily-grading.yml`
- Legacy/manual placement path: `nightly-pipeline.yml`
- Retired fallback: `daily-bets.yml` (manual only)

### Exchange engine workflows

- Dedicated separate workflow: `exchange-engine-daily.yml`

This separation means exchange runs do not need to modify or run betting workflows.

## Secrets You Must Set

Go to:

- `Repo Settings` -> `Secrets and variables` -> `Actions`

### Secrets used by DBB2 / Betting workflows

- `ODDS_API_KEY`
- `KALSHI_API_KEY_ID`
- `KALSHI_PRIVATE_KEY`

### Secrets used by Exchange workflow

- `DBB2_API_URL` (required for exchange workflow to run)
- `NOVIG_ODDS_URL` (optional but needed if you want Novig odds)
- `PROPHETX_ODDS_URL` (optional but needed if you want ProphetX odds)

Important:

- `exchange-engine-daily.yml` explicitly checks `DBB2_API_URL`.
- If `DBB2_API_URL` is missing, exchange run is skipped on purpose.

## Detailed Workflow Breakdown

## 1) Daily DBB2 Projections

File:

- `.github/workflows/daily-projections.yml`

Workflow name:

- `Daily DBB2 Projections`

Triggers:

- `schedule`: every hour (`0 * * * *`)
- `workflow_dispatch`: manual run

Why hourly if it should run once:

- The workflow includes an internal gate step.
- It only proceeds at `04:00` in `America/New_York` for scheduled runs.

Main steps:

1. Checkout repo
2. Gate run to 4 AM New York time
3. Setup Python 3.11
4. Install `dbb2-engine/requirements.txt`
5. Run projection engine:
   - `python dbb2-engine/run_engine.py --game-day --validate --output-dir dbb2-engine/output`
6. Copy output contract to:
   - `betting-engine/data/projections/YYYY-MM-DD.json`
7. Commit/push changed projection files

Files committed:

- `dbb2-engine/output/players.json`
- `dbb2-engine/output/projections.json`
- `dbb2-engine/output/risk.json`
- `dbb2-engine/output/insights.json`
- `dbb2-engine/output/betting_contract.json`
- `betting-engine/data/projections/${DATE}.json`

Concurrency:

- Group: `daily-dbb2-projections`
- `cancel-in-progress: false`

Meaning:

- Scheduled instances in same group won’t overlap-cancel each other.

## 2) Daily Bets (Retired)

File:

- `.github/workflows/daily-bets.yml`

Workflow name:

- `Daily Bets (RETIRED — replaced by nightly-pipeline.yml)`

Trigger:

- `workflow_dispatch` only

Purpose now:

- Emergency fallback manual run.

Working directory:

- `betting-engine`

Main steps:

1. Checkout
2. Python 3.11 setup
3. Install `betting-engine/requirements.txt`
4. Optional NBA games check via Odds API
5. Run `python src/bet_placer.py`
6. Commit generated bet artifacts

Committed paths:

- `betting-engine/data/bet_slips/`
- `betting-engine/data/bets/`
- `betting-engine/data/kalshi/bet_slips/`

## 3) Daily Grading

File:

- `.github/workflows/daily-grading.yml`

Workflow name:

- `Daily Grading`

Triggers:

- `schedule`: `0 16 * * *` (comment notes ET conversion)
- `workflow_dispatch` with optional `date` input

Working directory:

- `betting-engine`

Main steps:

1. Checkout
2. Python 3.11 setup
3. Install betting dependencies
4. Make logs directory
5. Determine grading date
   - Uses input date if provided
   - Otherwise defaults to yesterday
6. Check if relevant bet slip exists
7. Fetch closing lines (`clv_fetcher.py`)
8. Grade bets (`result_checker.py`)
9. Commit results + ledger + reports

Committed paths:

- `betting-engine/data/results/`
- `betting-engine/data/ledger.json`
- `betting-engine/data/ledger_history.md`
- `betting-engine/data/bets/`
- `betting-engine/reports/`

## 4) Nightly Pipeline (Legacy Manual)

File:

- `.github/workflows/nightly-pipeline.yml`

Workflow name:

- `Nightly Pipeline (Legacy Manual)`

Trigger:

- `workflow_dispatch` with inputs:
  - `season` (optional)
  - `skip_collection` (boolean)

Purpose:

- One manual workflow that can:
  - collect season data
  - run DBB2 engine
  - copy projections
  - run betting engine
  - commit outputs

Main steps:

1. Checkout
2. Setup Python 3.11
3. Install dbb2 + betting dependencies
4. Prepare folders
5. Determine season
6. Copy historical CSVs into `dbb2-engine/raw_data`
7. Optionally collect current season data (with retries)
8. Run DBB2 engine (`python run_engine.py --game-day`)
9. Copy contract to `betting-engine/data/projections/YYYY-MM-DD.json`
10. Check if games exist today
11. Run betting bet placer with projection file
12. Commit pipeline outputs

Committed paths:

- `dbb2-engine/output/`
- `betting-engine/data/projections/`
- `betting-engine/data/bet_slips/`
- `betting-engine/data/bets/`
- `betting-engine/data/kalshi/bet_slips/`

## 5) Exchange Engine Daily

File:

- `.github/workflows/exchange-engine-daily.yml`

Workflow name:

- `Exchange Engine Daily`

Triggers:

- `schedule`: `30 9 * * *`
- `workflow_dispatch`

Working directory:

- `exchange-engine`

Main steps:

1. Checkout
2. Python 3.11 setup
3. Install `exchange-engine/requirements.txt`
4. Ensure exchange data directories exist
5. Check `DBB2_API_URL` secret exists
6. Run:
   - `python -m src.bet_placer`
7. Commit exchange outputs

Environment passed into run:

- `DBB2_API_URL`
- `NOVIG_ODDS_URL`
- `PROPHETX_ODDS_URL`

Committed paths:

- `exchange-engine/data/projections/`
- `exchange-engine/data/exchange_odds/`
- `exchange-engine/data/ev_results/`
- `exchange-engine/data/sized_bets/`
- `exchange-engine/data/bet_slips/`
- `exchange-engine/data/orders/`
- `exchange-engine/data/ledger.json`

## Commit Behavior (All Workflows)

Most workflows follow this pattern:

1. `git add ...`
2. `git diff --cached --quiet`
3. If nothing changed, exit cleanly
4. If changed, `git commit` + `git push`

This prevents empty commits.

## Time and Timezone Notes

Cron is evaluated in UTC by GitHub.

Key behaviors in this repo:

- `daily-projections.yml` uses an hourly cron + explicit New York time gate.
- `daily-grading.yml` uses fixed cron with comment documenting ET conversion.
- `exchange-engine-daily.yml` currently runs at UTC `09:30`.

If schedule timing looks off:

- Check UTC vs ET
- Check daylight savings
- Check whether the workflow has an internal gate

## How to Manually Re-Run Failed Jobs

1. Go to `Actions`.
2. Open failed run.
3. Click `Re-run jobs`.
4. If secret/config issue, fix it first, then rerun.

## Common Failure Modes and Fixes

### Failure: missing secret

Symptom:

- Step fails or intentionally skips because env var missing.

Fix:

1. Add secret in GitHub repo settings.
2. Re-run workflow.

### Failure: no files committed

Symptom:

- Log says “No changes to commit”.

Usually this is normal:

- output didn’t change
- or upstream data produced same result

### Failure: projection file missing for betting run

Symptom:

- Nightly pipeline skip in bet step.

Fix:

1. Confirm DBB2 engine step produced `dbb2-engine/output/betting_contract.json`.
2. Confirm copy step succeeded.

### Failure: exchange run skips

Symptom:

- `DBB2_API_URL secret not set, skipping exchange run`.

Fix:

1. Add `DBB2_API_URL`.
2. Re-run workflow.

## How to Disable a Workflow Temporarily

Simple safe method:

1. Edit workflow trigger to remove `schedule` (keep `workflow_dispatch`).
2. Commit.

Or fully disable in GitHub UI if needed.

## Suggested Operating Pattern

If you want stability and clear ownership:

1. Keep `daily-projections.yml` as primary DBB2 projection automation.
2. Keep `daily-grading.yml` as primary betting grading automation.
3. Use `exchange-engine-daily.yml` for exchange engine separately.
4. Use `nightly-pipeline.yml` only for manual/legacy operations.
5. Keep `daily-bets.yml` retired unless emergency fallback is needed.

## Quick Reference Table

| Workflow | Purpose | Engine(s) | Trigger |
|---|---|---|---|
| `Daily DBB2 Projections` | Generate DBB2 outputs + copy contract | DBB2 + Betting projection handoff | Schedule + Manual |
| `Daily Bets (RETIRED...)` | Fallback manual bet placement | Betting | Manual only |
| `Daily Grading` | Grade previous bets, update ledger/reports | Betting | Schedule + Manual |
| `Nightly Pipeline (Legacy Manual)` | Manual all-in-one legacy flow | DBB2 + Betting | Manual only |
| `Exchange Engine Daily` | Daily exchange run + commit outputs | Exchange | Schedule + Manual |

## Final Notes

- This README describes the repo state as currently configured.
- If workflow files change, update this README in the same PR.
- Keep exchange and betting workflows separate unless you explicitly want cross-engine coupling.
