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
        
        # Build injury lookup by BOTH player_id AND name (ESPN doesn't provide NBA API IDs)
        injury_lookup_by_id = {}
        injury_lookup_by_name = {}
        if injuries:
            for injury in injuries:
                # Try player_id first (if available)
                if injury.get("player_id"):
                    injury_lookup_by_id[injury["player_id"]] = injury
                # Always index by name as fallback
                if injury.get("name"):
                    # Normalize name (remove Jr., Sr., III, etc. for better matching)
                    normalized_name = injury["name"].replace(" Jr.", "").replace(" Sr.", "").replace(" III", "").strip()
                    injury_lookup_by_name[normalized_name.lower()] = injury
        
        projections = []
        
        for player in players:
            if player["status"] == "active":
                projection = self._generate_player_projection(
                    player,
                    injury_lookup_by_id,
                    injury_lookup_by_name
                )
                if projection:  # Only add if projection succeeded
                    projections.append(projection)
        
        self.logger.info(f"Generated {len(projections)} real projections")
        return projections
    
    def _generate_player_projection(
        self,
        player: Dict,
        injury_lookup_by_id: Dict,
        injury_lookup_by_name: Dict
    ) -> Dict:
        """
        Generate projection for single player using DBB2 engine.

        Args:
            player: Player dict
            injury_lookup_by_id: Dict mapping player_id to injury info
            injury_lookup_by_name: Dict mapping player name to injury info

        Returns:
            Projection dict with real NBA data
        """
        player_id = player["player_id"]
        player_name = player["name"]
        
        try:
            # Use YOUR dbb2 projection engine!
            dbb2_projection = calculate_current_season_projection(player_id)
            
            if not dbb2_projection:
                self.logger.warning(f"No projection data for {player['name']} ({player_id})")
                return None

            # Check for season-ending conditions
            games_played = dbb2_projection.get('games_played', 0)

            # EXCLUDE players who haven't played this season (injuries from before season started)
            if games_played == 0:
                self.logger.info(f"Excluding {player['name']} - 0 games played this season")
                return None

            # Check injury status and determine modifier
            injury_modifier = self._calculate_injury_modifier(
                player_id,
                player_name,
                injury_lookup_by_id,
                injury_lookup_by_name
            )

            # Exclude if modifier is 0.0 (season-ending injury)
            if injury_modifier == 0.0:
                return None

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

    def _calculate_injury_modifier(
        self,
        player_id: str,
        player_name: str,
        injury_lookup_by_id: Dict,
        injury_lookup_by_name: Dict
    ) -> float:
        """
        Calculate injury modifier based on injury status.

        Args:
            player_id: Player ID
            player_name: Player name
            injury_lookup_by_id: Dict mapping player_id to injury info
            injury_lookup_by_name: Dict mapping name to injury info

        Returns:
            Modifier (0.0 = exclude, 0.9 = minor, 0.7 = moderate, 1.0 = healthy)
        """
        # Try to find injury by player_id first
        injury = injury_lookup_by_id.get(player_id)

        # If not found by ID, try by name
        if not injury:
            normalized_name = player_name.replace(" Jr.", "").replace(" Sr.", "").replace(" III", "").strip()
            injury = injury_lookup_by_name.get(normalized_name.lower())

        # If still not found, player is healthy
        if not injury:
            return 1.0
        status = injury.get('status', '').lower()
        injury_type = injury.get('injury_type', '').lower()
        details = injury.get('details', '').lower()

        # Season-ending injuries - EXCLUDE completely
        season_ending_keywords = [
            'acl', 'out for season', 'season-ending', 'torn acl', 'achilles',
            'season-ending surgery', 'out for the season', 'rest of the season'
        ]
        for keyword in season_ending_keywords:
            if keyword in injury_type or keyword in details:
                self.logger.info(f"Excluding {player_name} - Season-ending injury ({injury_type})")
                return 0.0  # Will be filtered out

        # Parse timeframe from details for smarter modifiers

        # 1. Indefinite / No timetable - Very long term
        indefinite_keywords = ['indefinitely', 'no timetable', 'extended absence', 'multiple weeks', 'out several weeks']
        if any(keyword in details for keyword in indefinite_keywords):
            self.logger.info(f"Heavy discount for {player_name} - Long-term injury ({injury_type})")
            return 0.50

        # 2. Multi-week injuries (2-4 weeks)
        multiweek_keywords = ['week', 'weeks', 're-evaluated', 'reevaluated', '2 weeks', '3 weeks', '4 weeks']
        if any(keyword in details for keyword in multiweek_keywords):
            return 0.75  # 25% discount for 2-4 week absence

        # 3. Game-to-game decisions (specific game mentioned)
        game_keywords = ['will not play', 'ruled out', 'out for', 'sidelined for']
        game_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'tonight', 'today']
        if any(keyword in details for keyword in game_keywords) and any(day in details for day in game_days):
            return 0.85  # 15% discount for game-to-game

        # 4. Day-to-Day or Questionable
        if 'day-to-day' in status or 'questionable' in status:
            return 0.95  # 5% discount

        # 5. Probable / Available soon
        if 'probable' in status or 'available' in details or 'expected to play' in details:
            return 0.98  # 2% discount

        # 6. "Out" status with serious injury but no timeframe - exclude for safety
        if 'out' in status:
            serious_injuries = ['knee', 'back', 'foot', 'ankle']
            if any(inj in injury_type for inj in serious_injuries):
                # If no timeframe mentioned, assume long-term and exclude
                self.logger.info(f"Excluding {player_name} - Out with {injury_type}, no clear return timeline")
                return 0.0

        # Default: moderate discount for unknown/other injuries
        return 0.80

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
