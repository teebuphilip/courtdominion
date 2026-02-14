"""
SGP (Standings Gain Points) weights tests.

Validates the generated SGP_WEIGHTS dictionary.
"""

import pytest


SGP_STATS = ["points", "rebounds", "assists", "steals", "blocks", "three_pm"]


class TestCategoryWeightsPresent:
    """All 6 fantasy stat categories should have weights."""

    def test_all_stats_present(self, sgp_weights):
        weights = sgp_weights["category_weights"]
        for stat in SGP_STATS:
            assert stat in weights, f"Missing weight for {stat}"

    def test_no_extra_stats(self, sgp_weights):
        weights = sgp_weights["category_weights"]
        for stat in weights:
            assert stat in SGP_STATS, f"Unexpected stat: {stat}"


class TestPointsBaseline:
    """Points should be normalized to 1.0."""

    def test_points_is_one(self, sgp_weights):
        assert sgp_weights["category_weights"]["points"] == 1.0


class TestScarceStatsHigherWeight:
    """Blocks and assists should have higher weight than points (scarcer stats)."""

    def test_blocks_above_points(self, sgp_weights):
        weights = sgp_weights["category_weights"]
        assert weights["blocks"] > weights["points"], (
            f"blocks={weights['blocks']} not > points={weights['points']}"
        )

    def test_assists_above_points(self, sgp_weights):
        weights = sgp_weights["category_weights"]
        assert weights["assists"] > weights["points"], (
            f"assists={weights['assists']} not > points={weights['points']}"
        )


class TestWeightsRange:
    """All weights should be positive and in reasonable range."""

    def test_weights_positive(self, sgp_weights):
        for stat, w in sgp_weights["category_weights"].items():
            assert w > 0, f"{stat}: weight = {w}"

    def test_weights_reasonable(self, sgp_weights):
        for stat, w in sgp_weights["category_weights"].items():
            assert 0.5 <= w <= 2.5, f"{stat}: weight = {w}"


class TestPositionBonuses:
    """Positional rarity bonuses should exist and be valid."""

    def test_bonuses_exist(self, sgp_weights):
        bonuses = sgp_weights["position_bonuses"]
        assert len(bonuses) >= 3, f"Only {len(bonuses)} bonuses"

    def test_bonuses_above_one(self, sgp_weights):
        for key, bonus in sgp_weights["position_bonuses"].items():
            assert bonus > 1.0, f"{key}: bonus = {bonus}"

    def test_bonuses_capped(self, sgp_weights):
        for key, bonus in sgp_weights["position_bonuses"].items():
            assert bonus <= 2.0, f"{key}: bonus = {bonus}"

    def test_assists_from_center_valued(self, sgp_weights):
        """Assists from centers should get a positional bonus."""
        bonuses = sgp_weights["position_bonuses"]
        assert ("assists", "C") in bonuses, "No bonus for assists from C"
        assert bonuses[("assists", "C")] > 1.2

    def test_rebounds_from_guard_valued(self, sgp_weights):
        """Rebounds from guards should get a positional bonus."""
        bonuses = sgp_weights["position_bonuses"]
        assert ("rebounds", "G") in bonuses, "No bonus for rebounds from G"
        assert bonuses[("rebounds", "G")] > 1.2

    def test_blocks_from_guard_valued(self, sgp_weights):
        """Blocks from guards should get a positional bonus."""
        bonuses = sgp_weights["position_bonuses"]
        assert ("blocks", "G") in bonuses, "No bonus for blocks from G"


class TestSeasonsAnalyzed:
    """Should show 30 seasons."""

    def test_thirty_seasons(self, sgp_weights):
        assert sgp_weights["seasons_analyzed"] == 30
