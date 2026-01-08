"""
Content Router
Provides dynamic content API for marketing copy.
"""

from fastapi import APIRouter, HTTPException
import json
import os

router = APIRouter(tags=["content"])


@router.get("/api/content")
def get_content():
    """
    Get dynamic marketing content.

    Reads from /data/outputs/content.json (automation-generated) first,
    falls back to backend/data/content.json (packaged default).
    Never errors if missing - returns fallback content.

    Returns:
        JSON content for frontend marketing pages
    """
    # Try /data/outputs/content.json first (automation-generated, editable without redeploy)
    data_dir = os.getenv("DATA_DIR", "/data/outputs")
    dynamic_content_path = os.path.join(data_dir, "content.json")

    if os.path.exists(dynamic_content_path):
        try:
            with open(dynamic_content_path, 'r') as f:
                content = json.load(f)
            return content
        except (json.JSONDecodeError, Exception):
            # Fall through to packaged content
            pass

    # Fallback to packaged content.json
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        content_path = os.path.join(backend_dir, "data", "content.json")

        with open(content_path, 'r') as f:
            content = json.load(f)

        return content
    except (FileNotFoundError, json.JSONDecodeError):
        # Return minimal valid content if all else fails
        return {
            "homepage": {
                "headline": "NBA Fantasy Projections",
                "subheadline": "Daily insights and analytics",
                "value_props": [],
                "cta_primary": "View Projections",
                "cta_secondary": "Learn More"
            }
        }
