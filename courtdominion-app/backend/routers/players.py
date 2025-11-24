"""
Players Router
Provides player listing and detail endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import List
from shared.load_shared_outputs import load_players

router = APIRouter(tags=["players"])


@router.get("/players")
def get_players():
    """
    Get all players.
    
    Returns:
        List of player dictionaries from players.json
        Returns [] if file missing (per Q4)
    """
    return load_players()


@router.get("/player/{player_id}")
def get_player(player_id: str):
    """
    Get specific player by ID.
    
    Args:
        player_id: Player ID to lookup
    
    Returns:
        Player dictionary if found
    
    Raises:
        HTTPException 404 if player not found
    """
    players = load_players()
    
    for player in players:
        if player.get("player_id") == player_id:
            return player
    
    # Return 404 if player not found
    raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
