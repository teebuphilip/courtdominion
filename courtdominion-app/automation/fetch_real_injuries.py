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
            
            # ESPN structure: {"injuries": [...], "season": {...}, ...}
            injury_list = data.get('injuries', [])
            
            if not injury_list:
                self.logger.warning(f"No injuries in ESPN response. Keys: {list(data.keys())}")
                return []
            
            self.logger.info(f"Processing {len(injury_list)} injury records from ESPN")
            
            injuries = []
            
            for injury_data in injury_list:
                # Extract athlete info
                athlete = injury_data.get('athlete', {})
                team_info = injury_data.get('team', {})
                
                injuries.append({
                    "player_id": str(athlete.get('id', '')),
                    "name": athlete.get('displayName', 'Unknown'),
                    "team": team_info.get('abbreviation', 'UNK'),
                    "status": injury_data.get('status', 'Unknown'),
                    "injury_type": injury_data.get('type', 'Unknown'),
                    "return_date": injury_data.get('date')  # ISO format or None
                })
            
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
