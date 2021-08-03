
import os

import pandas as pd
from esake_scraper.shared.common_paths import DATA_DIR


def concat_raw_tables() -> pd.DataFrame:
    raw_list = []
    for filename in os.listdir(DATA_DIR):
        raw_data = pd.read_csv(DATA_DIR / filename, index_col=0)
        raw_list.append(raw_data)
    raw_data = pd.concat(raw_list)
    return raw_data


def get_players_table(raw_data: pd.DataFrame) -> pd.DataFrame:
    # TODO Remove elements that include numbers
    raw_data["player_name"].unique()


def get_teams_table():
    pass


def get_games_table() -> pd.DataFrame:
    pass
