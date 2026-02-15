"""
Compute player baselines from raw CSV game logs.

Builds PlayerContext objects for all players found in the most recent
N seasons. Each context contains a weighted average of per-game stats
across available seasons, plus metadata (age, position, role).

Season weights: most_recent=0.50, prior=0.30, two_prior=0.20
(normalized if fewer seasons available)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from data_collection.utils import (
    STAT_COLUMNS,
    load_seasons_range,
    rebucket_role,
    age_bucket,
    normalize_position,
    calculate_fantasy_points,
)


# Weights for up to 3 seasons (most recent first)
SEASON_WEIGHTS_3 = [0.50, 0.30, 0.20]
SEASON_WEIGHTS_2 = [0.60, 0.40]
SEASON_WEIGHTS_1 = [1.00]

# Minimum games in a season to count it
MIN_GAMES_PER_SEASON = 10


@dataclass
class PlayerContext:
    """All inputs needed to project a single player."""
    player_id: str
    player_name: str
    team: str
    position: str          # Normalized: G, F, or C
    raw_position: str      # Original CSV position (G, F, C, G-F, etc.)
    age: int
    role: str              # Starter, Rotation, Bench, Scrub
    age_bracket: str       # Young, Prime, Veteran

    # Baseline per-game stats (weighted multi-season avg)
    baseline_stats: Dict[str, float] = field(default_factory=dict)

    # Per-season game counts (for durability)
    games_by_season: Dict[int, int] = field(default_factory=dict)

    # Per-game stat variance from most recent season
    stat_variance: Dict[str, float] = field(default_factory=dict)

    # Game-day context (optional, for DFS — populated externally)
    is_b2b: bool = False
    rest_days: int = 1
    opponent_team: str = ""
    opponent_defense_tier: str = "Average"
    location: str = "HOME"
    is_post_hot_spot: bool = False
    is_post_altitude: bool = False
    is_death_spot: bool = False
    death_spot_type: str = ""

    @property
    def status(self) -> str:
        return "active"


def build_player_contexts_from_csv(
    seasons_to_load: int = 3,
) -> List[PlayerContext]:
    """
    Build PlayerContext objects for all players in the most recent N seasons.

    Steps:
    1. Determine the most recent season year from available CSVs
    2. Load that range of seasons
    3. Group by player_id
    4. For each player: compute weighted baseline, determine metadata
    5. Return sorted by player_name
    """
    # Determine year range: most recent data is 2024-25 (start year 2024)
    # Load the most recent `seasons_to_load` seasons
    end_year = 2024
    start_year = end_year - seasons_to_load + 1

    df = load_seasons_range(start_year, end_year)

    # Standard cleanup
    df = df.dropna(subset=["position_group"])
    df = df[df["minutes_played"] > 0]

    # Add fantasy points
    df["fantasy_points"] = df.apply(calculate_fantasy_points, axis=1)

    contexts = []
    for player_id, player_df in df.groupby("player_id"):
        ctx = _build_single_context(player_id, player_df, end_year)
        if ctx is not None:
            contexts.append(ctx)

    contexts.sort(key=lambda c: c.player_name)
    return contexts


def _build_single_context(
    player_id: str,
    player_df: pd.DataFrame,
    most_recent_year: int,
) -> Optional[PlayerContext]:
    """Build a PlayerContext for one player from their game logs."""
    # Must have at least MIN_GAMES_PER_SEASON in the most recent season
    recent = player_df[player_df["season_start_year"] == most_recent_year]
    if len(recent) < MIN_GAMES_PER_SEASON:
        return None

    # Extract metadata from most recent game
    latest_game = recent.sort_values("game_date").iloc[-1]
    player_name = str(latest_game.get("player_name", "Unknown"))
    team = str(latest_game.get("team", "UNK"))
    raw_position = str(latest_game.get("position", "Unknown"))
    position = normalize_position(raw_position)
    if position is None:
        return None

    age_val = latest_game.get("age")
    if pd.isna(age_val):
        return None
    age = int(age_val)

    # Determine role from most recent season average minutes
    season_avg_min = recent["minutes_played"].mean()
    role = rebucket_role(season_avg_min)

    bracket = age_bucket(age)
    if bracket is None:
        return None

    # Games played per season
    games_by_season = {}
    for season_year, season_df in player_df.groupby("season_start_year"):
        games_by_season[int(season_year)] = len(season_df)

    # Compute weighted baseline
    baseline_stats = _compute_weighted_baseline(player_df, most_recent_year)

    # Compute stat variance from most recent season
    stat_variance = _compute_stat_variance(recent)

    return PlayerContext(
        player_id=str(player_id),
        player_name=player_name,
        team=team,
        position=position,
        raw_position=raw_position,
        age=age,
        role=role,
        age_bracket=bracket,
        baseline_stats=baseline_stats,
        games_by_season=games_by_season,
        stat_variance=stat_variance,
    )


def _compute_weighted_baseline(
    player_df: pd.DataFrame,
    most_recent_year: int,
) -> Dict[str, float]:
    """
    Compute weighted per-game averages across up to 3 seasons.

    Most recent season gets highest weight. Seasons with fewer than
    MIN_GAMES_PER_SEASON are excluded.
    """
    all_stats = list(STAT_COLUMNS) + ["fantasy_points"]

    # Get per-season averages, ordered most recent first
    season_avgs = []
    for year in range(most_recent_year, most_recent_year - 3, -1):
        season_df = player_df[player_df["season_start_year"] == year]
        if len(season_df) >= MIN_GAMES_PER_SEASON:
            avgs = {}
            for stat in all_stats:
                avgs[stat] = season_df[stat].mean()
            season_avgs.append(avgs)

    if not season_avgs:
        # Shouldn't happen if caller filters, but fallback to overall avg
        result = {}
        for stat in all_stats:
            result[stat] = player_df[stat].mean()
        return result

    # Select weights based on number of available seasons
    n = len(season_avgs)
    if n >= 3:
        weights = SEASON_WEIGHTS_3
    elif n == 2:
        weights = SEASON_WEIGHTS_2
    else:
        weights = SEASON_WEIGHTS_1

    # Weighted average
    result = {}
    for stat in all_stats:
        weighted_sum = 0.0
        for i, avg_dict in enumerate(season_avgs):
            weighted_sum += avg_dict[stat] * weights[i]
        result[stat] = weighted_sum

    return result


def _compute_stat_variance(season_df: pd.DataFrame) -> Dict[str, float]:
    """Compute variance for each stat from one season's game logs."""
    all_stats = list(STAT_COLUMNS) + ["fantasy_points"]
    variance = {}
    for stat in all_stats:
        vals = season_df[stat].dropna()
        if len(vals) > 1:
            variance[f"{stat}_variance"] = float(vals.var(ddof=1))
        else:
            variance[f"{stat}_variance"] = 0.0
    return variance
