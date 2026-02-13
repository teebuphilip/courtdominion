"""
Age-based performance profile tests.

Tests the generator logic (unit tests with synthetic data) and
validates the generated profile dictionaries (integration tests).
"""

import numpy as np
import pandas as pd
import pytest

from data_collection.utils import STAT_COLUMNS, rebucket_role


# ---------------------------------------------------------------------------
# Unit Tests — no generated data needed
# ---------------------------------------------------------------------------


class TestBucketingLogic:
    """Verify role re-bucketing from season-average minutes."""

    def test_starter_threshold(self):
        assert rebucket_role(35.0) == "Starter"
        assert rebucket_role(28.0) == "Starter"

    def test_rotation_threshold(self):
        assert rebucket_role(20.0) == "Rotation"
        assert rebucket_role(15.0) == "Rotation"
        assert rebucket_role(27.9) == "Rotation"

    def test_bench_threshold(self):
        assert rebucket_role(10.0) == "Bench"
        assert rebucket_role(8.0) == "Bench"
        assert rebucket_role(14.9) == "Bench"

    def test_scrub_threshold(self):
        assert rebucket_role(5.0) == "Scrub"
        assert rebucket_role(7.9) == "Scrub"
        assert rebucket_role(0.0) == "Scrub"

    def test_null_minutes(self):
        assert rebucket_role(None) == "Scrub"


class TestGeneratorFunction:
    """Test the generator's internal functions with synthetic data."""

    def test_compute_season_roles(self):
        from data_collection.generate_age_profiles import compute_season_roles

        df = pd.DataFrame({
            "player_id": [1, 1, 1, 2, 2, 2],
            "season_start_year": [2020, 2020, 2020, 2020, 2020, 2020],
            "minutes_played": [35.0, 30.0, 12.0, 10.0, 8.0, 6.0],
        })

        result = compute_season_roles(df)

        # Player 1: avg = (35+30+12)/3 = 25.67 -> Rotation
        assert result.loc[0, "rebucketed_role"] == "Rotation"
        assert result.loc[1, "rebucketed_role"] == "Rotation"
        assert result.loc[2, "rebucketed_role"] == "Rotation"

        # Player 2: avg = (10+8+6)/3 = 8.0 -> Bench
        assert result.loc[3, "rebucketed_role"] == "Bench"
        assert result.loc[4, "rebucketed_role"] == "Bench"
        assert result.loc[5, "rebucketed_role"] == "Bench"

    def test_build_profiles_basic(self):
        from data_collection.generate_age_profiles import build_profiles

        n = 60
        np.random.seed(42)
        df = pd.DataFrame({
            "age": [25] * n,
            "position_group": ["G"] * n,
            "rebucketed_role": ["Starter"] * n,
            "minutes_played": np.random.normal(32, 3, n),
            "points": np.random.normal(20, 5, n),
            "rebounds": np.random.normal(4, 2, n),
            "assists": np.random.normal(6, 2, n),
            "steals": np.random.normal(1.2, 0.8, n),
            "blocks": np.random.normal(0.3, 0.5, n),
            "turnovers": np.random.normal(2.5, 1.2, n),
            "fgm": np.random.normal(7, 2, n),
            "fga": np.random.normal(16, 3, n),
            "three_pm": np.random.normal(2, 1, n),
            "three_pa": np.random.normal(6, 2, n),
            "ftm": np.random.normal(4, 2, n),
            "fta": np.random.normal(5, 2, n),
        })

        profiles = build_profiles(df, min_sample=50)

        assert (25, "G", "Starter") in profiles
        entry = profiles[(25, "G", "Starter")]
        assert entry["sample_size"] == n
        assert 15 < entry["avg_points"] < 25

    def test_small_sample_filtered(self):
        from data_collection.generate_age_profiles import build_profiles

        n = 30  # below threshold
        df = pd.DataFrame({
            "age": [25] * n,
            "position_group": ["G"] * n,
            "rebucketed_role": ["Starter"] * n,
            **{stat: [10.0] * n for stat in STAT_COLUMNS},
        })

        profiles = build_profiles(df, min_sample=50)
        assert len(profiles) == 0


