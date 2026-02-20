# DFSRASE

Public Bankroll Model v1 for CourtDominion.

## Purpose

Run one deterministic bankroll simulation nightly:

- Start date: `2026-02-28`
- Starting bankroll: `$5,000.00`
- Wager rule:
  - `green`: 5%
  - `yellow`: 2%
  - `red`: 0%
- Payout rule (v1 locked):
  - if `auction_score_actual > projection_score_actual` => `1.5x wager`
  - else `0`

This repo is read-only/public modeling output. It has no auth, no user input, no real-money execution.

## Data Files

- `dfsrase/data/bankroll_history.json`
- `dfsrase/data/public_model_summary.json`
- `dfsrase/data/daily_slate_inputs/{YYYY-MM-DD}.json` (optional input cache)

## Local Run

```bash
cd ~/Documents/work/courtdominion
source ~/venvs/cd39/bin/activate
python dfsrase/src/public_model.py --date 2026-03-01
python scripts/generate_dfsrase_page.py
```
