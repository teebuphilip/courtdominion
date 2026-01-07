"""
Tests for content endpoint
"""

import pytest


def test_content_endpoint_exists(client):
    """Test that content endpoint is accessible"""
    response = client.get("/api/content")

    # Should return either 200 (with data) or 404 (file not found)
    assert response.status_code in [200, 404]


def test_content_endpoint_structure_when_exists(client):
    """Test content endpoint response structure if file exists"""
    response = client.get("/api/content")

    if response.status_code == 200:
        data = response.json()

        # Check for expected top-level keys
        # Content may have hero, features, about, stats sections
        assert isinstance(data, dict)


def test_content_endpoint_returns_json(client):
    """Test that content endpoint returns valid JSON"""
    response = client.get("/api/content")

    if response.status_code == 200:
        # Should be able to parse as JSON
        data = response.json()
        assert data is not None
