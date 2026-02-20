"""
Export engine results to the 4 JSON files expected by CourtDominion.

Output contract:
    players.json:     [{player_id, name, team, position, status}]
    projections.json: [{player_id, ..., tpm, tpa, ..., consistency}]
    risk.json:        [{player_id, injury_risk, volatility, minutes_risk}]
    insights.json:    [{player_id, value_score, risk_score, opportunity_index, notes}]
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from engine.baseline import PlayerContext
from engine.projections import SeasonProjection
from engine.pricing import AuctionValue
from engine.position_map import map_position_to_cd
from engine import lookup
from engine.live_data import compute_remaining_games_fields, normalize_name


def export_all(
    contexts: List[PlayerContext],
    projections: List[SeasonProjection],
    auction_values: List[AuctionValue],
    output_dir: str = "output",
    live_context: Optional[Dict] = None,
) -> Dict[str, str]:
    """
    Write all 4 JSON files. Returns dict of {filename: filepath}.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Build a lookup from player_id to auction value
    auction_map = {v.player_id: v for v in auction_values}

    # Build context map
    context_map = {c.player_id: c for c in contexts}

    # Sort projections by fantasy_points descending
    sorted_projections = sorted(projections, key=lambda p: p.fantasy_points, reverse=True)

    # Build risk data for each player
    risk_data = _build_risk_data(contexts, projections, live_context)
    risk_map = {r["player_id"]: r for r in risk_data}

    files = {}

    # 1. players.json
    players = _build_players_json(contexts)
    players_path = out_path / "players.json"
    _write_json(players_path, players)
    files["players.json"] = str(players_path)

    # 2. projections.json
    proj_json = _build_projections_json(sorted_projections, context_map, live_context)
    proj_path = out_path / "projections.json"
    _write_json(proj_path, proj_json)
    files["projections.json"] = str(proj_path)

    # 3. risk.json
    risk_path = out_path / "risk.json"
    _write_json(risk_path, risk_data)
    files["risk.json"] = str(risk_path)

    # 4. insights.json
    insights = _build_insights_json(contexts, projections, auction_map, risk_map)
    insights_path = out_path / "insights.json"
    _write_json(insights_path, insights)
    files["insights.json"] = str(insights_path)

    return files


