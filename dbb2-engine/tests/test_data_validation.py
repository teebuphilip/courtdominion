"""
CSV schema validation tests.

Validates that all 30 season CSVs have correct columns,
reasonable value ranges, and acceptable null coverage.
"""

import pytest
import pandas as pd
from pathlib import Path

from data_collection.utils import (
    CSV_COLUMNS,
    NUMERIC_COLUMNS,
    STAT_COLUMNS,
    load_season,
    normalize_position,
    rebucket_role,
)


class TestCSVSchema:
    """Verify all CSVs have the expected schema."""

    def test_all_30_seasons_exist(self, all_csv_paths):
        assert len(all_csv_paths) == 30, (
            f"Expected 30 season CSVs, found {len(all_csv_paths)}"
        )

    def test_filenames_span_1995_to_2024(self, all_csv_paths):
        stems = [p.stem for p in all_csv_paths]
        assert stems[0].startswith("games_1995"), f"First file: {stems[0]}"
        assert stems[-1].startswith("games_2024"), f"Last file: {stems[-1]}"

    def test_all_csvs_have_required_columns(self, all_csv_paths):
        required = set(CSV_COLUMNS)
        for path in all_csv_paths:
            df = pd.read_csv(path, nrows=1)
            missing = required - set(df.columns)
            assert not missing, (
                f"{path.name} missing columns: {missing}"
            )

    def test_sample_season_has_rows(self, sample_season_df):
        assert len(sample_season_df) > 10000, (
            f"Expected 10K+ rows in a season, got {len(sample_season_df)}"
        )


class TestDataQuality:
    """Verify data values are in reasonable ranges."""

    def test_minutes_played_range(self, sample_season_df):
        valid = sample_season_df["minutes_played"].dropna()
        assert valid.min() >= 0, "Negative minutes found"
        assert valid.max() <= 65, f"Unreasonable max minutes: {valid.max()}"

    def test_points_range(self, sample_season_df):
        valid = sample_season_df["points"].dropna()
        assert valid.min() >= 0, "Negative points found"
        assert valid.max() <= 85, f"Unreasonable max points: {valid.max()}"

    def test_age_range(self, sample_season_df):
        valid = sample_season_df["age"].dropna()
        assert valid.min() >= 18, f"Age below 18: {valid.min()}"
        assert valid.max() <= 45, f"Age above 45: {valid.max()}"

    def test_age_null_rate(self, sample_season_df):
        null_rate = sample_season_df["age"].isna().mean()
        assert null_rate < 0.10, (
            f"Age null rate {null_rate:.1%} exceeds 10% threshold"
        )

    def test_opponent_def_rank_range(self, sample_season_df):
        valid = sample_season_df["opponent_def_rank_vs_position"].dropna()
        assert valid.min() >= 1, f"Rank below 1: {valid.min()}"
        assert valid.max() <= 30, f"Rank above 30: {valid.max()}"

    def test_game_dates_are_valid(self, sample_season_df):
        valid = sample_season_df["game_date"].dropna()
        assert len(valid) > 0
        # Should be within NBA season range (Oct-Apr)
        assert valid.min().year >= 1995
        assert valid.max().year <= 2026

    def test_home_road_values(self, sample_season_df):
        values = sample_season_df["home_or_road"].dropna().unique()
        expected = {"HOME", "ROAD"}
        for v in values:
            assert v in expected, f"Unexpected home_or_road value: {v}"

    def test_roles_populated(self, sample_season_df):
        roles = sample_season_df["role"].dropna().unique()
        assert len(roles) >= 2, f"Expected multiple roles, got: {roles}"

    def test_positions_populated(self, sample_season_df):
        positions = sample_season_df["position"].dropna().unique()
        assert len(positions) >= 3, f"Expected multiple positions, got: {positions}"


class TestUtilities:
    """Test shared utility functions."""

    def test_normalize_position_guard(self):
        assert normalize_position("G") == "G"
        assert normalize_position("G-F") == "G"

    def test_normalize_position_forward(self):
        assert normalize_position("F") == "F"
        assert normalize_position("F-C") == "F"
        assert normalize_position("F-G") == "F"

    def test_normalize_position_center(self):
        assert normalize_position("C") == "C"
        assert normalize_position("C-F") == "C"

    def test_normalize_position_unknown(self):
        assert normalize_position("Unknown") is None
        assert normalize_position(None) is None

    def test_rebucket_role_starter(self):
        assert rebucket_role(35.0) == "Starter"
        assert rebucket_role(28.0) == "Starter"

    def test_rebucket_role_rotation(self):
        assert rebucket_role(20.0) == "Rotation"
        assert rebucket_role(15.0) == "Rotation"

    def test_rebucket_role_bench(self):
        assert rebucket_role(12.0) == "Bench"
        assert rebucket_role(8.0) == "Bench"

    def test_rebucket_role_scrub(self):
        assert rebucket_role(5.0) == "Scrub"
        assert rebucket_role(0.0) == "Scrub"
        assert rebucket_role(None) == "Scrub"


class TestNullCoverage:
    """Check null rates across all seasons for critical fields."""

    def test_age_null_rate_across_all_seasons(self, all_csv_paths):
        """Age nulls should be minimal — older seasons may have more."""
        for path in all_csv_paths:
            df = pd.read_csv(path, usecols=["age"])
            null_rate = df["age"].isna().mean()
            assert null_rate < 0.30, (
                f"{path.name}: age null rate {null_rate:.1%} exceeds 30%"
            )

    def test_critical_stats_not_null(self, sample_season_df):
        """Core stat columns should have very few nulls."""
        for col in ["points", "rebounds", "assists", "minutes_played"]:
            null_rate = sample_season_df[col].isna().mean()
            assert null_rate < 0.01, (
                f"{col} null rate {null_rate:.1%} exceeds 1%"
            )
