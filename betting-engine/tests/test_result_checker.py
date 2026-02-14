"""
Tests for src/result_checker.py — box score grading and payout calculation.

Tests grade_bet, calculate_payout, grade_all_bets, and season slug derivation.
Covers both sportsbook (OVER/UNDER) and Kalshi (YES/NO) grading.
NBA API integration is NOT tested here (requires live network).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.result_checker import (
    grade_bet,
    calculate_payout,
    grade_all_bets,
    get_season_slug,
    PROP_TO_STAT,
)


def _make_bet(**overrides):
    """Build a test bet dict matching bet_slip.output_json format."""
    defaults = {
        "player_name": "LeBron James",
        "prop_type": "points",
        "direction": "OVER",
        "source": "sportsbook",
        "dbb2_projection": 25.5,
        "sportsbook_line": 24.5,
        "edge_pct": 23.8,
        "confidence": 0.78,
        "units": 1.5,
        "over_odds": -115,
        "under_odds": -105,
        "decimal_odds": 1.870,
    }
    defaults.update(overrides)
    return defaults


def _make_kalshi_bet(**overrides):
    """Build a test Kalshi bet dict."""
    defaults = {
        "player_name": "LeBron James",
        "prop_type": "points",
        "direction": "YES",
        "source": "kalshi",
        "dbb2_projection": 27.2,
        "line": 25.0,
        "kalshi_price": 0.55,
        "dbb2_implied_prob": 70.0,
        "kalshi_implied_prob": 55.0,
        "edge_pct": 15.0,
        "confidence": 0.78,
        "units": 1.5,
        "ticker": "NBA-TEST",
        "volume": 1000,
    }
    defaults.update(overrides)
    return defaults


def _make_bet_slip(bets, date="2026-02-14"):
    """Build a test bet slip dict."""
    return {
        "date": date,
        "generated_at": "2026-02-14T12:00:00+00:00",
        "total_bets": len(bets),
        "total_units": sum(b["units"] for b in bets),
        "bets": bets,
    }


def _sample_box_scores():
    """Box scores matching the fixture players."""
    return {
        "lebron james": {
            "PTS": 27, "REB": 8, "AST": 9, "FG3M": 2,
            "STL": 1, "BLK": 1, "MIN": 35,
        },
        "giannis antetokounmpo": {
            "PTS": 33, "REB": 12, "AST": 5, "FG3M": 0,
            "STL": 2, "BLK": 2, "MIN": 37,
        },
    }


class TestGradeBet:
    """grade_bet: compare actual stat to sportsbook line."""

    def test_over_wins(self):
        bet = _make_bet(direction="OVER", sportsbook_line=24.5)
        assert grade_bet(bet, 27) == "WIN"

    def test_over_loses(self):
        bet = _make_bet(direction="OVER", sportsbook_line=24.5)
        assert grade_bet(bet, 20) == "LOSS"

    def test_under_wins(self):
        bet = _make_bet(direction="UNDER", sportsbook_line=2.5)
        assert grade_bet(bet, 2) == "WIN"

    def test_under_loses(self):
        bet = _make_bet(direction="UNDER", sportsbook_line=2.5)
        assert grade_bet(bet, 3) == "LOSS"

    def test_push_over(self):
        bet = _make_bet(direction="OVER", sportsbook_line=25.0)
        assert grade_bet(bet, 25) == "PUSH"

    def test_push_under(self):
        bet = _make_bet(direction="UNDER", sportsbook_line=25.0)
        assert grade_bet(bet, 25) == "PUSH"

    def test_dnp_returns_no_action(self):
        bet = _make_bet()
        assert grade_bet(bet, None) == "NO_ACTION"

    def test_zero_actual_under(self):
        bet = _make_bet(direction="UNDER", sportsbook_line=0.5)
        assert grade_bet(bet, 0) == "WIN"

    def test_zero_actual_over(self):
        bet = _make_bet(direction="OVER", sportsbook_line=0.5)
        assert grade_bet(bet, 0) == "LOSS"


class TestCalculatePayout:
    """calculate_payout: dollar profit/loss from graded bet."""

    def test_win_payout(self):
        bet = _make_bet(units=1.5, over_odds=-115, direction="OVER")
        payout = calculate_payout(bet, "WIN", unit_value=50.0)
        # stake = 1.5 * 50 = 75, decimal = 1.8696, profit = 75 * 0.8696 = 65.22
        assert payout == pytest.approx(65.22, abs=0.01)

    def test_loss_payout(self):
        bet = _make_bet(units=1.5, direction="OVER")
        payout = calculate_payout(bet, "LOSS", unit_value=50.0)
        assert payout == -75.0

    def test_push_zero(self):
        bet = _make_bet(units=1.5)
        payout = calculate_payout(bet, "PUSH", unit_value=50.0)
        assert payout == 0.0

    def test_no_action_zero(self):
        bet = _make_bet(units=1.5)
        payout = calculate_payout(bet, "NO_ACTION", unit_value=50.0)
        assert payout == 0.0

    def test_positive_odds_payout(self):
        bet = _make_bet(units=1.0, over_odds=150, direction="OVER")
        payout = calculate_payout(bet, "WIN", unit_value=50.0)
        # stake = 50, decimal = 2.5, profit = 50 * 1.5 = 75.0
        assert payout == 75.0

    def test_under_odds_used(self):
        bet = _make_bet(units=1.0, under_odds=-130, direction="UNDER")
        payout = calculate_payout(bet, "WIN", unit_value=50.0)
        # stake = 50, decimal = 1 + 100/130 = 1.7692, profit = 50 * 0.7692 = 38.46
        assert payout == pytest.approx(38.46, abs=0.01)


class TestGradeAllBets:
    """grade_all_bets: full slip grading against box scores."""

    def test_all_bets_graded(self):
        bets = [
            _make_bet(player_name="LeBron James", prop_type="points",
                      direction="OVER", sportsbook_line=24.5),
            _make_bet(player_name="Giannis Antetokounmpo", prop_type="points",
                      direction="OVER", sportsbook_line=29.5),
        ]
        slip = _make_bet_slip(bets)
        results = grade_all_bets(slip, _sample_box_scores(), unit_value=50.0)

        assert results["total_bets"] == 2
        assert results["date"] == "2026-02-14"

    def test_win_counted(self):
        bets = [
            _make_bet(player_name="LeBron James", prop_type="points",
                      direction="OVER", sportsbook_line=24.5),
        ]
        slip = _make_bet_slip(bets)
        results = grade_all_bets(slip, _sample_box_scores(), unit_value=50.0)
        # LeBron scored 27 > 24.5 → WIN
        assert results["wins"] == 1

    def test_loss_counted(self):
        bets = [
            _make_bet(player_name="LeBron James", prop_type="points",
                      direction="OVER", sportsbook_line=30.0),
        ]
        slip = _make_bet_slip(bets)
        results = grade_all_bets(slip, _sample_box_scores(), unit_value=50.0)
        # LeBron scored 27 < 30.0 → LOSS
        assert results["losses"] == 1

    def test_player_not_found_no_action(self):
        bets = [
            _make_bet(player_name="Unknown Player", prop_type="points",
                      direction="OVER", sportsbook_line=20.0),
        ]
        slip = _make_bet_slip(bets)
        results = grade_all_bets(slip, _sample_box_scores(), unit_value=50.0)
        assert results["no_action"] == 1

    def test_daily_pnl_summed(self):
        bets = [
            _make_bet(player_name="LeBron James", prop_type="points",
                      direction="OVER", sportsbook_line=24.5, units=1.0),
            _make_bet(player_name="LeBron James", prop_type="assists",
                      direction="OVER", sportsbook_line=10.0, units=1.0,
                      over_odds=-110),
        ]
        slip = _make_bet_slip(bets)
        results = grade_all_bets(slip, _sample_box_scores(), unit_value=50.0)
        # LeBron PTS 27 > 24.5 → WIN, AST 9 < 10.0 → LOSS
        assert results["wins"] == 1
        assert results["losses"] == 1
        # daily_pnl = win_payout + loss_payout
        assert results["daily_pnl"] != 0  # net result

    def test_graded_bet_has_actual_stat(self):
        bets = [
            _make_bet(player_name="LeBron James", prop_type="rebounds",
                      direction="UNDER", sportsbook_line=8.5),
        ]
        slip = _make_bet_slip(bets)
        results = grade_all_bets(slip, _sample_box_scores(), unit_value=50.0)
        assert results["bets"][0]["actual_stat"] == 8

    def test_graded_bet_has_outcome(self):
        bets = [
            _make_bet(player_name="LeBron James", prop_type="threes",
                      direction="UNDER", sportsbook_line=2.5),
        ]
        slip = _make_bet_slip(bets)
        results = grade_all_bets(slip, _sample_box_scores(), unit_value=50.0)
        # LeBron FG3M=2 < 2.5 → UNDER wins
        assert results["bets"][0]["outcome"] == "WIN"

    def test_all_six_props_have_mapping(self):
        assert len(PROP_TO_STAT) == 6
        expected = {"points", "rebounds", "assists", "threes", "steals", "blocks"}
        assert set(PROP_TO_STAT.keys()) == expected


class TestSeasonSlug:
    """get_season_slug: derive NBA season string from date."""

    def test_january_game(self):
        assert get_season_slug("2026-01-15") == "2025-26"

    def test_october_game(self):
        assert get_season_slug("2025-10-22") == "2025-26"

    def test_december_game(self):
        assert get_season_slug("2025-12-25") == "2025-26"

    def test_april_game(self):
        assert get_season_slug("2026-04-10") == "2025-26"

    def test_february_2026(self):
        assert get_season_slug("2026-02-14") == "2025-26"


class TestKalshiGradeBet:
    """grade_bet: Kalshi YES/NO grading with >= threshold."""

    def test_yes_wins_above_line(self):
        bet = _make_kalshi_bet(direction="YES", line=25.0)
        assert grade_bet(bet, 27) == "WIN"

    def test_yes_wins_at_line(self):
        """WHY: Kalshi '25+ points' means >= 25, so exact match = WIN for YES."""
        bet = _make_kalshi_bet(direction="YES", line=25.0)
        assert grade_bet(bet, 25) == "WIN"

    def test_yes_loses_below_line(self):
        bet = _make_kalshi_bet(direction="YES", line=25.0)
        assert grade_bet(bet, 24) == "LOSS"

    def test_no_wins_below_line(self):
        bet = _make_kalshi_bet(direction="NO", line=25.0)
        assert grade_bet(bet, 20) == "WIN"

    def test_no_loses_at_line(self):
        """WHY: At line, YES wins → NO loses (>= threshold)."""
        bet = _make_kalshi_bet(direction="NO", line=25.0)
        assert grade_bet(bet, 25) == "LOSS"

    def test_no_loses_above_line(self):
        bet = _make_kalshi_bet(direction="NO", line=25.0)
        assert grade_bet(bet, 30) == "LOSS"

    def test_dnp_returns_no_action(self):
        bet = _make_kalshi_bet()
        assert grade_bet(bet, None) == "NO_ACTION"


class TestKalshiCalculatePayout:
    """calculate_payout: Kalshi binary payout math."""

    def test_yes_win_payout(self):
        """Buy YES at $0.55 → win = stake * (1-0.55)/0.55."""
        bet = _make_kalshi_bet(units=1.0, kalshi_price=0.55)
        payout = calculate_payout(bet, "WIN", unit_value=50.0)
        # stake=50, profit = 50 * 0.45/0.55 = 40.91
        assert payout == pytest.approx(40.91, abs=0.01)

    def test_yes_loss_payout(self):
        bet = _make_kalshi_bet(units=1.0, kalshi_price=0.55)
        payout = calculate_payout(bet, "LOSS", unit_value=50.0)
        assert payout == -50.0

    def test_no_win_payout(self):
        """Buy NO at $0.40 → win = stake * (1-0.40)/0.40."""
        bet = _make_kalshi_bet(direction="NO", units=2.0, kalshi_price=0.40)
        payout = calculate_payout(bet, "WIN", unit_value=50.0)
        # stake=100, profit = 100 * 0.60/0.40 = 150.0
        assert payout == 150.0

    def test_push_zero(self):
        bet = _make_kalshi_bet()
        payout = calculate_payout(bet, "PUSH", unit_value=50.0)
        assert payout == 0.0

    def test_cheap_yes_big_payout(self):
        """Buy YES at $0.20 → high payout ratio on win."""
        bet = _make_kalshi_bet(units=1.0, kalshi_price=0.20)
        payout = calculate_payout(bet, "WIN", unit_value=50.0)
        # stake=50, profit = 50 * 0.80/0.20 = 200.0
        assert payout == 200.0


class TestKalshiGradeAllBets:
    """grade_all_bets: mixed sportsbook + Kalshi grading."""

    def test_mixed_slip_grades_both(self):
        bets = [
            _make_bet(player_name="LeBron James", prop_type="points",
                      direction="OVER", sportsbook_line=24.5),
            _make_kalshi_bet(player_name="LeBron James", prop_type="rebounds",
                             direction="YES", line=7.0),
        ]
        slip = _make_bet_slip(bets)
        results = grade_all_bets(slip, _sample_box_scores(), unit_value=50.0)
        assert results["total_bets"] == 2
        # PTS: 27 > 24.5 → WIN, REB: 8 >= 7 → YES WIN
        assert results["wins"] == 2

    def test_kalshi_bet_has_source_field(self):
        bets = [
            _make_kalshi_bet(player_name="LeBron James", prop_type="points",
                             direction="YES", line=25.0),
        ]
        slip = _make_bet_slip(bets)
        results = grade_all_bets(slip, _sample_box_scores(), unit_value=50.0)
        assert results["bets"][0]["source"] == "kalshi"

    def test_kalshi_no_bet_wins_below_line(self):
        bets = [
            _make_kalshi_bet(player_name="Giannis Antetokounmpo", prop_type="threes",
                             direction="NO", line=1.0),
        ]
        slip = _make_bet_slip(bets)
        results = grade_all_bets(slip, _sample_box_scores(), unit_value=50.0)
        # Giannis FG3M=0 < 1.0 → NO wins
        assert results["wins"] == 1
