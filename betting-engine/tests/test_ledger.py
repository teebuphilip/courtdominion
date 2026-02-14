"""
Tests for src/ledger.py — bankroll management and P&L tracking.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ledger import (
    STARTING_BANKROLL,
    UNIT_DIVISOR,
    load_ledger,
    save_ledger,
    update_ledger,
    get_current_bankroll,
    get_current_unit_value,
    generate_ledger_markdown,
    LEDGER_PATH,
)


def _fresh_ledger():
    """Create a fresh ledger dict without touching disk."""
    return {
        "created_at": "2026-02-14T00:00:00+00:00",
        "starting_bankroll": STARTING_BANKROLL,
        "current_bankroll": STARTING_BANKROLL,
        "unit_value": STARTING_BANKROLL / UNIT_DIVISOR,
        "total_bets": 0,
        "wins": 0,
        "losses": 0,
        "pushes": 0,
        "no_action": 0,
        "total_wagered": 0.0,
        "total_pnl": 0.0,
        "roi_pct": 0.0,
        "win_rate_pct": 0.0,
        "daily_log": [],
    }


def _sample_results(wins=3, losses=2, pushes=1, no_action=0, daily_pnl=50.0):
    """Create a sample daily results dict."""
    bets = []
    for _ in range(wins):
        bets.append({"units": 1.5})
    for _ in range(losses):
        bets.append({"units": 1.5})
    for _ in range(pushes):
        bets.append({"units": 1.5})
    for _ in range(no_action):
        bets.append({"units": 1.5})
    return {
        "date": "2026-02-14",
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "no_action": no_action,
        "daily_pnl": daily_pnl,
        "bets": bets,
    }


class TestLedgerConstants:
    def test_starting_bankroll(self):
        assert STARTING_BANKROLL == 5000.0

    def test_unit_divisor(self):
        assert UNIT_DIVISOR == 100

    def test_starting_unit_value(self):
        assert STARTING_BANKROLL / UNIT_DIVISOR == 50.0


class TestLoadLedger:
    def test_creates_fresh_if_no_file(self, tmp_path, monkeypatch):
        fake_path = str(tmp_path / "ledger.json")
        monkeypatch.setattr("src.ledger.LEDGER_PATH", fake_path)
        ledger = load_ledger()
        assert ledger["starting_bankroll"] == STARTING_BANKROLL
        assert ledger["current_bankroll"] == STARTING_BANKROLL
        assert ledger["total_bets"] == 0
        assert ledger["daily_log"] == []
        assert Path(fake_path).exists()

    def test_loads_existing(self, tmp_path, monkeypatch):
        fake_path = str(tmp_path / "ledger.json")
        saved = _fresh_ledger()
        saved["current_bankroll"] = 5200.0
        with open(fake_path, "w") as f:
            json.dump(saved, f)

        monkeypatch.setattr("src.ledger.LEDGER_PATH", fake_path)
        ledger = load_ledger()
        assert ledger["current_bankroll"] == 5200.0


class TestUpdateLedger:
    def test_updates_totals(self):
        ledger = _fresh_ledger()
        results = _sample_results(wins=3, losses=2, pushes=1, daily_pnl=50.0)
        updated = update_ledger(ledger, results)

        assert updated["wins"] == 3
        assert updated["losses"] == 2
        assert updated["pushes"] == 1
        assert updated["total_bets"] == 6

    def test_updates_bankroll(self):
        ledger = _fresh_ledger()
        results = _sample_results(daily_pnl=100.0)
        updated = update_ledger(ledger, results)
        assert updated["current_bankroll"] == 5100.0

    def test_negative_pnl(self):
        ledger = _fresh_ledger()
        results = _sample_results(daily_pnl=-75.0)
        updated = update_ledger(ledger, results)
        assert updated["current_bankroll"] == 4925.0

    def test_unit_value_recalculates(self):
        ledger = _fresh_ledger()
        results = _sample_results(daily_pnl=200.0)
        updated = update_ledger(ledger, results)
        expected = round(5200.0 / UNIT_DIVISOR, 2)
        assert updated["unit_value"] == expected

    def test_win_rate_calculation(self):
        ledger = _fresh_ledger()
        results = _sample_results(wins=4, losses=1, pushes=0, daily_pnl=100.0)
        updated = update_ledger(ledger, results)
        # 4 / (4+1) * 100 = 80.0%
        assert updated["win_rate_pct"] == 80.0

    def test_win_rate_excludes_pushes(self):
        ledger = _fresh_ledger()
        results = _sample_results(wins=3, losses=2, pushes=5, daily_pnl=50.0)
        updated = update_ledger(ledger, results)
        # 3 / (3+2) * 100 = 60.0%
        assert updated["win_rate_pct"] == 60.0

    def test_roi_calculation(self):
        ledger = _fresh_ledger()
        results = _sample_results(wins=2, losses=1, pushes=0, daily_pnl=50.0)
        updated = update_ledger(ledger, results)
        # total_wagered = 3 bets * 1.5 units * 50.0 unit_value = 225.0
        # roi = 50 / 225 * 100 = 22.2%
        assert updated["roi_pct"] == 22.2

    def test_daily_log_appended(self):
        ledger = _fresh_ledger()
        results = _sample_results()
        updated = update_ledger(ledger, results)
        assert len(updated["daily_log"]) == 1
        entry = updated["daily_log"][0]
        assert entry["date"] == "2026-02-14"
        assert entry["wins"] == 3
        assert entry["losses"] == 2
        assert entry["bankroll_after"] == updated["current_bankroll"]

    def test_multiple_days(self):
        ledger = _fresh_ledger()
        day1 = _sample_results(wins=3, losses=1, pushes=0, daily_pnl=80.0)
        day1["date"] = "2026-02-14"
        ledger = update_ledger(ledger, day1)

        day2 = _sample_results(wins=2, losses=3, pushes=0, daily_pnl=-40.0)
        day2["date"] = "2026-02-15"
        ledger = update_ledger(ledger, day2)

        assert len(ledger["daily_log"]) == 2
        assert ledger["total_pnl"] == 40.0
        assert ledger["current_bankroll"] == 5040.0
        assert ledger["wins"] == 5
        assert ledger["losses"] == 4

    def test_no_action_counted(self):
        ledger = _fresh_ledger()
        results = _sample_results(wins=1, losses=0, pushes=0, no_action=2, daily_pnl=50.0)
        updated = update_ledger(ledger, results)
        assert updated["no_action"] == 2
        assert updated["total_bets"] == 3


class TestGetters:
    def test_get_current_bankroll(self, tmp_path, monkeypatch):
        fake_path = str(tmp_path / "ledger.json")
        saved = _fresh_ledger()
        saved["current_bankroll"] = 5300.0
        with open(fake_path, "w") as f:
            json.dump(saved, f)

        monkeypatch.setattr("src.ledger.LEDGER_PATH", fake_path)
        assert get_current_bankroll() == 5300.0

    def test_get_current_unit_value(self, tmp_path, monkeypatch):
        fake_path = str(tmp_path / "ledger.json")
        saved = _fresh_ledger()
        saved["current_bankroll"] = 5200.0
        with open(fake_path, "w") as f:
            json.dump(saved, f)

        monkeypatch.setattr("src.ledger.LEDGER_PATH", fake_path)
        assert get_current_unit_value() == 52.0


class TestMarkdownGeneration:
    def test_generates_header(self):
        ledger = _fresh_ledger()
        md = generate_ledger_markdown(ledger)
        assert "# DBB2 Paper Trading Ledger" in md

    def test_contains_bankroll(self):
        ledger = _fresh_ledger()
        md = generate_ledger_markdown(ledger)
        assert "$5,000.00" in md

    def test_contains_daily_table_header(self):
        ledger = _fresh_ledger()
        md = generate_ledger_markdown(ledger)
        assert "| Date | Bets | W-L-P | Wagered | P&L | Bankroll |" in md

    def test_daily_log_row(self):
        ledger = _fresh_ledger()
        results = _sample_results(wins=4, losses=2, pushes=1, daily_pnl=100.0)
        updated = update_ledger(ledger, results)
        md = generate_ledger_markdown(updated)
        assert "2026-02-14" in md
        assert "4-2-1" in md

    def test_negative_pnl_formatting(self):
        ledger = _fresh_ledger()
        results = _sample_results(daily_pnl=-50.0)
        updated = update_ledger(ledger, results)
        md = generate_ledger_markdown(updated)
        assert "-$50.00" in md
