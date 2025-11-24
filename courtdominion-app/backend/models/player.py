"""
Player Pydantic Model
Matches exact JSON schema from authoritative specification (Q1).
Backend does NOT compute these fields - only loads from JSON.
"""

from pydantic import BaseModel


class Player(BaseModel):
    """
    Player model matching players.json schema.
    
    Example:
    {
        "player_id": "2544",
        "name": "LeBron James",
        "team": "LAL",
        "position": "SF",
        "status": "active"
    }
    """
    player_id: str
    name: str
    team: str
    position: str
    status: str
