"""
Injury data ingestion module - REAL ESPN DATA.

Fetches injury data from ESPN's free API and normalizes fields.
"""

from typing import List, Dict
from utils import get_logger

# Import real injury fetcher
from fetch_real_injuries import fetch_real_injuries


class InjuryIngestor:
    """
    Ingests injury data from ESPN API.
    
    Features:
    - Fetches from ESPN free API
    - Normalizes data format
    - Handles API failures gracefully
    - Returns structured injury data
    """
    
    def __init__(self):
        """Initialize injury ingestor"""
        self.logger = get_logger("injury_ingestor")
    
    def fetch_injuries(self) -> List[Dict]:
        """
        Fetch current NBA injuries from ESPN API.
        
        Returns:
            List of injury dicts with normalized fields
        """
        self.logger.section("FETCHING REAL INJURIES (ESPN)")
        
        # Fetch from ESPN API
        injuries = fetch_real_injuries()
        
        if not injuries:
            self.logger.warning("ESPN API returned no injuries (or failed)")
            return []
        
        self.logger.info(f"Fetched {len(injuries)} injury records from ESPN")
        return injuries
    
    def validate_injuries(self, injuries: List[Dict]) -> bool:
        """
        Validate injury data structure.
        
        Args:
            injuries: List of injury dicts
            
        Returns:
            True if valid
        """
        required_fields = ["player_id", "name", "team", "status", "injury_type", "return_date"]
        
        for injury in injuries:
            if not all(field in injury for field in required_fields):
                self.logger.error(f"Invalid injury record missing fields", player_id=injury.get("player_id"))
                return False
        
        return True


def ingest_injuries() -> List[Dict]:
    """
    Main entry point for injury ingestion - REAL ESPN DATA.
    
    Returns:
        List of injury dicts from ESPN
    """
    ingestor = InjuryIngestor()
    injuries = ingestor.fetch_injuries()
    
    if ingestor.validate_injuries(injuries):
        return injuries
    else:
        return []
