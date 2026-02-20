# DBB2 Engine API Documentation

This document is the full API reference for the new `dbb2-engine` service (`engine/api.py`).

## Base

- Local base URL: `http://localhost:8000`
- Framework: FastAPI
- Service file: `dbb2-engine/engine/api.py`
- OpenAPI/Swagger UI (when running): `GET /docs`
- OpenAPI JSON: `GET /openapi.json`

## Run The API

## Local (Python)

```bash
cd ~/Documents/work/courtdominion/dbb2-engine
source ~/venvs/cd39/bin/activate
uvicorn engine.api:app --host 0.0.0.0 --port 8000
```

## Docker

```bash
cd ~/Documents/work/courtdominion/dbb2-engine
docker build -t dbb2-engine .
docker run --rm -p 8000:8000 dbb2-engine
```

## Authentication

Most endpoints are public.

One endpoint is protected:

- `GET /api/internal/baseline-projections`

It requires header:

- `X-API-Key: <value>`

Validation source:

- Environment variable `INTERNAL_API_KEY`

Failure behavior:

- `503` if `INTERNAL_API_KEY` is not configured on server
- `401` if header is missing/invalid

## Caching Behavior

The API loads the full projection pipeline once per process and caches it in-memory using `@lru_cache(maxsize=1)`.

Implications:

- First request can be slower (pipeline build)
- Subsequent requests are fast (same in-memory snapshot)
- Data refresh requires process restart (or cache-clear code change)

---

## 1) Health

### `GET /health`

Basic liveness check.

### Response `200`

```json
{
  "status": "ok",
  "engine": "dbb2",
  "version": "1.0.0"
}
```

---

## 2) Betting Contract Projections

### `GET /projections/today`

Returns the betting-engine contract shape for all projected players.

### Response `200`

```json
{
  "players": [
    {
      "id": "203999",
      "name": "Nikola Jokic",
      "team": "DEN",
      "position": "C",
      "is_b2b": false,
      "pts": 26.8,
      "pts_std": 5.42,
      "pts_conf": 0.72,
      "reb": 12.1,
      "reb_std": 2.88,
      "reb_conf": 0.69,
      "ast": 8.9,
      "ast_std": 2.41,
      "ast_conf": 0.7,
      "fg3m": 1.2,
      "fg3m_std": 0.66,
      "fg3m_conf": 0.61,
      "stl": 1.3,
      "stl_std": 0.54,
      "stl_conf": 0.67,
      "blk": 0.9,
      "blk_std": 0.5,
      "blk_conf": 0.62
    }
  ]
}
```

### Field Notes

- `position` is the raw position from context (e.g., `G-F`, `C`)
- `*_std` derives from variance in player context (`sqrt(variance)`)
- `*_conf` is clamped to `[0.40, 0.95]`

---

## 3) Internal Baseline Projections (Protected)

### `GET /api/internal/baseline-projections`

Internal parity endpoint intended for service-to-service consumers.

### Headers

- `X-API-Key: <INTERNAL_API_KEY>`

### Response `200`

```json
{
  "players": [
    {
      "player_id": "203999",
      "name": "Nikola Jokic",
      "team": "DEN",
      "position": "C",
      "age": 30,
      "fantasy_points": 50.7,
      "points": 26.8,
      "rebounds": 12.1,
      "assists": 8.9,
      "steals": 1.3,
      "blocks": 0.9,
      "turnovers": 3.1,
      "three_pointers": 1.2,
      "fg_pct": 0.577,
      "ft_pct": 0.822,
      "minutes": 34.1,
      "games_played_3yr": [],
      "injury_history": {
        "total_games_missed_3yr": 0,
        "severe_injuries": 0
      },
      "auction_dollar": 66,
      "consistency": 81
    }
  ],
  "count": 1
}
```

### Error Responses

`401`
```json
{"detail":"Invalid API key"}
```

`503`
```json
{"detail":"Internal API key not configured on server"}
```

---

## 4) Advanced Tool: Lineup Optimizer

### `POST /tools/lineup/optimize`

Selects the best lineup by projected fantasy points from a provided player ID pool.

### Request Body

```json
{
  "player_ids": ["203999", "1629029", "201939"],
  "roster_size": 2
}
```

