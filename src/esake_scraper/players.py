"""This script includes all functionality to read and parse players' data on
   a per game basis"""
import re
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
from esake_scraper.shared.common_paths import DATA_DIR

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/46.0.2490.80 Safari/537.36",
    "Content-Type": "text/html",
}


def get_series_url(season: int, series: str) -> str:
    """
    Read a season and a series and return the respective URL
    Arguments:
        season: 1 if it's the regular season, 2 if it's the play-offs
        series: A two character string signifying the series, e.g. 01, 02,
                03, etc.

    Returns:
        str
    """
    url = f"http://www.esake.gr/el/action/EsakeResults?idchampionship=0000000D&idteam=&idseason=0000000{season}&series={series}"
    return url


def get_soup(url: str, headers: dict, is_game_id: bool) -> BeautifulSoup:
    """
    Read a URL and headers and parse the html data into a soup object.

    Arguments:
        url:        A string with the URL, whose content we want to parse
        headers:    The headers we use to access the URL content
        is_game_id: True if this is a game_id, False if it is an overview
    Returns:
        BeautifulSoup
    """
    if is_game_id:
        driver = webdriver.PhantomJS()
        driver.get(url)
        time.sleep(5)
        html = driver.page_source
    else:
        request = requests.get(url, headers=headers, verify=False)
        html = request.content
    soup = BeautifulSoup(html, "html.parser")
    return soup


def get_game_id_list(soup: BeautifulSoup) -> list:
    """
    Read a BeautifulSoup object and get a list with all the game id's

    Arguments:
        soup: A BeautifulSoup object

    Returns:
        list
    """
    games_id_list = [el[7:] for el in list(set(re.findall("idgame=.{8}", str(soup))))]
    return games_id_list


def get_game_url(game_id: str) -> str:
    """
    Read a game id and get the respective URL for the corresponding game

    Arguments:
        game_id: A game id

    Returns:
        str
    """
    game_url = f"http://www.esake.gr/el/action/EsakegameView?idgame={game_id}&mode=2"
    return game_url


def get_game_view(soup: BeautifulSoup) -> str:
    """
    Read a BeautifulSoup object and get a text with the corresponding game view, i.e.
    the html content including all the html content for a certain game

    Arguments:
        soup: A BeautifulSoup object with the html content of a specific game

    Returns:
        str
    """

    game_view_soup = soup.findAll(text=True)
    game_view_list = [game_view.strip().replace("\n", "") for game_view in game_view_soup]

    # Remove empty strings from the list
    game_view_list = [game_view for game_view in game_view_list if game_view]
    game_view_text = " ".join(list(game_view_list))
    return game_view_text


def get_teams(game_view_text: str) -> list:
    """
    Read a string with the html content corresponding to a single game and
    return a list with the names of the two teams playing

    Arguments:
        game_view_text: A string with the html content of a game

    Returns:
        list
    """
    teams_list = re.findall("(\w*|\w*\s\w*) SHOTS", game_view_text)
    teams_list = [team.strip() for team in teams_list]
    return teams_list


def get_players(game_view_text: str) -> list:
    """
    Read a string with the html content of a game and return a list of two lists,
    each of which contains the player names of each team.

    Arguments:
        game_view_text: A string with the html content of a game

    Returns:
        list
    """
    # The tricky part here is that some players also have a middle name and
    # therefore can't be matched by \w+\s\w+
    all_players_list = re.findall(r"[[\w\s]+ [\w\s\-]+", game_view_text)

    # The players of the first team start after the first string with the substring RANK
    synolo_elements = [el for el in all_players_list if "ΣΥΝΟΛΟ" in el]

    # Get the index of the first string including RANK
    first_synolo_element_index = all_players_list.index(synolo_elements[0])

    # Get the index of the second string including RANK
    second_synolo_element_index = all_players_list.index(
        synolo_elements[1], first_synolo_element_index + 1
    )

    indices = [
        (0, first_synolo_element_index),
        (first_synolo_element_index + 1, second_synolo_element_index),
    ]

    # Get a list of 2 lists, each of which includes the players of one team
    # The following returns the players' names including spaces in the string,
    # mixed with their stats
    players = [all_players_list[idx_start:idx_end] for idx_start, idx_end in indices]

    # For the last_player_index, one could argue that we could use 12,
    # but this wouldn't necessarily apply to seasons like 2020-2021, where
    # some teams might have occasionally had fewer players due to injuries
    # and financial issues
    players[0] = [
        player.replace("00", "").strip()
        for player in players[0]
        if " 00" in player and "RANK" not in player
    ]
    players[1] = [
        player.replace("00", "").strip()
        for player in players[1]
        if " 00" in player and "RANK" not in player
    ]
    last_player_numbers = re.findall(r"[\d\s]+", players[0][-1])
    last_player_numbers = [number for number in last_player_numbers if number != " "]
    last_player_numbers = "-".join(last_player_numbers)
    players[0][-1] = players[0][-1].replace(last_player_numbers, "")

    last_player_numbers = re.findall(r"[\d\s]+", players[1][-1])
    last_player_numbers = [number for number in last_player_numbers if number != " "]
    last_player_numbers = "-".join(last_player_numbers)
    players[1][-1] = players[1][-1].replace(last_player_numbers, "")

    return players


