"""
Insights generation module.

Generates fantasy insights based on projections and risk metrics.
"""

from typing import List, Dict

from utils import get_logger


class InsightsGenerator:
    """
    Generates fantasy insights for players.
    
    Analyzes projections and risk to produce:
    - Value scores
    - Risk scores
    - Opportunity indexes
    - Human-readable notes
    """
    
    def __init__(self):
        """Initialize insights generator."""
        self.logger = get_logger("insights_generator")
    
    def generate_insights(
        self,
        projections: List[Dict],
        risk_metrics: List[Dict]
    ) -> List[Dict]:
        """
        Generate insights for all players.
        
        Args:
            projections: List of projection dicts
            risk_metrics: List of risk metric dicts
            
        Returns:
            List of insight dicts
        """
        self.logger.section("GENERATING INSIGHTS")
        
        # Build risk lookup
        risk_lookup = {risk["player_id"]: risk for risk in risk_metrics}
        
        insights = []
        
        for projection in projections:
            player_id = projection["player_id"]
            risk = risk_lookup.get(player_id, {})
            
            insight = self._generate_player_insight(projection, risk)
            insights.append(insight)
        
        self.logger.info(f"Generated {len(insights)} insights")
        return insights
    
    def _generate_player_insight(
        self,
        projection: Dict,
        risk: Dict
    ) -> Dict:
        """
        Generate insight for single player.
        
        Args:
            projection: Projection dict
            risk: Risk metric dict
            
        Returns:
            Insight dict
        """
        player_id = projection["player_id"]
        
        # Calculate value score (0-100)
        value_score = self._calculate_value_score(projection)
        
        # Get risk score
        risk_score = risk.get("injury_risk", 50) if risk else 50
        
        # Calculate opportunity index
        opportunity_index = self._calculate_opportunity_index(projection, risk)
        
        # Generate notes
        notes = self._generate_notes(projection, risk, value_score, risk_score)
        
        return {
            "player_id": player_id,
            "value_score": int(value_score),
            "risk_score": int(risk_score),
            "opportunity_index": int(opportunity_index),
            "notes": notes
        }
    
    def _calculate_value_score(self, projection: Dict) -> float:
        """
        Calculate overall value score based on fantasy points and consistency.
        
        Args:
            projection: Projection dict
            
        Returns:
            Value score (0-100)
        """
        # Fantasy points normalized to 0-100 scale
        # Top players: ~60+ FP/game
        # Average: ~30 FP/game
        fantasy_points = projection.get("fantasy_points", 0)
        fp_score = min(100, (fantasy_points / 60.0) * 100)
        
        # Consistency bonus
        consistency = projection.get("consistency", 75)
        consistency_bonus = (consistency - 75) / 25.0 * 10  # ±10 points
        
        value_score = fp_score + consistency_bonus
        
        return max(0, min(100, value_score))
    
    def _calculate_opportunity_index(
        self,
        projection: Dict,
        risk: Dict
    ) -> float:
        """
        Calculate opportunity index.
        
        High opportunity = High upside + Low risk
        
        Args:
            projection: Projection dict
            risk: Risk metric dict
            
        Returns:
            Opportunity index (0-100)
        """
        # Upside potential (ceiling vs. projection)
        fantasy_points = projection.get("fantasy_points", 0)
        ceiling = projection.get("ceiling", fantasy_points)
        
        if fantasy_points > 0:
            upside_ratio = ceiling / fantasy_points
            upside_score = min(100, (upside_ratio - 1) * 100)
        else:
            upside_score = 0
        
        # Risk factor (lower risk = higher opportunity)
        if risk:
            risk_score = (
                risk.get("injury_risk", 50) * 0.5 +
                risk.get("volatility", 50) * 0.3 +
                risk.get("minutes_risk", 50) * 0.2
            )
        else:
            risk_score = 50
        
        safety_score = 100 - risk_score
        
        # Combined opportunity (60% upside, 40% safety)
        opportunity = upside_score * 0.6 + safety_score * 0.4
        
        return max(0, min(100, opportunity))
    
    def _generate_notes(
        self,
        projection: Dict,
        risk: Dict,
        value_score: float,
        risk_score: float
    ) -> str:
        """
        Generate human-readable notes.
        
        Args:
            projection: Projection dict
            risk: Risk metric dict
            value_score: Calculated value score
            risk_score: Risk score
            
        Returns:
            Notes string
        """
        notes_parts = []
        
        # Value assessment
        if value_score >= 80:
            notes_parts.append("Elite value")
        elif value_score >= 60:
            notes_parts.append("Strong value")
        elif value_score >= 40:
            notes_parts.append("Moderate value")
        else:
            notes_parts.append("Low value")
        
        # Consistency assessment
        consistency = projection.get("consistency", 75)
        if consistency >= 85:
            notes_parts.append("high consistency")
        elif consistency <= 65:
            notes_parts.append("volatile")
        
        # Risk assessment
        if risk:
            injury_risk = risk.get("injury_risk", 50)
            if injury_risk >= 70:
                notes_parts.append("high injury risk")
            elif injury_risk <= 30:
                notes_parts.append("durable")
            
            minutes_risk = risk.get("minutes_risk", 50)
            if minutes_risk >= 70:
                notes_parts.append("minutes concern")
        
        # Usage assessment
        usage_rate = projection.get("usage_rate", 0)
        if usage_rate >= 28:
            notes_parts.append("elite usage")
        elif usage_rate <= 18:
            notes_parts.append("low usage")
        
        return ", ".join(notes_parts).capitalize()


def generate_insights(
    projections: List[Dict],
    risk_metrics: List[Dict]
) -> List[Dict]:
    """
    Main entry point for insights generation.
    
    Args:
        projections: List of projection dicts
        risk_metrics: List of risk metric dicts
        
    Returns:
        List of insight dicts
    """
    generator = InsightsGenerator()
    return generator.generate_insights(projections, risk_metrics)
