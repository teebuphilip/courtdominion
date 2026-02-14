"""
Matchup adjustment multiplier tests.

Validates the generated MATCHUP_ADJUSTMENTS dictionary.
"""

import pytest


EXPECTED_FIELDS = {
    "points_multiplier",
    "rebounds_multiplier",
    "assists_multiplier",
    "steals_multiplier",
    "blocks_multiplier",
    "three_pm_multiplier",
    "fantasy_pts_multiplier",
    "sample_size",
}

VALID_OPP_BUCKETS = {"Elite", "Above Avg", "Average", "Below Avg", "Poor"}
VALID_LOCATIONS = {"HOME", "ROAD"}


class TestEliteDefenseReducesScoring:
    """Elite defenses should reduce scoring in majority of buckets."""

    def test_elite_points_below_one(self, matchup_adjustments):
        elite_count = 0
        below_one = 0
        for key, entry in matchup_adjustments.items():
            if key[3] == "Elite":
                elite_count += 1
                if entry["points_multiplier"] is not None and entry["points_multiplier"] < 1.0:
                    below_one += 1

        assert elite_count >= 10, f"Only {elite_count} Elite buckets"
        assert below_one > elite_count * 0.6, (
            f"Only {below_one}/{elite_count} Elite buckets have points < 1.0"
        )


class TestPoorDefenseBoostsScoring:
    """Poor defenses should boost scoring in majority of buckets."""

    def test_poor_points_above_one(self, matchup_adjustments):
        poor_count = 0
        above_one = 0
        for key, entry in matchup_adjustments.items():
            if key[3] == "Poor":
                poor_count += 1
                if entry["points_multiplier"] is not None and entry["points_multiplier"] > 1.0:
                    above_one += 1

        assert poor_count >= 10, f"Only {poor_count} Poor buckets"
        assert above_one > poor_count * 0.6, (
            f"Only {above_one}/{poor_count} Poor buckets have points > 1.0"
        )


class TestMultiplierRanges:
    """All multipliers should be in reasonable bounds."""

    def test_core_multipliers_in_range(self, matchup_adjustments):
        """Core stat multipliers for non-scrub roles in [0.60, 1.50]."""
        core_fields = [
            "points_multiplier", "rebounds_multiplier",
            "assists_multiplier", "fantasy_pts_multiplier",
        ]
        for key, entry in matchup_adjustments.items():
            if key[2] == "Scrub":
                continue  # Scrubs have tiny baselines → wild multipliers
            for field in core_fields:
                val = entry.get(field)
                if val is not None:
                    assert 0.60 <= val <= 1.50, (
                        f"{key}: {field} = {val}"
                    )

    def test_fantasy_pts_multiplier_all_roles(self, matchup_adjustments):
        """Fantasy pts multiplier (composite) should be reasonable even for scrubs."""
        for key, entry in matchup_adjustments.items():
            val = entry.get("fantasy_pts_multiplier")
            if val is not None:
                assert 0.30 <= val <= 2.50, (
                    f"{key}: fantasy_pts_multiplier = {val}"
                )


class TestHomeVsRoad:
    """For same matchup quality, home should generally score better than road."""

    def test_home_advantage(self, matchup_adjustments):
        comparisons = 0
        home_wins = 0
        for key, entry in matchup_adjustments.items():
            bucket, pos, role, opp, location = key
            if location == "HOME":
                road_key = (bucket, pos, role, opp, "ROAD")
                if road_key in matchup_adjustments:
                    home_pts = entry["fantasy_pts_multiplier"]
                    road_pts = matchup_adjustments[road_key]["fantasy_pts_multiplier"]
                    if home_pts is not None and road_pts is not None:
                        comparisons += 1
                        if home_pts >= road_pts:
                            home_wins += 1

        assert comparisons >= 20, f"Only {comparisons} home-road pairs"
        assert home_wins > comparisons * 0.5, (
            f"Home beat road in only {home_wins}/{comparisons} pairs"
        )


class TestAllFieldsPresent:
    """Every entry should have all expected fields."""

    def test_fields_present(self, matchup_adjustments):
        for key, entry in matchup_adjustments.items():
            missing = EXPECTED_FIELDS - set(entry.keys())
            assert not missing, f"{key} missing fields: {missing}"


class TestValidKeys:
    """All keys should have valid components."""

    def test_valid_key_components(self, matchup_adjustments):
        for key in matchup_adjustments:
            bucket, pos, role, opp, location = key
            assert bucket in ("Young", "Prime", "Veteran"), (
                f"Invalid age bucket: {bucket}"
            )
            assert pos in ("G", "F", "C"), f"Invalid position: {pos}"
            assert role in ("Starter", "Rotation", "Bench", "Scrub"), (
                f"Invalid role: {role}"
            )
            assert opp in VALID_OPP_BUCKETS, f"Invalid opponent bucket: {opp}"
            assert location in VALID_LOCATIONS, f"Invalid location: {location}"


class TestBucketCount:
    """Should have a meaningful number of buckets."""

    def test_bucket_count(self, matchup_adjustments):
        """3 age x 3 pos x 4 role x 5 opp x 2 loc = 360 max."""
        assert len(matchup_adjustments) >= 100


class TestSampleSizes:
    """Sample sizes should meet minimum threshold."""

    def test_sample_sizes_above_threshold(self, matchup_adjustments):
        for key, entry in matchup_adjustments.items():
            assert entry["sample_size"] >= 30, (
                f"{key}: sample_size = {entry['sample_size']}"
            )
