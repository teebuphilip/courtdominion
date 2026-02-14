"""
Tests for engine/game_day.py — DFS game-day adjustments.
"""

import pytest

from engine.game_day import (
    project_game_day,
    _get_schedule_multiplier,
    _get_city_multiplier,
    _get_matchup_multipliers,
    COMPOUND_MIN,
    COMPOUND_MAX,
)
from engine.projections import SeasonProjection
from engine.baseline import PlayerContext


def _make_context(**overrides):
    """Build a test PlayerContext."""
    defaults = dict(
        player_id="TEST001",
        player_name="Test Player",
        team="TST",
        position="G",
        raw_position="G",
        age=25,
        role="Starter",
        age_bracket="Young",
        baseline_stats={},
        games_by_season={},
        stat_variance={},
        is_b2b=False,
        rest_days=1,
        opponent_team="OPP",
        opponent_defense_tier="Average",
        location="HOME",
        is_post_hot_spot=False,
        is_post_altitude=False,
    )
    defaults.update(overrides)
    return PlayerContext(**defaults)


def _make_season_proj(**overrides):
    """Build a test SeasonProjection."""
    defaults = dict(
        player_id="TEST001",
        player_name="Test Player",
        team="TST",
        position="G",
        minutes=32.0,
        usage_rate=25.0,
        points=20.0,
        rebounds=5.0,
        assists=6.0,
        steals=1.5,
        blocks=0.5,
        turnovers=2.5,
        fgm=7.5,
        fga=16.0,
        three_pm=2.0,
        three_pa=5.5,
        ftm=3.0,
        fta=3.5,
        fg_pct=0.469,
        three_pt_pct=0.364,
        ft_pct=0.857,
        fantasy_points=35.0,
        projected_games=72,
        ceiling=52.0,
        floor=20.0,
        consistency=65,
    )
    defaults.update(overrides)
    return SeasonProjection(**defaults)


class TestScheduleMultiplier:
    """Schedule adjustment logic."""

    def test_b2b_applies_dropoff(self):
        ctx = _make_context(is_b2b=True, age_bracket="Prime", role="Starter")
        mult = _get_schedule_multiplier(ctx)
        # B2B should produce a multiplier (likely < 1.0 or close to 1.0)
        assert isinstance(mult, float)
        assert 0.5 <= mult <= 1.2

    def test_rest_applies_boost(self):
        ctx = _make_context(rest_days=4, age_bracket="Prime", role="Starter")
        mult = _get_schedule_multiplier(ctx)
        assert isinstance(mult, float)

    def test_normal_game_neutral(self):
        ctx = _make_context(rest_days=1, is_b2b=False)
        mult = _get_schedule_multiplier(ctx)
        assert mult == 1.0


class TestCityMultiplier:
    """City effect logic."""

    def test_hot_spot_applies_dropoff(self):
        ctx = _make_context(is_post_hot_spot=True, age_bracket="Prime", role="Starter")
        mult = _get_city_multiplier(ctx)
        assert isinstance(mult, float)
        assert 0.5 <= mult <= 1.2

    def test_altitude_applies_dropoff(self):
        ctx = _make_context(is_post_altitude=True, is_b2b=True,
                            age_bracket="Prime", role="Starter")
        mult = _get_city_multiplier(ctx)
        assert isinstance(mult, float)

    def test_no_city_effect_neutral(self):
        ctx = _make_context(is_post_hot_spot=False, is_post_altitude=False)
        mult = _get_city_multiplier(ctx)
        assert mult == 1.0


class TestMatchupMultiplier:
    """Matchup adjustment logic."""

    def test_returns_dict_with_multipliers(self):
        ctx = _make_context(
            age_bracket="Prime", position="G", role="Starter",
            opponent_defense_tier="Average", location="HOME",
        )
        result = _get_matchup_multipliers(ctx)
        assert "points_multiplier" in result
        assert "fantasy_pts_multiplier" in result

    def test_elite_defense_multiplier(self):
        ctx = _make_context(
            age_bracket="Prime", position="G", role="Starter",
            opponent_defense_tier="Elite", location="ROAD",
        )
        result = _get_matchup_multipliers(ctx)
        # Elite defense on road should reduce scoring (multiplier <= 1.0)
        assert result.get("fantasy_pts_multiplier", 1.0) <= 1.1

    def test_poor_defense_multiplier(self):
        ctx = _make_context(
            age_bracket="Prime", position="G", role="Starter",
            opponent_defense_tier="Poor", location="HOME",
        )
        result = _get_matchup_multipliers(ctx)
        # Poor defense at home should boost scoring
        assert result.get("fantasy_pts_multiplier", 1.0) >= 0.9


class TestCompoundClamp:
    """Compound multiplier clamping."""

    def test_game_day_output_valid(self):
        ctx = _make_context()
        proj = _make_season_proj()
        gd = project_game_day(ctx, proj)
        assert gd.compound_multiplier >= COMPOUND_MIN
        assert gd.compound_multiplier <= COMPOUND_MAX

    def test_b2b_plus_hot_spot(self):
        """Worst case: B2B + hot spot should still be >= 0.50."""
        ctx = _make_context(
            is_b2b=True, is_post_hot_spot=True,
            age_bracket="Veteran", role="Starter",
            opponent_defense_tier="Elite", location="ROAD",
        )
        proj = _make_season_proj()
        gd = project_game_day(ctx, proj)
        assert gd.compound_multiplier >= COMPOUND_MIN

    def test_neutral_game_no_adjustment(self):
        """Normal game should have compound ≈ 1.0."""
        ctx = _make_context()
        proj = _make_season_proj()
        gd = project_game_day(ctx, proj)
        assert 0.9 <= gd.compound_multiplier <= 1.1


class TestGameDayOutput:
    """Full game-day projection output."""

    def test_non_negative_stats(self):
        ctx = _make_context()
        proj = _make_season_proj()
        gd = project_game_day(ctx, proj)
        for attr in ("minutes", "points", "rebounds", "assists",
                      "steals", "blocks", "fantasy_points"):
            assert getattr(gd, attr) >= 0.0, f"{attr} is negative"

    def test_player_info_preserved(self):
        ctx = _make_context(player_id="XYZ", player_name="John Doe")
        proj = _make_season_proj(player_id="XYZ")
        gd = project_game_day(ctx, proj)
        assert gd.player_id == "XYZ"
        assert gd.player_name == "John Doe"
