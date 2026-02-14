"""
Auction pricing engine.

Converts season-long projections into dollar values ($1-$70 scale)
using z-scores, SGP weights, and position scarcity multipliers.

Target: 12-team league, $200 budget, 13-man rosters.
"""

from dataclasses import dataclass
from typing import Dict, List

from engine.projections import SeasonProjection
from engine import lookup


LEAGUE_SIZE = 12
BUDGET_PER_TEAM = 200
ROSTER_SIZE = 13
TOTAL_BUDGET = LEAGUE_SIZE * BUDGET_PER_TEAM      # $2,400
DRAFTABLE_PLAYERS = LEAGUE_SIZE * ROSTER_SIZE      # 156
MIN_PRICE = 1
MAX_PRICE = 70

# Stats used for z-score + SGP valuation
SGP_STATS = ["points", "rebounds", "assists", "steals", "blocks", "three_pm"]


@dataclass
class AuctionValue:
    """Auction value for a single player."""
    player_id: str = ""
    player_name: str = ""
    position: str = ""
    raw_z_score: float = 0.0       # Sum of raw z-scores
    sgp_value: float = 0.0         # After SGP weighting
    scarcity_adjusted: float = 0.0  # After position scarcity
    dollar_value: int = MIN_PRICE   # Final $1-$70


def price_auction(
    projections: List[SeasonProjection],
) -> List[AuctionValue]:
    """
    Convert season projections into auction dollar values.

    Steps:
    1. For each player, compute z-score per category
    2. Apply SGP weights and position bonuses
    3. Apply position scarcity multiplier
    4. Map to dollar values, budget-constrained
    """
    sgp = lookup.get_sgp_weights()
    category_weights = sgp.get("category_weights", {})
    position_bonuses = sgp.get("position_bonuses", {})

    values = []
    for proj in projections:
        # Z-scores
        zscores = _compute_category_zscores(proj)
        raw_z = sum(zscores.values())

        # SGP weighting with position bonuses
        sgp_val = _apply_sgp_weights(zscores, proj.position, category_weights, position_bonuses)

        # Position scarcity
        scarcity_data = lookup.lookup_position_scarcity(proj.position)
        scarcity_mult = scarcity_data.get("scarcity_multiplier", 1.0)
        scarcity_adjusted = sgp_val * scarcity_mult

        values.append(AuctionValue(
            player_id=proj.player_id,
            player_name=proj.player_name,
            position=proj.position,
            raw_z_score=raw_z,
            sgp_value=sgp_val,
            scarcity_adjusted=scarcity_adjusted,
        ))

    # Map to dollars
    _map_to_dollars(values)

    return values


def _compute_category_zscores(proj: SeasonProjection) -> Dict[str, float]:
    """
    Z-score per category: (player_stat - position_mean) / position_stddev.
    Uses position-specific baselines from ZSCORE_BASELINES.
    """
    baseline = lookup.lookup_zscore_baseline(proj.position)
    zscores = {}

    stat_attr_map = {
        "points": "points",
        "rebounds": "rebounds",
        "assists": "assists",
        "steals": "steals",
        "blocks": "blocks",
        "three_pm": "three_pm",
    }

    for stat in SGP_STATS:
        attr_name = stat_attr_map[stat]
        player_val = getattr(proj, attr_name, 0.0)
        mean_key = f"{stat}_mean"
        stddev_key = f"{stat}_stddev"

        mean_val = baseline.get(mean_key, 0.0)
        stddev_val = baseline.get(stddev_key, 1.0)

        if stddev_val > 0:
            zscores[stat] = (player_val - mean_val) / stddev_val
        else:
            zscores[stat] = 0.0

    return zscores


def _apply_sgp_weights(
    zscores: Dict[str, float],
    position: str,
    category_weights: dict,
    position_bonuses: dict,
) -> float:
    """
    Multiply each z-score by its SGP weight and position bonus.
    Sum all weighted values.
    """
    total = 0.0
    for stat in SGP_STATS:
        z = zscores.get(stat, 0.0)
        cat_weight = category_weights.get(stat, 1.0)
        bonus = position_bonuses.get((stat, position), 1.0)
        total += z * cat_weight * bonus
    return total


def _map_to_dollars(values: List[AuctionValue]) -> None:
    """
    Map scarcity-adjusted values to $1-$70 dollar scale.

    Strategy:
    1. Sort by scarcity_adjusted descending
    2. Top DRAFTABLE_PLAYERS get proportional share of budget
    3. Everyone else gets $1
    4. Clamp to [MIN_PRICE, MAX_PRICE]
    """
    # Sort descending by scarcity-adjusted value
    ranked = sorted(values, key=lambda v: v.scarcity_adjusted, reverse=True)

    # Select draftable pool
    draftable = ranked[:DRAFTABLE_PLAYERS]
    undraftable = ranked[DRAFTABLE_PLAYERS:]

    if not draftable:
        return

    # Shift values so minimum is 0 (handle negative z-scores)
    min_val = min(v.scarcity_adjusted for v in draftable)
    shifted = [v.scarcity_adjusted - min_val for v in draftable]
    total_shifted = sum(shifted)

    if total_shifted <= 0:
        # All players equal — distribute evenly
        even_price = TOTAL_BUDGET // DRAFTABLE_PLAYERS
        for v in draftable:
            v.dollar_value = max(MIN_PRICE, min(MAX_PRICE, even_price))
        for v in undraftable:
            v.dollar_value = MIN_PRICE
        return

    # Reserve $1 per roster spot, distribute remainder proportionally
    reserved = DRAFTABLE_PLAYERS * MIN_PRICE
    distributable = TOTAL_BUDGET - reserved

    # Raw dollar values (proportional share of distributable pool)
    raw_dollars = []
    for val in shifted:
        share = (val / total_shifted) * distributable
        raw_dollars.append(share)

    # Assign dollars: $1 base + proportional share
    for i, v in enumerate(draftable):
        dollar = MIN_PRICE + raw_dollars[i]
        v.dollar_value = max(MIN_PRICE, min(MAX_PRICE, round(dollar)))

    # Undraftable players get $1
    for v in undraftable:
        v.dollar_value = MIN_PRICE

    # Adjust to hit budget target: iteratively tweak top values
    _adjust_budget(draftable, undraftable)


def _adjust_budget(
    draftable: List[AuctionValue],
    undraftable: List[AuctionValue],
) -> None:
    """Fine-tune dollar values to hit exactly TOTAL_BUDGET."""
    all_players = draftable + undraftable
    total = sum(v.dollar_value for v in all_players)
    diff = TOTAL_BUDGET - total

    if diff == 0:
        return

    # Sort draftable by value (highest first) for adjustment
    sorted_draft = sorted(draftable, key=lambda v: v.scarcity_adjusted, reverse=True)

    if diff > 0:
        # Need to add dollars — add to top players
        i = 0
        while diff > 0 and i < len(sorted_draft):
            if sorted_draft[i].dollar_value < MAX_PRICE:
                sorted_draft[i].dollar_value += 1
                diff -= 1
            i += 1
            if i >= len(sorted_draft):
                i = 0
    elif diff < 0:
        # Need to remove dollars — remove from bottom draftable
        i = len(sorted_draft) - 1
        while diff < 0 and i >= 0:
            if sorted_draft[i].dollar_value > MIN_PRICE:
                sorted_draft[i].dollar_value -= 1
                diff += 1
            i -= 1
            if i < 0:
                i = len(sorted_draft) - 1
