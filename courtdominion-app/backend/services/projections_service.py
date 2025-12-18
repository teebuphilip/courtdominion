"""
Projections Service
Loads projection data from JSON files.

Per authoritative specification (Q6):
- ONLY loads/formats JSON
- Does NOT compute
- Does NOT merge
- Does NOT score
- Does NOT correlate

All computation resides in automation.
"""

from typing import List
from models.projection import Projection
from shared.load_shared_outputs import load_projections


def get_all_projections() -> List[dict]:
    """
    Get all player projections.
    
    Returns:
        List of projection dictionaries from projections.json
        Returns [] if file missing (per Q4)
    """
    return load_projections()


def get_projection_by_player_id(player_id: str) -> dict | None:
    """
    Get projection for specific player.
    
    Args:
        player_id: Player ID to lookup
    
    Returns:
        Projection dictionary if found, None otherwise
    """
    projections = load_projections()
    
    for proj in projections:
        if proj.get("player_id") == player_id:
            return proj
    
    return None
