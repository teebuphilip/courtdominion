#!/usr/bin/env python3
"""
Generate death spot compound effects from 30 years of NBA game logs.

Feature 2: Schedule patterns where performance penalties compound beyond
what individual B2B, hot spot, and altitude effects predict.

5 death spot patterns:
    party_b2b:          B2B after ROAD game at hot spot tier 1
    altitude_b2b:       B2B after ROAD game at altitude city
    cross_country_b2b:  B2B with 3+ timezone hour jump
    party_to_altitude:  At altitude within 2 days of ROAD hot spot game
    compound:           2+ patterns overlapping on one game

For overlapping patterns (party_b2b, altitude_b2b), computes RESIDUAL
multipliers — the extra penalty beyond what schedule_effects and
city_effects already capture individually. For unique patterns
(cross_country_b2b, party_to_altitude, compound), computes the residual
relative to what existing B2B/city effects would predict.

Produces:
    static_data/calendars/death_spot_effects.py

Usage:
    python -m data_collection.generate_death_spot_effects
"""

from pathlib import Path
from typing import Dict, Tuple, Optional

import pandas as pd

from data_collection.utils import (
    STATIC_DATA_DIR,
    age_bucket,
    is_altitude,
    is_hot_spot,
    load_all_seasons,
    rebucket_role,
    timezone_jump,
    TEAM_TIMEZONES,
)

# Lower than the 50 used by other generators — compound patterns are rarer
MIN_SAMPLE_SIZE = 30


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


