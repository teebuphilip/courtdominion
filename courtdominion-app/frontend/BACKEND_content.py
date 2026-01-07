"""
Content Router for CourtDominion Backend
Add this file to: courtdominion-app/backend/routers/content.py

Then add to main.py:
    from routers import content
    app.include_router(content.router)
"""

from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter()

DEFAULT_CONTENT = {
    "homepage": {
        "headline": "NBA Fantasy Projections Built Different",
        "subheadline": "Risk analysis, volatility metrics, and waiver wire intelligence",
        "value_props": [
            "Risk-adjusted projections you can trust",
            "Volatility indicators for every player",
            "Daily waiver wire insights"
        ],
        "cta_primary": "View Today's Projections",
        "cta_secondary": "Get Daily Insights"
    },
    "projections_page": {
        "title": "Daily Projections",
        "subtitle": "398 NBA players with risk-adjusted fantasy points",
        "email_gate": {
            "headline": "Want the full projections list?",
            "subheadline": "Get daily NBA fantasy insights delivered to your inbox",
            "cta": "Get Free Access"
        }
    },
    "insights_page": {
        "title": "Waiver Wire Insights",
        "subtitle": "Deep sleepers and value plays for your league",
        "description": "AI-powered waiver wire recommendations updated daily"
    },
    "player_detail": {
        "stats_title": "Season Averages",
        "risk_title": "Risk Analysis",
        "insight_title": "Fantasy Outlook"
    }
}

@router.get("/api/content")
async def get_content():
    """
    Return dynamic content for frontend pages.
    
    Checks for content.json file first (for dynamic updates),
    falls back to DEFAULT_CONTENT if file doesn't exist.
    
    This allows you to update copy without redeploying frontend:
    1. Edit /data/outputs/content.json on backend
    2. Restart backend
    3. Frontend fetches new content
    """
    content_file = Path("/data/outputs/content.json")
    
    # Try to load from file first (for production flexibility)
    if content_file.exists():
        try:
            with open(content_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupt, fall back to default
            pass
    
    # Return default content
    return DEFAULT_CONTENT
