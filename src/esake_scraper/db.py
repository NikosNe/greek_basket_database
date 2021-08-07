"""Contains all functions that prepare the data tables"""
import os

import pandas as pd
from esake_scraper.shared.common_paths import DATA_DIR


# TODO: Rename "player_name" column to "player"


def get_games_table() -> pd.DataFrame:
    """
    Read the files from many games and concatenate them to a single dataframe
    """
    games_list = []
    for filename in os.listdir(DATA_DIR / "raw_games_data"):
        games_table = pd.read_csv(DATA_DIR / "raw_games_data" / filename, index_col=0)
        games_list.append(games_table)
    games_table = pd.concat(games_list)
    games_table["player_name"] = games_table["player_name"].apply(lambda x: _capitalize_name(x))
    return games_table


def get_players_table(games_table: pd.DataFrame) -> pd.DataFrame:
    """
    Read a dataframe from many games and get a dataframe with the unique player names

    Arguments:
        games_table: A dataframe with data from many games

    Returns:
        pd.DataFrame
    """
    player_name_series = games_table["player_name"].unique()
    player_name_series = pd.Series(player_name_series)
    # In case a player name includes digits, it should be removed
    invalid_element_mask = player_name_series.str.contains(r"[0-9]")
    player_name_series = player_name_series[~invalid_element_mask]
    players_data = pd.DataFrame(data=player_name_series)
    players_data = players_data.reset_index()
    players_data.columns = ["id", "player_name"]
    return players_data


def _capitalize_name(player_name: str) -> str:
    """
    Read a player's name and capitalize it. This is because in some cases
    the last name is all capital and in others isn't and we'd rather have
    homogeneity.

    Arguments:
        player_name: The player's name

    Returns:
        The player's name capitalized
    """
    # Remove accents and replace final sigmas with normal ones
    player_name = player_name.translate(
        str.maketrans(
            {
                "ά": "α",
                "Ά": "α",
                "έ": "ε",
                "Έ": "ε",
                "ί": "ι",
                "Ί": "ι",
                "ή": "η",
                "Ή": "η",
                "ύ": "υ",
                "Ύ": "υ",
                "ό": "ο",
                "Ό": "o",
                "ώ": "ω",
                "Ώ": "ω",
                "ς": "σ",
            }
        )
    )

    player_name = player_name.upper()
    return player_name


def get_teams_table(games_table: pd.DataFrame) -> pd.DataFrame:
    """
    Read a dataframe from many games and get a dataframe with the unique team names

    Arguments:
        games_table: A dataframe with data from many games

    Returns:
        pd.DataFrame
    """
    team_name_series = games_table["team"].unique()
    teams_table = pd.DataFrame(data=team_name_series)
    teams_table = teams_table.reset_index()
    teams_table.columns = ["id", "team"]
    return teams_table


def _get_averages(games_table: pd.DataFrame, grouping_column: str) -> pd.DataFrame:
    """
    Read a dataframe with data from many games and calculate the average statistics we need.

    Arguments:
        games_table: A dataframe with data from many games

    Returns:
        pd.DataFrame
    """
    stats_table = (
        games_table[
            [
                grouping_column,
                "points",
                "free_throws_attempted",
                "two_point_attempted",
                "three_point_attempted",
                "blocks",
                "fouls_committed",
                "offensive_rebounds",
                "defensive_rebounds",
                "fouls_received",
                "turnovers",
                "assists",
                "duration",
            ]
        ]
        .groupby(grouping_column)
        .mean()
        .reset_index()
    )
    stats_table["avg_points_from_two_point"] = stats_table["two_point_attempted"] * 2
    stats_table["avg_points_from_three_point"] = stats_table["three_point_attempted"] * 3
    stats_table["avg_rebounds"] = stats_table["offensive_rebounds"] + stats_table["defensive_rebounds"]
    stats_table["avg_duration"] = stats_table["duration"] / 60
    return stats_table


def _get_percentages(games_table: pd.DataFrame, stats_table: pd.DataFrame,
                     grouping_column: str) -> pd.DataFrame:
    """
    Read a dataframe with data from many games and a dataframe with statistics and
    calculate the relevant percentages

    Arguments:
        games_table: A dataframe with data from many games
        stats_table: A dataframe with player statistics

    Returns:
        pd.DataFrame
    """
    stats_table[
        [
            "total_free_throws_achieved",
            "total_free_throws_attempted",
            "total_two_point_achieved",
            "total_two_point_attempted",
            "total_three_point_achieved",
            "total_three_point_attempted",
        ]
    ] = (
        games_table[
            [
                grouping_column,
                "free_throws_achieved",
                "free_throws_attempted",
                "two_point_achieved",
                "two_point_attempted",
                "three_point_achieved",
                "three_point_attempted",
            ]
        ]
        .groupby(grouping_column)
        .sum()
        .reset_index()
        .drop(grouping_column, axis=1)
    )

    stats_table["free_throws_pct"] = (
            stats_table["total_free_throws_achieved"] / stats_table["total_free_throws_attempted"]
    )
    stats_table["two_point_pct"] = (
            stats_table["total_two_point_achieved"] / stats_table["total_two_point_attempted"]
    )
    stats_table["three_point_pct"] = (
            stats_table["total_three_point_achieved"] / stats_table["total_three_point_attempted"]
    )
    return stats_table


def get_stats_table(games_table: pd.DataFrame, grouping_column: str) -> pd.DataFrame:
    """
    Read a dataframe with data from many games and calculate the various useful statistics to be displayed

    Arguments:
        games_table:      A dataframe with data from many games
        grouping_column:  The column we want to group by. Either "player_name" if
                          we are interested in player stats or "team" if we are
                          interested in team stats

    Returns:
        pd.DataFrame
    """
    stats_table = _get_averages(games_table, grouping_column)
    stats_table = _get_percentages(games_table, stats_table, grouping_column)
    stats_table = stats_table.rename(
        columns={
            "points": "avg_points",
            "blocks": "avg_blocks",
            "fouls_committed": "avg_fouls_committed",
            "fouls_received": "avg_fouls_received",
            "turnovers": "avg_turnovers",
            "assists": "avg_assists",
            "total_free_throws_achieved": "avg_points_from_free_throws",
        }
    )

    stats_table = stats_table[
        [
            grouping_column,
            "avg_points",
            "avg_points_from_two_point",
            "avg_points_from_three_point",
            "avg_points_from_free_throws",
            "free_throws_pct",
            "two_point_pct",
            "three_point_pct",
            "avg_blocks",
            "avg_rebounds",
            "avg_fouls_committed",
            "avg_fouls_received",
            "avg_turnovers",
            "avg_assists",
            "avg_duration",
        ]
    ]

    # There can be players that haven't attempted any type of shot,
    # in which case we would have NaN percentages. These we replace with "-"
    stats_table = stats_table.fillna("-")
    return stats_table


if __name__ == "__main__":
    games_table = get_games_table()
    players_table = get_players_table(games_table)
    teams_table = get_teams_table(games_table)
    player_stats_table = get_stats_table(games_table, "player_name")
    team_stats_table = get_stats_table(games_table, "team")
    games_table.to_csv(DATA_DIR / "data_tables" / "games_table.csv")
    players_table.to_csv(DATA_DIR / "data_tables" / "players_table.csv")
    teams_table.to_csv(DATA_DIR / "data_tables" / "teams_table.csv")
    player_stats_table.to_csv(DATA_DIR / "data_tables" / "player_stats_table.csv")
    team_stats_table.to_csv(DATA_DIR / "data_tables" / "team_stats_table.csv")
