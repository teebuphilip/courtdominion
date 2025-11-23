"""
Risk and Insight Pydantic Models
Matches exact JSON schemas from authoritative specification (Q1).
Backend does NOT compute these fields - only loads from JSON.
"""

from pydantic import BaseModel


class Risk(BaseModel):
    """
    Risk model matching risk.json schema.
    
    Example:
    {
        "player_id": "2544",
        "injury_risk": 12,
        "volatility": 9,
        "minutes_risk": 5
    }
    """
    player_id: str
    injury_risk: int
    volatility: int
    minutes_risk: int


class Insight(BaseModel):
    """
    Insight model matching insights.json schema.
    
    Example:
    {
        "player_id": "2544",
        "value_score": 86,
        "risk_score": 14,
        "opportunity_index": 72,
        "notes": "High consistency, elite usage"
    }
    """
    player_id: str
    value_score: int
    risk_score: int
    opportunity_index: int
    notes: str
