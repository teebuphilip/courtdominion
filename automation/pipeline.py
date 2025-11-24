"""
Main automation pipeline orchestrator.

Coordinates all data generation steps:
1. Fetch injuries
2. Generate projections
3. Generate insights
4. Generate risk metrics
5. Validate all outputs
6. Write to DATA_DIR
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from utils import (
    get_logger,
    create_writer,
    create_validator
)

from ingest_injuries import ingest_injuries
from projection_generator import generate_projections
from insights_generator import generate_insights
from risk_metrics import generate_risk_metrics


class AutomationPipeline:
    """
    Main automation pipeline.
    
    Orchestrates all data generation and validation steps.
    Never crashes - always fails gracefully.
    """
    
    def __init__(self, data_dir: Path = None):
        """
        Initialize pipeline.
        
        Args:
            data_dir: Output directory (defaults to DATA_DIR env var)
        """
        if data_dir is None:
            data_dir = Path(os.getenv("DATA_DIR", "/data/outputs"))
        
        self.data_dir = Path(data_dir)
        self.logger = get_logger("pipeline", log_dir=self.data_dir / "logs")
        self.writer = create_writer(data_dir)
        self.validator = create_validator()
        
        self.logger.section("COURTDOMINION AUTOMATION PIPELINE")
        self.logger.info(f"Data directory: {self.data_dir}")
        self.logger.info(f"Started at: {datetime.utcnow().isoformat()}")
    
    def run(self) -> bool:
        """
        Run complete automation pipeline.
        
        Steps:
        1. Fetch injuries
        2. Generate mock players (Phase 1)
        3. Generate projections
        4. Generate risk metrics
        5. Generate insights
        6. Validate all outputs
        7. Write to DATA_DIR
        
        Returns:
            True if successful, False if any step failed
        """
        try:
            # Step 1: Fetch injuries
            injuries = self._fetch_injuries()
            
            # Step 2: Generate mock players (Phase 1)
            # In Phase 2, this will fetch from database
            players = self._generate_mock_players()
            
            # Step 3: Generate projections
            projections = self._generate_projections(players, injuries)
            
            # Step 4: Generate risk metrics
            risk_metrics = self._generate_risk_metrics(projections, injuries)
            
            # Step 5: Generate insights
            insights = self._generate_insights(projections, risk_metrics)
            
            # Step 6: Validate all outputs
            validation_success = self._validate_outputs(
                players=players,
                projections=projections,
                insights=insights,
                risks=risk_metrics,
                injuries=injuries
            )
            
            if not validation_success:
                self.logger.error("Validation failed, but continuing to write outputs")
            
            # Step 7: Write all outputs
            write_success = self._write_outputs(
                players=players,
                projections=projections,
                insights=insights,
                risks=risk_metrics,
                injuries=injuries
            )
            
            if write_success:
                self.logger.section("PIPELINE COMPLETED SUCCESSFULLY")
                self._write_manifest(success=True)
                return True
            else:
                self.logger.error("Pipeline completed with errors")
                self._write_manifest(success=False)
                return False
                
        except Exception as e:
            self.logger.error(f"Pipeline failed with exception", error=str(e))
            self._write_manifest(success=False, error=str(e))
            return False
    
    def _fetch_injuries(self) -> List[Dict]:
        """
        Fetch injury data.
        
        Returns:
            List of injury dicts (empty list if failed)
        """
        try:
            injuries = ingest_injuries()
            self.logger.info(f"Fetched {len(injuries)} injuries")
            return injuries
        except Exception as e:
            self.logger.error(f"Failed to fetch injuries", error=str(e))
            return []
    
    def _generate_mock_players(self) -> List[Dict]:
        """
        Generate mock player data for Phase 1.
        
        Phase 2 will fetch real player data from database.
        
        Returns:
            List of player dicts
        """
        self.logger.section("GENERATING MOCK PLAYERS")
        
        mock_players = [
            {
                "player_id": "2544",
                "name": "LeBron James",
                "team": "LAL",
                "position": "SF",
                "status": "active"
            },
            {
                "player_id": "201935",
                "name": "James Harden",
                "team": "LAC",
                "position": "SG",
                "status": "active"
            },
            {
                "player_id": "203076",
                "name": "Anthony Davis",
                "team": "LAL",
                "position": "PF",
                "status": "active"
            },
            {
                "player_id": "1629029",
                "name": "Luka Doncic",
                "team": "DAL",
                "position": "PG",
                "status": "active"
            },
            {
                "player_id": "203507",
                "name": "Giannis Antetokounmpo",
                "team": "MIL",
                "position": "PF",
                "status": "active"
            },
            {
                "player_id": "1628369",
                "name": "Jayson Tatum",
                "team": "BOS",
                "position": "SF",
                "status": "active"
            },
            {
                "player_id": "203954",
                "name": "Joel Embiid",
                "team": "PHI",
                "position": "C",
                "status": "active"
            },
            {
                "player_id": "1630169",
                "name": "Alperen Sengun",
                "team": "HOU",
                "position": "C",
                "status": "active"
            },
            {
                "player_id": "1628983",
                "name": "Shai Gilgeous-Alexander",
                "team": "OKC",
                "position": "PG",
                "status": "active"
            },
            {
                "player_id": "203081",
                "name": "Damian Lillard",
                "team": "MIL",
                "position": "PG",
                "status": "active"
            }
        ]
        
        self.logger.info(f"Generated {len(mock_players)} mock players")
        return mock_players
    
    def _generate_projections(
        self,
        players: List[Dict],
        injuries: List[Dict]
    ) -> List[Dict]:
        """
        Generate projections.
        
        Returns:
            List of projection dicts (empty list if failed)
        """
        try:
            projections = generate_projections(players, injuries)
            self.logger.info(f"Generated {len(projections)} projections")
            return projections
        except Exception as e:
            self.logger.error(f"Failed to generate projections", error=str(e))
            return []
    
    def _generate_risk_metrics(
        self,
        projections: List[Dict],
        injuries: List[Dict]
    ) -> List[Dict]:
        """
        Generate risk metrics.
        
        Returns:
            List of risk metric dicts (empty list if failed)
        """
        try:
            risks = generate_risk_metrics(projections, injuries)
            self.logger.info(f"Generated {len(risks)} risk assessments")
            return risks
        except Exception as e:
            self.logger.error(f"Failed to generate risk metrics", error=str(e))
            return []
    
    def _generate_insights(
        self,
        projections: List[Dict],
        risk_metrics: List[Dict]
    ) -> List[Dict]:
        """
        Generate insights.
        
        Returns:
            List of insight dicts (empty list if failed)
        """
        try:
            insights = generate_insights(projections, risk_metrics)
            self.logger.info(f"Generated {len(insights)} insights")
            return insights
        except Exception as e:
            self.logger.error(f"Failed to generate insights", error=str(e))
            return []
    
    def _validate_outputs(
        self,
        players: List[Dict],
        projections: List[Dict],
        insights: List[Dict],
        risks: List[Dict],
        injuries: List[Dict]
    ) -> bool:
        """
        Validate all outputs against schemas.
        
        Returns:
            True if all valid
        """
        self.logger.section("VALIDATING OUTPUTS")
        
        all_valid, errors = self.validator.validate_all(
            players=players,
            projections=projections,
            insights=insights,
            risks=risks,
            injuries=injuries
        )
        
        if all_valid:
            self.logger.info("All outputs valid")
            return True
        else:
            self.logger.error("Validation errors found")
            for error in errors:
                self.logger.error(f"  - {error}")
            return False
    
    def _write_outputs(
        self,
        players: List[Dict],
        projections: List[Dict],
        insights: List[Dict],
        risks: List[Dict],
        injuries: List[Dict]
    ) -> bool:
        """
        Write all outputs to DATA_DIR.
        
        Returns:
            True if all writes successful
        """
        self.logger.section("WRITING OUTPUTS")
        
        success = True
        
        # Write players
        if not self.writer.write_players(players):
            self.logger.error("Failed to write players.json")
            success = False
        
        # Write projections
        if not self.writer.write_projections(projections):
            self.logger.error("Failed to write projections.json")
            success = False
        
        # Write insights
        if not self.writer.write_insights(insights):
            self.logger.error("Failed to write insights.json")
            success = False
        
        # Write risk metrics
        if not self.writer.write_risk_metrics(risks):
            self.logger.error("Failed to write risk.json")
            success = False
        
        # Write injuries
        if not self.writer.write_injuries(injuries):
            self.logger.error("Failed to write injuries.json")
            success = False
        
        if success:
            self.logger.info("All outputs written successfully")
        
        return success
    
    def _write_manifest(self, success: bool, error: str = None):
        """
        Write pipeline manifest.
        
        Args:
            success: Whether pipeline succeeded
            error: Error message (if failed)
        """
        manifest = {
            "pipeline_version": "1.0.0",
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "data_dir": str(self.data_dir)
        }
        
        if error:
            manifest["error"] = error
        
        self.writer.write_manifest(manifest)


def run_pipeline(data_dir: Path = None) -> bool:
    """
    Main entry point for automation pipeline.
    
    Args:
        data_dir: Output directory
        
    Returns:
        True if successful
    """
    pipeline = AutomationPipeline(data_dir)
    return pipeline.run()


if __name__ == "__main__":
    # Run pipeline
    success = run_pipeline()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
