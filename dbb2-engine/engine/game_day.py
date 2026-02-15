"""
Game-day adjustments for DFS projections.

Applies schedule effects, city effects, and matchup adjustments
on top of a season-long projection. All three are multiplicative
and compound-clamped to [0.50, 1.50].
"""

from dataclasses import dataclass
from typing import Dict

from engine.baseline import PlayerContext
from engine.projections import SeasonProjection, _calculate_fantasy_points
from engine import lookup

COMPOUND_MIN = 0.50
COMPOUND_MAX = 1.50

# Stats that get matchup-specific multipliers
MATCHUP_STAT_MAP = {
    "points": "points_multiplier",
    "rebounds": "rebounds_multiplier",
    "assists": "assists_multiplier",
    "steals": "steals_multiplier",
    "blocks": "blocks_multiplier",
    "three_pm": "three_pm_multiplier",
}

# Stats that get overall scoring multiplier (schedule/city)
SCORING_STATS = [
    "points", "rebounds", "assists", "steals", "blocks",
    "turnovers", "fgm", "fga", "three_pm", "three_pa",
    "ftm", "fta",
]


@dataclass
class GameDayProjection:
    """A single-game projection with DFS context applied."""
    player_id: str = ""
    player_name: str = ""
    team: str = ""
    position: str = ""
    opponent: str = ""
    location: str = ""

    # Per-game projected stats (adjusted for game context)
    minutes: float = 0.0
    points: float = 0.0
    rebounds: float = 0.0
    assists: float = 0.0
    steals: float = 0.0
    blocks: float = 0.0
    turnovers: float = 0.0
    fgm: float = 0.0
    fga: float = 0.0
    three_pm: float = 0.0
    three_pa: float = 0.0
    ftm: float = 0.0
    fta: float = 0.0

    fantasy_points: float = 0.0
    ceiling: float = 0.0
    floor: float = 0.0

    # Adjustment breakdown (for transparency)
    schedule_multiplier: float = 1.0
    city_multiplier: float = 1.0
    death_spot_multiplier: float = 1.0
    matchup_multiplier: float = 1.0
    compound_multiplier: float = 1.0


def project_game_day(
    ctx: PlayerContext,
    season_proj: SeasonProjection,
) -> GameDayProjection:
    """
    Apply game-day adjustments to a season projection.

    Steps:
    1. Get schedule multiplier (B2B or rest)
    2. Get city multiplier (hot spot or altitude)
    3. Get matchup multipliers (per-stat)
    4. Compound clamp all adjustments
    5. Apply to per-game stats
    6. Recalculate fantasy points
    """
    sched_mult = _get_schedule_multiplier(ctx)
    city_mult = _get_city_multiplier(ctx)
    death_spot_mult = _get_death_spot_multiplier(ctx)
    matchup_data = _get_matchup_multipliers(ctx)

    # Overall fantasy_pts_multiplier from matchup data
    matchup_overall = matchup_data.get("fantasy_pts_multiplier", 1.0)

    # Compound clamp for the overall multiplier
    compound = max(COMPOUND_MIN, min(COMPOUND_MAX, sched_mult * city_mult * death_spot_mult * matchup_overall))

    # Build adjusted stats
    stats = {
        "minutes_played": season_proj.minutes * max(COMPOUND_MIN, min(COMPOUND_MAX, sched_mult * city_mult * death_spot_mult)),
        "points": season_proj.points,
        "rebounds": season_proj.rebounds,
        "assists": season_proj.assists,
        "steals": season_proj.steals,
        "blocks": season_proj.blocks,
        "turnovers": season_proj.turnovers,
        "fgm": season_proj.fgm,
        "fga": season_proj.fga,
        "three_pm": season_proj.three_pm,
        "three_pa": season_proj.three_pa,
        "ftm": season_proj.ftm,
        "fta": season_proj.fta,
    }

    # Apply per-stat matchup multipliers where available
    for stat, mult_key in MATCHUP_STAT_MAP.items():
        stat_mult = matchup_data.get(mult_key, 1.0)
        # Combine with schedule + city + death spot for a per-stat compound
        per_stat_compound = max(COMPOUND_MIN, min(COMPOUND_MAX, sched_mult * city_mult * death_spot_mult * stat_mult))
        stats[stat] = stats[stat] * per_stat_compound

    # Apply schedule+city to non-matchup scoring stats
    for stat in ("turnovers", "fgm", "fga", "three_pa", "ftm", "fta"):
        if stat not in MATCHUP_STAT_MAP:
            sc_compound = max(COMPOUND_MIN, min(COMPOUND_MAX, sched_mult * city_mult * death_spot_mult))
            stats[stat] = stats[stat] * sc_compound

    # Recalculate fantasy points from adjusted stats
    fp = _calculate_fantasy_points(stats)

    # Adjusted ceiling/floor
    ceiling = season_proj.ceiling * compound
    floor = season_proj.floor * compound

    return GameDayProjection(
        player_id=ctx.player_id,
        player_name=ctx.player_name,
        team=ctx.team,
        position=ctx.position,
        opponent=ctx.opponent_team,
        location=ctx.location,
        minutes=max(0.0, stats["minutes_played"]),
        points=max(0.0, stats["points"]),
        rebounds=max(0.0, stats["rebounds"]),
        assists=max(0.0, stats["assists"]),
        steals=max(0.0, stats["steals"]),
        blocks=max(0.0, stats["blocks"]),
        turnovers=max(0.0, stats["turnovers"]),
        fgm=max(0.0, stats["fgm"]),
        fga=max(0.0, stats["fga"]),
        three_pm=max(0.0, stats["three_pm"]),
        three_pa=max(0.0, stats["three_pa"]),
        ftm=max(0.0, stats["ftm"]),
        fta=max(0.0, stats["fta"]),
        fantasy_points=max(0.0, fp),
        ceiling=max(0.0, ceiling),
        floor=max(0.0, floor),
        schedule_multiplier=sched_mult,
        city_multiplier=city_mult,
        death_spot_multiplier=death_spot_mult,
        matchup_multiplier=matchup_overall,
        compound_multiplier=compound,
    )


