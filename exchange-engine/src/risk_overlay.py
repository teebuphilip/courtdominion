"""Enhanced risk shadow overlay for exchange-engine."""

from pathlib import Path
from typing import Dict, List, Tuple

from src import load_json, logger, write_file, write_json


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
    daily = cfg.get("daily_risk_path_pattern", "data/risk/{date}.json").format(date=today)
    p_daily = Path(daily)
    if p_daily.exists():
        return p_daily
    return Path(cfg.get("fallback_risk_path", "../dbb2-engine/output/risk.json"))


def load_risk_map(today: str, settings: dict) -> Dict[str, dict]:
    risk_path = _resolve_risk_path(today, settings)
    if not risk_path.exists():
        logger.warning(f"Risk file not found for exchange enhanced mode: {risk_path}")
        return {}

    rows = load_json(str(risk_path))
    out = {}
    if not isinstance(rows, list):
        return out
    for row in rows:
        key = normalize_name(row.get("name", ""))
        if key:
            out[key] = row
    return out


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


def apply_enhanced_shadow(
    baseline_sized_bets: List[dict],
    settings: dict,
    risk_map: Dict[str, dict],
) -> Tuple[List[dict], dict]:
    cfg = settings.get("risk_overlay", {})
    alpha = float(cfg.get("alpha_confidence", 0.35))
    beta = float(cfg.get("beta_units", 0.50))
    edge_mult = float(cfg.get("high_risk_edge_multiplier", 0.80))
    max_avail = float(cfg.get("max_availability_risk", 0.85))
    weights = cfg.get(
        "fallback_weights",
        {"injury_risk": 0.5, "minutes_risk": 0.3, "volatility": 0.2},
    )

    thresholds = settings["ev_thresholds"]
    min_conf = float(thresholds["min_confidence"])
    base_make = float(thresholds["make_edge_pct"])
    base_take = float(thresholds["take_edge_pct"])
    max_bets = int(thresholds.get("max_bets_per_day", 10))

    kcfg = settings["kelly"]
    min_units = float(kcfg["min_units"])
    max_units = float(kcfg["max_units"])

    shadow = []
    dropped = 0
    changed = 0

    for bet in baseline_sized_bets:
        row = risk_map.get(normalize_name(bet.get("player_name", "")), {})
        penalty, level = _derive_penalty(row, weights)
        availability_risk = float(row.get("availability_risk", penalty))

        edge = float(bet.get("edge_pct", 0.0))
        conf = float(bet.get("confidence", 0.0))
        units = float(bet.get("units", min_units))

        eff_conf = max(0.0, min(1.0, conf * (1.0 - alpha * penalty)))
        eff_make = base_make * (1.0 + edge_mult * penalty)
        eff_take = base_take * (1.0 + edge_mult * penalty)

        if availability_risk > max_avail or edge < eff_make or eff_conf < min_conf:
            dropped += 1
            continue

        eff_units = units * (1.0 - beta * penalty)
        eff_units = max(min_units, min(max_units, eff_units))
        eff_units = round(eff_units * 2.0) / 2.0
        if eff_units != units:
            changed += 1

        execution_type = "TAKE" if edge >= eff_take else "MAKE"
        shadow.append(
            {
                **bet,
                "units": eff_units,
                "dollars": round(eff_units * (kcfg["bankroll"] / 100), 2),
                "execution_type": execution_type,
                "source": f"{bet.get('source', 'exchange')}_enhanced",
                "enhanced_risk_penalty": round(penalty, 3),
                "enhanced_risk_level": level,
                "enhanced_availability_risk": round(availability_risk, 3),
                "enhanced_confidence": round(eff_conf, 3),
                "enhanced_make_threshold": round(eff_make, 2),
                "enhanced_take_threshold": round(eff_take, 2),
            }
        )

    shadow.sort(key=lambda b: b.get("edge_pct", 0.0), reverse=True)
    shadow = shadow[:max_bets]

    summary = {
        "baseline_count": len(baseline_sized_bets),
        "enhanced_count": len(shadow),
        "dropped_count": dropped,
        "size_changed_count": changed,
        "baseline_units": round(sum(float(b.get("units", 0.0)) for b in baseline_sized_bets), 2),
        "enhanced_units": round(sum(float(b.get("units", 0.0)) for b in shadow), 2),
        "mode": cfg.get("mode", "off"),
    }
    return shadow, summary


def write_compare_report(today: str, baseline_bets: List[dict], enhanced_bets: List[dict], summary: dict) -> None:
    report_json = f"data/reports/risk_compare_{today}.json"
    report_md = f"data/reports/risk_compare_{today}.md"

    write_json(
        report_json,
        {
            "date": today,
            "summary": summary,
            "baseline_bets": baseline_bets,
            "enhanced_bets": enhanced_bets,
        },
    )

    lines = [
        f"# Exchange Risk Compare - {today}",
        "",
        f"- Baseline bets: {summary['baseline_count']}",
        f"- Enhanced bets: {summary['enhanced_count']}",
        f"- Dropped bets: {summary['dropped_count']}",
        f"- Size changed bets: {summary['size_changed_count']}",
        f"- Baseline units: {summary['baseline_units']}",
        f"- Enhanced units: {summary['enhanced_units']}",
        "",
        "| Player | Prop | Dir | Base Units | Enhanced Units | Risk Penalty | Risk Level |",
        "|---|---|---|---|---|---|---|",
    ]

    idx = {
        (b.get("player_name"), b.get("prop_type"), b.get("direction")): b for b in baseline_bets
    }
    for b in enhanced_bets:
        key = (b.get("player_name"), b.get("prop_type"), b.get("direction"))
        base = idx.get(key, {})
        lines.append(
            f"| {b.get('player_name','')} | {b.get('prop_type','')} | {b.get('direction','')} | "
            f"{base.get('units','')} | {b.get('units','')} | {b.get('enhanced_risk_penalty','')} | "
            f"{b.get('enhanced_risk_level','')} |"
        )

    write_file(report_md, "\n".join(lines) + "\n")
    logger.info(f"Wrote exchange risk compare report: {report_md}")
