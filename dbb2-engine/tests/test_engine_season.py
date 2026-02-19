from datetime import date

from engine.season import format_nba_season, get_current_nba_season_start_year


def test_get_current_nba_season_start_year_january():
    assert get_current_nba_season_start_year(date(2026, 1, 15)) == 2025


def test_get_current_nba_season_start_year_november():
    assert get_current_nba_season_start_year(date(2026, 11, 1)) == 2026


def test_format_nba_season():
    assert format_nba_season(2025) == "2025-26"
