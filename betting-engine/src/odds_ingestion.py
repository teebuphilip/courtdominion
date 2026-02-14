"""
Odds Ingestion — pull player prop lines from The Odds API and DBB2 projections.

Fetches both data sources, normalizes them to a standard structure,
and saves as flat JSON files in data/.
"""

import argparse
import sys
from pathlib import Path

import requests

# WHY: Add project root to path so 'src' package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import (
    load_settings,
    load_json,
    write_json,
    get_today_date,
    get_file_age_hours,
    logger,
)

# Map The Odds API market names to our short prop types
MARKET_TO_PROP = {
    "player_points": "points",
    "player_rebounds": "rebounds",
    "player_assists": "assists",
    "player_threes": "threes",
    "player_steals": "steals",
    "player_blocks": "blocks",
}


def fetch_projections(dry_run: bool = False, from_file: str = None) -> None:
    """
    Fetch today's projections from the DBB2 API and save as flat JSON.

    If from_file is provided, read the committed betting_contract.json
    instead of calling the API. This is used by GitHub Actions.
    """
    settings = load_settings()
    today = get_today_date()
    output_path = f"data/projections/{today}.json"

    if Path(output_path).exists():
        logger.info("Projections already fetched today, skipping")
        return

    if from_file:
        _load_projections_from_file(from_file, output_path)
        return

    if dry_run:
        logger.info("[DRY RUN] Would fetch projections from DBB2 API")
        _create_dry_run_projections(output_path)
        return

    api = settings["dbb2_api"]
    url = f"{api['base_url']}{api['projections_endpoint']}"
    timeout = api.get("timeout_seconds", 30)

    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as e:
        logger.error(f"Failed to reach DBB2 API at {url}: {e}")
        raise

    if response.status_code != 200:
        raise RuntimeError(f"DBB2 API returned {response.status_code}: {response.text[:200]}")

    raw = response.json()
    normalized = normalize_projections(raw)
    write_json(output_path, normalized)
    logger.info(f"Saved {len(normalized)} player projections to {output_path}")


def normalize_projections(raw: dict) -> dict:
    """
    Normalize DBB2 API response to standard structure.

    WHY: DBB2 may change its response shape - normalize here once
    so all downstream code uses a guaranteed structure.

    Output format:
    { player_id: { name, team, position, is_b2b, props: { stat: { projection, std_dev, confidence } } } }
    """
    result = {}
    players = raw.get("players", [])

    for player in players:
        pid = str(player["id"])
        result[pid] = {
            "name": player["name"],
            "team": player["team"],
            "position": player["position"],
            "is_b2b": player.get("is_b2b", False),
            "props": {
                "points":   {"projection": player["pts"],  "std_dev": player["pts_std"],  "confidence": player["pts_conf"]},
                "rebounds": {"projection": player["reb"],  "std_dev": player["reb_std"],  "confidence": player["reb_conf"]},
                "assists":  {"projection": player["ast"],  "std_dev": player["ast_std"],  "confidence": player["ast_conf"]},
                "threes":   {"projection": player["fg3m"], "std_dev": player["fg3m_std"], "confidence": player["fg3m_conf"]},
                "steals":   {"projection": player["stl"],  "std_dev": player["stl_std"],  "confidence": player["stl_conf"]},
                "blocks":   {"projection": player["blk"],  "std_dev": player["blk_std"],  "confidence": player["blk_conf"]},
            },
        }

    return result


def fetch_odds(dry_run: bool = False) -> None:
    """
    Fetch today's player prop odds from The Odds API.

    WHY: The Odds API charges per call - check file exists to avoid wasting quota.
    """
    settings = load_settings()
    today = get_today_date()
    output_path = f"data/odds/{today}.json"

    if Path(output_path).exists():
        # WHY: Overwrite if older than 2 hours - lines move throughout day
        file_age = get_file_age_hours(output_path)
        if file_age < 2:
            logger.info("Odds fetched recently, skipping")
            return

    if dry_run:
        logger.info("[DRY RUN] Would fetch odds from The Odds API")
        _create_dry_run_odds(output_path)
        return

    api = settings["odds_api"]
    all_odds = {}

    for market in api["markets"]:
        url = f"{api['base_url']}/sports/{api['sport']}/odds"
        params = {
            "apiKey": api["api_key"],
            "regions": ",".join(api["regions"]),
            "markets": market,
            "bookmakers": ",".join(api["bookmakers"]),
        }

        try:
            response = requests.get(url, params=params, timeout=30)
        except requests.RequestException as e:
            logger.warning(f"Odds API request failed for {market}: {e}")
            continue

        if response.status_code != 200:
            # WHY: Don't fail entire run if one market fails
            logger.warning(f"Odds API returned {response.status_code} for {market}")
            continue

        data = response.json()
        all_odds[market] = data
        logger.info(f"Fetched {market}: {len(data)} events")

    normalized = normalize_odds(all_odds)
    write_json(output_path, normalized)
    logger.info(f"Saved odds for {len(normalized)} players to {output_path}")


