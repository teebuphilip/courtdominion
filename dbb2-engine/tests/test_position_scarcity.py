"""
Position scarcity multiplier tests.

Validates the generated POSITION_SCARCITY dictionary.
"""

import pytest


EXPECTED_FIELDS = {
    "scarcity_multiplier",
    "avg_quality_players",
    "avg_elite_players",
    "avg_total_players",
    "seasons_analyzed",
}


class TestPositionsPresent:
    """All three positions should be present."""

    def test_exactly_three_positions(self, position_scarcity):
        assert set(position_scarcity.keys()) == {"C", "F", "G"}


class TestCentersScarcer:
    """Centers should have higher scarcity multiplier than guards."""

    def test_center_multiplier_greater_than_guard(self, position_scarcity):
        assert position_scarcity["C"]["scarcity_multiplier"] > position_scarcity["G"]["scarcity_multiplier"], (
            f"C={position_scarcity['C']['scarcity_multiplier']} "
            f"not > G={position_scarcity['G']['scarcity_multiplier']}"
        )

    def test_center_multiplier_greater_than_forward(self, position_scarcity):
        assert position_scarcity["C"]["scarcity_multiplier"] > position_scarcity["F"]["scarcity_multiplier"], (
            f"C={position_scarcity['C']['scarcity_multiplier']} "
            f"not > F={position_scarcity['F']['scarcity_multiplier']}"
        )


class TestMultiplierRanges:
    """Multipliers should be in reasonable bounds."""

    def test_multiplier_range(self, position_scarcity):
        for pos, entry in position_scarcity.items():
            val = entry["scarcity_multiplier"]
            assert 0.70 <= val <= 1.40, (
                f"{pos}: scarcity_multiplier = {val}"
            )

    def test_multipliers_balanced(self, position_scarcity):
        """Weighted average of multipliers (by quality count) should be near 1.0."""
        total_quality = sum(
            e["avg_quality_players"] for e in position_scarcity.values()
        )
        weighted = sum(
            e["scarcity_multiplier"] * e["avg_quality_players"]
            for e in position_scarcity.values()
        ) / total_quality
        assert 0.90 <= weighted <= 1.10, (
            f"Weighted average multiplier = {weighted:.4f}"
        )


class TestFieldsPresent:
    """Every entry should have all expected fields."""

    def test_all_fields_present(self, position_scarcity):
        for pos, entry in position_scarcity.items():
            missing = EXPECTED_FIELDS - set(entry.keys())
            assert not missing, f"{pos} missing fields: {missing}"


class TestCountRelationships:
    """Quality < total, elite < quality for each position."""

    def test_quality_less_than_total(self, position_scarcity):
        for pos, entry in position_scarcity.items():
            assert entry["avg_quality_players"] < entry["avg_total_players"], (
                f"{pos}: quality {entry['avg_quality_players']} "
                f"not < total {entry['avg_total_players']}"
            )

    def test_elite_less_than_quality(self, position_scarcity):
        for pos, entry in position_scarcity.items():
            assert entry["avg_elite_players"] <= entry["avg_quality_players"], (
                f"{pos}: elite {entry['avg_elite_players']} "
                f"not <= quality {entry['avg_quality_players']}"
            )


class TestSeasonsAnalyzed:
    """All positions should show 30 seasons of data."""

    def test_thirty_seasons(self, position_scarcity):
        for pos, entry in position_scarcity.items():
            assert entry["seasons_analyzed"] == 30, (
                f"{pos}: seasons_analyzed = {entry['seasons_analyzed']}"
            )
