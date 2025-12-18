"""
JSON file loader for automation pipeline.

Loads JSON files with error handling and validation.
"""

import json
import os
from pathlib import Path
from typing import Any, List, Dict, Optional

from .logger import get_logger


class FileLoader:
    """
    JSON file loader with error handling.
    
    Features:
    - Safe loading (returns None on error)
    - Type checking
    - Missing file handling
    """
    
    def __init__(self, data_dir: Path = None, logger_name: str = "file_loader"):
        """
        Initialize file loader.
        
        Args:
            data_dir: Directory to load from (defaults to DATA_DIR env var)
            logger_name: Name for logger
        """
        if data_dir is None:
            data_dir = Path(os.getenv("DATA_DIR", "/data/outputs"))
        
        self.data_dir = Path(data_dir)
        self.logger = get_logger(logger_name)
    
    def load_json(self, filename: str) -> Optional[Any]:
        """
        Load JSON file.
        
        Args:
            filename: Name of JSON file
            
        Returns:
            Parsed JSON data, or None if error
        """
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            self.logger.warning(f"File not found: {filename}")
            return None
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.logger.debug(f"Loaded {filename}", size_bytes=filepath.stat().st_size)
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {filename}", error=str(e))
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to load {filename}", error=str(e))
            return None
    
    def load_players(self) -> List[Dict]:
        """Load players.json, returns [] if not found."""
        data = self.load_json("players.json")
        return data if isinstance(data, list) else []
    
    def load_projections(self) -> List[Dict]:
        """Load projections.json, returns [] if not found."""
        data = self.load_json("projections.json")
        return data if isinstance(data, list) else []
    
    def load_insights(self) -> List[Dict]:
        """Load insights.json, returns [] if not found."""
        data = self.load_json("insights.json")
        return data if isinstance(data, list) else []
    
    def load_risk_metrics(self) -> List[Dict]:
        """Load risk.json, returns [] if not found."""
        data = self.load_json("risk.json")
        return data if isinstance(data, list) else []
    
    def load_injuries(self) -> List[Dict]:
        """Load injuries.json, returns [] if not found."""
        data = self.load_json("injuries.json")
        return data if isinstance(data, list) else []


def create_loader(data_dir: Path = None) -> FileLoader:
    """
    Create file loader instance.
    
    Args:
        data_dir: Directory to load from
        
    Returns:
        FileLoader instance
    """
    return FileLoader(data_dir)
