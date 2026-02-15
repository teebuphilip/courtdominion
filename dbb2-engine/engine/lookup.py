"""
Centralized static-data access with graceful fallback.

All 12 static data dictionaries are loaded at module level (one-time cost).
Lookup functions try the exact key first, then progressively broader keys.
No lookup can crash the pipeline — every function returns either a valid
dict or None (callers use neutral defaults).
"""

from typing import Optional, Dict, Tuple

# --------------------------------------------------------------------------
# Load all static data at module level
# --------------------------------------------------------------------------

from static_data.profiles import (
    AGE_PROFILES_OVERALL,
    AGE_PROFILES_MODERN,
    AGE_PROFILES_PRE_MODERN,
    CEILING_PROFILES,
)
from static_data.calendars import SCHEDULE_EFFECTS, CITY_EFFECTS, DEATH_SPOT_EFFECTS
from static_data.durability import DURABILITY_PROFILES
from static_data.usage import USAGE_PROFILES
from static_data.pricing import POSITION_SCARCITY, ZSCORE_BASELINES, SGP_WEIGHTS
from static_data.matchups import MATCHUP_ADJUSTMENTS


# --------------------------------------------------------------------------
# Era selector
# --------------------------------------------------------------------------

_ERA_MAP = {
    "overall": AGE_PROFILES_OVERALL,
    "modern": AGE_PROFILES_MODERN,
    "pre_modern": AGE_PROFILES_PRE_MODERN,
}


# --------------------------------------------------------------------------
# Role fallback order (prefer closer roles)
# --------------------------------------------------------------------------

ROLE_FALLBACK = ["Starter", "Rotation", "Bench", "Scrub"]

# Bracket fallback order
BRACKET_FALLBACK = ["Prime", "Young", "Veteran"]


# --------------------------------------------------------------------------
# Generic fallback helpers
# --------------------------------------------------------------------------

def _fallback_age_keyed(
    data: dict,
    age: int,
    pos: str,
    role: str,
) -> Optional[dict]:
    """
    Fallback chain for dicts keyed by (age:int, pos:str, role:str).

    1. Exact match
    2. Adjacent ages ±1, ±2 same pos/role
    3. Same age/pos, try other roles
    4. Wider age ±5, any role
    5. None
    """
    # 1. Exact
    key = (age, pos, role)
    if key in data:
        return data[key]

    # 2. Adjacent ages, same pos/role
    for offset in (-1, 1, -2, 2):
        neighbor = (age + offset, pos, role)
        if neighbor in data:
            return data[neighbor]

    # 3. Same age/pos, different role
    for alt_role in ROLE_FALLBACK:
        if alt_role != role:
            alt_key = (age, pos, alt_role)
            if alt_key in data:
                return data[alt_key]

    # 4. Wider age search ±5, any role
    for age_off in range(-5, 6):
        if age_off in (0, -1, 1, -2, 2):
            continue  # already tried
        for alt_role in ROLE_FALLBACK:
            wide_key = (age + age_off, pos, alt_role)
            if wide_key in data:
                return data[wide_key]

    return None


def _fallback_bracket_keyed(
    data: dict,
    age_bracket: str,
    pos: str,
    role: str,
) -> Optional[dict]:
    """
    Fallback chain for dicts keyed by (age_bracket:str, pos:str, role:str).

    1. Exact match
    2. Same bracket/pos, try other roles
    3. Try "Prime" bracket (largest sample), same pos, any role
    4. None
    """
    # 1. Exact
    key = (age_bracket, pos, role)
    if key in data:
        return data[key]

    # 2. Same bracket/pos, different role
    for alt_role in ROLE_FALLBACK:
        if alt_role != role:
            alt_key = (age_bracket, pos, alt_role)
            if alt_key in data:
                return data[alt_key]

    # 3. Try other brackets, same pos
    for bracket in BRACKET_FALLBACK:
        if bracket == age_bracket:
            continue
        for alt_role in [role] + ROLE_FALLBACK:
            fb_key = (bracket, pos, alt_role)
            if fb_key in data:
                return data[fb_key]

    return None


# --------------------------------------------------------------------------
# Typed lookup functions
# --------------------------------------------------------------------------

def lookup_age_profile(
    age: int,
    pos: str,
    role: str,
    era: str = "overall",
) -> Optional[dict]:
    """Look up age profile with fallback chain. Falls through eras if needed."""
    data = _ERA_MAP.get(era, AGE_PROFILES_OVERALL)
    result = _fallback_age_keyed(data, age, pos, role)

    # If non-overall era missed, try overall as final fallback
    if result is None and era != "overall":
        result = _fallback_age_keyed(AGE_PROFILES_OVERALL, age, pos, role)

    return result


