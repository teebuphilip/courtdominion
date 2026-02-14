"""
Season-long projection pipeline.

Takes a PlayerContext with baseline stats, applies age-profile adjustments,
usage normalization, durability projections, ceiling/floor, and consistency.

Adjustment chain:
    baseline → age_adjustment → usage_normalization → projected_per_game
    projected_per_game × projected_games → season_totals
"""

import math
from dataclasses import dataclass
from typing import Dict, Optional

from engine.baseline import PlayerContext
from engine import lookup

# Hard bounds for any compound multiplier
COMPOUND_MIN = 0.50
COMPOUND_MAX = 1.50

# Age adjustment blend: 70% player baseline, 30% age profile
PLAYER_WEIGHT = 0.70
PROFILE_WEIGHT = 0.30

# Durability blend: 60% recent history, 40% profile
RECENT_GAMES_WEIGHT = 0.60
PROFILE_GAMES_WEIGHT = 0.40

# Default projected games when no durability data
DEFAULT_GAMES = 65

# Stats that receive age adjustment (counting stats only)
AGE_ADJUSTED_STATS = [
    "minutes_played", "points", "rebounds", "assists", "steals",
    "blocks", "turnovers", "fgm", "fga", "three_pm", "three_pa",
    "ftm", "fta",
]


@dataclass
class SeasonProjection:
    """Output of the season-long projection pipeline for one player."""
    player_id: str = ""
    player_name: str = ""
    team: str = ""
    position: str = ""

    # Per-game projected stats
    minutes: float = 0.0
    usage_rate: float = 0.0
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

    # Derived percentages
    fg_pct: float = 0.0
    three_pt_pct: float = 0.0
    ft_pct: float = 0.0

    # Aggregates
    fantasy_points: float = 0.0
    projected_games: int = 0

    # Ceiling / floor / consistency
    ceiling: float = 0.0
    floor: float = 0.0
    consistency: int = 0


def project_season(ctx: PlayerContext) -> SeasonProjection:
    """
    Full season-long projection for one player.

    Steps:
    1. Start with baseline_stats
    2. Apply age adjustment (70/30 blend with profile)
    3. Normalize via usage profile (clamp minutes to reasonable range)
    4. Project games played via durability
    5. Compute ceiling and floor
    6. Derive consistency from stat variance
    7. Calculate fantasy points and percentages
    """
    stats = dict(ctx.baseline_stats)

    # 1. Age adjustment
    stats = _apply_age_adjustment(stats, ctx.age, ctx.position, ctx.role)

    # 2. Usage normalization
    stats = _apply_usage_normalization(stats, ctx.age, ctx.position, ctx.role)

    # 3. Projected games
    projected_games = _project_games_played(
        ctx.age, ctx.position, ctx.role, ctx.games_by_season
    )

    # 4. Fantasy points
    fp = _calculate_fantasy_points(stats)

    # 5. Ceiling and floor
    ceiling, floor = _compute_ceiling_floor(
        stats, fp, ctx.age, ctx.position, ctx.role, ctx.stat_variance
    )

    # 6. Consistency
    consistency = _compute_consistency(
        ctx.stat_variance, ctx.age, ctx.position, ctx.role, fp
    )

    # 7. Percentages
    fg_pct, three_pt_pct, ft_pct = _calculate_percentages(stats)

    # 8. Usage rate from profile
    usage_rate = _get_usage_rate(ctx.age, ctx.position, ctx.role)

    return SeasonProjection(
        player_id=ctx.player_id,
        player_name=ctx.player_name,
        team=ctx.team,
        position=ctx.position,
        minutes=max(0.0, stats.get("minutes_played", 0.0)),
        usage_rate=usage_rate,
        points=max(0.0, stats.get("points", 0.0)),
        rebounds=max(0.0, stats.get("rebounds", 0.0)),
        assists=max(0.0, stats.get("assists", 0.0)),
        steals=max(0.0, stats.get("steals", 0.0)),
        blocks=max(0.0, stats.get("blocks", 0.0)),
        turnovers=max(0.0, stats.get("turnovers", 0.0)),
        fgm=max(0.0, stats.get("fgm", 0.0)),
        fga=max(0.0, stats.get("fga", 0.0)),
        three_pm=max(0.0, stats.get("three_pm", 0.0)),
        three_pa=max(0.0, stats.get("three_pa", 0.0)),
        ftm=max(0.0, stats.get("ftm", 0.0)),
        fta=max(0.0, stats.get("fta", 0.0)),
        fg_pct=fg_pct,
        three_pt_pct=three_pt_pct,
        ft_pct=ft_pct,
        fantasy_points=max(0.0, fp),
        projected_games=projected_games,
        ceiling=max(0.0, ceiling),
        floor=max(0.0, floor),
        consistency=consistency,
    )


def _apply_age_adjustment(
    baseline: Dict[str, float],
    age: int,
    pos: str,
    role: str,
) -> Dict[str, float]:
    """
    Blend player baseline with age profile average.
    70% player baseline + 30% age profile.
    """
    profile = lookup.lookup_age_profile(age, pos, role)
    if profile is None:
        return baseline

    result = dict(baseline)
    for stat in AGE_ADJUSTED_STATS:
        player_val = baseline.get(stat, 0.0)
        profile_key = f"avg_{stat}"
        profile_val = profile.get(profile_key, player_val)

        blended = PLAYER_WEIGHT * player_val + PROFILE_WEIGHT * profile_val
        result[stat] = blended

    return result


