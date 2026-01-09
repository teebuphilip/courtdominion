"""
Fetch real NBA injuries from ESPN API
"""

import requests
from typing import List, Dict
from utils import get_logger


class ESPNInjuryFetcher:
    """
    Fetches real NBA injuries from ESPN's free API
    """
    
    ESPN_INJURY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
    
    def __init__(self):
        """Initialize injury fetcher"""
        self.logger = get_logger("espn_injury_fetcher")
    
    def fetch_injuries(self) -> List[Dict]:
        """
        Fetch current NBA injuries from ESPN.
        
        Returns:
            List of injury dicts with real data
        """
        self.logger.section("FETCHING REAL NBA INJURIES")
        
        try:
            response = requests.get(self.ESPN_INJURY_URL, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # ESPN structure: {"injuries": [team_data, ...], "season": {...}, ...}
            # Each team_data has: {"id": "1", "displayName": "Team Name", "injuries": [...]}
            teams_data = data.get('injuries', [])

            if not teams_data:
                self.logger.warning(f"No injuries in ESPN response. Keys: {list(data.keys())}")
                return []

            injuries = []
            total_injury_records = 0

            # Iterate through each team's injury data
            for team_data in teams_data:
                team_name = team_data.get('displayName', 'Unknown Team')
                team_injuries = team_data.get('injuries', [])
                total_injury_records += len(team_injuries)

                for injury_data in team_injuries:
                    # Extract athlete info
                    athlete = injury_data.get('athlete', {})

                    # Extract injury details
                    status = injury_data.get('status', 'Unknown')
                    short_comment = injury_data.get('shortComment', '')
                    long_comment = injury_data.get('longComment', '')

                    # Parse injury type from comments (e.g., "ankle", "knee", "hamstring")
                    injury_type = self._parse_injury_type(short_comment, long_comment)

                    injuries.append({
                        "player_id": str(athlete.get('id', '')) if athlete.get('id') else '',
                        "name": athlete.get('displayName', 'Unknown'),
                        "team": self._parse_team_abbrev(team_name),
                        "status": status,
                        "details": short_comment if short_comment else long_comment[:200],
                        "injury_type": injury_type,
                        "return_date": injury_data.get('date')  # ISO format or None
                    })

            self.logger.info(f"Processing {total_injury_records} injury records from ESPN")
            self.logger.info(f"Fetched {len(injuries)} current injuries from ESPN")
            
            return injuries
            
        except requests.exceptions.Timeout:
            self.logger.error(f"ESPN API request timed out")
            return []
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch injuries from ESPN", error=str(e))
            return []
            
        except Exception as e:
            self.logger.error(f"Unexpected error fetching injuries", error=str(e))
            return []

    def _parse_injury_type(self, short_comment: str, long_comment: str) -> str:
        """
        Parse injury type from comments (ankle, knee, hamstring, etc.)

        Args:
            short_comment: Short injury description
            long_comment: Long injury description

        Returns:
            Injury type string
        """
        combined = (short_comment + " " + long_comment).lower()

        # Common injury types
        injury_keywords = [
            'ankle', 'knee', 'hamstring', 'calf', 'groin', 'back',
            'shoulder', 'wrist', 'hand', 'finger', 'foot', 'achilles',
            'quad', 'hip', 'elbow', 'concussion', 'illness', 'rest',
            'personal', 'suspension', 'acl', 'mcl', 'meniscus'
        ]

        for keyword in injury_keywords:
            if keyword in combined:
                return keyword.capitalize()

        return "Other"

    def _parse_team_abbrev(self, team_name: str) -> str:
        """
        Convert team name to abbreviation.

        Args:
            team_name: Full team name (e.g., "Los Angeles Lakers")

        Returns:
            Team abbreviation (e.g., "LAL")
        """
        team_map = {
            'Atlanta Hawks': 'ATL',
            'Boston Celtics': 'BOS',
            'Brooklyn Nets': 'BKN',
            'Charlotte Hornets': 'CHA',
            'Chicago Bulls': 'CHI',
            'Cleveland Cavaliers': 'CLE',
            'Dallas Mavericks': 'DAL',
            'Denver Nuggets': 'DEN',
            'Detroit Pistons': 'DET',
            'Golden State Warriors': 'GSW',
            'Houston Rockets': 'HOU',
            'Indiana Pacers': 'IND',
            'Los Angeles Clippers': 'LAC',
            'Los Angeles Lakers': 'LAL',
            'Memphis Grizzlies': 'MEM',
            'Miami Heat': 'MIA',
            'Milwaukee Bucks': 'MIL',
            'Minnesota Timberwolves': 'MIN',
            'New Orleans Pelicans': 'NOP',
            'New York Knicks': 'NYK',
            'Oklahoma City Thunder': 'OKC',
            'Orlando Magic': 'ORL',
            'Philadelphia 76ers': 'PHI',
            'Phoenix Suns': 'PHX',
            'Portland Trail Blazers': 'POR',
            'Sacramento Kings': 'SAC',
            'San Antonio Spurs': 'SAS',
            'Toronto Raptors': 'TOR',
            'Utah Jazz': 'UTA',
            'Washington Wizards': 'WAS'
        }

        return team_map.get(team_name, 'UNK')


def fetch_real_injuries() -> List[Dict]:
    """
    Main entry point for fetching real NBA injuries.
    
    Returns:
        List of current injury dicts
    """
    fetcher = ESPNInjuryFetcher()
    return fetcher.fetch_injuries()


# For testing
if __name__ == "__main__":
    injuries = fetch_real_injuries()
    print(f"Found {len(injuries)} current injuries")
    print("\nFirst 5 injuries:")
    for inj in injuries[:5]:
        print(f"  {inj['name']} ({inj['team']}) - {inj['status']} - {inj['injury_type']}")
