"""
Tests for internal API endpoint (CRITICAL - used by microservices)
"""

import pytest


def test_internal_api_without_key(client, sample_players, sample_projections):
    """Test internal API returns 422 when API key header is missing"""
    response = client.get("/api/internal/baseline-projections")

    assert response.status_code == 422
    assert "x-api-key" in response.json()["detail"][0]["loc"]


def test_internal_api_with_wrong_key(client, sample_players, sample_projections):
    """Test internal API returns 401 when API key is invalid"""
    response = client.get(
        "/api/internal/baseline-projections",
        headers={"X-API-Key": "wrong_key"}
    )

    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]


def test_internal_api_with_correct_key(client, sample_players, sample_projections):
    """Test internal API returns data with correct API key"""
    response = client.get(
        "/api/internal/baseline-projections",
        headers={"X-API-Key": "test_api_key_12345"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "players" in data
    assert "last_updated" in data
    assert "count" in data


def test_internal_api_response_structure(client, sample_players, sample_projections):
    """Test internal API response has correct structure for microservices"""
    response = client.get(
        "/api/internal/baseline-projections",
        headers={"X-API-Key": "test_api_key_12345"}
    )

    data = response.json()

    assert isinstance(data["players"], list)
    assert data["count"] == len(data["players"])
    assert isinstance(data["last_updated"], str)


def test_internal_api_player_data_structure(client, sample_players, sample_projections):
    """Test that player data in internal API has all required fields for microservices"""
    response = client.get(
        "/api/internal/baseline-projections",
        headers={"X-API-Key": "test_api_key_12345"}
    )

    data = response.json()

    if len(data["players"]) > 0:
        player = data["players"][0]

        # Basic info
        assert "player_id" in player
        assert "name" in player
        assert "team" in player
        assert "position" in player
        assert "age" in player

        # Projections
        assert "fantasy_points" in player
        assert "points" in player
        assert "rebounds" in player
        assert "assists" in player
        assert "steals" in player
        assert "blocks" in player
        assert "turnovers" in player
        assert "three_pointers" in player
        assert "fg_pct" in player
        assert "ft_pct" in player
        assert "minutes" in player

        # Historical data (for risk modeling)
        assert "games_played_3yr" in player
        assert "injury_history" in player
        assert "total_games_missed_3yr" in player["injury_history"]
        assert "severe_injuries" in player["injury_history"]


def test_internal_api_combines_player_and_projection_data(client, sample_players, sample_projections):
    """Test that internal API correctly combines players with their projections"""
    response = client.get(
        "/api/internal/baseline-projections",
        headers={"X-API-Key": "test_api_key_12345"}
    )

    data = response.json()
    assert len(data["players"]) == 2  # Should have 2 players

    # Find Nikola Jokic
    jokic = next((p for p in data["players"] if p["player_id"] == "203999"), None)
    assert jokic is not None
    assert jokic["name"] == "Nikola Jokic"
    assert jokic["fantasy_points"] == 58.3
    assert jokic["points"] == 27.0

def test_internal_api_case_insensitive_header(client, sample_players, sample_projections):
    """Test that API key header is case-insensitive"""
    # FastAPI converts headers to lowercase automatically
    response = client.get(
        "/api/internal/baseline-projections",
        headers={"x-api-key": "test_api_key_12345"}  # lowercase
    )

    assert response.status_code == 200
