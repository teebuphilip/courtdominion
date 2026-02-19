from src.exchange_ev_calculator import calculate_ev, evaluate_player_prop


def _settings() -> dict:
    return {
        "ev_thresholds": {
            "take_edge_pct": 4.0,
            "make_edge_pct": 2.0,
            "min_confidence": 0.60,
            "min_available_size": 25,
            "max_bets_per_day": 10,
        }
    }


def test_edge_calculation():
    raw_edge, edge_pct, direction = calculate_ev(projection=27.8, line=26.5, std_dev=4.1)
    assert round(raw_edge, 2) == 1.3
    assert round(edge_pct, 2) == round((1.3 / 4.1) * 100, 2)
    assert direction == "OVER"


def test_take_vs_make_logic():
    settings = _settings()

    make_result = evaluate_player_prop(
        player_name="LeBron James",
        prop_type="points",
        projection_prop={"projection": 26.6, "std_dev": 4.1, "confidence": 0.71},
        odds_prop={
            "line": 26.5,
            "over": {"odds": -115, "available_size": 120},
            "under": {"odds": -105, "available_size": 75},
            "exchange": "novig",
        },
        settings=settings,
    )
    assert make_result is not None
    assert make_result["execution_type"] == "MAKE"

    take_result = evaluate_player_prop(
        player_name="LeBron James",
        prop_type="points",
        projection_prop={"projection": 27.8, "std_dev": 4.1, "confidence": 0.71},
        odds_prop={
            "line": 26.5,
            "over": {"odds": -115, "available_size": 120},
            "under": {"odds": -105, "available_size": 75},
            "exchange": "novig",
        },
        settings=settings,
    )
    assert take_result is not None
    assert take_result["execution_type"] == "TAKE"


def test_min_size_filter():
    settings = _settings()
    result = evaluate_player_prop(
        player_name="LeBron James",
        prop_type="points",
        projection_prop={"projection": 27.8, "std_dev": 4.1, "confidence": 0.71},
        odds_prop={
            "line": 26.5,
            "over": {"odds": -115, "available_size": 10},
            "under": {"odds": -105, "available_size": 75},
            "exchange": "novig",
        },
        settings=settings,
    )
    assert result is None
