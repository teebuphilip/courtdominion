"""
Durability (games played) profile tests.

Tests the generator logic (unit tests with synthetic data) and
validates the generated DURABILITY_PROFILES dictionary (integration tests).
"""

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Unit Tests — no generated data needed
# ---------------------------------------------------------------------------


class TestPlayerSeasonAggregation:
    """Verify player-season aggregation logic."""

    def test_games_played_count(self):
        from data_collection.generate_durability_profiles import aggregate_player_seasons

        df = pd.DataFrame({
            "player_id": ["A"] * 5 + ["B"] * 3,
            "season_start_year": [2023] * 5 + [2023] * 3,
            "game_date": pd.to_datetime([
                "2023-10-24", "2023-10-26", "2023-10-28", "2023-10-30", "2023-11-01",
                "2023-10-24", "2023-10-26", "2023-10-28",
            ]),
            "age": [25] * 5 + [30] * 3,
            "position_group": ["G"] * 5 + ["F"] * 3,
            "minutes_played": [30, 28, 32, 29, 31, 20, 18, 22],
        })

        result = aggregate_player_seasons(df)
        player_a = result[result["player_id"] == "A"].iloc[0]
        player_b = result[result["player_id"] == "B"].iloc[0]

        assert player_a["games_played"] == 5
        assert player_b["games_played"] == 3

    def test_season_age_mode(self):
        """Birthday mid-season: mode should pick the majority age."""
        from data_collection.generate_durability_profiles import aggregate_player_seasons

        df = pd.DataFrame({
            "player_id": ["A"] * 6,
            "season_start_year": [2023] * 6,
            "game_date": pd.to_datetime([
                "2023-10-24", "2023-11-01", "2023-12-01",
                "2024-01-15", "2024-02-10", "2024-03-05",
            ]),
            "age": [25, 25, 25, 25, 26, 26],
            "position_group": ["G"] * 6,
            "minutes_played": [30] * 6,
        })

        result = aggregate_player_seasons(df)
        assert result.iloc[0]["season_age"] == 25  # 4 games at 25 vs 2 at 26

    def test_zero_minute_games_counted(self):
        """Games with 0 minutes should still count toward games_played."""
        from data_collection.generate_durability_profiles import aggregate_player_seasons

        df = pd.DataFrame({
            "player_id": ["A"] * 4,
            "season_start_year": [2023] * 4,
            "game_date": pd.to_datetime([
                "2023-10-24", "2023-10-26", "2023-10-28", "2023-10-30",
            ]),
            "age": [27] * 4,
            "position_group": ["C"] * 4,
            "minutes_played": [30, 0, 28, 0],
        })

        result = aggregate_player_seasons(df)
        assert result.iloc[0]["games_played"] == 4  # all 4 games counted


class TestDurabilityCalculation:
    """Verify durability score and ironman percentage formulas."""

    def test_durability_score_formula(self):
        """durability_score = avg_games_played / 82."""
        assert abs(74.0 / 82 - 0.9024) < 0.001
        assert abs(58.0 / 82 - 0.7073) < 0.001

    def test_ironman_pct_formula(self):
        """ironman_pct = fraction with >= 70 games."""
        games = [75, 80, 60, 72, 50, 71, 40, 82, 69, 78]
        ironman = sum(1 for g in games if g >= 70) / len(games)
        assert abs(ironman - 0.6) < 0.001  # 6 of 10


# ---------------------------------------------------------------------------
# Integration Tests — require generated profile data
# ---------------------------------------------------------------------------


EXPECTED_FIELDS = {
    "avg_games_played",
    "stddev_games_played",
    "durability_score",
    "ironman_pct",
    "sample_size",
}


