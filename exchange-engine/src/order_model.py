"""Order model and state transitions."""

from dataclasses import asdict, dataclass

from src import get_timestamp


@dataclass
class Order:
    order_id: str
    timestamp: str
    exchange: str
    player_name: str
    prop_type: str
    direction: str
    line: float
    odds: int
    units: float
    dollars: float
    execution_type: str
    state: str
    time_in_force_seconds: int

    def to_dict(self) -> dict:
        return asdict(self)


def build_order(bet: dict, order_id: str, tif_seconds: int) -> Order:
    return Order(
        order_id=order_id,
        timestamp=get_timestamp(),
        exchange=bet["source"],
        player_name=bet["player_name"],
        prop_type=bet["prop_type"],
        direction=bet["direction"],
        line=bet["line"],
        odds=bet["odds"],
        units=bet["units"],
        dollars=bet["dollars"],
        execution_type=bet["execution_type"],
        state="NEW",
        time_in_force_seconds=tif_seconds,
    )


def transition(order: dict, new_state: str) -> dict:
    valid = {
        "NEW": {"OPEN", "FILLED"},
        "OPEN": {"FILLED", "EXPIRED"},
        "FILLED": set(),
        "EXPIRED": set(),
    }
    current = order["state"]
    if new_state not in valid[current]:
        raise ValueError(f"Invalid transition: {current} -> {new_state}")
    order["state"] = new_state
    return order
