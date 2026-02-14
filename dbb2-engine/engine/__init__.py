# DBB2 Engine — runtime projection and pricing logic
#
# Public API:
#   project_all_season() -> (contexts, projections, auction_values)
#   export_json()        -> {filename: filepath}

from engine.baseline import PlayerContext, build_player_contexts_from_csv
from engine.projections import SeasonProjection, project_season
from engine.game_day import GameDayProjection, project_game_day
from engine.pricing import AuctionValue, price_auction
from engine.export import export_all

from typing import Dict, List


def project_all_season(
    seasons_to_load: int = 3,
) -> tuple:
    """
    Full season-long projection pipeline for all players.

    Loads recent CSV data, builds player contexts, projects each player,
    and computes auction values.

    Returns:
        (contexts, projections, auction_values)
    """
    print("Building player contexts from CSV data...")
    contexts = build_player_contexts_from_csv(seasons_to_load)
    print(f"  Built {len(contexts)} player contexts")

    print("Projecting seasons...")
    projections = [project_season(ctx) for ctx in contexts]
    print(f"  Projected {len(projections)} players")

    print("Computing auction values...")
    auction_values = price_auction(projections)
    print(f"  Priced {len(auction_values)} players")

    return contexts, projections, auction_values


def project_all_game_day(
    contexts: List[PlayerContext],
    projections: List[SeasonProjection],
) -> List[GameDayProjection]:
    """
    Apply game-day adjustments to all players.
    PlayerContext objects must have game-day fields populated.
    """
    return [
        project_game_day(ctx, proj)
        for ctx, proj in zip(contexts, projections)
    ]


def export_json(
    contexts: List[PlayerContext],
    projections: List[SeasonProjection],
    auction_values: List[AuctionValue],
    output_dir: str = "output",
) -> Dict[str, str]:
    """Write the 4 CD JSON files."""
    print(f"Exporting JSON to {output_dir}/...")
    files = export_all(contexts, projections, auction_values, output_dir)
    for name, path in files.items():
        print(f"  Written: {path}")
    return files