# ---------------------------------------------------------------------------
# Integration Tests — require generated profile data
# ---------------------------------------------------------------------------


class TestKnownPlayerSanityChecks:
    """Validate realistic stat ranges for common buckets."""

    def test_prime_starter_points(self, age_profiles_overall):
        """Age 25-30 starters should average > 14 points."""
        for age in range(25, 31):
            for pos in ["G", "F", "C"]:
                key = (age, pos, "Starter")
                if key in age_profiles_overall:
                    assert age_profiles_overall[key]["avg_points"] > 14.0, (
                        f"{key}: avg_points = {age_profiles_overall[key]['avg_points']}"
                    )

    def test_guards_more_assists_than_centers(self, age_profiles_overall):
        """Guard starters should average more assists than center starters."""
        for age in range(25, 31):
            g_key = (age, "G", "Starter")
            c_key = (age, "C", "Starter")
            if g_key in age_profiles_overall and c_key in age_profiles_overall:
                assert (
                    age_profiles_overall[g_key]["avg_assists"]
                    > age_profiles_overall[c_key]["avg_assists"]
                ), f"Age {age}: G assists not > C assists"

    def test_centers_more_rebounds_than_guards(self, age_profiles_overall):
        """Center starters should average more rebounds than guard starters."""
        for age in range(25, 31):
            g_key = (age, "G", "Starter")
            c_key = (age, "C", "Starter")
            if g_key in age_profiles_overall and c_key in age_profiles_overall:
                assert (
                    age_profiles_overall[c_key]["avg_rebounds"]
                    > age_profiles_overall[g_key]["avg_rebounds"]
                ), f"Age {age}: C rebounds not > G rebounds"


class TestModernEraThreePoint:
    """Modern era should show higher three-point volume."""

    def test_modern_three_pm_higher(self, age_profiles_modern, age_profiles_pre_modern):
        """Modern era 3PM avg should exceed pre-modern in 70%+ of matching buckets."""
        matches_found = 0
        modern_wins = 0
        for key in age_profiles_modern:
            if key in age_profiles_pre_modern:
                matches_found += 1
                if (
                    age_profiles_modern[key]["avg_three_pm"]
                    > age_profiles_pre_modern[key]["avg_three_pm"]
                ):
                    modern_wins += 1

        assert matches_found >= 10, "Not enough matching buckets to compare"
        assert modern_wins / matches_found > 0.70, (
            f"Modern era 3PM higher in only {modern_wins}/{matches_found} buckets"
        )

    def test_modern_three_pa_higher(self, age_profiles_modern, age_profiles_pre_modern):
        """Modern era three-point attempts should also be higher."""
        matches_found = 0
        modern_wins = 0
        for key in age_profiles_modern:
            if key in age_profiles_pre_modern:
                matches_found += 1
                if (
                    age_profiles_modern[key]["avg_three_pa"]
                    > age_profiles_pre_modern[key]["avg_three_pa"]
                ):
                    modern_wins += 1

        assert matches_found >= 10
        assert modern_wins / matches_found > 0.70


class TestSampleSizes:
    """Verify sample sizes are reasonable."""

    def test_prime_ages_have_large_samples(self, age_profiles_overall):
        """Ages 25-30 G/F starters should have 200+ games."""
        for age in range(25, 31):
            for pos in ["G", "F"]:
                key = (age, pos, "Starter")
                if key in age_profiles_overall:
                    assert age_profiles_overall[key]["sample_size"] >= 200, (
                        f"{key}: sample_size = {age_profiles_overall[key]['sample_size']}"
                    )

    def test_overall_has_more_buckets_than_modern(
        self, age_profiles_overall, age_profiles_modern
    ):
        """Overall era (30 years) should have more buckets than modern (8 years)."""
        assert len(age_profiles_overall) > len(age_profiles_modern)


