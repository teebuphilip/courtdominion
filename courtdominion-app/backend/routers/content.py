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

    Returns:
        JSON content for frontend marketing pages
    """
    try:
        # Get the path to content.json
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        content_path = os.path.join(backend_dir, "data", "content.json")

        # Read and return content
        with open(content_path, 'r') as f:
            content = json.load(f)

        return content
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Content file not found"
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Invalid content file format"
        )
