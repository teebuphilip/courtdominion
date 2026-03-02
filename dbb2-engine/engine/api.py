"""
FastAPI server exposing DBB2 projection data + lightweight advanced tools.

Primary endpoints:
- GET /projections/today
- GET /api/internal/baseline-projections (API-key protected)
- POST /tools/lineup/optimize
- GET /tools/similar-players
- GET /tools/streaming-candidates
- POST /tools/trade/analyze
"""

import math
import os
from functools import lru_cache
from typing import Dict, List

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel

from engine import project_all_season
from engine.baseline import PlayerContext
from engine.projections import SeasonProjection
from engine.pricing import AuctionValue

app = FastAPI(title="DBB2 Projection API", version="1.0.0")


class LineupOptimizeRequest(BaseModel):
    player_ids: List[str]
    roster_size: int = 8


class TradeAnalyzeRequest(BaseModel):
    give_player_ids: List[str]
    receive_player_ids: List[str]

# Map engine stat names to betting engine short names
STAT_MAP = {
    "points": "pts",
    "rebounds": "reb",
    "assists": "ast",
    "three_pm": "fg3m",
    "steals": "stl",
    "blocks": "blk",
}

# Variance key format in PlayerContext.stat_variance
VARIANCE_KEY_MAP = {
    "points": "points_variance",
    "rebounds": "rebounds_variance",
    "assists": "assists_variance",
    "three_pm": "three_pm_variance",
    "steals": "steals_variance",
    "blocks": "blocks_variance",
}


@lru_cache(maxsize=1)
def _load_pipeline():
    """Run the full pipeline once and cache results."""
    contexts, projections, auction_values = project_all_season()
    return contexts, projections, auction_values


def _to_fantasy_points(proj: SeasonProjection) -> float:
    return round(
        proj.points * 1.0
        + proj.rebounds * 1.2
        + proj.assists * 1.5
        + proj.steals * 3.0
        + proj.blocks * 3.0
        - proj.turnovers * 1.0,
        1,
    )


def _get_std_dev(ctx: PlayerContext, stat: str) -> float:
    """Get std_dev for a stat from PlayerContext.stat_variance."""
    var_key = VARIANCE_KEY_MAP.get(stat)
    if var_key is None:
        return 0.0
    variance = ctx.stat_variance.get(var_key, 0.0)
    return math.sqrt(max(variance, 0.0))


def _get_confidence(
    projection_value: float,
    std_dev: float,
    base_confidence: float,
) -> float:
    """
    Derive per-stat confidence from consistency and coefficient of variation.

    base_confidence = consistency / 100 (global player consistency)
    Adjusted down by CV: higher variance relative to mean = lower confidence.
    Clamped to [0.40, 0.95].
    """
    if projection_value <= 0 or std_dev <= 0:
        return round(max(0.40, base_confidence * 0.8), 2)

    cv = std_dev / projection_value
    conf = base_confidence * (1 - min(cv, 0.5))
    return round(max(0.40, min(0.95, conf)), 2)


def _build_player_response(
    ctx: PlayerContext,
    proj: SeasonProjection,
) -> Dict:
    """Build the betting engine response shape for one player."""
    base_conf = proj.consistency / 100.0

    result = {
        "id": ctx.player_id,
        "name": ctx.player_name,
        "team": ctx.team,
        "position": ctx.raw_position,
        "is_b2b": ctx.is_b2b,
    }

    for engine_stat, short_name in STAT_MAP.items():
        proj_val = getattr(proj, engine_stat, 0.0)
        std_dev = _get_std_dev(ctx, engine_stat)
        confidence = _get_confidence(proj_val, std_dev, base_conf)

        result[short_name] = round(proj_val, 1)
        result[f"{short_name}_std"] = round(std_dev, 2)
        result[f"{short_name}_conf"] = confidence

    return result


def _safe_cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity with safe zero-norm handling."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _build_similarity_vector(ctx: PlayerContext, proj: SeasonProjection) -> List[float]:
    """
    Build a compact feature vector for player similarity.

    Uses per-game production, efficiency, role, and reliability signals.
    """
    return [
        float(proj.points),
        float(proj.rebounds),
        float(proj.assists),
        float(proj.steals),
        float(proj.blocks),
        float(proj.three_pm),
        float(proj.turnovers),
        float(proj.minutes),
        float(proj.fg_pct),
        float(proj.ft_pct),
        float(proj.usage_rate),
        float(proj.consistency),
        float(ctx.age),
    ]


@app.get("/projections/today")
def get_today_projections():
    """Return all player projections in the betting engine contract shape."""
    contexts, projections, _ = _load_pipeline()

    ctx_map = {c.player_id: c for c in contexts}
    players = []

    for proj in projections:
        ctx = ctx_map.get(proj.player_id)
        if ctx is None:
            continue
        players.append(_build_player_response(ctx, proj))

    return {"players": players}


