# Exchange Engine Docker Guide

This guide is for running `exchange-engine` on your desktop using Docker Desktop.

## 1. Prerequisites

1. Docker Desktop installed and running.
2. DBB2 API reachable from your machine.
3. Optional exchange source endpoints if you want live Novig/ProphetX fetches.

## 2. Configure Environment

From repo root:

```bash
cd exchange-engine
cp .env.example .env
```

Edit `.env`:

```bash
DBB2_API_URL=http://host.docker.internal:8000
NOVIG_ODDS_URL=
PROPHETX_ODDS_URL=
```

- `DBB2_API_URL` is required for projections.
- `NOVIG_ODDS_URL` and `PROPHETX_ODDS_URL` are optional.

## 3. Build and Run

From `exchange-engine/`:

```bash
docker compose build
docker compose run --rm exchange-engine
```

This executes `./run.sh` which runs:

```bash
python -m src.bet_placer
```

## 4. Output Files

Outputs persist locally in mounted folders:

- `exchange-engine/data/projections/`
- `exchange-engine/data/exchange_odds/`
- `exchange-engine/data/ev_results/`
- `exchange-engine/data/sized_bets/`
- `exchange-engine/data/bet_slips/`
- `exchange-engine/data/orders/`
- `exchange-engine/logs/`

## 5. Common Commands

```bash
# Rebuild after code changes
docker compose build

# Open shell inside container
docker compose run --rm exchange-engine bash

# Run tests inside container
docker compose run --rm exchange-engine python -m pytest -q tests

# Run dry-run orchestration
docker compose run --rm exchange-engine python -m src.bet_placer --dry-run
```

## 6. Troubleshooting

### No projections

- Verify DBB2 API is running.
- Confirm `DBB2_API_URL` in `.env`.

### No odds for one source

- Check that source URL exists in `.env`.
- Confirm endpoint returns normalized shape expected by this phase-1 engine.

### Files not appearing

- Confirm you run from `exchange-engine/` where `docker-compose.yml` lives.
- Check `exchange-engine/logs/`.
