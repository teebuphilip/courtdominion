# CourtDominion

CourtDominion contains the DBB2 projection engine, betting engine, and app code.

## Repository Structure
- `dbb2-engine/`: projection engine and API contract exporter
- `betting-engine/`: EV + Kelly + slip/CSV pipeline
- `courtdominion-app/`: frontend/backend app code
- `.github/workflows/`: scheduled automation and manual workflows

## Deploy DBB2 Engine To Railway

### 1. Service setup
- In Railway, create a new service from this repo.
- Set **Root Directory** to `dbb2-engine`.
- Deploy using the included `dbb2-engine/Dockerfile`.

### 2. Runtime behavior
The container starts:

```bash
uvicorn engine.api:app --host 0.0.0.0 --port ${PORT}
```

### 3. Verify deployment
After deploy, confirm:
- `GET /health`
- `GET /projections/today`

If both return successfully, Railway API deployment is complete.

## Daily 4:00 AM ET Projections + Git Commit

Daily projection generation and git commit now run from GitHub Actions (not Railway cron).

### Active workflow
- `.github/workflows/daily-projections.yml`

### Schedule behavior
- Workflow is triggered hourly in UTC.
- It only executes the projection job when local time is `04:00` in `America/New_York`.
- This keeps 4:00 AM ET aligned across DST changes.

### What the workflow does
1. Installs `dbb2-engine` dependencies.
2. Runs:
   - `python dbb2-engine/run_engine.py --game-day --validate --output-dir dbb2-engine/output`
3. Copies `dbb2-engine/output/betting_contract.json` to:
   - `betting-engine/data/projections/YYYY-MM-DD.json` (New York date)
4. Commits and pushes only projection artifacts when changed.

### Files committed by the workflow
- `dbb2-engine/output/players.json`
- `dbb2-engine/output/projections.json`
- `dbb2-engine/output/risk.json`
- `dbb2-engine/output/insights.json`
- `dbb2-engine/output/betting_contract.json`
- `betting-engine/data/projections/YYYY-MM-DD.json`

## Running Betting CSV Pipeline After Projections

After the daily projection commit lands, run your existing betting pipeline as needed:

```bash
cd betting-engine
./run.sh
```

Or run the manual GitHub workflow fallback in `.github/workflows/nightly-pipeline.yml`.

## Notes
- `nightly-pipeline.yml` is now manual (`workflow_dispatch`) legacy fallback only.
- `daily-bets.yml` remains a manual fallback workflow.
- `daily-grading.yml` remains scheduled for grading/ledger updates.
