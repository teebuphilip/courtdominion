"""Kelly sizing for exchange bets."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import get_today_date, load_json, load_settings, logger, write_json


def american_to_decimal(american_odds: int) -> float:
    if american_odds > 0:
        return (american_odds / 100) + 1
    return (100 / abs(american_odds)) + 1


def apply_kelly(bet: dict, settings: dict) -> dict:
    kelly_cfg = settings["kelly"]

    edge_pct = bet["edge_pct"] / 100
    confidence = bet["confidence"]
    odds = bet.get("odds")

    if odds is None:
        return {**bet, "units": kelly_cfg["min_units"], "dollars": 0}

    decimal_odds = american_to_decimal(odds)
    b = decimal_odds - 1
    if b <= 0:
        return {**bet, "units": kelly_cfg["min_units"], "dollars": 0}

    p = min(confidence * (1 + edge_pct), 0.85)
    q = 1 - p

    full_kelly = (b * p - q) / b
    fractional_kelly = full_kelly * kelly_cfg["fraction"]
    units = fractional_kelly * kelly_cfg["bankroll"] / 100

    units = max(kelly_cfg["min_units"], min(units, kelly_cfg["max_units"]))
    units = round(units * 2) / 2
    dollars = round(units * (kelly_cfg["bankroll"] / 100), 2)

    return {
        **bet,
        "units": units,
        "dollars": dollars,
    }


def run(dry_run: bool = False, use_ledger: bool = False) -> list:
    settings = load_settings()
    today = get_today_date()
    ev_path = f"data/ev_results/{today}.json"

    if not Path(ev_path).exists():
        logger.error(f"No EV results file: {ev_path}")
        return []

    if use_ledger:
        from src.ledger import get_current_bankroll

        ledger_bankroll = get_current_bankroll()
        settings["kelly"]["bankroll"] = ledger_bankroll
        logger.info(f"Using ledger bankroll: ${ledger_bankroll:.2f}")

    ev_results = load_json(ev_path)
    sized = [apply_kelly(bet, settings) for bet in ev_results]

    output_path = f"data/sized_bets/{today}.json"
    write_json(output_path, sized)
    logger.info(f"Saved {len(sized)} Kelly-sized bets to {output_path}")
    return sized


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exchange Kelly sizer")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--use-ledger",
        action="store_true",
        help="Read bankroll from data/ledger.json instead of settings.json",
    )
    args = parser.parse_args()
    run(dry_run=args.dry_run, use_ledger=args.use_ledger)