def get_data_per_player(players_list: list) -> list:
    """
    Read a list of lists with the player names
    and create a list of lists with the team names followed by their data, i.e.
    how many shots of various types they attempted, how many were succesful,
    how many blocks, steals, turnovers, etc.

    Arguments:
        players_list: A list of two lists, each of which has the player names of
                      each team

    Returns:
        list
    """
    players_data = [[], []]

    for ls, stats_ls in zip(players_list, players_data):
        for players_tup in zip(ls[:-1], ls[1:]):
            player_data = re.findall(
                f"{players_tup[0]} [0-9][0-9]:[0-9][0-9]:[0-9][0-9].* {players_tup[1]}",
                game_view_text,
            )
            # Between the string of players_tup[1] and the stats of players_tup[0]
            # there is occasionally a hash and occasionally a number, ergo the need
            # for using an or condition to remove these.
            player_data = re.sub(f"[#|[0-9]]* {players_tup[1]}", "", player_data[0])
            player_data = player_data.strip()
            stats_ls.append(player_data)
    players_data = _get_last_players_data(players_list, players_data)

    return players_data


def _get_last_players_data(players_list: list, players_data: list) -> list:
    """
    Read a list of lists with the player names and another list of lists with the player
    names and their data and get the data of the player of each team that is mentioned
    last
    Arguments:
        players_list: A list of two lists with the names of each team's players
        players_data: A list of two lists with the names and data of each team's
                      players

    Returns:
        list
    """
    # Handle the last player for each team
    last_player_data = re.findall(
        f"{players_list[0][-1]} [0-9][0-9]:[0-9][0-9]:[0-9][0-9].* {players_list[1][0]}",
        game_view_text,
    )
    last_player_data = re.findall(f"{players_list[0][-1]}.*ΣΥΝΟΛΟ", last_player_data[0])
    players_data[0].append(last_player_data[0])
    last_player_data = re.findall(
        f"{players_list[1][-1]} [0-9][0-9]:[0-9][0-9]:[0-9][0-9].*ΣΥΝΟΛΟ", game_view_text
    )
    players_data[1].append(last_player_data[0])
    for idx, player_stats in enumerate([players_data[0][-1], players_data[1][-1]]):
        player_stats = player_stats.replace("ΣΥΝΟΛΟ", "")
        player_stats = player_stats.strip()
        players_data[idx][-1] = player_stats
    return players_data


def _split_into_achieved_and_attempted(shots_series: pd.Series) -> pd.DataFrame:
    """
    Read a series with shot data, in the format <achieved> - <attempted> and return
    a dataframe with two columns, one with the achieved shots and the other with the
    attempted ones.

    Arguments:
        shots_series: A data series with shot data

    Returns:
        pd.DataFrame
    """
    achieved_and_attempted_data = pd.DataFrame(
        shots_series.apply(lambda x: x.split("-")).to_list()
    )
    achieved_and_attempted_data = achieved_and_attempted_data.apply(lambda x: x.str.strip())
    return achieved_and_attempted_data


