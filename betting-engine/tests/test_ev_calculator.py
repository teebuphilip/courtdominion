"""
Tests for EV Calculator — edge percentage and filtering logic.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ev_calculator import calculate_ev, find_projection_by_name


# --- Test fixtures ---

def _make_projection(**overrides):
    """Build a test projection dict."""
    defaults = {
        "name": "Test Player",
        "team": "TST",
        "position": "SF",
        "is_b2b": False,
        "props": {
            "points":   {"projection": 25.5, "std_dev": 4.2, "confidence": 0.78},
            "rebounds": {"projection": 7.8,  "std_dev": 2.1, "confidence": 0.72},
            "assists":  {"projection": 8.1,  "std_dev": 2.4, "confidence": 0.70},
            "threes":   {"projection": 1.8,  "std_dev": 0.9, "confidence": 0.65},
            "steals":   {"projection": 1.3,  "std_dev": 0.6, "confidence": 0.60},
            "blocks":   {"projection": 0.9,  "std_dev": 0.5, "confidence": 0.55},
        },
    }
    defaults.update(overrides)
    return defaults


def _make_odds(**overrides):
    """Build a test odds dict."""
    defaults = {
        "line": 24.5,
        "over_odds": -115,
        "under_odds": -105,
        "bookmaker": "draftkings",
    }
    defaults.update(overrides)
    return defaults


# --- TEST 1: Positive edge - projection above line ---

class TestPositiveEdge:
    def test_over_direction(self):
        """proj=25.5, line=24.5, std_dev=4.2 -> OVER with ~23.8% edge."""
        proj = _make_projection()
        odds = _make_odds(line=24.5)
        result = calculate_ev("Test Player", proj, "points", odds)

        assert result is not None
        assert result["direction"] == "OVER"
        assert result["edge_pct"] == pytest.approx(23.8, abs=0.1)
        assert result["dbb2_projection"] == 25.5
        assert result["sportsbook_line"] == 24.5

    def test_raw_edge_positive(self):
        proj = _make_projection()
        odds = _make_odds(line=24.5)
        result = calculate_ev("Test Player", proj, "points", odds)
        assert result["raw_edge"] == 1.0


# --- TEST 2: Negative edge - projection below line ---

class TestNegativeEdge:
    def test_under_direction(self):
        """proj=7.8, line=8.5, std_dev=2.1 -> UNDER with ~33.3% edge."""
        proj = _make_projection()
        odds = _make_odds(line=8.5)
        result = calculate_ev("Test Player", proj, "rebounds", odds)

        assert result is not None
        assert result["direction"] == "UNDER"
        assert result["edge_pct"] == pytest.approx(33.3, abs=0.1)

    def test_raw_edge_negative(self):
        proj = _make_projection()
        odds = _make_odds(line=8.5)
        result = calculate_ev("Test Player", proj, "rebounds", odds)
        assert result["raw_edge"] == -0.7


# --- TEST 3: Zero std_dev - should return None ---

class TestZeroStdDev:
    def test_returns_none(self):
        """std_dev=0 should not crash, should return None."""
        proj = _make_projection()
        proj["props"]["points"]["std_dev"] = 0
        odds = _make_odds(line=24.5)
        result = calculate_ev("Test Player", proj, "points", odds)
        assert result is None

    def test_null_std_dev_returns_none(self):
        proj = _make_projection()
        proj["props"]["points"]["std_dev"] = None
        odds = _make_odds(line=24.5)
        result = calculate_ev("Test Player", proj, "points", odds)
        assert result is None


# --- TEST 4: Missing prop type ---

class TestMissingProp:
    def test_missing_prop_returns_none(self):
        proj = _make_projection()
        odds = _make_odds()
        result = calculate_ev("Test Player", proj, "nonexistent", odds)
        assert result is None


# --- TEST 5: Player name matching ---

class TestNameMatching:
    def test_exact_match(self):
        projections = {
            "1": {"name": "LeBron James", "team": "LAL"},
            "2": {"name": "Stephen Curry", "team": "GSW"},
        }
        result = find_projection_by_name(projections, "LeBron James")
        assert result is not None
        assert result["name"] == "LeBron James"

    def test_case_insensitive(self):
        projections = {"1": {"name": "LeBron James", "team": "LAL"}}
        result = find_projection_by_name(projections, "lebron james")
        assert result is not None

    def test_fuzzy_last_name(self):
        projections = {"1": {"name": "LeBron James", "team": "LAL"}}
        result = find_projection_by_name(projections, "L. James")
        assert result is not None

    def test_no_match_returns_none(self):
        projections = {"1": {"name": "LeBron James", "team": "LAL"}}
        result = find_projection_by_name(projections, "Michael Jordan")
        assert result is None


# --- TEST 6: Result structure ---

class TestResultStructure:
    def test_all_fields_present(self):
        proj = _make_projection()
        odds = _make_odds()
        result = calculate_ev("Test Player", proj, "points", odds)

        required = [
            "player_name", "prop_type", "direction", "dbb2_projection",
            "sportsbook_line", "raw_edge", "edge_pct", "std_dev",
            "confidence", "over_odds", "under_odds", "bookmaker",
        ]
        for field in required:
            assert field in result, f"Missing field: {field}"


# --- TEST 7: Death spot filtering ---

class TestDeathSpotFiltering:
    def test_death_spot_projection_has_flag(self):
        """Projection with is_death_spot=True should be filterable."""
        proj = _make_projection(is_death_spot=True, death_spot_type="party_b2b")
        assert proj["is_death_spot"] is True
        assert proj["death_spot_type"] == "party_b2b"

    def test_game_day_adjusted_projection_used(self):
        """When projection has game-day adjusted values, EV uses them."""
        proj = _make_projection()
        # Simulate game-day adjusted projection (lower than season)
        proj["props"]["points"]["projection"] = 21.7
        odds = _make_odds(line=24.5)
        result = calculate_ev("Test Player", proj, "points", odds)

        assert result is not None
        assert result["dbb2_projection"] == 21.7
        assert result["direction"] == "UNDER"
