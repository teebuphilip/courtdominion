"""
Projection generation module using REAL DBB2 ENGINE.

Generates fantasy basketball projections for all active players using
your dbb2 projection algorithms with real NBA data.
"""

from typing import List, Dict
from utils import get_logger

# Import your DBB2 projection engine
from dbb2_projections import calculate_current_season_projection


class ProjectionGenerator:
    """
    Generates fantasy basketball projections using real DBB2 engine.
    
    Uses real NBA data from nba-api + your projection algorithms.
    """
    
    def __init__(self):
        """Initialize projection generator"""
        self.logger = get_logger("projection_generator")
    
    def generate_projections(self, players: List[Dict], injuries: List[Dict] = None) -> List[Dict]:
        """
        Generate projections for all players using DBB2 engine.
        
        Args:
            players: List of player dicts
            injuries: List of injury dicts (optional)
            
        Returns:
            List of projection dicts with REAL NBA data
        """
        self.logger.section("GENERATING REAL PROJECTIONS (DBB2 ENGINE)")
        
        # Build injury lookup
        injury_lookup = {}
        if injuries:
            injury_lookup = {injury["player_id"]: injury for injury in injuries}
        
        projections = []
        
        for player in players:
            if player["status"] == "active":
                projection = self._generate_player_projection(player, injury_lookup)
                if projection:  # Only add if projection succeeded
                    projections.append(projection)
        
        self.logger.info(f"Generated {len(projections)} real projections")
        return projections
    
    def _generate_player_projection(
        self,
        player: Dict,
        injury_lookup: Dict
    ) -> Dict:
        """
        Generate projection for single player using DBB2 engine.
        
        Args:
            player: Player dict
            injury_lookup: Dict mapping player_id to injury info
            
        Returns:
            Projection dict with real NBA data
        """
        player_id = player["player_id"]
        
        try:
            # Use YOUR dbb2 projection engine!
            dbb2_projection = calculate_current_season_projection(player_id)
            
            if not dbb2_projection:
                self.logger.warning(f"No projection data for {player['name']} ({player_id})")
                return None
            
            # Check if player is injured
            is_injured = player_id in injury_lookup
            
            # Apply injury modifier if needed
            injury_modifier = 0.7 if is_injured else 1.0
            
            # Calculate fantasy points (standard scoring)
            fantasy_points = self._calculate_fantasy_points(
                dbb2_projection['points_per_game'],
                dbb2_projection['rebounds_per_game'],
                dbb2_projection['assists_per_game'],
                dbb2_projection['steals_per_game'],
                dbb2_projection['blocks_per_game'],
                dbb2_projection['turnovers_per_game']
            )
            
            # Calculate ceiling/floor based on confidence
            confidence = dbb2_projection.get('confidence', 0.8)
            variance = (1.0 - confidence) * 0.3  # Max 30% variance
            ceiling = fantasy_points * (1 + variance)
            floor = fantasy_points * (1 - variance)
            
            # Determine consistency score (higher confidence = more consistent)
            consistency = int(confidence * 100)
            
            # Build full projection (matching backend format)
            projection = {
                "player_id": player_id,
                "name": player["name"],
                "team": player["team"],
                "position": dbb2_projection.get('position', player['position']),
                "minutes": dbb2_projection['minutes_per_game'] * injury_modifier,
                "usage_rate": 22.0,  # TODO: Calculate from DBB2 data
                "points": dbb2_projection['points_per_game'] * injury_modifier,
                "rebounds": dbb2_projection['rebounds_per_game'] * injury_modifier,
                "assists": dbb2_projection['assists_per_game'] * injury_modifier,
                "steals": dbb2_projection['steals_per_game'] * injury_modifier,
                "blocks": dbb2_projection['blocks_per_game'] * injury_modifier,
                "turnovers": dbb2_projection['turnovers_per_game'] * injury_modifier,
                "fg_pct": dbb2_projection['field_goal_pct'],
                "three_pt_pct": dbb2_projection['three_point_pct'],
                "ft_pct": dbb2_projection['free_throw_pct'],
                "fgm": dbb2_projection['field_goals_made'] * injury_modifier,
                "fga": dbb2_projection['field_goals_attempted'] * injury_modifier,
                "tpm": dbb2_projection['three_pointers_made'] * injury_modifier,
                "tpa": dbb2_projection['three_pointers_attempted'] * injury_modifier,
                "ftm": dbb2_projection['free_throws_made'] * injury_modifier,
                "fta": dbb2_projection['free_throws_attempted'] * injury_modifier,
                "fantasy_points": round(fantasy_points * injury_modifier, 1),
                "ceiling": round(ceiling * injury_modifier, 1),
                "floor": round(floor * injury_modifier, 1),
                "consistency": consistency
            }
            
            return projection
            
        except Exception as e:
            self.logger.error(
                f"Failed to generate projection for {player['name']}",
                player_id=player_id,
                error=str(e)
            )
            return None
    
    def _calculate_fantasy_points(
        self,
        points: float,
        rebounds: float,
        assists: float,
        steals: float,
        blocks: float,
        turnovers: float
    ) -> float:
        """
        Calculate standard fantasy points.
        
        Standard scoring:
        - Points: 1 point
        - Rebounds: 1.2 points
        - Assists: 1.5 points
        - Steals: 3 points
        - Blocks: 3 points
        - Turnovers: -1 point
        """
        return (
            points * 1.0 +
            rebounds * 1.2 +
            assists * 1.5 +
            steals * 3.0 +
            blocks * 3.0 +
            turnovers * -1.0
        )


def generate_projections(players: List[Dict], injuries: List[Dict] = None) -> List[Dict]:
    """
    Main entry point for projection generation with REAL DBB2 ENGINE.
    
    Args:
        players: List of player dicts
        injuries: List of injury dicts (optional)
        
    Returns:
        List of projection dicts with real NBA data
    """
    generator = ProjectionGenerator()
    return generator.generate_projections(players, injuries)
