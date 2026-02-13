#!/usr/bin/env python3
"""
Generate hot spot hangover and altitude recovery profiles from 30 years of NBA game logs.

Feature 7: Performance decline after visiting party cities (road games only)
Feature 8: Recovery time after playing at altitude cities (Denver, Utah)

Produces:
    static_data/calendars/city_effects.py

Usage:
    python -m data_collection.generate_city_effects
"""

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from data_collection.utils import (
    STATIC_DATA_DIR,
    age_bucket,
    is_altitude,
    is_hot_spot,
    load_all_seasons,
    rebucket_role,
)

MIN_SAMPLE_SIZE = 50


def compute_season_roles(df: pd.DataFrame) -> pd.DataFrame:
    """Compute season-average minutes per player-season, then re-bucket role."""
    season_avg = (
        df.groupby(["player_id", "season_start_year"])["minutes_played"]
        .mean()
        .reset_index()
        .rename(columns={"minutes_played": "season_avg_minutes"})
    )
    season_avg["rebucketed_role"] = season_avg["season_avg_minutes"].apply(rebucket_role)

    return df.merge(
        season_avg[["player_id", "season_start_year", "rebucketed_role"]],
        on=["player_id", "season_start_year"],
        how="left",
    )


def add_previous_game_context(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort by (player_id, game_date) and add previous game context columns.

    Adds:
        - days_since_last: days between consecutive games
        - prev_opponent: opponent in the previous game
        - prev_home_or_road: HOME/ROAD in the previous game
        - post_hot_spot: True if prev game was ROAD at a hot spot city within 2 days
        - post_altitude: True if prev game was ROAD at an altitude city within 2 days
    """
    df = df.sort_values(["player_id", "game_date"]).reset_index(drop=True)

    # Compute days since last game
    df["days_since_last"] = (
        df.groupby("player_id")["game_date"].diff().dt.days
    )

    # Shift opponent and home_or_road to get previous game context
    df["prev_opponent"] = df.groupby("player_id")["opponent"].shift(1)
    df["prev_home_or_road"] = df.groupby("player_id")["home_or_road"].shift(1)

    # Flag post-hot-spot games (prev game was ROAD at a hot spot, within 2 days)
    df["prev_was_road"] = df["prev_home_or_road"] == "ROAD"
    df["prev_hot_spot_tier"] = df["prev_opponent"].apply(
        lambda x: is_hot_spot(x) if pd.notna(x) else 0
    )
    df["prev_is_altitude"] = df["prev_opponent"].apply(
        lambda x: is_altitude(x) if pd.notna(x) else False
    )

    df["post_hot_spot"] = (
        df["prev_was_road"]
        & (df["prev_hot_spot_tier"] >= 1)
        & (df["days_since_last"] <= 2)
    )

    df["post_altitude"] = (
        df["prev_was_road"]
        & df["prev_is_altitude"]
        & (df["days_since_last"] <= 2)
    )

    return df


def build_city_effects(
    df: pd.DataFrame,
    min_sample: int = MIN_SAMPLE_SIZE,
) -> Dict[Tuple[str, str, str], dict]:
    """
    Build hot spot + altitude multipliers by (age_bucket, position, role).

    Compares post-hot-spot and post-altitude performance against baseline
    (games that are neither post-hot-spot nor post-altitude).
    """
    baseline = df[~df["post_hot_spot"] & ~df["post_altitude"]]
    hot_spot = df[df["post_hot_spot"]]
    alt_b2b = df[df["post_altitude"] & (df["days_since_last"] == 1)]
    alt_1day = df[df["post_altitude"] & (df["days_since_last"] == 2)]
    alt_2plus = df[df["post_altitude"] & (df["days_since_last"] >= 3)]

    group_cols = ["age_bucket", "position_group", "rebucketed_role"]

    baseline_avg = baseline.groupby(group_cols)[["minutes_played", "points"]].mean()
    hot_spot_avg = hot_spot.groupby(group_cols)[["minutes_played", "points"]].mean()
    hot_spot_counts = hot_spot.groupby(group_cols).size()

    alt_b2b_avg = alt_b2b.groupby(group_cols)[["points"]].mean()
    alt_1day_avg = alt_1day.groupby(group_cols)[["points"]].mean()
    alt_2plus_avg = alt_2plus.groupby(group_cols)[["points"]].mean()
    alt_total_counts = df[df["post_altitude"]].groupby(group_cols).size()

    profiles = {}
    for idx in baseline_avg.index:
        bucket, pos, role = idx

        hs_n = int(hot_spot_counts.get(idx, 0))
        alt_n = int(alt_total_counts.get(idx, 0))

        if hs_n < min_sample and alt_n < min_sample:
            continue

        norm_pts = baseline_avg.loc[idx, "points"]
        norm_mins = baseline_avg.loc[idx, "minutes_played"]

        if norm_pts <= 0 or norm_mins <= 0:
            continue

        entry = {}

        # F7: Hot spot effects
        if hs_n >= min_sample and idx in hot_spot_avg.index:
            entry["hot_spot_scoring_dropoff"] = round(
                float(hot_spot_avg.loc[idx, "points"] / norm_pts), 4
            )
            entry["hot_spot_minutes_dropoff"] = round(
                float(hot_spot_avg.loc[idx, "minutes_played"] / norm_mins), 4
            )
        else:
            entry["hot_spot_scoring_dropoff"] = None
            entry["hot_spot_minutes_dropoff"] = None
        entry["hot_spot_sample_size"] = hs_n

        # F8: Altitude effects by recovery window
        if alt_n >= min_sample:
            if idx in alt_b2b_avg.index and len(alt_b2b.groupby(group_cols).get_group(idx)) >= 10:
                entry["altitude_b2b_dropoff"] = round(
                    float(alt_b2b_avg.loc[idx, "points"] / norm_pts), 4
                )
            else:
                entry["altitude_b2b_dropoff"] = None

            if idx in alt_1day_avg.index and len(alt_1day.groupby(group_cols).get_group(idx)) >= 10:
                entry["altitude_1day_dropoff"] = round(
                    float(alt_1day_avg.loc[idx, "points"] / norm_pts), 4
                )
            else:
                entry["altitude_1day_dropoff"] = None

            if idx in alt_2plus_avg.index and len(alt_2plus.groupby(group_cols).get_group(idx)) >= 10:
                entry["altitude_2plus_dropoff"] = round(
                    float(alt_2plus_avg.loc[idx, "points"] / norm_pts), 4
                )
            else:
                entry["altitude_2plus_dropoff"] = None
        else:
            entry["altitude_b2b_dropoff"] = None
            entry["altitude_1day_dropoff"] = None
            entry["altitude_2plus_dropoff"] = None
        entry["altitude_sample_size"] = alt_n

        profiles[(bucket, pos, role)] = entry

    return profiles


EFFECT_FIELDS = [
    "hot_spot_scoring_dropoff",
    "hot_spot_minutes_dropoff",
    "hot_spot_sample_size",
    "altitude_b2b_dropoff",
    "altitude_1day_dropoff",
    "altitude_2plus_dropoff",
    "altitude_sample_size",
]


def write_effects_file(
    profiles: dict,
    variable_name: str,
    output_path: Path,
) -> None:
    """Write city effects dict as a Python literal to a .py file."""
    lines = []
    lines.append("# auto-generated by generate_city_effects.py")
    lines.append("# Do not edit manually — re-run the generator to update.")
    lines.append("")
    lines.append(f"{variable_name} = {{")

    for key in sorted(profiles.keys()):
        entry = profiles[key]
        bucket, pos, role = key
        lines.append(f"    ('{bucket}', '{pos}', '{role}'): {{")

        for field in EFFECT_FIELDS:
            val = entry[field]
            if val is None:
                lines.append(f"        '{field}': None,")
            else:
                lines.append(f"        '{field}': {val},")

        lines.append("    },")

    lines.append("}")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))


def main() -> None:
    """Generate hot spot + altitude city effects."""
    print("Loading all seasons...")
    df = load_all_seasons()
    print(f"  Loaded {len(df):,} rows")

    # Standard cleanup
    before = len(df)
    df = df.dropna(subset=["age"])
    df["age"] = df["age"].astype(int)
    print(f"  Dropped {before - len(df):,} rows with null age ({len(df):,} remaining)")

    before = len(df)
    df = df.dropna(subset=["position_group"])
    print(
        f"  Dropped {before - len(df):,} rows with unknown position "
        f"({len(df):,} remaining)"
    )

    before = len(df)
    df = df[df["minutes_played"] > 0]
    print(
        f"  Dropped {before - len(df):,} rows with 0 minutes "
        f"({len(df):,} remaining)"
    )

    # Compute season-average roles and age buckets
    print("Computing season-average roles...")
    df = compute_season_roles(df)
    df["age_bucket"] = df["age"].apply(age_bucket)
    df = df.dropna(subset=["age_bucket"])

    # Add previous game context and flag hot spot / altitude
    print("Tracking previous game context...")
    df = add_previous_game_context(df)

    post_hs = df["post_hot_spot"].sum()
    post_alt = df["post_altitude"].sum()
    print(f"  Post-hot-spot games: {post_hs:,}")
    print(f"  Post-altitude games: {post_alt:,}")

    # Build city effects
    print("Building city effects...")
    profiles = build_city_effects(df)
    print(f"  Buckets: {len(profiles)} (after min sample filter)")

    # Write output
    output_path = STATIC_DATA_DIR / "calendars" / "city_effects.py"
    write_effects_file(profiles, "CITY_EFFECTS", output_path)
    print(f"  Written: {output_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
