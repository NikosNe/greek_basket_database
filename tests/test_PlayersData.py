from unittest import mock
import pickle

import bs4
import pandas as pd

from esake_scraper.PlayersData import PlayersData
from esake_scraper.shared.common_paths import TESTS_DATA_DIR
import pandas.api.types as ptypes

with open(TESTS_DATA_DIR / "dummy_soup.pickle", "rb") as f:
    DUMMY_GAME_ID_SOUP = pickle.load(f)


def test_players_data():
    pld = PlayersData("00F123", DUMMY_GAME_ID_SOUP, False)
    assert isinstance(pld.game_id_soup, bs4.element.ResultSet)
    assert isinstance(pld.game_view_text_, str)
    assert isinstance(pld.teams_list_, list)
    assert len(pld.teams_list_) == 2
    assert isinstance(pld.players_list_, list)
    assert len(pld.players_list_) == 2
    assert isinstance(pld.players_data_, list)
    assert len(pld.players_data_) == 2
    assert isinstance(pld.players_data_df_, pd.DataFrame)
    assert len(pld.players_data_df_) == len(pld.players_list_[0]) + len(pld.players_list_[1])
    assert all(
        pld.players_data_df_.columns
        == [
            "team",
            "player_name",
            "duration",
            "points",
            "two_point_achieved",
            "two_point_attempted",
            "three_point_achieved",
            "three_point_attempted",
            "free_throws_achieved",
            "free_throws_attempted",
            "turnovers",
            "steals",
            "fouls_committed",
            "fouls_received",
            "blocks",
            "assists",
            "offensive_rebounds",
            "defensive_rebounds",
            "game_id",
            "game_date"
        ]
    )
    all(ptypes.is_object_dtype(pld.players_data_df_[col]) for col in ["team", "player_name"])
    all(
        ptypes.is_numeric_dtype(pld.players_data_df_[col])
        for col in [
            "duration",
            "points",
            "two_point_achieved",
            "two_point_attempted",
            "three_point_achieved",
            "three_point_attempted",
            "free_throws_achieved",
            "free_throws_attempted",
            "turnovers",
            "steals",
            "fouls_committed",
            "fouls_received",
            "blocks",
            "assists",
            "offensive_rebounds",
            "defensive_rebounds",
        ]
    )
