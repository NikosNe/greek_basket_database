import re

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


URL = "http://www.esake.gr/el/action/EsakeResults?idchampionship=0000000D&idteam=&idseason=00000001&series=01"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/46.0.2490.80 Safari/537.36",
    "Content-Type": "text/html",
}

# Using this URL, we get a general overview of the games
request = requests.get(URL, headers=HEADERS, verify=False)
soup = BeautifulSoup(request.content, "html.parser")

# Get a list of the idgames and use them in http://www.esake.gr/el/action/EsakegameView?idgame=<idgame>&mode=2
# To get the players stats
games_id_list = [el[7:] for el in list(set(re.findall("idgame=.{8}", str(soup))))]

# 000F7010 is the first id that does have statistics. Check what are the differences between its soup
# with the soups of id's including statistics
url = "http://www.esake.gr/el/action/EsakegameView?idgame=000F7010&mode=2"
request = requests.get(URL, headers=HEADERS, verify=False)
id_soup = BeautifulSoup(request.content, "html.parser")
test = id_soup.find_all()

# We are using webdriver, otherwise we can't parse the html
import time
from selenium import webdriver
driver = webdriver.PhantomJS()
driver.get("http://www.esake.gr/el/action/EsakegameView?idgame=000F7010&mode=2")
time.sleep(5)# you can give it some time to load the js
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
test = soup.findAll(text=True)
test = [el.strip().replace("\n", "") for el in test]
test = [el for el in test if el]
test_text = ' '.join(list(test))

# Get a list with the teams playing. Test with a few other matches to
# see if it applies more generally
teams_playing = re.findall("(\w*|\w*\s\w*) SHOTS", test_text)
teams_playing = [team.strip() for team in teams_playing]

# Use the teams to get the players and their stats
players_of_team_0 = re.findall(f"{teams_playing[0]}.*SHOTS", test_text)

# The tricky part here is that some players also have a middle name and
# therefore can't be matched by \w+\s\w+
all_players_list = re.findall(r"[\w\s]+ ", test_text)

# The players of the first team start after the first element with RANK
rank_elements = [el for el in all_players_list if "RANK" in el]
first_rank_element_index = all_players_list.index(rank_elements[0])
second_rank_element_index = all_players_list.index(rank_elements[0], first_rank_element_index + 1)

# The following returns the players' names including spaces in the string, mixed with their stats
players_team_0 = \
    all_players_list[first_rank_element_index + 1: second_rank_element_index]
players_team_1 = \
    all_players_list[second_rank_element_index + 1:]

# For the last_player_index, one could argue that we could use 12,
# but this wouldn't necessarily apply to seasons like 2020-2021, where
# some teams might have occasionally had fewer players due to injuries
# and financial issues
players_team_0 = [player for player in players_team_0 if not re.match("(\s\d+\s|\d+\s)", player)]
last_player_index = players_team_0.index(" ΠΑΙΚΤΗΣ ")
players_team_0 = players_team_0[:last_player_index]
players_team_0 = [player.strip() for player in players_team_0]

players_team_1 = [player for player in players_team_1 if not re.match("(\s\d+\s|\d+\s)", player)]
last_player_index = [i for i, el in enumerate(players_team_1) if "GLOBAL" in el][0]
players_team_1 = players_team_1[:last_player_index]
players_team_1 = [player.strip() for player in players_team_1]