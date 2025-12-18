"""
JSON schema validators for automation outputs.

Validates data against predefined schemas.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import jsonschema
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

from .logger import get_logger


class Validator:
    """
    JSON schema validator for automation outputs.
    
    Validates data against schemas defined in schemas/ directory.
    """
    
    def __init__(self, schema_dir: Path = None, logger_name: str = "validator"):
        """
        Initialize validator.
        
        Args:
            schema_dir: Directory containing JSON schemas
            logger_name: Name for logger
        """
        if schema_dir is None:
            schema_dir = Path(__file__).parent.parent / "schemas"
        
        self.schema_dir = Path(schema_dir)
        self.logger = get_logger(logger_name)
        self.schemas = {}
        
        if not JSONSCHEMA_AVAILABLE:
            self.logger.warning("jsonschema not installed, validation will be skipped")
    
    def load_schema(self, schema_name: str) -> Dict:
        """
        Load schema from file.
        
        Args:
            schema_name: Name of schema file (e.g., "players_schema.json")
            
        Returns:
            Schema dict
        """
        if schema_name in self.schemas:
            return self.schemas[schema_name]
        
        schema_path = self.schema_dir / schema_name
        
        if not schema_path.exists():
            self.logger.warning(f"Schema not found: {schema_name}")
            return {}
        
        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            self.schemas[schema_name] = schema
            self.logger.debug(f"Loaded schema: {schema_name}")
            return schema
            
        except Exception as e:
            self.logger.error(f"Failed to load schema {schema_name}", error=str(e))
            return {}
    
    def validate_data(
        self,
        data: Any,
        schema: Dict
    ) -> Tuple[bool, str]:
        """
        Validate data against schema.
        
        Args:
            data: Data to validate
            schema: JSON schema
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not JSONSCHEMA_AVAILABLE:
            return True, ""
        
        if not schema:
            self.logger.debug("No schema provided, skipping validation")
            return True, ""
        
        try:
            validate(instance=data, schema=schema)
            return True, ""
            
        except ValidationError as e:
            error_msg = f"Validation error: {e.message}"
            self.logger.error("Schema validation failed", error=error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected validation error: {str(e)}"
            self.logger.error("Validation error", error=str(e))
            return False, error_msg
    
    def validate_players(self, players: List[Dict]) -> Tuple[bool, str]:
        """Validate players data."""
        schema = self.load_schema("players_schema.json")
        return self.validate_data(players, schema)
    
    def validate_projections(self, projections: List[Dict]) -> Tuple[bool, str]:
        """Validate projections data."""
        schema = self.load_schema("projections_schema.json")
        return self.validate_data(projections, schema)
    
    def validate_insights(self, insights: List[Dict]) -> Tuple[bool, str]:
        """Validate insights data."""
        schema = self.load_schema("insights_schema.json")
        return self.validate_data(insights, schema)
    
    def validate_risk_metrics(self, risks: List[Dict]) -> Tuple[bool, str]:
        """Validate risk metrics data."""
        schema = self.load_schema("risk_schema.json")
        return self.validate_data(risks, schema)
    
    def validate_injuries(self, injuries: List[Dict]) -> Tuple[bool, str]:
        """Validate injuries data."""
        schema = self.load_schema("injuries_schema.json")
        return self.validate_data(injuries, schema)
    
    def validate_all(
        self,
        players: List[Dict] = None,
        projections: List[Dict] = None,
        insights: List[Dict] = None,
        risks: List[Dict] = None,
        injuries: List[Dict] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate all provided datasets.
        
        Args:
            players: Players data (optional)
            projections: Projections data (optional)
            insights: Insights data (optional)
            risks: Risk metrics data (optional)
            injuries: Injuries data (optional)
            
        Returns:
            Tuple of (all_valid, list_of_errors)
        """
        errors = []
        
        if players is not None:
            valid, error = self.validate_players(players)
            if not valid:
                errors.append(f"Players: {error}")
        
        if projections is not None:
            valid, error = self.validate_projections(projections)
            if not valid:
                errors.append(f"Projections: {error}")
        
        if insights is not None:
            valid, error = self.validate_insights(insights)
            if not valid:
                errors.append(f"Insights: {error}")
        
        if risks is not None:
            valid, error = self.validate_risk_metrics(risks)
            if not valid:
                errors.append(f"Risk Metrics: {error}")
        
        if injuries is not None:
            valid, error = self.validate_injuries(injuries)
            if not valid:
                errors.append(f"Injuries: {error}")
        
        return len(errors) == 0, errors


def create_validator(schema_dir: Path = None) -> Validator:
    """
    Create validator instance.
    
    Args:
        schema_dir: Directory containing schemas
        
    Returns:
        Validator instance
    """
    return Validator(schema_dir)
