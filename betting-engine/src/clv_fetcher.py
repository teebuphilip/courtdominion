"""
CLV Fetcher — fetch closing lines and calculate Closing Line Value.

Runs BEFORE bet grading. Fetches final market prices for today's PENDING bets,
calculates CLV (positive = model beat the closing line), and writes results
back to master_bets.csv.

Usage:
    python src/clv_fetcher.py                    # Today's pending bets
    python src/clv_fetcher.py --date 2026-02-14  # Specific date
    python src/clv_fetcher.py --dry-run           # No API calls or CSV changes
"""

import argparse
import csv
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import load_settings, write_json, get_today_date, logger
from src.csv_tracker import CSV_PATH, CSV_HEADERS
from src.odds_ingestion import normalize_odds
from src.kalshi_ingestion import (
    authenticate,
    fetch_nba_markets,
    normalize_kalshi_markets,
)


def calculate_sportsbook_clv(
    morning_line: float, closing_line: float, direction: str
) -> float:
    """
    CLV for sportsbook bets.

    OVER: positive CLV = closing line moved UP (market agreed OVER is right).
    UNDER: positive CLV = closing line moved DOWN (market agreed UNDER is right).
    """
    if direction == "OVER":
        return round(closing_line - morning_line, 2)
    else:
        return round(morning_line - closing_line, 2)


def calculate_kalshi_clv(
    morning_price: float, closing_price: float, direction: str
) -> float:
    """
    CLV for Kalshi bets (in probability points).

    YES: positive CLV = YES price rose (market more confident in YES).
    NO: positive CLV = YES price fell (market more confident in NO).
    """
    if direction == "YES":
        return round(closing_price - morning_price, 4)
    else:
        return round(morning_price - closing_price, 4)


def fetch_sportsbook_closing(settings: dict) -> dict:
    """
    Fetch current sportsbook lines from The Odds API.

    WHY: Makes its own API call instead of using fetch_odds() to avoid
    overwriting the morning odds file (data/odds/{date}.json).

    Returns: {(player_name_lower, prop_type): closing_line_float}
    """
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
            logger.warning(f"CLV: Odds API request failed for {market}: {e}")
            continue

        if response.status_code != 200:
            logger.warning(f"CLV: Odds API returned {response.status_code} for {market}")
            continue

        all_odds[market] = response.json()

    normalized = normalize_odds(all_odds)

    # Build lookup keyed by (player_name_lower, prop_type)
    result = {}
    for player_name, props in normalized.items():
        for prop_type, data in props.items():
            line = data.get("line")
            if line is not None:
                result[(player_name.lower().strip(), prop_type)] = line

    logger.info(f"CLV: Fetched closing lines for {len(result)} sportsbook props")
    return result


def fetch_kalshi_closing(settings: dict) -> dict:
    """
    Fetch current Kalshi YES prices.

    WHY: Uses fetch_nba_markets(force=True) to bypass cache, then normalizes.

    Returns: {(player_name_lower, prop_type): closing_yes_price_float}
    """
    try:
        raw_markets = fetch_nba_markets(force=True)
    except Exception as e:
        logger.warning(f"CLV: Kalshi market fetch failed: {e}")
        return {}

    if isinstance(raw_markets, dict):
        normalized = raw_markets
    else:
        normalized = normalize_kalshi_markets(raw_markets)

    result = {}
    for player_name, props in normalized.items():
        for prop_type, data in props.items():
            yes_price = data.get("yes_price")
            if yes_price is not None:
                result[(player_name.lower().strip(), prop_type)] = yes_price

    logger.info(f"CLV: Fetched closing prices for {len(result)} Kalshi props")
    return result


