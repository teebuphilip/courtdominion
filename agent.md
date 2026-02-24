# CourtDominion Agent Handoff

Last updated: 2026-02-24 (local workspace scan)

## Scope I Reviewed
- Root markdown files:
  - `README.md`
  - `CODEBASE_TLDR.md`
  - `DEBUGGING_GUIDE.md`
  - `DOCKER_CHEATSHEET.md`
  - `GITHUB_ACTIONS_README.md`
  - `JOBS_TLDR.md`
  - `TESTING.md`
  - `TODO.md`
- GitHub workflows:
  - `.github/workflows/daily-projections.yml`
  - `.github/workflows/daily-grading.yml`
  - `.github/workflows/exchange-engine-daily.yml`
  - `.github/workflows/nightly-pipeline.yml`
  - `.github/workflows/daily-bets.yml`
  - `.github/workflows/dfsrase-public-model.yml`
- Engine directories:
  - `dbb2-engine/`
  - `betting-engine/`
  - `exchange-engine/`

## Fast Resume Checklist
1. `cd /Users/teebuphilip/Documents/work/courtdominion`
2. Check current automation health:
   - `gh run list --limit 10`
   - confirm `Daily DBB2 Projections`, `Daily Grading`, `Exchange Engine Daily`
3. Check freshest artifacts:
   - `ls -lt dbb2-engine/output`
   - `ls -lt betting-engine/data/projections betting-engine/data/risk`
   - `ls -lt exchange-engine/data/risk exchange-engine/data/orders`
4. If running locally:
   - DBB2: `python dbb2-engine/run_engine.py --game-day --validate --output-dir dbb2-engine/output`
   - Betting: `(cd betting-engine && ./run.sh)`
   - Exchange: `(cd exchange-engine && python -m src.bet_placer)`

## System Snapshot
- Monorepo with three active engines:
  - `dbb2-engine`: projection producer + API contract exporter.
  - `betting-engine`: sportsbook/Kalshi/Polymarket-demo EV + Kelly + slips + grading.
  - `exchange-engine`: Novig/ProphetX exchange EV + Kelly + order lifecycle.
- Daily flow:
  - DBB2 generates `betting_contract.json` + `risk.json`.
  - Workflow copies DBB2 contract/risk into betting + exchange dated data folders.
  - Betting and exchange pipelines consume those files and generate slips/orders/ledger outputs.

## Workflow Reality (Important)
- `daily-projections.yml`
  - Triggered hourly UTC, gated to run only at 04:00 `America/New_York`.
  - Generates DBB2 outputs and copies:
    - `betting-engine/data/projections/YYYY-MM-DD.json`
    - `betting-engine/data/risk/YYYY-MM-DD.json`
    - `exchange-engine/data/risk/YYYY-MM-DD.json`
- `exchange-engine-daily.yml`
  - Scheduled `30 9 * * *` (roughly 4:30/5:30 ET depending DST).
  - Requires `DBB2_API_URL` secret or it skips.
- `daily-grading.yml`
  - Scheduled `0 16 * * *` (11:00/12:00 ET depending DST).
  - Grades slips, updates ledgers/results, generates/syncs report pages to `free-site/public`.
- `nightly-pipeline.yml`
  - Manual legacy end-to-end fallback.
- `daily-bets.yml`
  - Manual retired fallback.

## Engine Entry Points
- DBB2
  - CLI: `dbb2-engine/run_engine.py`
  - API: `dbb2-engine/engine/api.py`
  - Key outputs: `dbb2-engine/output/{players,projections,risk,insights,betting_contract}.json`
- Betting
  - Orchestrator: `betting-engine/src/bet_placer.py`
  - Scripted run: `betting-engine/run.sh`
  - Config: `betting-engine/config/settings.json`
  - Key outputs: `betting-engine/data/{bet_slips,bets,results,ledger*.json,risk,projections}`
- Exchange
  - Orchestrator: `exchange-engine/src/bet_placer.py`
  - Scripted run: `exchange-engine/run.sh`
  - Config: `exchange-engine/config/settings.json`
  - Key outputs: `exchange-engine/data/{projections,exchange_odds,ev_results,sized_bets,orders,ledger.json}`

## Active Risk Overlay Track
- Both betting and exchange configs include `risk_overlay` with `mode: "observe"`.
- Enhanced outputs are written in parallel:
  - Betting: `data/bet_slips_enhanced`, `data/bets/master_bets_enhanced.csv`, `data/ledger_enhanced.json`
  - Exchange: `data/sized_bets_enhanced`, `data/bet_slips_enhanced`, `data/orders_enhanced`
- Root `TODO.md` still calls out migration follow-up for expanded risk fields:
  - `availability_risk`, `role_risk`, `composition_risk`, `total_risk`, `risk_level`

## Secrets/Env Dependencies
- Betting workflows/pipeline:
  - `ODDS_API_KEY`
  - `KALSHI_API_KEY_ID`
  - `KALSHI_PRIVATE_KEY`
- Exchange workflow/pipeline:
  - `DBB2_API_URL` (required for run)
  - `NOVIG_ODDS_URL` (optional)
  - `PROPHETX_ODDS_URL` (optional)

## High-Value Files To Open First Next Session
1. `.github/workflows/daily-projections.yml`
2. `.github/workflows/daily-grading.yml`
3. `.github/workflows/exchange-engine-daily.yml`
4. `betting-engine/src/bet_placer.py`
5. `exchange-engine/src/bet_placer.py`
6. `dbb2-engine/run_engine.py`
7. `TODO.md`

## Practical Notes
- There are committed runtime artifacts in `data/` and `output/`; avoid broad refactors that assume these are clean/generated-only.
- `exchange-engine/src/__pycache__/` and some compiled files are present in repo paths; avoid touching unless explicitly cleaning.
- Most operational breakages are secrets/schedule gating/date path issues rather than code syntax.

## If You Want Me To Continue Instantly Next Time
- Tell me one of:
  - “Check today’s workflow health and summarize failures.”
  - “Run local dry-run for betting + exchange and report diffs.”
  - “Finish risk migration TODO end-to-end.”
