# TODO

## Risk Migration Follow-Up

- [ ] Implement plan in `docs/enhanced-risk-shadow-ledger-plan.md`
- [ ] Update `betting-engine` to consume new `dbb2-engine` risk fields from `risk.json`:
  - `availability_risk`
  - `role_risk`
  - `composition_risk`
  - `total_risk`
  - `risk_level`
- [ ] Update `exchange-engine` to consume new `dbb2-engine` risk fields from `risk.json`:
  - `availability_risk`
  - `role_risk`
  - `composition_risk`
  - `total_risk`
  - `risk_level`

## Feature Roadmap

### Roster Gap/Needs Analysis (Medium Value, Medium Effort)

- [ ] Define API contract for stateless roster-gap analysis (no persistence required):
  - Request:
    - `roster_player_ids: string[]`
    - `weekly_targets: { [category]: number }`
    - optional `games_per_week_assumption`
  - Response:
    - per-category `current`, `target`, `remaining`, `on_track`
    - normalized `per_player_per_game_needed`
    - ranked `priority_categories`
- [ ] Implement pure service module under `dbb2-engine/engine/`:
  - derive weekly totals from DBB2 per-game projections
  - compute category gaps and pacing math
  - return deterministic sorted output for UI/API consumers
- [ ] Add endpoint `POST /tools/roster/gap-analysis` in `engine/api.py`.
- [ ] Add input validation:
  - empty roster handling
  - invalid categories
  - duplicate player IDs
  - target values < 0
- [ ] Add tests:
  - happy path with known sample players
  - empty roster behavior
  - unsupported category rejection
  - deterministic priority ordering
- [ ] Add docs in `dbb2-engine/API_DOCUMENTATION.md` with request/response examples.

### Historical Persistence Layer For Projections (High Value, Higher Effort)

- [ ] Decide storage target and ops constraints:
  - PostgreSQL on Railway (preferred) vs alternative
  - retention window and storage budget
  - deployment topology (DBB2 API + ingestion worker)
- [ ] Define schema (v1):
  - `projection_runs` (run metadata: timestamp, source commit, season mode)
  - `player_projections_daily` (one row per player per run date)
  - `player_risk_daily` (risk fields for betting/exchange analytics)
  - optional `model_diagnostics_daily` (distribution/drift snapshots)
- [ ] Add migration tooling (Alembic or equivalent) and bootstrap scripts.
- [ ] Build idempotent ingest job:
  - input from `dbb2-engine/output/*.json`
  - upsert by (`run_date`, `player_id`)
  - write run status and row counts
  - fail loudly on partial writes
- [ ] Add backfill job for historical flat files.
- [ ] Add data quality checks:
  - row count thresholds
  - null/shape validation
  - duplicate key checks
  - anomaly checks on projection deltas
- [ ] Add analytics query layer (read-only):
  - player projection trend (7/30-day)
  - largest movers day-over-day
  - model calibration snapshots vs actuals (when outcomes wired)
- [ ] Add scheduled run and observability:
  - daily ingestion cron
  - metrics/logging for job duration, inserted/updated rows, failures
  - alert routing for ingestion failures
- [ ] Add rollback and disaster-recovery notes:
  - migration rollback steps
  - backup/restore procedure
  - replay from flat-file artifacts

### Roster Decision Assistant (Depends On Gap Analysis + Similarity)

- [ ] Define assistant scope (stateless first):
  - input roster + targets
  - output recommended adds/drops/streams with reasons
  - no user auth/state in v1
- [ ] Build recommendation logic:
  - start from roster-gap priorities
  - candidate pool from `streaming-candidates` + `similar-players`
  - score candidates by projected category lift per roster slot
  - apply configurable constraints (position fit, min confidence, risk filters)
- [ ] Add endpoint `POST /tools/roster/decision-assistant`.
- [ ] Return explainable output:
  - recommendation rank
  - expected lift by category
  - confidence/risk summary
  - short rationale text for UI
- [ ] Add guardrails:
  - max recommendation count
  - prevent duplicate suggestions already on roster
  - deterministic tie-breakers
- [ ] Add tests:
  - consistent recommendation order
  - respects constraints
  - handles no-solution scenarios
- [ ] Add docs and example payloads in `dbb2-engine/API_DOCUMENTATION.md`.
