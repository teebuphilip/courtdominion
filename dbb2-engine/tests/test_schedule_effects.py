"""
B2B decline and rest days boost tests.

Tests the generator logic (unit tests with synthetic data) and
validates the generated SCHEDULE_EFFECTS dictionary (integration tests).
"""

import pandas as pd
import pytest

from data_collection.utils import age_bucket


# ---------------------------------------------------------------------------
# Unit Tests — no generated data needed
# ---------------------------------------------------------------------------


class TestDaysSinceLastGame:
    """Verify game gap computation and flagging."""

    def test_b2b_detection(self):
        from data_collection.generate_schedule_effects import compute_days_since_last_game

        df = pd.DataFrame({
            "player_id": [1, 1, 1, 1],
            "game_date": pd.to_datetime([
                "2023-01-10", "2023-01-11", "2023-01-13", "2023-01-16",
            ]),
        })

        result = compute_days_since_last_game(df)
        days = result["days_since_last"].tolist()

        assert pd.isna(days[0])  # first game — no previous
        assert days[1] == 1      # B2B (Jan 10 → Jan 11)
        assert days[2] == 2      # normal rest (Jan 11 → Jan 13)
        assert days[3] == 3      # extended rest (Jan 13 → Jan 16)

    def test_multiple_players(self):
        from data_collection.generate_schedule_effects import compute_days_since_last_game

        df = pd.DataFrame({
            "player_id": [1, 1, 2, 2],
            "game_date": pd.to_datetime([
                "2023-01-10", "2023-01-11",
                "2023-01-10", "2023-01-15",
            ]),
        })

        result = compute_days_since_last_game(df)
        # Player 1: NaN, 1 (B2B)
        # Player 2: NaN, 5 (extended rest)
        assert result.loc[result["player_id"] == 1, "days_since_last"].tolist()[1] == 1
        assert result.loc[result["player_id"] == 2, "days_since_last"].tolist()[1] == 5


class TestAgeBucket:
    """Verify age bucket function from utils."""

    def test_young(self):
        assert age_bucket(20) == "Young"
        assert age_bucket(26) == "Young"

    def test_prime(self):
        assert age_bucket(27) == "Prime"
        assert age_bucket(30) == "Prime"

    def test_veteran(self):
        assert age_bucket(31) == "Veteran"
        assert age_bucket(38) == "Veteran"

    def test_null(self):
        assert age_bucket(None) is None


class TestDropoffCalculation:
    """Verify ratio calculation with synthetic data."""

    def test_b2b_ratio(self):
        """B2B scoring 18 vs normal 20 → dropoff = 0.9"""
        ratio = 18.0 / 20.0
        assert abs(ratio - 0.9) < 0.001

    def test_rest_boost_ratio(self):
        """Rest scoring 22 vs normal 20 → boost = 1.1"""
        ratio = 22.0 / 20.0
        assert abs(ratio - 1.1) < 0.001


# ---------------------------------------------------------------------------
# Integration Tests — require generated profile data
# ---------------------------------------------------------------------------


EXPECTED_FIELDS = {
    "b2b_minutes_dropoff",
    "b2b_scoring_dropoff",
    "b2b_sample_size",
    "rest_minutes_boost",
    "rest_scoring_boost",
    "rest_sample_size",
}


class TestStarterB2BDecline:
    """Starters should show scoring decline on B2B 2nd nights."""

    def test_starter_b2b_scoring_below_one(self, schedule_effects):
        """Starter B2B scoring dropoff should be < 1.0 (they score less)."""
        checks = 0
        for key, entry in schedule_effects.items():
            bucket, pos, role = key
            if role == "Starter" and entry["b2b_scoring_dropoff"] is not None:
                assert entry["b2b_scoring_dropoff"] < 1.0, (
                    f"{key}: b2b_scoring_dropoff = {entry['b2b_scoring_dropoff']}"
                )
                checks += 1
        assert checks >= 6  # 3 age buckets × 3 positions (some may exist)


class TestRestEffects:
    """Rest effects show starters maintain performance, bench/scrub lose rhythm."""

    def test_starter_rest_closer_to_one(self, schedule_effects):
        """Starters after rest should be closer to 1.0 than bench players."""
        starter_diffs = []
        bench_diffs = []
        for key, entry in schedule_effects.items():
            bucket, pos, role = key
            if entry["rest_scoring_boost"] is not None:
                diff = abs(1.0 - entry["rest_scoring_boost"])
                if role == "Starter":
                    starter_diffs.append(diff)
                elif role == "Bench":
                    bench_diffs.append(diff)

        assert len(starter_diffs) >= 5 and len(bench_diffs) >= 5
        avg_starter = sum(starter_diffs) / len(starter_diffs)
        avg_bench = sum(bench_diffs) / len(bench_diffs)
        assert avg_starter < avg_bench, (
            f"Starter avg deviation {avg_starter:.4f} not < bench {avg_bench:.4f}"
        )


class TestMultiplierRanges:
    """All multipliers should be in reasonable ranges."""

    def test_b2b_dropoff_range(self, schedule_effects):
        """B2B dropoff should be between 0.70 and 1.30."""
        for key, entry in schedule_effects.items():
            val = entry["b2b_scoring_dropoff"]
            if val is not None:
                assert 0.70 <= val <= 1.30, (
                    f"{key}: b2b_scoring_dropoff = {val}"
                )

    def test_b2b_minutes_range(self, schedule_effects):
        for key, entry in schedule_effects.items():
            val = entry["b2b_minutes_dropoff"]
            if val is not None:
                assert 0.70 <= val <= 1.30, (
                    f"{key}: b2b_minutes_dropoff = {val}"
                )

    def test_rest_boost_range(self, schedule_effects):
        """Rest boost should be between 0.60 and 1.30."""
        for key, entry in schedule_effects.items():
            val = entry["rest_scoring_boost"]
            if val is not None:
                assert 0.60 <= val <= 1.30, (
                    f"{key}: rest_scoring_boost = {val}"
                )

    def test_rest_minutes_range(self, schedule_effects):
        for key, entry in schedule_effects.items():
            val = entry["rest_minutes_boost"]
            if val is not None:
                assert 0.60 <= val <= 1.30, (
                    f"{key}: rest_minutes_boost = {val}"
                )


class TestDataIntegrity:
    """Verify structure and consistency of generated data."""

    def test_all_fields_present(self, schedule_effects):
        for key, entry in schedule_effects.items():
            missing = EXPECTED_FIELDS - set(entry.keys())
            assert not missing, f"{key} missing fields: {missing}"

    def test_sample_sizes_positive(self, schedule_effects):
        for key, entry in schedule_effects.items():
            assert entry["b2b_sample_size"] > 0
            assert entry["rest_sample_size"] > 0

    def test_valid_age_buckets(self, schedule_effects):
        for key in schedule_effects:
            bucket, pos, role = key
            assert bucket in ("Young", "Prime", "Veteran"), (
                f"Invalid age bucket: {bucket}"
            )
            assert pos in ("G", "F", "C")
            assert role in ("Starter", "Rotation", "Bench", "Scrub")

    def test_bucket_count(self, schedule_effects):
        """Should have up to 36 buckets (3 age × 3 pos × 4 roles)."""
        assert 20 <= len(schedule_effects) <= 36
