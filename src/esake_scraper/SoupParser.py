
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from esake_scraper.shared.common_paths import SRC_DIR
from esake_scraper.shared.logging import logging
import esake_scraper.utils as utils


logger = logging.getLogger("Parsing using BeautifulSoup")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/46.0.2490.80 Safari/537.36",
    "Content-Type": "text/html",
}

SEASON_MAP = {"regular": 1, "play_offs": 2}


class SoupParser:
    """
    Parse the data of either a single game -if is_game_id is True- or a series (otherwise)
    into a BeautifulSoup object.
    """
    def __init__(self, season: str, series: int, is_game_id: bool,
                 game_id: Optional[str] = None):
        """
        Arguments:
            season:     Either "regular" or "play_offs"
            series:     A single-digit integer signifying which series data we are scraping
            is_game_id: True if this is a game_id, False if it is an overview
            game_id:    A game id
        """

        if is_game_id and game_id is None:
            raise utils.GameIdError("No game id provided")
        if season not in SEASON_MAP.keys():
            raise utils.SeasonError(f"Season must be one of {SEASON_MAP.keys()}")

        self.season = SEASON_MAP[season]
        self.series = series
        self.is_game_id = is_game_id
        self.game_id = game_id
        self.url_ = ""
        self.soup_ = BeautifulSoup
        self.get_url()
        self.get_soup()

    def get_url(self):
        """
        Get either a series or a game url, depending whether is_game_id is respectively False or True
        """
        if self.is_game_id:
            self.url_ = f"http://www.esake.gr/el/action/EsakegameView?idgame={self.game_id}&mode=2"
        else:
            self.url_ = f"http://www.esake.gr/el/action/EsakeResults?idchampionship=0000000D&idteam=&idseason=0000000{self.season}&series={self.series}"

    def get_soup(self):
        """
        Parse the html data from a url into a BeautifulSoup object.
        """
        if self.is_game_id:
            options = webdriver.ChromeOptions()
            options.add_argument('headless')
            driver = webdriver.Chrome(SRC_DIR / 'chromedriver', options=options)
            driver.get(self.url_)
            time.sleep(5)
            html = driver.page_source
            self.soup_ = BeautifulSoup(html, "html.parser")
            self.soup_ = self.soup_.findAll(text=True)
        else:
            request = requests.get(self.url_, headers=HEADERS, verify=False)
            html = request.content
            self.soup_ = BeautifulSoup(html, "html.parser")