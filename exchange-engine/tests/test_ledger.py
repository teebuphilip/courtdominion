from src.ledger import STARTING_BANKROLL, UNIT_DIVISOR, load_ledger


def test_exchange_ledger_bootstrap():
    ledger = load_ledger()
    assert ledger["starting_bankroll"] == STARTING_BANKROLL
    assert ledger["unit_value"] == STARTING_BANKROLL / UNIT_DIVISOR
