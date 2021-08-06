
import unittest.mock as mock

import pandas as pd

from esake_scraper import db
from pandas.testing import assert_frame_equal
from esake_scraper.shared.common_paths import TESTS_DATA_DIR

DUMMY_GAMES_DATA = pd.read_csv(TESTS_DATA_DIR / "dummy_games_data.csv", index_col=0)


def test_get_games_data():
    expected_data = DUMMY_GAMES_DATA
    with mock.patch("pandas.read_csv") as mock_pandas:
        mock_pandas.return_value = pd.DataFrame(data=[["ΑΕΚ", "ΜΠΕΤΣ Άντριου", 1393.0]],
                                                columns=["team", "player_name", "duration"])
        returned_data = db.get_games_data()
        assert_frame_equal(returned_data.iloc[[0]], expected_data)


def test_get_players_table():
    dummy_games_data = pd.concat([DUMMY_GAMES_DATA]*2)
    returned_data = db.get_players_table(dummy_games_data)
    expected_data = pd.read_csv(TESTS_DATA_DIR / "dummy_players_table.csv", index_col=0)
    assert_frame_equal(returned_data, expected_data)
