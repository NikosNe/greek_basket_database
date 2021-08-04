
import os

import pandas as pd
from esake_scraper.shared.common_paths import DATA_DIR


def get_games_data() -> pd.DataFrame:
    games_list = []
    for filename in os.listdir(DATA_DIR):
        games_data = pd.read_csv(DATA_DIR / filename, index_col=0)
        games_list.append(games_data)
    games_data = pd.concat(games_list)
    games_data["player_name"] = games_data["player_name"].apply(lambda x: _capitalize_name(x))
    return games_data


def get_players_table(games_data: pd.DataFrame) -> pd.DataFrame:
    player_name_series = games_data["player_name"].unique()[:-1]
    players_data = pd.DataFrame(data=player_name_series)
    players_data = players_data.reset_index()
    players_data.columns = ["id", "player_name"]
    return players_data


def _capitalize_name(player_name: str) -> str:
    # Remove accents
    player_name = player_name.replace("ά", "α").replace("έ", "ε").replace("ί", "ι").replace("ή", "η").replace("ύ", "υ").replace("ό", "ο").replace("ώ", "ω")

    # Replace final sigmas
    player_name = player_name.replace("ς", "σ")
    player_name = player_name.upper()
    return player_name


def get_teams_table(games_data: pd.DataFrame) -> pd.DataFrame:
    team_name_series = games_data["team"].unique()
    teams_data = pd.DataFrame(data=team_name_series)
    teams_data = teams_data.reset_index()
    teams_data.columns = ["id", "team"]
    return teams_data


def get_stats_table(games_data: pd.DataFrame) -> pd.DataFrame:

    games_data["two_point_pct"] = games_data["two_point_achieved"] / games_data["two_point_attempted"]
    games_data["three_point_pct"] = games_data["three_point_achieved"] / games_data["three_point_attempted"]
    stats_data = games_data[["player_name", "points", "free_throws_attempted", "two_point_attempted",
                             "three_point_attempted", "blocks", "fouls_committed", "offensive_rebounds",
                             "defensive_rebounds", "fouls_received", "turnovers", "assists",
                             "duration"]].groupby("player_name").mean().reset_index()
    stats_data["avg_points_from_two_point"] = stats_data["two_point_attempted"] * 2
    stats_data["avg_points_from_three_point"] = stats_data["three_point_attempted"] * 3
    stats_data["avg_rebounds"] = stats_data["offensive_rebounds"] + stats_data["defensive_rebounds"]
    stats_data["avg_duration"] = stats_data["duration"] / 60
    stats_data[["total_free_throws_achieved", "total_free_throws_attempted",
                "total_two_point_achieved", "total_two_point_attempted",
                "total_three_point_achieved", "total_three_point_attempted"]] = \
        games_data[["player_name", "free_throws_achieved", "free_throws_attempted",
                    "two_point_achieved", "two_point_attempted",
                    "three_point_achieved", "three_point_attempted"]].groupby("player_name").sum().reset_index().drop("player_name", axis=1)

    stats_data["free_throws_pct"] = stats_data["total_free_throws_achieved"] / stats_data["total_free_throws_attempted"]
    stats_data["two_point_pct"] = stats_data["total_two_point_achieved"] / stats_data["total_two_point_attempted"]
    stats_data["three_point_pct"] = stats_data["total_three_point_achieved"] / stats_data["total_three_point_attempted"]
    stats_data = stats_data.rename(columns={"points": "avg_points", "blocks": "avg_blocks",
                               "fouls_committed": "avg_fouls_committed",
                               "fouls_received": "avg_fouls_received",
                               "turnovers": "avg_turnovers", "assists": "avg_assists",
                               "total_free_throws_achieved": "avg_points_from_free_throws"
                               })

    stats_data = stats_data[["player_name", "avg_points", "avg_points_from_two_point",
                             "avg_points_from_three_point", "avg_points_from_free_throws",
                             "free_throws_pct", "two_point_pct", "three_point_pct",
                             "avg_blocks", "avg_rebounds", "avg_fouls_committed",
                             "avg_fouls_received", "avg_turnovers", "avg_assists",
                             "avg_duration"]]
    return stats_data