class TestEdgeCases:
    """Test boundary ages."""

    def test_age_19_exists(self, age_profiles_overall):
        """At least one age-19 bucket should exist in overall."""
        age_19_keys = [k for k in age_profiles_overall if k[0] == 19]
        assert len(age_19_keys) >= 1, "No age 19 buckets found"

    def test_age_39_plus_sparse(self, age_profiles_overall):
        """Ages 39+ should have fewer buckets than ages 25-30."""
        old_keys = [k for k in age_profiles_overall if k[0] >= 39]
        prime_keys = [k for k in age_profiles_overall if 25 <= k[0] <= 30]
        assert len(old_keys) < len(prime_keys)

    def test_old_players_generally_lower_scoring(self, age_profiles_overall):
        """Majority of age 38 buckets should score fewer points than age 27.

        Survivor bias means a few age-38 buckets (e.g. F/Starter = LeBron)
        may outscore the broader age-27 pool. But across all matching
        position/role combos, the majority should show decline.
        """
        comparisons = 0
        declines = 0
        for pos in ["G", "F", "C"]:
            for role in ["Starter", "Rotation"]:
                old_key = (38, pos, role)
                prime_key = (27, pos, role)
                if old_key in age_profiles_overall and prime_key in age_profiles_overall:
                    comparisons += 1
                    if (
                        age_profiles_overall[old_key]["avg_points"]
                        <= age_profiles_overall[prime_key]["avg_points"]
                    ):
                        declines += 1
        assert comparisons >= 3, "Not enough matching buckets"
        assert declines / comparisons >= 0.60, (
            f"Only {declines}/{comparisons} buckets show age decline"
        )


class TestDataIntegrity:
    """Verify mathematical consistency and non-negativity."""

    def test_all_averages_non_negative(self, age_profiles_overall):
        for key, entry in age_profiles_overall.items():
            for stat in STAT_COLUMNS:
                avg_val = entry[f"avg_{stat}"]
                assert avg_val >= 0, f"{key}: avg_{stat} = {avg_val}"

    def test_all_stddev_non_negative(self, age_profiles_overall):
        for key, entry in age_profiles_overall.items():
            for stat in STAT_COLUMNS:
                stddev_val = entry[f"stddev_{stat}"]
                assert stddev_val >= 0, f"{key}: stddev_{stat} = {stddev_val}"

    def test_variance_approx_stddev_squared(self, age_profiles_overall):
        """variance should approximately equal stddev^2."""
        for key, entry in age_profiles_overall.items():
            for stat in STAT_COLUMNS:
                stddev = entry[f"stddev_{stat}"]
                variance = entry[f"variance_{stat}"]
                expected = stddev ** 2
                assert abs(variance - expected) < 0.1, (
                    f"{key}: variance_{stat}={variance}, stddev^2={expected}"
                )

    def test_min_sample_enforced(self, age_profiles_overall):
        for key, entry in age_profiles_overall.items():
            assert entry["sample_size"] >= 50, (
                f"{key}: sample_size = {entry['sample_size']}"
            )

    def test_min_sample_enforced_modern(self, age_profiles_modern):
        for key, entry in age_profiles_modern.items():
            assert entry["sample_size"] >= 50

    def test_min_sample_enforced_pre_modern(self, age_profiles_pre_modern):
        for key, entry in age_profiles_pre_modern.items():
            assert entry["sample_size"] >= 50

    def test_all_expected_fields_present(self, age_profiles_overall):
        """Every bucket should have all 39 stat fields + sample_size."""
        expected_fields = set()
        for stat in STAT_COLUMNS:
            expected_fields.add(f"avg_{stat}")
            expected_fields.add(f"stddev_{stat}")
            expected_fields.add(f"variance_{stat}")
        expected_fields.add("sample_size")

        for key, entry in age_profiles_overall.items():
            missing = expected_fields - set(entry.keys())
            assert not missing, f"{key} missing fields: {missing}"

    def test_tuple_key_types(self, age_profiles_overall):
        """Keys should be (int, str, str) tuples."""
        for key in age_profiles_overall:
            assert isinstance(key, tuple) and len(key) == 3
            assert isinstance(key[0], int), f"Age not int: {type(key[0])}"
            assert isinstance(key[1], str), f"Position not str: {type(key[1])}"
            assert isinstance(key[2], str), f"Role not str: {type(key[2])}"
            assert key[1] in ("G", "F", "C"), f"Invalid position: {key[1]}"
            assert key[2] in ("Starter", "Rotation", "Bench", "Scrub"), (
                f"Invalid role: {key[2]}"
            )
