#!/usr/bin/env python3
"""
Simple Projections - No database, no server, just output data
"""
import os
import json
from datetime import datetime, date

# Get output file from environment
output_file = os.getenv('PROJECTIONS_OUTPUT', '/tmp/projections_output.json')
proj_date = os.getenv('PROJECTIONS_DATE', date.today().isoformat())

# Create simple projection data
projections = {
    "date": proj_date,
    "generated_at": datetime.utcnow().isoformat(),
    "status": "success",
    "projections": [
        {
            "player_id": 1,
            "player_name": "LeBron James",
            "team": "LAL",
            "projected_points": 24.5,
            "projected_rebounds": 7.8,
            "projected_assists": 7.2,
            "projected_steals": 1.1,
            "projected_blocks": 0.6,
            "projected_turnovers": 3.2,
            "projected_threes": 1.8,
            "projected_fg_pct": 0.512,
            "projected_ft_pct": 0.735
        },
        {
            "player_id": 2,
            "player_name": "Stephen Curry",
            "team": "GSW",
            "projected_points": 28.3,
            "projected_rebounds": 5.1,
            "projected_assists": 6.4,
            "projected_steals": 1.3,
            "projected_blocks": 0.4,
            "projected_turnovers": 3.0,
            "projected_threes": 4.5,
            "projected_fg_pct": 0.461,
            "projected_ft_pct": 0.915
        },
        {
            "player_id": 3,
            "player_name": "Giannis Antetokounmpo",
            "team": "MIL",
            "projected_points": 31.2,
            "projected_rebounds": 11.5,
            "projected_assists": 5.8,
            "projected_steals": 1.2,
            "projected_blocks": 1.4,
            "projected_turnovers": 3.5,
            "projected_threes": 0.6,
            "projected_fg_pct": 0.579,
            "projected_ft_pct": 0.658
        },
        {
            "player_id": 4,
            "player_name": "Nikola Jokic",
            "team": "DEN",
            "projected_points": 26.8,
            "projected_rebounds": 12.3,
            "projected_assists": 9.2,
            "projected_steals": 1.3,
            "projected_blocks": 0.8,
            "projected_turnovers": 3.1,
            "projected_threes": 1.2,
            "projected_fg_pct": 0.631,
            "projected_ft_pct": 0.822
        },
        {
            "player_id": 5,
            "player_name": "Luka Doncic",
            "team": "DAL",
            "projected_points": 32.5,
            "projected_rebounds": 8.7,
            "projected_assists": 9.8,
            "projected_steals": 1.4,
            "projected_blocks": 0.5,
            "projected_turnovers": 4.1,
            "projected_threes": 2.8,
            "projected_fg_pct": 0.487,
            "projected_ft_pct": 0.742
        }
    ],
    "metadata": {
        "total_players": 5,
        "note": "Mock data for testing - replace with real projections once database is connected"
    }
}

# Write output
with open(output_file, 'w') as f:
    json.dump(projections, f, indent=2)

print(f"✅ Projections written to {output_file}")
print(f"✅ Generated {len(projections['projections'])} player projections")
