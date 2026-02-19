"""
Live-data helpers used to enrich projection export fields.
"""

from math import floor
from typing import Dict, List, Tuple

from data_collection.fetch_real_injuries import fetch_real_injuries
from data_collection.fetch_real_players import fetch_team_games_played
from engine.season import format_nba_season, get_current_nba_season_start_year


def normalize_name(name: str) -> str:
    return (
        (name or "")
        .replace(" Jr.", "")
        .replace(" Sr.", "")
        .replace(" III", "")
        .strip()
        .lower()
    )


def build_injury_lookup(injuries: List[Dict]) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
    by_id: Dict[str, Dict] = {}
    by_name: Dict[str, Dict] = {}
    for injury in injuries:
        pid = str(injury.get("player_id", "")).strip()
        if pid:
            by_id[pid] = injury
        name_key = normalize_name(injury.get("name", ""))
        if name_key:
            by_name[name_key] = injury
    return by_id, by_name


def calculate_injury_modifier(
    player_id: str,
    player_name: str,
    injury_by_id: Dict[str, Dict],
    injury_by_name: Dict[str, Dict],
) -> float:
    injury = injury_by_id.get(str(player_id)) or injury_by_name.get(normalize_name(player_name))
    if not injury:
        return 1.0

    status = str(injury.get("status", "")).lower()
    injury_type = str(injury.get("injury_type", "")).lower()
    details = str(injury.get("details", "")).lower()

    season_ending_keywords = (
        "acl",
        "out for season",
        "season-ending",
        "torn acl",
        "achilles",
        "season-ending surgery",
        "out for the season",
        "rest of the season",
    )
    if any(k in injury_type or k in details for k in season_ending_keywords):
        return 0.0

    if any(k in details for k in ("indefinitely", "no timetable", "extended absence", "multiple weeks", "out several weeks")):
        return 0.50
    if any(k in details for k in ("week", "weeks", "re-evaluated", "reevaluated", "2 weeks", "3 weeks", "4 weeks")):
        return 0.75
    if any(k in details for k in ("will not play", "ruled out", "out for", "sidelined for")) and any(
        d in details for d in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "tonight", "today")
    ):
        return 0.85
    if "day-to-day" in status or "questionable" in status:
        return 0.95
    if "probable" in status or "available" in details or "expected to play" in details:
        return 0.98
    if "out" in status and any(k in injury_type for k in ("knee", "back", "foot", "ankle")):
        return 0.0
    return 0.80


def load_live_context() -> Dict:
    season_start = get_current_nba_season_start_year()
    season = format_nba_season(season_start)
    team_games_played = fetch_team_games_played(season)
    injuries = fetch_real_injuries()
    by_id, by_name = build_injury_lookup(injuries)
    return {
        "season": season,
        "team_games_played": team_games_played,
        "injury_by_id": by_id,
        "injury_by_name": by_name,
    }


def compute_remaining_games_fields(
    player_id: str,
    player_name: str,
    team: str,
    projected_games: int,
    tpm_per_game: float,
    live_ctx: Dict,
) -> Dict[str, int]:
    team_games_played = live_ctx.get("team_games_played", {})
    injury_by_id = live_ctx.get("injury_by_id", {})
    injury_by_name = live_ctx.get("injury_by_name", {})

    games_played = int(team_games_played.get(team, 40))
    team_games_remaining = max(0, 82 - games_played)

    injury_modifier = calculate_injury_modifier(player_id, player_name, injury_by_id, injury_by_name)
    historical_availability = min(1.0, max(0.0, projected_games / 82.0))
    games_remaining_projected = floor(team_games_remaining * historical_availability * injury_modifier)
    three_pointers_made_projected = floor(max(0.0, tpm_per_game) * games_remaining_projected)

    return {
        "team_games_remaining": int(team_games_remaining),
        "games_remaining_projected": int(max(0, games_remaining_projected)),
        "three_pointers_made_projected": int(max(0, three_pointers_made_projected)),
    }
