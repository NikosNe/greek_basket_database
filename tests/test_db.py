import unittest.mock as mock

import pandas as pd

from esake_scraper import db
from pandas.testing import assert_frame_equal
from esake_scraper.shared.common_paths import TESTS_DATA_DIR

DUMMY_GAMES_DATA = pd.read_csv(TESTS_DATA_DIR / "dummy_games_data.csv", index_col=0)


def test_get_games_data():
    expected_data = DUMMY_GAMES_DATA
    with mock.patch("pandas.read_csv") as mock_pandas:
        mock_pandas.return_value = pd.DataFrame(
            data=[["ΑΕΚ", "ΜΠΕΤΣ Άντριου", 1393.0]], columns=["team", "player_name", "duration"]
        )
        returned_data = db.get_games_table()
        assert_frame_equal(returned_data.iloc[[0]], expected_data)


def test_get_players_table():
    dummy_games_data = pd.concat([DUMMY_GAMES_DATA] * 2)
    dummy_games_data["player_name"].iloc[1] = "00-09-87-09"
    returned_data = db.get_players_table(dummy_games_data)
    expected_data = pd.read_csv(TESTS_DATA_DIR / "dummy_players_table.csv", index_col=0)
    assert_frame_equal(returned_data, expected_data)


def test_get_teams_table():
    dummy_games_data = pd.concat([DUMMY_GAMES_DATA] * 2)
    dummy_games_data["team"].iloc[1] = "ΑΡΗΣ"
    returned_data = db.get_teams_table(dummy_games_data)
    returned_data.to_csv(TESTS_DATA_DIR / "dummy_teams_table.csv")
    expected_data = pd.read_csv(TESTS_DATA_DIR / "dummy_teams_table.csv", index_col=0)
    assert_frame_equal(returned_data, expected_data)


def test_get_stats_table():
    dummy_games_data = pd.read_csv(TESTS_DATA_DIR / "dummy_games_for_stats.csv", index_col=0)
    returned_player_data = db.get_stats_table(dummy_games_data, "player_name")
    expected_player_data = pd.read_csv(TESTS_DATA_DIR / "dummy_player_stats_table.csv", index_col=0)
    assert_frame_equal(returned_player_data, expected_player_data)

    dummy_games_data = pd.read_csv(TESTS_DATA_DIR / "dummy_games_for_stats.csv", index_col=0)
    dummy_games_data["team"].iloc[0] = "ΑΡΗΣ"
    returned_team_data = db.get_stats_table(dummy_games_data, "team")
    expected_team_data = pd.read_csv(TESTS_DATA_DIR / "dummy_team_stats_table.csv", index_col=0)
    # After filling NaN's with "-", comparing "0.75" as a string raised
    # an error. This is why we convert it back to float for the comparison
    assert float(returned_team_data["free_throws_pct"].iloc[1]) == float(expected_team_data["free_throws_pct"].iloc[1])
    assert_frame_equal(returned_team_data.drop("free_throws_pct", axis=1),
                       expected_team_data.drop("free_throws_pct", axis=1))
