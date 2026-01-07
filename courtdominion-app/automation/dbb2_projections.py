"""
DBB2 Projection Engine - Cache-Based Version

Uses cached player stats instead of hitting NBA.com API.
FAST - reads from cache file in <1 second.

Cache is built/refreshed by build_cache.py (separate process).
"""

import json
import csv
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


# Cache file location
CACHE_FILE = Path('/data/outputs/player_stats_cache.json')

# Rookie comparables CSV location
ROOKIE_COMPARABLES_FILE = Path(__file__).parent / 'rookie_comparables.csv'


def load_cache() -> Dict:
    """
    Load player stats from cache file.
    
    Returns:
        Dict of player_id -> stats, or empty dict if no cache
    """
    if not CACHE_FILE.exists():
        print(f"WARNING: Cache file not found: {CACHE_FILE}")
        print("Run build_cache.py first to create cache!")
        return {}
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
        
        players = cache_data.get('players', {})
        cached_at = cache_data.get('cached_at', 'unknown')
        
        print(f"Loaded cache: {len(players)} players (cached at {cached_at})")
        
        return players
        
    except Exception as e:
        print(f"Error loading cache: {e}")
        return {}


def find_player_id_by_name(player_name: str, cache: Dict) -> Optional[str]:
    """
    Find player ID by name in the cache.

    Args:
        player_name: Player's full name
        cache: Pre-loaded cache dict

    Returns:
        Player ID (string) or None if not found
    """
    for player_id, stats in cache.items():
        if stats.get('player_name', '').lower() == player_name.lower():
            return player_id
    return None


