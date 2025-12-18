"""
Cache Builder - Fetches NBA stats and caches to file

This script:
1. Fetches stats for all ~450 active NBA players from NBA.com
2. Has robust RETRY LOGIC with exponential backoff
3. Saves to player_stats_cache.json
4. Takes 20-30 minutes (run once per day, who cares?)

Run this SEPARATELY from main automation (nightly background job).
"""

import json
import time
import random
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo


class CacheBuilder:
    """
    Builds player stats cache with retry logic.
    """
    
    def __init__(self, cache_file: Path = None):
        """Initialize cache builder"""
        if cache_file is None:
            cache_file = Path('/data/outputs/player_stats_cache.json')
        
        self.cache_file = cache_file
        self.stats_cache = {}
        self.failed_players = []
    
    def build_cache(self) -> bool:
        """
        Build complete cache for all active players.
        
        Returns:
            True if successful
        """
        print("=" * 70)
        print("  NBA STATS CACHE BUILDER")
        print("=" * 70)
        print(f"Cache file: {self.cache_file}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Get all active players
        print("Fetching active player list...")
        all_players = players.get_active_players()
        print(f"Found {len(all_players)} active NBA players")
        print()
        
        # Fetch stats for each player
        total = len(all_players)
        success_count = 0
        skip_count = 0
        
        for idx, player in enumerate(all_players, 1):
            player_id = str(player['id'])
            player_name = player['full_name']
            
            print(f"[{idx}/{total}] {player_name} (ID: {player_id})...", end=" ")
            
            # Fetch with retry
            stats = self._fetch_player_stats_with_retry(player_id, player_name)
            
            if stats:
                self.stats_cache[player_id] = stats
                success_count += 1
                print("✓")
            else:
                skip_count += 1
                self.failed_players.append((player_id, player_name))
                print("✗ (skipped)")
        
        print()
        print("=" * 70)
        print(f"Cache build complete!")
        print(f"  Success: {success_count}/{total}")
        print(f"  Skipped: {skip_count}/{total}")
        print(f"  Failed: {len(self.failed_players)}")
        print("=" * 70)
        
        # Save cache
        success = self._save_cache()
        
        if success:
            print(f"✓ Cache saved to: {self.cache_file}")
            print(f"✓ File size: {self.cache_file.stat().st_size / 1024:.1f} KB")
        
        # Log failed players
        if self.failed_players:
            print("\nFailed players:")
            for pid, pname in self.failed_players[:10]:
                print(f"  - {pname} ({pid})")
            if len(self.failed_players) > 10:
                print(f"  ... and {len(self.failed_players) - 10} more")
        
        return success
    
    def _fetch_player_stats_with_retry(
        self, 
        player_id: str, 
        player_name: str,
        max_retries: int = 3
    ) -> Optional[Dict]:
        """
        Fetch player stats with exponential backoff retry.
        
        Args:
            player_id: NBA player ID
            player_name: Player name
            max_retries: Maximum retry attempts
            
        Returns:
            Stats dict or None
        """
        for attempt in range(max_retries):
            try:
                # Fetch career stats
                career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
                
                # Random delay (2-4 seconds) to appear more human
                time.sleep(random.uniform(2.0, 4.0))
                
                df = career_stats.get_data_frames()[0]
                
                if df.empty:
                    return None
                
                # Get last 5 seasons
                recent = df.tail(5)
                total_games = recent['GP'].sum()
                
                if total_games < 50:
                    return None
                
                # Calculate per-game averages
                stats = {
                    'player_id': player_id,
                    'player_name': player_name,
                    'games_played': int(recent['GP'].mean()),
                    'minutes_per_game': round(recent['MIN'].sum() / total_games, 1),
                    'points_per_game': round(recent['PTS'].sum() / total_games, 1),
                    'rebounds_per_game': round(recent['REB'].sum() / total_games, 1),
                    'assists_per_game': round(recent['AST'].sum() / total_games, 1),
                    'steals_per_game': round(recent['STL'].sum() / total_games, 1),
                    'blocks_per_game': round(recent['BLK'].sum() / total_games, 1),
                    'turnovers_per_game': round(recent['TOV'].sum() / total_games, 1),
                    'field_goals_made': round(recent['FGM'].sum() / total_games, 1),
                    'field_goals_attempted': round(recent['FGA'].sum() / total_games, 1),
                    'field_goal_pct': round(recent['FG_PCT'].mean(), 3),
                    'three_pointers_made': round(recent['FG3M'].sum() / total_games, 1),
                    'three_pointers_attempted': round(recent['FG3A'].sum() / total_games, 1),
                    'three_point_pct': round(recent['FG3_PCT'].mean(), 3),
                    'free_throws_made': round(recent['FTM'].sum() / total_games, 1),
                    'free_throws_attempted': round(recent['FTA'].sum() / total_games, 1),
                    'free_throw_pct': round(recent['FT_PCT'].mean(), 3),
                    'confidence': min(1.0, total_games / 400.0),
                    'cached_at': datetime.now().isoformat()
                }
                
                # Get player info for age/position
                try:
                    player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
                    time.sleep(random.uniform(2.0, 4.0))
                    
                    info_df = player_info.get_data_frames()[0]
                    
                    if not info_df.empty:
                        birthdate = info_df['BIRTHDATE'].iloc[0]
                        position = info_df['POSITION'].iloc[0] or 'SF'
                        
                        # Calculate age
                        if birthdate:
                            birth_year = int(birthdate.split('-')[0])
                            age = datetime.now().year - birth_year
                            stats['age'] = age
                        
                        stats['position'] = position
                
                except Exception as e:
                    # Age/position is optional
                    pass
                
                return stats
                
            except Exception as e:
                error_msg = str(e)
                
                if attempt < max_retries - 1:
                    # Exponential backoff: 5s, 10s, 20s
                    wait_time = 5 * (2 ** attempt)
                    print(f"⚠ (retry in {wait_time}s)", end=" ")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    return None
        
        return None
    
    def _save_cache(self) -> bool:
        """Save cache to file"""
        try:
            cache_data = {
                'version': '1.0',
                'cached_at': datetime.now().isoformat(),
                'player_count': len(self.stats_cache),
                'players': self.stats_cache
            }
            
            # Atomic write
            temp_file = self.cache_file.with_suffix('.tmp')
            
            with open(temp_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            temp_file.replace(self.cache_file)
            
            return True
            
        except Exception as e:
            print(f"Error saving cache: {e}")
            return False


def build_cache(cache_file: Path = None) -> bool:
    """
    Main entry point for cache building.
    
    Args:
        cache_file: Path to cache file (optional)
        
    Returns:
        True if successful
    """
    builder = CacheBuilder(cache_file)
    return builder.build_cache()


if __name__ == "__main__":
    import sys
    
    print("\n🏀 NBA Stats Cache Builder")
    print("This will take 20-30 minutes...")
    print("Grab a coffee! ☕\n")
    
    success = build_cache()
    
    sys.exit(0 if success else 1)
