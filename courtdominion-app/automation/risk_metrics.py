"""
Risk metrics generation module.

Generates risk assessments for players based on injuries and projections.
"""

import random
from typing import List, Dict

from utils import get_logger


class RiskMetricsGenerator:
    """
    Generates risk metrics for players.
    
    Calculates:
    - Injury risk (0-100)
    - Volatility (0-100)
    - Minutes risk (0-100)
    """
    
    def __init__(self):
        """Initialize risk metrics generator."""
        self.logger = get_logger("risk_metrics_generator")
    
    def generate_risk_metrics(
        self,
        projections: List[Dict],
        injuries: List[Dict] = None
    ) -> List[Dict]:
        """
        Generate risk metrics for all players.
        
        Args:
            projections: List of projection dicts
            injuries: List of injury dicts (optional)
            
        Returns:
            List of risk metric dicts
        """
        self.logger.section("GENERATING RISK METRICS")
        
        # Build injury lookup
        injury_lookup = {}
        if injuries:
            injury_lookup = {injury["player_id"]: injury for injury in injuries}
        
        risk_metrics = []
        
        for projection in projections:
            player_id = projection["player_id"]
            injury = injury_lookup.get(player_id)
            
            risk = self._generate_player_risk(projection, injury)
            risk_metrics.append(risk)
        
        self.logger.info(f"Generated {len(risk_metrics)} risk assessments")
        return risk_metrics
    
    def _generate_player_risk(
        self,
        projection: Dict,
        injury: Dict = None
    ) -> Dict:
        """
        Generate risk metrics for single player.
        
        Args:
            projection: Projection dict
            injury: Injury dict (optional)
            
        Returns:
            Risk metrics dict
        """
        player_id = projection["player_id"]
        
        # Calculate injury risk
        injury_risk = self._calculate_injury_risk(projection, injury)
        
        # Calculate volatility (performance consistency)
        volatility = self._calculate_volatility(projection)
        
        # Calculate minutes risk
        minutes_risk = self._calculate_minutes_risk(projection, injury)
        
        return {
            "player_id": player_id,
            "injury_risk": int(injury_risk),
            "volatility": int(volatility),
            "minutes_risk": int(minutes_risk)
        }
    
    def _calculate_injury_risk(
        self,
        projection: Dict,
        injury: Dict = None
    ) -> float:
        """
        Calculate injury risk score.
        
        Args:
            projection: Projection dict
            injury: Injury dict (optional)
            
        Returns:
            Injury risk (0-100, higher = more risky)
        """
        # Base risk (age, position factors)
        # Phase 1: Simplified calculation
        # Phase 2: Historical injury data + ML model
        
        base_risk = 30  # League average
        
        # Current injury status
        if injury:
            status = injury.get("status", "").lower()
            if status == "out":
                base_risk = 80
            elif status == "doubtful":
                base_risk = 70
            elif status == "questionable":
                base_risk = 50
            elif status == "probable":
                base_risk = 40
        
        # Add randomization for Phase 1
        risk = base_risk + random.uniform(-10, 10)
        
        return max(0, min(100, risk))
    
    def _calculate_volatility(self, projection: Dict) -> float:
        """
        Calculate performance volatility.
        
        High volatility = Inconsistent performance
        
        Args:
            projection: Projection dict
            
        Returns:
            Volatility (0-100, higher = more volatile)
        """
        # Inverse of consistency
        consistency = projection.get("consistency", 75)
        volatility = 100 - consistency
        
        # Adjust based on ceiling/floor spread
        fantasy_points = projection.get("fantasy_points", 0)
        ceiling = projection.get("ceiling", fantasy_points)
        floor = projection.get("floor", fantasy_points)
        
        if fantasy_points > 0:
            spread_ratio = (ceiling - floor) / fantasy_points
            spread_adjustment = spread_ratio * 20  # Up to 20 points
        else:
            spread_adjustment = 0
        
        total_volatility = volatility + spread_adjustment
        
        return max(0, min(100, total_volatility))
    
    def _calculate_minutes_risk(
        self,
        projection: Dict,
        injury: Dict = None
    ) -> float:
        """
        Calculate minutes reduction risk.
        
        High risk = Likely to lose minutes
        
        Args:
            projection: Projection dict
            injury: Injury dict (optional)
            
        Returns:
            Minutes risk (0-100)
        """
        # Base risk from projected minutes
        minutes = projection.get("minutes", 30)
        
        # High minutes = Higher risk of load management
        if minutes >= 35:
            base_risk = 50
        elif minutes >= 30:
            base_risk = 30
        elif minutes >= 25:
            base_risk = 20
        else:
            base_risk = 10
        
        # Injury increases minutes risk
        if injury:
            base_risk += 20
        
        # Add randomization for Phase 1
        risk = base_risk + random.uniform(-10, 10)
        
        return max(0, min(100, risk))


def generate_risk_metrics(
    projections: List[Dict],
    injuries: List[Dict] = None
) -> List[Dict]:
    """
    Main entry point for risk metrics generation.
    
    Args:
        projections: List of projection dicts
        injuries: List of injury dicts (optional)
        
    Returns:
        List of risk metric dicts
    """
    generator = RiskMetricsGenerator()
    return generator.generate_risk_metrics(projections, injuries)
