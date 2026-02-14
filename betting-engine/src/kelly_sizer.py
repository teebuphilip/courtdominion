"""
Kelly Sizer — calculate recommended bet size using fractional Kelly criterion.

Given EV results, compute units for each bet.
Full Kelly is mathematically optimal but too aggressive for real use.
We use 25% Kelly (configurable via settings.kelly.fraction).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import load_settings, load_json, write_json, get_today_date, logger


def run(dry_run: bool = False, use_ledger: bool = False) -> list:
    """Main Kelly sizing pipeline."""
    settings = load_settings()
    today = get_today_date()
    ev_path = f"data/ev_results_{today}.json"

    if not Path(ev_path).exists():
        logger.error(f"No EV results file: {ev_path}")
        return []

    # Override bankroll from ledger if requested (paper trading mode)
    if use_ledger:
        from src.ledger import get_current_bankroll
        ledger_bankroll = get_current_bankroll()
        settings["kelly"]["bankroll"] = ledger_bankroll
        logger.info(f"Using ledger bankroll: ${ledger_bankroll:.2f}")

    ev_results = load_json(ev_path)
    output_path = f"data/sized_bets_{today}.json"

    sized_bets = []
    for bet in ev_results:
        sized = apply_kelly(bet, settings)
        sized_bets.append(sized)

    # WHY: Enforce max bets per day (already sorted by edge desc from EV calc)
    max_bets = settings["ev_thresholds"]["max_bets_per_day"]
    sized_bets = sized_bets[:max_bets]

    write_json(output_path, sized_bets)
    logger.info(f"Sized {len(sized_bets)} bets, saved to {output_path}")
    return sized_bets


def apply_kelly(bet: dict, settings: dict) -> dict:
    """
    Apply fractional Kelly criterion to a single bet.

    Kelly formula: f = (bp - q) / b
    b = decimal odds - 1
    p = win probability (confidence * edge as proxy)
    q = 1 - p
    """
    kelly_cfg = settings["kelly"]
    edge_pct = bet["edge_pct"] / 100  # convert to decimal
    confidence = bet["confidence"]
    odds = get_american_odds(bet)

    if odds is None:
        return {
            **bet,
            "units": kelly_cfg["min_units"],
            "decimal_odds": 0,
            "kelly_raw": 0,
            "kelly_fractional": 0,
            "kelly_note": "missing_odds",
        }

    decimal_odds = american_to_decimal(odds)
    b = decimal_odds - 1

    if b <= 0:
        return {
            **bet,
            "units": kelly_cfg["min_units"],
            "decimal_odds": round(decimal_odds, 3),
            "kelly_raw": 0,
            "kelly_fractional": 0,
            "kelly_note": "invalid_odds",
        }

    # WHY: Scale win probability by edge strength
    p = confidence * (1 + edge_pct)
    # WHY: Cap at 85% - never assume certainty
    p = min(p, 0.85)
    q = 1 - p

    full_kelly = (b * p - q) / b
    fractional_kelly = full_kelly * kelly_cfg["fraction"]

    # WHY: Convert to units using bankroll
    units = fractional_kelly * kelly_cfg["bankroll"] / 100

    # WHY: Clamp to protect bankroll from extreme recommendations
    units = max(kelly_cfg["min_units"], min(units, kelly_cfg["max_units"]))

    # WHY: Round to nearest 0.5 unit for clean sizing
    units = round(units * 2) / 2

    return {
        **bet,
        "units": units,
        "decimal_odds": round(decimal_odds, 3),
        "kelly_raw": round(full_kelly, 4),
        "kelly_fractional": round(fractional_kelly, 4),
    }


def american_to_decimal(american_odds: int) -> float:
    """
    Convert American odds to decimal.

    WHY: American odds sign determines formula.
    +150 = risk 100 to win 150 = 2.50 decimal
    -150 = risk 150 to win 100 = 1.667 decimal
    """
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1


def get_american_odds(bet: dict) -> int:
    """Return the odds for the direction we're betting."""
    if bet["direction"] == "OVER":
        return bet.get("over_odds")
    else:
        return bet.get("under_odds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DBB2 Kelly Sizer")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--use-ledger", action="store_true",
                        help="Read bankroll from data/ledger.json instead of settings.json")
    args = parser.parse_args()
    results = run(dry_run=args.dry_run, use_ledger=args.use_ledger)
    if results:
        total_units = sum(b["units"] for b in results)
        logger.info(f"Total exposure: {total_units}u across {len(results)} bets")
