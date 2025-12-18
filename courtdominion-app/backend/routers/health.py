"""
Health Router
Provides health check endpoint.
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """
    Health check endpoint.
    
    Returns:
        Status OK with timestamp
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }
