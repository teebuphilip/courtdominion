"""
Projections Router
Provides projection data endpoints.
"""

from fastapi import APIRouter, Query
from typing import Optional
from services.projections_service import get_all_projections, sort_and_paginate_projections

router = APIRouter(tags=["projections"])


@router.get("/projections")
def get_projections(
    sort_by: Optional[str] = Query(default="fantasy_points", description="Field to sort by"),
    order: Optional[str] = Query(default="desc", description="Sort order: asc or desc"),
    limit: Optional[int] = Query(default=None, description="Number of results to return"),
    offset: Optional[int] = Query(default=0, description="Number of results to skip")
):
    """
    Get player projections with sorting and pagination.

    Args:
        sort_by: Field to sort by (default: fantasy_points)
        order: Sort order - 'asc' or 'desc' (default: desc)
        limit: Max results to return (default: all)
        offset: Number of results to skip (default: 0)

    Returns:
        List of projection dictionaries from projections.json
        Returns [] if file missing (per Q4)
    """
    all_projections = get_all_projections()

    return sort_and_paginate_projections(
        all_projections,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset
    )