def _get_schedule_multiplier(ctx: PlayerContext) -> float:
    """
    B2B → scoring dropoff. Rest ≥ 3 days → scoring boost. Otherwise 1.0.
    """
    if not ctx.is_b2b and ctx.rest_days < 3:
        return 1.0

    effect = lookup.lookup_schedule_effect(ctx.age_bracket, ctx.position, ctx.role)
    if effect is None:
        return 1.0

    if ctx.is_b2b:
        return effect.get("b2b_scoring_dropoff", 1.0)
    elif ctx.rest_days >= 3:
        return effect.get("rest_scoring_boost", 1.0)

    return 1.0


def _get_city_multiplier(ctx: PlayerContext) -> float:
    """
    Post-hot-spot → scoring dropoff. Post-altitude → altitude dropoff.
    """
    if not ctx.is_post_hot_spot and not ctx.is_post_altitude:
        return 1.0

    effect = lookup.lookup_city_effect(ctx.age_bracket, ctx.position, ctx.role)
    if effect is None:
        return 1.0

    if ctx.is_post_hot_spot:
        return effect.get("hot_spot_scoring_dropoff", 1.0)
    elif ctx.is_post_altitude:
        # Use b2b altitude dropoff if also b2b, else 1-day
        if ctx.is_b2b:
            val = effect.get("altitude_b2b_dropoff")
            if val is not None:
                return val
        val = effect.get("altitude_1day_dropoff")
        if val is not None:
            return val
        return 1.0

    return 1.0


_DEATH_SPOT_TYPE_TO_FIELD = {
    "party_b2b": "party_b2b_residual",
    "altitude_b2b": "altitude_b2b_residual",
    "cross_country_b2b": "cross_country_b2b_dropoff",
    "party_to_altitude": "party_to_altitude_dropoff",
    "compound": "compound_worst_dropoff",
}


def _get_death_spot_multiplier(ctx: PlayerContext) -> float:
    """
    Death spot compound residual effect.

    Returns the RESIDUAL penalty beyond what schedule + city effects
    already capture, or the FULL penalty for unique patterns (cross-country,
    party-to-altitude) that no existing feature covers.
    """
    if not ctx.is_death_spot:
        return 1.0

    effect = lookup.lookup_death_spot_effect(ctx.age_bracket, ctx.position, ctx.role)
    if effect is None:
        return 1.0

    field = _DEATH_SPOT_TYPE_TO_FIELD.get(ctx.death_spot_type)
    if field is None:
        return 1.0

    val = effect.get(field)
    return val if val is not None else 1.0


def _get_matchup_multipliers(ctx: PlayerContext) -> Dict[str, float]:
    """
    Look up per-stat matchup multipliers.
    Falls back to neutral 1.0 for all stats.
    """
    result = lookup.lookup_matchup(
        ctx.age_bracket,
        ctx.position,
        ctx.role,
        ctx.opponent_defense_tier,
        ctx.location,
    )
    if result is not None:
        return result
    return lookup.NEUTRAL_MATCHUP
