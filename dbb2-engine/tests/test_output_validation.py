"""Tests for engine/validate.py — schema + cross-file consistency checks."""

import json
import os
import pytest
from pathlib import Path

from engine.validate import validate_output_dir, validate_cross_file_consistency
from engine.position_map import CD_POSITIONS


# Use existing output/ directory if available
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
SCHEMA_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "courtdominion-app"
    / "automation"
    / "schemas"
)

has_output = OUTPUT_DIR.exists() and (OUTPUT_DIR / "players.json").exists()
has_schemas = SCHEMA_DIR.exists() and (SCHEMA_DIR / "players_schema.json").exists()

try:
    import jsonschema
    has_jsonschema = True
except ImportError:
    has_jsonschema = False


@pytest.mark.skipif(not has_output, reason="No output/ directory with generated files")
class TestCrossFileConsistency:
    """Validate cross-file consistency of generated output."""

    def test_all_four_files_exist(self):
        for f in ("players.json", "projections.json", "risk.json", "insights.json"):
            assert (OUTPUT_DIR / f).exists(), f"{f} missing"

    def test_players_positions_are_cd_enum(self):
        players = _load(OUTPUT_DIR / "players.json")
        positions = {p["position"] for p in players}
        assert positions.issubset(CD_POSITIONS), f"Invalid positions: {positions - CD_POSITIONS}"

    def test_projections_positions_are_cd_enum(self):
        proj = _load(OUTPUT_DIR / "projections.json")
        positions = {p["position"] for p in proj}
        assert positions.issubset(CD_POSITIONS), f"Invalid positions: {positions - CD_POSITIONS}"

    def test_same_player_ids_across_files(self):
        players_ids = {p["player_id"] for p in _load(OUTPUT_DIR / "players.json")}
        proj_ids = {p["player_id"] for p in _load(OUTPUT_DIR / "projections.json")}
        risk_ids = {p["player_id"] for p in _load(OUTPUT_DIR / "risk.json")}
        insight_ids = {p["player_id"] for p in _load(OUTPUT_DIR / "insights.json")}

        assert players_ids == proj_ids, "players vs projections mismatch"
        assert players_ids == risk_ids, "players vs risk mismatch"
        assert players_ids == insight_ids, "players vs insights mismatch"

    def test_projections_sorted_by_fantasy_points_desc(self):
        proj = _load(OUTPUT_DIR / "projections.json")
        fps = [p["fantasy_points"] for p in proj]
        assert fps == sorted(fps, reverse=True), "projections not sorted by fantasy_points desc"

    def test_risk_values_are_ints_0_100(self):
        risk = _load(OUTPUT_DIR / "risk.json")
        for r in risk:
            for field in ("injury_risk", "volatility", "minutes_risk"):
                val = r[field]
                assert isinstance(val, int), f"{field} not int: {type(val)}"
                assert 0 <= val <= 100, f"{field} out of range: {val}"

    def test_insight_values_are_ints_0_100(self):
        insights = _load(OUTPUT_DIR / "insights.json")
        for i in insights:
            for field in ("value_score", "risk_score", "opportunity_index"):
                val = i[field]
                assert isinstance(val, int), f"{field} not int: {type(val)}"
                assert 0 <= val <= 100, f"{field} out of range: {val}"

    def test_no_negative_stat_projections(self):
        proj = _load(OUTPUT_DIR / "projections.json")
        stat_fields = [
            "minutes", "points", "rebounds", "assists", "steals", "blocks",
            "fgm", "fga", "tpm", "tpa", "ftm", "fta", "fantasy_points",
        ]
        for p in proj:
            for field in stat_fields:
                assert p[field] >= 0, f"{p['name']} {field} = {p[field]} is negative"

    def test_consistency_is_int_0_100(self):
        proj = _load(OUTPUT_DIR / "projections.json")
        for p in proj:
            c = p["consistency"]
            assert isinstance(c, int), f"consistency not int: {type(c)}"
            assert 0 <= c <= 100, f"consistency out of range: {c}"

    def test_validate_cross_file_function_passes(self):
        valid, errors = validate_cross_file_consistency(str(OUTPUT_DIR))
        assert valid, f"Cross-file validation failed: {errors}"


@pytest.mark.skipif(
    not (has_output and has_schemas and has_jsonschema),
    reason="Requires output/, CD schemas, and jsonschema package",
)
class TestSchemaValidation:
    """Validate output against CD JSON schemas."""

    def test_schema_validation_passes(self):
        valid, errors = validate_output_dir(str(OUTPUT_DIR), str(SCHEMA_DIR))
        assert valid, f"Schema validation failed:\n" + "\n".join(errors[:10])

    def test_players_schema(self):
        _assert_schema_valid("players.json", "players_schema.json")

    def test_projections_schema(self):
        _assert_schema_valid("projections.json", "projections_schema.json")

    def test_risk_schema(self):
        _assert_schema_valid("risk.json", "risk_schema.json")

    def test_insights_schema(self):
        _assert_schema_valid("insights.json", "insights_schema.json")


