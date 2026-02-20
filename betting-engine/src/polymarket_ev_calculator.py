"""
Polymarket EV Calculator (Demonstration Only)

Calculates hypothetical EV for educational comparison.
This module never places trades and all outputs are demo-labeled.
"""

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import load_settings, load_json, write_json, get_today_date, logger
from src.ev_calculator import find_projection_by_name


def normal_cdf_upper_tail(mean: float, std_dev: float, threshold: float) -> float:
    """
    WHY: Convert projection to probability above line without introducing scipy dependency.
    """
    if std_dev <= 0:
        return 0.50
    z = (threshold - mean) / (std_dev * math.sqrt(2))
    prob = 0.5 * (1 - math.erf(z))
    return max(0.01, min(0.99, prob))


def calculate_implied_probability(projection: float, line: float, std_dev: float) -> float:
    """WHY: Thin wrapper keeps formula centralized for tests and readability."""
    return round(normal_cdf_upper_tail(projection, std_dev, line), 4)


def load_dbb2_projections(today: str) -> dict:
    path = Path(f"data/projections/{today}.json")
    if not path.exists():
        raise FileNotFoundError(f"DBB2 projections not found: {path}")
    return load_json(str(path))


def load_polymarket_odds(today: str) -> dict:
    path = Path(f"data/polymarket/odds/{today}.json")
    if not path.exists():
        raise FileNotFoundError(f"Polymarket odds not found: {path}")
    return load_json(str(path))


def calculate_polymarket_ev(projections: dict, polymarket_odds: dict, min_edge_pct: float = 5.0) -> list:
    """
    WHY: Compare model probability to market probability and surface only meaningful disagreements.
    """
    results = []
    for player_name, player_props in polymarket_odds.items():
        projection = find_projection_by_name(projections, player_name)
        if projection is None:
            logger.warning(f"No DBB2 projection for Polymarket player: {player_name}")
            continue

        props = projection.get("props", {})
        for prop_type, market_data in player_props.items():
            if prop_type not in props:
                continue

            line = market_data.get("line")
            yes_price = market_data.get("yes_price")
            no_price = market_data.get("no_price")
            if line is None or yes_price is None or no_price is None:
                continue

            stat = props[prop_type]
            dbb2_proj = stat.get("projection")
            std_dev = stat.get("std_dev", 0)
            confidence = stat.get("confidence", 0.5)
            if dbb2_proj is None or std_dev in (None, 0):
                continue

            dbb2_prob = calculate_implied_probability(dbb2_proj, line, std_dev)
            polymarket_prob = float(yes_price)
            edge = dbb2_prob - polymarket_prob
            edge_pct = edge * 100

            if abs(edge_pct) < min_edge_pct:
                continue

            if edge > 0:
                bet_side = "YES"
                bet_price = yes_price
                display_edge = edge_pct
            else:
                bet_side = "NO"
                bet_price = no_price
                display_edge = -edge_pct

            results.append(
                {
                    "source": "polymarket-demo",
                    "player": player_name,
                    "prop_type": prop_type,
                    "line": line,
                    "dbb2_projection": round(dbb2_proj, 1),
                    "dbb2_prob": round(dbb2_prob, 4),
                    "polymarket_prob": round(polymarket_prob, 4),
                    "edge_pct": round(display_edge, 2),
                    "bet_side": bet_side,
                    "bet_price": round(float(bet_price), 3),
                    "confidence": round(float(confidence), 2),
                    "question": market_data.get("question", ""),
                    "market_id": market_data.get("market_id", ""),
                    "demo_only": True,
                }
            )

    results.sort(key=lambda x: abs(x["edge_pct"]), reverse=True)
    return results


def write_demo_bets(today: str, demo_bets: list, disclaimer: str) -> str:
    """
    WHY: Store hypothetical positions separately so they are never mixed with real bets.
    """
    output_path = f"data/polymarket/bet_slips/{today}_polymarket_DEMO.json"
    write_json(
        output_path,
        {
            "date": today,
            "demo_bets": demo_bets,
            "legal_notice": disclaimer,
            "count": len(demo_bets),
        },
    )
    return output_path


def run() -> list:
    settings = load_settings()
    pm_settings = settings.get("polymarket", {})
    if not pm_settings.get("enabled", False):
        logger.info("Polymarket adapter disabled in settings; skipping EV calculation")
        return []

    print("=" * 70)
    print(pm_settings["legal_disclaimer"])
    print("=" * 70)

    today = get_today_date()
    try:
        projections = load_dbb2_projections(today)
        polymarket_odds = load_polymarket_odds(today)
    except FileNotFoundError as e:
        logger.error(str(e))
        return []

    min_edge = float(pm_settings.get("min_edge_pct", 5.0))
    demo_bets = calculate_polymarket_ev(projections, polymarket_odds, min_edge_pct=min_edge)
    output_path = write_demo_bets(today, demo_bets, pm_settings["legal_disclaimer"])

    logger.info(f"Polymarket demo opportunities: {len(demo_bets)} -> {output_path}")
    if demo_bets:
        for i, bet in enumerate(demo_bets[:3], start=1):
            logger.info(
                f"  {i}. {bet['player']} {bet['prop_type']} {bet['line']} "
                f"{bet['bet_side']} | edge {bet['edge_pct']}%"
            )
    print(pm_settings["legal_disclaimer"])
    return demo_bets


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Polymarket EV Calculator (Demo)")
    parser.parse_args()
    run()
