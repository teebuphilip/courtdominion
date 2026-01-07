"""
Internal API Router
Provides private API endpoints for microservices to consume Phase 1 data.

SECURITY: This endpoint is protected by API key authentication.
Only internal services should have access to the INTERNAL_API_KEY.
"""

from fastapi import APIRouter, Header, HTTPException
from typing import List, Dict, Any
import os
from datetime import datetime

from shared.load_shared_outputs import load_players, load_projections, get_data_dir

router = APIRouter(tags=["internal"])

# Secret API key from environment variable (set in Railway/Docker)
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")


@router.get("/api/internal/baseline-projections")
async def get_baseline_projections(
    x_api_key: str = Header(...)
):
    """
    Internal API for microservices.

    Returns all player projections + historical data for use by
    Features 1-7 microservices.

    Security:
        - Requires X-API-Key header matching INTERNAL_API_KEY
        - Returns 401 if key is invalid or missing

    Returns:
        JSON with:
        - players: List of player objects with projections and history
        - last_updated: Timestamp of data generation
        - count: Total number of players

    Raises:
        HTTPException 401: Invalid or missing API key
        HTTPException 503: API key not configured on server
    """

    # Check if API key is configured
    if not INTERNAL_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Internal API key not configured on server"
        )

    # Validate API key
    if x_api_key != INTERNAL_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    # Load data
    players = load_players()
    projections = load_projections()

    # Combine players with their projections
    # Create a lookup map for projections by player_id
    projections_map = {
        p.get("player_id"): p for p in projections
    }

    # Build combined response
    combined_data = []

    for player in players:
        player_id = player.get("player_id")
        projection = projections_map.get(player_id, {})

        # Combine player info with projection data
        player_data = {
            "player_id": player_id,
            "name": player.get("name", "Unknown"),
            "team": player.get("team", "N/A"),
            "position": player.get("position", "N/A"),
            "age": player.get("age", 0),

            # Projections
            "fantasy_points": projection.get("fantasy_points", 0.0),
            "points": projection.get("points_per_game", 0.0),
            "rebounds": projection.get("rebounds_per_game", 0.0),
            "assists": projection.get("assists_per_game", 0.0),
            "steals": projection.get("steals_per_game", 0.0),
            "blocks": projection.get("blocks_per_game", 0.0),
            "turnovers": projection.get("turnovers_per_game", 0.0),
            "three_pointers": projection.get("three_pointers_per_game", 0.0),
            "fg_pct": projection.get("field_goal_pct", 0.0),
            "ft_pct": projection.get("free_throw_pct", 0.0),
            "minutes": projection.get("minutes_per_game", 0.0),

            # Historical data (for risk modeling by microservices)
            "games_played_3yr": projection.get("games_played_history", []),
            "injury_history": {
                "total_games_missed_3yr": projection.get("total_games_missed", 0),
                "severe_injuries": projection.get("severe_injury_count", 0)
            }
        }

        combined_data.append(player_data)

    # Get last updated timestamp from data directory
    last_updated = get_last_cache_update()

    return {
        "players": combined_data,
        "last_updated": last_updated,
        "count": len(combined_data)
    }


def get_last_cache_update() -> str:
    """
    Get timestamp of last cache update.

    Checks manifest.json for timestamp, falls back to current time.

    Returns:
        ISO 8601 timestamp string
    """
    import json

    data_dir = get_data_dir()
    manifest_path = data_dir / "manifest.json"

    try:
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                return manifest.get("timestamp", datetime.utcnow().isoformat())
    except Exception:
        pass

    # Fallback to current time
    return datetime.utcnow().isoformat()
