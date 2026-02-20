import pytest

from src.polymarket_ingestion import parse_market_question, normalize_polymarket_markets
from src.polymarket_ev_calculator import (
    calculate_implied_probability,
    calculate_polymarket_ev,
    write_demo_bets,
)


def test_market_parsing():
    questions = [
        "Will LeBron James score 25+ points vs Warriors?",
        "Steph Curry to make 3+ three-pointers?",
        "Giannis Antetokounmpo 10+ rebounds?",
    ]
    parsed = [parse_market_question(q) for q in questions]
    assert parsed[0]["player_name"] == "Lebron James"
    assert parsed[0]["prop_type"] == "points"
    assert parsed[0]["line"] == 25.0
    assert parsed[1]["prop_type"] == "threes"
    assert parsed[2]["prop_type"] == "rebounds"


def test_probability_calculation():
    # Given projection=26, line=24.5, std_dev=3.0
    # P(X > 24.5) ~= 0.6915 under normal assumptions.
    prob = calculate_implied_probability(26.0, 24.5, 3.0)
    assert prob == pytest.approx(0.6915, abs=0.01)


def test_edge_calculation():
    projections = {
        "p1": {
            "name": "Luka Doncic",
            "props": {
                "points": {
                    "projection": 31.0,
                    "std_dev": 3.0,
                    "confidence": 0.7,
                }
            },
        }
    }
    odds = {
        "Luka Doncic": {
            "points": {
                "line": 28.5,
                "yes_price": 0.58,
                "no_price": 0.42,
                "question": "Will Luka Doncic score 28.5+ points vs Celtics?",
                "market_id": "pm-123",
            }
        }
    }
    rows = calculate_polymarket_ev(projections, odds, min_edge_pct=1.0)
    assert len(rows) == 1
    # DBB2 should be above market on this setup
    assert rows[0]["bet_side"] == "YES"
    assert rows[0]["edge_pct"] > 0


def test_demo_only_flags():
    settings = {
        "min_yes_price": 0.1,
        "max_yes_price": 0.9,
        "min_liquidity_usd": 500,
        "rate_limit_delay_seconds": 0,
    }
    raw_markets = [{"id": "pm-1", "question": "Will LeBron James score 25+ points vs Warriors?"}]

    def fake_prices(_settings, _market_id):
        return {"yes_price": 0.55, "no_price": 0.45, "volume_24h": 1000, "liquidity_usd": 1000}

    from src import polymarket_ingestion as pm_ing

    orig = pm_ing.fetch_market_prices
    pm_ing.fetch_market_prices = fake_prices
    try:
        normalized = normalize_polymarket_markets(settings, raw_markets)
    finally:
        pm_ing.fetch_market_prices = orig

    player = next(iter(normalized))
    prop = next(iter(normalized[player]))
    assert normalized[player][prop]["demo_only"] is True


def test_legal_disclaimer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    output_path = write_demo_bets(
        "2026-02-20",
        [{"player": "Test", "demo_only": True}],
        "DEMONSTRATION ONLY - US PERSONS CANNOT LEGALLY TRADE ON POLYMARKET",
    )
    import json
    from pathlib import Path

    payload = json.loads(Path(output_path).read_text())
    assert "DEMONSTRATION ONLY" in payload["legal_notice"]
    assert payload["demo_bets"][0]["demo_only"] is True
