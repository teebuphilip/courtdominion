"""
Export projections in the betting engine contract format.

Mirrors the /projections/today API response but writes to a JSON file
so GitHub Actions can consume it without running the FastAPI server.

Uses the same std_dev/confidence logic as engine/api.py but avoids
importing from api.py to prevent circular imports.
"""

import json
import math
from pathlib import Path
from typing import Dict, List

from engine.baseline import PlayerContext
from engine.projections import SeasonProjection

# Same mappings as engine/api.py
STAT_MAP = {
    "points": "pts",
    "rebounds": "reb",
    "assists": "ast",
    "three_pm": "fg3m",
    "steals": "stl",
    "blocks": "blk",
}

VARIANCE_KEY_MAP = {
    "points": "points_variance",
    "rebounds": "rebounds_variance",
    "assists": "assists_variance",
    "three_pm": "three_pm_variance",
    "steals": "steals_variance",
    "blocks": "blocks_variance",
}


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
    """Derive per-stat confidence from consistency and coefficient of variation."""
    if projection_value <= 0 or std_dev <= 0:
        return round(max(0.40, base_confidence * 0.8), 2)
    cv = std_dev / projection_value
    conf = base_confidence * (1 - min(cv, 0.5))
    return round(max(0.40, min(0.95, conf)), 2)


def export_betting_contract(
    contexts: List[PlayerContext],
    projections: List[SeasonProjection],
    output_dir: str = "output",
) -> str:
    """
    Write output/betting_contract.json matching the betting engine's expected shape.

    Output format (normalized for odds_ingestion.py --from-file):
    { player_id: { name, team, position, is_b2b, props: { stat: { projection, std_dev, confidence } } } }
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    ctx_map = {c.player_id: c for c in contexts}
    result = {}

    for proj in projections:
        ctx = ctx_map.get(proj.player_id)
        if ctx is None:
            continue

        base_conf = proj.consistency / 100.0
        props = {}

        for engine_stat, short_name in STAT_MAP.items():
            proj_val = getattr(proj, engine_stat, 0.0)
            std_dev = _get_std_dev(ctx, engine_stat)
            confidence = _get_confidence(proj_val, std_dev, base_conf)

            # Map short names to betting engine prop names
            prop_name = {
                "pts": "points", "reb": "rebounds", "ast": "assists",
                "fg3m": "threes", "stl": "steals", "blk": "blocks",
            }[short_name]

            props[prop_name] = {
                "projection": round(proj_val, 1),
                "std_dev": round(std_dev, 2),
                "confidence": confidence,
            }

        result[ctx.player_id] = {
            "name": ctx.player_name,
            "team": ctx.team,
            "position": ctx.raw_position,
            "is_b2b": ctx.is_b2b,
            "props": props,
        }

    file_path = out_path / "betting_contract.json"
    with open(file_path, "w") as f:
        json.dump(result, f, indent=2)

    return str(file_path)
