"""
Cache-based projection helper with rookie comparable fallback.
"""

import csv
import json
from pathlib import Path
from typing import Dict, Optional


def _default_cache_file() -> Path:
    docker_path = Path("/data/outputs/player_stats_cache.json")
    if docker_path.exists():
        return docker_path
    return Path(__file__).resolve().parent.parent / "output" / "player_stats_cache.json"


CACHE_FILE = _default_cache_file()
ROOKIE_COMPARABLES_FILE = Path(__file__).resolve().parent / "rookie_comparables.csv"


def load_cache() -> Dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            payload = json.load(f)
        return payload.get("players", {})
    except Exception:
        return {}


def find_player_id_by_name(player_name: str, cache: Dict) -> Optional[str]:
    lookup = player_name.lower().strip()
    for player_id, stats in cache.items():
        if str(stats.get("player_name", "")).lower().strip() == lookup:
            return player_id
    return None


def get_rookie_comparable(player_name: str, cache: Dict) -> Optional[str]:
    if not ROOKIE_COMPARABLES_FILE.exists():
        return None
    try:
        with open(ROOKIE_COMPARABLES_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["rookie_name"].lower().strip() == player_name.lower().strip():
                    return find_player_id_by_name(row["comparable_player"], cache)
    except Exception:
        return None
    return None


def get_age_factor(age: int) -> float:
    if age < 20:
        return 0.80
    if age <= 23:
        return 0.85 + (age - 20) * 0.025
    if age <= 29:
        return 1.0
    if age <= 35:
        return 1.0 - (age - 29) * 0.05
    return max(0.60, 0.75 - (age - 35) * 0.03)


def get_injury_risk_factor(age: int) -> float:
    if age < 24:
        return 0.3
    if age <= 27:
        return 0.2
    if age <= 30:
        return 0.3
    if age <= 33:
        return 0.5
    return 0.7


def predict_games_played(mpg: float, age: int, position: str) -> int:
    base_games = 82
    if mpg >= 36:
        minutes_factor = 0.85
    elif mpg >= 32:
        minutes_factor = 0.90
    elif mpg >= 28:
        minutes_factor = 0.95
    else:
        minutes_factor = 1.0

    age_factor = 1.0 - get_injury_risk_factor(age)
    position_factor = 0.92 if position in ("C", "PF") else 0.96
    return max(50, min(82, int(base_games * minutes_factor * age_factor * position_factor)))


def calculate_current_season_projection(
    player_id: str,
    cache: Optional[Dict] = None,
    player_name: Optional[str] = None,
) -> Optional[Dict]:
    if cache is None:
        cache = load_cache()

    baseline = cache.get(player_id)
    resolved_player_id = player_id

    if not baseline and player_name:
        comparable_id = get_rookie_comparable(player_name, cache)
        if comparable_id:
            baseline = cache.get(comparable_id)
            resolved_player_id = comparable_id

    if not baseline:
        return None

    age = int(baseline.get("age", 25))
    position = baseline.get("position", "SF")
    age_factor = get_age_factor(age)
    games = predict_games_played(float(baseline.get("minutes_per_game", 0.0)), age, str(position))

    return {
        "player_id": resolved_player_id,
        "age": age,
        "position": position,
        "games_played": games,
        "minutes_per_game": round(float(baseline["minutes_per_game"]) * age_factor, 1),
        "points_per_game": round(float(baseline["points_per_game"]) * age_factor, 1),
        "rebounds_per_game": round(float(baseline["rebounds_per_game"]) * age_factor, 1),
        "assists_per_game": round(float(baseline["assists_per_game"]) * age_factor, 1),
        "steals_per_game": round(float(baseline["steals_per_game"]) * age_factor, 1),
        "blocks_per_game": round(float(baseline["blocks_per_game"]) * age_factor, 1),
        "turnovers_per_game": round(float(baseline["turnovers_per_game"]) * age_factor, 1),
        "field_goals_made": round(float(baseline["field_goals_made"]) * age_factor, 1),
        "field_goals_attempted": round(float(baseline["field_goals_attempted"]) * age_factor, 1),
        "field_goal_pct": baseline.get("field_goal_pct", 0.0),
        "three_pointers_made": round(float(baseline["three_pointers_made"]) * age_factor, 1),
        "three_pointers_attempted": round(float(baseline["three_pointers_attempted"]) * age_factor, 1),
        "three_point_pct": baseline.get("three_point_pct", 0.0),
        "free_throws_made": round(float(baseline["free_throws_made"]) * age_factor, 1),
        "free_throws_attempted": round(float(baseline["free_throws_attempted"]) * age_factor, 1),
        "free_throw_pct": baseline.get("free_throw_pct", 0.0),
        "injury_risk": get_injury_risk_factor(age),
        "age_factor": age_factor,
        "confidence": baseline.get("confidence", 0.5),
    }
