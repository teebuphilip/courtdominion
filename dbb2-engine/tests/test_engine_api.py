"""
Tests for engine/api.py — FastAPI projection endpoint for the betting engine.

Unit tests for std_dev derivation, confidence calculation, and response shape.
Integration test hits the real pipeline via TestClient.
"""

import math

import pytest
from fastapi.testclient import TestClient

from engine.api import (
    app,
    _get_std_dev,
    _get_confidence,
    _build_player_response,
    STAT_MAP,
    VARIANCE_KEY_MAP,
)
from engine.baseline import PlayerContext
from engine.projections import SeasonProjection
from engine.pricing import AuctionValue


def _make_context(**overrides):
    """Build a test PlayerContext."""
    defaults = dict(
        player_id="TEST001",
        player_name="Test Player",
        team="TST",
        position="G",
        raw_position="G-F",
        age=27,
        role="Starter",
        age_bracket="Prime",
        stat_variance={
            "points_variance": 25.0,       # std_dev = 5.0
            "rebounds_variance": 4.0,       # std_dev = 2.0
            "assists_variance": 9.0,        # std_dev = 3.0
            "three_pm_variance": 1.0,       # std_dev = 1.0
            "steals_variance": 0.49,        # std_dev = 0.7
            "blocks_variance": 0.25,        # std_dev = 0.5
        },
    )
    defaults.update(overrides)
    return PlayerContext(**defaults)


def _make_projection(**overrides):
    """Build a test SeasonProjection."""
    defaults = dict(
        player_id="TEST001",
        player_name="Test Player",
        team="TST",
        position="G",
        minutes=32.0,
        usage_rate=25.0,
        points=20.0,
        rebounds=6.0,
        assists=5.0,
        steals=1.5,
        blocks=1.0,
        turnovers=2.5,
        fgm=7.5,
        fga=16.0,
        three_pm=2.0,
        three_pa=5.5,
        ftm=3.0,
        fta=3.5,
        fg_pct=0.469,
        three_pt_pct=0.364,
        ft_pct=0.857,
        fantasy_points=35.0,
        projected_games=72,
        ceiling=52.0,
        floor=20.0,
        consistency=70,
    )
    defaults.update(overrides)
    return SeasonProjection(**defaults)


class TestStdDev:
    """Standard deviation derivation from stat_variance."""

    def test_known_variance(self):
        """sqrt(25.0) = 5.0 for points."""
        ctx = _make_context()
        assert _get_std_dev(ctx, "points") == pytest.approx(5.0)

    def test_all_six_stats(self):
        """All 6 betting props should return positive std_dev."""
        ctx = _make_context()
        for stat in STAT_MAP:
            sd = _get_std_dev(ctx, stat)
            assert sd > 0, f"{stat} std_dev should be > 0"

    def test_missing_variance_returns_zero(self):
        ctx = _make_context(stat_variance={})
        assert _get_std_dev(ctx, "points") == 0.0

    def test_unknown_stat_returns_zero(self):
        ctx = _make_context()
        assert _get_std_dev(ctx, "nonexistent") == 0.0

    def test_negative_variance_safe(self):
        """Negative variance (shouldn't happen) returns 0, not crash."""
        ctx = _make_context(stat_variance={"points_variance": -1.0})
        assert _get_std_dev(ctx, "points") == 0.0