def get_rookie_comparable(player_name: str, cache: Dict) -> Optional[str]:
    """
    Get comparable veteran player ID for a rookie.

    Args:
        player_name: Rookie's name
        cache: Pre-loaded cache dict

    Returns:
        Comparable player ID (string) or None if no match
    """
    if not ROOKIE_COMPARABLES_FILE.exists():
        return None

    try:
        with open(ROOKIE_COMPARABLES_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['rookie_name'].lower() == player_name.lower():
                    comparable_name = row['comparable_player']
                    # Find the comparable player's ID in cache
                    return find_player_id_by_name(comparable_name, cache)
    except Exception as e:
        print(f"Error reading rookie comparables: {e}")

    return None


def get_age_factor(age: int) -> float:
    """
    Calculate performance multiplier based on player age.
    
    Ages 20-23: Improvement phase (0.85 → 0.95)
    Ages 24-29: Prime years (1.0)
    Ages 30+: Decline phase (1.0 → 0.75)
    """
    if age < 20:
        return 0.80
    elif age <= 23:
        return 0.85 + (age - 20) * 0.025
    elif age <= 29:
        return 1.0
    elif age <= 35:
        return 1.0 - (age - 29) * 0.05
    else:
        return max(0.60, 0.75 - (age - 35) * 0.03)


def get_injury_risk_factor(age: int) -> float:
    """
    Calculate injury risk probability based on age.
    
    Returns:
        Float between 0.0-1.0 (higher = more risky)
    """
    if age < 24:
        return 0.3
    elif age <= 27:
        return 0.2
    elif age <= 30:
        return 0.3
    elif age <= 33:
        return 0.5
    else:
        return 0.7


def predict_games_played(mpg: float, age: int, position: str) -> int:
    """
    Predict games played based on minutes, age, position.
    """
    base_games = 82
    
    if mpg >= 36:
        minutes_factor = 0.85
    elif mpg >= 32:
        minutes_factor = 0.90
    elif mpg >= 28:
        minutes_factor = 0.95
    else:
        minutes_factor = 1.0
    
    injury_risk = get_injury_risk_factor(age)
    age_factor = 1.0 - injury_risk
    
    if position in ['C', 'PF']:
        position_factor = 0.92
    else:
        position_factor = 0.96
    
    predicted = int(base_games * minutes_factor * age_factor * position_factor)
    
    return max(50, min(82, predicted))


def calculate_5year_average(player_id: str, cache: Dict = None) -> Optional[Dict]:
    """
    Get 5-year average from cache.
    
    Args:
        player_id: NBA player ID (string)
        cache: Pre-loaded cache dict (optional)
        
    Returns:
        Dict with per-game averages, or None if not in cache
    """
    if cache is None:
        cache = load_cache()
    
    stats = cache.get(player_id)
    
    if not stats:
        return None
    
    return stats


def calculate_current_season_projection(player_id: str, cache: Dict = None, player_name: str = None) -> Optional[Dict]:
    """
    Calculate current season projection with age adjustments.
    Uses CACHED stats instead of hitting NBA.com.
    For rookies without NBA data, uses comparable veteran projections.

    Args:
        player_id: NBA player ID (string)
        cache: Pre-loaded cache dict (optional)
        player_name: Player name (optional, used for rookie lookup)

    Returns:
        Dict with age-adjusted projection, or None if not in cache
    """
    if cache is None:
        cache = load_cache()

    # Get baseline from cache
    baseline = cache.get(player_id)

    # If player not in cache and name provided, check for rookie comparable
    if not baseline and player_name:
        comparable_id = get_rookie_comparable(player_name, cache)
        if comparable_id:
            print(f"Using comparable for rookie {player_name}: {cache.get(comparable_id, {}).get('player_name', 'Unknown')}")
            baseline = cache.get(comparable_id)
            if baseline:
                # Mark this as a rookie projection using comparable
                player_id = comparable_id

    if not baseline:
        return None
    
    # Extract age and position from cache
    age = baseline.get('age', 25)  # Default to prime age if missing
    position = baseline.get('position', 'SF')
    
    # Apply age factor
    age_factor = get_age_factor(age)
    
    # Predict games played
    mpg = baseline['minutes_per_game']
    games = predict_games_played(mpg, age, position)
    
    # Create age-adjusted projection
    projection = {
        'player_id': player_id,
        'age': age,
        'position': position,
        'games_played': games,
        'minutes_per_game': round(baseline['minutes_per_game'] * age_factor, 1),
        'points_per_game': round(baseline['points_per_game'] * age_factor, 1),
        'rebounds_per_game': round(baseline['rebounds_per_game'] * age_factor, 1),
        'assists_per_game': round(baseline['assists_per_game'] * age_factor, 1),
        'steals_per_game': round(baseline['steals_per_game'] * age_factor, 1),
        'blocks_per_game': round(baseline['blocks_per_game'] * age_factor, 1),
        'turnovers_per_game': round(baseline['turnovers_per_game'] * age_factor, 1),
        'field_goals_made': round(baseline['field_goals_made'] * age_factor, 1),
        'field_goals_attempted': round(baseline['field_goals_attempted'] * age_factor, 1),
        'field_goal_pct': baseline['field_goal_pct'],
        'three_pointers_made': round(baseline['three_pointers_made'] * age_factor, 1),
        'three_pointers_attempted': round(baseline['three_pointers_attempted'] * age_factor, 1),
        'three_point_pct': baseline['three_point_pct'],
        'free_throws_made': round(baseline['free_throws_made'] * age_factor, 1),
        'free_throws_attempted': round(baseline['free_throws_attempted'] * age_factor, 1),
        'free_throw_pct': baseline['free_throw_pct'],
        'injury_risk': get_injury_risk_factor(age),
        'age_factor': age_factor,
        'confidence': baseline['confidence']
    }
    
    return projection


def get_all_active_players():
    """
    Get list of all players in cache.
    
    Returns:
        List of player dicts with id, name
    """
    cache = load_cache()
    
    return [{
        'player_id': pid,
        'name': stats.get('player_name', 'Unknown'),
        'is_active': True
    } for pid, stats in cache.items()]


# For testing
if __name__ == "__main__":
    print("Testing DBB2 Projection Engine (Cache-Based)...")
    
    # Load cache once
    cache = load_cache()
    
    if not cache:
        print("ERROR: No cache found. Run build_cache.py first!")
    else:
        print(f"\nCache loaded: {len(cache)} players")
        
        # Test with LeBron James (player_id: 2544)
        print("\nLeBron James Projection:")
        proj = calculate_current_season_projection('2544', cache)
        if proj:
            print(f"  Age: {proj['age']}")
            print(f"  Points: {proj['points_per_game']}")
            print(f"  Rebounds: {proj['rebounds_per_game']}")
            print(f"  Assists: {proj['assists_per_game']}")
            print(f"  Games: {proj['games_played']}")
            print(f"  Age Factor: {proj['age_factor']}")
        else:
            print("  Not in cache")
