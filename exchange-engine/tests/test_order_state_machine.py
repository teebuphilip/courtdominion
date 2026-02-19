from datetime import datetime, timedelta, timezone

from src.order_manager import _order_age_seconds
from src.order_model import transition


def test_new_to_open():
    order = {"state": "NEW"}
    updated = transition(order, "OPEN")
    assert updated["state"] == "OPEN"


def test_open_to_filled():
    order = {"state": "OPEN"}
    updated = transition(order, "FILLED")
    assert updated["state"] == "FILLED"


def test_open_to_expired():
    created = (datetime.now(timezone.utc) - timedelta(seconds=700)).isoformat()
    order = {"state": "OPEN", "timestamp": created}
    assert _order_age_seconds(order) > 600
    updated = transition(order, "EXPIRED")
    assert updated["state"] == "EXPIRED"
