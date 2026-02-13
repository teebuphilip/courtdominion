"""
Hot spot hangover and altitude recovery tests.

Tests the generator logic (unit tests with synthetic data) and
validates the generated CITY_EFFECTS dictionary (integration tests).
"""

import pandas as pd
import pytest

from data_collection.utils import is_hot_spot, is_altitude


# ---------------------------------------------------------------------------
# Unit Tests — no generated data needed
# ---------------------------------------------------------------------------


class TestPreviousGameTracking:
    """Verify previous game context flagging."""

    def test_post_hot_spot_flagged(self):
        """Player plays ROAD@MIA then next day → post_hot_spot=True."""
        from data_collection.generate_city_effects import add_previous_game_context

        df = pd.DataFrame({
            "player_id": [1, 1],
            "game_date": pd.to_datetime(["2023-01-10", "2023-01-11"]),
            "opponent": ["MIA", "BOS"],
            "home_or_road": ["ROAD", "HOME"],
            "minutes_played": [30, 28],
            "points": [20, 18],
        })

        result = add_previous_game_context(df)
        assert result.iloc[1]["post_hot_spot"] is True or result.iloc[1]["post_hot_spot"] == True

    def test_post_altitude_flagged(self):
        """Player plays ROAD@DEN then next day → post_altitude=True."""
        from data_collection.generate_city_effects import add_previous_game_context

        df = pd.DataFrame({
            "player_id": [1, 1],
            "game_date": pd.to_datetime(["2023-01-10", "2023-01-11"]),
            "opponent": ["DEN", "LAL"],
            "home_or_road": ["ROAD", "HOME"],
            "minutes_played": [32, 25],
            "points": [22, 15],
        })

        result = add_previous_game_context(df)
        assert result.iloc[1]["post_altitude"] is True or result.iloc[1]["post_altitude"] == True

    def test_first_game_not_flagged(self):
        """First game of a player should never be flagged."""
        from data_collection.generate_city_effects import add_previous_game_context

        df = pd.DataFrame({
            "player_id": [1, 1],
            "game_date": pd.to_datetime(["2023-01-10", "2023-01-11"]),
            "opponent": ["MIA", "BOS"],
            "home_or_road": ["ROAD", "HOME"],
            "minutes_played": [30, 28],
            "points": [20, 18],
        })

        result = add_previous_game_context(df)
        assert result.iloc[0]["post_hot_spot"] == False
        assert result.iloc[0]["post_altitude"] == False


class TestHomeGamesExempt:
    """Home games should not trigger hot spot or altitude flags."""

    def test_home_vs_hot_spot_not_flagged(self):
        """Playing HOME vs MIA means Miami came to you — no hangover."""
        from data_collection.generate_city_effects import add_previous_game_context

        df = pd.DataFrame({
            "player_id": [1, 1],
            "game_date": pd.to_datetime(["2023-01-10", "2023-01-11"]),
            "opponent": ["MIA", "BOS"],
            "home_or_road": ["HOME", "HOME"],
            "minutes_played": [30, 28],
            "points": [20, 18],
        })

        result = add_previous_game_context(df)
        assert result.iloc[1]["post_hot_spot"] == False

    def test_home_vs_altitude_not_flagged(self):
        """Playing HOME vs DEN means Denver came to you — no altitude effect."""
        from data_collection.generate_city_effects import add_previous_game_context

        df = pd.DataFrame({
            "player_id": [1, 1],
            "game_date": pd.to_datetime(["2023-01-10", "2023-01-11"]),
            "opponent": ["DEN", "BOS"],
            "home_or_road": ["HOME", "ROAD"],
            "minutes_played": [30, 28],
            "points": [20, 18],
        })

        result = add_previous_game_context(df)
        assert result.iloc[1]["post_altitude"] == False


class TestGapTooLarge:
    """Games more than 2 days apart should not be flagged."""

    def test_hot_spot_3_day_gap(self):
        """ROAD@MIA then 3 days later → NOT post_hot_spot."""
        from data_collection.generate_city_effects import add_previous_game_context

        df = pd.DataFrame({
            "player_id": [1, 1],
            "game_date": pd.to_datetime(["2023-01-10", "2023-01-13"]),
            "opponent": ["MIA", "BOS"],
            "home_or_road": ["ROAD", "HOME"],
            "minutes_played": [30, 28],
            "points": [20, 18],
        })

        result = add_previous_game_context(df)
        assert result.iloc[1]["post_hot_spot"] == False


class TestHotSpotUtilities:
    """Verify hot spot and altitude utility functions."""

    def test_miami_is_hot_spot(self):
        assert is_hot_spot("MIA") >= 1

    def test_denver_is_altitude(self):
        assert is_altitude("DEN") is True

    def test_utah_is_altitude(self):
        assert is_altitude("UTA") is True or is_altitude("UTH") is True

    def test_boston_not_hot_spot(self):
        assert is_hot_spot("BOS") == 0

    def test_boston_not_altitude(self):
        assert is_altitude("BOS") is False


