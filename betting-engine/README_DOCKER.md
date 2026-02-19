# Betting Engine Docker Guide

This guide is for running `betting-engine` on your desktop using Docker Desktop.

## 1. Prerequisites

1. Docker Desktop installed and running.
2. DBB2 API reachable from your machine.
3. The following secrets available:
   - `ODDS_API_KEY`
   - `KALSHI_API_KEY_ID` (optional unless using Kalshi flow)
   - `KALSHI_PRIVATE_KEY` (optional unless using Kalshi flow)

## 2. Configure Environment

From repo root:

```bash
cd betting-engine
cp .env.example .env
```

Edit `.env` and set at minimum:

```bash
ODDS_API_KEY=your_odds_api_key
DBB2_API_URL=http://host.docker.internal:8000
```

Optional Kalshi values:

```bash
KALSHI_API_KEY_ID=...
KALSHI_PRIVATE_KEY=...
```

## 3. Build and Run

From `betting-engine/`:

```bash
docker compose build
docker compose run --rm betting-engine
```

This runs `./run.sh` inside the container.

## 4. Output Files

Because volumes are mounted, outputs persist on your machine in:

- `betting-engine/data/`
- `betting-engine/logs/`

## 5. Common Commands

```bash
# Rebuild image after code changes
docker compose build

# Run one-off shell in container
docker compose run --rm betting-engine bash

# Run just bet placer directly
docker compose run --rm betting-engine python src/bet_placer.py
```

## 6. Troubleshooting

### Cannot reach DBB2 API

- Make sure DBB2 API is running.
- Verify `.env` has correct `DBB2_API_URL`.
- On macOS Docker Desktop, `host.docker.internal` is the right host alias.

### Missing odds key

- Confirm `ODDS_API_KEY` is set in `.env`.

### No output files

- Check logs in `betting-engine/logs/`.
- Run interactive shell and inspect:
  - `docker compose run --rm betting-engine bash`
  - `ls -la data`