def get_players_data_df(players_data: list, teams_list: list, players_list: list) -> pd.DataFrame:
    """
    Read a list of lists with the players' data, a list with the names of the two teams
    and a list of lists with the players' names and parse these into a dataframe.

    Arguments:
        players_data: A list of two lists with the names and data of each team's
                      players
        teams_list:   A list with the names of the two teams playing
        players_list: A list of two lists with the names of each team's players
    Returns:
        pd.DataFrame
    """
    team_stats_list = []
    for team, team_players_stats in zip(teams_list, players_data):
        team_stats_df = pd.DataFrame(team_players_stats, columns=["all_stats"])
        team_stats_df["team"] = team
        team_stats_list.append(team_stats_df)

    players_stats_df = pd.concat(team_stats_list, ignore_index=True)
    players_stats_df["player_name"] = pd.Series([player for ls in players_list for player in ls])
    players_stats_df["duration"] = players_stats_df["all_stats"].apply(lambda x: _get_duration(x))
    players_stats_df["points"] = players_stats_df["all_stats"].apply(lambda x: _get_points(x))
    players_stats_df["all_shots"] = players_stats_df["all_stats"].apply(lambda x: _get_all_shots(x))

    players_stats_df[["two_point", "three_point", "free_throws"]] = pd.DataFrame(
        players_stats_df["all_shots"].to_list()
    )

    for col_name, series in players_stats_df[["two_point", "three_point", "free_throws"]].iteritems():
        players_stats_df[[f"{col_name}_achieved", f"{col_name}_attempted"]] = _split_into_achieved_and_attempted(
            players_stats_df[col_name])
    players_stats_df[
        [
            "turnovers",
            "steals",
            "fouls_committed",
            "fouls_received",
            "blocks",
            "assists",
            "offensive_rebounds",
            "defensive_rebounds",
        ]
    ] = pd.DataFrame(players_stats_df["all_stats"].apply(lambda x: x[-15:].split(" ")).to_list())

    players_stats_df = players_stats_df.drop(
        ["all_stats", "all_shots", "two_point", "three_point", "free_throws"], axis=1
    )

    players_stats_df[players_stats_df.columns.drop(["team", "player_name"])] = \
        players_stats_df[players_stats_df.columns.drop(["team", "player_name"])].astype(int)
    return players_stats_df


def _get_duration(player_data: str) -> int:
    """
    Read a player's data and calculate its duration in seconds
    Arguments:
        player_data: A string with the data of a player

    Returns:
        int
    """
    # Get the duration of play
    duration = re.findall(r"[0-9][0-9]:[0-9][0-9]:[0-9][0-9]", player_data)[0]
    duration = duration.split(":")
    # Convert to seconds
    duration = int(duration[0]) * 3600 + int(duration[1]) * 60 + int(duration[2])
    return duration


def _get_points(player_data: str) -> int:
    """
    Read a player's data and get its points
    Arguments:
        player_data: A string with the data of a player

    Returns:
        int
    """
    points = int(re.findall(r":[0-9][0-9] [0-9]+", player_data)[0].split(" ")[1])
    return points


def _get_all_shots(player_data: str) -> list:
    """
    Read a player's data and return a list with all his shots (both attempted and
    achieved) in the <achieved> - <attempted> format
    Arguments:
        player_data: A string with the data of a player

    Returns:
        list
    """
    all_shots = re.findall(r"[0-9]+ - [0-9]+", player_data)
    return all_shots


if __name__ == "__main__":
    series_url = get_series_url(1, "01")
    general_overview_soup = get_soup(series_url, HEADERS, False)
    game_id_list = get_game_id_list(general_overview_soup)

    games_dict = {}
    for game_id in game_id_list:
        game_url = get_game_url(game_id)
        game_id_soup = get_soup(game_url, HEADERS, True)

        game_view_text = get_game_view(game_id_soup)
        teams_list = get_teams(game_view_text)

        if teams_list:
            players_list = get_players(game_view_text)
            players_data = get_data_per_player(players_list)
            players_data_df = get_players_data_df(players_data, teams_list, players_list)
            games_dict[teams_list[0] + "_" + teams_list[1]] = players_data_df
    for game, data in games_dict.items():
        data.to_csv(DATA_DIR / f"{game}.csv")