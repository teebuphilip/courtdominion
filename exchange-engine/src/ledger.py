"""Ledger bankroll state for exchange paper tracking."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import get_timestamp, load_json, logger, write_json

LEDGER_PATH = "data/ledger.json"
STARTING_BANKROLL = 5000.00
UNIT_DIVISOR = 100


def load_ledger() -> dict:
    """Load existing ledger or create a fresh one at $5000 bankroll."""
    if Path(LEDGER_PATH).exists():
        return load_json(LEDGER_PATH)

    ledger = {
        "created_at": get_timestamp(),
        "starting_bankroll": STARTING_BANKROLL,
        "current_bankroll": STARTING_BANKROLL,
        "unit_value": STARTING_BANKROLL / UNIT_DIVISOR,
        "total_bets": 0,
        "wins": 0,
        "losses": 0,
        "pushes": 0,
        "no_action": 0,
        "total_wagered": 0.0,
        "total_pnl": 0.0,
        "roi_pct": 0.0,
        "win_rate_pct": 0.0,
        "daily_log": [],
    }
    save_ledger(ledger)
    logger.info(f"Created new exchange ledger with ${STARTING_BANKROLL:.2f} bankroll")
    return ledger


def save_ledger(ledger: dict) -> None:
    write_json(LEDGER_PATH, ledger)


def get_current_bankroll() -> float:
    return load_ledger()["current_bankroll"]


def get_current_unit_value() -> float:
    return get_current_bankroll() / UNIT_DIVISOR
