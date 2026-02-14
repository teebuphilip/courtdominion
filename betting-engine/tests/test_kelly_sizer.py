"""
Tests for Kelly Sizer — fractional Kelly bet sizing.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.kelly_sizer import apply_kelly, american_to_decimal, get_american_odds


# Default settings matching config/settings.json
DEFAULT_SETTINGS = {
    "kelly": {
        "fraction": 0.25,
        "max_units": 3.0,
        "min_units": 0.5,
        "bankroll": 1000,
    },
    "ev_thresholds": {
        "min_edge_pct": 5.0,
        "min_confidence": 0.60,
        "max_bets_per_day": 10,
    },
}


def _make_bet(**overrides):
    """Build a test bet dict (output of EV calculator)."""
    defaults = {
        "player_name": "Test Player",
        "prop_type": "points",
        "direction": "OVER",
        "dbb2_projection": 25.5,
        "sportsbook_line": 24.5,
        "raw_edge": 1.0,
        "edge_pct": 20.0,
        "std_dev": 4.2,
        "confidence": 0.75,
        "over_odds": -110,
        "under_odds": -110,
        "bookmaker": "draftkings",
    }
    defaults.update(overrides)
    return defaults


# --- TEST 1: Normal bet produces valid units ---

class TestNormalBet:
    def test_units_in_range(self):
        """edge_pct=20.0, confidence=0.75, over_odds=-110 -> 0.5 <= units <= 3.0."""
        bet = _make_bet(edge_pct=20.0, confidence=0.75, over_odds=-110)
        result = apply_kelly(bet, DEFAULT_SETTINGS)
        assert 0.5 <= result["units"] <= 3.0

    def test_has_kelly_fields(self):
        bet = _make_bet()
        result = apply_kelly(bet, DEFAULT_SETTINGS)
        assert "units" in result
        assert "decimal_odds" in result
        assert "kelly_raw" in result
        assert "kelly_fractional" in result


# --- TEST 2: Max units cap ---

class TestMaxCap:
    def test_extreme_edge_never_exceeds_max(self):
        """No bet should ever exceed max_units regardless of edge."""
        bet = _make_bet(edge_pct=90.0, confidence=0.99, over_odds=500)
        result = apply_kelly(bet, DEFAULT_SETTINGS)
        assert result["units"] <= DEFAULT_SETTINGS["kelly"]["max_units"]

    def test_extreme_edge_produces_high_units(self):
        """Very favorable bet should produce high (but capped) units."""
        bet = _make_bet(edge_pct=90.0, confidence=0.99, over_odds=500)
        result = apply_kelly(bet, DEFAULT_SETTINGS)
        # WHY: p capped at 0.85, so max practical units with 25% Kelly ~2.0u
        assert result["units"] >= 1.5


# --- TEST 3: Min units floor ---

class TestMinFloor:
    def test_small_edge_floored(self):
        """edge_pct=5.1, confidence=0.61, over_odds=-200 -> units == 0.5 (floored)."""
        bet = _make_bet(edge_pct=5.1, confidence=0.61, over_odds=-200)
        result = apply_kelly(bet, DEFAULT_SETTINGS)
        assert result["units"] == 0.5


# --- TEST 4: Units rounded to 0.5 ---

class TestRounding:
    def test_units_rounded_to_half(self):
        """Any valid bet should have units as a multiple of 0.5."""
        bet = _make_bet(edge_pct=30.0, confidence=0.80, over_odds=-115)
        result = apply_kelly(bet, DEFAULT_SETTINGS)
        assert result["units"] % 0.5 == 0


# --- TEST 5: American to decimal conversion ---

class TestOddsConversion:
    def test_positive_american(self):
        """'+150' = 2.50 decimal."""
        assert american_to_decimal(150) == pytest.approx(2.5)

    def test_negative_american(self):
        """'-110' = 1.909 decimal."""
        assert american_to_decimal(-110) == pytest.approx(1.909, abs=0.001)

    def test_even_money(self):
        """'+100' = 2.00 decimal."""
        assert american_to_decimal(100) == pytest.approx(2.0)

    def test_heavy_favorite(self):
        """'-200' = 1.50 decimal."""
        assert american_to_decimal(-200) == pytest.approx(1.5)


# --- TEST 6: Missing odds handling ---

class TestMissingOdds:
    def test_missing_odds_returns_min(self):
        bet = _make_bet(over_odds=None, under_odds=None)
        result = apply_kelly(bet, DEFAULT_SETTINGS)
        assert result["units"] == DEFAULT_SETTINGS["kelly"]["min_units"]
        assert result.get("kelly_note") == "missing_odds"


# --- TEST 7: Direction selection ---

class TestDirectionOdds:
    def test_over_uses_over_odds(self):
        bet = _make_bet(direction="OVER", over_odds=-110, under_odds=-130)
        assert get_american_odds(bet) == -110

    def test_under_uses_under_odds(self):
        bet = _make_bet(direction="UNDER", over_odds=-110, under_odds=-130)
        assert get_american_odds(bet) == -130
