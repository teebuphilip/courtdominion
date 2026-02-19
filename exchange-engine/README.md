# Exchange Engine (Novig + ProphetX)

This is a **minimal MAKE/TAKE exchange betting engine** for DBB2 projections.

It is a separate engine from `betting-engine` and lives in:

- `exchange-engine/`

## Operator Checklist (Daily)

1. `cd /Users/teebuphilip/Documents/work/courtdominion/exchange-engine`
2. `source ~/venvs/cd39/bin/activate` (or `cdpy`)
3. `python -m pytest -q tests` (quick health check)
4. Confirm `config/settings.json` thresholds are what you want for today.
5. Confirm env vars if using live source pulls:
   `NOVIG_ODDS_URL`, `PROPHETX_ODDS_URL`
6. Run engine: `python -m src.bet_placer`
7. Check outputs:
   `data/ev_results/YYYY-MM-DD.json`, `data/sized_bets/YYYY-MM-DD.json`
8. Check orders:
   `data/orders/YYYY-MM-DD.json`
9. Check slip:
   `data/bet_slips/YYYY-MM-DD.md`
10. Confirm bankroll source file is present:
    `data/ledger.json` (starts `$5000`, unit `$50`)

It does exactly this:

1. Fetch projections from DBB2
2. Fetch exchange odds from Novig + ProphetX
3. Normalize odds into one format
4. Compute edge (`projection vs line`)
5. Choose `TAKE` or `MAKE`
6. Size bets using Kelly
7. Create/submit orders
8. Track open orders with a small state machine
9. Write bet slips and order files

## 1. Before You Run Anything

On this machine, always activate the Python env first:

```bash
source ~/venvs/cd39/bin/activate
```

If you use your alias:

```bash
cdpy
```

All Python commands in this README assume the env is active.

## 2. Directory Layout

```text
exchange-engine/
  config/
    settings.json
  src/
    __init__.py
    common.py
    projections.py
    exchange_ingestion.py
    exchange_ev_calculator.py
    kelly_sizer.py
    bet_slip.py
    bet_placer.py
    ledger.py
    order_model.py
    order_manager.py
    novig/
      __init__.py
      client.py
      normalize.py
    prophetx/
      __init__.py
      client.py
      normalize.py
  data/
    projections/
    exchange_odds/
      novig/
      prophetx/
    ev_results/
    sized_bets/
    bet_slips/
    orders/
    ledger.json
  tests/
    fixtures/
    test_exchange_ev.py
    test_order_state_machine.py
    test_ledger.py
  requirements.txt
  run.sh
```

## 3. What Each File Does

- `src/common.py`
  - Shared utilities: JSON read/write, settings load, timestamp/date, logging.
- `src/projections.py`
  - Calls DBB2 projections endpoint and writes `data/projections/YYYY-MM-DD.json`.
- `src/exchange_ingestion.py`
  - Pulls source odds (Novig/ProphetX), normalizes, writes per-source files.
- `src/exchange_ev_calculator.py`
  - Core edge math + filters + TAKE/MAKE selection.
- `src/kelly_sizer.py`
  - Kelly sizing for each candidate bet.
  - Uses ledger bankroll when `use_ledger=True`.
- `src/ledger.py`
  - Paper bankroll tracking.
  - Starts at `$5000`, unit value is `bankroll / 100` (starts at `$50`).
- `src/order_model.py`
  - Order schema and state transition validation.
- `src/order_manager.py`
  - Poll loop for open orders; marks `FILLED` or `EXPIRED`.
- `src/bet_slip.py`
  - Writes daily slip outputs (`json` + `md`) with required columns.
- `src/bet_placer.py`
  - Main orchestrator: runs everything in order.
- `src/novig/client.py`, `src/prophetx/client.py`
  - Minimal source clients (URL from env vars).
- `src/novig/normalize.py`, `src/prophetx/normalize.py`
  - Normalize source payloads to common odds format.

## 4. Config (`config/settings.json`)

Current config:

- `dbb2_api`
  - `base_url`: DBB2 host (default: `http://localhost:8000`)
  - `projections_endpoint`: projection route (default: `/projections/today`)
  - `timeout_seconds`: HTTP timeout
- `ev_thresholds`
  - `take_edge_pct`: threshold for TAKE
  - `make_edge_pct`: threshold for MAKE
  - `min_confidence`: minimum projection confidence
  - `min_available_size`: minimum size available in chosen side
  - `max_bets_per_day`: output cap
- `kelly`
  - `fraction`: fractional Kelly multiplier
  - `max_units`: cap per bet
  - `min_units`: floor per bet
  - `bankroll`: fallback bankroll (overridden by ledger when enabled)
- `exchange`
  - `mode`: execution mode string
  - `time_in_force_seconds`: order TTL
  - `price_shade_pct`: configured for MAKE behavior
  - `fee_bps`: fee basis points
  - `include_sources`: `["novig", "prophetx"]`

## 5. Data Contracts

### 5.1 Projections input shape

File:

- `data/projections/YYYY-MM-DD.json`

Shape:

```json
{
  "LeBron James": {
    "team": "LAL",
    "is_b2b": false,
    "props": {
      "points": {
        "projection": 27.8,
        "std_dev": 4.1,
        "confidence": 0.71
      }
    }
  }
}
```

### 5.2 Normalized exchange odds shape

Files:

- `data/exchange_odds/novig/YYYY-MM-DD.json`
- `data/exchange_odds/prophetx/YYYY-MM-DD.json`

Shape:

```json
{
  "LeBron James": {
    "points": {
      "line": 26.5,
      "over": { "odds": -115, "available_size": 120 },
      "under": { "odds": -105, "available_size": 75 },
      "exchange": "novig"
    }
  }
}
```

