"""
Tests for retry_failed_players functionality
"""

import pytest
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from retry_failed_players import find_failed_players, update_cache


def test_find_failed_players_confidence_zero():
    """Test finding players with confidence = 0.0"""
    cache_data = {
        'players': {
            '12345': {
                'player_name': 'Failed Player',
                'confidence': 0.0,
                'points_per_game': 20.0
            },
            '67890': {
                'player_name': 'Good Player',
                'confidence': 0.95,
                'points_per_game': 15.0
            }
        }
    }

    failed = find_failed_players(cache_data)
    assert '12345' in failed
    assert '67890' not in failed
    assert len(failed) == 1


def test_find_failed_players_missing_stats():
    """Test finding players with missing stats (negative values)"""
    cache_data = {
        'players': {
            '12345': {
                'player_name': 'Failed Player',
                'confidence': 1.0,
                'points_per_game': -1  # Missing stat indicator
            },
            '67890': {
                'player_name': 'Good Player',
                'confidence': 0.95,
                'points_per_game': 15.0
            }
        }
    }

    failed = find_failed_players(cache_data)
    assert '12345' in failed
    assert '67890' not in failed


def test_find_failed_players_multiple_failures():
    """Test finding multiple failed players"""
    cache_data = {
        'players': {
            '1': {'confidence': 0.0, 'points_per_game': 10},
            '2': {'confidence': 0.95, 'points_per_game': 15},
            '3': {'confidence': 0.0, 'points_per_game': 12},
            '4': {'confidence': 1.0, 'points_per_game': -1},
        }
    }

    failed = find_failed_players(cache_data)
    assert len(failed) == 3  # Players 1, 3, 4
    assert '1' in failed
    assert '3' in failed
    assert '4' in failed
    assert '2' not in failed


def test_find_failed_players_empty_cache():
    """Test finding failed players in empty cache"""
    cache_data = {'players': {}}

    failed = find_failed_players(cache_data)
    assert len(failed) == 0


def test_update_cache():
    """Test updating cache with new player stats"""
    cache_data = {
        'players': {
            '12345': {
                'player_name': 'Failed Player',
                'confidence': 0.0,
                'points_per_game': -1
            }
        },
        'cached_at': '2026-01-01'
    }

    new_stats = {
        'player_name': 'Failed Player',
        'confidence': 0.95,
        'points_per_game': 20.5
    }

    update_cache(cache_data, '12345', new_stats)

    # Check player was updated
    assert cache_data['players']['12345']['confidence'] == 0.95
    assert cache_data['players']['12345']['points_per_game'] == 20.5

    # Check last_retry timestamp was added
    assert 'last_retry' in cache_data


def test_update_cache_preserves_other_players():
    """Test that updating one player doesn't affect others"""
    cache_data = {
        'players': {
            '12345': {'confidence': 0.0},
            '67890': {'confidence': 0.95}
        }
    }

    new_stats = {'confidence': 0.98}

    update_cache(cache_data, '12345', new_stats)

    # Original player should be unchanged
    assert cache_data['players']['67890']['confidence'] == 0.95
