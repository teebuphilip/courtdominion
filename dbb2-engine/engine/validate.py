"""
Validate DBB2 engine output against CD app JSON schemas.

Two validation passes:
1. Schema validation — each JSON file matches its CD schema (requires jsonschema)
2. Cross-file consistency — player_ids match, sort order correct, values in range
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

from engine.position_map import CD_POSITIONS

# CD schema directory (default: sibling repo)
DEFAULT_SCHEMA_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "courtdominion-app"
    / "automation"
    / "schemas"
)

# Map output filename → schema filename
FILE_TO_SCHEMA = {
    "players.json": "players_schema.json",
    "projections.json": "projections_schema.json",
    "risk.json": "risk_schema.json",
    "insights.json": "insights_schema.json",
}


def validate_output_dir(
    output_dir: str,
    schema_dir: str = None,
) -> Tuple[bool, List[str]]:
    """
    Validate all 4 JSON files against CD schemas.

    Returns (all_valid, list_of_error_strings).
    Requires jsonschema package — returns error if not installed.
    """
    try:
        import jsonschema
    except ImportError:
        return False, ["jsonschema not installed — run: pip install jsonschema>=4.0.0"]

    schema_path = Path(schema_dir) if schema_dir else DEFAULT_SCHEMA_DIR
    out_path = Path(output_dir)
    errors = []

    for filename, schema_file in FILE_TO_SCHEMA.items():
        json_path = out_path / filename
        s_path = schema_path / schema_file

        if not json_path.exists():
            errors.append(f"{filename}: file not found at {json_path}")
            continue

        if not s_path.exists():
            errors.append(f"{schema_file}: schema not found at {s_path}")
            continue

        with open(json_path) as f:
            data = json.load(f)

        with open(s_path) as f:
            schema = json.load(f)

        validator = jsonschema.Draft7Validator(schema)
        for error in validator.iter_errors(data):
            path = " → ".join(str(p) for p in error.absolute_path) or "root"
            errors.append(f"{filename} [{path}]: {error.message}")

    valid = len(errors) == 0
    return valid, errors


def validate_cross_file_consistency(output_dir: str) -> Tuple[bool, List[str]]:
    """
    Check consistency across the 4 output files.

    Checks:
    - All 4 files exist and are non-empty arrays
    - Same set of player_ids across all files
    - All positions are CD 5-position enum values
    - projections.json sorted by fantasy_points descending
    - Risk/insight integer values in 0-100
    - No negative stat projections
    """
    out_path = Path(output_dir)
    errors = []

    # Load all 4 files
    data = {}
    for filename in FILE_TO_SCHEMA:
        json_path = out_path / filename
        if not json_path.exists():
            errors.append(f"{filename}: file not found")
            continue
        with open(json_path) as f:
            data[filename] = json.load(f)

    if len(data) < 4:
        return False, errors

    # Non-empty arrays
    for filename, arr in data.items():
        if not isinstance(arr, list) or len(arr) == 0:
            errors.append(f"{filename}: expected non-empty array, got {type(arr).__name__} len={len(arr) if isinstance(arr, list) else 'N/A'}")

    # Same player_ids across all files
    id_sets = {}
    for filename, arr in data.items():
        if isinstance(arr, list):
            id_sets[filename] = {item.get("player_id") for item in arr if isinstance(item, dict)}

    if len(id_sets) >= 2:
        ref_name = "players.json"
        ref_ids = id_sets.get(ref_name, set())
        for filename, ids in id_sets.items():
            if filename == ref_name:
                continue
            missing = ref_ids - ids
            extra = ids - ref_ids
            if missing:
                errors.append(f"{filename}: missing {len(missing)} player_ids from {ref_name}")
            if extra:
                errors.append(f"{filename}: has {len(extra)} extra player_ids not in {ref_name}")

    # Positions are CD enum
    for filename in ("players.json", "projections.json"):
        arr = data.get(filename, [])
        for i, item in enumerate(arr):
            pos = item.get("position")
            if pos and pos not in CD_POSITIONS:
                errors.append(f"{filename}[{i}]: invalid position '{pos}', expected one of {sorted(CD_POSITIONS)}")

    # projections.json sorted by fantasy_points descending
    proj = data.get("projections.json", [])
    for i in range(1, len(proj)):
        prev_fp = proj[i - 1].get("fantasy_points", 0)
        curr_fp = proj[i].get("fantasy_points", 0)
        if curr_fp > prev_fp:
            errors.append(
                f"projections.json: not sorted descending at index {i} "
                f"({prev_fp} < {curr_fp})"
            )
            break  # one error is enough

    # Risk/insight values 0-100
    int_fields = {
        "risk.json": ["injury_risk", "volatility", "minutes_risk"],
        "insights.json": ["value_score", "risk_score", "opportunity_index"],
    }
    for filename, fields in int_fields.items():
        arr = data.get(filename, [])
        for i, item in enumerate(arr):
            for field in fields:
                val = item.get(field)
                if val is not None:
                    if not isinstance(val, int):
                        errors.append(f"{filename}[{i}].{field}: expected int, got {type(val).__name__}")
                    elif val < 0 or val > 100:
                        errors.append(f"{filename}[{i}].{field}: {val} out of range 0-100")

    # Optional extended risk fields
    risk = data.get("risk.json", [])
    for i, item in enumerate(risk):
        for field in ("availability_risk", "role_risk", "composition_risk", "total_risk"):
            if field in item:
                val = item[field]
                if not isinstance(val, (int, float)):
                    errors.append(f"risk.json[{i}].{field}: expected number, got {type(val).__name__}")
                elif val < 0.0 or val > 1.0:
                    errors.append(f"risk.json[{i}].{field}: {val} out of range 0.0-1.0")
        if "risk_level" in item and item["risk_level"] not in ("Low", "Medium", "High"):
            errors.append(f"risk.json[{i}].risk_level: invalid value '{item['risk_level']}'")

    # No negative stat projections
    stat_fields = [
        "minutes", "points", "rebounds", "assists", "steals", "blocks",
        "fgm", "fga", "tpm", "tpa", "ftm", "fta", "fantasy_points",
    ]
    for i, item in enumerate(proj):
        for field in stat_fields:
            val = item.get(field)
            if val is not None and val < 0:
                errors.append(f"projections.json[{i}].{field}: negative value {val}")

    valid = len(errors) == 0
    return valid, errors
