"""
Risk metrics generation module - FIX-006 REBUILD.

Generates uncertainty-driven risk assessments for players.

Risk Definition (LOCKED):
Risk = likelihood the projection is materially wrong.

Components:
1. Availability Risk (60% weight) - Will they play the projected games?
2. Role Risk (25% weight) - Will their minutes/role stay stable? Includes injury history.
3. Composition Risk (15% weight) - Is their value from volatile stats?

Classification (POST-PROJECTION):
- Low: total_risk < 0.25
- Medium: 0.25 <= total_risk <= 0.55
- High: total_risk > 0.55
"""

from typing import List, Dict
from utils import get_logger


class RiskMetricsGenerator:
    """
    Generates uncertainty-driven risk metrics for players.

    NO random values. NO default-to-Low behavior.
    All risk is computed from actual projection data.
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
        Generate risk metrics for all players (POST-PROJECTION).

        Args:
            projections: List of projection dicts (must include new FIX-001/002 fields)
            injuries: List of injury dicts (optional, for additional context)

        Returns:
            List of risk metric dicts with risk_level classification
        """
        self.logger.section("GENERATING RISK METRICS (FIX-006 REBUILD)")

        # Build injury lookup by name (ESPN doesn't always have player_id)
        injury_lookup = {}
        if injuries:
            for injury in injuries:
                if injury.get("name"):
                    injury_lookup[injury["name"].lower()] = injury
                if injury.get("player_id"):
                    injury_lookup[injury["player_id"]] = injury

        risk_metrics = []
        risk_distribution = {"Low": 0, "Medium": 0, "High": 0}

        for projection in projections:
            risk = self._generate_player_risk(projection, injury_lookup)
            risk_metrics.append(risk)
            risk_distribution[risk["risk_level"]] += 1

        self.logger.info(f"Generated {len(risk_metrics)} risk assessments")
        self.logger.info(f"Distribution: Low={risk_distribution['Low']}, Medium={risk_distribution['Medium']}, High={risk_distribution['High']}")

        return risk_metrics

    def _generate_player_risk(
        self,
        projection: Dict,
        injury_lookup: Dict
    ) -> Dict:
        """
        Generate risk metrics for single player using uncertainty model.

        Args:
            projection: Projection dict (with team_games_remaining, games_remaining_projected)
            injury_lookup: Dict for injury lookups

        Returns:
            Risk metrics dict with component scores and classification
        """
        player_id = projection["player_id"]
        player_name = projection.get("name", "")

        # Component 1: Availability Risk (50% weight)
        availability_risk = self._calculate_availability_risk(projection)

        # Component 2: Role/Minutes Volatility (30% weight)
        role_risk = self._calculate_role_risk(projection, injury_lookup, player_name)

        # Component 3: Stat Composition Risk (20% weight)
        composition_risk = self._calculate_composition_risk(projection)

        # Aggregate risk (weights updated per user feedback)
        total_risk = (
            0.60 * availability_risk +
            0.25 * role_risk +
            0.15 * composition_risk
        )

        # Classify (POST-PROJECTION ONLY)
        if total_risk < 0.25:
            risk_level = "Low"
        elif total_risk <= 0.55:
            risk_level = "Medium"
        else:
            risk_level = "High"

        return {
            "player_id": player_id,
            "availability_risk": round(availability_risk, 3),
            "role_risk": round(role_risk, 3),
            "composition_risk": round(composition_risk, 3),
            "total_risk": round(total_risk, 3),
            "risk_level": risk_level
        }

    def _calculate_availability_risk(self, projection: Dict) -> float:
        """
        Calculate availability risk.

        Formula: 1 - (games_remaining_projected / team_games_remaining)

        A player projected to play all remaining team games = 0 risk
        A player projected to miss half the games = 0.5 risk

        Returns:
            Float 0.0-1.0 (higher = more risky)
        """
        team_games_remaining = projection.get("team_games_remaining", 42)
        games_remaining_projected = projection.get("games_remaining_projected", 42)

        if team_games_remaining <= 0:
            return 0.0

        availability_risk = 1.0 - (games_remaining_projected / team_games_remaining)

        return max(0.0, min(1.0, availability_risk))

    def _calculate_role_risk(
        self,
        projection: Dict,
        injury_lookup: Dict,
        player_name: str
    ) -> float:
        """
        Calculate role/minutes volatility risk.

        Factors:
        - Low minutes = higher role uncertainty
        - Current injury status = role instability
        - Injury history = even when healthy, injury-prone players are risky
        - Consistency score = proxy for role stability

        Returns:
            Float 0.0-1.0 (higher = more risky)
        """
        risk_score = 0.0

        # Factor 1: Minutes-based role security (0-0.35)
        # High-minute players have secure roles, low-minute players are volatile
        minutes = projection.get("minutes", 25)
        if minutes >= 32:
            minutes_risk = 0.05  # Starter, secure role
        elif minutes >= 28:
            minutes_risk = 0.12  # Solid rotation player
        elif minutes >= 22:
            minutes_risk = 0.20  # Rotation player, some uncertainty
        elif minutes >= 15:
            minutes_risk = 0.28  # Bench player, role at risk
        else:
            minutes_risk = 0.35  # Deep bench, highly volatile role

        risk_score += minutes_risk

        # Factor 2: Current injury status (0-0.25)
        injury = None
        if player_name:
            injury = injury_lookup.get(player_name.lower())
        if not injury:
            injury = injury_lookup.get(projection.get("player_id"))

        if injury:
            status = injury.get("status", "").lower()
            if "out" in status:
                risk_score += 0.25  # Out = major role uncertainty when returning
            elif "doubtful" in status:
                risk_score += 0.20
            elif "questionable" in status:
                risk_score += 0.12
            elif "probable" in status or "day-to-day" in status:
                risk_score += 0.05

        # Factor 3: INJURY HISTORY (0-0.25) - NEW
        # Even when currently healthy, historically injury-prone players are risky
        # Use availability ratio as proxy for injury history
        team_games_remaining = projection.get("team_games_remaining", 42)
        games_remaining_projected = projection.get("games_remaining_projected", 42)

        if team_games_remaining > 0:
            historical_availability = games_remaining_projected / team_games_remaining
            # Players who historically miss games get penalized
            # E.g., Embiid plays ~65% of games = 0.35 * 0.25 = 0.0875 penalty
            injury_history_risk = (1.0 - historical_availability) * 0.25
            risk_score += injury_history_risk

        # Factor 4: Consistency as proxy for role stability (0-0.15)
        # Low consistency = volatile production = potentially unstable role
        consistency = projection.get("consistency", 75)
        consistency_risk = (100 - consistency) / 100 * 0.15

        risk_score += consistency_risk

        return max(0.0, min(1.0, risk_score))

    def _calculate_composition_risk(self, projection: Dict) -> float:
        """
        Calculate stat composition risk.

        High-variance stats (3PM, STL, BLK) are less predictable.
        Players dependent on these have higher projection risk.

        Returns:
            Float 0.0-1.0 (higher = more risky)
        """
        fantasy_points = projection.get("fantasy_points", 0)

        if fantasy_points <= 0:
            return 0.5  # Unknown, moderate risk

        # Calculate fantasy points from each category
        # Standard scoring: PTS=1, REB=1.2, AST=1.5, STL=3, BLK=3, TO=-1
        points_fp = projection.get("points", 0) * 1.0
        rebounds_fp = projection.get("rebounds", 0) * 1.2
        assists_fp = projection.get("assists", 0) * 1.5
        steals_fp = projection.get("steals", 0) * 3.0
        blocks_fp = projection.get("blocks", 0) * 3.0
        turnovers_fp = projection.get("turnovers", 0) * -1.0

        # High-variance categories: 3PM (from tpm), STL, BLK
        tpm = projection.get("tpm", 0)
        three_pm_fp = tpm * 1.0  # 3PM contributes to points already, but track separately

        # Calculate % of value from high-variance stats
        high_variance_fp = steals_fp + blocks_fp + (three_pm_fp * 2)  # Weight 3PM extra
        stable_fp = points_fp + rebounds_fp + assists_fp - (three_pm_fp * 2)  # Remove 3PM double count

        total_positive_fp = points_fp + rebounds_fp + assists_fp + steals_fp + blocks_fp
        if total_positive_fp <= 0:
            return 0.5

        high_variance_ratio = high_variance_fp / total_positive_fp

        # Also check single-category dependency
        max_category = max(points_fp, rebounds_fp, assists_fp, steals_fp, blocks_fp)
        dependency_ratio = max_category / total_positive_fp

        # Combined composition risk
        # High variance ratio = risky, high single-category dependency = risky
        composition_risk = (high_variance_ratio * 0.6) + (dependency_ratio * 0.4)

        return max(0.0, min(1.0, composition_risk))


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
        List of risk metric dicts with risk_level classification
    """
    generator = RiskMetricsGenerator()
    return generator.generate_risk_metrics(projections, injuries)
