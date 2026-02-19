"""Order polling manager with minimal state machine updates."""

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import get_today_date, load_json, load_settings, logger, write_json
from src.order_model import transition


def check_exchange(order: dict) -> str:
    return order.get("state", "OPEN")


def cancel_order(order: dict) -> None:
    logger.info(f"Canceled order {order['order_id']}")


def _order_age_seconds(order: dict) -> float:
    created = datetime.fromisoformat(order["timestamp"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return (now - created).total_seconds()


def poll_open_orders(
    poll_seconds: int = 30,
    max_cycles: Optional[int] = None,
) -> list:
    settings = load_settings()
    today = get_today_date()
    orders_path = f"data/orders/{today}.json"

    if not Path(orders_path).exists():
        return []

    cycles = 0
    while True:
        orders = load_json(orders_path)
        open_orders = [o for o in orders if o["state"] == "OPEN"]
        if not open_orders:
            return orders

        for order in open_orders:
            status = check_exchange(order)
            if status == "FILLED":
                transition(order, "FILLED")
                continue

            if _order_age_seconds(order) > settings["exchange"]["time_in_force_seconds"]:
                cancel_order(order)
                transition(order, "EXPIRED")

        write_json(orders_path, orders)

        cycles += 1
        if max_cycles is not None and cycles >= max_cycles:
            return orders

        time.sleep(poll_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exchange order manager")
    parser.add_argument("--poll-seconds", type=int, default=30)
    parser.add_argument("--max-cycles", type=int, default=None)
    args = parser.parse_args()
    poll_open_orders(poll_seconds=args.poll_seconds, max_cycles=args.max_cycles)
