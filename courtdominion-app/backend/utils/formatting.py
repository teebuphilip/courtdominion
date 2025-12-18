"""
Formatting Utilities
Placeholder for future formatting functions.
"""

def format_percentage(value: float) -> str:
    """Format float as percentage string."""
    return f"{value * 100:.1f}%"


def format_stat(value: float, decimals: int = 1) -> str:
    """Format stat with specified decimal places."""
    return f"{value:.{decimals}f}"