class TestConfidence:
    """Per-stat confidence derivation."""

    def test_high_consistency_low_cv(self):
        """High consistency + low CV -> high confidence."""
        conf = _get_confidence(projection_value=20.0, std_dev=2.0, base_confidence=0.80)
        # CV = 2/20 = 0.10, conf = 0.80 * (1 - 0.10) = 0.72
        assert conf == pytest.approx(0.72, abs=0.01)

    def test_low_consistency_high_cv(self):
        """Low consistency + high CV -> clamped to 0.40."""
        conf = _get_confidence(projection_value=1.0, std_dev=2.0, base_confidence=0.40)
        # CV = 2.0, capped at 0.5, conf = 0.40 * (1 - 0.5) = 0.20 -> clamped to 0.40
        assert conf == 0.40

    def test_zero_projection(self):
        """Zero projection falls back to 80% of base, clamped."""
        conf = _get_confidence(projection_value=0.0, std_dev=1.0, base_confidence=0.70)
        assert conf == pytest.approx(0.56, abs=0.01)

    def test_zero_std_dev(self):
        """Zero std_dev falls back to 80% of base, clamped."""
        conf = _get_confidence(projection_value=20.0, std_dev=0.0, base_confidence=0.70)
        assert conf == pytest.approx(0.56, abs=0.01)

    def test_clamp_max_095(self):
        """Confidence should never exceed 0.95."""
        conf = _get_confidence(projection_value=30.0, std_dev=0.1, base_confidence=0.99)
        assert conf <= 0.95

    def test_clamp_min_040(self):
        """Confidence should never go below 0.40."""
        conf = _get_confidence(projection_value=0.5, std_dev=5.0, base_confidence=0.30)
        assert conf >= 0.40


class TestPlayerResponse:
    """Response shape for the betting engine contract."""

    def test_required_fields(self):
        ctx = _make_context()
        proj = _make_projection()
        resp = _build_player_response(ctx, proj)

        assert resp["id"] == "TEST001"
        assert resp["name"] == "Test Player"
        assert resp["team"] == "TST"
        assert resp["position"] == "G-F"  # raw_position
        assert resp["is_b2b"] is False

    def test_all_six_stat_triples(self):
        """Each prop stat should have value, _std, and _conf."""
        ctx = _make_context()
        proj = _make_projection()
        resp = _build_player_response(ctx, proj)

        for short_name in STAT_MAP.values():
            assert short_name in resp, f"Missing {short_name}"
            assert f"{short_name}_std" in resp, f"Missing {short_name}_std"
            assert f"{short_name}_conf" in resp, f"Missing {short_name}_conf"

    def test_stat_values_match_projection(self):
        ctx = _make_context()
        proj = _make_projection(points=22.5, rebounds=8.0)
        resp = _build_player_response(ctx, proj)

        assert resp["pts"] == 22.5
        assert resp["reb"] == 8.0

    def test_std_dev_values_positive(self):
        ctx = _make_context()
        proj = _make_projection()
        resp = _build_player_response(ctx, proj)

        for short_name in STAT_MAP.values():
            assert resp[f"{short_name}_std"] >= 0

    def test_confidence_in_range(self):
        ctx = _make_context()
        proj = _make_projection()
        resp = _build_player_response(ctx, proj)

        for short_name in STAT_MAP.values():
            conf = resp[f"{short_name}_conf"]
            assert 0.40 <= conf <= 0.95, f"{short_name}_conf={conf}"

    def test_b2b_flag_propagated(self):
        ctx = _make_context(is_b2b=True)
        proj = _make_projection()
        resp = _build_player_response(ctx, proj)
        assert resp["is_b2b"] is True

    def test_field_count(self):
        """Should have 5 base fields + 6 stats * 3 = 23 total fields."""
        ctx = _make_context()
        proj = _make_projection()
        resp = _build_player_response(ctx, proj)
        assert len(resp) == 23


class TestStatMapping:
    """Verify the STAT_MAP and VARIANCE_KEY_MAP are consistent."""

    def test_all_stat_map_keys_in_variance_map(self):
        for stat in STAT_MAP:
            assert stat in VARIANCE_KEY_MAP, f"{stat} missing from VARIANCE_KEY_MAP"

    def test_six_stats(self):
        assert len(STAT_MAP) == 6
        assert len(VARIANCE_KEY_MAP) == 6


