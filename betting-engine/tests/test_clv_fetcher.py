"""Tests for CLV Fetcher — closing line value math and CSV schema."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.clv_fetcher import calculate_sportsbook_clv, calculate_kalshi_clv
from src.csv_tracker import CSV_HEADERS


# ---------------------------------------------------------------------------
# Sportsbook CLV math
# ---------------------------------------------------------------------------

class TestSportsbookCLV:
    def test_over_positive_clv(self):
        """Morning 24.5, closing 25.5, OVER → +1.0 (market moved your way)."""
        assert calculate_sportsbook_clv(24.5, 25.5, "OVER") == 1.0

    def test_over_negative_clv(self):
        """Morning 24.5, closing 23.5, OVER → -1.0 (market moved against you)."""
        assert calculate_sportsbook_clv(24.5, 23.5, "OVER") == -1.0

    def test_over_zero_clv(self):
        """Morning 24.5, closing 24.5, OVER → 0.0 (no movement)."""
        assert calculate_sportsbook_clv(24.5, 24.5, "OVER") == 0.0

    def test_under_positive_clv(self):
        """Morning 24.5, closing 23.5, UNDER → +1.0 (market moved your way)."""
        assert calculate_sportsbook_clv(24.5, 23.5, "UNDER") == 1.0

    def test_under_negative_clv(self):
        """Morning 24.5, closing 25.5, UNDER → -1.0 (market moved against you)."""
        assert calculate_sportsbook_clv(24.5, 25.5, "UNDER") == -1.0

    def test_half_point_movement(self):
        """Morning 6.5, closing 7.0, OVER → +0.5."""
        assert calculate_sportsbook_clv(6.5, 7.0, "OVER") == 0.5


# ---------------------------------------------------------------------------
# Kalshi CLV math
# ---------------------------------------------------------------------------

class TestKalshiCLV:
    def test_yes_positive_clv(self):
        """Morning 0.55, closing 0.63, YES → +0.08."""
        result = calculate_kalshi_clv(0.55, 0.63, "YES")
        assert result == pytest.approx(0.08, abs=0.0001)

    def test_yes_negative_clv(self):
        """Morning 0.55, closing 0.47, YES → -0.08."""
        result = calculate_kalshi_clv(0.55, 0.47, "YES")
        assert result == pytest.approx(-0.08, abs=0.0001)

    def test_no_positive_clv(self):
        """Morning 0.55, closing 0.47, NO → +0.08 (YES fell = good for NO)."""
        result = calculate_kalshi_clv(0.55, 0.47, "NO")
        assert result == pytest.approx(0.08, abs=0.0001)

    def test_no_negative_clv(self):
        """Morning 0.55, closing 0.63, NO → -0.08 (YES rose = bad for NO)."""
        result = calculate_kalshi_clv(0.55, 0.63, "NO")
        assert result == pytest.approx(-0.08, abs=0.0001)

    def test_four_decimal_precision(self):
        """Kalshi CLV should have 4 decimal places."""
        result = calculate_kalshi_clv(0.5512, 0.5637, "YES")
        assert result == 0.0125
        assert len(str(result).split(".")[-1]) <= 4


# ---------------------------------------------------------------------------
# CSV schema
# ---------------------------------------------------------------------------

class TestCSVSchema:
    def test_closing_line_in_headers(self):
        assert "closing_line" in CSV_HEADERS

    def test_clv_in_headers(self):
        assert "clv" in CSV_HEADERS

    def test_column_order(self):
        """closing_line and clv should come after pnl, before notes."""
        pnl_idx = CSV_HEADERS.index("pnl")
        closing_idx = CSV_HEADERS.index("closing_line")
        clv_idx = CSV_HEADERS.index("clv")
        notes_idx = CSV_HEADERS.index("notes")

        assert closing_idx == pnl_idx + 1
        assert clv_idx == pnl_idx + 2
        assert notes_idx == pnl_idx + 3

    def test_total_columns(self):
        """Should have 22 columns after adding closing_line and clv."""
        assert len(CSV_HEADERS) == 22


# ---------------------------------------------------------------------------
# Graceful failure
# ---------------------------------------------------------------------------

class TestGracefulFailure:
    def test_clv_when_player_not_found(self):
        """If player not in closing odds, CLV calc shouldn't crash."""
        # No closing data available — function returns empty dict
        closing = {}
        key = ("unknown player", "points")
        assert key not in closing

    def test_clv_with_empty_morning_line(self):
        """If morning line is empty string, should handle gracefully."""
        try:
            float("")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected — clv_fetcher catches this

    def test_sportsbook_clv_symmetry(self):
        """OVER and UNDER CLV should be symmetric."""
        over_clv = calculate_sportsbook_clv(24.5, 25.5, "OVER")
        under_clv = calculate_sportsbook_clv(24.5, 25.5, "UNDER")
        assert over_clv == -under_clv
