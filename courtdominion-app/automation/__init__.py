"""
CourtDominion Automation Package

Phase 1 automation for generating fantasy basketball projections and insights.

Main entry point: pipeline.run_pipeline()
"""

from .pipeline import run_pipeline, AutomationPipeline
from .ingest_injuries import ingest_injuries
from .projection_generator import generate_projections
from .insights_generator import generate_insights
from .risk_metrics import generate_risk_metrics

__version__ = "1.0.0"
__all__ = [
    "run_pipeline",
    "AutomationPipeline",
    "ingest_injuries",
    "generate_projections",
    "generate_insights",
    "generate_risk_metrics",
]
