"""
Helpers for resolving the active NBA season.
"""

from datetime import date
from typing import Optional


def get_current_nba_season_start_year(today: Optional[date] = None) -> int:
    """
    Return NBA season start year for a given date.

    NBA regular seasons roll over in October:
    - Oct-Dec 2025 => 2025-26 season (start year 2025)
    - Jan-Sep 2026 => 2025-26 season (start year 2025)
    """
    if today is None:
        today = date.today()
    return today.year if today.month >= 10 else today.year - 1


def format_nba_season(start_year: int) -> str:
    """Format start year as NBA season string, e.g. 2025 -> '2025-26'."""
    return f"{start_year}-{str((start_year + 1) % 100).zfill(2)}"
