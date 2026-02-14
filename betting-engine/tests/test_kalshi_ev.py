"""
Tests for Kalshi EV calculator — probability-based EV, normal CDF, Kelly sizing,
and market title parsing.
"""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.kalshi_ev_calculator import (
    normal_cdf_upper_tail,
    calculate_kalshi_ev,
    calculate_kalshi_kelly,
)
from src.kalshi_ingestion import parse_market_title


def _sample_settings():
    return {
        "ev_thresholds": {"min_edge_pct": 5.0, "min_confidence": 0.60},
        "kelly": {"fraction": 0.25, "max_units": 3.0, "min_units": 0.5, "bankroll": 5000},
        "kalshi": {"min_edge_pct": 5.0, "min_yes_price": 0.10, "max_yes_price": 0.90},
        "excluded": {"skip_b2b": True},
    }


def _sample_projection(**overrides):
    defaults = {
        "name": "LeBron James",
        "team": "LAL",
        "position": "SF",
        "is_b2b": False,
        "props": {
            "points": {"projection": 27.2, "std_dev": 4.2, "confidence": 0.78},
            "rebounds": {"projection": 7.8, "std_dev": 2.1, "confidence": 0.72},
            "assists": {"projection": 8.1, "std_dev": 2.4, "confidence": 0.70},
            "threes": {"projection": 1.8, "std_dev": 0.9, "confidence": 0.65},
        },
    }
    defaults.update(overrides)
    return defaults


class TestNormalCDF:
    """normal_cdf_upper_tail: P(X >= threshold) for normal distribution."""

    def test_projection_above_line(self):
        """mean=27.2, threshold=25 → P(X >= 25) should be ~0.70."""
        prob = normal_cdf_upper_tail(mean=27.2, std_dev=4.2, threshold=25.0)
        assert 0.60 <= prob <= 0.75

    def test_projection_below_line(self):
        """mean=22.0, threshold=25 → P(X >= 25) should be ~0.24."""
        prob = normal_cdf_upper_tail(mean=22.0, std_dev=4.2, threshold=25.0)
        assert 0.15 <= prob <= 0.35

    def test_projection_at_line(self):
        """mean == threshold → P(X >= threshold) should be ~0.50."""
        prob = normal_cdf_upper_tail(mean=25.0, std_dev=4.2, threshold=25.0)
        assert prob == pytest.approx(0.50, abs=0.01)

    def test_clamped_low(self):
        """Extreme below → clamped to 0.01."""
        prob = normal_cdf_upper_tail(mean=10.0, std_dev=1.0, threshold=25.0)
        assert prob == 0.01

    def test_clamped_high(self):
        """Extreme above → clamped to 0.99."""
        prob = normal_cdf_upper_tail(mean=40.0, std_dev=1.0, threshold=25.0)
        assert prob == 0.99

    def test_zero_std_dev_returns_half(self):
        prob = normal_cdf_upper_tail(mean=27.0, std_dev=0, threshold=25.0)
        assert prob == 0.50

    def test_symmetry(self):
        """P(X >= mean+2) should roughly equal 1 - P(X >= mean-2)."""
        p_above = normal_cdf_upper_tail(mean=25.0, std_dev=4.0, threshold=27.0)
        p_below = normal_cdf_upper_tail(mean=25.0, std_dev=4.0, threshold=23.0)
        assert p_above + p_below == pytest.approx(1.0, abs=0.01)


class TestCalculateKalshiEV:
    """EV calculation: DBB2 probability vs Kalshi price."""

    def test_yes_bet_when_dbb2_prob_higher(self):
        """DBB2 prob ~70% vs Kalshi 55% → YES bet with ~15% edge."""
        proj = _sample_projection()
        kalshi_data = {
            "line": 25.0, "yes_price": 0.55, "no_price": 0.45,
            "ticker": "TEST", "volume": 1000,
        }
        result = calculate_kalshi_ev(
            "LeBron James", proj, "points", kalshi_data, _sample_settings()
        )
        assert result is not None
        assert result["direction"] == "YES"
        assert result["edge_pct"] > 10.0

    def test_no_bet_when_dbb2_prob_lower(self):
        """DBB2 prob ~24% vs Kalshi 55% → NO bet."""
        proj = _sample_projection(
            props={"points": {"projection": 22.0, "std_dev": 4.2, "confidence": 0.78}}
        )
        kalshi_data = {
            "line": 25.0, "yes_price": 0.55, "no_price": 0.45,
            "ticker": "TEST", "volume": 1000,
        }
        result = calculate_kalshi_ev(
            "LeBron James", proj, "points", kalshi_data, _sample_settings()
        )
        assert result is not None
        assert result["direction"] == "NO"
        assert result["edge_pct"] > 20.0

    def test_no_edge_returns_none(self):
        """DBB2 prob ~50% vs Kalshi 50% → no edge on either side."""
        proj = _sample_projection(
            props={"points": {"projection": 25.0, "std_dev": 4.2, "confidence": 0.78}}
        )
        kalshi_data = {
            "line": 25.0, "yes_price": 0.50, "no_price": 0.50,
            "ticker": "TEST", "volume": 1000,
        }
        result = calculate_kalshi_ev(
            "LeBron James", proj, "points", kalshi_data, _sample_settings()
        )
        assert result is None

    def test_missing_prop_returns_none(self):
        proj = _sample_projection()
        kalshi_data = {"line": 5.0, "yes_price": 0.55, "no_price": 0.45, "ticker": "T", "volume": 100}
        result = calculate_kalshi_ev(
            "LeBron James", proj, "steals", kalshi_data, _sample_settings()
        )
        assert result is None

    def test_zero_std_dev_returns_none(self):
        proj = _sample_projection(
            props={"points": {"projection": 27.0, "std_dev": 0, "confidence": 0.78}}
        )
        kalshi_data = {"line": 25.0, "yes_price": 0.55, "no_price": 0.45, "ticker": "T", "volume": 100}
        result = calculate_kalshi_ev(
            "LeBron James", proj, "points", kalshi_data, _sample_settings()
        )
        assert result is None

    def test_result_has_source_kalshi(self):
        proj = _sample_projection()
        kalshi_data = {
            "line": 25.0, "yes_price": 0.55, "no_price": 0.45,
            "ticker": "TEST-TICKER", "volume": 1000,
        }
        result = calculate_kalshi_ev(
            "LeBron James", proj, "points", kalshi_data, _sample_settings()
        )
        assert result["source"] == "kalshi"
        assert result["ticker"] == "TEST-TICKER"
        assert result["volume"] == 1000

    def test_result_has_implied_probs(self):
        proj = _sample_projection()
        kalshi_data = {
            "line": 25.0, "yes_price": 0.55, "no_price": 0.45,
            "ticker": "T", "volume": 1000,
        }
        result = calculate_kalshi_ev(
            "LeBron James", proj, "points", kalshi_data, _sample_settings()
        )
        assert "dbb2_implied_prob" in result
        assert "kalshi_implied_prob" in result
        assert result["kalshi_implied_prob"] == 55.0


class TestKalshiKelly:
    """Kalshi Kelly sizing with binary payout."""

    def test_units_in_range(self):
        settings = _sample_settings()
        units = calculate_kalshi_kelly(
            edge_pct=15.0, bet_price=0.55, confidence=0.78, settings=settings
        )
        assert settings["kelly"]["min_units"] <= units <= settings["kelly"]["max_units"]

    def test_units_rounded_to_half(self):
        settings = _sample_settings()
        units = calculate_kalshi_kelly(
            edge_pct=15.0, bet_price=0.55, confidence=0.78, settings=settings
        )
        assert units % 0.5 == 0

    def test_extreme_edge_capped(self):
        settings = _sample_settings()
        units = calculate_kalshi_kelly(
            edge_pct=50.0, bet_price=0.30, confidence=0.90, settings=settings
        )
        assert units <= settings["kelly"]["max_units"]

    def test_small_edge_floored(self):
        settings = _sample_settings()
        units = calculate_kalshi_kelly(
            edge_pct=5.0, bet_price=0.80, confidence=0.60, settings=settings
        )
        assert units >= settings["kelly"]["min_units"]

    def test_win_amount_zero_returns_min(self):
        settings = _sample_settings()
        units = calculate_kalshi_kelly(
            edge_pct=10.0, bet_price=1.0, confidence=0.80, settings=settings
        )
        assert units == settings["kelly"]["min_units"]


class TestParseMarketTitle:
    """parse_market_title: extract player, line, prop from Kalshi titles."""

    def test_points(self):
        result = parse_market_title("LeBron James: 25+ points scored tonight")
        assert result["player_name"] == "Lebron James"
        assert result["line"] == 25.0
        assert result["prop_type"] == "points"

    def test_rebounds(self):
        result = parse_market_title("Nikola Jokic: 12+ rebounds")
        assert result["player_name"] == "Nikola Jokic"
        assert result["line"] == 12.0
        assert result["prop_type"] == "rebounds"

    def test_assists(self):
        result = parse_market_title("Luka Doncic: 8+ assists in game")
        assert result["player_name"] == "Luka Doncic"
        assert result["line"] == 8.0
        assert result["prop_type"] == "assists"

    def test_three_pointers(self):
        result = parse_market_title("Stephen Curry: 3+ three-pointers made")
        assert result["player_name"] == "Stephen Curry"
        assert result["line"] == 3.0
        assert result["prop_type"] == "threes"

    def test_threes_alternate(self):
        result = parse_market_title("Steph Curry: 4+ threes tonight")
        assert result["player_name"] == "Steph Curry"
        assert result["line"] == 4.0
        assert result["prop_type"] == "threes"

    def test_unparseable_returns_none(self):
        result = parse_market_title("Lakers win by 5+ points")
        assert result is None

    def test_decimal_line(self):
        result = parse_market_title("LeBron James: 24.5+ points")
        assert result["line"] == 24.5

    def test_case_insensitive(self):
        result = parse_market_title("LEBRON JAMES: 25+ POINTS")
        assert result is not None
        assert result["prop_type"] == "points"
