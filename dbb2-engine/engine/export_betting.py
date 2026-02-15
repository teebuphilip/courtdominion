"""
Export projections in the betting engine contract format.

Mirrors the /projections/today API response but writes to a JSON file
so GitHub Actions can consume it without running the FastAPI server.

Uses the same std_dev/confidence logic as engine/api.py but avoids
importing from api.py to prevent circular imports.

When game_day_projections are provided, exports adjusted values with
full adjustment breakdown. Backward compatible — omitting game_day
projections produces the same output as before.
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Optional

from engine.baseline import PlayerContext
from engine.projections import SeasonProjection
from engine.game_day import GameDayProjection

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

# Maps engine stat names to GameDayProjection attribute names
_GD_STAT_ATTR = {
    "points": "points",
    "rebounds": "rebounds",
    "assists": "assists",
    "three_pm": "three_pm",
    "steals": "steals",
    "blocks": "blocks",
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
    game_day_projections: Optional[List[GameDayProjection]] = None,
    output_dir: str = "output",
) -> str:
    """
    Write output/betting_contract.json matching the betting engine's expected shape.

    When game_day_projections is provided, the `projection` field contains the
    game-day adjusted value, with `season_projection` preserving the baseline.
    Additional fields `is_death_spot`, `death_spot_type`, `game_day_adjusted`,
    and `adjustments` are included for transparency.

    Output format (normalized for odds_ingestion.py --from-file):
    { player_id: { name, team, position, is_b2b, props: { stat: { projection, std_dev, confidence } } } }
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    ctx_map = {c.player_id: c for c in contexts}
    gd_map = {}
    if game_day_projections:
        gd_map = {g.player_id: g for g in game_day_projections}

    result = {}

    for proj in projections:
        ctx = ctx_map.get(proj.player_id)
        if ctx is None:
            continue

        gd = gd_map.get(proj.player_id)
        base_conf = proj.consistency / 100.0
        props = {}

        for engine_stat, short_name in STAT_MAP.items():
            season_val = getattr(proj, engine_stat, 0.0)
            std_dev = _get_std_dev(ctx, engine_stat)
            confidence = _get_confidence(season_val, std_dev, base_conf)

            # Map short names to betting engine prop names
            prop_name = {
                "pts": "points", "reb": "rebounds", "ast": "assists",
                "fg3m": "threes", "stl": "steals", "blk": "blocks",
            }[short_name]

            prop_entry = {
                "std_dev": round(std_dev, 2),
                "confidence": confidence,
            }

            if gd is not None:
                # Use game-day adjusted value as the projection
                gd_attr = _GD_STAT_ATTR.get(engine_stat, engine_stat)
                adjusted_val = getattr(gd, gd_attr, season_val)
                prop_entry["projection"] = round(adjusted_val, 1)
                prop_entry["season_projection"] = round(season_val, 1)
            else:
                prop_entry["projection"] = round(season_val, 1)

            props[prop_name] = prop_entry

        entry = {
            "name": ctx.player_name,
            "team": ctx.team,
            "position": ctx.raw_position,
            "is_b2b": ctx.is_b2b,
            "is_death_spot": ctx.is_death_spot,
            "death_spot_type": ctx.death_spot_type,
            "props": props,
        }

        if gd is not None:
            entry["game_day_adjusted"] = True
            entry["adjustments"] = {
                "schedule_multiplier": round(gd.schedule_multiplier, 4),
                "city_multiplier": round(gd.city_multiplier, 4),
                "death_spot_multiplier": round(gd.death_spot_multiplier, 4),
                "matchup_multiplier": round(gd.matchup_multiplier, 4),
                "compound_multiplier": round(gd.compound_multiplier, 4),
            }

        result[ctx.player_id] = entry

    file_path = out_path / "betting_contract.json"
    with open(file_path, "w") as f:
        json.dump(result, f, indent=2)

    return str(file_path)
