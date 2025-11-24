"""
JSON file writer for automation outputs.

Writes JSON files to DATA_DIR with atomic writes and validation.
"""

import json
import os
from pathlib import Path
from typing import Any, List, Dict
from datetime import datetime

from .logger import get_logger


class FileWriter:
    """
    JSON file writer with atomic writes and error handling.
    
    Features:
    - Atomic writes (write to temp, then rename)
    - Directory creation
    - Pretty-printed JSON
    - Error recovery
    """
    
    def __init__(self, data_dir: Path = None, logger_name: str = "file_writer"):
        """
        Initialize file writer.
        
        Args:
            data_dir: Directory for output files (defaults to DATA_DIR env var)
            logger_name: Name for logger
        """
        if data_dir is None:
            data_dir = Path(os.getenv("DATA_DIR", "/data/outputs"))
        
        self.data_dir = Path(data_dir)
        self.logger = get_logger(logger_name)
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"File writer initialized", data_dir=str(self.data_dir))
    
    def write_json(
        self,
        filename: str,
        data: Any,
        indent: int = 2
    ) -> bool:
        """
        Write data to JSON file with atomic write.
        
        Args:
            filename: Name of JSON file (e.g., "players.json")
            data: Data to write (must be JSON-serializable)
            indent: JSON indentation (default: 2)
            
        Returns:
            True if successful, False otherwise
        """
        filepath = self.data_dir / filename
        temp_filepath = self.data_dir / f".{filename}.tmp"
        
        try:
            self.logger.debug(f"Writing {filename}", records=len(data) if isinstance(data, list) else "N/A")
            
            # Write to temporary file first
            with open(temp_filepath, 'w') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            
            # Atomic rename
            temp_filepath.replace(filepath)
            
            self.logger.info(f"Successfully wrote {filename}", size_bytes=filepath.stat().st_size)
            return True
            
        except TypeError as e:
            self.logger.error(f"Failed to serialize {filename}", error=f"Not JSON-serializable: {str(e)}")
            return False
            
        except IOError as e:
            self.logger.error(f"Failed to write {filename}", error=f"IO error: {str(e)}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to write {filename}", error=f"Unexpected: {str(e)}")
            return False
        
        finally:
            # Cleanup temp file if it exists
            if temp_filepath.exists():
                try:
                    temp_filepath.unlink()
                except:
                    pass
    
    def write_players(self, players: List[Dict]) -> bool:
        """
        Write players.json.
        
        Args:
            players: List of player dicts
            
        Returns:
            True if successful
        """
        return self.write_json("players.json", players)
    
    def write_projections(self, projections: List[Dict]) -> bool:
        """
        Write projections.json.
        
        Args:
            projections: List of projection dicts
            
        Returns:
            True if successful
        """
        return self.write_json("projections.json", projections)
    
    def write_insights(self, insights: List[Dict]) -> bool:
        """
        Write insights.json.
        
        Args:
            insights: List of insight dicts
            
        Returns:
            True if successful
        """
        return self.write_json("insights.json", insights)
    
    def write_risk_metrics(self, risks: List[Dict]) -> bool:
        """
        Write risk.json.
        
        Args:
            risks: List of risk metric dicts
            
        Returns:
            True if successful
        """
        return self.write_json("risk.json", risks)
    
    def write_injuries(self, injuries: List[Dict]) -> bool:
        """
        Write injuries.json.
        
        Args:
            injuries: List of injury dicts
            
        Returns:
            True if successful
        """
        return self.write_json("injuries.json", injuries)
    
    def write_manifest(self, manifest: Dict) -> bool:
        """
        Write pipeline manifest with metadata.
        
        Args:
            manifest: Manifest data
            
        Returns:
            True if successful
        """
        # Add timestamp
        manifest["generated_at"] = datetime.utcnow().isoformat()
        return self.write_json("manifest.json", manifest)


def create_writer(data_dir: Path = None) -> FileWriter:
    """
    Create file writer instance.
    
    Args:
        data_dir: Output directory (defaults to DATA_DIR env var)
        
    Returns:
        FileWriter instance
    """
    return FileWriter(data_dir)
