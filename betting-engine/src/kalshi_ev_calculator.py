"""
Kalshi EV Calculator — compare DBB2 projections against Kalshi probability prices.

The core difference from sportsbook EV:
  Sportsbook: edge = (projection - line) / std_dev (distance-based)
  Kalshi:     edge = dbb2_implied_prob - kalshi_price (probability-based)

DBB2 projection + std_dev → P(X >= line) via normal CDF → compare vs Kalshi yes_price.
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
    P(X >= threshold) where X ~ N(mean, std_dev).

    WHY: scipy not in requirements — implement with math.erf only.
    Returns probability clamped to [0.01, 0.99] to avoid degenerate bets.
    """
    if std_dev <= 0:
        return 0.50

    # WHY: erf-based normal CDF: P(X >= t) = 0.5 * (1 - erf(z))
    # where z = (t - mean) / (std_dev * sqrt(2))
    z = (threshold - mean) / (std_dev * math.sqrt(2))
    prob = 0.5 * (1 - math.erf(z))

    return max(0.01, min(0.99, prob))


def calculate_kalshi_ev(
    player_name: str,
    projection: dict,
    prop_type: str,
    kalshi_data: dict,
    settings: dict,
) -> dict:
    """
    Calculate EV for a single Kalshi player prop.

    Converts DBB2 projection into a probability of hitting the Kalshi line,
    then compares against Kalshi's market price to find edge.
    """
    props = projection.get("props", {})
    prop_data = props.get(prop_type)

    if prop_data is None:
        return None

    dbb2_proj = prop_data.get("projection")
    std_dev = prop_data.get("std_dev")
    confidence = prop_data.get("confidence", 0.5)
    line = kalshi_data["line"]
    yes_price = kalshi_data["yes_price"]
    no_price = kalshi_data["no_price"]

    if dbb2_proj is None or std_dev is None or std_dev == 0:
        logger.warning(f"No std_dev for {player_name} {prop_type}")
        return None

    # WHY: Kalshi line "25+ points" means player must hit >= 25
    # Convert projection + std_dev into P(player >= line)
    dbb2_implied_prob = normal_cdf_upper_tail(
        mean=dbb2_proj, std_dev=std_dev, threshold=line
    )

    # WHY: Compare DBB2 probability vs Kalshi market price
    # Positive yes_edge = DBB2 thinks YES is more likely than Kalshi prices
    yes_edge = (dbb2_implied_prob - yes_price) * 100
    no_edge = ((1 - dbb2_implied_prob) - no_price) * 100

    kalshi_cfg = settings.get("kalshi", {})
    min_edge = kalshi_cfg.get("min_edge_pct", settings["ev_thresholds"]["min_edge_pct"])

    # WHY: Take the best side, but only if it meets the min edge
    if yes_edge >= no_edge and yes_edge >= min_edge:
        direction = "YES"
        edge_pct = round(yes_edge, 1)
        bet_price = yes_price
    elif no_edge > yes_edge and no_edge >= min_edge:
        direction = "NO"
        edge_pct = round(no_edge, 1)
        bet_price = no_price
    else:
        return None

    units = calculate_kalshi_kelly(edge_pct, bet_price, confidence, settings)

    return {
        "source": "kalshi",
        "player_name": player_name,
        "prop_type": prop_type,
        "direction": direction,
        "line": line,
        "dbb2_projection": round(dbb2_proj, 1),
        "dbb2_implied_prob": round(dbb2_implied_prob * 100, 1),
        "kalshi_price": bet_price,
        "kalshi_implied_prob": round(bet_price * 100, 1),
        "edge_pct": edge_pct,
        "std_dev": round(std_dev, 2),
        "confidence": round(confidence, 2),
        "units": units,
        "ticker": kalshi_data.get("ticker", ""),
        "volume": kalshi_data.get("volume", 0),
    }


def calculate_kalshi_kelly(
    edge_pct: float,
    bet_price: float,
    confidence: float,
    settings: dict,
) -> float:
    """
    Kelly criterion for Kalshi binary payouts.

    WHY: Kalshi payout differs from sportsbook. If you buy YES at $0.55:
      Win = $0.45 profit per contract (receive $1.00, paid $0.55)
      Lose = $0.55 loss per contract
    Kelly: f = (p * win - (1-p) * loss) / win
    """
    kelly_cfg = settings["kelly"]

    p = confidence * (1 + edge_pct / 100)
    p = min(p, 0.85)

    win_amount = 1 - bet_price
    loss_amount = bet_price

    if win_amount <= 0:
        return kelly_cfg["min_units"]

    full_kelly = (p * win_amount - (1 - p) * loss_amount) / win_amount
    fractional_kelly = full_kelly * kelly_cfg["fraction"]

    units = fractional_kelly * kelly_cfg["bankroll"] / 100
    units = max(kelly_cfg["min_units"], min(units, kelly_cfg["max_units"]))
    units = round(units * 2) / 2

    return units


def run(dry_run: bool = False) -> list:
    """Main Kalshi EV calculation pipeline."""
    settings = load_settings()
    today = get_today_date()

    proj_path = f"data/projections/{today}.json"
    kalshi_odds_path = f"data/kalshi/odds/{today}.json"
    output_path = f"data/kalshi/ev_results_{today}.json"

    if not Path(proj_path).exists():
        logger.error(f"No projections file: {proj_path}")
        return []
    if not Path(kalshi_odds_path).exists():
        logger.error(f"No Kalshi odds file: {kalshi_odds_path}")
        return []

    projections = load_json(proj_path)
    kalshi_odds = load_json(kalshi_odds_path)

    ev_results = []

    for player_name, player_kalshi in kalshi_odds.items():
        projection = find_projection_by_name(projections, player_name)

        if projection is None:
            logger.warning(f"No DBB2 projection for Kalshi player: {player_name}")
            continue

        if settings["excluded"].get("skip_b2b") and projection.get("is_b2b", False):
            continue

        for prop_type, kalshi_data in player_kalshi.items():
            result = calculate_kalshi_ev(
                player_name, projection, prop_type, kalshi_data, settings
            )
            if result is not None:
                ev_results.append(result)

    # WHY: Sort by edge descending — best bets first
    ev_results.sort(key=lambda x: x["edge_pct"], reverse=True)

    # Filter by min confidence
    min_conf = settings["ev_thresholds"]["min_confidence"]
    qualified = [r for r in ev_results if r["confidence"] >= min_conf]

    write_json(output_path, qualified)
    logger.info(f"Kalshi: {len(qualified)} +EV spots from {len(ev_results)} props evaluated")
    return qualified


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kalshi EV Calculator")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    results = run(dry_run=args.dry_run)
    if results:
        for r in results[:5]:
            logger.info(
                f"  {r['player_name']} {r['prop_type']} {r['direction']} "
                f"| DBB2: {r['dbb2_implied_prob']}% vs Kalshi: {r['kalshi_implied_prob']}% "
                f"| Edge: {r['edge_pct']}%"
            )
