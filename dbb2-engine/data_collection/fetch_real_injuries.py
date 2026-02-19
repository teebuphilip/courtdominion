"""
Fetch live NBA injuries from ESPN.
"""

from typing import Dict, List

import requests

ESPN_INJURY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"

TEAM_MAP = {
    "Atlanta Hawks": "ATL",
    "Boston Celtics": "BOS",
    "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA",
    "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW",
    "Houston Rockets": "HOU",
    "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC",
    "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL",
    "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP",
    "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA",
    "Washington Wizards": "WAS",
}


def fetch_real_injuries(timeout: int = 10) -> List[Dict]:
    """Return normalized injury rows; empty list on failure."""
    try:
        response = requests.get(ESPN_INJURY_URL, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []

    injuries: List[Dict] = []
    for team_data in payload.get("injuries", []):
        team_name = team_data.get("displayName", "")
        team_abbrev = TEAM_MAP.get(team_name, "UNK")
        for injury_data in team_data.get("injuries", []):
            athlete = injury_data.get("athlete", {})
            short_comment = injury_data.get("shortComment", "") or ""
            long_comment = injury_data.get("longComment", "") or ""
            details = short_comment if short_comment else long_comment[:200]
            combined = f"{short_comment} {long_comment}".lower()

            injury_type = "Other"
            for keyword in (
                "ankle", "knee", "hamstring", "calf", "groin", "back",
                "shoulder", "wrist", "hand", "finger", "foot", "achilles",
                "quad", "hip", "elbow", "concussion", "illness", "rest",
                "personal", "suspension", "acl", "mcl", "meniscus",
            ):
                if keyword in combined:
                    injury_type = keyword.capitalize()
                    break

            injuries.append(
                {
                    "player_id": str(athlete.get("id", "")) if athlete.get("id") else "",
                    "name": athlete.get("displayName", "Unknown"),
                    "team": team_abbrev,
                    "status": injury_data.get("status", ""),
                    "details": details,
                    "injury_type": injury_type,
                    "return_date": injury_data.get("date"),
                }
            )
    return injuries
