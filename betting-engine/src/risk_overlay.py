"""
Risk overlay utilities for enhanced shadow betting analysis.
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

from src import load_json, write_json, write_file, logger


def normalize_name(name: str) -> str:
    return (
        (name or "")
        .replace(" Jr.", "")
        .replace(" Sr.", "")
        .replace(" III", "")
        .strip()
        .lower()
    )


def _resolve_risk_path(today: str, settings: dict) -> Path:
    cfg = settings.get("risk_overlay", {})
    daily_path = cfg.get("daily_risk_path_pattern", "data/risk/{date}.json").format(date=today)
    p_daily = Path(daily_path)
    if p_daily.exists():
        return p_daily
    fallback = cfg.get("fallback_risk_path", "../dbb2-engine/output/risk.json")
    return Path(fallback)


def load_risk_map(today: str, settings: dict) -> Dict[str, dict]:
    """
    Load risk rows keyed by normalized player name.
    Returns empty dict if unavailable.
    """
    risk_path = _resolve_risk_path(today, settings)
    if not risk_path.exists():
        logger.warning(f"Risk file not found, enhanced overlay disabled for run: {risk_path}")
        return {}

    rows = load_json(str(risk_path))
    risk_map = {}
    if not isinstance(rows, list):
        return risk_map
    for row in rows:
        key = normalize_name(row.get("name", ""))
        if key:
            risk_map[key] = row
    return risk_map


def _derive_penalty(row: dict, weights: dict) -> Tuple[float, str]:
    if not row:
        return 0.0, "Unknown"

    total = row.get("total_risk")
    level = row.get("risk_level", "Medium")
    if isinstance(total, (int, float)):
        return max(0.0, min(1.0, float(total))), level

    inj = float(row.get("injury_risk", 35)) / 100.0
    mins = float(row.get("minutes_risk", 50)) / 100.0
    vol = float(row.get("volatility", 50)) / 100.0
    penalty = (
        weights.get("injury_risk", 0.5) * inj
        + weights.get("minutes_risk", 0.3) * mins
        + weights.get("volatility", 0.2) * vol
    )
    return max(0.0, min(1.0, penalty)), level


def _decision_id(date: str, bet: dict) -> str:
    key = "|".join(
        [
            date,
            str(bet.get("player_name", "")),
            str(bet.get("prop_type", "")),
            str(bet.get("direction", "")),
            str(bet.get("sportsbook_line", bet.get("line", ""))),
            str(bet.get("source", "")),
        ]
    )
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def apply_enhanced_shadow(
    baseline_bets: List[dict],
    date: str,
    settings: dict,
    risk_map: Dict[str, dict],
) -> Tuple[List[dict], dict]:
    """
    Compute enhanced shadow decisions from baseline allocated bets.
    Returns (enhanced_selected_bets, comparison_summary_payload).
    """
    cfg = settings.get("risk_overlay", {})
    alpha = float(cfg.get("alpha_confidence", 0.35))
    beta = float(cfg.get("beta_units", 0.50))
    edge_mult = float(cfg.get("high_risk_edge_multiplier", 0.80))
    max_avail = float(cfg.get("max_availability_risk", 0.85))
    weights = cfg.get(
        "fallback_weights",
        {"injury_risk": 0.5, "minutes_risk": 0.3, "volatility": 0.2},
    )

    min_edge = float(settings.get("ev_thresholds", {}).get("min_edge_pct", 5.0))
    min_conf = float(settings.get("ev_thresholds", {}).get("min_confidence", 0.60))
    min_units = float(settings.get("kelly", {}).get("min_units", 0.5))
    max_units = float(settings.get("kelly", {}).get("max_units", 3.0))

    shadow = []
    dropped = 0
    changed = 0

    for bet in baseline_bets:
        row = risk_map.get(normalize_name(bet.get("player_name", "")), {})
        penalty, level = _derive_penalty(row, weights)
        availability_risk = float(row.get("availability_risk", penalty))

        base_conf = float(bet.get("confidence", 0.5))
        base_edge = float(bet.get("edge_pct", 0.0))
        base_units = float(bet.get("units", min_units))

        eff_conf = max(0.0, min(1.0, base_conf * (1.0 - alpha * penalty)))
        eff_min_edge = min_edge * (1.0 + edge_mult * penalty)
        eff_units = base_units * (1.0 - beta * penalty)
        eff_units = max(min_units, min(max_units, eff_units))
        eff_units = round(eff_units * 2.0) / 2.0

        blocked = False
        reason = ""
        if availability_risk > max_avail:
            blocked = True
            reason = "availability_guard"
        elif abs(base_edge) < eff_min_edge:
            blocked = True
            reason = "edge_guard"
        elif eff_conf < min_conf:
            blocked = True
            reason = "confidence_guard"

        annotated = {
            **bet,
            "decision_id": _decision_id(date, bet),
            "enhanced_risk_penalty": round(penalty, 3),
            "enhanced_risk_level": level,
            "enhanced_availability_risk": round(availability_risk, 3),
            "enhanced_confidence": round(eff_conf, 3),
            "enhanced_min_edge_required": round(eff_min_edge, 2),
            "enhanced_units": eff_units,
            "enhanced_blocked": blocked,
            "enhanced_block_reason": reason,
        }

        if blocked:
            dropped += 1
            continue

        if eff_units != base_units:
            changed += 1
        annotated["units"] = eff_units
        annotated["source"] = f"{bet.get('source', 'sportsbook')}_enhanced"
        shadow.append(annotated)

    summary = {
        "date": date,
        "baseline_count": len(baseline_bets),
        "enhanced_count": len(shadow),
        "dropped_count": dropped,
        "size_changed_count": changed,
        "baseline_units": round(sum(float(b.get("units", 0.0)) for b in baseline_bets), 2),
        "enhanced_units": round(sum(float(b.get("units", 0.0)) for b in shadow), 2),
        "mode": cfg.get("mode", "off"),
    }
    return shadow, summary


def write_compare_report(date: str, baseline_bets: List[dict], enhanced_bets: List[dict], summary: dict) -> None:
    report_json = f"data/reports/risk_compare_{date}.json"
    report_md = f"data/reports/risk_compare_{date}.md"

    payload = {
        "summary": summary,
        "baseline_bets": baseline_bets,
        "enhanced_bets": enhanced_bets,
    }
    write_json(report_json, payload)

    lines = [
        f"# Risk Compare Report - {date}",
        "",
        f"- Baseline bets: {summary['baseline_count']}",
        f"- Enhanced bets: {summary['enhanced_count']}",
        f"- Dropped by enhanced guards: {summary['dropped_count']}",
        f"- Size-changed bets: {summary['size_changed_count']}",
        f"- Baseline exposure (units): {summary['baseline_units']}",
        f"- Enhanced exposure (units): {summary['enhanced_units']}",
        "",
        "## Enhanced Bets",
        "",
        "| Player | Prop | Dir | Base Units | Enhanced Units | Risk Penalty | Risk Level |",
        "|--------|------|-----|------------|----------------|--------------|------------|",
    ]

    base_index = {
        (b.get("player_name"), b.get("prop_type"), b.get("direction"), b.get("source")): b
        for b in baseline_bets
    }
    for eb in enhanced_bets:
        key = (
            eb.get("player_name"),
            eb.get("prop_type"),
            eb.get("direction"),
            str(eb.get("source", "")).replace("_enhanced", ""),
        )
        base = base_index.get(key, {})
        lines.append(
            "| "
            + f"{eb.get('player_name','')} | {eb.get('prop_type','')} | {eb.get('direction','')} | "
            + f"{base.get('units','')} | {eb.get('units','')} | "
            + f"{eb.get('enhanced_risk_penalty','')} | {eb.get('enhanced_risk_level','')} |"
        )

    write_file(report_md, "\n".join(lines) + "\n")
    logger.info(f"Wrote risk compare report: {report_md}")
