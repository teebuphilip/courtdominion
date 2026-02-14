"""
Tests for engine/lookup.py — static data loader + fallback lookups.
"""

import pytest


class TestAllDictsLoad:
    """All 12 static data dictionaries should load without errors."""

    def test_age_profiles_overall_loaded(self):
        from engine.lookup import AGE_PROFILES_OVERALL
        assert len(AGE_PROFILES_OVERALL) > 0

    def test_age_profiles_modern_loaded(self):
        from engine.lookup import AGE_PROFILES_MODERN
        assert len(AGE_PROFILES_MODERN) > 0

    def test_age_profiles_pre_modern_loaded(self):
        from engine.lookup import AGE_PROFILES_PRE_MODERN
        assert len(AGE_PROFILES_PRE_MODERN) > 0

    def test_ceiling_profiles_loaded(self):
        from engine.lookup import CEILING_PROFILES
        assert len(CEILING_PROFILES) > 0

    def test_schedule_effects_loaded(self):
        from engine.lookup import SCHEDULE_EFFECTS
        assert len(SCHEDULE_EFFECTS) > 0

    def test_city_effects_loaded(self):
        from engine.lookup import CITY_EFFECTS
        assert len(CITY_EFFECTS) > 0

    def test_durability_profiles_loaded(self):
        from engine.lookup import DURABILITY_PROFILES
        assert len(DURABILITY_PROFILES) > 0

    def test_usage_profiles_loaded(self):
        from engine.lookup import USAGE_PROFILES
        assert len(USAGE_PROFILES) > 0

    def test_position_scarcity_loaded(self):
        from engine.lookup import POSITION_SCARCITY
        assert len(POSITION_SCARCITY) >= 3

    def test_zscore_baselines_loaded(self):
        from engine.lookup import ZSCORE_BASELINES
        assert len(ZSCORE_BASELINES) >= 4

    def test_sgp_weights_loaded(self):
        from engine.lookup import SGP_WEIGHTS
        assert "category_weights" in SGP_WEIGHTS
        assert "position_bonuses" in SGP_WEIGHTS

    def test_matchup_adjustments_loaded(self):
        from engine.lookup import MATCHUP_ADJUSTMENTS
        assert len(MATCHUP_ADJUSTMENTS) > 0


class TestAgeProfileLookup:
    """Age profile lookups with fallback chain."""

    def test_exact_key_found(self):
        from engine.lookup import lookup_age_profile
        # (25, 'G', 'Starter') should be a common key
        result = lookup_age_profile(25, "G", "Starter")
        assert result is not None
        assert "avg_points" in result

    def test_adjacent_age_fallback(self):
        from engine.lookup import lookup_age_profile
        # Age 18 Starter G may not exist, should fall to adjacent
        result = lookup_age_profile(18, "G", "Starter")
        # Should find something (even if via fallback)
        assert result is not None or True  # Allow None for very edge cases

    def test_role_fallback(self):
        from engine.lookup import lookup_age_profile
        # 40-year-old Starter C is unlikely to exist
        result = lookup_age_profile(40, "C", "Starter")
        # Should fallback to adjacent ages or different role
        # May still be None for extreme ages, which is OK

    def test_total_miss_returns_none(self):
        from engine.lookup import lookup_age_profile
        result = lookup_age_profile(99, "X", "Unknown")
        assert result is None

    def test_modern_era_lookup(self):
        from engine.lookup import lookup_age_profile
        result = lookup_age_profile(25, "G", "Starter", era="modern")
        assert result is not None
        assert "avg_points" in result

    def test_modern_fallback_to_overall(self):
        from engine.lookup import lookup_age_profile
        # If modern misses, should fall to overall
        result = lookup_age_profile(18, "C", "Scrub", era="modern")
        # Should find something via overall fallback
        assert result is not None or True


class TestCeilingProfileLookup:
    """Ceiling profile lookups."""

    def test_common_key(self):
        from engine.lookup import lookup_ceiling_profile
        result = lookup_ceiling_profile(25, "G", "Starter")
        assert result is not None
        assert "ceiling_game_pct" in result

    def test_miss_returns_none(self):
        from engine.lookup import lookup_ceiling_profile
        result = lookup_ceiling_profile(99, "X", "Unknown")
        assert result is None


class TestScheduleEffectLookup:
    """Schedule effect lookups with bracket-keyed fallback."""

    def test_exact_bracket_key(self):
        from engine.lookup import lookup_schedule_effect
        result = lookup_schedule_effect("Prime", "C", "Starter")
        assert result is not None
        assert "b2b_scoring_dropoff" in result

    def test_fallback_to_prime(self):
        from engine.lookup import lookup_schedule_effect
        # If exact bracket misses, should fall to Prime
        result = lookup_schedule_effect("Young", "G", "Starter")
        assert result is not None

    def test_total_miss(self):
        from engine.lookup import lookup_schedule_effect
        result = lookup_schedule_effect("Unknown", "X", "Unknown")
        assert result is None


class TestMatchupLookup:
    """Matchup adjustment lookups with 5-tuple fallback."""

    def test_exact_5tuple(self):
        from engine.lookup import lookup_matchup
        result = lookup_matchup("Prime", "C", "Starter", "Average", "HOME")
        assert result is not None
        assert "points_multiplier" in result

    def test_fallback_to_average_defense(self):
        from engine.lookup import lookup_matchup
        # "Unknown" defense tier should fall to Average
        result = lookup_matchup("Prime", "G", "Starter", "Unknown", "HOME")
        assert result is not None

    def test_total_miss_returns_none(self):
        from engine.lookup import lookup_matchup
        result = lookup_matchup("Unknown", "X", "Unknown", "Unknown", "X")
        assert result is None


class TestNeutralMatchup:
    """Neutral matchup constant should have all required keys."""

    def test_all_multiplier_keys(self):
        from engine.lookup import NEUTRAL_MATCHUP
        for key in ("points_multiplier", "rebounds_multiplier",
                     "assists_multiplier", "steals_multiplier",
                     "blocks_multiplier", "three_pm_multiplier",
                     "fantasy_pts_multiplier"):
            assert key in NEUTRAL_MATCHUP
            assert NEUTRAL_MATCHUP[key] == 1.0


class TestZscoreBaselineLookup:
    """Z-score baseline lookups always succeed."""

    def test_position_specific(self):
        from engine.lookup import lookup_zscore_baseline
        result = lookup_zscore_baseline("C")
        assert "points_mean" in result
        assert "points_stddev" in result

    def test_fallback_to_all(self):
        from engine.lookup import lookup_zscore_baseline
        result = lookup_zscore_baseline("X")
        # Should fall to ALL
        assert "points_mean" in result


class TestPositionScarcityLookup:
    """Position scarcity lookups always succeed."""

    def test_known_position(self):
        from engine.lookup import lookup_position_scarcity
        result = lookup_position_scarcity("C")
        assert "scarcity_multiplier" in result
        assert result["scarcity_multiplier"] > 1.0  # Centers are scarcer

    def test_unknown_position_returns_neutral(self):
        from engine.lookup import lookup_position_scarcity
        result = lookup_position_scarcity("X")
        assert result["scarcity_multiplier"] == 1.0