def run(date: str = None, dry_run: bool = False) -> int:
    """
    Main CLV pipeline.

    1. Load CSV, find today's PENDING bets with empty closing_line
    2. Fetch closing lines from sportsbook + Kalshi APIs
    3. Calculate CLV for each matched bet
    4. Rewrite CSV with closing_line + clv filled in
    5. Save audit trail to data/closing_lines/{date}.json

    Returns count of bets updated.
    """
    if date is None:
        date = get_today_date()

    settings = load_settings()
    clv_cfg = settings.get("clv", {})

    if not Path(CSV_PATH).exists():
        logger.info("CLV: No master CSV found, nothing to do")
        return 0

    # Read all CSV rows
    all_rows = []
    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_rows.append(row)

    # Find pending bets that need closing lines
    pending = [
        r for r in all_rows
        if r["date"] == date
        and r["status"] == "PENDING"
        and r.get("closing_line", "") == ""
    ]

    if not pending:
        logger.info(f"CLV: No pending bets need closing lines for {date}")
        return 0

    sb_pending = [r for r in pending if r["source"] == "sportsbook"]
    kal_pending = [r for r in pending if r["source"] == "kalshi"]
    logger.info(
        f"CLV: {len(pending)} pending bets ({len(sb_pending)} sportsbook, "
        f"{len(kal_pending)} Kalshi)"
    )

    if dry_run:
        logger.info("[DRY RUN] Would fetch closing lines — skipping API calls")
        return 0

    # Fetch closing lines
    sb_closing = {}
    kal_closing = {}

    if sb_pending and clv_cfg.get("fetch_closing_sportsbook", True):
        try:
            sb_closing = fetch_sportsbook_closing(settings)
        except Exception as e:
            logger.warning(f"CLV: Sportsbook closing fetch failed: {e}")

    if kal_pending and clv_cfg.get("fetch_closing_kalshi", True):
        try:
            kal_closing = fetch_kalshi_closing(settings)
        except Exception as e:
            logger.warning(f"CLV: Kalshi closing fetch failed: {e}")

    # Save audit trail
    _save_audit(date, sb_closing, kal_closing)

    # Match closing lines to pending bets and calculate CLV
    updated = 0
    for row in all_rows:
        if row["date"] != date or row["status"] != "PENDING":
            continue
        if row.get("closing_line", "") != "":
            continue

        key = (row["player_name"].lower().strip(), row["prop_type"])

        if row["source"] == "sportsbook" and key in sb_closing:
            closing = sb_closing[key]
            try:
                morning = float(row["sportsbook_line"])
            except (ValueError, TypeError):
                continue
            row["closing_line"] = str(closing)
            row["clv"] = str(calculate_sportsbook_clv(morning, closing, row["direction"]))
            updated += 1

        elif row["source"] == "kalshi" and key in kal_closing:
            closing = kal_closing[key]
            try:
                morning = float(row["odds_or_price"])
            except (ValueError, TypeError):
                continue
            row["closing_line"] = str(closing)
            row["clv"] = str(calculate_kalshi_clv(morning, closing, row["direction"]))
            updated += 1

    # Rewrite CSV
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS, restval="", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    logger.info(f"CLV: Updated {updated} of {len(pending)} bets with closing lines")
    return updated


def _save_audit(date: str, sb_closing: dict, kal_closing: dict) -> None:
    """Save closing line data for audit trail."""
    audit = {
        "date": date,
        "sportsbook_closing_lines": {
            f"{k[0]}|{k[1]}": v for k, v in sb_closing.items()
        },
        "kalshi_closing_prices": {
            f"{k[0]}|{k[1]}": v for k, v in kal_closing.items()
        },
        "sportsbook_count": len(sb_closing),
        "kalshi_count": len(kal_closing),
    }
    audit_path = f"data/closing_lines/{date}.json"
    write_json(audit_path, audit)
    logger.info(f"CLV: Audit trail saved to {audit_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DBB2 CLV Fetcher")
    parser.add_argument("--date", type=str, default=None,
                        help="Date to fetch closing lines for (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show pending bets but don't fetch or update")
    args = parser.parse_args()
    count = run(date=args.date, dry_run=args.dry_run)
    if count:
        logger.info(f"Done: {count} bets updated with closing lines")
    else:
        logger.info("Done: no bets updated")
