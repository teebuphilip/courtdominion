"""Exchange EV calculator and TAKE/MAKE decision logic."""

import argparse
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import get_today_date, load_json, load_settings, logger, write_json


def calculate_ev(projection: float, line: float, std_dev: float) -> tuple[float, float, str]:
    raw_edge = projection - line
    edge_pct = (raw_edge / std_dev) * 100
    direction = "OVER" if raw_edge > 0 else "UNDER"
    return raw_edge, edge_pct, direction


def determine_execution(edge_pct_abs: float, settings: dict) -> Optional[str]:
    thresholds = settings["ev_thresholds"]
    if edge_pct_abs >= thresholds["take_edge_pct"]:
        return "TAKE"
    if edge_pct_abs >= thresholds["make_edge_pct"]:
        return "MAKE"
    return None


def evaluate_player_prop(
    player_name: str,
    prop_type: str,
    projection_prop: dict,
    odds_prop: dict,
    settings: dict,
) -> Optional[dict]:
    projection = projection_prop.get("projection")
    std_dev = projection_prop.get("std_dev")
    confidence = projection_prop.get("confidence", 0)
    line = odds_prop.get("line")

    if projection is None or std_dev in (None, 0) or line is None:
        return None

    raw_edge, edge_pct, direction = calculate_ev(projection, line, std_dev)
    edge_abs = abs(edge_pct)

    if direction == "OVER":
        side_market = odds_prop.get("over", {})
    else:
        side_market = odds_prop.get("under", {})

    odds = side_market.get("odds")
    available_size = side_market.get("available_size", 0)

    thresholds = settings["ev_thresholds"]
    if edge_abs < thresholds["make_edge_pct"]:
        return None
    if confidence < thresholds["min_confidence"]:
        return None
    if available_size < thresholds["min_available_size"]:
        return None

    execution_type = determine_execution(edge_abs, settings)
    if execution_type is None:
        return None

    return {
        "player_name": player_name,
        "prop_type": prop_type,
        "direction": direction,
        "projection": round(projection, 2),
        "line": line,
        "raw_edge": round(raw_edge, 2),
        "edge_pct": round(edge_abs, 2),
        "confidence": round(confidence, 2),
        "std_dev": round(std_dev, 2),
        "odds": odds,
        "available_size": available_size,
        "source": odds_prop.get("exchange", "unknown"),
        "execution_type": execution_type,
    }


def run(dry_run: bool = False) -> list:
    settings = load_settings()
    today = get_today_date()

    proj_path = f"data/projections/{today}.json"
    if not Path(proj_path).exists():
        logger.error(f"No projections file for today: {proj_path}")
        return []

    projections = load_json(proj_path)
    include_sources = settings["exchange"].get("include_sources", [])

    results = []
    for source in include_sources:
        odds_path = f"data/exchange_odds/{source}/{today}.json"
        if not Path(odds_path).exists():
            logger.warning(f"Missing odds file for {source}: {odds_path}")
            continue

        source_odds = load_json(odds_path)
        for player_name, props in source_odds.items():
            player_proj = projections.get(player_name, {})
            player_proj_props = player_proj.get("props", {})

            for prop_type, odds_prop in props.items():
                proj_prop = player_proj_props.get(prop_type)
                if proj_prop is None:
                    continue
                result = evaluate_player_prop(
                    player_name=player_name,
                    prop_type=prop_type,
                    projection_prop=proj_prop,
                    odds_prop=odds_prop,
                    settings=settings,
                )
                if result is not None:
                    results.append(result)

    results.sort(key=lambda r: r["edge_pct"], reverse=True)
    results = results[: settings["ev_thresholds"].get("max_bets_per_day", 10)]

    output_path = f"data/ev_results/{today}.json"
    write_json(output_path, results)
    logger.info(f"Saved {len(results)} exchange EV results to {output_path}")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exchange EV calculator")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
