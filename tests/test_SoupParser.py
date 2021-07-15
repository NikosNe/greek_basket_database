

from unittest import mock
import pytest
import esake_scraper.SoupParser as esp
import esake_scraper.utils as utils


@pytest.mark.parametrize("season", ["regular", "play_offs"])
def test_SoupParser_raises_game_id_error(season):
    with pytest.raises(utils.GameIdError):
        esp.SoupParser(season, "01", True)


def test_SoupParser_raises_season_error():
    with pytest.raises(utils.SeasonError):
        esp.SoupParser("wrong_season_name", "01", True, "wer")


@pytest.mark.parametrize("season, is_game_id, game_id", [("regular", True, "wer"),
                                                         ("regular", False, None),
                                                         ("play_offs", True, "wer"),
                                                         ("play_offs", False, None)])
def test_SoupParser(season, is_game_id, game_id):
    with mock.patch("selenium.webdriver.ChromeOptions") as mock_options:
        with mock.patch("selenium.webdriver.Chrome") as mock_chrome:
            with mock.patch("esake_scraper.SoupParser.BeautifulSoup") as mock_soup:
                esp.SoupParser(season, "01", is_game_id, game_id)
                if is_game_id:
                    mock_options.assert_called()
                    mock_chrome.assert_called()
                mock_soup.assert_called()