def normalize_odds(raw: dict) -> dict:
    """
    Normalize Odds API response to standard structure.

    WHY: Match odds to player by name - The Odds API uses names not IDs.

    Output format:
    { player_name: { prop_type: { line, over_odds, under_odds, bookmaker } } }
    """
    result = {}

    for market, games in raw.items():
        prop_type = MARKET_TO_PROP.get(market, market)

        for game in games:
            for bookmaker in game.get("bookmakers", []):
                for mkt in bookmaker.get("markets", []):
                    for outcome in mkt.get("outcomes", []):
                        player_name = outcome.get("description", "")
                        if not player_name:
                            continue

                        line = outcome.get("point")
                        price = outcome.get("price")
                        name = outcome.get("name", "")

                        if player_name not in result:
                            result[player_name] = {}

                        # WHY: Keep best line across bookmakers
                        if prop_type not in result[player_name]:
                            result[player_name][prop_type] = {
                                "line": line,
                                "over_odds": None,
                                "under_odds": None,
                                "bookmaker": bookmaker.get("key", "unknown"),
                            }

                        entry = result[player_name][prop_type]
                        if name == "Over" and price is not None:
                            if entry["over_odds"] is None or price > entry["over_odds"]:
                                entry["over_odds"] = price
                        elif name == "Under" and price is not None:
                            if entry["under_odds"] is None or price > entry["under_odds"]:
                                entry["under_odds"] = price

                        # WHY: Update line if this bookmaker has a different one
                        if line is not None:
                            entry["line"] = line

    return result


def _load_projections_from_file(from_file: str, output_path: str) -> None:
    """Load projections from a committed betting_contract.json file."""
    if not Path(from_file).exists():
        raise FileNotFoundError(f"Projection file not found: {from_file}")

    data = load_json(from_file)
    write_json(output_path, data)
    logger.info(f"Loaded {len(data)} player projections from {from_file} -> {output_path}")


def _create_dry_run_projections(output_path: str) -> None:
    """Create projection file from fixtures for dry-run testing."""
    fixture = "tests/fixtures/sample_projections.json"
    if Path(fixture).exists():
        data = load_json(fixture)
        write_json(output_path, data)
        logger.info(f"[DRY RUN] Wrote {len(data)} sample projections to {output_path}")
    else:
        write_json(output_path, {})
        logger.warning(f"[DRY RUN] No fixture found, wrote empty projections")


def _create_dry_run_odds(output_path: str) -> None:
    """Create odds file from fixtures for dry-run testing."""
    fixture = "tests/fixtures/sample_odds.json"
    if Path(fixture).exists():
        data = load_json(fixture)
        write_json(output_path, data)
        logger.info(f"[DRY RUN] Wrote odds for {len(data)} players to {output_path}")
    else:
        write_json(output_path, {})
        logger.warning(f"[DRY RUN] No fixture found, wrote empty odds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DBB2 Odds Ingestion")
    parser.add_argument("--fetch-projections", action="store_true")
    parser.add_argument("--fetch-odds", action="store_true")
    parser.add_argument("--from-file", type=str, default=None,
                        help="Load projections from file instead of DBB2 API")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.fetch_projections or args.from_file:
        fetch_projections(dry_run=args.dry_run, from_file=args.from_file)
    if args.fetch_odds:
        fetch_odds(dry_run=args.dry_run)
    if not args.fetch_projections and not args.fetch_odds and not args.from_file:
        fetch_projections(dry_run=args.dry_run)
        fetch_odds(dry_run=args.dry_run)
