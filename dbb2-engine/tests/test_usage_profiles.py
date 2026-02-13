"""
Usage rate and minutes distribution profile tests.

Tests the generator logic (unit tests with synthetic data) and
validates the generated USAGE_PROFILES dictionary (integration tests).
"""

import numpy as np
import pandas as pd
import pytest

from data_collection.generate_usage_profiles import classify_volatility


# ---------------------------------------------------------------------------
# Unit Tests — no generated data needed
# ---------------------------------------------------------------------------


class TestUsageRateCalculation:
    """Verify usage rate formula with synthetic data."""

    def test_usage_rate_formula(self):
        """usage_rate = (FGA + 0.44*FTA + TOV) / minutes_played"""
        # Player: 15 FGA, 6 FTA, 3 TOV in 36 minutes
        fga, fta, tov, mp = 15, 6, 3, 36
        expected = (fga + 0.44 * fta + tov) / mp
        assert abs(expected - 0.5733) < 0.001

    def test_fga_per_minute(self):
        """fga_per_minute = FGA / minutes_played"""
        assert 10 / 30 == pytest.approx(0.3333, abs=0.001)

    def test_build_profiles_synthetic(self):
        from data_collection.generate_usage_profiles import build_usage_profiles

        n = 60
        np.random.seed(42)
        df = pd.DataFrame({
            "age": [25] * n,
            "position_group": ["G"] * n,
            "rebucketed_role": ["Starter"] * n,
            "minutes_played": np.random.normal(32, 3, n).clip(min=1),
            "usage_rate": np.random.normal(0.5, 0.1, n),
            "fga_per_minute": np.random.normal(0.45, 0.08, n),
        })

        profiles = build_usage_profiles(df, min_sample=50)
        assert (25, "G", "Starter") in profiles
        entry = profiles[(25, "G", "Starter")]
        assert entry["sample_size"] == n
        assert 0.3 < entry["avg_usage_rate"] < 0.7

    def test_small_sample_filtered(self):
        from data_collection.generate_usage_profiles import build_usage_profiles

        n = 30
        df = pd.DataFrame({
            "age": [25] * n,
            "position_group": ["G"] * n,
            "rebucketed_role": ["Starter"] * n,
            "minutes_played": [30.0] * n,
            "usage_rate": [0.5] * n,
            "fga_per_minute": [0.4] * n,
        })

        profiles = build_usage_profiles(df, min_sample=50)
        assert len(profiles) == 0


class TestVolatilityClassification:
    """Verify minutes volatility classification thresholds."""

    def test_low_volatility(self):
        assert classify_volatility(3.0) == "low"
        assert classify_volatility(4.9) == "low"

    def test_medium_volatility(self):
        assert classify_volatility(5.0) == "medium"
        assert classify_volatility(7.5) == "medium"
        assert classify_volatility(10.0) == "medium"

    def test_high_volatility(self):
        assert classify_volatility(10.1) == "high"
        assert classify_volatility(15.0) == "high"


# ---------------------------------------------------------------------------
# Integration Tests — require generated profile data
# ---------------------------------------------------------------------------


EXPECTED_FIELDS = {
    "avg_usage_rate",
    "stddev_usage_rate",
    "avg_fga_per_minute",
    "stddev_fga_per_minute",
    "minutes_10th",
    "minutes_50th",
    "minutes_90th",
    "minutes_volatility",
    "sample_size",
}


class TestUsageRanges:
    """Validate usage rate values are in reasonable ranges."""

    def test_starter_usage_higher_than_bench(self, usage_profiles):
        """Starters should have higher avg usage rate than bench at same age/pos."""
        comparisons = 0
        starter_wins = 0
        for age in range(24, 31):
            for pos in ["G", "F", "C"]:
                s_key = (age, pos, "Starter")
                b_key = (age, pos, "Bench")
                if s_key in usage_profiles and b_key in usage_profiles:
                    comparisons += 1
                    if (
                        usage_profiles[s_key]["avg_usage_rate"]
                        > usage_profiles[b_key]["avg_usage_rate"]
                    ):
                        starter_wins += 1
        assert comparisons >= 5, "Not enough matching buckets"
        assert starter_wins / comparisons >= 0.70

    def test_usage_rate_positive(self, usage_profiles):
        for key, entry in usage_profiles.items():
            assert entry["avg_usage_rate"] > 0, f"{key}: avg_usage_rate <= 0"

    def test_fga_per_minute_reasonable(self, usage_profiles):
        """FGA per minute should be between 0 and 1.5 for all buckets."""
        for key, entry in usage_profiles.items():
            assert 0 < entry["avg_fga_per_minute"] < 1.5, (
                f"{key}: avg_fga_per_minute = {entry['avg_fga_per_minute']}"
            )


