"""
Tests for engine/pricing.py — auction pricing.
"""

import pytest

from engine.pricing import (
    price_auction,
    _compute_category_zscores,
    _apply_sgp_weights,
    _map_to_dollars,
    AuctionValue,
    TOTAL_BUDGET,
    MIN_PRICE,
    MAX_PRICE,
    DRAFTABLE_PLAYERS,
    SGP_STATS,
)
from engine.projections import SeasonProjection


def _make_proj(**overrides):
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


class TestZScores:
    """Z-score computation."""

    def test_all_sgp_stats_present(self):
        proj = _make_proj()
        zscores = _compute_category_zscores(proj)
        for stat in SGP_STATS:
            assert stat in zscores

    def test_elite_player_positive_zscores(self):
        """A player significantly above average should have positive z-scores."""
        proj = _make_proj(
            points=30.0, rebounds=12.0, assists=10.0,
            steals=2.5, blocks=2.0, three_pm=4.0,
        )
        zscores = _compute_category_zscores(proj)
        # Most z-scores should be positive for elite stats
        positive_count = sum(1 for z in zscores.values() if z > 0)
        assert positive_count >= 4


class TestSGPWeighting:
    """SGP weight application."""

    def test_weights_applied(self):
        from engine.lookup import get_sgp_weights
        sgp = get_sgp_weights()
        zscores = {"points": 1.0, "rebounds": 1.0, "assists": 1.0,
                    "steals": 1.0, "blocks": 1.0, "three_pm": 1.0}
        result = _apply_sgp_weights(
            zscores, "G",
            sgp["category_weights"],
            sgp["position_bonuses"],
        )
        # Blocks weight (~2.0) should make total > 6.0 (if all z=1.0)
        assert result > 6.0

    def test_position_bonus_for_center(self):
        """Center assists should get a positional bonus."""
        from engine.lookup import get_sgp_weights
        sgp = get_sgp_weights()
        zscores = {"points": 0.0, "rebounds": 0.0, "assists": 1.0,
                    "steals": 0.0, "blocks": 0.0, "three_pm": 0.0}

        val_c = _apply_sgp_weights(zscores, "C", sgp["category_weights"], sgp["position_bonuses"])
        val_g = _apply_sgp_weights(zscores, "G", sgp["category_weights"], sgp["position_bonuses"])

        # Center should get higher value for assists (position bonus)
        assert val_c > val_g


class TestDollarMapping:
    """Dollar value mapping."""

    def test_min_price(self):
        """No player should get less than $1."""
        projections = [_make_proj(player_id=f"P{i}", points=float(i))
                       for i in range(200)]
        values = price_auction(projections)
        for v in values:
            assert v.dollar_value >= MIN_PRICE

    def test_max_price(self):
        """No player should exceed $70."""
        projections = [_make_proj(player_id=f"P{i}", points=float(i * 0.2))
                       for i in range(200)]
        values = price_auction(projections)
        for v in values:
            assert v.dollar_value <= MAX_PRICE

    def test_top_player_highest(self):
        """The player with highest scarcity_adjusted should have highest dollar."""
        projections = [
            _make_proj(player_id="STAR", points=35.0, rebounds=12.0,
                       assists=10.0, steals=2.5, blocks=2.0, three_pm=4.0),
            *[_make_proj(player_id=f"P{i}", points=10.0 + i * 0.1)
              for i in range(50)],
        ]
        values = price_auction(projections)
        star = next(v for v in values if v.player_id == "STAR")
        assert star.dollar_value == max(v.dollar_value for v in values)


class TestBudgetConstraint:
    """Budget should hit $2,400 target for draftable pool."""

    def test_budget_with_large_pool(self):
        """With 200+ players, top 156 should sum close to $2,400."""
        projections = [
            _make_proj(
                player_id=f"P{i}",
                position=["G", "F", "C"][i % 3],
                points=8.0 + i * 0.15,
                rebounds=3.0 + i * 0.05,
                assists=2.0 + i * 0.05,
            )
            for i in range(200)
        ]
        values = price_auction(projections)
        total = sum(v.dollar_value for v in values)
        assert total == TOTAL_BUDGET
