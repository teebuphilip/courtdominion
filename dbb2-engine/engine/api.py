"""
FastAPI server exposing DBB2 projections for the betting engine.

Single endpoint: GET /projections/today
Returns per-player per-stat projections with std_dev and confidence,
matching the contract expected by the betting engine.
"""

import math
from functools import lru_cache
from typing import Dict, List

from fastapi import FastAPI

from engine import project_all_season
from engine.baseline import PlayerContext
from engine.projections import SeasonProjection

app = FastAPI(title="DBB2 Projection API", version="1.0.0")

# Map engine stat names to betting engine short names
STAT_MAP = {
    "points": "pts",
    "rebounds": "reb",
    "assists": "ast",
    "three_pm": "fg3m",
    "steals": "stl",
    "blocks": "blk",
}

# Variance key format in PlayerContext.stat_variance
VARIANCE_KEY_MAP = {
    "points": "points_variance",
    "rebounds": "rebounds_variance",
    "assists": "assists_variance",
    "three_pm": "three_pm_variance",
    "steals": "steals_variance",
    "blocks": "blocks_variance",
}


@lru_cache(maxsize=1)
def _load_projections():
    """Run the full pipeline once and cache results."""
    contexts, projections, _ = project_all_season()
    return contexts, projections


def _get_std_dev(ctx: PlayerContext, stat: str) -> float:
    """Get std_dev for a stat from PlayerContext.stat_variance."""
    var_key = VARIANCE_KEY_MAP.get(stat)
    if var_key is None:
        return 0.0
    variance = ctx.stat_variance.get(var_key, 0.0)
    return math.sqrt(max(variance, 0.0))


def _get_confidence(
    projection_value: float,
    std_dev: float,
    base_confidence: float,
) -> float:
    """
    Derive per-stat confidence from consistency and coefficient of variation.

    base_confidence = consistency / 100 (global player consistency)
    Adjusted down by CV: higher variance relative to mean = lower confidence.
    Clamped to [0.40, 0.95].
    """
    if projection_value <= 0 or std_dev <= 0:
        return round(max(0.40, base_confidence * 0.8), 2)

    cv = std_dev / projection_value
    conf = base_confidence * (1 - min(cv, 0.5))
    return round(max(0.40, min(0.95, conf)), 2)


def _build_player_response(
    ctx: PlayerContext,
    proj: SeasonProjection,
) -> Dict:
    """Build the betting engine response shape for one player."""
    base_conf = proj.consistency / 100.0

    result = {
        "id": ctx.player_id,
        "name": ctx.player_name,
        "team": ctx.team,
        "position": ctx.raw_position,
        "is_b2b": ctx.is_b2b,
    }

    for engine_stat, short_name in STAT_MAP.items():
        proj_val = getattr(proj, engine_stat, 0.0)
        std_dev = _get_std_dev(ctx, engine_stat)
        confidence = _get_confidence(proj_val, std_dev, base_conf)

        result[short_name] = round(proj_val, 1)
        result[f"{short_name}_std"] = round(std_dev, 2)
        result[f"{short_name}_conf"] = confidence

    return result


@app.get("/projections/today")
def get_today_projections():
    """Return all player projections in the betting engine contract shape."""
    contexts, projections = _load_projections()

    ctx_map = {c.player_id: c for c in contexts}
    players = []

    for proj in projections:
        ctx = ctx_map.get(proj.player_id)
        if ctx is None:
            continue
        players.append(_build_player_response(ctx, proj))

    return {"players": players}


@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok", "engine": "dbb2", "version": "1.0.0"}
