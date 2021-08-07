import re
from bs4 import BeautifulSoup


def get_game_id_list(game_view_soup: BeautifulSoup) -> list:
    game_id_list = [el[7:] for el in list(set(re.findall("idgame=.{8}", str(game_view_soup))))]
    return game_id_list


class GameIdError(Exception):
    pass


class SeasonError(Exception):
    pass
