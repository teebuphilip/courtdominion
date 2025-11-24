"""
Insights Service
Loads insight data from JSON files.

Per authoritative specification (Q6):
- ONLY loads/formats JSON
- Does NOT compute
- Does NOT merge
- Does NOT score
- Does NOT correlate

All computation resides in automation.
"""

from typing import List
from shared.load_shared_outputs import load_insights


def get_all_insights() -> List[dict]:
    """
    Get all player insights.
    
    Returns:
        List of insight dictionaries from insights.json
        Returns [] if file missing (per Q4)
    """
    return load_insights()


def get_insight_by_player_id(player_id: str) -> dict | None:
    """
    Get insights for specific player.
    
    Args:
        player_id: Player ID to lookup
    
    Returns:
        Insight dictionary if found, None otherwise
    """
    insights = load_insights()
    
    for insight in insights:
        if insight.get("player_id") == player_id:
            return insight
    
    return None
