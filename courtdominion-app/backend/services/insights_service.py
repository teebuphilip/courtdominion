"""
Insights Service
Loads insight data from JSON files and enriches with player data.

Per authoritative specification (Q6):
- ONLY loads/formats JSON
- Does NOT compute
- Does NOT score
- Does NOT correlate

All computation resides in automation.
Backend only merges/enriches for display.
"""

from typing import List
from shared.load_shared_outputs import load_insights, load_projections


def get_all_insights() -> List[dict]:
    """
    Get all player insights enriched with player data.

    Returns:
        List of insight dictionaries merged with player name/team/position
        Returns [] if file missing (per Q4)
    """
    insights = load_insights()
    projections = load_projections()

    # Build projection lookup by player_id
    proj_lookup = {p["player_id"]: p for p in projections}

    # Enrich insights with player data from projections
    enriched = []
    for insight in insights:
        player_id = insight.get("player_id")
        proj = proj_lookup.get(player_id, {})

        # Merge insight with player info
        enriched_insight = {
            **insight,
            "name": proj.get("name", "Unknown Player"),
            "team": proj.get("team", "UNK"),
            "position": proj.get("position", "UNK"),
            # Frontend expects these fields for InsightCard
            "recommendation": _generate_recommendation(insight),
            "reasoning": _generate_reasoning(insight, proj),
            "trending": _determine_trending(insight)
        }
        enriched.append(enriched_insight)

    return enriched


def get_insight_by_player_id(player_id: str) -> dict | None:
    """
    Get insights for specific player.

    Args:
        player_id: Player ID to lookup

    Returns:
        Insight dictionary if found, None otherwise
    """
    insights = get_all_insights()  # Use enriched version

    for insight in insights:
        if insight.get("player_id") == player_id:
            return insight

    return None


def _generate_recommendation(insight: dict) -> str:
    """
    Generate recommendation text based on value and risk scores.

    Args:
        insight: Insight dictionary with value_score and risk_score

    Returns:
        Recommendation string
    """
    value = insight.get("value_score", 0)
    risk = insight.get("risk_score", 50)

    # High value, low risk
    if value >= 80 and risk <= 30:
        return "Add Immediately"
    elif value >= 70 and risk <= 40:
        return "Strong Add"
    elif value >= 60:
        return "Consider Adding"
    elif value >= 40:
        return "Streaming Option"
    elif value >= 30:
        return "Deep League Option"
    else:
        return "Monitor"


def _generate_reasoning(insight: dict, projection: dict) -> str:
    """
    Generate reasoning text based on insight and projection data.

    Args:
        insight: Insight dictionary
        projection: Projection dictionary

    Returns:
        Reasoning string
    """
    value = insight.get("value_score", 0)
    risk = insight.get("risk_score", 50)
    notes = insight.get("notes", "")

    # Get key stats from projection
    minutes = projection.get("minutes", 0)
    points = projection.get("points", 0)
    rebounds = projection.get("rebounds", 0)
    assists = projection.get("assists", 0)

    reasoning_parts = []

    # Value reasoning
    if value >= 70:
        reasoning_parts.append(f"High fantasy value with strong production")
    elif value >= 40:
        reasoning_parts.append(f"Moderate fantasy value")
    else:
        reasoning_parts.append(f"Limited fantasy value")

    # Stats context
    if minutes > 30:
        reasoning_parts.append(f"averaging {minutes:.1f} minutes")

    stat_line = []
    if points > 15:
        stat_line.append(f"{points:.1f} pts")
    if rebounds > 5:
        stat_line.append(f"{rebounds:.1f} reb")
    if assists > 5:
        stat_line.append(f"{assists:.1f} ast")

    if stat_line:
        reasoning_parts.append(" / ".join(stat_line))

    # Risk reasoning
    if risk >= 70:
        reasoning_parts.append("High injury/volatility risk")
    elif risk <= 30:
        reasoning_parts.append("Low risk, consistent performer")

    # Add notes
    if notes:
        reasoning_parts.append(notes.lower())

    return ". ".join(reasoning_parts) + "."


def _determine_trending(insight: dict) -> str:
    """
    Determine trending direction based on opportunity index.

    Args:
        insight: Insight dictionary

    Returns:
        "up", "down", or "neutral"
    """
    opportunity = insight.get("opportunity_index", 35)

    if opportunity >= 38:
        return "up"
    elif opportunity <= 32:
        return "down"
    else:
        return "neutral"


def filter_insights_by_category(insights: List[dict], category: str) -> List[dict]:
    """
    Filter insights by category.

    Categories:
    - high_value: Value score >= 60 (strong/elite value players)
    - sleepers: Value score 40-59 + low ownership (good upside picks)
    - avoid: High risk score >= 70 (injury-prone or volatile)

    Args:
        insights: List of insight dicts
        category: Category to filter by

    Returns:
        Filtered list of insights
    """
    if category == "high_value":
        # Players with strong value (60+)
        return [i for i in insights if i.get("value_score", 0) >= 60]

    elif category == "sleepers":
        # Moderate value with good opportunity
        return [
            i for i in insights
            if 40 <= i.get("value_score", 0) < 60
            and i.get("opportunity_index", 0) >= 35
        ]

    elif category == "avoid":
        # High risk players
        return [i for i in insights if i.get("risk_score", 0) >= 70]

    # Default: return all
    return insights
