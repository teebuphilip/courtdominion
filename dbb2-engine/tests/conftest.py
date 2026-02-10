"""
Shared test fixtures for DBB2 engine tests.
"""

import pytest
import pandas as pd
from pathlib import Path

from data_collection.utils import RAW_DATA_DIR, load_season, load_all_seasons


@pytest.fixture(scope="session")
def raw_data_dir():
    """Path to raw data directory."""
    return RAW_DATA_DIR


@pytest.fixture(scope="session")
def sample_season_path(raw_data_dir):
    """Path to a single recent season CSV for quick tests."""
    path = raw_data_dir / "games_2023_24.csv"
    if not path.exists():
        pytest.skip("Sample season CSV not found")
    return str(path)


@pytest.fixture(scope="session")
def sample_season_df(sample_season_path):
    """DataFrame of a single recent season."""
    return load_season(sample_season_path)


@pytest.fixture(scope="session")
def all_csv_paths(raw_data_dir):
    """Sorted list of all CSV file paths."""
    paths = sorted(raw_data_dir.glob("games_*.csv"))
    if not paths:
        pytest.skip("No raw data CSVs found")
    return paths
