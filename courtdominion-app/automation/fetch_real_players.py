"""
Fetch real NBA players from NBA.com API
"""

from nba_api.stats.static import players as nba_players
from nba_api.stats.endpoints import commonallplayers
import time
from typing import List, Dict
from utils import get_logger


class RealPlayerFetcher:
    """
    Fetches real NBA players from NBA.com API
    """
    
    def __init__(self):
        """Initialize player fetcher"""
        self.logger = get_logger("real_player_fetcher")
    
    def fetch_active_players(self) -> List[Dict]:
        """
        Fetch all active NBA players.
        
        Returns:
            List of player dicts with real data (~450 players)
        """
        self.logger.section("FETCHING REAL NBA PLAYERS")
        
        try:
            # Method 1: Static players (faster, but may be outdated)
            all_players = nba_players.get_active_players()
            
            self.logger.info(f"Fetched {len(all_players)} active players from NBA API")
            
            # Convert to our format
            player_list = []
            for p in all_players:
                player_list.append({
                    "player_id": str(p['id']),
                    "name": p['full_name'],
                    "team": "UNK",  # Not provided by static API
                    "position": "SF",  # Not provided by static API
                    "status": "active"
                })
            
            return player_list
            
        except Exception as e:
            self.logger.error(f"Failed to fetch NBA players", error=str(e))
            return []
    
    def fetch_active_players_with_teams(self) -> List[Dict]:
        """
        Fetch all active NBA players with team information.
        Uses dynamic API (slower but has team data).
        
        Returns:
            List of player dicts with team info
        """
        self.logger.section("FETCHING REAL NBA PLAYERS (WITH TEAMS)")
        
        try:
            # Method 2: commonallplayers (has team data, but slower)
            all_players_endpoint = commonallplayers.CommonAllPlayers(
                is_only_current_season=1,
                league_id='00',
                season='2025-26'
            )
            
            time.sleep(0.6)  # Rate limiting
            
            df = all_players_endpoint.get_data_frames()[0]
            
            self.logger.info(f"Fetched {len(df)} players with team data")
            
            # Convert to our format
            player_list = []
            for _, row in df.iterrows():
                # Map position (simplified mapping)
                position = self._map_position(row.get('ROSTER_STATUS', ''))
                
                player_list.append({
                    "player_id": str(row['PERSON_ID']),
                    "name": row['DISPLAY_FIRST_LAST'],
                    "team": row['TEAM_ABBREVIATION'] if row['TEAM_ABBREVIATION'] else "FA",
                    "position": position,
                    "status": "active"
                })
            
            return player_list
            
        except Exception as e:
            self.logger.error(f"Failed to fetch NBA players with teams", error=str(e))
            # Fallback to method 1
            return self.fetch_active_players()
    
    def _map_position(self, roster_status: str) -> str:
        """
        Map roster status to position (simplified).
        In reality, need separate position lookup.
        """
        # Default to SF for now
        # TODO: Add proper position mapping
        return "SF"


def fetch_real_players(include_teams: bool = False) -> List[Dict]:
    """
    Main entry point for fetching real NBA players.
    
    Args:
        include_teams: If True, fetch team data (slower)
        
    Returns:
        List of active NBA player dicts
    """
    fetcher = RealPlayerFetcher()
    
    if include_teams:
        return fetcher.fetch_active_players_with_teams()
    else:
        return fetcher.fetch_active_players()


# For testing
if __name__ == "__main__":
    players = fetch_real_players()
    print(f"Found {len(players)} active players")
    print("\nFirst 5 players:")
    for p in players[:5]:
        print(f"  {p['name']} (ID: {p['player_id']})")
