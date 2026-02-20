from src.risk_overlay import apply_enhanced_shadow


def _settings():
    return {
        "ev_thresholds": {
            "take_edge_pct": 4.0,
            "make_edge_pct": 2.0,
            "min_confidence": 0.60,
            "max_bets_per_day": 10,
        },
        "kelly": {
            "bankroll": 5000,
            "min_units": 0.5,
            "max_units": 3.0,
        },
        "risk_overlay": {
            "mode": "observe",
            "alpha_confidence": 0.35,
            "beta_units": 0.50,
            "high_risk_edge_multiplier": 0.80,
            "max_availability_risk": 0.85,
            "fallback_weights": {
                "injury_risk": 0.5,
                "minutes_risk": 0.3,
                "volatility": 0.2,
            },
        },
    }


def test_apply_enhanced_shadow_haircut_and_filter():
    baseline = [
        {
            "player_name": "LeBron James",
            "prop_type": "points",
            "direction": "OVER",
            "edge_pct": 6.0,
            "confidence": 0.75,
            "units": 2.0,
            "available_size": 100,
            "source": "novig",
        },
        {
            "player_name": "High Risk Guy",
            "prop_type": "points",
            "direction": "OVER",
            "edge_pct": 3.0,
            "confidence": 0.62,
            "units": 1.0,
            "available_size": 100,
            "source": "novig",
        },
    ]
    risk_map = {
        "lebron james": {"total_risk": 0.40, "risk_level": "Medium", "availability_risk": 0.30},
        "high risk guy": {"total_risk": 0.95, "risk_level": "High", "availability_risk": 0.95},
    }

    enhanced, summary = apply_enhanced_shadow(baseline, _settings(), risk_map)
    assert len(enhanced) == 1
    assert summary["baseline_count"] == 2
    assert summary["enhanced_count"] == 1
    assert summary["dropped_count"] == 1

    kept = enhanced[0]
    assert kept["player_name"] == "LeBron James"
    assert kept["units"] <= 2.0
    assert "enhanced_risk_penalty" in kept