def _write_json(path: Path, data: list) -> None:
    """Write JSON array to file."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _build_players_json(contexts: List[PlayerContext]) -> List[dict]:
    """Build players.json entries. Positions mapped to CD 5-position enum."""
    return [
        {
            "player_id": ctx.player_id,
            "name": ctx.player_name,
            "team": ctx.team,
            "position": map_position_to_cd(ctx.raw_position),
            "status": ctx.status,
        }
        for ctx in contexts
    ]


def _build_projections_json(
    projections: List[SeasonProjection],
    context_map: Dict[str, PlayerContext] = None,
    live_context: Optional[Dict] = None,
) -> List[dict]:
    """
    Build projections.json entries.
    Note: three_pm → tpm, three_pa → tpa for CD contract.
    Positions mapped to CD 5-position enum using raw_position from context.
    """
    def _get_cd_position(p):
        if context_map and p.player_id in context_map:
            return map_position_to_cd(context_map[p.player_id].raw_position)
        return map_position_to_cd(p.position)

    entries = []
    for p in projections:
        entry = {
            "player_id": p.player_id,
            "name": p.player_name,
            "team": p.team,
            "position": _get_cd_position(p),
            "minutes": round(p.minutes, 1),
            "usage_rate": round(p.usage_rate, 1),
            "points": round(p.points, 1),
            "rebounds": round(p.rebounds, 1),
            "assists": round(p.assists, 1),
            "steals": round(p.steals, 1),
            "blocks": round(p.blocks, 1),
            "turnovers": round(p.turnovers, 1),
            "fg_pct": round(p.fg_pct, 3),
            "three_pt_pct": round(p.three_pt_pct, 3),
            "ft_pct": round(p.ft_pct, 3),
            "fgm": round(p.fgm, 1),
            "fga": round(p.fga, 1),
            "tpm": round(p.three_pm, 1),
            "tpa": round(p.three_pa, 1),
            "ftm": round(p.ftm, 1),
            "fta": round(p.fta, 1),
            "fantasy_points": round(p.fantasy_points, 1),
            "ceiling": round(p.ceiling, 1),
            "floor": round(p.floor, 1),
            "consistency": _clamp_int(p.consistency, 0, 100),
        }

        if live_context is not None:
            entry.update(
                compute_remaining_games_fields(
                    player_id=p.player_id,
                    player_name=p.player_name,
                    team=p.team,
                    projected_games=p.projected_games,
                    tpm_per_game=p.three_pm,
                    live_ctx=live_context,
                )
            )

        entries.append(entry)

    return entries


def _build_risk_data(
    contexts: List[PlayerContext],
    projections: List[SeasonProjection],
    live_context: Optional[Dict] = None,
) -> List[dict]:
    """
    Build risk.json entries.

    Backward-compatible fields:
    - injury_risk: 100 - (durability_score * 100)
    - volatility: 100 - consistency
    - minutes_risk: from minutes_volatility + role modifier

    Extended fields (legacy uncertainty model parity):
    - availability_risk (0.0-1.0)
    - role_risk (0.0-1.0)
    - composition_risk (0.0-1.0)
    - total_risk (0.0-1.0)
    - risk_level (Low/Medium/High)
    """
    proj_map = {p.player_id: p for p in projections}
    injury_by_id = (live_context or {}).get("injury_by_id", {})
    injury_by_name = (live_context or {}).get("injury_by_name", {})
    risk_data = []

    for ctx in contexts:
        proj = proj_map.get(ctx.player_id)
        consistency = proj.consistency if proj else 50

        # Injury risk from durability
        durability = lookup.lookup_durability(ctx.age, ctx.position, ctx.role)
        if durability is not None:
            durability_score = durability.get("durability_score", 0.65)
            injury_risk = int(100 - durability_score * 100)
        else:
            injury_risk = 35  # moderate default

        # Volatility = inverse of consistency
        volatility = 100 - consistency

        # Minutes risk from usage volatility + role
        usage = lookup.lookup_usage(ctx.age, ctx.position, ctx.role)
        if usage is not None:
            vol_label = usage.get("minutes_volatility", "medium")
            base_risk = {"low": 20, "medium": 50, "high": 80}.get(vol_label, 50)
        else:
            base_risk = 50

        # Role modifier: Bench/Scrub inherently riskier
        role_mod = {"Bench": 15, "Scrub": 20}.get(ctx.role, 0)
        minutes_risk = base_risk + role_mod

        # Legacy uncertainty components
        availability_risk = _calculate_availability_risk(ctx, proj, live_context)
        role_risk = _calculate_role_risk(
            ctx, proj, availability_risk, injury_by_id, injury_by_name
        )
        composition_risk = _calculate_composition_risk(proj)
        total_risk = (
            0.60 * availability_risk
            + 0.25 * role_risk
            + 0.15 * composition_risk
        )
        risk_level = _classify_risk_level(total_risk)

        risk_data.append({
            "player_id": ctx.player_id,
            "name": ctx.player_name,
            "team": ctx.team,
            "injury_risk": _clamp_int(injury_risk, 0, 100),
            "volatility": _clamp_int(volatility, 0, 100),
            "minutes_risk": _clamp_int(minutes_risk, 0, 100),
            "availability_risk": round(_clamp_float(availability_risk, 0.0, 1.0), 3),
            "role_risk": round(_clamp_float(role_risk, 0.0, 1.0), 3),
            "composition_risk": round(_clamp_float(composition_risk, 0.0, 1.0), 3),
            "total_risk": round(_clamp_float(total_risk, 0.0, 1.0), 3),
            "risk_level": risk_level,
        })

    return risk_data


def _build_insights_json(
    contexts: List[PlayerContext],
    projections: List[SeasonProjection],
    auction_map: Dict[str, AuctionValue],
    risk_map: Dict[str, dict],
) -> List[dict]:
    """
    Build insights.json entries.

    value_score: percentile rank of dollar_value
    risk_score: avg of 3 risk metrics
    opportunity_index: high value + low risk composite
    notes: auto-generated one-liner
    """
    # Compute value percentiles from auction values
    dollar_values = sorted(
        [v.dollar_value for v in auction_map.values()], reverse=True
    )
    total_players = len(dollar_values)

    proj_map = {p.player_id: p for p in projections}
    insights = []

    for ctx in contexts:
        auction = auction_map.get(ctx.player_id)
        risk = risk_map.get(ctx.player_id, {})
        proj = proj_map.get(ctx.player_id)

        # Value score: percentile rank
        if auction and total_players > 0:
            rank = sum(1 for d in dollar_values if d > auction.dollar_value)
            value_score = int(100 * (1 - rank / total_players))
        else:
            value_score = 50

        # Risk score: average of 3 risk metrics
        ir = risk.get("injury_risk", 35)
        vol = risk.get("volatility", 50)
        mr = risk.get("minutes_risk", 50)
        risk_score = int((ir + vol + mr) / 3)

        # Opportunity index: value - risk + age bonus + role bonus
        opp = value_score - risk_score
        if ctx.age <= 23:
            opp += 10
        if ctx.role == "Starter":
            opp += 5
        opportunity_index = _clamp_int(int(50 + opp / 2), 0, 100)

        # Notes
        notes = _generate_note(ctx, proj, auction, value_score, risk_score)

        insights.append({
            "player_id": ctx.player_id,
            "value_score": _clamp_int(value_score, 0, 100),
            "risk_score": _clamp_int(risk_score, 0, 100),
            "opportunity_index": opportunity_index,
            "notes": notes,
        })

    return insights


def _generate_note(
    ctx: PlayerContext,
    proj: SeasonProjection,
    auction: AuctionValue,
    value_score: int,
    risk_score: int,
) -> str:
    """Generate a human-readable one-liner note."""
    # Value tier
    if value_score >= 90:
        val_tier = "Elite"
    elif value_score >= 70:
        val_tier = "Strong"
    elif value_score >= 40:
        val_tier = "Moderate"
    else:
        val_tier = "Low"

    # Risk tier
    if risk_score < 30:
        risk_tier = "low risk"
    elif risk_score < 60:
        risk_tier = "moderate risk"
    else:
        risk_tier = "high risk"

    # Consistency tier
    consistency = proj.consistency if proj else 50
    if consistency >= 70:
        cons = "elite consistency"
    elif consistency >= 50:
        cons = "solid consistency"
    else:
        cons = "inconsistent"

    dollar = auction.dollar_value if auction else 1
    return (
        f"{val_tier} value (${dollar}), {risk_tier}. "
        f"{ctx.age_bracket} {ctx.position} {ctx.role} with {cons}."
    )


def _clamp_int(value: int, lo: int, hi: int) -> int:
    """Clamp integer to [lo, hi]."""
    return max(lo, min(hi, value))


def _clamp_float(value: float, lo: float, hi: float) -> float:
    """Clamp float to [lo, hi]."""
    return max(lo, min(hi, value))


def _lookup_injury(
    ctx: PlayerContext,
    injury_by_id: Dict[str, dict],
    injury_by_name: Dict[str, dict],
) -> Optional[dict]:
    by_id = injury_by_id.get(str(ctx.player_id))
    if by_id:
        return by_id
    return injury_by_name.get(normalize_name(ctx.player_name))


def _calculate_availability_risk(
    ctx: PlayerContext,
    proj: Optional[SeasonProjection],
    live_context: Optional[Dict],
) -> float:
    if proj is None:
        return 0.5

    if live_context is not None:
        ros = compute_remaining_games_fields(
            player_id=ctx.player_id,
            player_name=ctx.player_name,
            team=ctx.team,
            projected_games=proj.projected_games,
            tpm_per_game=proj.three_pm,
            live_ctx=live_context,
        )
        team_games_remaining = ros.get("team_games_remaining", 82)
        games_remaining_projected = ros.get("games_remaining_projected", proj.projected_games)
    else:
        team_games_remaining = 82
        games_remaining_projected = min(82, max(0, int(proj.projected_games)))

    if team_games_remaining <= 0:
        return 0.0
    return 1.0 - (games_remaining_projected / float(team_games_remaining))


def _calculate_role_risk(
    ctx: PlayerContext,
    proj: Optional[SeasonProjection],
    availability_risk: float,
    injury_by_id: Dict[str, dict],
    injury_by_name: Dict[str, dict],
) -> float:
    risk_score = 0.0
    minutes = proj.minutes if proj is not None else 25.0

    if minutes >= 32:
        risk_score += 0.05
    elif minutes >= 28:
        risk_score += 0.12
    elif minutes >= 22:
        risk_score += 0.20
    elif minutes >= 15:
        risk_score += 0.28
    else:
        risk_score += 0.35

    injury = _lookup_injury(ctx, injury_by_id, injury_by_name)
    if injury:
        status = str(injury.get("status", "")).lower()
        if "out" in status:
            risk_score += 0.25
        elif "doubtful" in status:
            risk_score += 0.20
        elif "questionable" in status:
            risk_score += 0.12
        elif "probable" in status or "day-to-day" in status:
            risk_score += 0.05

    risk_score += _clamp_float(availability_risk, 0.0, 1.0) * 0.25

    consistency = proj.consistency if proj is not None else 75
    risk_score += ((100 - consistency) / 100.0) * 0.15

    return _clamp_float(risk_score, 0.0, 1.0)


def _calculate_composition_risk(proj: Optional[SeasonProjection]) -> float:
    if proj is None:
        return 0.5

    points_fp = max(0.0, proj.points * 1.0)
    rebounds_fp = max(0.0, proj.rebounds * 1.2)
    assists_fp = max(0.0, proj.assists * 1.5)
    steals_fp = max(0.0, proj.steals * 3.0)
    blocks_fp = max(0.0, proj.blocks * 3.0)
    three_pm_fp = max(0.0, proj.three_pm * 1.0)

    total_positive_fp = points_fp + rebounds_fp + assists_fp + steals_fp + blocks_fp
    if total_positive_fp <= 0:
        return 0.5

    high_variance_fp = steals_fp + blocks_fp + (three_pm_fp * 2.0)
    high_variance_ratio = high_variance_fp / total_positive_fp
    dependency_ratio = max(
        points_fp, rebounds_fp, assists_fp, steals_fp, blocks_fp
    ) / total_positive_fp
    return _clamp_float((high_variance_ratio * 0.6) + (dependency_ratio * 0.4), 0.0, 1.0)


def _classify_risk_level(total_risk: float) -> str:
    if total_risk < 0.25:
        return "Low"
    if total_risk <= 0.55:
        return "Medium"
    return "High"
