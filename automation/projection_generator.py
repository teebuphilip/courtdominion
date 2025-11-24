"""
Projection generation module.

Generates fantasy basketball projections for all active players.
"""

import random
from typing import List, Dict

from utils import get_logger


class ProjectionGenerator:
    """
    Generates fantasy basketball projections.
    
    Phase 1: Simplified projections based on mock data
    Phase 2: Advanced projections using historical data and ML models
    """
    
    def __init__(self):
        """Initialize projection generator."""
        self.logger = get_logger("projection_generator")
    
    def generate_projections(self, players: List[Dict], injuries: List[Dict] = None) -> List[Dict]:
        """
        Generate projections for all players.
        
        Args:
            players: List of player dicts
            injuries: List of injury dicts (optional)
            
        Returns:
            List of projection dicts
        """
        self.logger.section("GENERATING PROJECTIONS")
        
        # Build injury lookup
        injury_lookup = {}
        if injuries:
            injury_lookup = {injury["player_id"]: injury for injury in injuries}
        
        projections = []
        
        for player in players:
            if player["status"] == "active":
                projection = self._generate_player_projection(player, injury_lookup)
                projections.append(projection)
        
        self.logger.info(f"Generated {len(projections)} projections")
        return projections
    
    def _generate_player_projection(
        self,
        player: Dict,
        injury_lookup: Dict
    ) -> Dict:
        """
        Generate projection for single player.
        
        Args:
            player: Player dict
            injury_lookup: Dict mapping player_id to injury info
            
        Returns:
            Projection dict
        """
        player_id = player["player_id"]
        
        # Check if player is injured
        is_injured = player_id in injury_lookup
        injury_modifier = 0.7 if is_injured else 1.0
        
        # Generate base stats (Phase 1: simplified mock data)
        # Phase 2 will use historical data + ML models
        base_stats = self._get_base_stats(player["position"])
        
        # Apply injury modifier
        minutes = base_stats["minutes"] * injury_modifier
        usage_rate = base_stats["usage_rate"]
        
        # Core stats
        points = base_stats["points"] * injury_modifier
        rebounds = base_stats["rebounds"] * injury_modifier
        assists = base_stats["assists"] * injury_modifier
        steals = base_stats["steals"] * injury_modifier
        blocks = base_stats["blocks"] * injury_modifier
        turnovers = base_stats["turnovers"] * injury_modifier
        
        # Shooting percentages (not affected by injuries)
        fg_pct = base_stats["fg_pct"]
        three_pt_pct = base_stats["three_pt_pct"]
        ft_pct = base_stats["ft_pct"]
        
        # Made/Attempted
        fgm = points * 0.4  # Rough approximation
        fga = fgm / fg_pct if fg_pct > 0 else 0
        tpm = base_stats["tpm"] * injury_modifier
        tpa = tpm / three_pt_pct if three_pt_pct > 0 else 0
        ftm = points * 0.2
        fta = ftm / ft_pct if ft_pct > 0 else 0
        
        # Fantasy points (standard scoring)
        fantasy_points = self._calculate_fantasy_points(
            points, rebounds, assists, steals, blocks, turnovers
        )
        
        # Ceiling/Floor (variance based on consistency)
        consistency = base_stats["consistency"]
        variance = (100 - consistency) / 100.0
        ceiling = fantasy_points * (1 + variance)
        floor = fantasy_points * (1 - variance)
        
        return {
            "player_id": player_id,
            "name": player["name"],
            "team": player["team"],
            "position": player["position"],
            "minutes": round(minutes, 1),
            "usage_rate": round(usage_rate, 1),
            "points": round(points, 1),
            "rebounds": round(rebounds, 1),
            "assists": round(assists, 1),
            "steals": round(steals, 1),
            "blocks": round(blocks, 1),
            "turnovers": round(turnovers, 1),
            "fg_pct": round(fg_pct, 3),
            "three_pt_pct": round(three_pt_pct, 3),
            "ft_pct": round(ft_pct, 3),
            "fgm": round(fgm, 1),
            "fga": round(fga, 1),
            "tpm": round(tpm, 1),
            "tpa": round(tpa, 1),
            "ftm": round(ftm, 1),
            "fta": round(fta, 1),
            "fantasy_points": round(fantasy_points, 1),
            "ceiling": round(ceiling, 1),
            "floor": round(floor, 1),
            "consistency": consistency
        }
    
    def _get_base_stats(self, position: str) -> Dict:
        """
        Get base stats for position.
        
        Phase 1: Position averages with randomization
        Phase 2: Historical player data
        
        Args:
            position: Player position
            
        Returns:
            Base stats dict
        """
        # Position templates (league averages)
        templates = {
            "PG": {
                "minutes": 30.0,
                "usage_rate": 22.0,
                "points": 15.0,
                "rebounds": 4.0,
                "assists": 6.0,
                "steals": 1.0,
                "blocks": 0.3,
                "turnovers": 2.0,
                "fg_pct": 0.450,
                "three_pt_pct": 0.360,
                "ft_pct": 0.800,
                "tpm": 2.0,
                "consistency": 75
            },
            "SG": {
                "minutes": 30.0,
                "usage_rate": 22.0,
                "points": 16.0,
                "rebounds": 4.5,
                "assists": 4.0,
                "steals": 1.0,
                "blocks": 0.4,
                "turnovers": 2.0,
                "fg_pct": 0.455,
                "three_pt_pct": 0.370,
                "ft_pct": 0.820,
                "tpm": 2.2,
                "consistency": 75
            },
            "SF": {
                "minutes": 30.0,
                "usage_rate": 22.0,
                "points": 16.0,
                "rebounds": 6.0,
                "assists": 3.5,
                "steals": 1.0,
                "blocks": 0.6,
                "turnovers": 2.0,
                "fg_pct": 0.465,
                "three_pt_pct": 0.360,
                "ft_pct": 0.780,
                "tpm": 1.8,
                "consistency": 75
            },
            "PF": {
                "minutes": 30.0,
                "usage_rate": 22.0,
                "points": 15.0,
                "rebounds": 8.0,
                "assists": 2.5,
                "steals": 0.8,
                "blocks": 1.0,
                "turnovers": 1.8,
                "fg_pct": 0.485,
                "three_pt_pct": 0.340,
                "ft_pct": 0.750,
                "tpm": 1.0,
                "consistency": 75
            },
            "C": {
                "minutes": 28.0,
                "usage_rate": 20.0,
                "points": 13.0,
                "rebounds": 10.0,
                "assists": 2.0,
                "steals": 0.7,
                "blocks": 1.5,
                "turnovers": 1.5,
                "fg_pct": 0.550,
                "three_pt_pct": 0.280,
                "ft_pct": 0.700,
                "tpm": 0.3,
                "consistency": 80
            }
        }
        
        template = templates.get(position, templates["SF"])
        
        # Add randomization (±20%)
        randomized = {}
        for key, value in template.items():
            if isinstance(value, float):
                if key in ["fg_pct", "three_pt_pct", "ft_pct"]:
                    # Shooting percentages: ±5%
                    randomized[key] = value * random.uniform(0.95, 1.05)
                else:
                    # Other stats: ±20%
                    randomized[key] = value * random.uniform(0.8, 1.2)
            else:
                randomized[key] = value
        
        return randomized
    
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
    Main entry point for projection generation.
    
    Args:
        players: List of player dicts
        injuries: List of injury dicts (optional)
        
    Returns:
        List of projection dicts
    """
    generator = ProjectionGenerator()
    return generator.generate_projections(players, injuries)
