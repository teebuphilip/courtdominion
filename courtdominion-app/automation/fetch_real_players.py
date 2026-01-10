"""
Fetch real NBA players and team standings from NBA.com API
"""

from nba_api.stats.static import players as nba_players
from nba_api.stats.endpoints import commonallplayers, leaguestandings
import time
from typing import List, Dict
from utils import get_logger


# Team abbreviation mapping (NBA API uses different formats)
TEAM_ABBREV_MAP = {
    'Atlanta Hawks': 'ATL', 'Boston Celtics': 'BOS', 'Brooklyn Nets': 'BKN',
    'Charlotte Hornets': 'CHA', 'Chicago Bulls': 'CHI', 'Cleveland Cavaliers': 'CLE',
    'Dallas Mavericks': 'DAL', 'Denver Nuggets': 'DEN', 'Detroit Pistons': 'DET',
    'Golden State Warriors': 'GSW', 'Houston Rockets': 'HOU', 'Indiana Pacers': 'IND',
    'Los Angeles Clippers': 'LAC', 'Los Angeles Lakers': 'LAL', 'Memphis Grizzlies': 'MEM',
    'Miami Heat': 'MIA', 'Milwaukee Bucks': 'MIL', 'Minnesota Timberwolves': 'MIN',
    'New Orleans Pelicans': 'NOP', 'New York Knicks': 'NYK', 'Oklahoma City Thunder': 'OKC',
    'Orlando Magic': 'ORL', 'Philadelphia 76ers': 'PHI', 'Phoenix Suns': 'PHX',
    'Portland Trail Blazers': 'POR', 'Sacramento Kings': 'SAC', 'San Antonio Spurs': 'SAS',
    'Toronto Raptors': 'TOR', 'Utah Jazz': 'UTA', 'Washington Wizards': 'WAS'
}


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


def fetch_team_games_played() -> Dict[str, int]:
    """
    Fetch games played for each NBA team from standings.

    Returns:
        Dict mapping team abbreviation -> games played
        e.g., {'LAL': 35, 'BOS': 36, ...}
    """
    logger = get_logger("team_standings_fetcher")
    logger.section("FETCHING TEAM STANDINGS")

    try:
        standings = leaguestandings.LeagueStandings(
            season='2025-26',
            league_id='00'
        )

        time.sleep(0.6)  # Rate limiting

        df = standings.get_data_frames()[0]

        team_games = {}
        for _, row in df.iterrows():
            # Get team name and calculate games played (wins + losses)
            team_name = f"{row['TeamCity']} {row['TeamName']}"
            games_played = int(row['WINS']) + int(row['LOSSES'])

            # Map to abbreviation
            abbrev = TEAM_ABBREV_MAP.get(team_name)
            if abbrev:
                team_games[abbrev] = games_played
            else:
                # Try to extract from TeamSlug or use first 3 letters
                logger.warning(f"Unknown team: {team_name}")

        logger.info(f"Fetched standings for {len(team_games)} teams")
        return team_games

    except Exception as e:
        logger.error(f"Failed to fetch team standings: {e}")
        # Return default (assume ~40 games played mid-season)
        return {abbrev: 40 for abbrev in TEAM_ABBREV_MAP.values()}


# For testing
if __name__ == "__main__":
    players = fetch_real_players()
    print(f"Found {len(players)} active players")
    print("\nFirst 5 players:")
    for p in players[:5]:
        print(f"  {p['name']} (ID: {p['player_id']})")

    print("\n" + "="*50)
    print("Testing team standings fetch...")
    team_games = fetch_team_games_played()
    print(f"Fetched {len(team_games)} teams")
    for team, games in sorted(team_games.items())[:5]:
        print(f"  {team}: {games} games played, {82 - games} remaining")
