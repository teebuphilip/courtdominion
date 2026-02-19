"""
Fetch live NBA standings data from NBA.com via nba_api.
"""

from typing import Dict

TEAM_ABBREV_MAP = {
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
    "LA Clippers": "LAC",
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


def fetch_team_games_played(season: str) -> Dict[str, int]:
    """
    Fetch games played per team for a given season (e.g., '2025-26').
    Returns {} on failure.
    """
    try:
        from nba_api.stats.endpoints import leaguestandings
    except Exception:
        return {}

    try:
        standings = leaguestandings.LeagueStandings(season=season, league_id="00")
        df = standings.get_data_frames()[0]
        team_games = {}

        for _, row in df.iterrows():
            team_name = f"{row['TeamCity']} {row['TeamName']}"
            abbrev = TEAM_ABBREV_MAP.get(team_name)
            if not abbrev:
                continue
            team_games[abbrev] = int(row["WINS"]) + int(row["LOSSES"])

        return team_games
    except Exception:
        return {}
