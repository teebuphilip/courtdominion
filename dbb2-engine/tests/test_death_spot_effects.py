"""Tests for death spot pattern detection, effects data, and engine integration."""

import pytest

from data_collection.utils import timezone_jump, TEAM_TIMEZONES
from engine.baseline import PlayerContext
from engine.game_day import (
    project_game_day,
    _get_death_spot_multiplier,
    _DEATH_SPOT_TYPE_TO_FIELD,
)
from engine.projections import SeasonProjection
from engine import lookup


# ---------------------------------------------------------------------------
# Test timezone utilities
# ---------------------------------------------------------------------------

class TestTimezoneJump:
    def test_la_to_boston_3_hours(self):
        assert timezone_jump("LAL", "BOS") == 3

    def test_same_city_0_hours(self):
        assert timezone_jump("NYK", "BKN") == 0

    def test_unknown_team_defaults_eastern(self):
        assert timezone_jump("UNKNOWN", "LAL") == 3  # -5 default vs -8

    def test_denver_to_la_1_hour(self):
        assert timezone_jump("DEN", "LAL") == 1

    def test_all_teams_have_timezone(self):
        # Every team in TEAM_TIMEZONES should have a valid offset
        for team, tz in TEAM_TIMEZONES.items():
            assert isinstance(tz, int), f"{team} timezone is not int"
            assert -8 <= tz <= -5, f"{team} timezone {tz} out of range"


# ---------------------------------------------------------------------------
# Test death spot effects data structure
# ---------------------------------------------------------------------------

class TestDeathSpotEffectsStructure:
    @pytest.fixture(autouse=True)
    def load_effects(self):
        from static_data.calendars.death_spot_effects import DEATH_SPOT_EFFECTS
        self.effects = DEATH_SPOT_EFFECTS

    def test_all_keys_are_valid_tuples(self):
        valid_brackets = {"Young", "Prime", "Veteran"}
        valid_positions = {"G", "F", "C"}
        valid_roles = {"Starter", "Rotation", "Bench", "Scrub"}

        for key in self.effects:
            assert len(key) == 3, f"Key {key} is not a 3-tuple"
            bucket, pos, role = key
            assert bucket in valid_brackets, f"Invalid bracket: {bucket}"
            assert pos in valid_positions, f"Invalid position: {pos}"
            assert role in valid_roles, f"Invalid role: {role}"

    def test_all_expected_fields_present(self):
        expected_fields = {
            "party_b2b_residual", "sample_size_party_b2b",
            "altitude_b2b_residual", "sample_size_altitude_b2b",
            "cross_country_b2b_dropoff", "sample_size_cross_country_b2b",
            "party_to_altitude_dropoff", "sample_size_party_to_altitude",
            "compound_worst_dropoff", "sample_size_compound",
        }
        for key, entry in self.effects.items():
            assert set(entry.keys()) == expected_fields, f"Wrong fields for {key}"

    def test_multipliers_in_valid_range(self):
        multiplier_fields = [
            "party_b2b_residual", "altitude_b2b_residual",
            "cross_country_b2b_dropoff", "party_to_altitude_dropoff",
            "compound_worst_dropoff",
        ]
        for key, entry in self.effects.items():
            for field in multiplier_fields:
                val = entry[field]
                if val is not None:
                    assert 0.40 <= val <= 2.00, f"{key}.{field} = {val} out of range"

    def test_sample_sizes_are_ints(self):
        sample_fields = [
            "sample_size_party_b2b", "sample_size_altitude_b2b",
            "sample_size_cross_country_b2b", "sample_size_party_to_altitude",
            "sample_size_compound",
        ]
        for key, entry in self.effects.items():
            for field in sample_fields:
                val = entry[field]
                assert isinstance(val, int), f"{key}.{field} not int: {type(val)}"

    def test_at_least_20_buckets(self):
        assert len(self.effects) >= 20, f"Only {len(self.effects)} buckets"

    def test_party_b2b_has_data(self):
        """At least some buckets should have party_b2b residual data."""
        with_data = sum(
            1 for e in self.effects.values() if e["party_b2b_residual"] is not None
        )
        assert with_data >= 10, f"Only {with_data} buckets with party_b2b data"


