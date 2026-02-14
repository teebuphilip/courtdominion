"""
Ledger — bankroll state management and P&L tracking for paper trading.

Persists to data/ledger.json. Generates human-readable markdown summary.
Unit value recalculates after each day: unit_value = current_bankroll / 100.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import load_json, write_json, write_file, get_timestamp, logger

LEDGER_PATH = "data/ledger.json"
STARTING_BANKROLL = 5000.00
UNIT_DIVISOR = 100


def load_ledger() -> dict:
    """Load existing ledger or create fresh one with starting bankroll."""
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
    logger.info(f"Created new ledger with ${STARTING_BANKROLL} bankroll")
    return ledger


def save_ledger(ledger: dict) -> None:
    """Write ledger to JSON."""
    write_json(LEDGER_PATH, ledger)


def get_current_bankroll() -> float:
    """Read current bankroll for Kelly sizer."""
    ledger = load_ledger()
    return ledger["current_bankroll"]


def get_current_unit_value() -> float:
    """Current unit value = bankroll / 100."""
    return get_current_bankroll() / UNIT_DIVISOR


def update_ledger(ledger: dict, results: dict) -> dict:
    """
    Apply a daily results file to the ledger.

    results: output of result_checker.run() — has wins, losses, pushes,
             daily_pnl, and per-bet details.
    """
    date = results["date"]
    wins = results.get("wins", 0)
    losses = results.get("losses", 0)
    pushes = results.get("pushes", 0)
    no_action = results.get("no_action", 0)
    daily_pnl = results.get("daily_pnl", 0.0)

    # Calculate total wagered today
    unit_value = ledger["current_bankroll"] / UNIT_DIVISOR
    total_units = sum(b.get("units", 0) for b in results.get("bets", []))
    daily_wagered = round(total_units * unit_value, 2)

    # Update running totals
    ledger["total_bets"] += wins + losses + pushes + no_action
    ledger["wins"] += wins
    ledger["losses"] += losses
    ledger["pushes"] += pushes
    ledger["no_action"] += no_action
    ledger["total_wagered"] = round(ledger["total_wagered"] + daily_wagered, 2)
    ledger["total_pnl"] = round(ledger["total_pnl"] + daily_pnl, 2)
    ledger["current_bankroll"] = round(ledger["current_bankroll"] + daily_pnl, 2)
    ledger["unit_value"] = round(ledger["current_bankroll"] / UNIT_DIVISOR, 2)

    # Derived stats
    resolved = ledger["wins"] + ledger["losses"]
    if resolved > 0:
        ledger["win_rate_pct"] = round(ledger["wins"] / resolved * 100, 1)
    if ledger["total_wagered"] > 0:
        ledger["roi_pct"] = round(ledger["total_pnl"] / ledger["total_wagered"] * 100, 1)

    # Append daily log entry
    ledger["daily_log"].append({
        "date": date,
        "bets": wins + losses + pushes + no_action,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "no_action": no_action,
        "wagered": daily_wagered,
        "pnl": round(daily_pnl, 2),
        "bankroll_after": ledger["current_bankroll"],
    })

    logger.info(
        f"Ledger updated: {date} — {wins}W-{losses}L-{pushes}P, "
        f"P&L: ${daily_pnl:+.2f}, Bankroll: ${ledger['current_bankroll']:.2f}"
    )
    return ledger


def generate_ledger_markdown(ledger: dict) -> str:
    """Generate human-readable Markdown summary."""
    total_resolved = ledger["wins"] + ledger["losses"]
    record = f"{ledger['wins']}W-{ledger['losses']}L-{ledger['pushes']}P"
    pnl_sign = "+" if ledger["total_pnl"] >= 0 else ""

    lines = [
        "# DBB2 Paper Trading Ledger",
        "",
        f"**Started:** {ledger.get('created_at', 'N/A')[:10]} | "
        f"**Starting Bankroll:** ${ledger['starting_bankroll']:,.2f}",
        "",
        "## Current Status",
        f"- **Bankroll:** ${ledger['current_bankroll']:,.2f}",
        f"- **Total P&L:** {pnl_sign}${ledger['total_pnl']:,.2f}",
        f"- **Record:** {record} ({ledger['win_rate_pct']}% win rate)",
        f"- **ROI:** {ledger['roi_pct']}%",
        f"- **Current Unit:** ${ledger['unit_value']:.2f}",
        f"- **Total Wagered:** ${ledger['total_wagered']:,.2f}",
        "",
        "## Daily Results",
        "",
        "| Date | Bets | W-L-P | Wagered | P&L | Bankroll |",
        "|------|------|-------|---------|-----|----------|",
    ]

    for day in ledger.get("daily_log", []):
        pnl_str = f"+${day['pnl']:.2f}" if day["pnl"] >= 0 else f"-${abs(day['pnl']):.2f}"
        wlp = f"{day['wins']}-{day['losses']}-{day['pushes']}"
        lines.append(
            f"| {day['date']} | {day['bets']} | {wlp} | "
            f"${day['wagered']:,.2f} | {pnl_str} | ${day['bankroll_after']:,.2f} |"
        )

    return "\n".join(lines) + "\n"
