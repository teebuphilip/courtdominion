"""
CSV Tracker — append-only master CSV for all bets across sportsbook and Kalshi.

data/bets/master_bets.csv is the single source of truth for season-long tracking.
Never overwrites existing rows — new bets are appended, grading updates in-place.
"""

import csv
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import load_settings, get_today_date, logger

CSV_PATH = "data/bets/master_bets.csv"

CSV_HEADERS = [
    "bet_id", "date", "source", "player_name", "team", "prop_type", "direction",
    "dbb2_projection", "sportsbook_line", "edge_pct", "confidence", "units",
    "dollar_amount", "odds_or_price", "dbb2_implied_prob", "market_implied_prob",
    "actual_result", "status", "pnl", "closing_line", "clv", "notes",
]


def ensure_csv_exists() -> None:
    """Create CSV with headers if it doesn't exist."""
    p = Path(CSV_PATH)
    if p.exists():
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
    logger.info(f"Created master CSV: {CSV_PATH}")


def load_todays_bets(date: str = None) -> list:
    """Load all bets for a given date to check for duplicates."""
    if date is None:
        date = get_today_date()
    if not Path(CSV_PATH).exists():
        return []
    rows = []
    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("date") == date:
                rows.append(row)
    return rows


def append_bets(bets: list, date: str = None) -> int:
    """
    Append new bets to master CSV as PENDING rows.

    Returns number of rows written.
    """
    if date is None:
        date = get_today_date()
    settings = load_settings()
    unit_size = settings.get("bankroll", {}).get("unit_size", 100)

    ensure_csv_exists()

    rows_written = 0
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)

        for bet in bets:
            source = bet.get("source", "sportsbook")
            units = bet.get("units", 0)
            dollar_amount = round(units * unit_size, 2)

            # WHY: Map odds/price based on source
            if source == "kalshi":
                odds_or_price = str(bet.get("kalshi_price", ""))
                dbb2_implied_prob = bet.get("dbb2_implied_prob", "")
                market_implied_prob = bet.get("kalshi_implied_prob", "")
                line = bet.get("line", "")
            else:
                direction = bet.get("direction", "")
                if direction == "OVER":
                    odds_or_price = str(bet.get("over_odds", ""))
                else:
                    odds_or_price = str(bet.get("under_odds", ""))
                dbb2_implied_prob = ""
                market_implied_prob = ""
                line = bet.get("sportsbook_line", "")

            # WHY: Collect notes for sharp signals, B2B, low volume
            notes_parts = []
            if bet.get("sharp_signal", "NONE") != "NONE":
                notes_parts.append(bet["sharp_signal"])
            volume = bet.get("volume", 0)
            low_warn = settings.get("kalshi", {}).get("low_volume_warning", 500)
            if source == "kalshi" and volume and volume < low_warn:
                notes_parts.append("low_volume")

            row = {
                "bet_id": str(uuid.uuid4())[:8],
                "date": date,
                "source": source,
                "player_name": bet.get("player_name", ""),
                "team": bet.get("team", ""),
                "prop_type": bet.get("prop_type", ""),
                "direction": bet.get("direction", ""),
                "dbb2_projection": bet.get("dbb2_projection", ""),
                "sportsbook_line": line,
                "edge_pct": bet.get("edge_pct", ""),
                "confidence": bet.get("confidence", ""),
                "units": units,
                "dollar_amount": dollar_amount,
                "odds_or_price": odds_or_price,
                "dbb2_implied_prob": dbb2_implied_prob,
                "market_implied_prob": market_implied_prob,
                "actual_result": "",
                "status": "PENDING",
                "pnl": "",
                "closing_line": "",
                "clv": "",
                "notes": ",".join(notes_parts),
            }
            writer.writerow(row)
            rows_written += 1

    logger.info(f"Appended {rows_written} bets to {CSV_PATH}")
    return rows_written


def update_graded_bets(date: str, graded_results: list) -> int:
    """
    Update PENDING bets for a date with actual results and P&L.

    WHY: Full CSV rewrite preserving all history — only today's PENDING rows change.
    """
    if not Path(CSV_PATH).exists():
        logger.warning("No CSV to update")
        return 0

    # Build lookup: (player_name, prop_type, direction) → graded result
    result_map = {}
    for g in graded_results:
        key = (g["player_name"].lower(), g["prop_type"], g.get("direction", ""))
        result_map[key] = g

    all_rows = []
    updated = 0

    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["date"] == date and row["status"] == "PENDING":
                key = (row["player_name"].lower(), row["prop_type"], row["direction"])
                graded = result_map.get(key)
                if graded:
                    row["actual_result"] = graded.get("actual_stat", "")
                    row["status"] = graded.get("outcome", "NO_ACTION")
                    row["pnl"] = graded.get("payout_dollars", 0)
                    updated += 1
            all_rows.append(row)

    # Rewrite CSV
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS, restval="", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    logger.info(f"Updated {updated} graded bets in {CSV_PATH}")
    return updated
