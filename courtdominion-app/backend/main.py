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
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Import all routers
from routers import health, players, projections, insights, content, internal


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
# WHY: Wildcard + credentials = CSRF vulnerability. Attacker site can make
# authenticated requests on behalf of logged-in users.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Explicit allowlist, no wildcards
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Only methods we use
    allow_headers=["x-api-key", "x-admin-key", "content-type"],  # Only headers we need
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Add browser security headers to all responses.

    WHY: Defense in depth. Even if XSS gets through, these headers
    limit what an attacker can do.
    """
    response = await call_next(request)

    # Prevent MIME-type sniffing (IE XSS vector)
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Force HTTPS (browser remembers for 1 year)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Don't cache API responses (sensitive data)
    response.headers["Cache-Control"] = "no-store"

    # Disable browser features we don't need
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    return response


# Include all routers
app.include_router(health.router)
app.include_router(players.router)
app.include_router(projections.router)
app.include_router(insights.router)
app.include_router(content.router)
app.include_router(internal.router)


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
            "internal_api": "/api/internal/baseline-projections (Requires X-API-Key)",
            "risk_metrics": "/risk-metrics",
            "lineup_suggestions": "/lineup-suggestions (POST)",
            "player_detail": "/player/{player_id}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    # For local development only
    uvicorn.run(app, host="0.0.0.0", port=8000)
