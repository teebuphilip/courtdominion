"""
Risk Service
Loads risk data from JSON files.

Per authoritative specification (Q6):
- ONLY loads/formats JSON
- Does NOT compute
- Does NOT merge
- Does NOT score
- Does NOT correlate

All computation resides in automation.
"""

from typing import List
from shared.load_shared_outputs import load_risk


def get_all_risk_metrics() -> List[dict]:
    """
    Get all player risk metrics.
    
    Returns:
        List of risk dictionaries from risk.json
        Returns [] if file missing (per Q4)
    """
    return load_risk()


def get_risk_by_player_id(player_id: str) -> dict | None:
    """
    Get risk metrics for specific player.
    
    Args:
        player_id: Player ID to lookup
    
    Returns:
        Risk dictionary if found, None otherwise
    """
    risks = load_risk()
    
    for risk in risks:
        if risk.get("player_id") == player_id:
            return risk
    
    return None