def lookup_ceiling_profile(
    age: int,
    pos: str,
    role: str,
) -> Optional[dict]:
    """Look up ceiling profile with age-keyed fallback."""
    return _fallback_age_keyed(CEILING_PROFILES, age, pos, role)


def lookup_durability(
    age: int,
    pos: str,
    role: str,
) -> Optional[dict]:
    """Look up durability profile with age-keyed fallback."""
    return _fallback_age_keyed(DURABILITY_PROFILES, age, pos, role)


def lookup_usage(
    age: int,
    pos: str,
    role: str,
) -> Optional[dict]:
    """Look up usage profile with age-keyed fallback."""
    return _fallback_age_keyed(USAGE_PROFILES, age, pos, role)


def lookup_schedule_effect(
    age_bracket: str,
    pos: str,
    role: str,
) -> Optional[dict]:
    """Look up schedule effect with bracket-keyed fallback."""
    return _fallback_bracket_keyed(SCHEDULE_EFFECTS, age_bracket, pos, role)


def lookup_city_effect(
    age_bracket: str,
    pos: str,
    role: str,
) -> Optional[dict]:
    """Look up city effect with bracket-keyed fallback."""
    return _fallback_bracket_keyed(CITY_EFFECTS, age_bracket, pos, role)


def lookup_death_spot_effect(
    age_bracket: str,
    pos: str,
    role: str,
) -> Optional[dict]:
    """Look up death spot compound effect with bracket-keyed fallback."""
    return _fallback_bracket_keyed(DEATH_SPOT_EFFECTS, age_bracket, pos, role)


def lookup_matchup(
    age_bracket: str,
    pos: str,
    role: str,
    defense_tier: str,
    location: str,
) -> Optional[dict]:
    """
    Look up matchup adjustment with 5-tuple key and fallback.

    1. Exact 5-tuple
    2. Same bracket/pos/role/location, try "Average" defense
    3. Same bracket/pos/role, try "Average" defense + both locations
    4. Return None (caller uses neutral 1.0 multipliers)
    """
    # 1. Exact
    key = (age_bracket, pos, role, defense_tier, location)
    if key in MATCHUP_ADJUSTMENTS:
        return MATCHUP_ADJUSTMENTS[key]

    # 2. Fallback to Average defense, same location
    avg_key = (age_bracket, pos, role, "Average", location)
    if avg_key in MATCHUP_ADJUSTMENTS:
        return MATCHUP_ADJUSTMENTS[avg_key]

    # 3. Try Average defense, either location
    for loc in ("HOME", "ROAD"):
        fb_key = (age_bracket, pos, role, "Average", loc)
        if fb_key in MATCHUP_ADJUSTMENTS:
            return MATCHUP_ADJUSTMENTS[fb_key]

    # 4. Try other roles with Average defense
    for alt_role in ROLE_FALLBACK:
        if alt_role != role:
            for loc in (location, "HOME", "ROAD"):
                fb_key = (age_bracket, pos, alt_role, "Average", loc)
                if fb_key in MATCHUP_ADJUSTMENTS:
                    return MATCHUP_ADJUSTMENTS[fb_key]

    return None


# --------------------------------------------------------------------------
# Neutral matchup multipliers (used when lookup returns None)
# --------------------------------------------------------------------------

NEUTRAL_MATCHUP = {
    "points_multiplier": 1.0,
    "rebounds_multiplier": 1.0,
    "assists_multiplier": 1.0,
    "steals_multiplier": 1.0,
    "blocks_multiplier": 1.0,
    "three_pm_multiplier": 1.0,
    "fantasy_pts_multiplier": 1.0,
    "sample_size": 0,
}


# --------------------------------------------------------------------------
# String-keyed lookups (always succeed)
# --------------------------------------------------------------------------

def lookup_zscore_baseline(pos: str) -> dict:
    """Position-specific z-score baseline, fallback to 'ALL'."""
    if pos in ZSCORE_BASELINES:
        return ZSCORE_BASELINES[pos]
    return ZSCORE_BASELINES["ALL"]


def lookup_position_scarcity(pos: str) -> dict:
    """Position scarcity data. Returns neutral if unknown position."""
    if pos in POSITION_SCARCITY:
        return POSITION_SCARCITY[pos]
    return {"scarcity_multiplier": 1.0}


def get_sgp_weights() -> dict:
    """Return the SGP_WEIGHTS dict directly."""
    return SGP_WEIGHTS
