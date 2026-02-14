"""
Z-score baselines tests.

Validates the generated ZSCORE_BASELINES dictionary.
"""

import pytest

from data_collection.utils import STAT_COLUMNS


BASELINE_STATS = list(STAT_COLUMNS) + ["fantasy_points"]


class TestAllPositionsPresent:
    """Should have G, F, C, and ALL."""

    def test_four_keys(self, zscore_baselines):
        assert set(zscore_baselines.keys()) == {"C", "F", "G", "ALL"}


class TestFieldsPresent:
    """Each position should have mean+stddev for all stats + sample_size."""

    def test_all_stat_fields(self, zscore_baselines):
        for pos, entry in zscore_baselines.items():
            for stat in BASELINE_STATS:
                assert f"{stat}_mean" in entry, (
                    f"{pos} missing {stat}_mean"
                )
                assert f"{stat}_stddev" in entry, (
                    f"{pos} missing {stat}_stddev"
                )
            assert "sample_size" in entry, f"{pos} missing sample_size"


class TestMeansPositive:
    """All stat means should be positive."""

    def test_positive_means(self, zscore_baselines):
        for pos, entry in zscore_baselines.items():
            for stat in BASELINE_STATS:
                val = entry[f"{stat}_mean"]
                assert val >= 0, f"{pos}: {stat}_mean = {val}"


class TestStddevsPositive:
    """All stddevs should be positive."""

    def test_positive_stddevs(self, zscore_baselines):
        for pos, entry in zscore_baselines.items():
            for stat in BASELINE_STATS:
                val = entry[f"{stat}_stddev"]
                assert val > 0, f"{pos}: {stat}_stddev = {val}"


class TestPositionalPatterns:
    """Basketball domain knowledge checks."""

    def test_centers_more_rebounds(self, zscore_baselines):
        assert zscore_baselines["C"]["rebounds_mean"] > zscore_baselines["G"]["rebounds_mean"]

    def test_guards_more_assists(self, zscore_baselines):
        assert zscore_baselines["G"]["assists_mean"] > zscore_baselines["C"]["assists_mean"]

    def test_centers_more_blocks(self, zscore_baselines):
        assert zscore_baselines["C"]["blocks_mean"] > zscore_baselines["G"]["blocks_mean"]

    def test_guards_more_three_pm(self, zscore_baselines):
        assert zscore_baselines["G"]["three_pm_mean"] > zscore_baselines["C"]["three_pm_mean"]


class TestSampleSizes:
    """Each position should have substantial data."""

    def test_substantial_samples(self, zscore_baselines):
        for pos, entry in zscore_baselines.items():
            assert entry["sample_size"] >= 10000, (
                f"{pos}: sample_size = {entry['sample_size']}"
            )

    def test_all_is_sum(self, zscore_baselines):
        """ALL sample should roughly equal sum of individual positions."""
        pos_sum = sum(
            zscore_baselines[p]["sample_size"] for p in ("C", "F", "G")
        )
        all_size = zscore_baselines["ALL"]["sample_size"]
        assert abs(pos_sum - all_size) / all_size < 0.01
