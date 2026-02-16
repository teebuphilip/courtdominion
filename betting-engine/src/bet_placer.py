"""
Bet Placer — single orchestrator for the daily betting pipeline.

Runs both sportsbook and Kalshi pipelines, applies daily budget cap,
appends to master CSV, and generates the bet slip.

This is the entry point for GitHub Actions CI.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import load_settings, load_json, get_today_date, logger
from src.csv_tracker import load_todays_bets, append_bets


def has_nba_games_today(date: str = None) -> bool:
    """Check NBA schedule file to see if games are scheduled today."""
    if date is None:
        date = get_today_date()
    settings = load_settings()
    schedule_path = settings.get("schedule", {}).get("nba_schedule_path", "")

    if not schedule_path or not Path(schedule_path).exists():
        # WHY: If no schedule file, assume games are on (fail open)
        logger.warning("No NBA schedule file found — assuming games today")
        return True

    schedule = load_json(schedule_path)
    game_dates = schedule.get("game_dates", [])
    return date in game_dates


def run_sportsbook_pipeline(dry_run: bool = False, from_file: str = None) -> list:
    """
    Run the sportsbook pipeline: projections → odds → EV → Kelly.

    Returns list of sized sportsbook bets.
    """
    from src.odds_ingestion import run as run_ingestion
    from src.ev_calculator import run as run_ev
    from src.kelly_sizer import run as run_kelly

    logger.info("=== Sportsbook Pipeline ===")

    run_ingestion(dry_run=dry_run, from_file=from_file)

    ev_results = run_ev(dry_run=dry_run)
    if not ev_results:
        logger.info("Sportsbook: no +EV bets found")
        return []

    sized_bets = run_kelly(dry_run=dry_run, use_ledger=True)
    for bet in sized_bets:
        bet.setdefault("source", "sportsbook")

    logger.info(f"Sportsbook: {len(sized_bets)} sized bets")
    return sized_bets


def run_kalshi_pipeline(dry_run: bool = False) -> list:
    """
    Run the Kalshi pipeline: markets → EV.

    Returns list of Kalshi bets (already Kelly-sized inside kalshi_ev_calculator).
    """
    from src.kalshi_ingestion import run as run_kalshi_ingestion
    from src.kalshi_ev_calculator import run as run_kalshi_ev

    logger.info("=== Kalshi Pipeline ===")

    try:
        run_kalshi_ingestion(dry_run=dry_run)
    except Exception as e:
        logger.warning(f"Kalshi ingestion failed (skipping): {e}")
        return []

    kalshi_bets = run_kalshi_ev(dry_run=dry_run)
    if not kalshi_bets:
        logger.info("Kalshi: no +EV bets found")
        return []

    logger.info(f"Kalshi: {len(kalshi_bets)} +EV bets")
    return kalshi_bets


def allocate_daily_budget(bets: list, settings: dict) -> list:
    """
    Enforce daily budget cap — best edge first, partial funding for last bet.

    WHY: Prevents overexposure on any single day.
    Bets arrive sorted by edge_pct descending from their respective pipelines.
    """
    daily_limit = settings.get("bankroll", {}).get("daily_limit", 5000)
    unit_size = settings.get("bankroll", {}).get("unit_size", 100)

    # Sort all bets by edge descending (best first)
    bets.sort(key=lambda b: b.get("edge_pct", 0), reverse=True)

    allocated = []
    total_dollars = 0.0

    for bet in bets:
        bet_dollars = bet["units"] * unit_size
        if total_dollars + bet_dollars <= daily_limit:
            allocated.append(bet)
            total_dollars += bet_dollars
        elif total_dollars < daily_limit:
            # WHY: Partial funding for the last bet that would exceed the cap
            remaining = daily_limit - total_dollars
            partial_units = remaining / unit_size
            partial_units = round(partial_units * 2) / 2  # round to nearest 0.5
            if partial_units >= settings.get("kelly", {}).get("min_units", 0.5):
                bet["units"] = partial_units
                allocated.append(bet)
                total_dollars += partial_units * unit_size
            break
        else:
            break

    logger.info(
        f"Budget: ${total_dollars:.0f} / ${daily_limit} allocated across {len(allocated)} bets"
    )
    return allocated


def run(dry_run: bool = False, date: str = None, from_file: str = None) -> None:
    """
    Main bet placer pipeline.

    1. Check if NBA games today
    2. Check for duplicate bets (already placed today)
    3. Run sportsbook + Kalshi pipelines
    4. Apply daily budget cap
    5. Append to master CSV
    6. Generate bet slip
    """
    settings = load_settings()
    if date is None:
        date = get_today_date()

    # Step 1: Check NBA schedule
    if not has_nba_games_today(date):
        logger.info(f"No NBA games on {date} — skipping")
        return

    # Step 2: Check for duplicates
    existing = load_todays_bets(date)
    if existing:
        logger.warning(f"Bets already placed for {date} ({len(existing)} rows in CSV) — skipping")
        return

    # Step 3: Run both pipelines
    sportsbook_bets = run_sportsbook_pipeline(dry_run=dry_run, from_file=from_file)
    kalshi_bets = run_kalshi_pipeline(dry_run=dry_run)

    all_bets = sportsbook_bets + kalshi_bets
    if not all_bets:
        logger.info("No bets from either pipeline — nothing to place")
        return

    # Step 4: Apply daily budget cap
    allocated = allocate_daily_budget(all_bets, settings)
    if not allocated:
        logger.info("No bets survived budget allocation")
        return

    # Step 5: Append to master CSV
    rows_written = append_bets(allocated, date=date)
    logger.info(f"Wrote {rows_written} bets to master CSV")

    # Step 6: Generate bet slip
    from src.bet_slip import run as run_bet_slip
    run_bet_slip(dry_run=dry_run)

    # Summary
    sb_count = sum(1 for b in allocated if b.get("source") == "sportsbook")
    k_count = sum(1 for b in allocated if b.get("source") == "kalshi")
    total_units = sum(b["units"] for b in allocated)
    unit_size = settings.get("bankroll", {}).get("unit_size", 100)
    logger.info(
        f"Placed {len(allocated)} bets ({sb_count} sportsbook, {k_count} Kalshi) "
        f"| {total_units}u = ${total_units * unit_size:.0f}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DBB2 Bet Placer — Daily Orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="Use fixture data")
    parser.add_argument("--date", type=str, default=None, help="Override date (YYYY-MM-DD)")
    parser.add_argument("--from-file", type=str, default=None,
                        help="Load projections from file instead of DBB2 API")
    args = parser.parse_args()
    run(dry_run=args.dry_run, date=args.date, from_file=args.from_file)
