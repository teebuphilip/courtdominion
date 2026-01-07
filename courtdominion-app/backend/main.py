"""
CourtDominion Backend API
Main application entry point.

Per Backend Master Specification:
- Serves insights via REST API
- Supports automation pipelines
- Provides deterministic, stable output
- Runs locally via Docker
- Runs in production via Railway
- Stateless (no database in Phase 1)

Architecture:
- FastAPI framework
- Modular routers
- Service layer for business logic
- Pydantic models for validation
- Reads JSON from DATA_DIR (written by automation)
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all routers
from routers import health, players, projections, insights, content


# Read environment variables (per Backend Master Spec section 7)
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DATA_DIR = os.getenv("DATA_DIR", "/data/outputs")

# Validate environment variables on startup
print(f"[BACKEND] Starting CourtDominion Backend")
print(f"[BACKEND] ENVIRONMENT: {ENVIRONMENT}")
print(f"[BACKEND] BACKEND_URL: {BACKEND_URL}")
print(f"[BACKEND] DATA_DIR: {DATA_DIR}")

# Ensure DATA_DIR exists
os.makedirs(DATA_DIR, exist_ok=True)


# Create FastAPI application
app = FastAPI(
    title="CourtDominion Backend",
    description="Fantasy Basketball Insights Engine API",
    version="1.0.0",
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(health.router)
app.include_router(players.router)
app.include_router(projections.router)
app.include_router(insights.router)
app.include_router(content.router)


# Root endpoint
@app.get("/")
def root():
    """
    Root endpoint providing API information.
    """
    return {
        "service": "CourtDominion Backend",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "players": "/players",
            "projections": "/projections",
            "insights": "/insights",
            "content": "/api/content",
            "risk_metrics": "/risk-metrics",
            "lineup_suggestions": "/lineup-suggestions (POST)",
            "player_detail": "/player/{player_id}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    # For local development only
    uvicorn.run(app, host="0.0.0.0", port=8000)
