"""
Pytest configuration and fixtures for backend tests
"""

import pytest
import os
import json
from pathlib import Path
from fastapi.testclient import TestClient

# Set test environment
os.environ["DATA_DIR"] = "/tmp/courtdominion_test_data"
os.environ["INTERNAL_API_KEY"] = "test_api_key_12345"

from main import app


@pytest.fixture(scope="session")
def test_data_dir():
    """Create and return test data directory"""
    data_dir = Path("/tmp/courtdominion_test_data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def client():
    """Create TestClient for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_players(test_data_dir):
    """Create sample players.json for testing"""
    players = [
        {
            "player_id": "203999",
            "name": "Nikola Jokic",
            "team": "DEN",
            "position": "C",
            "age": 28
        },
        {
            "player_id": "203076",
            "name": "Anthony Davis",
            "team": "LAL",
            "position": "PF-C",
            "age": 30
        }
    ]

    with open(test_data_dir / "players.json", "w") as f:
        json.dump(players, f)

    yield players

    # Cleanup
    if (test_data_dir / "players.json").exists():
        (test_data_dir / "players.json").unlink()


@pytest.fixture
def sample_projections(test_data_dir):
    """Create sample projections.json for testing"""
    projections = [
        {
            "player_id": "203999",
            "fantasy_points": 58.3,
            "points_per_game": 27.0,
            "rebounds_per_game": 13.2,
            "assists_per_game": 8.8,
            "steals_per_game": 1.3,
            "blocks_per_game": 0.9,
            "turnovers_per_game": 3.1,
            "three_pointers_per_game": 0.8,
            "field_goal_pct": 0.632,
            "free_throw_pct": 0.817,
            "minutes_per_game": 34.5,
            "games_played_history": [75, 73, 69],
            "total_games_missed": 37,
            "severe_injury_count": 0
        },
        {
            "player_id": "203076",
            "fantasy_points": 52.1,
            "points_per_game": 24.7,
            "rebounds_per_game": 11.1,
            "assists_per_game": 3.1,
            "steals_per_game": 1.2,
            "blocks_per_game": 2.3,
            "turnovers_per_game": 2.0,
            "three_pointers_per_game": 0.4,
            "field_goal_pct": 0.561,
            "free_throw_pct": 0.781,
            "minutes_per_game": 33.8,
            "games_played_history": [76, 40, 56],
            "total_games_missed": 90,
            "severe_injury_count": 2
        }
    ]

    with open(test_data_dir / "projections.json", "w") as f:
        json.dump(projections, f)

    yield projections

    # Cleanup
    if (test_data_dir / "projections.json").exists():
        (test_data_dir / "projections.json").unlink()


@pytest.fixture
def sample_content(test_data_dir):
    """Create sample content.json for testing"""
    # Content endpoint reads from backend/data/content.json, not DATA_DIR
    # So we need to handle this differently
    content = {
        "hero": {
            "title": "Test Title",
            "subtitle": "Test Subtitle",
            "cta": "Test CTA"
        },
        "features": [
            {
                "title": "Feature 1",
                "description": "Description 1"
            }
        ]
    }

    return content


@pytest.fixture
def cleanup_test_data(test_data_dir):
    """Cleanup all test data files after tests"""
    yield

    # Remove all JSON files in test data dir
    for json_file in test_data_dir.glob("*.json"):
        json_file.unlink()
