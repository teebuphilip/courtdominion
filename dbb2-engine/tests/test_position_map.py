"""Tests for engine/position_map.py — raw CSV position to CD 5-position enum."""

import pytest

from engine.position_map import map_position_to_cd, RAW_TO_CD, CD_POSITIONS


class TestPositionMapping:
    """map_position_to_cd: every raw position maps to a valid CD position."""

    def test_all_raw_positions_map_to_valid_cd(self):
        for raw, cd in RAW_TO_CD.items():
            assert cd in CD_POSITIONS

    def test_guard_maps_to_pg(self):
        assert map_position_to_cd("G") == "PG"

    def test_forward_maps_to_sf(self):
        assert map_position_to_cd("F") == "SF"

    def test_center_stays_center(self):
        assert map_position_to_cd("C") == "C"

    def test_guard_forward_maps_to_sg(self):
        assert map_position_to_cd("G-F") == "SG"

    def test_forward_guard_maps_to_sg(self):
        assert map_position_to_cd("F-G") == "SG"

    def test_forward_center_maps_to_pf(self):
        assert map_position_to_cd("F-C") == "PF"

    def test_center_forward_maps_to_pf(self):
        assert map_position_to_cd("C-F") == "PF"

    def test_unknown_position_raises(self):
        with pytest.raises(ValueError):
            map_position_to_cd("XYZ")

    def test_all_seven_raw_positions_covered(self):
        expected = {"G", "F", "C", "G-F", "F-G", "F-C", "C-F"}
        assert set(RAW_TO_CD.keys()) == expected
