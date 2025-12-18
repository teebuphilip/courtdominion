"""
Main automation pipeline orchestrator - WITH REAL NBA DATA + CONTENT GENERATION.

Coordinates all data generation steps using:
1. Real NBA player roster (NBA.com API)
2. Real injuries (ESPN API)
3. Real projections (YOUR DBB2 ENGINE!)
4. Real insights generation
5. Real risk metrics
6. CONTENT GENERATION (OpenAI/ChatGPT)
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

# Import REAL data fetchers
from fetch_real_players import fetch_real_players
from ingest_injuries import ingest_injuries
from projection_generator import generate_projections
from insights_generator import generate_insights
from risk_metrics import generate_risk_metrics

# Import content generator
import generator


class AutomationPipeline:
    """
    Main automation pipeline with REAL NBA DATA + CONTENT GENERATION.
    
    Orchestrates all data generation and validation steps using:
    - Real NBA players from NBA.com
    - Real injuries from ESPN
    - YOUR dbb2 projection engine
    - OpenAI content generation
    
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
        
        self.logger.section("COURTDOMINION AUTOMATION PIPELINE - REAL NBA DATA + CONTENT")
        self.logger.info(f"Data directory: {self.data_dir}")
        self.logger.info(f"Started at: {datetime.utcnow().isoformat()}")
    
    def run(self) -> bool:
        """
        Run complete automation pipeline with REAL DATA + CONTENT.
        
        Steps:
        1. Fetch real injuries (ESPN)
        2. Fetch real players (NBA.com - ~450 players)
        3. Generate real projections (DBB2 engine)
        4. Generate risk metrics
        5. Generate insights
        6. Validate all outputs
        7. Write to DATA_DIR
        8. GENERATE CONTENT (OpenAI) ← NEW!
        
        Returns:
            True if successful, False if any step failed
        """
        try:
            # Step 1: Fetch real injuries from ESPN
            injuries = self._fetch_injuries()
            
            # Step 2: Fetch real NBA players (~450 active players)
            players = self._fetch_real_players()
            
            # Step 3: Generate REAL projections using YOUR dbb2 engine
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
            
            if not write_success:
                self.logger.error("Failed to write outputs")
                self._write_manifest(success=False)
                return False
            
            # Step 8: GENERATE CONTENT (NEW!)
            content_success = self._generate_content(
                projections=projections,
                insights=insights,
                risk_metrics=risk_metrics
            )
            
            if content_success:
                self.logger.section("PIPELINE COMPLETED SUCCESSFULLY - REAL NBA DATA + CONTENT")
                self._write_manifest(success=True)
                return True
            else:
                self.logger.warning("Content generation failed, but data pipeline succeeded")
                self._write_manifest(success=True, warning="Content generation failed")
                return True  # Still return True since data pipeline worked
                
        except Exception as e:
            self.logger.error(f"Pipeline failed with exception", error=str(e))
            self._write_manifest(success=False, error=str(e))
            return False
    
    def _fetch_injuries(self) -> List[Dict]:
        """
        Fetch REAL injury data from ESPN.
        
        Returns:
            List of injury dicts (empty list if failed)
        """
        try:
            injuries = ingest_injuries()
            self.logger.info(f"Fetched {len(injuries)} real injuries from ESPN")
            return injuries
        except Exception as e:
            self.logger.error(f"Failed to fetch injuries", error=str(e))
            return []
    
    def _fetch_real_players(self) -> List[Dict]:
        """
        Fetch REAL NBA player roster from NBA.com.
        
        Returns:
            List of ~450 active NBA player dicts
        """
        self.logger.section("FETCHING REAL NBA PLAYERS")
        
        try:
            players = fetch_real_players(include_teams=False)
            self.logger.info(f"Fetched {len(players)} real NBA players from NBA.com")
            return players
        except Exception as e:
            self.logger.error(f"Failed to fetch real players", error=str(e))
            return []
    
    def _generate_projections(
        self,
        players: List[Dict],
        injuries: List[Dict]
    ) -> List[Dict]:
        """
        Generate REAL projections using YOUR dbb2 engine.
        
        Returns:
            List of projection dicts (empty list if failed)
        """
        try:
            projections = generate_projections(players, injuries)
            self.logger.info(f"Generated {len(projections)} real projections (DBB2 engine)")
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
    
    def _generate_content(
        self,
        projections: List[Dict],
        insights: List[Dict],
        risk_metrics: List[Dict]
    ) -> bool:
        """
        Generate marketing content using OpenAI.
        
        Creates blog posts, tweets, Reddit posts, etc.
        
        Returns:
            True if successful
        """
        self.logger.section("GENERATING CONTENT (OpenAI)")
        
        try:
            # Call generator module
            content_dir = generator.generate_all_content(
                data_dir=self.data_dir,
                projections=projections,
                insights=insights,
                risk_metrics=risk_metrics
            )
            
            if content_dir:
                self.logger.info(f"Content generated successfully: {content_dir}")
                return True
            else:
                self.logger.error("Content generation returned no output directory")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to generate content", error=str(e))
            return False
    
    def _write_manifest(self, success: bool, error: str = None, warning: str = None):
        """
        Write pipeline manifest.
        
        Args:
            success: Whether pipeline succeeded
            error: Error message (if failed)
            warning: Warning message (if partial success)
        """
        manifest = {
            "pipeline_version": "1.0.0-real-data-content",
            "data_source": "NBA.com + ESPN + DBB2 + OpenAI",
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "data_dir": str(self.data_dir)
        }
        
        if error:
            manifest["error"] = error
        
        if warning:
            manifest["warning"] = warning
        
        self.writer.write_manifest(manifest)


def run_pipeline(data_dir: Path = None) -> bool:
    """
    Main entry point for automation pipeline - REAL NBA DATA + CONTENT.
    
    Args:
        data_dir: Output directory
        
    Returns:
        True if successful
    """
    pipeline = AutomationPipeline(data_dir)
    return pipeline.run()


if __name__ == "__main__":
    # Run pipeline with real data + content generation
    success = run_pipeline()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
