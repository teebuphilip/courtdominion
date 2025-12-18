"""
Shared JSON Loader Utility
Loads JSON files from DATA_DIR with proper error handling.

Per authoritative specification:
- Load fresh on every request (Q5 - Option B)
- Return [] on missing files (Q4 - Option B)
- Return [] on JSON parse errors
- Never crash, never raise exceptions to caller
"""

import json
import os
from typing import List, Any
from pathlib import Path


def get_data_dir() -> Path:
    """
    Get DATA_DIR from environment variable.
    Defaults to /data/outputs if not set.
    """
    data_dir = os.getenv("DATA_DIR", "/data/outputs")
    return Path(data_dir)


def load_json_file(filename: str) -> List[Any]:
    """
    Load JSON file from DATA_DIR.
    
    Args:
        filename: Name of JSON file (e.g., "players.json")
    
    Returns:
        List of parsed JSON objects, or [] if file missing/invalid
    
    Behavior per Q4:
        - Missing file → return []
        - Invalid JSON → return []
        - Empty file → return []
        - Never crash
    
    Load Strategy per Q5:
        - Loads fresh on EVERY request (no caching)
        - Ensures backend always returns latest automation outputs
    """
    data_dir = get_data_dir()
    file_path = data_dir / filename
    
    # Check if file exists
    if not file_path.exists():
        # Per Q4: Return empty list, don't crash
        return []
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Ensure we return a list
        if isinstance(data, list):
            return data
        else:
            # If JSON is not a list, wrap it or return empty
            return []
            
    except json.JSONDecodeError:
        # Per Q4: Return empty list on parse error
        return []
    except Exception:
        # Per Q4: Return empty list on any error
        return []


def load_players() -> List[Any]:
    """Load players.json"""
    return load_json_file("players.json")


def load_projections() -> List[Any]:
    """Load projections.json"""
    return load_json_file("projections.json")


def load_insights() -> List[Any]:
    """Load insights.json"""
    return load_json_file("insights.json")


def load_risk() -> List[Any]:
    """Load risk.json"""
    return load_json_file("risk.json")
