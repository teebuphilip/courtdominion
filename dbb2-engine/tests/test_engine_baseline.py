"""
Tests for engine/baseline.py — player context builder.
"""

import pytest
import pandas as pd

from data_collection.utils import STAT_COLUMNS
from engine.baseline import (
    PlayerContext,
    _compute_weighted_baseline,
    _compute_stat_variance,
    SEASON_WEIGHTS_3,
    SEASON_WEIGHTS_2,
    MIN_GAMES_PER_SEASON,
)


# --------------------------------------------------------------------------
# Helper: build a small fake DataFrame for testing
# --------------------------------------------------------------------------

def _make_player_df(seasons_data):
    """
    Build a fake player DataFrame.
    seasons_data: list of (season_year, num_games, avg_points, avg_minutes)
    """
    rows = []
    for year, n_games, avg_pts, avg_min in seasons_data:
        for i in range(n_games):
            rows.append({
                "player_id": "TEST001",
                "player_name": "Test Player",
                "team": "TST",
                "position": "G",
                "position_group": "G",
                "home_or_road": "HOME",
                "age": 25,
                "game_date": pd.Timestamp(f"{year}-11-{(i % 28) + 1:02d}"),
                "season_start_year": year,
                "minutes_played": avg_min + (i % 5 - 2),  # some variance
                "points": avg_pts + (i % 7 - 3),
                "rebounds": 5.0,
                "assists": 6.0,
                "steals": 1.5,
                "blocks": 0.5,
                "turnovers": 2.0,
                "fgm": 8.0,
                "fga": 16.0,
                "three_pm": 2.0,
                "three_pa": 5.0,
                "ftm": 3.0,
                "fta": 4.0,
                "fantasy_points": avg_pts + 5 * 1.2 + 6 * 1.5 + 1.5 * 3 + 0.5 * 3 - 2,
            })
    return pd.DataFrame(rows)


class TestWeightedAverage:
    """Verify weighted average math."""

    def test_three_seasons_weighted(self):
        """50/30/20 weighting for 3 seasons."""
        df = _make_player_df([
            (2024, 60, 20.0, 30.0),
            (2023, 60, 18.0, 28.0),
            (2022, 60, 16.0, 26.0),
        ])
        result = _compute_weighted_baseline(df, 2024)

        # Expected points: 20*0.5 + 18*0.3 + 16*0.2 = 10 + 5.4 + 3.2 = 18.6
        # Note: actual values have variance from i%7-3, so check approximate
        assert abs(result["points"] - 18.6) < 1.5

    def test_two_seasons_weighted(self):
        """60/40 weighting for 2 seasons."""
        df = _make_player_df([
            (2024, 60, 20.0, 30.0),
            (2023, 60, 10.0, 28.0),
        ])
        result = _compute_weighted_baseline(df, 2024)

        # Expected points: 20*0.6 + 10*0.4 = 12 + 4 = 16.0
        assert abs(result["points"] - 16.0) < 1.5

    def test_one_season_passthrough(self):
        """Single season = raw average."""
        df = _make_player_df([
            (2024, 60, 20.0, 30.0),
        ])
        result = _compute_weighted_baseline(df, 2024)
        assert abs(result["points"] - 20.0) < 1.5

    def test_all_stat_columns_present(self):
        """Output should have all STAT_COLUMNS + fantasy_points."""
        df = _make_player_df([(2024, 60, 20.0, 30.0)])
        result = _compute_weighted_baseline(df, 2024)
        for stat in STAT_COLUMNS:
            assert stat in result, f"Missing {stat}"
        assert "fantasy_points" in result

    def test_skips_low_game_seasons(self):
        """Seasons with fewer than MIN_GAMES_PER_SEASON are excluded."""
        df = _make_player_df([
            (2024, 60, 20.0, 30.0),
            (2023, 5, 30.0, 35.0),  # Too few games
        ])
        result = _compute_weighted_baseline(df, 2024)
        # Should only use 2024 (1-season weight = 1.0)
        assert abs(result["points"] - 20.0) < 1.5


class TestStatVariance:
    """Verify stat variance computation."""

    def test_variance_positive(self):
        """Variance should be > 0 for varied data."""
        df = _make_player_df([(2024, 60, 20.0, 30.0)])
        result = _compute_stat_variance(df)
        assert result["points_variance"] > 0

    def test_all_variance_keys(self):
        """Should have variance for all stats + fantasy_points."""
        df = _make_player_df([(2024, 60, 20.0, 30.0)])
        result = _compute_stat_variance(df)
        for stat in STAT_COLUMNS:
            assert f"{stat}_variance" in result
        assert "fantasy_points_variance" in result


class TestPlayerContext:
    """Verify PlayerContext structure."""

    def test_status_property(self):
        ctx = PlayerContext(
            player_id="1", player_name="Test", team="TST",
            position="G", raw_position="G", age=25,
            role="Starter", age_bracket="Young",
        )
        assert ctx.status == "active"

    def test_default_game_day_fields(self):
        ctx = PlayerContext(
            player_id="1", player_name="Test", team="TST",
            position="G", raw_position="G", age=25,
            role="Starter", age_bracket="Young",
        )
        assert ctx.is_b2b is False
        assert ctx.rest_days == 1
        assert ctx.location == "HOME"
