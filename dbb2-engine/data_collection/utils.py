"""
Shared utilities for DBB2 data collection and generation scripts.

Provides:
- load_all_seasons(): Read all 30 CSVs into a single DataFrame
- load_seasons_range(): Read CSVs for a specific year range
- rebucket_role(): Re-classify role from raw minutes_played (spec thresholds)
- POSITION_GROUPS: Mapping from CSV positions to simplified groups
- TEAM_CITIES: Team abbreviation to city characteristics
"""

import glob
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "raw_data"
STATIC_DATA_DIR = PROJECT_ROOT / "static_data"

# --------------------------------------------------------------------------
# Position Mapping
# --------------------------------------------------------------------------

# CSV positions: G, F, C, C-F, F-C, G-F, F-G, Unknown
# Group into 3 primary buckets for tuple keys
POSITION_GROUPS = {
    "G": "G",
    "F": "F",
    "C": "C",
    "C-F": "C",   # Center-Forward → Center (primary position first)
    "F-C": "F",   # Forward-Center → Forward
    "G-F": "G",   # Guard-Forward → Guard
    "F-G": "F",   # Forward-Guard → Forward
    "Unknown": None,
}


def normalize_position(position: str) -> Optional[str]:
    """Map CSV position to standardized group (G, F, C) or None."""
    if pd.isna(position):
        return None
    return POSITION_GROUPS.get(str(position).strip(), None)


# --------------------------------------------------------------------------
# Role Re-bucketing (spec thresholds)
# --------------------------------------------------------------------------

def rebucket_role(minutes_played: float) -> str:
    """
    Re-classify role from raw minutes_played using spec thresholds.

    Spec (model-updates.txt):
        Starter: 28+ mpg
        Rotation: 15-27 mpg
        Bench: 8-14 mpg
        Scrub: <8 mpg

    Note: The CSVs have per-game roles using 20/10 thresholds.
    For age profiles, we re-bucket using season-average minutes,
    but this function works on any minutes value.
    """
    if pd.isna(minutes_played) or minutes_played <= 0:
        return "Scrub"
    if minutes_played >= 28:
        return "Starter"
    if minutes_played >= 15:
        return "Rotation"
    if minutes_played >= 8:
        return "Bench"
    return "Scrub"


# --------------------------------------------------------------------------
# Team → City Mapping
# --------------------------------------------------------------------------

# Used for hot spot detection and altitude effects.
# Keys are team abbreviations as they appear in CSVs (may vary across eras).
TEAM_CITIES = {
    # Hot Spot Tier 1 (notorious party cities)
    "MIA": {"city": "Miami", "hot_spot": 1, "altitude": False},
    "LAL": {"city": "Los Angeles", "hot_spot": 1, "altitude": False},
    "LAC": {"city": "Los Angeles", "hot_spot": 1, "altitude": False},
    "ATL": {"city": "Atlanta", "hot_spot": 1, "altitude": False},
    "NYK": {"city": "New York", "hot_spot": 1, "altitude": False},
    "BKN": {"city": "Brooklyn", "hot_spot": 1, "altitude": False},
    "NJN": {"city": "New Jersey", "hot_spot": 1, "altitude": False},  # Nets pre-2012
    "PHX": {"city": "Phoenix", "hot_spot": 1, "altitude": False},
    "PHO": {"city": "Phoenix", "hot_spot": 1, "altitude": False},  # Alt abbreviation

    # Hot Spot Tier 2 (good scene)
    "GSW": {"city": "San Francisco", "hot_spot": 2, "altitude": False},
    "HOU": {"city": "Houston", "hot_spot": 2, "altitude": False},
    "TOR": {"city": "Toronto", "hot_spot": 2, "altitude": False},
    "DAL": {"city": "Dallas", "hot_spot": 2, "altitude": False},

    # Altitude cities
    "DEN": {"city": "Denver", "hot_spot": 0, "altitude": True, "elevation_ft": 5280},
    "UTA": {"city": "Salt Lake City", "hot_spot": 0, "altitude": True, "elevation_ft": 4226},
    "UTH": {"city": "Salt Lake City", "hot_spot": 0, "altitude": True, "elevation_ft": 4226},  # Alt

    # Regular cities (no special effects)
    "BOS": {"city": "Boston", "hot_spot": 0, "altitude": False},
    "CLE": {"city": "Cleveland", "hot_spot": 0, "altitude": False},
    "CHI": {"city": "Chicago", "hot_spot": 0, "altitude": False},
    "DET": {"city": "Detroit", "hot_spot": 0, "altitude": False},
    "IND": {"city": "Indianapolis", "hot_spot": 0, "altitude": False},
    "MIL": {"city": "Milwaukee", "hot_spot": 0, "altitude": False},
    "ORL": {"city": "Orlando", "hot_spot": 0, "altitude": False},
    "PHI": {"city": "Philadelphia", "hot_spot": 0, "altitude": False},
    "WAS": {"city": "Washington", "hot_spot": 0, "altitude": False},
    "CHA": {"city": "Charlotte", "hot_spot": 0, "altitude": False},
    "CHH": {"city": "Charlotte", "hot_spot": 0, "altitude": False},  # Hornets pre-2004
    "MEM": {"city": "Memphis", "hot_spot": 0, "altitude": False},
    "VAN": {"city": "Vancouver", "hot_spot": 0, "altitude": False},  # Grizzlies pre-2001
    "MIN": {"city": "Minneapolis", "hot_spot": 0, "altitude": False},
    "NOP": {"city": "New Orleans", "hot_spot": 0, "altitude": False},
    "NOH": {"city": "New Orleans", "hot_spot": 0, "altitude": False},  # Hornets era
    "NOK": {"city": "New Orleans", "hot_spot": 0, "altitude": False},  # OK City temp
    "OKC": {"city": "Oklahoma City", "hot_spot": 0, "altitude": False},
    "POR": {"city": "Portland", "hot_spot": 0, "altitude": False},
    "SAC": {"city": "Sacramento", "hot_spot": 0, "altitude": False},
    "SAS": {"city": "San Antonio", "hot_spot": 0, "altitude": False},
    "SEA": {"city": "Seattle", "hot_spot": 0, "altitude": False},  # Supersonics pre-2008
}


