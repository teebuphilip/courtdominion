"""
Projection Pydantic Model
Matches exact JSON schema from authoritative specification (Q1).
Backend does NOT compute these fields - only loads from JSON.
"""

from pydantic import BaseModel


class Projection(BaseModel):
    """
    Projection model matching projections.json schema.
    
    Example:
    {
        "player_id": "2544",
        "name": "LeBron James",
        "team": "LAL",
        "position": "SF",
        "minutes": 34.5,
        "usage_rate": 28.4,
        "points": 25.3,
        "rebounds": 7.2,
        "assists": 7.8,
        "steals": 1.3,
        "blocks": 0.8,
        "turnovers": 3.2,
        "fg_pct": 0.523,
        "three_pt_pct": 0.378,
        "ft_pct": 0.711,
        "fgm": 9.8,
        "fga": 18.7,
        "tpm": 2.1,
        "tpa": 5.6,
        "ftm": 3.7,
        "fta": 5.2,
        "fantasy_points": 48.7,
        "ceiling": 62.1,
        "floor": 36.4,
        "consistency": 81
    }
    """
    player_id: str
    name: str
    team: str
    position: str
    
    # Minutes and usage
    minutes: float
    usage_rate: float
    
    # Core stats
    points: float
    rebounds: float
    assists: float
    steals: float
    blocks: float
    turnovers: float
    
    # Shooting percentages
    fg_pct: float
    three_pt_pct: float
    ft_pct: float
    
    # Made/Attempted stats
    fgm: float
    fga: float
    tpm: float
    tpa: float
    ftm: float
    fta: float
    
    # Fantasy metrics
    fantasy_points: float
    ceiling: float
    floor: float
    consistency: int
