"""
Integration tests for the full engine pipeline.

End-to-end: CSV data → project_all_season → export_json → 4 valid JSON files.
These tests load real data and take longer to run.
"""

import json
import tempfile
from pathlib import Path

import pytest

from engine import project_all_season, export_json


@pytest.fixture(scope="module")
def engine_output():
    """Run the full pipeline once and cache results for all tests."""
    contexts, projections, auction_values = project_all_season(seasons_to_load=3)
    return contexts, projections, auction_values


@pytest.fixture(scope="module")
def json_output(engine_output):
    """Export JSON files to a temp dir and return paths + data."""
    contexts, projections, auction_values = engine_output
    with tempfile.TemporaryDirectory() as tmpdir:
        files = export_json(contexts, projections, auction_values, tmpdir)
        data = {}
        for name, path in files.items():
            with open(path) as f:
                data[name] = json.load(f)
        yield files, data


class TestEndToEnd:
    """Full pipeline produces valid output."""

    def test_contexts_non_empty(self, engine_output):
        contexts, _, _ = engine_output
        assert len(contexts) > 100, f"Only {len(contexts)} players"

    def test_projections_match_contexts(self, engine_output):
        contexts, projections, _ = engine_output
        assert len(projections) == len(contexts)

    def test_auction_values_match(self, engine_output):
        _, projections, auction_values = engine_output
        assert len(auction_values) == len(projections)

    def test_four_json_files(self, json_output):
        files, data = json_output
        assert len(files) == 4
        for name in ("players.json", "projections.json",
                      "risk.json", "insights.json"):
            assert name in files

    def test_json_parseable(self, json_output):
        _, data = json_output
        for name, entries in data.items():
            assert isinstance(entries, list), f"{name} is not a list"
            assert len(entries) > 0, f"{name} is empty"

    def test_counts_consistent(self, json_output):
        _, data = json_output
        player_count = len(data["players.json"])
        assert len(data["projections.json"]) == player_count
        assert len(data["risk.json"]) == player_count
        assert len(data["insights.json"]) == player_count


class TestKnownPlayerRange:
    """Sanity checks on projected values."""

    def test_prime_starter_reasonable_stats(self, engine_output):
        """A prime-age starter should project reasonable numbers."""
        contexts, projections, _ = engine_output
        # Find a prime-age (27-30) starter
        starters = [
            (c, p) for c, p in zip(contexts, projections)
            if c.role == "Starter" and 27 <= c.age <= 30
        ]
        assert len(starters) > 0, "No prime starters found"

        # Check the top starter by fantasy points
        starters.sort(key=lambda x: x[1].fantasy_points, reverse=True)
        _, top = starters[0]

        assert top.points > 10, f"Top starter only {top.points} ppg"
        assert top.fantasy_points > 20, f"Top starter only {top.fantasy_points} fp"
        assert top.projected_games > 50, f"Top starter only {top.projected_games} games"

    def test_bench_lower_minutes(self, engine_output):
        """Bench players should average fewer minutes than starters."""
        contexts, projections, _ = engine_output
        starter_min = [
            p.minutes for c, p in zip(contexts, projections)
            if c.role == "Starter"
        ]
        bench_min = [
            p.minutes for c, p in zip(contexts, projections)
            if c.role == "Bench"
        ]
        if starter_min and bench_min:
            avg_starter = sum(starter_min) / len(starter_min)
            avg_bench = sum(bench_min) / len(bench_min)
            assert avg_starter > avg_bench

    def test_no_negative_projections(self, engine_output):
        """No player should have negative stat projections."""
        _, projections, _ = engine_output
        for p in projections:
            assert p.points >= 0, f"{p.player_name}: points={p.points}"
            assert p.rebounds >= 0, f"{p.player_name}: rebounds={p.rebounds}"
            assert p.assists >= 0, f"{p.player_name}: assists={p.assists}"
            assert p.fantasy_points >= 0, f"{p.player_name}: fp={p.fantasy_points}"


class TestAuctionValues:
    """Auction pricing sanity checks."""

    def test_dollar_range(self, engine_output):
        """All dollar values should be in [1, 70]."""
        _, _, auction_values = engine_output
        for v in auction_values:
            assert 1 <= v.dollar_value <= 70, (
                f"{v.player_name}: ${v.dollar_value}"
            )

    def test_budget_constraint(self, engine_output):
        """Total dollar values should equal $2,400."""
        _, _, auction_values = engine_output
        total = sum(v.dollar_value for v in auction_values)
        from engine.pricing import TOTAL_BUDGET
        assert total == TOTAL_BUDGET, f"Total: ${total} != ${TOTAL_BUDGET}"

    def test_top_player_premium(self, engine_output):
        """Top player should be worth significantly more than average."""
        _, _, auction_values = engine_output
        sorted_vals = sorted(auction_values, key=lambda v: v.dollar_value, reverse=True)
        top_dollar = sorted_vals[0].dollar_value
        avg_dollar = sum(v.dollar_value for v in auction_values) / len(auction_values)
        assert top_dollar > avg_dollar * 2


class TestRiskScores:
    """Risk score validation."""

    def test_all_scores_valid(self, json_output):
        _, data = json_output
        for entry in data["risk.json"]:
            for field in ("injury_risk", "volatility", "minutes_risk"):
                assert 0 <= entry[field] <= 100


class TestInsightsScores:
    """Insights score validation."""

    def test_all_scores_valid(self, json_output):
        _, data = json_output
        for entry in data["insights.json"]:
            for field in ("value_score", "risk_score", "opportunity_index"):
                assert 0 <= entry[field] <= 100
            assert len(entry["notes"]) > 0
