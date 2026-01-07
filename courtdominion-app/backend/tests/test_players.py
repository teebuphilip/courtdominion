"""
Tests for players endpoint
"""

import pytest


def test_get_players_empty(client):
    """Test getting players when no data exists"""
    response = client.get("/players")

    assert response.status_code == 200
    assert response.json() == []


def test_get_players_with_data(client, sample_players):
    """Test getting players when data exists"""
    response = client.get("/players")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "Nikola Jokic"
    assert data[1]["name"] == "Anthony Davis"


def test_get_player_by_id(client, sample_players):
    """Test getting a specific player by ID"""
    response = client.get("/player/203999")

    assert response.status_code == 200
    data = response.json()

    assert data["player_id"] == "203999"
    assert data["name"] == "Nikola Jokic"
    assert data["team"] == "DEN"
    assert data["position"] == "C"


def test_get_player_not_found(client, sample_players):
    """Test getting a player that doesn't exist"""
    response = client.get("/player/999999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_players_endpoint_structure(client, sample_players):
    """Test that players have expected fields"""
    response = client.get("/players")
    data = response.json()

    player = data[0]
    assert "player_id" in player
    assert "name" in player
    assert "team" in player
    assert "position" in player
    assert "age" in player
