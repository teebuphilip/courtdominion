"""
Result Checker — fetch NBA box scores and grade yesterday's bets.

Fetches actual stats from the NBA Stats API (same endpoint as data collection),
compares each bet against actual results, calculates payouts, and writes
a daily results file to data/results/{date}.json.
"""

import argparse
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import load_json, write_json, get_timestamp, logger
from src.kelly_sizer import american_to_decimal, get_american_odds
from src.ledger import load_ledger, update_ledger, save_ledger, generate_ledger_markdown

# NBA Stats API config (same pattern as DBB2 data collection)
NBA_API_URL = "https://stats.nba.com/stats/leaguegamelog"
NBA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Connection": "keep-alive",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
}

# Map betting engine prop names to NBA API column names
PROP_TO_STAT = {
    "points": "PTS",
    "rebounds": "REB",
    "assists": "AST",
    "threes": "FG3M",
    "steals": "STL",
    "blocks": "BLK",
}


def get_season_slug(date_str: str) -> str:
    """
    Derive NBA season slug from a date string (YYYY-MM-DD).

    Oct-Dec games belong to {year}-{year+1} season.
    Jan-Jun games belong to {year-1}-{year} season.
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    if dt.month >= 10:
        start_year = dt.year
    else:
        start_year = dt.year - 1
    end_suffix = str(start_year + 1)[-2:]
    return f"{start_year}-{end_suffix}"


def fetch_box_scores(date_str: str) -> dict:
    """
    Fetch player box scores for a single date from the NBA Stats API.

    Returns: {player_name_lower: {PTS: int, REB: int, AST: int, ...}}
    """
    import requests

    season = get_season_slug(date_str)
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    date_formatted = dt.strftime("%m/%d/%Y")

    params = {
        "Season": season,
        "SeasonType": "Regular Season",
        "LeagueID": "00",
        "PlayerOrTeam": "P",
        "Direction": "DESC",
        "Sorter": "DATE",
        "Counter": "0",
        "DateFrom": date_formatted,
        "DateTo": date_formatted,
    }

    logger.info(f"Fetching box scores for {date_str} (season={season})...")

    response = requests.get(
        NBA_API_URL, headers=NBA_HEADERS, params=params, timeout=30
    )
    time.sleep(1)  # Rate limit respect

    if response.status_code != 200:
        raise RuntimeError(
            f"NBA API returned status {response.status_code}: {response.text[:300]}"
        )

    data = response.json()
    if "resultSets" not in data or len(data["resultSets"]) == 0:
        raise RuntimeError("Unexpected NBA API response structure")

    result_set = data["resultSets"][0]
    headers = result_set["headers"]
    rows = result_set["rowSet"]

    if not rows:
        logger.warning(f"No box score data for {date_str} — possibly no games played")
        return {}

    logger.info(f"  Fetched {len(rows)} player lines for {date_str}")

    # Build lookup keyed by lowercase player name
    box_scores = {}
    for row in rows:
        record = dict(zip(headers, row))
        name = record.get("PLAYER_NAME", "").lower().strip()
        if name:
            box_scores[name] = {
                "PTS": record.get("PTS", 0) or 0,
                "REB": record.get("REB", 0) or 0,
                "AST": record.get("AST", 0) or 0,
                "FG3M": record.get("FG3M", 0) or 0,
                "STL": record.get("STL", 0) or 0,
                "BLK": record.get("BLK", 0) or 0,
                "MIN": record.get("MIN", 0),
                "PLAYER_NAME": record.get("PLAYER_NAME", ""),
            }

    return box_scores


def grade_bet(bet: dict, actual_stat) -> str:
    """
    Grade a single bet against the actual stat value.

    Returns: "WIN", "LOSS", "PUSH", or "NO_ACTION"
    """
    if actual_stat is None:
        return "NO_ACTION"

    line = bet["sportsbook_line"]
    direction = bet["direction"]

    if actual_stat > line:
        return "WIN" if direction == "OVER" else "LOSS"
    elif actual_stat < line:
        return "WIN" if direction == "UNDER" else "LOSS"
    else:
        return "PUSH"


def calculate_payout(bet: dict, outcome: str, unit_value: float) -> float:
    """
    Calculate dollar profit/loss for a graded bet.

    WIN:  stake * (decimal_odds - 1)
    LOSS: -stake
    PUSH / NO_ACTION: $0
    """
    if outcome in ("PUSH", "NO_ACTION"):
        return 0.0

    stake = bet["units"] * unit_value
    odds = get_american_odds(bet)

    if odds is None:
        decimal_odds = bet.get("decimal_odds", 1.91)
    else:
        decimal_odds = american_to_decimal(odds)

    if outcome == "WIN":
        return round(stake * (decimal_odds - 1), 2)
    else:
        return round(-stake, 2)


def grade_all_bets(bet_slip: dict, box_scores: dict, unit_value: float) -> dict:
    """
    Grade every bet from a daily bet slip against actual box scores.

    Returns results dict ready for data/results/{date}.json.
    """
    date = bet_slip["date"]
    bets = bet_slip.get("bets", [])

    graded = []
    wins = losses = pushes = no_action = 0
    daily_pnl = 0.0

    for bet in bets:
        player_name = bet["player_name"]
        prop_type = bet["prop_type"]
        stat_key = PROP_TO_STAT.get(prop_type)

        if stat_key is None:
            logger.warning(f"Unknown prop type: {prop_type}")
            continue

        # Look up actual stats (case-insensitive)
        player_stats = box_scores.get(player_name.lower().strip())

        if player_stats is None:
            actual_stat = None
            outcome = "NO_ACTION"
        else:
            actual_stat = player_stats.get(stat_key)
            outcome = grade_bet(bet, actual_stat)

        payout = calculate_payout(bet, outcome, unit_value)
        daily_pnl += payout

        if outcome == "WIN":
            wins += 1
        elif outcome == "LOSS":
            losses += 1
        elif outcome == "PUSH":
            pushes += 1
        else:
            no_action += 1

        graded.append({
            "player_name": player_name,
            "prop_type": prop_type,
            "direction": bet["direction"],
            "sportsbook_line": bet["sportsbook_line"],
            "dbb2_projection": bet.get("dbb2_projection"),
            "actual_stat": actual_stat,
            "outcome": outcome,
            "units": bet["units"],
            "payout_dollars": payout,
        })

    return {
        "date": date,
        "graded_at": get_timestamp(),
        "total_bets": len(graded),
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "no_action": no_action,
        "daily_pnl": round(daily_pnl, 2),
        "bets": graded,
    }


def run(date: str = None, dry_run: bool = False) -> dict:
    """
    Main grading pipeline.

    1. Load yesterday's bet slip
    2. Fetch box scores from NBA Stats API
    3. Grade each bet
    4. Write results file
    5. Update ledger
    """
    if date is None:
        yesterday = datetime.now() - timedelta(days=1)
        date = yesterday.strftime("%Y-%m-%d")

    slip_path = f"data/bet_slips/{date}.json"
    results_path = f"data/results/{date}.json"

    if not Path(slip_path).exists():
        logger.info(f"No bet slip for {date}, nothing to grade")
        return {}

    bet_slip = load_json(slip_path)
    logger.info(f"Loaded bet slip: {date} — {bet_slip['total_bets']} bets")

    # Fetch box scores
    if dry_run:
        fixture_path = "tests/fixtures/sample_box_scores.json"
        if Path(fixture_path).exists():
            box_scores = load_json(fixture_path)
            logger.info(f"  Dry run: loaded fixture box scores ({len(box_scores)} players)")
        else:
            logger.warning("  Dry run: no fixture file, using empty box scores")
            box_scores = {}
    else:
        box_scores = fetch_box_scores(date)

    # Get unit value from ledger
    ledger = load_ledger()
    unit_value = ledger["current_bankroll"] / 100

    # Grade bets
    results = grade_all_bets(bet_slip, box_scores, unit_value)

    # Write results file
    write_json(results_path, results)
    logger.info(
        f"Results: {results['wins']}W-{results['losses']}L-{results['pushes']}P, "
        f"P&L: ${results['daily_pnl']:+.2f}"
    )

    # Update ledger
    if not dry_run:
        ledger = update_ledger(ledger, results)
        save_ledger(ledger)

        md = generate_ledger_markdown(ledger)
        from src import write_file
        write_file("data/ledger_history.md", md)

        logger.info(
            f"Ledger updated: bankroll ${ledger['current_bankroll']:.2f}, "
            f"ROI {ledger['roi_pct']}%"
        )

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DBB2 Result Checker")
    parser.add_argument(
        "--date", type=str, default=None,
        help="Date to grade (YYYY-MM-DD). Defaults to yesterday."
    )
    parser.add_argument("--dry-run", action="store_true", help="Use fixture data")
    args = parser.parse_args()
    results = run(date=args.date, dry_run=args.dry_run)
    if results:
        print(
            f"\n{results['wins']}W-{results['losses']}L-{results['pushes']}P | "
            f"P&L: ${results['daily_pnl']:+.2f}"
        )
