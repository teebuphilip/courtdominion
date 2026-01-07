"""
Retry Failed Players Script

Detects players that failed during cache building and retries with exponential backoff.
Improves data quality by recovering from transient NBA.com API failures.
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Cache file location
CACHE_FILE = Path('/data/outputs/player_stats_cache.json')


def load_cache() -> Optional[Dict]:
    """Load the player stats cache."""
    if not CACHE_FILE.exists():
        print(f"ERROR: Cache file not found: {CACHE_FILE}")
        return None

    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load cache: {e}")
        return None


def find_failed_players(cache_data: Dict) -> List[str]:
    """
    Find players that failed during cache building.

    Failed players are marked with confidence = 0.0 or missing required stats.

    Returns:
        List of player IDs that failed
    """
    failed_players = []

    players = cache_data.get('players', {})

    for player_id, stats in players.items():
        # Check if player has failed indicators
        if stats.get('confidence', 1.0) == 0.0:
            failed_players.append(player_id)
        elif stats.get('points_per_game', -1) < 0:
            failed_players.append(player_id)

    return failed_players


def retry_player(player_id: str, max_retries: int = 5) -> Optional[Dict]:
    """
    Retry fetching a failed player with exponential backoff.

    Args:
        player_id: NBA player ID
        max_retries: Maximum retry attempts

    Returns:
        Player stats dict if successful, None if failed
    """
    from build_cache import fetch_player_stats

    for attempt in range(1, max_retries + 1):
        try:
            print(f"  Attempt {attempt}/{max_retries} for player {player_id}...")

            # Try to fetch player stats
            stats = fetch_player_stats(player_id)

            if stats and stats.get('confidence', 0) > 0:
                print(f"  ✓ Success on attempt {attempt}")
                return stats

            # Exponential backoff: 1s, 2s, 4s, 8s, 16s
            if attempt < max_retries:
                wait_time = 2 ** (attempt - 1)
                print(f"  ✗ Failed, waiting {wait_time}s before retry...")
                time.sleep(wait_time)

        except Exception as e:
            print(f"  ✗ Error on attempt {attempt}: {e}")

            if attempt < max_retries:
                wait_time = 2 ** (attempt - 1)
                print(f"  Waiting {wait_time}s before retry...")
                time.sleep(wait_time)

    print(f"  ✗ All retries failed for player {player_id}")
    return None


def update_cache(cache_data: Dict, player_id: str, stats: Dict) -> None:
    """Update cache with newly fetched player stats."""
    cache_data['players'][player_id] = stats
    cache_data['last_retry'] = datetime.utcnow().isoformat()


def save_cache(cache_data: Dict) -> bool:
    """Save updated cache to file."""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
        return True
    except Exception as e:
        print(f"ERROR: Failed to save cache: {e}")
        return False


def main(dry_run: bool = False):
    """
    Main entry point for retry script.

    Args:
        dry_run: If True, only detect failures without retrying
    """
    print("=" * 60)
    print("RETRY FAILED PLAYERS")
    print("=" * 60)
    print()

    # Load cache
    cache_data = load_cache()
    if not cache_data:
        print("ERROR: Cannot proceed without cache")
        sys.exit(1)

    # Find failed players
    failed_players = find_failed_players(cache_data)

    print(f"Found {len(failed_players)} failed players")

    if len(failed_players) == 0:
        print("✓ No failed players detected. Cache is healthy!")
        sys.exit(0)

    if dry_run:
        print("\nDry run mode - showing failures without retrying:")
        for player_id in failed_players:
            player_name = cache_data['players'][player_id].get('player_name', 'Unknown')
            print(f"  - {player_name} (ID: {player_id})")
        sys.exit(0)

    # Retry each failed player
    print("\nRetrying failed players...")
    print()

    success_count = 0

    for i, player_id in enumerate(failed_players, 1):
        player_name = cache_data['players'][player_id].get('player_name', 'Unknown')
        print(f"[{i}/{len(failed_players)}] Retrying: {player_name} (ID: {player_id})")

        stats = retry_player(player_id)

        if stats:
            update_cache(cache_data, player_id, stats)
            success_count += 1
            print()
        else:
            print(f"  WARNING: Could not recover data for {player_name}")
            print()

    # Save updated cache
    if success_count > 0:
        print("=" * 60)
        print(f"Saving cache with {success_count} recovered players...")

        if save_cache(cache_data):
            print(f"✓ Cache updated successfully!")
            print(f"  Recovered: {success_count}/{len(failed_players)} players")
        else:
            print("✗ Failed to save cache")
            sys.exit(1)
    else:
        print("=" * 60)
        print("No players were recovered. Cache unchanged.")

    print("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    # Check for --dry-run flag
    dry_run = "--dry-run" in sys.argv

    main(dry_run=dry_run)