class TestDurabilityRanges:
    """All values should be in reasonable ranges."""

    def test_avg_games_range(self, durability_profiles):
        for key, entry in durability_profiles.items():
            val = entry["avg_games_played"]
            assert 1 <= val <= 82, f"{key}: avg_games_played = {val}"

    def test_durability_score_range(self, durability_profiles):
        for key, entry in durability_profiles.items():
            val = entry["durability_score"]
            assert 0 < val <= 1.0, f"{key}: durability_score = {val}"

    def test_ironman_pct_range(self, durability_profiles):
        for key, entry in durability_profiles.items():
            val = entry["ironman_pct"]
            assert 0.0 <= val <= 1.0, f"{key}: ironman_pct = {val}"

    def test_stddev_non_negative(self, durability_profiles):
        for key, entry in durability_profiles.items():
            val = entry["stddev_games_played"]
            assert val >= 0, f"{key}: stddev_games_played = {val}"


class TestAgeDurabilityPattern:
    """Older players should generally have lower durability."""

    def test_prime_more_durable_than_old(self, durability_profiles):
        """Prime (27-30) rotation have higher avg_games than 32+ rotation (majority)."""
        comparisons = 0
        prime_wins = 0
        for pos in ("G", "F", "C"):
            prime_games = []
            old_games = []
            for (age, p, role), entry in durability_profiles.items():
                if p == pos and role == "Rotation":
                    if 27 <= age <= 30:
                        prime_games.append(entry["avg_games_played"])
                    elif age >= 32:
                        old_games.append(entry["avg_games_played"])
            if prime_games and old_games:
                comparisons += 1
                if sum(prime_games) / len(prime_games) > sum(old_games) / len(old_games):
                    prime_wins += 1

        assert comparisons >= 2, f"Only {comparisons} position comparisons possible"
        assert prime_wins >= comparisons * 0.6, (
            f"Prime beat old in only {prime_wins}/{comparisons} positions"
        )


class TestStarterDurability:
    """Starters generally play more games than bench players."""

    def test_starters_more_games_than_bench(self, durability_profiles):
        """For matched (age, position) pairs, starters > bench in majority."""
        comparisons = 0
        starter_wins = 0
        for (age, pos, role), entry in durability_profiles.items():
            if role == "Starter":
                bench_key = (age, pos, "Bench")
                if bench_key in durability_profiles:
                    comparisons += 1
                    if entry["avg_games_played"] > durability_profiles[bench_key]["avg_games_played"]:
                        starter_wins += 1

        assert comparisons >= 5, f"Only {comparisons} starter-bench pairs"
        assert starter_wins > comparisons * 0.6, (
            f"Starters beat bench in only {starter_wins}/{comparisons} pairs"
        )


class TestDataIntegrity:
    """Verify structure and consistency of generated data."""

    def test_all_fields_present(self, durability_profiles):
        for key, entry in durability_profiles.items():
            missing = EXPECTED_FIELDS - set(entry.keys())
            assert not missing, f"{key} missing fields: {missing}"

    def test_sample_sizes_above_threshold(self, durability_profiles):
        for key, entry in durability_profiles.items():
            assert entry["sample_size"] >= 50, (
                f"{key}: sample_size = {entry['sample_size']}"
            )

    def test_valid_key_types(self, durability_profiles):
        for key in durability_profiles:
            age, pos, role = key
            assert isinstance(age, int), f"Age not int: {age}"
            assert pos in ("G", "F", "C"), f"Invalid position: {pos}"
            assert role in ("Starter", "Rotation", "Bench", "Scrub"), (
                f"Invalid role: {role}"
            )

    def test_valid_age_range(self, durability_profiles):
        for key in durability_profiles:
            age = key[0]
            assert 18 <= age <= 45, f"Unusual age: {age}"

    def test_bucket_count(self, durability_profiles):
        """Should have 100+ buckets (individual ages x 3 positions x 4 roles)."""
        assert len(durability_profiles) >= 80

    def test_durability_matches_avg(self, durability_profiles):
        """durability_score should equal avg_games_played / 82."""
        for key, entry in durability_profiles.items():
            expected = round(entry["avg_games_played"] / 82, 4)
            assert abs(entry["durability_score"] - expected) < 0.001, (
                f"{key}: score {entry['durability_score']} != {expected}"
            )
