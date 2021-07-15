"""This script includes all functionality to read and parse players' data on
   a per game basis"""
import re

from bs4 import BeautifulSoup

import pandas as pd
from esake_scraper.shared.common_paths import DATA_DIR
from esake_scraper.shared.logging import logging
from esake_scraper.SoupParser import SoupParser
import esake_scraper.utils as utils


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/46.0.2490.80 Safari/537.36",
    "Content-Type": "text/html",
}

logger = logging.getLogger("ESAKE players logger")


class PlayersData:
    def __init__(self, game_id_soup: BeautifulSoup, to_csv: bool):
        self.game_id_soup = game_id_soup
        self.game_id_list_ = []
        self.game_view_text_ = ""
        self.teams_list_ = []
        self.players_list_ = []
        self.players_data_ = [[], []]
        self.players_data_df_ = pd.DataFrame()
        self.to_csv = to_csv
        self.get_game_view()
        self.get_teams()
        if self.teams_list_:
            self.get_players()
            self.get_data_per_player()
            self.get_players_data_df()
            if to_csv:
                logger.info("Saving to csv")
                self.save_to_csv()
        else:
            logger.warning("No data for provided game")

    def get_game_view(self):
        """
        Read a BeautifulSoup object and get a text with the corresponding game view, i.e.
        the html content including all the html content for a certain game
    
        Arguments:
            soup: A BeautifulSoup object with the html content of a specific game
    
        Returns:
            str
        """

        game_view_list = [game_view.strip().replace("\n", "") for game_view in self.game_id_soup]
    
        # Remove empty strings from the list
        game_view_list = [game_view for game_view in game_view_list if game_view]
        self.game_view_text_ = " ".join(list(game_view_list))
    
    def get_teams(self):
        """
        Read a string with the html content corresponding to a single game and
        return a list with the names of the two teams playing
    
        Arguments:
            game_view_text: A string with the html content of a game
    
        Returns:
            list
        """
        self.teams_list_ = re.findall("(\w*|\w*\s\w*) SHOTS", self.game_view_text_)
        self.teams_list_ = [team.strip().replace("0 ", "") for team in self.teams_list_]

    def get_players(self):
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
        all_players_list = re.findall(r"[\[\w\s]+ [\w\s\-]+", self.game_view_text_)
    
        # The players of the first team start after the first string with the substring RANK
        synolo_elements = [el for el in all_players_list if "ΣΥΝΟΛΟ" in el]
    
        # Get the index of the first string including RANK
        first_synolo_element_index = all_players_list.index(synolo_elements[0])
    
        # Get the index of the second string including RANK
        second_synolo_element_index = all_players_list.index(
            synolo_elements[1], first_synolo_element_index + 1
        )

        # For the last_player_index, one could argue that we could use 12,
        # but this wouldn't necessarily apply to seasons like 2020-2021, where
        # some teams might have occasionally had fewer players due to injuries
        # and financial issues

        indices = [
            (0, first_synolo_element_index),
            (first_synolo_element_index + 1, second_synolo_element_index),
        ]
    
        # Get a list of 2 lists, each of which includes the players of one team
        # The following returns the players' names including spaces in the string,
        # mixed with their stats
        self.players_list_ = [all_players_list[idx_start:idx_end] for idx_start, idx_end in indices]

        # Remove the "00" after each player's name
        for idx in range(len(self.players_list_)):
            self.players_list_[idx] = [
                player.replace("00", "").strip()
                for player in self.players_list_[idx]
                if " 00" in player and "RANK" not in player
            ]
            # Remove extraneous number data that are prepended to the names of the last
            # players of each team
            last_player_numbers = re.findall(r"[\d\s]+", self.players_list_[idx][-1])
            last_player_numbers = [number for number in last_player_numbers if number != " "]
            last_player_numbers = "-".join(last_player_numbers)
            self.players_list_[idx][-1] = self.players_list_[idx][-1].replace(last_player_numbers, "")

    def get_data_per_player(self):
        """
        Read a list of lists with the player names
        and create a list of lists with the team names followed by their data, i.e.
        how many shots of various types they attempted, how many were succesful,
        how many blocks, steals, turnovers, etc.
    
        Arguments:
            players_list: A list of two lists, each of which has the player names of
                          each team

        """
    
        for ls, stats_ls in zip(self.players_list_, self.players_data_):
            for players_tup in zip(ls[:-1], ls[1:]):
                player_data = re.findall(
                    f"{players_tup[0]} [0-9][0-9]:[0-9][0-9]:[0-9][0-9].* {players_tup[1]}",
                    self.game_view_text_,
                )
                # Between the string of players_tup[1] and the stats of players_tup[0]
                # there is occasionally a hash and occasionally a number, ergo the need
                # for using an or condition to remove these.
                player_data = re.sub(f"[#|[0-9]]* {players_tup[1]}", "", player_data[0])
                player_data = player_data.strip()
                stats_ls.append(player_data)
        self._get_last_players_data()

    def _get_last_players_data(self):
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
            f"{self.players_list_[0][-1]} [0-9][0-9]:[0-9][0-9]:[0-9][0-9].* {self.players_list_[1][0]}",
            self.game_view_text_,
        )
        last_player_data = re.findall(f"{self.players_list_[0][-1]}.*ΣΥΝΟΛΟ", last_player_data[0])
        self.players_data_[0].append(last_player_data[0])
        last_player_data = re.findall(
            f"{self.players_list_[1][-1]} [0-9][0-9]:[0-9][0-9]:[0-9][0-9].*ΣΥΝΟΛΟ", self.game_view_text_
        )
        self.players_data_[1].append(last_player_data[0])
        for idx, player_stats in enumerate([self.players_data_[0][-1], self.players_data_[1][-1]]):
            player_stats = player_stats.replace("ΣΥΝΟΛΟ", "")
            player_stats = player_stats.strip()
            self.players_data_[idx][-1] = player_stats

    @staticmethod
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

    def get_players_data_df(self):
        """
        Read a list of lists with the players' data, a list with the names of the two teams
        and a list of lists with the players' names and parse these into a dataframe.

        Returns:
            pd.DataFrame
        """
        team_stats_list = []
        for team, team_players_stats in zip(self.teams_list_, self.players_data_):
            team_stats_df = pd.DataFrame(team_players_stats, columns=["all_stats"])
            team_stats_df["team"] = team
            team_stats_list.append(team_stats_df)

        self.players_data_df_ = pd.concat(team_stats_list, ignore_index=True)
        self.players_data_df_["player_name"] = pd.Series([player for ls in self.players_list_ for player in ls])
        self.players_data_df_["duration"] = self.players_data_df_["all_stats"].apply(lambda x: self._get_duration(x))
        self.players_data_df_["points"] = self.players_data_df_["all_stats"].apply(lambda x: self._get_points(x))
        self.players_data_df_["all_shots"] = self.players_data_df_["all_stats"].apply(lambda x: self._get_all_shots(x))

        self.players_data_df_[["two_point", "three_point", "free_throws"]] = pd.DataFrame(
            self.players_data_df_["all_shots"].to_list()
        )

        for col_name, series in self.players_data_df_[["two_point", "three_point", "free_throws"]].iteritems():
            self.players_data_df_[[f"{col_name}_achieved", f"{col_name}_attempted"]] = self._split_into_achieved_and_attempted(
                self.players_data_df_[col_name])
        self.players_data_df_[
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
        ] = pd.DataFrame(self.players_data_df_["all_stats"].apply(lambda x: x[-15:].split(" ")).to_list())

        self.players_data_df_ = self.players_data_df_.drop(
            ["all_stats", "all_shots", "two_point", "three_point", "free_throws"], axis=1
        )

        self.players_data_df_[self.players_data_df_.columns.drop(["team", "player_name"])] = \
            self.players_data_df_[self.players_data_df_.columns.drop(["team", "player_name"])].astype(int)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    def save_to_csv(self):
        self.players_data_df_.to_csv(DATA_DIR / f"{self.teams_list_[0]}_{self.teams_list_[1]}.csv")


if __name__ == "__main__":
    SERIES = "01"
    SEASON = "regular"
    series_sp = SoupParser(SEASON, SERIES, False)
    series_soup = series_sp.soup_
    game_id_list = utils.get_game_id_list(series_soup)
    for game_id in game_id_list:
        game_sp = SoupParser(SEASON, SERIES, True, game_id)
        game_soup = game_sp.soup_
        pld = PlayersData(game_soup, True)
