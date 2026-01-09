"""
Insights Router
Provides insights, risk metrics, and lineup suggestion endpoints.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from services.insights_service import get_all_insights
from services.risk_service import get_all_risk_metrics

router = APIRouter(tags=["insights"])


@router.get("/insights")
def get_insights(category: str = "all"):
    """
    Get player insights filtered by category.

    Args:
        category: Filter category (all, high_value, sleepers, avoid)

    Returns:
        List of insight dictionaries from insights.json
        Returns [] if file missing (per Q4)
    """
    from services.insights_service import filter_insights_by_category

    all_insights = get_all_insights()

    if category == "all":
        return all_insights

    return filter_insights_by_category(all_insights, category)


@router.get("/risk-metrics")
def get_risk_metrics():
    """
    Get all player risk metrics.
    
    Returns:
        List of risk dictionaries from risk.json
        Returns [] if file missing (per Q4)
    """
    return get_all_risk_metrics()


# Request model for lineup suggestions
class LineupRequest(BaseModel):
    roster: List[dict]
    settings: dict


@router.post("/lineup-suggestions")
def get_lineup_suggestions(request: LineupRequest):
    """
    Get lineup suggestions (STUB for Phase 2).
    
    Per authoritative specification (Q7):
    This is a stub endpoint that returns a Phase 2 message.
    Actual lineup optimization logic will be implemented in Phase 2.
    
    Args:
        request: Lineup request with roster and settings
    
    Returns:
        Stub response indicating Phase 2 availability
    """
    return {
        "message": "Lineup suggestions will be available in Phase 2.",
        "suggestions": []
    }