class TestValidationWithBadData:
    """Test that validation catches problems with synthetic bad data."""

    def test_missing_output_dir(self, tmp_path):
        valid, errors = validate_cross_file_consistency(str(tmp_path / "nonexistent"))
        assert not valid

    def test_bad_position_caught(self, tmp_path):
        _write_minimal_output(tmp_path, position="XYZ")
        valid, errors = validate_cross_file_consistency(str(tmp_path))
        assert not valid
        assert any("invalid position" in e for e in errors)

    def test_mismatched_player_ids_caught(self, tmp_path):
        _write_minimal_output(tmp_path)
        # Overwrite risk.json with different player_id
        risk = [{"player_id": "WRONG", "injury_risk": 30, "volatility": 40, "minutes_risk": 50}]
        _write(tmp_path / "risk.json", risk)
        valid, errors = validate_cross_file_consistency(str(tmp_path))
        assert not valid
        assert any("missing" in e or "extra" in e for e in errors)

    def test_unsorted_projections_caught(self, tmp_path):
        _write_minimal_output(tmp_path)
        # Overwrite with unsorted projections
        proj = [
            _make_proj("p1", "A", 10.0),
            _make_proj("p2", "B", 20.0),  # higher FP after lower — wrong order
        ]
        _write(tmp_path / "projections.json", proj)
        # Also need matching player ids in other files
        _write(tmp_path / "players.json", [
            {"player_id": "p1", "name": "A", "team": "BOS", "position": "PG", "status": "active"},
            {"player_id": "p2", "name": "B", "team": "LAL", "position": "SG", "status": "active"},
        ])
        _write(tmp_path / "risk.json", [
            {"player_id": "p1", "injury_risk": 30, "volatility": 40, "minutes_risk": 50},
            {"player_id": "p2", "injury_risk": 30, "volatility": 40, "minutes_risk": 50},
        ])
        _write(tmp_path / "insights.json", [
            {"player_id": "p1", "value_score": 50, "risk_score": 40, "opportunity_index": 55, "notes": "ok"},
            {"player_id": "p2", "value_score": 50, "risk_score": 40, "opportunity_index": 55, "notes": "ok"},
        ])
        valid, errors = validate_cross_file_consistency(str(tmp_path))
        assert not valid
        assert any("not sorted" in e for e in errors)

    def test_negative_stat_caught(self, tmp_path):
        _write_minimal_output(tmp_path)
        proj = [_make_proj("p1", "Test", 10.0, points=-5.0)]
        _write(tmp_path / "projections.json", proj)
        valid, errors = validate_cross_file_consistency(str(tmp_path))
        assert not valid
        assert any("negative" in e for e in errors)

    def test_out_of_range_risk_caught(self, tmp_path):
        _write_minimal_output(tmp_path)
        risk = [{"player_id": "p1", "injury_risk": 150, "volatility": 40, "minutes_risk": 50}]
        _write(tmp_path / "risk.json", risk)
        valid, errors = validate_cross_file_consistency(str(tmp_path))
        assert not valid
        assert any("out of range" in e for e in errors)


# --- Helpers ---

def _load(path):
    with open(path) as f:
        return json.load(f)


def _write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)


def _make_proj(pid, name, fp, points=10.0):
    return {
        "player_id": pid, "name": name, "team": "BOS", "position": "PG",
        "minutes": 30.0, "usage_rate": 20.0, "points": points,
        "rebounds": 5.0, "assists": 5.0, "steals": 1.0, "blocks": 0.5,
        "turnovers": 2.0, "fg_pct": 0.450, "three_pt_pct": 0.350,
        "ft_pct": 0.800, "fgm": 7.0, "fga": 15.0, "tpm": 2.0, "tpa": 5.0,
        "ftm": 3.0, "fta": 4.0, "fantasy_points": fp, "ceiling": fp + 10,
        "floor": fp - 5, "consistency": 65,
    }


def _write_minimal_output(tmp_path, position="PG"):
    """Write a minimal valid set of 4 output files."""
    _write(tmp_path / "players.json", [
        {"player_id": "p1", "name": "Test", "team": "BOS", "position": position, "status": "active"},
    ])
    _write(tmp_path / "projections.json", [_make_proj("p1", "Test", 25.0)])
    _write(tmp_path / "risk.json", [
        {"player_id": "p1", "injury_risk": 30, "volatility": 40, "minutes_risk": 50},
    ])
    _write(tmp_path / "insights.json", [
        {"player_id": "p1", "value_score": 70, "risk_score": 40, "opportunity_index": 65, "notes": "Solid value."},
    ])


def _assert_schema_valid(data_file, schema_file):
    """Validate a single file against its schema."""
    import jsonschema

    with open(OUTPUT_DIR / data_file) as f:
        data = json.load(f)
    with open(SCHEMA_DIR / schema_file) as f:
        schema = json.load(f)

    jsonschema.validate(data, schema)
