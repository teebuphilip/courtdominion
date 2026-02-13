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


@pytest.fixture(scope="session")
def age_profiles_overall():
    """Load the overall age profiles dict."""
    from static_data.profiles.age_profiles_overall import AGE_PROFILES_OVERALL
    return AGE_PROFILES_OVERALL


@pytest.fixture(scope="session")
def age_profiles_pre_modern():
    """Load pre-modern era profiles."""
    from static_data.profiles.age_profiles_pre_modern import AGE_PROFILES_PRE_MODERN
    return AGE_PROFILES_PRE_MODERN


@pytest.fixture(scope="session")
def age_profiles_modern():
    """Load modern era profiles."""
    from static_data.profiles.age_profiles_modern import AGE_PROFILES_MODERN
    return AGE_PROFILES_MODERN


@pytest.fixture(scope="session")
def usage_profiles():
    """Load usage rate + minutes distribution profiles."""
    from static_data.usage.usage_profiles import USAGE_PROFILES
    return USAGE_PROFILES


@pytest.fixture(scope="session")
def schedule_effects():
    """Load B2B decline + rest boost schedule effects."""
    from static_data.calendars.schedule_effects import SCHEDULE_EFFECTS
    return SCHEDULE_EFFECTS
