"""
Bet Slip Generator — aggregate EV + Kelly + line movement into daily bet slip.

Outputs to terminal (colorized table), JSON, and Markdown.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import load_settings, load_json, write_json, write_file, get_today_date, get_timestamp, logger

try:
    from tabulate import tabulate
except ImportError:
    tabulate = None

try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init()
except ImportError:
    # WHY: Graceful fallback if colorama not installed
    class _NoColor:
        GREEN = RED = YELLOW = RESET_ALL = BRIGHT = ""
    Fore = Style = _NoColor()

from src.line_tracker import detect_movement


def run(dry_run: bool = False) -> None:
    """Main bet slip generation pipeline."""
    settings = load_settings()
    today = get_today_date()
    sized_path = f"data/sized_bets_{today}.json"

    if not Path(sized_path).exists():
        logger.error(f"No sized bets file: {sized_path}")
        return

    sized_bets = load_json(sized_path)
    movements = detect_movement()

    enriched = enrich_with_movement(sized_bets, movements)

    if settings["output"].get("terminal", True):
        output_terminal(enriched, today, settings)
    if settings["output"].get("json", True):
        output_json(enriched, today)
    if settings["output"].get("markdown", True):
        output_markdown(enriched, today, settings)


def enrich_with_movement(bets: list, movements: list) -> list:
    """Add line movement data to each bet."""
    movement_index = {}
    for m in movements:
        key = f"{m['player_name']}_{m['prop_type']}"
        movement_index[key] = m

    for bet in bets:
        key = f"{bet['player_name']}_{bet['prop_type']}"
        movement = movement_index.get(key)
        bet["line_movement"] = movement
        bet["sharp_signal"] = movement["sharp_signal"] if movement else "NONE"

    return bets


def output_terminal(bets: list, today: str, settings: dict) -> None:
    """Print colorized terminal table."""
    bankroll = settings["kelly"]["bankroll"]

    print(f"\n{'=' * 70}")
    print(f"  {Fore.GREEN}DBB2 BETTING ENGINE{Style.RESET_ALL} - {today}")
    print(f"  {len(bets)} bets | Bankroll: ${bankroll}")
    print(f"{'=' * 70}\n")

    if not bets:
        print("  No qualifying bets today.\n")
        return

    headers = ["Player", "Prop", "Dir", "Proj", "Line", "Edge%", "Conf", "Units", "Odds", "Sharp"]
    rows = []

    for bet in bets:
        # WHY: Color code direction for quick visual scanning
        direction = bet["direction"]
        if direction == "OVER":
            dir_display = f"{Fore.GREEN}OVER{Style.RESET_ALL}"
        else:
            dir_display = f"{Fore.RED}UNDR{Style.RESET_ALL}"

        odds_display = bet.get("over_odds") if direction == "OVER" else bet.get("under_odds")
        sharp_flag = f"{Fore.YELLOW}⚡{Style.RESET_ALL}" if "SHARP" in bet.get("sharp_signal", "") else ""

        rows.append([
            bet["player_name"][:18],
            bet["prop_type"][:8],
            dir_display,
            bet["dbb2_projection"],
            bet["sportsbook_line"],
            f"{bet['edge_pct']}%",
            f"{int(bet['confidence'] * 100)}%",
            f"{bet['units']}u",
            odds_display,
            sharp_flag,
        ])

    if tabulate:
        print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))
    else:
        # WHY: Fallback if tabulate not installed
        print("\t".join(headers))
        for row in rows:
            print("\t".join(str(c) for c in row))

    total_units = sum(bet["units"] for bet in bets)
    total_dollars = total_units * (bankroll / 100)
    print(f"\n  Total exposure: {total_units}u = ${total_dollars:.0f}\n")


def output_json(bets: list, today: str) -> None:
    """Write bet slip as JSON."""
    output_path = f"data/bet_slips/{today}.json"
    write_json(output_path, {
        "date": today,
        "generated_at": get_timestamp(),
        "total_bets": len(bets),
        "total_units": sum(bet["units"] for bet in bets),
        "bets": bets,
    })
    logger.info(f"JSON bet slip saved: {output_path}")


def output_markdown(bets: list, today: str, settings: dict) -> None:
    """Write bet slip as Markdown."""
    output_path = f"data/bet_slips/{today}.md"
    total_units = sum(bet["units"] for bet in bets)

    lines = [
        f"# DBB2 Betting Engine - {today}",
        f"**Generated:** {get_timestamp()}  ",
        f"**Total Bets:** {len(bets)}  ",
        f"**Total Units:** {total_units}u",
        "",
        "| Player | Prop | Dir | DBB2 Proj | Line | Edge% | Conf | Units | Odds | Sharp |",
        "|--------|------|-----|-----------|------|-------|------|-------|------|-------|",
    ]

    for bet in bets:
        sharp_flag = "⚡" if "SHARP" in bet.get("sharp_signal", "") else ""
        odds = bet.get("over_odds") if bet["direction"] == "OVER" else bet.get("under_odds")
        lines.append(
            f"| {bet['player_name']} | {bet['prop_type']} | {bet['direction']} | "
            f"{bet['dbb2_projection']} | {bet['sportsbook_line']} | {bet['edge_pct']}% | "
            f"{int(bet['confidence'] * 100)}% | {bet['units']}u | {odds} | {sharp_flag} |"
        )

    ev_cfg = settings["ev_thresholds"]
    lines += [
        "",
        "## Notes",
        "- Edge% = (DBB2 projection - line) / std_dev * 100",
        f"- Units sized via {int(settings['kelly']['fraction'] * 100)}% fractional Kelly",
        f"- Min edge threshold: {ev_cfg['min_edge_pct']}%",
        f"- Min confidence threshold: {int(ev_cfg['min_confidence'] * 100)}%",
        "- ⚡ = sharp money signal detected via line movement",
    ]

    write_file(output_path, "\n".join(lines))
    logger.info(f"Markdown bet slip saved: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DBB2 Bet Slip Generator")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
