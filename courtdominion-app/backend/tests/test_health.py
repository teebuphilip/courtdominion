"""
Tests for health endpoint
"""

import pytest


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_health_endpoint_returns_timestamp(client):
    """Test that health endpoint returns a valid timestamp"""
    response = client.get("/health")
    data = response.json()

    # Timestamp should be ISO format string
    assert isinstance(data["timestamp"], str)
    assert "T" in data["timestamp"]  # ISO format contains T