def add_death_spot_context(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort by (player_id, game_date) and add death spot pattern flags.

    Adds columns for each of the 5 death spot patterns plus
    the location context needed for timezone calculations.
    """
    df = df.sort_values(["player_id", "game_date"]).reset_index(drop=True)

    # Days since last game
    df["days_since_last"] = (
        df.groupby("player_id")["game_date"].diff().dt.days
    )

    # Previous game context
    df["prev_opponent"] = df.groupby("player_id")["opponent"].shift(1)
    df["prev_home_or_road"] = df.groupby("player_id")["home_or_road"].shift(1)
    df["prev_team"] = df.groupby("player_id")["team"].shift(1)

    # Two-games-back context (for party_to_altitude sequences)
    df["prev2_opponent"] = df.groupby("player_id")["opponent"].shift(2)
    df["prev2_home_or_road"] = df.groupby("player_id")["home_or_road"].shift(2)
    df["days_since_2_ago"] = (
        df.groupby("player_id")["game_date"]
        .apply(lambda x: x.diff(2))
        .reset_index(level=0, drop=True)
        .dt.days
    )

    # B2B flag
    df["is_b2b"] = df["days_since_last"] == 1

    # Previous game city (where the player physically was)
    df["prev_city_team"] = df.apply(
        lambda r: r["prev_opponent"] if r["prev_home_or_road"] == "ROAD" else r["prev_team"],
        axis=1,
    )
    # Current game city
    df["curr_city_team"] = df.apply(
        lambda r: r["opponent"] if r["home_or_road"] == "ROAD" else r["team"],
        axis=1,
    )

    # Previous game flags
    df["prev_was_road"] = df["prev_home_or_road"] == "ROAD"
    df["prev_hot_spot_1"] = df["prev_opponent"].apply(
        lambda x: is_hot_spot(x) == 1 if pd.notna(x) else False
    )
    df["prev_is_altitude"] = df["prev_opponent"].apply(
        lambda x: is_altitude(x) if pd.notna(x) else False
    )

    # Two-games-back flags
    df["prev2_was_road"] = df["prev2_home_or_road"] == "ROAD"
    df["prev2_hot_spot_1"] = df["prev2_opponent"].apply(
        lambda x: is_hot_spot(x) == 1 if pd.notna(x) else False
    )

    # Current game at altitude?
    df["curr_is_altitude"] = df.apply(
        lambda r: is_altitude(r["opponent"]) if r["home_or_road"] == "ROAD"
        else is_altitude(r["team"]),
        axis=1,
    )

    # Timezone jump on B2Bs
    df["tz_jump"] = df.apply(
        lambda r: timezone_jump(str(r["prev_city_team"]), str(r["curr_city_team"]))
        if pd.notna(r["prev_city_team"]) and pd.notna(r["curr_city_team"])
        else 0,
        axis=1,
    )

    # --- Pattern flags ---

    # 1. Party B2B: B2B after ROAD game at hot spot tier 1
    df["ds_party_b2b"] = (
        df["is_b2b"]
        & df["prev_was_road"]
        & df["prev_hot_spot_1"]
    )

    # 2. Altitude B2B: B2B after ROAD game at altitude city
    df["ds_altitude_b2b"] = (
        df["is_b2b"]
        & df["prev_was_road"]
        & df["prev_is_altitude"]
    )

    # 3. Cross-country B2B: B2B with 3+ timezone jump
    df["ds_cross_country_b2b"] = (
        df["is_b2b"]
        & (df["tz_jump"] >= 3)
    )

    # 4. Party to altitude: at altitude within 2 days of ROAD hot spot game
    # Either prev game was ROAD at hot spot (within 2 days)
    # or 2-games-ago was ROAD at hot spot (within 2 days total)
    df["ds_party_to_altitude"] = (
        df["curr_is_altitude"]
        & (
            (df["prev_was_road"] & df["prev_hot_spot_1"] & (df["days_since_last"] <= 2))
            | (df["prev2_was_road"] & df["prev2_hot_spot_1"] & df["days_since_2_ago"].notna() & (df["days_since_2_ago"] <= 3))
        )
    )

    # 5. Compound: 2+ patterns active
    pattern_cols = ["ds_party_b2b", "ds_altitude_b2b", "ds_cross_country_b2b", "ds_party_to_altitude"]
    df["ds_pattern_count"] = df[pattern_cols].sum(axis=1)
    df["ds_compound"] = df["ds_pattern_count"] >= 2

    # Any death spot
    df["ds_any"] = df["ds_pattern_count"] >= 1

    return df


def _get_individual_prediction(
    schedule_effects: dict,
    city_effects: dict,
    bucket: str,
    pos: str,
    role: str,
    pattern: str,
) -> float:
    """
    Compute what individual effects predict for this pattern + bucket.

    Returns the product of individual multipliers that would be applied
    by schedule_effects and city_effects in the engine.
    """
    sched = schedule_effects.get((bucket, pos, role), {})
    city = city_effects.get((bucket, pos, role), {})

    b2b_drop = sched.get("b2b_scoring_dropoff") or 1.0

    if pattern == "party_b2b":
        hs_drop = city.get("hot_spot_scoring_dropoff") or 1.0
        return b2b_drop * hs_drop

    elif pattern == "altitude_b2b":
        alt_drop = city.get("altitude_b2b_dropoff") or 1.0
        return b2b_drop * alt_drop

    elif pattern == "cross_country_b2b":
        # Only B2B is an existing effect — timezone jump is the new part
        return b2b_drop

    elif pattern == "party_to_altitude":
        # Hot spot + altitude — but may or may not be a B2B
        hs_drop = city.get("hot_spot_scoring_dropoff") or 1.0
        alt_drop = city.get("altitude_1day_dropoff") or 1.0
        return hs_drop * alt_drop

    elif pattern == "compound":
        # Use the worst individual prediction (most penalty)
        hs_drop = city.get("hot_spot_scoring_dropoff") or 1.0
        alt_drop = city.get("altitude_b2b_dropoff") or 1.0
        return b2b_drop * min(hs_drop, alt_drop)

    return 1.0


def build_death_spot_effects(
    df: pd.DataFrame,
    min_sample: int = MIN_SAMPLE_SIZE,
) -> Dict[Tuple[str, str, str], dict]:
    """
    Build death spot residual multipliers by (age_bucket, position, role).

    Compares death-spot performance against baseline, then divides out
    the predicted individual effects to get the residual compound penalty.
    """
    # Load existing static data for residual computation
    from static_data.calendars.schedule_effects import SCHEDULE_EFFECTS
    from static_data.calendars.city_effects import CITY_EFFECTS

    # Baseline: games with NO death spot flags
    baseline = df[~df["ds_any"]]

    # Pattern subsets
    party_b2b = df[df["ds_party_b2b"]]
    altitude_b2b = df[df["ds_altitude_b2b"]]
    cross_country = df[df["ds_cross_country_b2b"]]
    party_altitude = df[df["ds_party_to_altitude"]]
    compound = df[df["ds_compound"]]

    group_cols = ["age_bucket", "position_group", "rebucketed_role"]

    baseline_avg = baseline.groupby(group_cols)["points"].mean()

    pattern_data = {
        "party_b2b": (party_b2b, "party_b2b_residual"),
        "altitude_b2b": (altitude_b2b, "altitude_b2b_residual"),
        "cross_country_b2b": (cross_country, "cross_country_b2b_dropoff"),
        "party_to_altitude": (party_altitude, "party_to_altitude_dropoff"),
        "compound": (compound, "compound_worst_dropoff"),
    }

    # Compute per-pattern averages and counts
    pattern_avgs = {}
    pattern_counts = {}
    for name, (subset, _) in pattern_data.items():
        pattern_avgs[name] = subset.groupby(group_cols)["points"].mean()
        pattern_counts[name] = subset.groupby(group_cols).size()

    profiles = {}

    for idx in baseline_avg.index:
        bucket, pos, role = idx
        norm_pts = baseline_avg.loc[idx]

        if norm_pts <= 0:
            continue

        # Check if any pattern has enough samples
        any_valid = False
        for name in pattern_data:
            if int(pattern_counts[name].get(idx, 0)) >= min_sample:
                any_valid = True
                break

        if not any_valid:
            continue

        entry = {}

        for pattern_name, (_, field_name) in pattern_data.items():
            n = int(pattern_counts[pattern_name].get(idx, 0))
            entry[f"sample_size_{pattern_name}"] = n

            if n >= min_sample and idx in pattern_avgs[pattern_name].index:
                observed = float(pattern_avgs[pattern_name].loc[idx] / norm_pts)

                # Divide out the individual prediction to get residual
                predicted = _get_individual_prediction(
                    SCHEDULE_EFFECTS, CITY_EFFECTS, bucket, pos, role, pattern_name,
                )

                if predicted > 0:
                    residual = round(observed / predicted, 4)
                else:
                    residual = round(observed, 4)

                entry[field_name] = residual
            else:
                entry[field_name] = None

        profiles[(bucket, pos, role)] = entry

    return profiles


EFFECT_FIELDS = [
    "party_b2b_residual",
    "sample_size_party_b2b",
    "altitude_b2b_residual",
    "sample_size_altitude_b2b",
    "cross_country_b2b_dropoff",
    "sample_size_cross_country_b2b",
    "party_to_altitude_dropoff",
    "sample_size_party_to_altitude",
    "compound_worst_dropoff",
    "sample_size_compound",
]


def write_effects_file(
    profiles: dict,
    variable_name: str,
    output_path: Path,
) -> None:
    """Write death spot effects dict as a Python literal to a .py file."""
    lines = []
    lines.append("# auto-generated by generate_death_spot_effects.py")
    lines.append("# Do not edit manually — re-run the generator to update.")
    lines.append("")
    lines.append(f"{variable_name} = {{")

    for key in sorted(profiles.keys()):
        entry = profiles[key]
        bucket, pos, role = key
        lines.append(f"    ('{bucket}', '{pos}', '{role}'): {{")

        for field in EFFECT_FIELDS:
            val = entry.get(field)
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
    """Generate death spot compound effects."""
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
    print(f"  Dropped {before - len(df):,} rows with unknown position ({len(df):,} remaining)")

    before = len(df)
    df = df[df["minutes_played"] > 0]
    print(f"  Dropped {before - len(df):,} rows with 0 minutes ({len(df):,} remaining)")

    # Compute season-average roles and age buckets
    print("Computing season-average roles...")
    df = compute_season_roles(df)
    df["age_bucket"] = df["age"].apply(age_bucket)
    df = df.dropna(subset=["age_bucket"])

    # Add death spot context flags
    print("Detecting death spot patterns...")
    df = add_death_spot_context(df)

    # Report pattern counts
    for pattern in ["ds_party_b2b", "ds_altitude_b2b", "ds_cross_country_b2b",
                     "ds_party_to_altitude", "ds_compound"]:
        count = df[pattern].sum()
        print(f"  {pattern}: {count:,} games")
    print(f"  ds_any: {df['ds_any'].sum():,} games")

    # Build death spot effects
    print("Building death spot effects...")
    profiles = build_death_spot_effects(df)
    print(f"  Buckets: {len(profiles)} (after min sample filter)")

    # Write output
    output_path = STATIC_DATA_DIR / "calendars" / "death_spot_effects.py"
    write_effects_file(profiles, "DEATH_SPOT_EFFECTS", output_path)
    print(f"  Written: {output_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
