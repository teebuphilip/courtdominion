"""
Tests for projections endpoint
"""

import pytest


def test_get_projections_empty(client):
    """Test getting projections when no data exists"""
    response = client.get("/projections")

    assert response.status_code == 200
    assert response.json() == []


def test_get_projections_with_data(client, sample_projections):
    """Test getting projections when data exists"""
    response = client.get("/projections")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0]["player_id"] == "203999"
    assert data[1]["player_id"] == "203076"


def test_projections_structure(client, sample_projections):
    """Test that projections have expected statistical fields"""
    response = client.get("/projections")
    data = response.json()

    projection = data[0]

    # Core stats
    assert "player_id" in projection
    assert "fantasy_points" in projection
    assert "points_per_game" in projection
    assert "rebounds_per_game" in projection
    assert "assists_per_game" in projection
    assert "steals_per_game" in projection
    assert "blocks_per_game" in projection
    assert "turnovers_per_game" in projection

    # Shooting stats
    assert "three_pointers_per_game" in projection
    assert "field_goal_pct" in projection
    assert "free_throw_pct" in projection

    # Other
    assert "minutes_per_game" in projection


def test_projections_data_types(client, sample_projections):
    """Test that projection values are correct types"""
    response = client.get("/projections")
    data = response.json()

    projection = data[0]

    assert isinstance(projection["fantasy_points"], (int, float))
    assert isinstance(projection["points_per_game"], (int, float))
    assert isinstance(projection["field_goal_pct"], (int, float))
    assert projection["field_goal_pct"] <= 1.0  # Percentage should be 0-1
