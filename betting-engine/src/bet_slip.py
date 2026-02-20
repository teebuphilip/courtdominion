"""
Bet Slip Generator — aggregate EV + Kelly + line movement into daily bet slip.

Outputs to terminal (colorized table), JSON, and Markdown.
Supports both sportsbook and Kalshi bets with separate table sections.
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


def run(dry_run: bool = False, source: str = None) -> None:
    """
    Main bet slip generation pipeline.

    source: None = both, "sportsbook" = sportsbook only, "kalshi" = kalshi only
    """
    settings = load_settings()
    today = get_today_date()

    # WHY: Demo-only append path should never alter real JSON bet slip data.
    if source == "polymarket-demo":
        append_polymarket_demo_to_markdown(today, settings)
        return

    sportsbook_bets = []
    kalshi_bets = []

    # Load sportsbook bets
    if source is None or source == "sportsbook":
        sized_path = f"data/sized_bets_{today}.json"
        if Path(sized_path).exists():
            raw = load_json(sized_path)
            for b in raw:
                b.setdefault("source", "sportsbook")
            sportsbook_bets = raw
            movements = detect_movement()
            sportsbook_bets = enrich_with_movement(sportsbook_bets, movements)

    # Load Kalshi bets
    if source is None or source == "kalshi":
        kalshi_path = f"data/kalshi/ev_results_{today}.json"
        if Path(kalshi_path).exists():
            kalshi_bets = load_json(kalshi_path)

    if settings["output"].get("terminal", True):
        output_terminal(sportsbook_bets, kalshi_bets, today, settings)
    if settings["output"].get("json", True):
        output_json(sportsbook_bets, kalshi_bets, today)
    if settings["output"].get("markdown", True):
        output_markdown(sportsbook_bets, kalshi_bets, today, settings)


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


def _volume_flag(volume: int, settings: dict) -> str:
    """Return volume warning flag for Kalshi bets."""
    kalshi_cfg = settings.get("kalshi", {})
    low_warn = kalshi_cfg.get("low_volume_warning", 500)
    if volume >= low_warn:
        return ""
    return "LOW"


def output_terminal(
    sportsbook_bets: list, kalshi_bets: list, today: str, settings: dict
) -> None:
    """Print colorized terminal tables — one per source."""
    bankroll = settings["kelly"]["bankroll"]
    total_bets = len(sportsbook_bets) + len(kalshi_bets)

    print(f"\n{'=' * 70}")
    print(f"  {Fore.GREEN}DBB2 BETTING ENGINE{Style.RESET_ALL} - {today}")
    print(f"  {total_bets} bets | Bankroll: ${bankroll}")
    print(f"{'=' * 70}")

    # Sportsbook section
    if sportsbook_bets:
        print(f"\n  {Fore.GREEN}=== SPORTSBOOK PROPS ==={Style.RESET_ALL}\n")
        headers = ["Player", "Prop", "Dir", "Proj", "Line", "Edge%", "Conf", "Units", "Odds", "Sharp"]
        rows = []
        for bet in sportsbook_bets:
            direction = bet["direction"]
            if direction == "OVER":
                dir_display = f"{Fore.GREEN}OVER{Style.RESET_ALL}"
            else:
                dir_display = f"{Fore.RED}UNDR{Style.RESET_ALL}"
            odds_display = bet.get("over_odds") if direction == "OVER" else bet.get("under_odds")
            sharp_flag = f"{Fore.YELLOW}⚡{Style.RESET_ALL}" if "SHARP" in bet.get("sharp_signal", "") else ""
            rows.append([
                bet["player_name"][:18], bet["prop_type"][:8], dir_display,
                bet["dbb2_projection"], bet["sportsbook_line"],
                f"{bet['edge_pct']}%", f"{int(bet['confidence'] * 100)}%",
                f"{bet['units']}u", odds_display, sharp_flag,
            ])
        if tabulate:
            print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))
        else:
            print("\t".join(headers))
            for row in rows:
                print("\t".join(str(c) for c in row))
        sb_units = sum(b["units"] for b in sportsbook_bets)
        print(f"\n  Sportsbook exposure: {sb_units}u = ${sb_units * (bankroll / 100):.0f}")

    # Kalshi section
    if kalshi_bets:
        print(f"\n  {Fore.GREEN}=== KALSHI PREDICTION MARKETS ==={Style.RESET_ALL}\n")
        headers = ["Player", "Prop", "Dir", "Proj", "Line", "DBB2%", "Kalshi%", "Edge%", "Conf", "Units", "Vol"]
        rows = []
        for bet in kalshi_bets:
            direction = bet["direction"]
            if direction == "YES":
                dir_display = f"{Fore.GREEN}YES{Style.RESET_ALL}"
            else:
                dir_display = f"{Fore.RED}NO{Style.RESET_ALL}"
            vol = bet.get("volume", 0)
            vol_flag = _volume_flag(vol, settings)
            vol_display = f"{vol}" if not vol_flag else f"{vol} {Fore.YELLOW}⚠️{Style.RESET_ALL}"
            rows.append([
                bet["player_name"][:18], bet["prop_type"][:8], dir_display,
                bet["dbb2_projection"], bet["line"],
                f"{bet['dbb2_implied_prob']}%", f"{bet['kalshi_implied_prob']}%",
                f"{bet['edge_pct']}%", f"{int(bet['confidence'] * 100)}%",
                f"{bet['units']}u", vol_display,
            ])
        if tabulate:
            print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))
        else:
            print("\t".join(headers))
            for row in rows:
                print("\t".join(str(c) for c in row))
        k_units = sum(b["units"] for b in kalshi_bets)
        print(f"\n  Kalshi exposure: {k_units}u = ${k_units * (bankroll / 100):.0f}")

    if not sportsbook_bets and not kalshi_bets:
        print("\n  No qualifying bets today.\n")
        return

    total_units = sum(b["units"] for b in sportsbook_bets) + sum(b["units"] for b in kalshi_bets)
    print(f"\n  Total exposure: {total_units}u = ${total_units * (bankroll / 100):.0f}\n")


def output_json(sportsbook_bets: list, kalshi_bets: list, today: str) -> None:
    """Write bet slip as JSON with source labels."""
    all_bets = sportsbook_bets + kalshi_bets
    output_path = f"data/bet_slips/{today}.json"
    write_json(output_path, {
        "date": today,
        "generated_at": get_timestamp(),
        "total_bets": len(all_bets),
        "total_units": sum(b["units"] for b in all_bets),
        "sportsbook_count": len(sportsbook_bets),
        "kalshi_count": len(kalshi_bets),
        "bets": all_bets,
    })
    logger.info(f"JSON bet slip saved: {output_path}")

    # WHY: Separate Kalshi slip for Kalshi-specific grading
    if kalshi_bets:
        kalshi_path = f"data/kalshi/bet_slips/{today}_kalshi.json"
        write_json(kalshi_path, {
            "date": today,
            "generated_at": get_timestamp(),
            "total_bets": len(kalshi_bets),
            "total_units": sum(b["units"] for b in kalshi_bets),
            "bets": kalshi_bets,
        })
        logger.info(f"Kalshi JSON bet slip saved: {kalshi_path}")


def output_markdown(
    sportsbook_bets: list, kalshi_bets: list, today: str, settings: dict
) -> None:
    """Write bet slip as Markdown with both sections."""
    output_path = f"data/bet_slips/{today}.md"
    all_bets = sportsbook_bets + kalshi_bets
    total_units = sum(b["units"] for b in all_bets)

    lines = [
        f"# DBB2 Betting Engine - {today}",
        f"**Generated:** {get_timestamp()}  ",
        f"**Total Bets:** {len(all_bets)}  ",
        f"**Total Units:** {total_units}u",
    ]

    # Sportsbook section
    if sportsbook_bets:
        lines += [
            "",
            "## Sportsbook Props",
            "",
            "| Player | Prop | Dir | DBB2 Proj | Line | Edge% | Conf | Units | Odds | Sharp |",
            "|--------|------|-----|-----------|------|-------|------|-------|------|-------|",
        ]
        for bet in sportsbook_bets:
            sharp_flag = "⚡" if "SHARP" in bet.get("sharp_signal", "") else ""
            odds = bet.get("over_odds") if bet["direction"] == "OVER" else bet.get("under_odds")
            lines.append(
                f"| {bet['player_name']} | {bet['prop_type']} | {bet['direction']} | "
                f"{bet['dbb2_projection']} | {bet['sportsbook_line']} | {bet['edge_pct']}% | "
                f"{int(bet['confidence'] * 100)}% | {bet['units']}u | {odds} | {sharp_flag} |"
            )

    # Kalshi section
    if kalshi_bets:
        lines += [
            "",
            "## Kalshi Prediction Markets",
            "",
            "| Player | Prop | Dir | DBB2 Proj | Line | DBB2% | Kalshi% | Edge% | Conf | Units | Vol |",
            "|--------|------|-----|-----------|------|-------|---------|-------|------|-------|-----|",
        ]
        for bet in kalshi_bets:
            vol = bet.get("volume", 0)
            vol_flag = _volume_flag(vol, settings)
            vol_str = f"{vol}" if not vol_flag else f"{vol} ⚠️"
            lines.append(
                f"| {bet['player_name']} | {bet['prop_type']} | {bet['direction']} | "
                f"{bet['dbb2_projection']} | {bet['line']} | "
                f"{bet['dbb2_implied_prob']}% | {bet['kalshi_implied_prob']}% | "
                f"{bet['edge_pct']}% | {int(bet['confidence'] * 100)}% | "
                f"{bet['units']}u | {vol_str} |"
            )

    ev_cfg = settings["ev_thresholds"]
    lines += [
        "",
        "## Notes",
        "- Sportsbook Edge% = (DBB2 projection - line) / std_dev * 100",
        "- Kalshi Edge% = (DBB2 implied probability - Kalshi price) * 100",
        f"- Units sized via {int(settings['kelly']['fraction'] * 100)}% fractional Kelly",
        f"- Min edge threshold: {ev_cfg['min_edge_pct']}%",
        f"- Min confidence threshold: {int(ev_cfg['min_confidence'] * 100)}%",
        "- ⚡ = sharp money signal (sportsbook) | ⚠️ = low volume (Kalshi)",
    ]

    markdown = "\n".join(lines)

    # WHY: Keep demo comparison visible in the same daily report but isolated from real bets.
    if settings.get("polymarket", {}).get("enabled", False):
        markdown = append_polymarket_demo_section(markdown, today, settings)

    write_file(output_path, markdown)
    logger.info(f"Markdown bet slip saved: {output_path}")


def append_polymarket_demo_section(md_content: str, today: str, settings: dict) -> str:
    """
    Append Polymarket comparison table to markdown content.

    WHY: Users need side-by-side context, but this must stay visibly legal/demo-only.
    """
    demo_path = Path(f"data/polymarket/bet_slips/{today}_polymarket_DEMO.json")
    if not demo_path.exists():
        return md_content

    try:
        demo_data = load_json(str(demo_path))
    except Exception as e:
        logger.warning(f"Could not load Polymarket demo slip: {e}")
        return md_content

    demo_bets = demo_data.get("demo_bets", [])
    if not demo_bets:
        return md_content

    disclaimer = settings.get("polymarket", {}).get(
        "legal_disclaimer",
        "DEMONSTRATION ONLY - US PERSONS CANNOT LEGALLY TRADE ON POLYMARKET",
    )

    md_content += "\n\n---\n\n"
    md_content += "## ⚠️ POLYMARKET COMPARISON (DEMONSTRATION ONLY)\n\n"
    md_content += f"**LEGAL NOTICE:** {disclaimer}\n\n"
    md_content += "| Player | Prop | Line | Side | Edge | DBB2 Prob | PM Prob |\n"
    md_content += "|--------|------|------|------|------|-----------|---------|\n"

    for bet in demo_bets[:10]:
        md_content += (
            f"| {bet.get('player', '')} "
            f"| {bet.get('prop_type', '')} "
            f"| {bet.get('line', '')} "
            f"| {bet.get('bet_side', '')} "
            f"| {bet.get('edge_pct', '')}% "
            f"| {float(bet.get('dbb2_prob', 0)) * 100:.1f}% "
            f"| {float(bet.get('polymarket_prob', 0)) * 100:.1f}% |\n"
        )

    md_content += "\n*These are hypothetical comparisons for educational purposes only.*\n"
    return md_content


def append_polymarket_demo_to_markdown(today: str, settings: dict) -> None:
    """
    Append demo section to existing daily markdown slip in-place.

    WHY: run.sh calls this as a dedicated step after Polymarket EV generation.
    """
    slip_path = Path(f"data/bet_slips/{today}.md")
    if not slip_path.exists():
        logger.warning(f"No markdown bet slip found to append Polymarket demo: {slip_path}")
        return

    current = slip_path.read_text()
    updated = append_polymarket_demo_section(current, today, settings)
    if updated == current:
        logger.info("No Polymarket demo section added (no demo bets found or already absent)")
        return
    write_file(str(slip_path), updated)
    logger.info(f"Appended Polymarket demo section to {slip_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DBB2 Bet Slip Generator")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--source", type=str, default=None,
                        choices=["sportsbook", "kalshi", "polymarket-demo"],
                        help="Generate slip for one source only")
    args = parser.parse_args()
    run(dry_run=args.dry_run, source=args.source)
