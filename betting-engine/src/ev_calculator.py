"""
EV Calculator — compare DBB2 projections against sportsbook lines.

Core formula: edge_pct = (dbb2_projection - sportsbook_line) / std_dev * 100

Positive edge = OVER, negative edge = UNDER.
Only surfaces bets where abs(edge_pct) >= min_edge_pct.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import load_settings, load_json, write_json, get_today_date, logger


def run(dry_run: bool = False) -> list:
    """Main EV calculation pipeline."""
    settings = load_settings()
    today = get_today_date()

    proj_path = f"data/projections/{today}.json"
    odds_path = f"data/odds/{today}.json"

    if not Path(proj_path).exists():
        logger.error(f"No projections file for today: {proj_path}")
        return []
    if not Path(odds_path).exists():
        logger.error(f"No odds file for today: {odds_path}")
        return []

    projections = load_json(proj_path)
    odds = load_json(odds_path)
    output_path = f"data/ev_results_{today}.json"
    rejects_path = f"data/ev_rejections_{today}.json"
    reject_summary_path = f"data/ev_rejection_summary_{today}.json"
    reports_dir = Path("data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    reports_rejects_path = reports_dir / f"ev_rejections_{today}.json"
    reports_summary_path = reports_dir / f"ev_rejection_summary_{today}.json"

    ev_results = []
    rejections = []
    min_edge = settings["ev_thresholds"]["min_edge_pct"]
    min_conf = settings["ev_thresholds"]["min_confidence"]

    def add_rejection(
        player_name: str,
        prop_type: str,
        reason: str,
        detail: str = "",
        *,
        sportsbook_line=None,
        dbb2_projection=None,
        edge_pct=None,
        confidence=None,
    ) -> None:
        rejections.append(
            {
                "player_name": player_name,
                "prop_type": prop_type,
                "reason": reason,
                "detail": detail,
                "sportsbook_line": sportsbook_line,
                "dbb2_projection": dbb2_projection,
                "edge_pct": edge_pct,
                "confidence": confidence,
            }
        )

    for player_name, player_odds in odds.items():
        projection = find_projection_by_name(projections, player_name)

        if projection is None:
            logger.warning(f"No DBB2 projection found for {player_name}, skipping")
            for prop_type, odds_data in player_odds.items():
                add_rejection(
                    player_name,
                    prop_type,
                    "no_projection_match",
                    "No DBB2 projection found for player name",
                    sportsbook_line=odds_data.get("line"),
                )
            continue

        # WHY: Skip B2B players if configured — their projections are less reliable
        if settings["excluded"].get("skip_b2b") and projection.get("is_b2b", False):
            logger.info(f"Skipping {player_name} - back-to-back")
            for prop_type, odds_data in player_odds.items():
                add_rejection(
                    player_name,
                    prop_type,
                    "excluded_back_to_back",
                    "Player excluded by skip_b2b rule",
                    sportsbook_line=odds_data.get("line"),
                    dbb2_projection=(projection.get("props", {}).get(prop_type, {}) or {}).get("projection"),
                    confidence=(projection.get("props", {}).get(prop_type, {}) or {}).get("confidence"),
                )
            continue

        # WHY: Skip death spot players if configured — compound fatigue
        if settings["excluded"].get("skip_death_spots") and projection.get("is_death_spot", False):
            logger.info(f"Skipping {player_name} - death spot ({projection.get('death_spot_type', 'unknown')})")
            for prop_type, odds_data in player_odds.items():
                add_rejection(
                    player_name,
                    prop_type,
                    "excluded_death_spot",
                    f"Player excluded by death spot rule ({projection.get('death_spot_type', 'unknown')})",
                    sportsbook_line=odds_data.get("line"),
                    dbb2_projection=(projection.get("props", {}).get(prop_type, {}) or {}).get("projection"),
                    confidence=(projection.get("props", {}).get(prop_type, {}) or {}).get("confidence"),
                )
            continue

        for prop_type, odds_data in player_odds.items():
            result, reason, detail = calculate_ev_with_reason(
                player_name, projection, prop_type, odds_data
            )
            if result is None:
                add_rejection(
                    player_name,
                    prop_type,
                    reason or "unknown_reject_reason",
                    detail=detail or "",
                    sportsbook_line=odds_data.get("line"),
                    dbb2_projection=(projection.get("props", {}).get(prop_type, {}) or {}).get("projection"),
                    confidence=(projection.get("props", {}).get(prop_type, {}) or {}).get("confidence"),
                )
                continue
            ev_results.append(result)

    # WHY: Sort by abs edge descending - best bets first
    ev_results.sort(key=lambda x: abs(x["edge_pct"]), reverse=True)

    # Filter to only bets above threshold
    qualified = []
    for r in ev_results:
        if abs(r["edge_pct"]) < min_edge:
            add_rejection(
                r["player_name"],
                r["prop_type"],
                "below_edge_threshold",
                f"edge_pct {r['edge_pct']} < min_edge_pct {min_edge}",
                sportsbook_line=r.get("sportsbook_line"),
                dbb2_projection=r.get("dbb2_projection"),
                edge_pct=r.get("edge_pct"),
                confidence=r.get("confidence"),
            )
            continue
        if r["confidence"] < min_conf:
            add_rejection(
                r["player_name"],
                r["prop_type"],
                "below_confidence_threshold",
                f"confidence {r['confidence']} < min_confidence {min_conf}",
                sportsbook_line=r.get("sportsbook_line"),
                dbb2_projection=r.get("dbb2_projection"),
                edge_pct=r.get("edge_pct"),
                confidence=r.get("confidence"),
            )
            continue
        qualified.append(r)

    reject_counts = dict(Counter(r["reason"] for r in rejections))

    write_json(output_path, qualified)
    write_json(rejects_path, rejections)
    write_json(str(reports_rejects_path), rejections)
    write_json(
        reject_summary_path,
        {
            "date": today,
            "qualified_count": len(qualified),
            "evaluated_count": len(ev_results),
            "rejected_count": len(rejections),
            "reason_counts": reject_counts,
            "thresholds": {
                "min_edge_pct": min_edge,
                "min_confidence": min_conf,
            },
        },
    )
    write_json(
        str(reports_summary_path),
        {
            "date": today,
            "qualified_count": len(qualified),
            "evaluated_count": len(ev_results),
            "rejected_count": len(rejections),
            "reason_counts": reject_counts,
            "thresholds": {
                "min_edge_pct": min_edge,
                "min_confidence": min_conf,
            },
        },
    )
    logger.info(f"Found {len(qualified)} +EV spots from {len(ev_results)} total props evaluated")
    if reject_counts:
        logger.info(f"EV reject reason counts: {reject_counts}")
    return qualified


def calculate_ev(
    player_name: str,
    projection: dict,
    prop_type: str,
    odds_data: dict,
) -> dict:
    """
    Calculate expected value for a single player prop.

    Returns None if data is insufficient.
    """
    result, _, _ = calculate_ev_with_reason(player_name, projection, prop_type, odds_data)
    return result


def calculate_ev_with_reason(
    player_name: str,
    projection: dict,
    prop_type: str,
    odds_data: dict,
):
    """Calculate EV and return (result, reason, detail) for reject auditing."""
    props = projection.get("props", {})
    prop_data = props.get(prop_type)

    if prop_data is None:
        return None, "missing_projection_prop", "Projection missing requested prop type"

    dbb2_proj = prop_data.get("projection")
    std_dev = prop_data.get("std_dev")
    confidence = prop_data.get("confidence", 0.5)
    sportsbook_line = odds_data.get("line")

    if dbb2_proj is None:
        return None, "missing_projection_value", "Projection value is null"
    if sportsbook_line is None:
        return None, "missing_sportsbook_line", "Sportsbook line is null"

    # WHY: If std_dev is zero or null, cannot calculate edge
    if std_dev is None or std_dev == 0:
        logger.warning(f"No std_dev for {player_name} {prop_type}, skipping")
        return None, "missing_std_dev", "Projection std_dev is null or zero"

    # WHY: Edge is measured in standard deviations
    # Positive = projection above line = lean OVER
    # Negative = projection below line = lean UNDER
    raw_edge = dbb2_proj - sportsbook_line
    edge_pct = (raw_edge / std_dev) * 100

    direction = "OVER" if edge_pct > 0 else "UNDER"

    return {
        "player_name": player_name,
        "prop_type": prop_type,
        "direction": direction,
        "dbb2_projection": round(dbb2_proj, 1),
        "sportsbook_line": sportsbook_line,
        "raw_edge": round(raw_edge, 1),
        "edge_pct": round(abs(edge_pct), 1),
        "std_dev": round(std_dev, 2),
        "confidence": round(confidence, 2),
        "over_odds": odds_data.get("over_odds"),
        "under_odds": odds_data.get("under_odds"),
        "bookmaker": odds_data.get("bookmaker", "unknown"),
    }, None, None


def find_projection_by_name(projections: dict, player_name: str) -> dict:
    """
    Find a player projection by name matching.

    WHY: The Odds API uses "FirstName LastName", DBB2 may differ.
    Do case-insensitive match, fallback to partial match on last name.
    """
    lower_name = player_name.lower()

    # Exact match
    for player_id, data in projections.items():
        if data.get("name", "").lower() == lower_name:
            return data

    # Fallback: partial match on last name
    parts = lower_name.split()
    if parts:
        last_name = parts[-1]
        for player_id, data in projections.items():
            if last_name in data.get("name", "").lower():
                logger.warning(f"Fuzzy match: {player_name} -> {data.get('name')}")
                return data

    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DBB2 EV Calculator")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    results = run(dry_run=args.dry_run)
    if results:
        logger.info(f"Top bet: {results[0]['player_name']} {results[0]['prop_type']} "
                     f"{results[0]['direction']} ({results[0]['edge_pct']}% edge)")
