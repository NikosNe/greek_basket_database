import re
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver

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
        series: An two character string signifying the series, e.g. 01, 02,
                03, etc.

    Returns:
        str
    """
    url = f"http://www.esake.gr/el/action/EsakeResults?idchampionship=0000000D&idteam=&idseason=0000000{season}&series={series}"
    return url


def get_soup(url: str, headers: dict,
             is_game_id: bool) -> BeautifulSoup:
    """

    Arguments:
        url:
        headers:
        driver:
    Returns:

    """
    if is_game_id:
        driver = webdriver.PhantomJS()
        driver.get(game_id_url)
        time.sleep(5)
        html = driver.page_source
    else:
        request = requests.get(url, headers=headers, verify=False)
        html = request.content
    soup = BeautifulSoup(html, "html.parser")
    return soup


def get_game_id_list(soup: BeautifulSoup) -> list:
    """

    Arguments:
        soup:

    Returns:

    """
    games_id_list = [el[7:] for el in list(set(re.findall("idgame=.{8}", str(soup))))]
    return games_id_list


def get_game_id_url(game_id: str) -> str:
    """

    Arguments:
        game_id:

    Returns:

    """
    game_id_url = f"http://www.esake.gr/el/action/EsakegameView?idgame={game_id}&mode=2"
    return game_id_url


def get_game_view(soup: BeautifulSoup) -> str:
    """

    Arguments:
        soup:

    Returns:

    """

    game_view_soup = soup.findAll(text=True)
    game_view_list = [game_view.strip().replace("\n", "") for game_view in game_view_soup]
    # Remove empty strings from the list
    game_view_list = [game_view for game_view in game_view_list if game_view]
    game_view_text = ' '.join(list(game_view_list))
    return game_view_text


def get_teams(game_view_text: str) -> list:
    """

    Arguments:
        game_view_text:

    Returns:

    """
    teams_list = re.findall("(\w*|\w*\s\w*) SHOTS", game_view_text)
    teams_list = [team.strip() for team in teams_list]
    return teams_list


def get_players(game_view_text: str) -> list:
    # TODO: This function needs more cleaning up
    # The tricky part here is that some players also have a middle name and
    # therefore can't be matched by \w+\s\w+
    all_players_list = re.findall(r"[\w\s]+ ", game_view_text)

    # The players of the first team start after the first string with the substring RANK
    rank_elements = [el for el in all_players_list if "RANK" in el]
    # Get the index of the first string including RANK
    first_rank_element_index = all_players_list.index(rank_elements[0])
    # Get the index of the second string including RANK
    second_rank_element_index = all_players_list.index(rank_elements[0], first_rank_element_index + 1)

    indices = [(first_rank_element_index + 1, second_rank_element_index),
               (second_rank_element_index + 1, len(all_players_list))]

    # Get a list of 2 lists, each of which includes the players of one team
    # The following returns the players' names including spaces in the string,
    # mixed with their stats
    players = [all_players_list[idx_start: idx_end] for idx_start, idx_end
               in indices]

    # For the last_player_index, one could argue that we could use 12,
    # but this wouldn't necessarily apply to seasons like 2020-2021, where
    # some teams might have occasionally had fewer players due to injuries
    # and financial issues
    players[0] = [player for player in players[0] if not re.match("(\s\d+\s|\d+\s)", player)]
    last_player_index = players[0].index(" ΠΑΙΚΤΗΣ ")
    players[0] = players[0][:last_player_index]
    players[0] = [player.strip() for player in players[0]]

    players[1] = [player for player in players[1] if not re.match("(\s\d+\s|\d+\s)", player)]
    last_player_index = [i for i, el in enumerate(players[1]) if "GLOBAL" in el][0]
    players[1] = players[1][:last_player_index]
    players[1] = [player.strip() for player in players[1]]
    players_list = [players[0], players[1]]
    return players_list


def get_stats_per_player(player: str, game_view_text: str):
    pass


if __name__ == "__main__":
    series_url = get_series_url(1, "01")
    general_overview_soup = get_soup(series_url, HEADERS, False)
    game_id_list = get_game_id_list(general_overview_soup)

    game_id_url = get_game_id_url(game_id_list[0])
    game_id_soup = get_soup(game_id_url, HEADERS, True)

    game_view_text = get_game_view(game_id_soup)
    teams_list = get_teams(game_view_text)
    players_list = get_players(game_view_text)

players_stats = [[], []]
# With this loop we can get the stats of all but the last player of team 0
for players_tup in zip(players_list[0][:-1], players_list[0][1:]):
    player_stats = re.findall(f"{players_tup[0]} [0-9][0-9]:[0-9][0-9]:[0-9][0-9].* {players_tup[1]}", game_view_text)
    player_stats = player_stats[0].replace(players_tup[1], "").replace("#", "")
    player_stats = player_stats.strip()
    players_stats[0].append(player_stats)

last_player_stats = re.findall(f"{players_list[0][-1]}.*{teams_list[1]}", game_view_text)
last_player_stats = re.findall(f"{players_list[0][-1]}.*ΣΥΝΟΛΟ", last_player_stats[0])
last_player_stats = last_player_stats[0].replace("ΣΥΝΟΛΟ", "")
last_player_stats = last_player_stats.strip()
players_stats[0].append(last_player_stats)

# Same process for team 1
for players_tup in zip(players_list[1][:-1], players_list[1][1:]):
    player_stats = re.findall(f"{players_tup[0]} [0-9][0-9]:[0-9][0-9]:[0-9][0-9].* {players_tup[1]}", game_view_text)
    player_stats = player_stats[0].replace(players_tup[1], "").replace("#", "")
    player_stats = player_stats.strip()
    players_stats[1].append(player_stats)

last_player_stats = re.findall(f"{players_list[1][-1]} [0-9][0-9]:[0-9][0-9]:[0-9][0-9].*ΣΥΝΟΛΟ", game_view_text)
last_player_stats = last_player_stats[0].replace("ΣΥΝΟΛΟ", "")
last_player_stats = last_player_stats.strip()
players_stats[1].append(last_player_stats)
