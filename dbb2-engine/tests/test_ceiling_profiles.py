"""
Ceiling game (blowup probability) profile tests.

Tests the generator logic (unit tests with synthetic data) and
validates the generated CEILING_PROFILES dictionary (integration tests).
"""

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Unit Tests — no generated data needed
# ---------------------------------------------------------------------------


class TestCeilingCalculation:
    """Verify 90th percentile threshold and ceiling game logic."""

    def test_90th_percentile(self):
        """90th percentile of [1..100] should be ~90."""
        data = list(range(1, 101))
        threshold = np.percentile(data, 90)
        assert abs(threshold - 90.1) < 1.0

    def test_ceiling_game_pct_near_10(self):
        """With 100 evenly distributed values, ~10% should be at or above 90th pct."""
        data = list(range(1, 101))
        threshold = np.percentile(data, 90)
        ceiling_count = sum(1 for x in data if x >= threshold)
        pct = ceiling_count / len(data)
        assert 0.08 <= pct <= 0.15

    def test_ceiling_avg_above_overall(self):
        """Ceiling game average must exceed overall average by definition."""
        data = list(range(1, 101))
        threshold = np.percentile(data, 90)
        ceiling_games = [x for x in data if x >= threshold]
        assert np.mean(ceiling_games) > np.mean(data)


# ---------------------------------------------------------------------------
# Integration Tests — require generated profile data
# ---------------------------------------------------------------------------


EXPECTED_FIELDS = {
    "ceiling_threshold",
    "ceiling_game_pct",
    "avg_ceiling_game_pts",
    "avg_fantasy_pts",
    "sample_size",
}


class TestCeilingRanges:
    """All values should be in reasonable ranges."""

    def test_threshold_positive(self, ceiling_profiles):
        for key, entry in ceiling_profiles.items():
            assert entry["ceiling_threshold"] > 0, (
                f"{key}: ceiling_threshold = {entry['ceiling_threshold']}"
            )

    def test_ceiling_pct_range(self, ceiling_profiles):
        for key, entry in ceiling_profiles.items():
            val = entry["ceiling_game_pct"]
            assert 0.01 <= val <= 0.30, (
                f"{key}: ceiling_game_pct = {val}"
            )

    def test_avg_ceiling_positive(self, ceiling_profiles):
        for key, entry in ceiling_profiles.items():
            assert entry["avg_ceiling_game_pts"] > 0, (
                f"{key}: avg_ceiling_game_pts = {entry['avg_ceiling_game_pts']}"
            )


class TestCeilingAboveAverage:
    """Ceiling games should by definition score above overall average."""

    def test_ceiling_exceeds_average(self, ceiling_profiles):
        for key, entry in ceiling_profiles.items():
            assert entry["avg_ceiling_game_pts"] > entry["avg_fantasy_pts"], (
                f"{key}: ceiling {entry['avg_ceiling_game_pts']} "
                f"not > avg {entry['avg_fantasy_pts']}"
            )


class TestStarterHigherCeiling:
    """Starters should have higher ceiling thresholds than bench players."""

    def test_starter_threshold_above_bench(self, ceiling_profiles):
        """For matched (age, position) pairs, starter threshold > bench (majority)."""
        comparisons = 0
        starter_wins = 0
        for (age, pos, role), entry in ceiling_profiles.items():
            if role == "Starter":
                bench_key = (age, pos, "Bench")
                if bench_key in ceiling_profiles:
                    comparisons += 1
                    if entry["ceiling_threshold"] > ceiling_profiles[bench_key]["ceiling_threshold"]:
                        starter_wins += 1

        assert comparisons >= 5, f"Only {comparisons} starter-bench pairs"
        assert starter_wins > comparisons * 0.8, (
            f"Starters beat bench in only {starter_wins}/{comparisons} pairs"
        )


class TestDataIntegrity:
    """Verify structure and consistency of generated data."""

    def test_all_fields_present(self, ceiling_profiles):
        for key, entry in ceiling_profiles.items():
            missing = EXPECTED_FIELDS - set(entry.keys())
            assert not missing, f"{key} missing fields: {missing}"

    def test_sample_sizes_above_threshold(self, ceiling_profiles):
        for key, entry in ceiling_profiles.items():
            assert entry["sample_size"] >= 50, (
                f"{key}: sample_size = {entry['sample_size']}"
            )

    def test_valid_key_types(self, ceiling_profiles):
        for key in ceiling_profiles:
            age, pos, role = key
            assert isinstance(age, int), f"Age not int: {age}"
            assert pos in ("G", "F", "C"), f"Invalid position: {pos}"
            assert role in ("Starter", "Rotation", "Bench", "Scrub"), (
                f"Invalid role: {role}"
            )

    def test_bucket_count(self, ceiling_profiles):
        """Should have 100+ buckets (individual ages x 3 positions x 4 roles)."""
        assert len(ceiling_profiles) >= 100
