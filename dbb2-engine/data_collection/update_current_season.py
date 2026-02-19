#!/usr/bin/env python3
"""
Collect/update the active NBA season CSV in dbb2 raw_data.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collect_nba_season import NBASeasonCollector
from engine.season import format_nba_season, get_current_nba_season_start_year


def main() -> int:
    parser = argparse.ArgumentParser(description="Update current NBA season CSV from NBA.com")
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent.parent / "raw_data"),
        help="Directory where games_YYYY_YY.csv will be written",
    )
    args = parser.parse_args()

    start_year = get_current_nba_season_start_year()
    season = format_nba_season(start_year)

    print(f"Resolved active NBA season: {season}")
    collector = NBASeasonCollector(season=season, output_dir=args.output_dir)
    ok = collector.collect()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
