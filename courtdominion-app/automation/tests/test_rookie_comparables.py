"""
Tests for rookie comparables functionality
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dbb2_projections import find_player_id_by_name, get_rookie_comparable


def test_find_player_by_name():
    """Test finding player ID by name"""
    mock_cache = {
        '203076': {
            'player_name': 'Anthony Davis',
            'points_per_game': 24.7
        },
        '203999': {
            'player_name': 'Nikola Jokic',
            'points_per_game': 27.0
        }
    }

    # Test exact match
    player_id = find_player_id_by_name('Anthony Davis', mock_cache)
    assert player_id == '203076'

    # Test case insensitive
    player_id = find_player_id_by_name('anthony davis', mock_cache)
    assert player_id == '203076'

    # Test not found
    player_id = find_player_id_by_name('Unknown Player', mock_cache)
    assert player_id is None


def test_find_player_empty_cache():
    """Test finding player in empty cache"""
    player_id = find_player_id_by_name('Test Player', {})
    assert player_id is None


def test_get_rookie_comparable(tmp_path):
    """Test getting rookie comparable from CSV"""
    # Create temp CSV file
    csv_file = tmp_path / "rookie_comparables.csv"
    csv_file.write_text(
        "rookie_name,comparable_player,similarity_score\n"
        "Cooper Flagg,Anthony Davis,0.84\n"
    )

    mock_cache = {
        '203076': {
            'player_name': 'Anthony Davis',
            'points_per_game': 24.7
        }
    }

    # Temporarily override the CSV path
    import dbb2_projections
    original_path = dbb2_projections.ROOKIE_COMPARABLES_FILE
    dbb2_projections.ROOKIE_COMPARABLES_FILE = csv_file

    try:
        # Test getting comparable
        comparable_id = get_rookie_comparable('Cooper Flagg', mock_cache)
        assert comparable_id == '203076'

        # Test case insensitive
        comparable_id = get_rookie_comparable('cooper flagg', mock_cache)
        assert comparable_id == '203076'

        # Test not found
        comparable_id = get_rookie_comparable('Unknown Rookie', mock_cache)
        assert comparable_id is None

    finally:
        # Restore original path
        dbb2_projections.ROOKIE_COMPARABLES_FILE = original_path


def test_get_rookie_comparable_missing_csv():
    """Test getting rookie comparable when CSV doesn't exist"""
    mock_cache = {
        '203076': {
            'player_name': 'Anthony Davis',
        }
    }

    # Use a path that doesn't exist
    import dbb2_projections
    original_path = dbb2_projections.ROOKIE_COMPARABLES_FILE
    dbb2_projections.ROOKIE_COMPARABLES_FILE = Path('/nonexistent/path.csv')

    try:
        comparable_id = get_rookie_comparable('Cooper Flagg', mock_cache)
        assert comparable_id is None
    finally:
        dbb2_projections.ROOKIE_COMPARABLES_FILE = original_path


def test_rookie_comparables_csv_format():
    """Test that actual rookie_comparables.csv has correct format"""
    csv_path = Path(__file__).parent.parent / "rookie_comparables.csv"

    if csv_path.exists():
        import csv

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            # Check headers
            assert 'rookie_name' in headers
            assert 'comparable_player' in headers
            assert 'similarity_score' in headers

            # Check at least one row exists
            rows = list(reader)
            assert len(rows) > 0

            # Check similarity score is valid
            for row in rows:
                score = float(row['similarity_score'])
                assert 0.0 <= score <= 1.0