def _build_internal_player_row(
    ctx: PlayerContext,
    proj: SeasonProjection,
    auction_map: Dict[str, AuctionValue],
) -> Dict:
    auction = auction_map.get(ctx.player_id)
    return {
        "player_id": ctx.player_id,
        "name": ctx.player_name,
        "team": ctx.team,
        "position": ctx.raw_position,
        "age": ctx.age,
        "fantasy_points": _to_fantasy_points(proj),
        "points": round(proj.points, 1),
        "rebounds": round(proj.rebounds, 1),
        "assists": round(proj.assists, 1),
        "steals": round(proj.steals, 1),
        "blocks": round(proj.blocks, 1),
        "turnovers": round(proj.turnovers, 1),
        "three_pointers": round(proj.three_pm, 1),
        "fg_pct": round(proj.fg_pct, 3),
        "ft_pct": round(proj.ft_pct, 3),
        "minutes": round(proj.minutes, 1),
        "games_played_3yr": [],
        "injury_history": {
            "total_games_missed_3yr": 0,
            "severe_injuries": 0,
        },
        "auction_dollar": auction.dollar_value if auction else 1,
        "consistency": int(proj.consistency),
    }


@app.get("/api/internal/baseline-projections")
def get_internal_baseline_projections(
    x_api_key: str = Header(...),
):
    """
    Internal API parity endpoint.

    Requires X-API-Key header matching INTERNAL_API_KEY env var.
    """
    internal_api_key = os.getenv("INTERNAL_API_KEY")
    if not internal_api_key:
        raise HTTPException(status_code=503, detail="Internal API key not configured on server")
    if x_api_key != internal_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    contexts, projections, auction_values = _load_pipeline()
    proj_map = {p.player_id: p for p in projections}
    auction_map = {a.player_id: a for a in auction_values}
    rows = []
    for ctx in contexts:
        proj = proj_map.get(ctx.player_id)
        if proj is None:
            continue
        rows.append(_build_internal_player_row(ctx, proj, auction_map))

    return {"players": rows, "count": len(rows)}


@app.post("/tools/lineup/optimize")
def optimize_lineup(request: LineupOptimizeRequest):
    """Optimize lineup by fantasy points from provided player IDs."""
    player_ids = request.player_ids
    roster_size = request.roster_size
    if roster_size <= 0:
        raise HTTPException(status_code=400, detail="roster_size must be > 0")
    contexts, projections, _ = _load_pipeline()
    ctx_map = {c.player_id: c for c in contexts}
    proj_map = {p.player_id: p for p in projections}

    selected = []
    for player_id in player_ids:
        proj = proj_map.get(player_id)
        ctx = ctx_map.get(player_id)
        if proj is None or ctx is None:
            continue
        selected.append(
            {
                "player_id": player_id,
                "name": ctx.player_name,
                "team": ctx.team,
                "position": ctx.raw_position,
                "fantasy_points": _to_fantasy_points(proj),
            }
        )
    selected.sort(key=lambda x: x["fantasy_points"], reverse=True)
    lineup = selected[:roster_size]
    bench = selected[roster_size:]
    return {
        "lineup": lineup,
        "bench": bench,
        "projected_total_fantasy_points": round(sum(p["fantasy_points"] for p in lineup), 1),
    }


