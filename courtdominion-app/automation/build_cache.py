"""
Cache Builder - Fetches NBA stats and caches to file

This script:
1. Fetches stats for all ~450 active NBA players from NBA.com
2. Has robust RETRY LOGIC with 5s → 10s → 300s backoff
3. INCREMENTAL SAVES every 10 players (never lose progress!)
4. RESUMES from where it left off if interrupted
5. Saves to /data/outputs/player_stats_cache.json

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
    Builds player stats cache with retry logic and incremental saves.
    """
    
    def __init__(self, cache_file: Path = None):
        """Initialize cache builder"""
        if cache_file is None:
            # Use shared volume location for Docker
            cache_file = Path('/data/outputs/player_stats_cache.json')
        
        self.cache_file = cache_file
        self.stats_cache = {}
        self.failed_players = []
        self.save_counter = 0
        
        # Load existing cache if it exists (resume capability)
        self._load_existing_cache()
    
    def _load_existing_cache(self):
        """Load existing cache to resume from where we left off"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                self.stats_cache = cache_data.get('players', {})
                
                if self.stats_cache:
                    print(f"📦 Found existing cache: {len(self.stats_cache)} players")
                    print(f"📦 Cached at: {cache_data.get('cached_at', 'unknown')}")
                    print(f"📦 Will skip already-cached players and continue...")
                    print()
            
            except Exception as e:
                print(f"⚠️  Could not load existing cache: {e}")
                print(f"⚠️  Starting fresh...")
                self.stats_cache = {}
    
    def build_cache(self) -> bool:
        """
        Build complete cache for all active players.
        Resumes from existing cache if found.
        
        Returns:
            True if successful
        """
        print("=" * 70)
        print("  NBA STATS CACHE BUILDER - WITH INCREMENTAL SAVES")
        print("=" * 70)
        print(f"Cache file: {self.cache_file}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Get all active players
        print("Fetching active player list...")
        all_players = players.get_active_players()
        print(f"Found {len(all_players)} active NBA players")
        
        # Filter out already-cached players
        already_cached = len(self.stats_cache)
        players_to_fetch = [p for p in all_players if str(p['id']) not in self.stats_cache]
        
        if already_cached > 0:
            print(f"Already cached: {already_cached} players")
            print(f"Remaining: {len(players_to_fetch)} players")
        
        print()
        
        # Fetch stats for remaining players
        total = len(all_players)
        success_count = already_cached
        skip_count = 0
        
        for idx, player in enumerate(all_players, 1):
            player_id = str(player['id'])
            player_name = player['full_name']
            
            # Skip if already cached
            if player_id in self.stats_cache:
                print(f"[{idx}/{total}] {player_name} (ID: {player_id})... ✓ (cached)")
                continue
            
            print(f"[{idx}/{total}] {player_name} (ID: {player_id})...", end=" ")
            
            # Fetch with retry
            stats = self._fetch_player_stats_with_retry(player_id, player_name)
            
            if stats:
                self.stats_cache[player_id] = stats
                success_count += 1
                self.save_counter += 1
                print("✓")
                
                # INCREMENTAL SAVE every 10 players
                if self.save_counter >= 10:
                    self._save_cache()
                    self.save_counter = 0
                    print(f"    💾 Progress saved ({success_count} players cached)")
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
        
        # Final save
        success = self._save_cache()
        
        if success:
            print(f"✓ Cache saved to: {self.cache_file}")
            print(f"✓ File size: {self.cache_file.stat().st_size / 1024:.1f} KB")
        
        # Log failed players
        if self.failed_players:
            print("\nFailed players (after all retries):")
            for pid, pname in self.failed_players[:10]:
                print(f"  - {pname} ({pid})")
            if len(self.failed_players) > 10:
                print(f"  ... and {len(self.failed_players) - 10} more")
        
        return success
    
    def _fetch_player_stats_with_retry(
        self, 
        player_id: str, 
        player_name: str,
        max_retries: int = 4
    ) -> Optional[Dict]:
        """
        Fetch player stats with aggressive backoff retry.
        
        Retry strategy: 5s → 10s → 300s (5 minutes!)
        
        Args:
            player_id: NBA player ID
            player_name: Player name
            max_retries: Maximum retry attempts (4 = 3 retries)
            
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
                
                # Calculate per-game averages (5-YEAR BASELINE)
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
                    # Aggressive backoff: 5s, 10s, 300s (5 minutes!)
                    if attempt == 0:
                        wait_time = 5
                    elif attempt == 1:
                        wait_time = 10
                    else:
                        wait_time = 300  # 5 minutes
                    
                    if wait_time >= 60:
                        print(f"⚠ (retry in {wait_time//60}min)", end=" ")
                    else:
                        print(f"⚠ (retry in {wait_time}s)", end=" ")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    return None
        
        return None
    
    def _save_cache(self) -> bool:
        """
        Save cache to file with atomic write.
        Called incrementally AND at end.
        """
        try:
            cache_data = {
                'version': '1.0',
                'cached_at': datetime.now().isoformat(),
                'player_count': len(self.stats_cache),
                'players': self.stats_cache
            }
            
            # Atomic write (write to temp, then rename)
            temp_file = self.cache_file.with_suffix('.tmp')
            
            with open(temp_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            # Atomic rename (won't corrupt existing cache if interrupted)
            temp_file.replace(self.cache_file)
            
            return True
            
        except Exception as e:
            print(f"⚠️  Error saving cache: {e}")
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
    
    print("\n🏀 NBA Stats Cache Builder - Incremental Save Edition")
    print("Features:")
    print("  ✓ Saves progress every 10 players")
    print("  ✓ Resumes if interrupted")
    print("  ✓ Aggressive retry: 5s → 10s → 5min")
    print("\nThis will take 30-60 minutes with NBA.com rate limits...")
    print("Grab a coffee (or lunch)! ☕🍕\n")
    
    success = build_cache()
    
    sys.exit(0 if success else 1)
