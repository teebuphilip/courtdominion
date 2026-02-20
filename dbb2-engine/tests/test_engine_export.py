"""
Tests for engine/export.py — JSON output formatter.
"""

import json
import tempfile
from pathlib import Path

import pytest

from engine.baseline import PlayerContext
from engine.projections import SeasonProjection
from engine.pricing import AuctionValue
from engine.export import export_all


def _make_contexts(n=5):
    """Build test PlayerContexts."""
    return [
        PlayerContext(
            player_id=f"P{i}",
            player_name=f"Player {i}",
            team="TST",
            position=["G", "F", "C"][i % 3],
            raw_position=["G", "F", "C"][i % 3],
            age=22 + i,
            role="Starter" if i < 3 else "Rotation",
            age_bracket="Young" if i < 3 else "Prime",
        )
        for i in range(n)
    ]


def _make_projections(n=5):
    """Build test SeasonProjections."""
    return [
        SeasonProjection(
            player_id=f"P{i}",
            player_name=f"Player {i}",
            team="TST",
            position=["G", "F", "C"][i % 3],
            minutes=28.0 + i,
            usage_rate=22.0 + i,
            points=15.0 + i * 2,
            rebounds=4.0 + i * 0.5,
            assists=3.0 + i * 0.8,
            steals=1.0 + i * 0.1,
            blocks=0.5 + i * 0.1,
            turnovers=2.0,
            fgm=6.0 + i,
            fga=13.0 + i,
            three_pm=1.5 + i * 0.3,
            three_pa=4.0 + i * 0.5,
            ftm=2.5,
            fta=3.0,
            fg_pct=0.46,
            three_pt_pct=0.37,
            ft_pct=0.83,
            fantasy_points=30.0 + i * 3,
            projected_games=70 + i,
            ceiling=45.0 + i * 4,
            floor=18.0 + i,
            consistency=50 + i * 5,
        )
        for i in range(n)
    ]


def _make_auction_values(n=5):
    """Build test AuctionValues."""
    return [
        AuctionValue(
            player_id=f"P{i}",
            player_name=f"Player {i}",
            position=["G", "F", "C"][i % 3],
            raw_z_score=1.0 + i * 0.5,
            sgp_value=2.0 + i,
            scarcity_adjusted=2.5 + i,
            dollar_value=5 + i * 10,
        )
        for i in range(n)
    ]


class TestPlayersJson:
    """players.json output validation."""

    def test_required_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_all(
                _make_contexts(), _make_projections(),
                _make_auction_values(), tmpdir,
            )
            data = json.loads((Path(tmpdir) / "players.json").read_text())
            for entry in data:
                assert "player_id" in entry
                assert "name" in entry
                assert "team" in entry
                assert "position" in entry
                assert "status" in entry

    def test_no_none_values(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_all(
                _make_contexts(), _make_projections(),
                _make_auction_values(), tmpdir,
            )
            data = json.loads((Path(tmpdir) / "players.json").read_text())
            for entry in data:
                for key, val in entry.items():
                    assert val is not None, f"{key} is None"


class TestProjectionsJson:
    """projections.json output validation."""

    def test_field_mapping_tpm_tpa(self):
        """three_pm should map to tpm, three_pa to tpa."""
        with tempfile.TemporaryDirectory() as tmpdir:
            export_all(
                _make_contexts(), _make_projections(),
                _make_auction_values(), tmpdir,
            )
            data = json.loads((Path(tmpdir) / "projections.json").read_text())
            for entry in data:
                assert "tpm" in entry, "Missing tpm field"
                assert "tpa" in entry, "Missing tpa field"
                assert "three_pm" not in entry, "Should be tpm not three_pm"
                assert "three_pa" not in entry, "Should be tpa not three_pa"

    def test_consistency_int_0_100(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_all(
                _make_contexts(), _make_projections(),
                _make_auction_values(), tmpdir,
            )
            data = json.loads((Path(tmpdir) / "projections.json").read_text())
            for entry in data:
                assert isinstance(entry["consistency"], int)
                assert 0 <= entry["consistency"] <= 100

    def test_non_negative_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_all(
                _make_contexts(), _make_projections(),
                _make_auction_values(), tmpdir,
            )
            data = json.loads((Path(tmpdir) / "projections.json").read_text())
            stat_fields = [
                "minutes", "points", "rebounds", "assists",
                "steals", "blocks", "turnovers", "fgm", "fga",
                "tpm", "tpa", "ftm", "fta", "fantasy_points",
            ]
            for entry in data:
                for field in stat_fields:
                    assert entry[field] >= 0, f"{field} = {entry[field]}"

    def test_percentages_reasonable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_all(
                _make_contexts(), _make_projections(),
                _make_auction_values(), tmpdir,
            )
            data = json.loads((Path(tmpdir) / "projections.json").read_text())
            for entry in data:
                for pct_field in ("fg_pct", "three_pt_pct", "ft_pct"):
                    assert 0.0 <= entry[pct_field] <= 1.0, (
                        f"{pct_field} = {entry[pct_field]}"
                    )


class TestRiskJson:
    """risk.json output validation."""

    def test_all_scores_int_0_100(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_all(
                _make_contexts(), _make_projections(),
                _make_auction_values(), tmpdir,
            )
            data = json.loads((Path(tmpdir) / "risk.json").read_text())
            for entry in data:
                for field in ("injury_risk", "volatility", "minutes_risk"):
                    assert isinstance(entry[field], int)
                    assert 0 <= entry[field] <= 100, (
                        f"{field} = {entry[field]}"
                    )

    def test_extended_uncertainty_fields_exist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_all(
                _make_contexts(), _make_projections(),
                _make_auction_values(), tmpdir,
            )
            data = json.loads((Path(tmpdir) / "risk.json").read_text())
            for entry in data:
                assert "availability_risk" in entry
                assert "role_risk" in entry
                assert "composition_risk" in entry
                assert "total_risk" in entry
                assert "risk_level" in entry
                assert 0.0 <= entry["availability_risk"] <= 1.0
                assert 0.0 <= entry["role_risk"] <= 1.0
                assert 0.0 <= entry["composition_risk"] <= 1.0
                assert 0.0 <= entry["total_risk"] <= 1.0
                assert entry["risk_level"] in {"Low", "Medium", "High"}


class TestInsightsJson:
    """insights.json output validation."""

    def test_all_scores_int_0_100(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_all(
                _make_contexts(), _make_projections(),
                _make_auction_values(), tmpdir,
            )
            data = json.loads((Path(tmpdir) / "insights.json").read_text())
            for entry in data:
                for field in ("value_score", "risk_score", "opportunity_index"):
                    assert isinstance(entry[field], int)
                    assert 0 <= entry[field] <= 100, (
                        f"{field} = {entry[field]}"
                    )

    def test_notes_nonempty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_all(
                _make_contexts(), _make_projections(),
                _make_auction_values(), tmpdir,
            )
            data = json.loads((Path(tmpdir) / "insights.json").read_text())
            for entry in data:
                assert isinstance(entry["notes"], str)
                assert len(entry["notes"]) > 0


class TestFileCount:
    """Should produce exactly 4 JSON files."""

    def test_four_files_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = export_all(
                _make_contexts(), _make_projections(),
                _make_auction_values(), tmpdir,
            )
            assert len(files) == 4
            for name in ("players.json", "projections.json",
                          "risk.json", "insights.json"):
                assert name in files
                assert Path(files[name]).exists()
