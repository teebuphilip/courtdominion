# CourtDominion Backend (Hybrid)
This repo includes legacy projection engine (app/legacy) and a thin FastAPI wrapper to run projections.

Quickstart (Docker):
1. docker compose build
2. docker compose up -d
3. curl http://localhost:8000/health
4. curl -X POST http://localhost:8000/v1/run_projections -H 'Content-Type: application/json' -d '{}'