### 5.3 EV output

File:

- `data/ev_results/YYYY-MM-DD.json`

Per-row fields:

- `player_name`
- `prop_type`
- `direction`
- `projection`
- `line`
- `raw_edge`
- `edge_pct`
- `confidence`
- `std_dev`
- `odds`
- `available_size`
- `source`
- `execution_type`

### 5.4 Kelly-sized output

File:

- `data/sized_bets/YYYY-MM-DD.json`

Adds:

- `units`
- `dollars`

### 5.5 Orders output

File:

- `data/orders/YYYY-MM-DD.json`

Per-order fields:

- `order_id`
- `timestamp`
- `exchange`
- `player_name`
- `prop_type`
- `direction`
- `line`
- `odds`
- `units`
- `dollars`
- `execution_type`
- `state`
- `time_in_force_seconds`

### 5.6 Bet slip output

Files:

- `data/bet_slips/YYYY-MM-DD.json`
- `data/bet_slips/YYYY-MM-DD.md`

Slip columns:

- `Player | Prop | Dir | Proj | Line | Edge% | Conf | Units | Odds | AvailSize | Source | ExecType`

## 6. Edge + Execution Logic

Math:

- `raw_edge = projection - line`
- `edge_pct = (raw_edge / std_dev) * 100`

Direction:

- `raw_edge > 0` -> `OVER`
- else -> `UNDER`

Filters:

- `abs(edge_pct) >= make_edge_pct`
- `confidence >= min_confidence`
- `available_size >= min_available_size`

Execution:

- `abs(edge_pct) >= take_edge_pct` -> `TAKE`
- else if `abs(edge_pct) >= make_edge_pct` -> `MAKE`
- else skip

## 7. Order State Machine

Allowed transitions:

- `NEW -> OPEN`
- `NEW -> FILLED`
- `OPEN -> FILLED`
- `OPEN -> EXPIRED`

States:

- `NEW`: created locally
- `OPEN`: posted (MAKE)
- `FILLED`: fully matched (TAKE immediate fill, or later fill)
- `EXPIRED`: timed out and canceled

## 8. Ledger and Bet Sizing

Ledger file:

- `data/ledger.json`

Defaults:

- `starting_bankroll`: `5000.0`
- `unit_value`: `50.0` (because bankroll / 100)

Kelly uses ledger bankroll in orchestrated run:

- `src/bet_placer.py` calls `run_kelly(..., use_ledger=True)`

So if bankroll changes later, Kelly sizing follows that bankroll automatically.

## 9. Environment Variables

Optional source URLs:

- `NOVIG_ODDS_URL`
- `PROPHETX_ODDS_URL`

If missing, source clients return `{}` and that source contributes no odds.

Optional config override:

- `CONFIG_PATH`

## 10. How to Run

From repo root:

```bash
cd exchange-engine
source ~/venvs/cd39/bin/activate
python -m src.bet_placer
```

Or:

```bash
cd exchange-engine
./run.sh
```

Dry run:

```bash
cd exchange-engine
source ~/venvs/cd39/bin/activate
python -m src.bet_placer --dry-run
```

Run modules individually:

```bash
python -m src.projections
python -m src.exchange_ingestion
python -m src.exchange_ev_calculator
python -m src.kelly_sizer --use-ledger
python -m src.bet_slip
python -m src.order_manager --max-cycles 1
```

## 11. Test Commands

Run tests:

```bash
cd exchange-engine
source ~/venvs/cd39/bin/activate
python -m pytest -q tests
```

Current suite includes:

- `tests/test_exchange_ev.py`
- `tests/test_order_state_machine.py`
- `tests/test_ledger.py`

## 12. Typical End-to-End Flow (What You Should See)

1. Projections file appears in `data/projections/`.
2. Per-source odds files appear in `data/exchange_odds/novig/` and `data/exchange_odds/prophetx/`.
3. Filtered EV candidates appear in `data/ev_results/`.
4. Kelly-sized bets appear in `data/sized_bets/`.
5. Orders are created in `data/orders/` with `state` set based on MAKE/TAKE behavior.
6. Bet slip files appear in `data/bet_slips/`.
7. Ledger remains in `data/ledger.json` and is used as bankroll source for sizing.

## 13. Troubleshooting

### Problem: `python -m pytest` says module missing

Do this:

```bash
source ~/venvs/cd39/bin/activate
python -m pytest -q tests
```

### Problem: no bets generated

Check these first:

1. `data/projections/YYYY-MM-DD.json` exists and has player props with `projection/std_dev/confidence`.
2. Odds files for included sources exist and contain matching player names.
3. `confidence` and `available_size` pass thresholds.
4. `edge_pct` passes `make_edge_pct`.

### Problem: one source is always empty

Confirm env var is set:

- `NOVIG_ODDS_URL` for Novig
- `PROPHETX_ODDS_URL` for ProphetX

### Problem: bankroll not using ledger

Verify:

1. `data/ledger.json` exists.
2. `src/bet_placer.py` calls `run_kelly(..., use_ledger=True)`.
3. Logs show `Using ledger bankroll: $...`.

## 14. Scope (What This Engine Does Not Do)

Phase-1 exclusions:

- Partial fills
- Queue logic
- Opponent profiling
- Auto repricing
- Hedging
- Maker rebates

## 15. Quick Start (Copy/Paste)

```bash
cd /Users/teebuphilip/Documents/work/courtdominion/exchange-engine
source ~/venvs/cd39/bin/activate
python -m pytest -q tests
python -m src.bet_placer --dry-run
```
