"""Main exchange engine orchestration flow."""

import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import get_today_date, load_json, load_settings, logger, write_json
from src.bet_slip import run as run_bet_slip
from src.exchange_ev_calculator import run as run_exchange_ev
from src.exchange_ingestion import run as run_exchange_ingestion
from src.kelly_sizer import run as run_kelly
from src.order_manager import poll_open_orders
from src.order_model import build_order, transition
from src.projections import run as run_projections
from src.risk_overlay import load_risk_map, apply_enhanced_shadow, write_compare_report


def _load_sized_bets() -> list:
    today = get_today_date()
    path = Path(f"data/sized_bets/{today}.json")
    if not path.exists():
        return []
    return load_json(str(path))


def _submit_order(order: dict) -> dict:
    if order["execution_type"] == "TAKE":
        return transition(order, "FILLED")

    if order["execution_type"] == "MAKE":
        return transition(order, "OPEN")

    return order


def run(dry_run: bool = False) -> None:
    settings = load_settings()
    today = get_today_date()

    run_projections(dry_run=dry_run)
    run_exchange_ingestion(dry_run=dry_run)
    run_exchange_ev(dry_run=dry_run)
    run_kelly(dry_run=dry_run, use_ledger=True)

    sized_bets = _load_sized_bets()
    if not sized_bets:
        logger.info("No exchange bets to place")
        run_bet_slip()
        write_json(f"data/orders/{today}.json", [])
        return

    orders = []
    tif_seconds = settings["exchange"]["time_in_force_seconds"]
    for bet in sized_bets:
        order = build_order(bet, order_id=str(uuid.uuid4()), tif_seconds=tif_seconds).to_dict()
        order = _submit_order(order)
        orders.append(order)

    write_json(f"data/orders/{today}.json", orders)
    run_bet_slip()
    poll_open_orders(poll_seconds=30, max_cycles=1 if dry_run else None)

    # Enhanced risk shadow track (parallel path).
    risk_cfg = settings.get("risk_overlay", {})
    risk_mode = risk_cfg.get("mode", "off")
    if risk_mode in ("observe", "enforce"):
        risk_map = load_risk_map(today, settings)
        enhanced_sized, summary = apply_enhanced_shadow(
            baseline_sized_bets=sized_bets,
            settings=settings,
            risk_map=risk_map,
        )
        write_json(f"data/sized_bets_enhanced/{today}.json", enhanced_sized)
        write_json(
            f"data/bet_slips_enhanced/{today}.json",
            {
                "date": today,
                "total_bets": len(enhanced_sized),
                "bets": enhanced_sized,
            },
        )

        lines = [
            "| Player | Prop | Dir | Proj | Line | Edge% | Conf | Units | Odds | AvailSize | Source | ExecType |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for bet in enhanced_sized:
            lines.append(
                f"| {bet['player_name']} | {bet['prop_type']} | {bet['direction']} | {bet['projection']} | "
                f"{bet['line']} | {bet['edge_pct']} | {bet['confidence']} | {bet['units']} | {bet['odds']} | "
                f"{bet['available_size']} | {bet['source']} | {bet['execution_type']} |"
            )
        from src import write_file
        write_file(f"data/bet_slips_enhanced/{today}.md", "\n".join(lines) + "\n")

        enhanced_orders = []
        tif_seconds = settings["exchange"]["time_in_force_seconds"]
        for bet in enhanced_sized:
            order = build_order(bet, order_id=str(uuid.uuid4()), tif_seconds=tif_seconds).to_dict()
            order = _submit_order(order)
            enhanced_orders.append(order)
        write_json(f"data/orders_enhanced/{today}.json", enhanced_orders)
        write_compare_report(today, sized_bets, enhanced_sized, summary)

        logger.info(
            f"Enhanced shadow generated: baseline={summary['baseline_count']} "
            f"enhanced={summary['enhanced_count']} dropped={summary['dropped_count']}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exchange bet placer")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
