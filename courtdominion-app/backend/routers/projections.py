"""
Projections Router
Provides projection data endpoints.
"""

from fastapi import APIRouter
from services.projections_service import get_all_projections

router = APIRouter(tags=["projections"])


@router.get("/projections")
def get_projections():
    """
    Get all player projections.
    
    Returns:
        List of projection dictionaries from projections.json
        Returns [] if file missing (per Q4)
    """
    return get_all_projections()
