# Changelog

All notable changes to this repository are tracked here.

## 2026-02-24

### CI / Automation
- Scheduled nightly betting flow by updating `.github/workflows/nightly-pipeline.yml` to run daily.
- Added concurrency guard for nightly pipeline runs.
- Updated `.github/workflows/exchange-engine-daily.yml` to fail fast when `DBB2_API_URL` is missing (no silent skip).
- Added `.github/workflows/nightly-bets-guard.yml` to fail when no nightly betting outputs are detected.

### Ops / Handoff
- Added root `agent.md` with restart context, workflow map, run commands, and active TODO/risk-overlay notes.

### Reporting
- Regenerated and re-synced historical/today bet pages through `Daily Grading` pipeline to reflect graded outcomes (including 2026-02-20 results: 1W / 3L).