### Constraints

- `roster_size` must be `> 0`

### Response `200`

```json
{
  "lineup": [
    {
      "player_id": "203999",
      "name": "Nikola Jokic",
      "team": "DEN",
      "position": "C",
      "fantasy_points": 50.7
    },
    {
      "player_id": "1629029",
      "name": "Luka Doncic",
      "team": "DAL",
      "position": "G",
      "fantasy_points": 49.9
    }
  ],
  "bench": [
    {
      "player_id": "201939",
      "name": "Stephen Curry",
      "team": "GSW",
      "position": "G",
      "fantasy_points": 39.2
    }
  ],
  "projected_total_fantasy_points": 100.6
}
```

### Error Response `400`

```json
{"detail":"roster_size must be > 0"}
```

---

## 5) Advanced Tool: Streaming Candidates

### `GET /tools/streaming-candidates`

Returns value stream candidates ranked by `stream_score`.

### Query Params

- `limit` (optional, default `10`, min `1`, max `50`)

### Example

`GET /tools/streaming-candidates?limit=5`

### Response `200`

```json
{
  "candidates": [
    {
      "player_id": "1620001",
      "name": "Sample Player",
      "team": "LAL",
      "position": "G-F",
      "fantasy_points": 28.4,
      "auction_dollar": 3,
      "stream_score": 9.47
    }
  ],
  "count": 1
}
```

### Ranking Logic

- `stream_score = fantasy_points / max(auction_dollar, 1)`
- Sorted by:
1. `stream_score` descending
2. `fantasy_points` descending

---

## 6) Advanced Tool: Trade Analyzer

### `POST /tools/trade/analyze`

Compares outgoing and incoming player packages by fantasy points and auction value.

### Request Body

```json
{
  "give_player_ids": ["201939"],
  "receive_player_ids": ["203999"]
}
```

### Response `200`

```json
{
  "give": [
    {
      "player_id": "201939",
      "name": "Stephen Curry",
      "fantasy_points": 39.2,
      "auction_dollar": 44
    }
  ],
  "receive": [
    {
      "player_id": "203999",
      "name": "Nikola Jokic",
      "fantasy_points": 50.7,
      "auction_dollar": 66
    }
  ],
  "summary": {
    "give_fantasy_points": 39.2,
    "receive_fantasy_points": 50.7,
    "delta_fantasy_points": 11.5,
    "give_auction_dollar": 44,
    "receive_auction_dollar": 66,
    "delta_auction_dollar": 22,
    "verdict": "accept"
  }
}
```

### Verdict Logic

- `accept` if:
  - `delta_fantasy_points > 0` and `delta_auction_dollar >= -3`, or
  - `delta_auction_dollar > 0`
- otherwise `decline`

---

## Common Error Model

FastAPI default error shape:

```json
{
  "detail": "Error message"
}
```

Validation errors (422) include structured details:

```json
{
  "detail": [
    {
      "loc": ["body", "player_ids"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Curl Examples

## Health

```bash
curl -s http://localhost:8000/health
```

## Projections

```bash
curl -s http://localhost:8000/projections/today | jq '.players[0]'
```

## Internal Baseline (Protected)

```bash
curl -s \
  -H "X-API-Key: ${INTERNAL_API_KEY}" \
  http://localhost:8000/api/internal/baseline-projections | jq '.count'
```

## Lineup Optimizer

```bash
curl -s -X POST http://localhost:8000/tools/lineup/optimize \
  -H "Content-Type: application/json" \
  -d '{"player_ids":["203999","1629029","201939"],"roster_size":2}' | jq
```

## Streaming Candidates

```bash
curl -s "http://localhost:8000/tools/streaming-candidates?limit=10" | jq '.candidates[0]'
```

## Trade Analyzer

```bash
curl -s -X POST http://localhost:8000/tools/trade/analyze \
  -H "Content-Type: application/json" \
  -d '{"give_player_ids":["201939"],"receive_player_ids":["203999"]}' | jq '.summary'
```

---

## Notes For Consumers

- IDs are string player IDs.
- Unknown player IDs in tool payloads are ignored (not fatal).
- Returned totals only include recognized players present in the loaded pipeline.
- Because data is cached in-process, restart API to force fresh data snapshot.