class TestMinutesPercentiles:
    """Validate minutes distribution percentiles."""

    def test_percentile_ordering(self, usage_profiles):
        """10th < 50th < 90th for all buckets."""
        for key, entry in usage_profiles.items():
            assert entry["minutes_10th"] <= entry["minutes_50th"], (
                f"{key}: 10th ({entry['minutes_10th']}) > 50th ({entry['minutes_50th']})"
            )
            assert entry["minutes_50th"] <= entry["minutes_90th"], (
                f"{key}: 50th ({entry['minutes_50th']}) > 90th ({entry['minutes_90th']})"
            )

    def test_starter_90th_above_35(self, usage_profiles):
        """Prime-age starter 90th percentile should be above 35 minutes."""
        checks = 0
        for age in range(25, 31):
            for pos in ["G", "F"]:
                key = (age, pos, "Starter")
                if key in usage_profiles:
                    assert usage_profiles[key]["minutes_90th"] >= 35, (
                        f"{key}: minutes_90th = {usage_profiles[key]['minutes_90th']}"
                    )
                    checks += 1
        assert checks >= 3


class TestBenchVsStarter:
    """Bench players should have lower minutes than starters."""

    def test_bench_median_below_starter(self, usage_profiles):
        comparisons = 0
        for age in range(24, 31):
            for pos in ["G", "F", "C"]:
                s_key = (age, pos, "Starter")
                b_key = (age, pos, "Bench")
                if s_key in usage_profiles and b_key in usage_profiles:
                    assert (
                        usage_profiles[b_key]["minutes_50th"]
                        < usage_profiles[s_key]["minutes_50th"]
                    ), f"Age {age} {pos}: bench median not < starter median"
                    comparisons += 1
        assert comparisons >= 5


class TestDataIntegrity:
    """Verify structure and consistency of generated data."""

    def test_all_fields_present(self, usage_profiles):
        for key, entry in usage_profiles.items():
            missing = EXPECTED_FIELDS - set(entry.keys())
            assert not missing, f"{key} missing fields: {missing}"

    def test_min_sample_enforced(self, usage_profiles):
        for key, entry in usage_profiles.items():
            assert entry["sample_size"] >= 50, (
                f"{key}: sample_size = {entry['sample_size']}"
            )

    def test_all_values_non_negative(self, usage_profiles):
        numeric_fields = [f for f in EXPECTED_FIELDS if f not in ("minutes_volatility", "sample_size")]
        for key, entry in usage_profiles.items():
            for field in numeric_fields:
                assert entry[field] >= 0, f"{key}: {field} = {entry[field]}"

    def test_tuple_key_types(self, usage_profiles):
        for key in usage_profiles:
            assert isinstance(key, tuple) and len(key) == 3
            assert isinstance(key[0], int)
            assert key[1] in ("G", "F", "C")
            assert key[2] in ("Starter", "Rotation", "Bench", "Scrub")

    def test_volatility_values(self, usage_profiles):
        for key, entry in usage_profiles.items():
            assert entry["minutes_volatility"] in ("low", "medium", "high"), (
                f"{key}: minutes_volatility = {entry['minutes_volatility']}"
            )


class TestVolatilityPatterns:
    """Bench players should be more volatile than starters."""

    def test_bench_more_high_volatility(self, usage_profiles):
        """Higher % of bench buckets should be 'high' volatility vs starters."""
        starter_high = 0
        starter_total = 0
        bench_high = 0
        bench_total = 0

        for key, entry in usage_profiles.items():
            _, _, role = key
            if role == "Starter":
                starter_total += 1
                if entry["minutes_volatility"] == "high":
                    starter_high += 1
            elif role == "Bench":
                bench_total += 1
                if entry["minutes_volatility"] == "high":
                    bench_high += 1

        assert starter_total >= 10 and bench_total >= 10
        starter_pct = starter_high / starter_total
        bench_pct = bench_high / bench_total
        assert bench_pct > starter_pct, (
            f"Bench high-vol {bench_pct:.0%} not > starter high-vol {starter_pct:.0%}"
        )