@app.get("/tools/similar-players")
def get_similar_players(
    player_id: str = Query(default="", description="Player ID to compare against"),
    player_name: str = Query(default="", description="Player name to compare against"),
    top_n: int = Query(default=10, ge=1, le=50),
):
    """
    Return players most similar to a target player based on projection profile.

    Provide exactly one of `player_id` or `player_name`.
    """
    target_id = player_id.strip()
    target_name = player_name.strip()
    if bool(target_id) == bool(target_name):
        raise HTTPException(
            status_code=400,
            detail="Provide exactly one of player_id or player_name",
        )

    contexts, projections, auction_values = _load_pipeline()
    ctx_map = {c.player_id: c for c in contexts}
    proj_map = {p.player_id: p for p in projections}
    auction_map = {a.player_id: a for a in auction_values}

    if target_id:
        if target_id not in ctx_map or target_id not in proj_map:
            raise HTTPException(status_code=404, detail="Target player not found")
    else:
        name_to_ids = []
        for c in contexts:
            if c.player_id not in proj_map:
                continue
            if c.player_name.lower() == target_name.lower():
                name_to_ids = [c.player_id]
                break
            if target_name.lower() in c.player_name.lower():
                name_to_ids.append(c.player_id)
        if not name_to_ids:
            raise HTTPException(status_code=404, detail="Target player not found")
        if len(name_to_ids) > 1:
            raise HTTPException(status_code=400, detail="player_name matched multiple players; use player_id")
        target_id = name_to_ids[0]

    target_ctx = ctx_map[target_id]
    target_proj = proj_map[target_id]
    target_vec = _build_similarity_vector(target_ctx, target_proj)

    rows = []
    for c in contexts:
        pid = c.player_id
        if pid == target_id:
            continue
        p = proj_map.get(pid)
        if p is None:
            continue
        sim = _safe_cosine_similarity(target_vec, _build_similarity_vector(c, p))
        auction = auction_map.get(pid)
        rows.append(
            {
                "player_id": pid,
                "name": c.player_name,
                "team": c.team,
                "position": c.raw_position,
                "similarity": round(sim, 4),
                "fantasy_points": _to_fantasy_points(p),
                "auction_dollar": auction.dollar_value if auction else 1,
            }
        )

    rows.sort(key=lambda x: (x["similarity"], x["fantasy_points"]), reverse=True)
    top = rows[:top_n]
    target_auction = auction_map.get(target_id)

    return {
        "target": {
            "player_id": target_id,
            "name": target_ctx.player_name,
            "team": target_ctx.team,
            "position": target_ctx.raw_position,
            "fantasy_points": _to_fantasy_points(target_proj),
            "auction_dollar": target_auction.dollar_value if target_auction else 1,
        },
        "matches": top,
        "count": len(top),
    }


@app.get("/tools/streaming-candidates")
def get_streaming_candidates(limit: int = Query(default=10, ge=1, le=50)):
    """Return short-term streaming candidates emphasizing low auction cost and usable projection."""
    contexts, projections, auction_values = _load_pipeline()
    proj_map = {p.player_id: p for p in projections}
    auction_map = {a.player_id: a for a in auction_values}
    rows = []
    for ctx in contexts:
        proj = proj_map.get(ctx.player_id)
        if proj is None:
            continue
        auction = auction_map.get(ctx.player_id)
        dollar = auction.dollar_value if auction else 1
        fp = _to_fantasy_points(proj)
        stream_score = round(fp / max(dollar, 1), 2)
        rows.append(
            {
                "player_id": ctx.player_id,
                "name": ctx.player_name,
                "team": ctx.team,
                "position": ctx.raw_position,
                "fantasy_points": fp,
                "auction_dollar": dollar,
                "stream_score": stream_score,
            }
        )
    rows.sort(key=lambda x: (x["stream_score"], x["fantasy_points"]), reverse=True)
    return {"candidates": rows[:limit], "count": min(limit, len(rows))}


@app.post("/tools/trade/analyze")
def analyze_trade(request: TradeAnalyzeRequest):
    """Analyze trade value using fantasy points + auction value."""
    give_player_ids = request.give_player_ids
    receive_player_ids = request.receive_player_ids
    contexts, projections, auction_values = _load_pipeline()
    ctx_map = {c.player_id: c for c in contexts}
    proj_map = {p.player_id: p for p in projections}
    auction_map = {a.player_id: a for a in auction_values}

    def pack(player_id: str) -> Dict:
        ctx = ctx_map.get(player_id)
        proj = proj_map.get(player_id)
        if ctx is None or proj is None:
            return {}
        auction = auction_map.get(player_id)
        return {
            "player_id": player_id,
            "name": ctx.player_name,
            "fantasy_points": _to_fantasy_points(proj),
            "auction_dollar": auction.dollar_value if auction else 1,
        }

    give = [p for p in (pack(pid) for pid in give_player_ids) if p]
    receive = [p for p in (pack(pid) for pid in receive_player_ids) if p]

    give_fp = round(sum(p["fantasy_points"] for p in give), 1)
    receive_fp = round(sum(p["fantasy_points"] for p in receive), 1)
    give_auction = round(sum(p["auction_dollar"] for p in give), 1)
    receive_auction = round(sum(p["auction_dollar"] for p in receive), 1)

    delta_fp = round(receive_fp - give_fp, 1)
    delta_auction = round(receive_auction - give_auction, 1)
    verdict = "accept" if (delta_fp > 0 and delta_auction >= -3) or delta_auction > 0 else "decline"

    return {
        "give": give,
        "receive": receive,
        "summary": {
            "give_fantasy_points": give_fp,
            "receive_fantasy_points": receive_fp,
            "delta_fantasy_points": delta_fp,
            "give_auction_dollar": give_auction,
            "receive_auction_dollar": receive_auction,
            "delta_auction_dollar": delta_auction,
            "verdict": verdict,
        },
    }


@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok", "engine": "dbb2", "version": "1.0.0"}
