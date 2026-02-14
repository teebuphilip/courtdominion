"""
Line Tracker — track line movement and detect sharp money signals.

Snapshots odds throughout the day. Compares earliest vs latest snapshot
to detect movement. Classifies sharp vs public money based on line
direction vs odds juice.
"""

import argparse
import glob
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import load_json, write_json, get_today_date, logger


def snapshot_lines() -> None:
    """
    Save a timestamped snapshot of current odds.

    WHY: Called multiple times per day to capture movement.
    First call = open lines. Subsequent calls = movement detection.
    """
    today = get_today_date()
    now = datetime.now().strftime("%H%M%S")
    odds_path = f"data/odds/{today}.json"

    if not Path(odds_path).exists():
        logger.warning("No odds file found for today, cannot snapshot")
        return

    current_odds = load_json(odds_path)
    snapshot_path = f"data/line_movement/{today}_snapshot_{now}.json"

    write_json(snapshot_path, {
        "timestamp": datetime.now().isoformat(),
        "odds": current_odds,
    })
    logger.info(f"Line snapshot saved: {snapshot_path}")


def detect_movement() -> list:
    """
    Compare earliest snapshot to latest snapshot for today.

    WHY: Line movement reveals bookmaker adjustments.
    Sharp money typically moves lines before public action.
    """
    today = get_today_date()
    snapshots = _get_todays_snapshots(today)

    if len(snapshots) < 2:
        logger.info("Not enough snapshots to detect movement")
        return []

    open_snapshot = load_json(snapshots[0])
    current_snapshot = load_json(snapshots[-1])

    open_odds = open_snapshot.get("odds", {})
    current_odds = current_snapshot.get("odds", {})

    movements = []

    for player_name, current_props in current_odds.items():
        if player_name not in open_odds:
            continue

        open_props = open_odds[player_name]

        for prop_type, current_data in current_props.items():
            if prop_type not in open_props:
                continue

            open_line = open_props[prop_type].get("line")
            current_line = current_data.get("line")

            if open_line is None or current_line is None:
                continue

            line_delta = current_line - open_line

            # WHY: Only flag meaningful moves (0.5+ points)
            if abs(line_delta) >= 0.5:
                movements.append({
                    "player_name": player_name,
                    "prop_type": prop_type,
                    "open_line": open_line,
                    "current_line": current_line,
                    "line_delta": round(line_delta, 1),
                    "direction": "LINE_UP" if line_delta > 0 else "LINE_DOWN",
                    "sharp_signal": classify_sharp_signal(line_delta, current_data),
                })

    if movements:
        logger.info(f"Detected {len(movements)} line movements")
    else:
        logger.info("No significant line movements detected")

    return movements


def classify_sharp_signal(line_delta: float, odds_data: dict) -> str:
    """
    Classify whether line movement is sharp or public money.

    WHY: Sharp money moves lines but odds stay juicy on sharp side.
    If line moves up (books expect more scoring) but under is still -110 = sharp under.
    """
    over_odds = odds_data.get("over_odds")
    under_odds = odds_data.get("under_odds")

    if over_odds is None or under_odds is None:
        return "UNKNOWN"

    # WHY: If line moved up but under is still -110 or better = sharp UNDER
    if line_delta > 0 and under_odds <= -110:
        return "SHARP_UNDER"

    # WHY: If line moved down but over is still -110 or better = sharp OVER
    if line_delta < 0 and over_odds <= -110:
        return "SHARP_OVER"

    return "PUBLIC"


def _get_todays_snapshots(today: str) -> list:
    """Get all snapshot files for today, sorted by time ascending."""
    pattern = f"data/line_movement/{today}_snapshot_*.json"
    files = sorted(glob.glob(pattern))
    return files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DBB2 Line Tracker")
    parser.add_argument("--snapshot", action="store_true",
                        help="Save a snapshot of current lines")
    parser.add_argument("--detect", action="store_true",
                        help="Detect line movement from today's snapshots")
    args = parser.parse_args()

    if args.snapshot:
        snapshot_lines()
    if args.detect:
        movements = detect_movement()
        for m in movements:
            logger.info(f"  {m['player_name']} {m['prop_type']}: "
                        f"{m['open_line']} -> {m['current_line']} "
                        f"({m['direction']}, {m['sharp_signal']})")
    if not args.snapshot and not args.detect:
        snapshot_lines()
        detect_movement()
