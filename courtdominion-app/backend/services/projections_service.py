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

from typing import List, Optional
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


def sort_and_paginate_projections(
    projections: List[dict],
    sort_by: str = "fantasy_points",
    order: str = "desc",
    limit: Optional[int] = None,
    offset: int = 0
) -> List[dict]:
    """
    Sort and paginate projections.

    Args:
        projections: List of projection dicts
        sort_by: Field to sort by
        order: 'asc' or 'desc'
        limit: Max results to return (None = all)
        offset: Number to skip

    Returns:
        Sorted and paginated list of projections
    """
    # Sort projections
    reverse = (order.lower() == "desc")

    try:
        sorted_projections = sorted(
            projections,
            key=lambda x: x.get(sort_by, 0) if isinstance(x.get(sort_by, 0), (int, float)) else 0,
            reverse=reverse
        )
    except Exception:
        # If sorting fails, return unsorted
        sorted_projections = projections

    # Apply pagination
    if limit is not None:
        end = offset + limit
        return sorted_projections[offset:end]
    else:
        return sorted_projections[offset:]