# ---------------------------------------------------------------------------
# Integration Tests — require generated profile data
# ---------------------------------------------------------------------------


EXPECTED_FIELDS = {
    "hot_spot_scoring_dropoff",
    "hot_spot_minutes_dropoff",
    "hot_spot_sample_size",
    "altitude_b2b_dropoff",
    "altitude_1day_dropoff",
    "altitude_2plus_dropoff",
    "altitude_sample_size",
}


class TestMultiplierRanges:
    """All multipliers should be in reasonable ranges."""

    def test_hot_spot_scoring_range(self, city_effects):
        """Hot spot scoring dropoff should be between 0.70 and 1.40."""
        for key, entry in city_effects.items():
            val = entry["hot_spot_scoring_dropoff"]
            if val is not None:
                assert 0.70 <= val <= 1.40, (
                    f"{key}: hot_spot_scoring_dropoff = {val}"
                )

    def test_hot_spot_minutes_range(self, city_effects):
        for key, entry in city_effects.items():
            val = entry["hot_spot_minutes_dropoff"]
            if val is not None:
                assert 0.70 <= val <= 1.40, (
                    f"{key}: hot_spot_minutes_dropoff = {val}"
                )

    def test_altitude_b2b_range(self, city_effects):
        """Altitude B2B dropoff should be between 0.60 and 1.50."""
        for key, entry in city_effects.items():
            val = entry["altitude_b2b_dropoff"]
            if val is not None:
                assert 0.60 <= val <= 1.50, (
                    f"{key}: altitude_b2b_dropoff = {val}"
                )

    def test_altitude_1day_range(self, city_effects):
        for key, entry in city_effects.items():
            val = entry["altitude_1day_dropoff"]
            if val is not None:
                assert 0.60 <= val <= 1.50, (
                    f"{key}: altitude_1day_dropoff = {val}"
                )

    def test_altitude_2plus_range(self, city_effects):
        for key, entry in city_effects.items():
            val = entry["altitude_2plus_dropoff"]
            if val is not None:
                assert 0.60 <= val <= 1.50, (
                    f"{key}: altitude_2plus_dropoff = {val}"
                )


class TestDataIntegrity:
    """Verify structure and consistency of generated data."""

    def test_all_fields_present(self, city_effects):
        for key, entry in city_effects.items():
            missing = EXPECTED_FIELDS - set(entry.keys())
            assert not missing, f"{key} missing fields: {missing}"

    def test_sample_sizes_non_negative(self, city_effects):
        for key, entry in city_effects.items():
            assert entry["hot_spot_sample_size"] >= 0, (
                f"{key}: hot_spot_sample_size = {entry['hot_spot_sample_size']}"
            )
            assert entry["altitude_sample_size"] >= 0, (
                f"{key}: altitude_sample_size = {entry['altitude_sample_size']}"
            )

    def test_valid_age_buckets(self, city_effects):
        for key in city_effects:
            bucket, pos, role = key
            assert bucket in ("Young", "Prime", "Veteran"), (
                f"Invalid age bucket: {bucket}"
            )
            assert pos in ("G", "F", "C")
            assert role in ("Starter", "Rotation", "Bench", "Scrub")

    def test_bucket_count(self, city_effects):
        """Should have up to 36 buckets (3 age x 3 pos x 4 roles)."""
        assert 20 <= len(city_effects) <= 36

    def test_keys_are_tuples(self, city_effects):
        for key in city_effects:
            assert isinstance(key, tuple) and len(key) == 3


class TestAtLeastSomeData:
    """Verify that the dataset has meaningful coverage."""

    def test_starters_have_hot_spot_data(self, city_effects):
        """At least some starter buckets should have hot spot data."""
        count = 0
        for key, entry in city_effects.items():
            if key[2] == "Starter" and entry["hot_spot_scoring_dropoff"] is not None:
                count += 1
        assert count >= 6, f"Only {count} starter buckets have hot spot data"

    def test_some_altitude_data_exists(self, city_effects):
        """At least some buckets should have altitude B2B data."""
        count = 0
        for key, entry in city_effects.items():
            if entry["altitude_b2b_dropoff"] is not None:
                count += 1
        assert count >= 5, f"Only {count} buckets have altitude B2B data"

    def test_hot_spot_sample_sizes_substantial(self, city_effects):
        """Starter hot spot sample sizes should be meaningful (>100)."""
        for key, entry in city_effects.items():
            if key[2] == "Starter" and entry["hot_spot_scoring_dropoff"] is not None:
                assert entry["hot_spot_sample_size"] >= 100, (
                    f"{key}: hot_spot_sample_size = {entry['hot_spot_sample_size']}"
                )
