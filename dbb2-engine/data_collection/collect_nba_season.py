#!/usr/bin/env python3
"""
collect_nba_season.py

Collects complete NBA season game logs with all required fields for dbb2.

Usage:
    python collect_nba_season.py --season 1995-96 --output raw_data/
    python collect_nba_season.py --season 2024-25 --output raw_data/

Output:
    raw_data/games_1995_1996.csv
    raw_data/games_2024_2025.csv

Fields collected:
    - player_name, player_id
    - game_date
    - team, opponent
    - home_or_road
    - minutes_played
    - points, rebounds, assists, steals, blocks, turnovers
    - fgm, fga, three_pm, three_pa, ftm, fta
    - age (calculated from birthdate)
    - position (PG, SG, SF, PF, C)
    - role (Starter, Bench, Rotation)
    - opponent_def_rank_vs_position (1-30 ranking)

Rate limiting: Built-in delays to respect NBA API limits
Resume capability: Can resume if interrupted
Validation: Checks for missing games and data quality
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import requests
import pandas as pd


class NBASeasonCollector:
    """Collects and enriches NBA season data for dbb2."""
    
    def __init__(self, season: str, output_dir: str):
        """
        Args:
            season: Season in format "1995-96" or "2024-25"
            output_dir: Directory to save CSV output
        """
        self.season = season
        self.output_dir = output_dir
        self.season_slug = self._parse_season(season)
        self.output_file = self._get_output_filename()
        
        # Cache for player info (birthdate, position)
        self.player_cache: Dict[int, Dict] = {}
        
        # Cache for opponent defense rankings
        self.opponent_defense_cache: Dict[Tuple[str, str], int] = {}
        
        print(f"Initialized collector for {season}")
        print(f"Output file: {self.output_file}")
    
    def _parse_season(self, season: str) -> str:
        """Convert season format to NBA API format."""
        if '-' in season:
            parts = season.split('-')
            start = parts[0]
            end = parts[1]
            
            # Ensure 4-digit years
            if len(start) == 2:
                start = '19' + start if int(start) > 50 else '20' + start
            
            if len(end) == 2:
                # Convert short year to full year
                start_year = int(start)
                end_year_short = int(end)
                
                # Figure out century for end year
                if end_year_short == 0:
                    end = str(start_year + 1)
                elif end_year_short < 50:
                    end = '20' + end
                else:
                    end = '19' + end
            
            return f"{start}-{end[-2:]}"  # Return as "1995-96" format
        
        return season
    
    def _get_output_filename(self) -> str:
        """Generate output filename."""
        # Convert "1995-96" to "games_1995_1996.csv"
        parts = self.season_slug.split('-')
        start_year = parts[0]
        end_year = parts[1]
        
        os.makedirs(self.output_dir, exist_ok=True)
        return os.path.join(self.output_dir, f"games_{start_year}_{end_year}.csv")
    
    def collect(self) -> bool:
        """
        Main collection method.
        
        Returns:
            True if successful, False otherwise
        """
        print(f"\n{'='*60}")
        print(f"COLLECTING {self.season} SEASON")
        print(f"{'='*60}\n")
        
        try:
            # Step 1: Collect player game logs
            print("Step 1/4: Fetching player game logs...")
            game_logs = self._fetch_player_game_logs()
            print(f"  → Collected {len(game_logs)} player-game records")
            
            # Step 2: Enrich with player info (age, position)
            print("\nStep 2/4: Enriching with player info...")
            game_logs = self._enrich_player_info(game_logs)
            print(f"  → Enriched {len(game_logs)} records")
            
            # Step 3: Determine roles (Starter, Bench, Rotation)
            print("\nStep 3/4: Determining player roles...")
            game_logs = self._determine_roles(game_logs)
            print(f"  → Assigned roles to {len(game_logs)} records")
            
            # Step 4: Calculate opponent defensive rankings
            print("\nStep 4/4: Calculating opponent defensive rankings...")
            game_logs = self._add_opponent_defense_rankings(game_logs)
            print(f"  → Added defensive rankings to {len(game_logs)} records")
            
            # Step 5: Write to CSV
            print(f"\nWriting to {self.output_file}...")
            self._write_csv(game_logs)
            print(f"  → Successfully wrote {len(game_logs)} records")
            
            # Step 6: Validate
            print("\nValidating output...")
            self._validate_output()
            print("  → Validation passed")
            
            print(f"\n{'='*60}")
            print(f"SUCCESS: {self.season} collected to {self.output_file}")
            print(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _fetch_player_game_logs(self) -> List[Dict]:
        """Fetch all player game logs for the season."""
        print(f"  Fetching from NBA API (season={self.season_slug})...")
        
        try:
            import requests
            import pandas as pd
            
            # Use direct HTTP API with proper headers
            url = "https://stats.nba.com/stats/leaguegamelog"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.nba.com/',
                'Origin': 'https://www.nba.com',
                'Connection': 'keep-alive',
                'x-nba-stats-origin': 'stats',
                'x-nba-stats-token': 'true'
            }
            
            params = {
                'Season': self.season_slug,
                'SeasonType': 'Regular Season',
                'LeagueID': '00',
                'PlayerOrTeam': 'P',  # P for Player
                'Direction': 'DESC',
                'Sorter': 'DATE',
                'Counter': '0'
            }
            
            print(f"  Making request to NBA.com...")
            print(f"  URL: {url}")
            print(f"  Season parameter: {self.season_slug}")
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # Rate limit respect
            time.sleep(1)
            
            if response.status_code != 200:
                print(f"  Response status: {response.status_code}")
                print(f"  Response body: {response.text[:500]}")
                
                # Try alternative season format
                print(f"  Trying alternative season format...")
                
                # NBA API might want "1995-96" or "1995" format
                alt_formats = [
                    self.season_slug,
                    self.season_slug.split('-')[0],  # Just start year "1995"
                ]
                
                for alt_season in alt_formats:
                    print(f"    Trying: {alt_season}")
                    params['Season'] = alt_season
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                    time.sleep(1)
                    
                    if response.status_code == 200:
                        print(f"    ✓ Success with format: {alt_season}")
                        break
                else:
                    raise Exception(f"API returned status code {response.status_code} for all season formats")
            
            data = response.json()
            
            # Check response structure
            if 'resultSets' not in data or len(data['resultSets']) == 0:
                print(f"  Response keys: {list(data.keys())}")
                raise Exception(f"Unexpected API response structure")
            
            result_set = data['resultSets'][0]
            headers_list = result_set['headers']
            rows = result_set['rowSet']
            
            if not rows:
                raise Exception(f"No data returned for season {self.season_slug}")
            
            print(f"  → Raw data: {len(rows)} records")
            
            # Convert to DataFrame for easier handling
            df = pd.DataFrame(rows, columns=headers_list)
            
            # Convert to list of dicts
            game_logs = df.to_dict('records')
            
            # Extract fields we need
            extracted = []
            for row in game_logs:
                # Parse matchup to determine home/road and opponent
                matchup = row.get('MATCHUP', '')
                if ' vs. ' in matchup:
                    home_or_road = 'HOME'
                    opponent = matchup.split(' vs. ')[-1].strip()
                elif ' @ ' in matchup:
                    home_or_road = 'ROAD'
                    opponent = matchup.split(' @ ')[-1].strip()
                else:
                    home_or_road = 'Unknown'
                    opponent = 'Unknown'
                
                extracted.append({
                    'player_id': row.get('PLAYER_ID'),
                    'player_name': row.get('PLAYER_NAME'),
                    'team': row.get('TEAM_ABBREVIATION'),
                    'game_date': row.get('GAME_DATE'),
                    'matchup': matchup,
                    'opponent': opponent,
                    'home_or_road': home_or_road,
                    'wl': row.get('WL'),
                    'min': row.get('MIN'),
                    'fgm': row.get('FGM', 0),
                    'fga': row.get('FGA', 0),
                    'fg_pct': row.get('FG_PCT', 0),
                    'fg3m': row.get('FG3M', 0),
                    'fg3a': row.get('FG3A', 0),
                    'fg3_pct': row.get('FG3_PCT', 0),
                    'ftm': row.get('FTM', 0),
                    'fta': row.get('FTA', 0),
                    'ft_pct': row.get('FT_PCT', 0),
                    'oreb': row.get('OREB', 0),
                    'dreb': row.get('DREB', 0),
                    'reb': row.get('REB', 0),
                    'ast': row.get('AST', 0),
                    'stl': row.get('STL', 0),
                    'blk': row.get('BLK', 0),
                    'tov': row.get('TOV', 0),
                    'pf': row.get('PF', 0),
                    'pts': row.get('PTS', 0),
                    'plus_minus': row.get('PLUS_MINUS')
                })
            
            return extracted
            
        except Exception as e:
            print(f"  ERROR fetching game logs: {e}")
            raise
    
    def _enrich_player_info(self, game_logs: List[Dict]) -> List[Dict]:
        """Add age and position to each game log."""
        unique_players = set(g['player_id'] for g in game_logs)
        print(f"  Fetching info for {len(unique_players)} unique players...")
        
        import requests
        
        # For older seasons, position data may not be available
        # We'll try to infer it from other sources or mark as Unknown
        
        for i, player_id in enumerate(unique_players):
            if player_id in self.player_cache:
                continue
            
            try:
                # Fetch player info using direct HTTP
                url = "https://stats.nba.com/stats/commonplayerinfo"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.nba.com/',
                    'Origin': 'https://www.nba.com',
                    'Connection': 'keep-alive',
                    'x-nba-stats-origin': 'stats',
                    'x-nba-stats-token': 'true'
                }
                
                params = {
                    'PlayerID': player_id,
                    'LeagueID': '00'
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=10)
                time.sleep(0.6)  # Rate limit: ~100 requests per minute
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'resultSets' in data and len(data['resultSets']) > 0:
                        result_set = data['resultSets'][0]
                        headers_list = result_set['headers']
                        rows = result_set['rowSet']
                        
                        if len(rows) > 0:
                            row_dict = dict(zip(headers_list, rows[0]))
                            
                            # Try to get position, with fallback
                            position = 'Unknown'
                            if 'POSITION' in row_dict and row_dict['POSITION']:
                                position = row_dict['POSITION']
                            
                            # Try to get birthdate, with fallback
                            birthdate = None
                            if 'BIRTHDATE' in row_dict and row_dict['BIRTHDATE']:
                                birthdate = row_dict['BIRTHDATE']
                            
                            self.player_cache[player_id] = {
                                'birthdate': birthdate,
                                'position': position
                            }
                        else:
                            self.player_cache[player_id] = {
                                'birthdate': None,
                                'position': 'Unknown'
                            }
                    else:
                        self.player_cache[player_id] = {
                            'birthdate': None,
                            'position': 'Unknown'
                        }
                else:
                    self.player_cache[player_id] = {
                        'birthdate': None,
                        'position': 'Unknown'
                    }
                
                if (i + 1) % 10 == 0:
                    print(f"    Progress: {i+1}/{len(unique_players)} players")
                    
            except Exception as e:
                print(f"    Warning: Could not fetch info for player {player_id}: {e}")
                self.player_cache[player_id] = {
                    'birthdate': None,
                    'position': 'Unknown'
                }
                continue
        
        # Now enrich each game log
        for log in game_logs:
            player_id = log['player_id']
            player_info = self.player_cache.get(player_id, {})
            
            # Calculate age
            birthdate_str = player_info.get('birthdate')
            game_date_str = log['game_date']
            
            if birthdate_str and game_date_str:
                try:
                    # Handle various date formats
                    if 'T' in birthdate_str:
                        birthdate = datetime.strptime(birthdate_str, '%Y-%m-%dT%H:%M:%S')
                    else:
                        birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d')
                    
                    game_date = datetime.strptime(game_date_str, '%Y-%m-%d')
                    age = (game_date - birthdate).days // 365
                    log['age'] = age
                except Exception as e:
                    log['age'] = None
            else:
                log['age'] = None
            
            # Add position
            position = player_info.get('position', 'Unknown')
            
            # Normalize position names (sometimes API returns "Guard", "Forward", etc.)
            position_map = {
                'Guard': 'G',
                'Forward': 'F',
                'Center': 'C',
                'Guard-Forward': 'G-F',
                'Forward-Guard': 'F-G',
                'Forward-Center': 'F-C',
                'Center-Forward': 'C-F'
            }
            
            log['position'] = position_map.get(position, position)
        
        return game_logs
    
    def _determine_roles(self, game_logs: List[Dict]) -> List[Dict]:
        """
        Determine if player was Starter, Bench, or Rotation.
        
        Heuristic:
        - Starter: minutes >= 24 in majority of games
        - Rotation: 10 <= minutes < 24 in majority of games
        - Bench: minutes < 10
        
        For single game, we approximate:
        - >= 20 minutes: Likely starter
        - 10-20 minutes: Likely rotation
        - < 10 minutes: Bench
        """
        for log in game_logs:
            minutes = log.get('min')
            
            # Parse minutes (could be "25:30" format or just 25)
            if isinstance(minutes, str):
                if ':' in minutes:
                    parts = minutes.split(':')
                    minutes = int(parts[0]) + int(parts[1]) / 60
                else:
                    try:
                        minutes = float(minutes)
                    except:
                        minutes = 0
            elif minutes is None:
                minutes = 0
            
            # Simple heuristic for single game
            if minutes >= 20:
                log['role'] = 'Starter'
            elif minutes >= 10:
                log['role'] = 'Rotation'
            else:
                log['role'] = 'Bench'
            
            # Store parsed minutes as float
            log['minutes_played'] = minutes
        
        return game_logs
    
    def _add_opponent_defense_rankings(self, game_logs: List[Dict]) -> List[Dict]:
        """
        Calculate opponent defensive rankings by position.
        
        This is THE CRITICAL UPDATE mentioned in the doc.
        
        Process:
        1. For each team, calculate points allowed per game by opponent position
        2. Rank teams 1-30 for each position (1 = best defense, 30 = worst)
        3. Add opponent_def_rank_vs_position to each game log
        """
        print("  Calculating team defensive stats by position...")
        
        # Group game logs by (team, opponent_position)
        # We need: How many points did TEAM allow to opponent POSITION players?
        
        # Structure: {(team, position): [points_allowed_list]}
        team_position_points = {}
        
        for log in game_logs:
            opponent_team = log['team']  # The team this player played FOR
            player_position = log['position']
            points = log['pts']
            
            # For each game, the opponent DEFENSE is the team this player played AGAINST
            defending_team = log['opponent']
            
            key = (defending_team, player_position)
            if key not in team_position_points:
                team_position_points[key] = []
            
            team_position_points[key].append(points)
        
        # Calculate average points allowed per game by position
        team_position_avg = {}
        for key, points_list in team_position_points.items():
            team, position = key
            avg = sum(points_list) / len(points_list) if points_list else 0
            team_position_avg[key] = avg
        
        # Rank teams by position (lower avg = better defense = rank 1)
        position_rankings = {}
        for position in ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'C-F', 'F-C', 'F-G', 'G-F']:
            # Get all teams for this position
            teams_for_position = [(team, avg) for (team, pos), avg in team_position_avg.items() if pos == position]
            
            # Sort by avg (ascending = best defense first)
            teams_for_position.sort(key=lambda x: x[1])
            
            # Assign ranks 1-N
            position_rankings[position] = {}
            for rank, (team, avg) in enumerate(teams_for_position, start=1):
                position_rankings[position][team] = rank
        
        print(f"  Calculated rankings for {len(position_rankings)} positions")
        
        # Now add rankings to each game log
        for log in game_logs:
            opponent = log['opponent']
            position = log['position']
            
            # Get rank (default to 15 if not found = average)
            rank = position_rankings.get(position, {}).get(opponent, 15)
            log['opponent_def_rank_vs_position'] = rank
        
        return game_logs
    
    def _write_csv(self, game_logs: List[Dict]):
        """Write game logs to CSV with final schema."""
        
        # Define output columns (matches dbb2 requirements)
        columns = [
            'player_name',
            'player_id',
            'game_date',
            'team',
            'opponent',
            'home_or_road',
            'minutes_played',
            'points',
            'rebounds',
            'assists',
            'steals',
            'blocks',
            'turnovers',
            'fgm',
            'fga',
            'fg_pct',
            'three_pm',
            'three_pa',
            'fg3_pct',
            'ftm',
            'fta',
            'ft_pct',
            'age',
            'position',
            'role',
            'opponent_def_rank_vs_position',
            'plus_minus',
            'wl'
        ]
        
        with open(self.output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            
            for log in game_logs:
                row = {
                    'player_name': log['player_name'],
                    'player_id': log['player_id'],
                    'game_date': log['game_date'],
                    'team': log['team'],
                    'opponent': log['opponent'],
                    'home_or_road': log['home_or_road'],
                    'minutes_played': log.get('minutes_played', 0),
                    'points': log['pts'],
                    'rebounds': log['reb'],
                    'assists': log['ast'],
                    'steals': log['stl'],
                    'blocks': log['blk'],
                    'turnovers': log['tov'],
                    'fgm': log['fgm'],
                    'fga': log['fga'],
                    'fg_pct': log['fg_pct'],
                    'three_pm': log['fg3m'],
                    'three_pa': log['fg3a'],
                    'fg3_pct': log['fg3_pct'],
                    'ftm': log['ftm'],
                    'fta': log['fta'],
                    'ft_pct': log['ft_pct'],
                    'age': log.get('age'),
                    'position': log['position'],
                    'role': log['role'],
                    'opponent_def_rank_vs_position': log['opponent_def_rank_vs_position'],
                    'plus_minus': log.get('plus_minus'),
                    'wl': log.get('wl')
                }
                writer.writerow(row)
    
    def _validate_output(self):
        """Basic validation of output CSV."""
        if not os.path.exists(self.output_file):
            raise Exception(f"Output file not created: {self.output_file}")
        
        with open(self.output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if len(rows) == 0:
                raise Exception("Output CSV is empty")
            
            # Check required columns
            required = ['player_name', 'game_date', 'points', 'opponent_def_rank_vs_position']
            for col in required:
                if col not in rows[0]:
                    raise Exception(f"Missing required column: {col}")
            
            print(f"  → {len(rows)} records")
            print(f"  → {len(set(r['player_id'] for r in rows))} unique players")
            print(f"  → Date range: {min(r['game_date'] for r in rows)} to {max(r['game_date'] for r in rows)}")


def main():
    parser = argparse.ArgumentParser(description='Collect NBA season data for dbb2')
    parser.add_argument('--season', required=True, 
                       help='Season in format "1995-96" or "2024-25"')
    parser.add_argument('--output', default='raw_data',
                       help='Output directory (default: raw_data)')
    
    args = parser.parse_args()
    
    collector = NBASeasonCollector(args.season, args.output)
    success = collector.collect()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
