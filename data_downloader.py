from urllib.parse import urljoin
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import teams
import player
import random
import time

class PlaywrightController:
    def __init__(self, dtb_data):
        self.dtb_data = dtb_data
        self.playwright = None
        self.browser = None
        self.page = None
        self.scraped_items = []

    def playwright_starter(self):
        if self.playwright is None:
            self.playwright = sync_playwright().start()
        if self.browser is None:
            self.browser = self.playwright.chromium.launch(headless=True)
        if self.page is None:
            self.page = self.browser.new_page()

    def get_page_content(self, full_url):
        time.sleep(random.uniform(1.0, 3.0))
        self.page.goto(full_url)
        html = self.page.content()
        return html

    def playwright_termination(self):
        self.browser.close()
        self.playwright.stop()

    def soup_maker(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        return soup

    def get_url(self, url_content, chosen_league):
        for dtb_item in self.dtb_data:
            if dtb_item["league_id"] == chosen_league or chosen_league == 0:
                full_url = urljoin("https://www.eliteprospects.com/", dtb_item["elite_url"])
                returned_html_content = self.get_page_content(full_url)
                returned_soup = self.soup_maker(returned_html_content)

                if url_content == "league":
                    self.team_soup_parse(dtb_item["league_id"], returned_soup)
                elif url_content == "team_roster":
                    self.team_roster_parse(returned_soup, dtb_item["league_id"], dtb_item["team_id"])
        return self.scraped_items

    def team_soup_parse(self, league_id, soup):
        """Metoda najde všechny týmy dané ligy na stránce. Získá jméno týmu a odkaz na profil týmu."""
        list_of_scraped_teams = soup.find_all("a", class_ = "TextLink_link__RhSiC LabelWithIcon_link__67DL_ TableBody_link__dfR3c TableBody_plainText__KuMY7")
        for team in list_of_scraped_teams:
            team_name = team.text
            team_url = team.get("href")
            new_team = teams.Teams(league_id, team_name, team_url)
            print(league_id, team_name, team_url)
            self.scraped_items.append(new_team)

    def team_roster_parse(self, soup, league_id, team_id):
        """Metoda najde všechny hráče týmu na stránce. Získá jejich jméno a odkaz na profil hráče."""
        roster_player_divs = soup.find_all("div", class_ = "Roster_player__e6EbP")
        for roster_player_div in roster_player_divs:
            roster_player_a = roster_player_div.find("a")
            roster_player_url = roster_player_a.get("href")
            full_url = urljoin("https://www.eliteprospects.com/", roster_player_url)
            returned_player = self.player_profile_parse(full_url, league_id, team_id)
            self.scraped_items.append(returned_player)

    def player_name_splitter(self, player_fullname):
        word_list = player_fullname.split()
        player_first_name = word_list[0]
        player_last_name = " ".join(word_list[1:]) or None
        return player_first_name, player_last_name

    def player_profile_parse(self, full_url, league_id, team_id):
        html_content = self.get_page_content(full_url)
        returned_soup = self.soup_maker(html_content)
        player_h1 = returned_soup.find("h1", class_ = "Profile_headerMain__WPgYE")
        print(player_h1)
        player_nation = player_h1.find("img").get("title")
        player_fullname = player_h1.text
        adjusted_player_name = self.player_name_splitter(player_fullname)
        player_surname = adjusted_player_name[0]
        player_lastname = adjusted_player_name[1]

        player_card_ul = returned_soup.find("ul", class_ = "PlayerFacts_factsList__Xw_ID")
        list_of_player_facts = player_card_ul.find_all("li")
        player_position = list_of_player_facts[5].text
        sliced_player_position = player_position[len("Position"):]
        player_date_of_birth = list_of_player_facts[0].text
        sliced_player_date_of_birth = player_date_of_birth[len("Date of Birth"):]

        new_player = player.Player(player_surname, player_lastname, player_nation, league_id, player_position, sliced_player_date_of_birth, team_id, full_url)
        print(player_surname, player_lastname, player_nation, league_id, sliced_player_position, sliced_player_date_of_birth, team_id, full_url)
        return new_player



# class WebScraper:
#     def __init__(self, dtb_data):
#         self.dtb_data = dtb_data
#         self.scraped_items = []
#
#     def get_url(self, url_content, chosen_league):
#         for dtb_item in self.dtb_data:
#             if dtb_item["league_id"] == chosen_league or chosen_league == 0:
#                 full_url = urljoin("https://www.eliteprospects.com/", dtb_item["elite_url"])
#                 returned_soup = self.download_url_content(full_url)
#
#                 if url_content == "league":
#                     self.team_soup_parse(dtb_item["league_id"], returned_soup)
#                 elif url_content == "team_roster":
#                     self.team_roster_parse(returned_soup, dtb_item["league_id"], dtb_item["team_id"])
#         return self.scraped_items
#
#     def download_url_content(self, full_url):
#         response = requests.get(full_url)
#         web = response.text
#         soup = BeautifulSoup(web, "html.parser")
#         time.sleep(random.uniform(1.0, 3.0)) #zkouška proti ochraně před webscrapingem
#         return soup
#
#     def team_soup_parse(self, league_id, soup):
#         """Metoda najde všechny týmy dané ligy na stránce. Získá jméno týmu a odkaz na profil týmu."""
#         list_of_scraped_teams = soup.find_all("a", class_ = "TextLink_link__RhSiC LabelWithIcon_link__67DL_ TableBody_link__dfR3c TableBody_plainText__KuMY7")
#         for team in list_of_scraped_teams:
#             team_name = team.text
#             team_url = team.get("href")
#             new_team = teams.Teams(league_id, team_name, team_url)
#             print(league_id, team_name, team_url)
#             self.scraped_items.append(new_team)
#
#     def team_roster_parse(self, soup, league_id, team_id):
#         """Metoda najde všechny hráče týmu na stránce. Získá jejich jméno a odkaz na profil hráče."""
#         roster_player_divs = soup.find_all("div", class_ = "Roster_player__e6EbP")
#         for roster_player_div in roster_player_divs:
#             roster_player_a = roster_player_div.find("a")
#             roster_player_url = roster_player_a.get("href")
#             full_url = urljoin("https://www.eliteprospects.com/", roster_player_url)
#             returned_player = self.player_profile_parse(full_url, league_id, team_id)
#             self.scraped_items.append(returned_player)
#
#     def player_name_splitter(self, player_fullname):
#         word_list = player_fullname.split()
#         player_first_name = word_list[0]
#         player_last_name = " ".join(word_list[1:]) or None
#         return player_first_name, player_last_name
#
#     def player_profile_parse(self, full_url, league_id, team_id):
#         returned_soup = self.download_url_content(full_url)
#         player_h1 = returned_soup.find("h1", class_ = "Profile_headerMain__WPgYE")
#         player_nation = player_h1.find("img").get("title")
#         player_fullname = player_h1.text
#         adjusted_player_name = self.player_name_splitter(player_fullname)
#         player_surname = adjusted_player_name[0]
#         player_lastname = adjusted_player_name[1]
#
#         player_card_ul = returned_soup.find("ul", class_ = "PlayerFacts_factsList__Xw_ID")
#         list_of_player_facts = player_card_ul.find_all("li")
#         player_position = list_of_player_facts[5].text
#         sliced_player_position = player_position[len("Position"):]
#         player_date_of_birth = list_of_player_facts[0].text
#         sliced_player_date_of_birth = player_date_of_birth[len("Date of Birth"):]
#
#         new_player = player.Player(player_surname, player_lastname, player_nation, league_id, player_position, sliced_player_date_of_birth, team_id, full_url)
#         print(player_surname, player_lastname, player_nation, league_id, sliced_player_position, sliced_player_date_of_birth, team_id, full_url)
#         return new_player