def is_hot_spot(team_abbrev: str) -> int:
    """Return hot spot tier (0=none, 1=tier1, 2=tier2) for a team."""
    info = TEAM_CITIES.get(team_abbrev)
    return info["hot_spot"] if info else 0


def is_altitude(team_abbrev: str) -> bool:
    """Return True if team plays at altitude (Denver, Utah)."""
    info = TEAM_CITIES.get(team_abbrev)
    return info["altitude"] if info else False


# --------------------------------------------------------------------------
# Data Loading
# --------------------------------------------------------------------------

# CSV columns and their expected dtypes
CSV_COLUMNS = [
    "player_name", "player_id", "game_date", "team", "opponent",
    "home_or_road", "minutes_played", "points", "rebounds", "assists",
    "steals", "blocks", "turnovers", "fgm", "fga", "fg_pct",
    "three_pm", "three_pa", "fg3_pct", "ftm", "fta", "ft_pct",
    "age", "position", "role", "opponent_def_rank_vs_position",
    "plus_minus", "wl",
]

NUMERIC_COLUMNS = [
    "minutes_played", "points", "rebounds", "assists", "steals",
    "blocks", "turnovers", "fgm", "fga", "fg_pct", "three_pm",
    "three_pa", "fg3_pct", "ftm", "fta", "ft_pct", "age",
    "opponent_def_rank_vs_position", "plus_minus",
]

STAT_COLUMNS = [
    "minutes_played", "points", "rebounds", "assists", "steals",
    "blocks", "turnovers", "fgm", "fga", "three_pm", "three_pa",
    "ftm", "fta",
]

PCT_COLUMNS = ["fg_pct", "fg3_pct", "ft_pct"]


def _season_year_from_filename(filename: str) -> int:
    """Extract start year from filename like 'games_1995_96.csv' → 1995."""
    stem = Path(filename).stem  # 'games_1995_96'
    parts = stem.split("_")
    return int(parts[1])


def load_season(filepath: str) -> pd.DataFrame:
    """Load a single season CSV into a DataFrame with proper types."""
    df = pd.read_csv(filepath)

    # Coerce numeric columns
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Parse game_date
    if "game_date" in df.columns:
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")

    # Add season_start_year from filename
    df["season_start_year"] = _season_year_from_filename(filepath)

    return df


def load_all_seasons(data_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load all 30 season CSVs into a single DataFrame.

    Args:
        data_dir: Path to raw_data directory. Defaults to project's raw_data/.

    Returns:
        Combined DataFrame with all seasons, ~733K rows.
    """
    if data_dir is None:
        data_dir = str(RAW_DATA_DIR)

    csv_files = sorted(glob.glob(f"{data_dir}/games_*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    frames = []
    for f in csv_files:
        df = load_season(f)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)

    # Add normalized position
    combined["position_group"] = combined["position"].apply(normalize_position)

    return combined


def load_seasons_range(
    start_year: int,
    end_year: int,
    data_dir: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load CSVs for seasons starting in [start_year, end_year].

    Example: load_seasons_range(2022, 2024) loads 2022-23, 2023-24, 2024-25.
    """
    if data_dir is None:
        data_dir = str(RAW_DATA_DIR)

    csv_files = sorted(glob.glob(f"{data_dir}/games_*.csv"))
    filtered = [
        f for f in csv_files
        if start_year <= _season_year_from_filename(f) <= end_year
    ]

    if not filtered:
        raise FileNotFoundError(
            f"No CSV files found for years {start_year}-{end_year} in {data_dir}"
        )

    frames = [load_season(f) for f in filtered]
    combined = pd.concat(frames, ignore_index=True)
    combined["position_group"] = combined["position"].apply(normalize_position)

    return combined


# --------------------------------------------------------------------------
# Age Bucketing (for schedule effects)
# --------------------------------------------------------------------------

def age_bucket(age: float) -> Optional[str]:
    """Classify age into buckets for schedule effect analysis."""
    if pd.isna(age):
        return None
    age = int(age)
    if age <= 21:
        return "Young"
    if age <= 26:
        return "Young"
    if age <= 30:
        return "Prime"
    return "Veteran"


# --------------------------------------------------------------------------
# Fantasy Points Calculation
# --------------------------------------------------------------------------

def calculate_fantasy_points(row) -> float:
    """
    Standard DFS fantasy scoring.
    PTS*1 + REB*1.2 + AST*1.5 + STL*3 + BLK*3 + TOV*-1
    """
    return (
        row.get("points", 0) * 1.0
        + row.get("rebounds", 0) * 1.2
        + row.get("assists", 0) * 1.5
        + row.get("steals", 0) * 3.0
        + row.get("blocks", 0) * 3.0
        + row.get("turnovers", 0) * -1.0
    )