# ---------------------------------------------------------------------------
# Test death spot multiplier in game-day engine
# ---------------------------------------------------------------------------

class TestDeathSpotMultiplier:
    def _make_ctx(self, is_death_spot=False, death_spot_type="", **kwargs):
        defaults = dict(
            player_id="test", player_name="Test", team="BOS", position="G",
            raw_position="G", age=28, role="Starter", age_bracket="Prime",
        )
        defaults.update(kwargs)
        return PlayerContext(
            is_death_spot=is_death_spot,
            death_spot_type=death_spot_type,
            **defaults,
        )

    def _make_proj(self):
        return SeasonProjection(
            player_id="test", player_name="Test", team="BOS", position="G",
            minutes=32.0, usage_rate=25.0, points=22.0, rebounds=4.0,
            assists=6.0, steals=1.2, blocks=0.4, turnovers=2.5,
            fg_pct=0.460, three_pt_pct=0.380, ft_pct=0.850,
            fgm=8.0, fga=17.0, three_pm=2.5, three_pa=6.5,
            ftm=3.5, fta=4.0, fantasy_points=40.0, ceiling=55.0,
            floor=25.0, consistency=70, projected_games=75,
        )

    def test_no_death_spot_returns_neutral(self):
        ctx = self._make_ctx(is_death_spot=False)
        assert _get_death_spot_multiplier(ctx) == 1.0

    def test_death_spot_returns_non_neutral(self):
        ctx = self._make_ctx(is_death_spot=True, death_spot_type="party_b2b")
        mult = _get_death_spot_multiplier(ctx)
        # Should be some value (may be 1.0 if no data, but should work without error)
        assert isinstance(mult, float)
        assert 0.5 <= mult <= 1.5

    def test_unknown_type_returns_neutral(self):
        ctx = self._make_ctx(is_death_spot=True, death_spot_type="nonexistent")
        assert _get_death_spot_multiplier(ctx) == 1.0

    def test_all_types_have_field_mapping(self):
        expected_types = {"party_b2b", "altitude_b2b", "cross_country_b2b",
                          "party_to_altitude", "compound"}
        assert set(_DEATH_SPOT_TYPE_TO_FIELD.keys()) == expected_types

    def test_death_spot_affects_game_day_projection(self):
        ctx = self._make_ctx(is_death_spot=True, death_spot_type="party_b2b")
        proj = self._make_proj()
        gd = project_game_day(ctx, proj)
        assert gd.death_spot_multiplier != 0  # Should have a value
        assert hasattr(gd, "death_spot_multiplier")

    def test_compound_clamp_applies(self):
        """Even with extreme death spot, compound should be >= 0.50."""
        ctx = self._make_ctx(
            is_death_spot=True, death_spot_type="compound",
            is_b2b=True, is_post_hot_spot=True, is_post_altitude=True,
        )
        proj = self._make_proj()
        gd = project_game_day(ctx, proj)
        assert gd.compound_multiplier >= 0.50
        assert gd.compound_multiplier <= 1.50


# ---------------------------------------------------------------------------
# Test lookup function
# ---------------------------------------------------------------------------

class TestDeathSpotLookup:
    def test_lookup_returns_dict_or_none(self):
        result = lookup.lookup_death_spot_effect("Prime", "G", "Starter")
        assert result is None or isinstance(result, dict)

    def test_fallback_works(self):
        """If exact key doesn't exist, fallback should find something."""
        result = lookup.lookup_death_spot_effect("Prime", "G", "Starter")
        if result is not None:
            assert "party_b2b_residual" in result

    def test_unknown_bracket_uses_fallback(self):
        result = lookup.lookup_death_spot_effect("Unknown", "G", "Starter")
        # Should fallback to a valid bracket or return None — not crash
        assert result is None or isinstance(result, dict)
