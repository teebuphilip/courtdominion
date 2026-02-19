from engine.live_data import (
    calculate_injury_modifier,
    compute_remaining_games_fields,
    normalize_name,
)


def test_normalize_name():
    assert normalize_name("LeBron James Jr.") == "lebron james"


def test_season_ending_modifier():
    injuries_by_id = {
        "1": {"status": "Out", "injury_type": "ACL", "details": "out for season"}
    }
    val = calculate_injury_modifier("1", "Player", injuries_by_id, {})
    assert val == 0.0


def test_compute_remaining_games_fields():
    live_ctx = {
        "team_games_played": {"LAL": 50},
        "injury_by_id": {},
        "injury_by_name": {},
    }
    fields = compute_remaining_games_fields(
        player_id="1",
        player_name="Player",
        team="LAL",
        projected_games=70,
        tpm_per_game=2.0,
        live_ctx=live_ctx,
    )
    assert fields["team_games_remaining"] == 32
    assert fields["games_remaining_projected"] >= 0
    assert fields["three_pointers_made_projected"] >= 0
