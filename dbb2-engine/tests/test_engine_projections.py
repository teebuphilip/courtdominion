"""
Tests for engine/projections.py — season-long projection pipeline.
"""

import pytest

from engine.projections import (
    project_season,
    _apply_age_adjustment,
    _calculate_fantasy_points,
    _calculate_percentages,
    _project_games_played,
    _compute_ceiling_floor,
    _compute_consistency,
    _clamp_adjustment,
    PLAYER_WEIGHT,
    PROFILE_WEIGHT,
    COMPOUND_MIN,
    COMPOUND_MAX,
)
from engine.baseline import PlayerContext


def _make_context(**overrides):
    """Build a test PlayerContext with sensible defaults."""
    defaults = dict(
        player_id="TEST001",
        player_name="Test Player",
        team="TST",
        position="G",
        raw_position="G",
        age=25,
        role="Starter",
        age_bracket="Young",
        baseline_stats={
            "minutes_played": 32.0,
            "points": 20.0,
            "rebounds": 5.0,
            "assists": 6.0,
            "steals": 1.5,
            "blocks": 0.5,
            "turnovers": 2.5,
            "fgm": 7.5,
            "fga": 16.0,
            "three_pm": 2.0,
            "three_pa": 5.5,
            "ftm": 3.0,
            "fta": 3.5,
            "fantasy_points": 35.0,
        },
        games_by_season={2024: 72, 2023: 68},
        stat_variance={
            "points_variance": 40.0,
            "rebounds_variance": 8.0,
            "assists_variance": 6.0,
            "steals_variance": 1.5,
            "blocks_variance": 0.5,
            "turnovers_variance": 2.0,
            "minutes_played_variance": 25.0,
            "fgm_variance": 8.0,
            "fga_variance": 15.0,
            "three_pm_variance": 2.5,
            "three_pa_variance": 4.0,
            "ftm_variance": 3.0,
            "fta_variance": 4.0,
            "fantasy_points_variance": 100.0,
        },
    )
    defaults.update(overrides)
    return PlayerContext(**defaults)


class TestAgeAdjustment:
    """Age adjustment should blend player baseline with profile."""

    def test_adjustment_is_conservative(self):
        """Result should be between baseline and profile."""
        baseline = {"points": 30.0, "rebounds": 5.0}
        result = _apply_age_adjustment(baseline, 25, "G", "Starter")
        # With profile avg (likely ~18-22 for a 25yo G Starter),
        # result should be pulled toward profile but still closer to 30
        assert result["points"] < 30.0  # Regressed toward mean
        assert result["points"] > 15.0  # But not too far

    def test_missing_profile_returns_baseline(self):
        """If no profile found, return baseline unchanged."""
        baseline = {"points": 20.0}
        result = _apply_age_adjustment(baseline, 99, "X", "Unknown")
        assert result["points"] == 20.0


class TestDurabilityProjection:
    """Games played projection."""

    def test_blend_recent_and_profile(self):
        """60% recent + 40% profile."""
        games = {2024: 72, 2023: 68}
        result = _project_games_played(25, "G", "Starter", games)
        # Recent avg = 70, profile likely ~70-75 for young starter
        assert 60 <= result <= 82

    def test_clamped_to_82(self):
        """Never exceeds 82."""
        games = {2024: 82, 2023: 82, 2022: 82}
        result = _project_games_played(25, "G", "Starter", games)
        assert result <= 82

    def test_no_games_uses_default(self):
        """Empty games dict uses default 65."""
        result = _project_games_played(25, "G", "Starter", {})
        assert 50 <= result <= 75


class TestCeilingFloor:
    """Ceiling and floor computation."""

    def test_ceiling_greater_than_floor(self):
        stats = {"points": 20.0}
        variance = {"fantasy_points_variance": 100.0}
        ceiling, floor = _compute_ceiling_floor(
            stats, 35.0, 25, "G", "Starter", variance
        )
        assert ceiling > floor

    def test_floor_non_negative(self):
        stats = {"points": 5.0}
        variance = {"fantasy_points_variance": 400.0}  # High variance
        _, floor = _compute_ceiling_floor(
            stats, 5.0, 25, "G", "Bench", variance
        )
        assert floor >= 0.0


class TestConsistency:
    """Consistency score derivation."""

    def test_score_clamped_0_100(self):
        variance = {"fantasy_points_variance": 100.0}
        score = _compute_consistency(variance, 25, "G", "Starter", 35.0)
        assert 0 <= score <= 100

    def test_zero_fantasy_points_returns_50(self):
        variance = {"fantasy_points_variance": 0.0}
        score = _compute_consistency(variance, 25, "G", "Starter", 0.0)
        assert score == 50


class TestFantasyPoints:
    """Fantasy points calculation."""

    def test_known_calculation(self):
        """20pts + 10reb + 5ast + 1stl + 1blk + 2tov = 20 + 12 + 7.5 + 3 + 3 - 2 = 43.5"""
        stats = {
            "points": 20.0,
            "rebounds": 10.0,
            "assists": 5.0,
            "steals": 1.0,
            "blocks": 1.0,
            "turnovers": 2.0,
        }
        result = _calculate_fantasy_points(stats)
        assert abs(result - 43.5) < 0.01

    def test_zero_stats(self):
        stats = {}
        result = _calculate_fantasy_points(stats)
        assert result == 0.0


class TestPercentages:
    """Shooting percentage derivation."""

    def test_normal_percentages(self):
        stats = {"fgm": 8.0, "fga": 16.0, "three_pm": 2.0,
                 "three_pa": 5.0, "ftm": 4.0, "fta": 5.0}
        fg, three, ft = _calculate_percentages(stats)
        assert abs(fg - 0.5) < 0.01
        assert abs(three - 0.4) < 0.01
        assert abs(ft - 0.8) < 0.01

    def test_zero_attempts(self):
        stats = {"fgm": 0.0, "fga": 0.0, "three_pm": 0.0,
                 "three_pa": 0.0, "ftm": 0.0, "fta": 0.0}
        fg, three, ft = _calculate_percentages(stats)
        assert fg == 0.0
        assert three == 0.0
        assert ft == 0.0


class TestCompoundBounds:
    """Compound adjustment clamping."""

    def test_clamped_at_max(self):
        assert _clamp_adjustment(2.0) == COMPOUND_MAX

    def test_clamped_at_min(self):
        assert _clamp_adjustment(0.1) == COMPOUND_MIN

    def test_normal_passthrough(self):
        assert _clamp_adjustment(1.0) == 1.0


class TestFullProjection:
    """End-to-end season projection."""

    def test_produces_valid_output(self):
        ctx = _make_context()
        proj = project_season(ctx)
        assert proj.player_id == "TEST001"
        assert proj.points > 0
        assert proj.fantasy_points > 0
        assert proj.projected_games > 0
        assert 0 <= proj.consistency <= 100
        assert proj.ceiling > proj.floor

    def test_no_negative_stats(self):
        ctx = _make_context()
        proj = project_season(ctx)
        for attr in ("minutes", "points", "rebounds", "assists",
                      "steals", "blocks", "turnovers", "fgm", "fga",
                      "three_pm", "three_pa", "ftm", "fta",
                      "fantasy_points", "ceiling", "floor"):
            assert getattr(proj, attr) >= 0.0, f"{attr} is negative"