def _apply_usage_normalization(
    stats: Dict[str, float],
    age: int,
    pos: str,
    role: str,
) -> Dict[str, float]:
    """
    Sanity-check minutes against usage profile percentiles.
    If outside [10th, 90th], nudge toward median.
    """
    usage = lookup.lookup_usage(age, pos, role)
    if usage is None:
        return stats

    result = dict(stats)
    minutes = result.get("minutes_played", 0.0)
    p10 = usage.get("minutes_10th", 0.0)
    p50 = usage.get("minutes_50th", minutes)
    p90 = usage.get("minutes_90th", 48.0)

    if minutes > p90:
        # Nudge down: midpoint between current and 90th
        result["minutes_played"] = (minutes + p90) / 2.0
    elif minutes < p10:
        # Nudge up: midpoint between current and 10th
        result["minutes_played"] = (minutes + p10) / 2.0

    return result


def _project_games_played(
    age: int,
    pos: str,
    role: str,
    games_by_season: Dict[int, int],
) -> int:
    """
    Blend recent history with durability profile.
    60% recent avg + 40% profile avg. Clamped [0, 82].
    """
    # Recent average from actual game counts
    if games_by_season:
        recent_avg = sum(games_by_season.values()) / len(games_by_season)
    else:
        recent_avg = DEFAULT_GAMES

    # Profile average
    durability = lookup.lookup_durability(age, pos, role)
    if durability is not None:
        profile_avg = durability.get("avg_games_played", DEFAULT_GAMES)
    else:
        profile_avg = DEFAULT_GAMES

    blended = RECENT_GAMES_WEIGHT * recent_avg + PROFILE_GAMES_WEIGHT * profile_avg
    return max(0, min(82, round(blended)))


def _compute_ceiling_floor(
    stats: Dict[str, float],
    fantasy_points: float,
    age: int,
    pos: str,
    role: str,
    stat_variance: Dict[str, float],
) -> tuple:
    """
    Ceiling from ceiling profiles, floor from variance.
    """
    ceiling_profile = lookup.lookup_ceiling_profile(age, pos, role)

    if ceiling_profile is not None:
        ceiling = ceiling_profile.get("avg_ceiling_game_pts", fantasy_points * 1.3)
    else:
        ceiling = fantasy_points * 1.3

    # Floor: baseline fantasy_points - 1.5 * stddev
    fp_var = stat_variance.get("fantasy_points_variance", 0.0)
    fp_stddev = math.sqrt(fp_var) if fp_var > 0 else fantasy_points * 0.3
    floor = fantasy_points - 1.5 * fp_stddev

    # Ensure ceiling > floor
    if ceiling <= floor:
        ceiling = floor + 5.0

    return ceiling, max(0.0, floor)


def _compute_consistency(
    stat_variance: Dict[str, float],
    age: int,
    pos: str,
    role: str,
    fantasy_points: float,
) -> int:
    """
    Consistency score 0-100.
    Lower variance relative to profile = higher consistency.
    """
    fp_var = stat_variance.get("fantasy_points_variance", 0.0)
    if fantasy_points <= 0:
        return 50

    # Player's coefficient of variation
    player_cv = math.sqrt(fp_var) / fantasy_points if fp_var > 0 else 0.3

    # Profile's CV for comparison
    profile = lookup.lookup_age_profile(age, pos, role)
    if profile is not None:
        profile_avg = profile.get("avg_points", 10.0)
        profile_var = profile.get("variance_points", 25.0)
        profile_cv = math.sqrt(profile_var) / profile_avg if profile_avg > 0 else 0.5
    else:
        profile_cv = 0.5

    # Ratio: lower player_cv relative to profile = higher consistency
    if profile_cv > 0:
        ratio = player_cv / profile_cv
    else:
        ratio = 1.0

    # Convert to 0-100 scale: ratio of 1.0 = 50, lower = higher score
    # score = 100 - (ratio * 50), clamped
    score = int(100 - ratio * 50)
    return max(0, min(100, score))


def _calculate_percentages(stats: Dict[str, float]) -> tuple:
    """Derive fg_pct, three_pt_pct, ft_pct from made/attempted."""
    fga = stats.get("fga", 0.0)
    fg_pct = stats.get("fgm", 0.0) / fga if fga > 0 else 0.0

    three_pa = stats.get("three_pa", 0.0)
    three_pt_pct = stats.get("three_pm", 0.0) / three_pa if three_pa > 0 else 0.0

    fta = stats.get("fta", 0.0)
    ft_pct = stats.get("ftm", 0.0) / fta if fta > 0 else 0.0

    return fg_pct, three_pt_pct, ft_pct


def _calculate_fantasy_points(stats: Dict[str, float]) -> float:
    """PTS*1 + REB*1.2 + AST*1.5 + STL*3 + BLK*3 + TOV*-1"""
    return (
        stats.get("points", 0.0) * 1.0
        + stats.get("rebounds", 0.0) * 1.2
        + stats.get("assists", 0.0) * 1.5
        + stats.get("steals", 0.0) * 3.0
        + stats.get("blocks", 0.0) * 3.0
        + stats.get("turnovers", 0.0) * -1.0
    )


def _get_usage_rate(age: int, pos: str, role: str) -> float:
    """Get usage rate from profile."""
    usage = lookup.lookup_usage(age, pos, role)
    if usage is not None:
        return usage.get("avg_usage_rate", 0.0)
    return 0.0


def _clamp_adjustment(value: float) -> float:
    """Clamp compound multiplier to [COMPOUND_MIN, COMPOUND_MAX]."""
    return max(COMPOUND_MIN, min(COMPOUND_MAX, value))