def _mock_pipeline():
    ctx1 = _make_context(player_id="P1", player_name="Alpha Guard", team="AAA", raw_position="G", age=26)
    ctx2 = _make_context(player_id="P2", player_name="Beta Big", team="BBB", raw_position="C", age=30)
    proj1 = _make_projection(
        player_id="P1",
        player_name="Alpha Guard",
        team="AAA",
        position="G",
        points=24.0,
        rebounds=5.0,
        assists=7.0,
        steals=1.8,
        blocks=0.4,
        turnovers=3.0,
        consistency=78,
    )
    proj2 = _make_projection(
        player_id="P2",
        player_name="Beta Big",
        team="BBB",
        position="C",
        points=18.0,
        rebounds=11.0,
        assists=3.0,
        steals=0.8,
        blocks=1.7,
        turnovers=2.1,
        consistency=68,
    )
    av1 = AuctionValue(player_id="P1", player_name="Alpha Guard", position="G", dollar_value=34)
    av2 = AuctionValue(player_id="P2", player_name="Beta Big", position="C", dollar_value=28)
    return [ctx1, ctx2], [proj1, proj2], [av1, av2]


class TestApiEndpoints:
    def test_projections_today(self, monkeypatch):
        monkeypatch.setattr("engine.api._load_pipeline", _mock_pipeline)
        client = TestClient(app)
        res = client.get("/projections/today")
        assert res.status_code == 200
        body = res.json()
        assert "players" in body
        assert len(body["players"]) == 2

    def test_internal_baseline_requires_configured_key(self, monkeypatch):
        monkeypatch.setattr("engine.api._load_pipeline", _mock_pipeline)
        monkeypatch.delenv("INTERNAL_API_KEY", raising=False)
        client = TestClient(app)
        res = client.get("/api/internal/baseline-projections", headers={"x-api-key": "x"})
        assert res.status_code == 503

    def test_internal_baseline_rejects_invalid_key(self, monkeypatch):
        monkeypatch.setattr("engine.api._load_pipeline", _mock_pipeline)
        monkeypatch.setenv("INTERNAL_API_KEY", "secret")
        client = TestClient(app)
        res = client.get("/api/internal/baseline-projections", headers={"x-api-key": "wrong"})
        assert res.status_code == 401

    def test_internal_baseline_success(self, monkeypatch):
        monkeypatch.setattr("engine.api._load_pipeline", _mock_pipeline)
        monkeypatch.setenv("INTERNAL_API_KEY", "secret")
        client = TestClient(app)
        res = client.get("/api/internal/baseline-projections", headers={"x-api-key": "secret"})
        assert res.status_code == 200
        body = res.json()
        assert body["count"] == 2
        assert body["players"][0]["player_id"] in {"P1", "P2"}
        assert "fantasy_points" in body["players"][0]

    def test_lineup_optimize(self, monkeypatch):
        monkeypatch.setattr("engine.api._load_pipeline", _mock_pipeline)
        client = TestClient(app)
        res = client.post("/tools/lineup/optimize", json={"player_ids": ["P1", "P2"], "roster_size": 8})
        assert res.status_code == 200
        body = res.json()
        assert "lineup" in body
        assert len(body["lineup"]) == 2
        assert body["projected_total_fantasy_points"] > 0

    def test_streaming_candidates(self, monkeypatch):
        monkeypatch.setattr("engine.api._load_pipeline", _mock_pipeline)
        client = TestClient(app)
        res = client.get("/tools/streaming-candidates?limit=1")
        assert res.status_code == 200
        body = res.json()
        assert body["count"] == 1
        assert len(body["candidates"]) == 1
        assert "stream_score" in body["candidates"][0]

    def test_trade_analyze(self, monkeypatch):
        monkeypatch.setattr("engine.api._load_pipeline", _mock_pipeline)
        client = TestClient(app)
        res = client.post(
            "/tools/trade/analyze",
            json={
                "give_player_ids": ["P2"],
                "receive_player_ids": ["P1"],
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert "summary" in body
        assert body["summary"]["delta_fantasy_points"] != 0
        assert body["summary"]["verdict"] in {"accept", "decline"}
