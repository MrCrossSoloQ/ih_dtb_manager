from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import teams
import player

class WebScraper:
    def __init__(self, dtb_data):
        self.dtb_data = dtb_data
        self.scraped_items = []

    def get_url(self, url_content, chosen_league):
        for dtb_item in self.dtb_data:
            if dtb_item["league_id"] == chosen_league or chosen_league == 0:
                full_url = urljoin("https://www.eliteprospects.com/", dtb_item["elite_url"])
                returned_soup = self.download_url_content(full_url)

                if url_content == "league":
                    self.team_soup_parse(dtb_item["league_id"], returned_soup)
                elif url_content == "team_roster":
                    self.team_roster_parse(returned_soup, dtb_item["league_id"], dtb_item["team_id"])
        return self.scraped_items

    def download_url_content(self, full_url):
        response = requests.get(full_url)
        web = response.text
        soup = BeautifulSoup(web, "html.parser")
        return soup

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
        returned_soup = self.download_url_content(full_url)
        player_h1 = returned_soup.find("h1", class_ = "Profile_headerMain__WPgYE")
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

# from bs4 import BeautifulSoup
# import requests
# import teams
# from urllib.parse import urljoin
# import player
#
# """Funkce, která stáhne obsah webu, převede na bf4 objekt. Obsah stránky je následně parsován jako html"""
# def page_download(full_url):
#     response = requests.get(full_url)
#     web = response.text
#     soup = BeautifulSoup(web, "html.parser")
#     return soup
#
# def player_data_download(player_url, league_id, team_id):
#     full_url = urljoin("https://www.eliteprospects.com/", player_url)
#
#     soup = page_download(full_url)
#     header = soup.find("h1", class_="Profile_headerMain__WPgYE")
#
#     player_surname = header.text.split()[0] #uloží křestní jméno hráče
#     player_last_name = header.text.split()[1] #Uloží příjmení hráče
#     country = header.find('img')['title'] #uloží zemi hráče
#
#     player_facts = soup.find("ul", class_="PlayerFacts_factsList__Xw_ID")
#     all_li = player_facts.find_all("li")
#     date_of_birth = all_li[0].text
#     sliced_date_of_birth = date_of_birth[len("Date of Birth"):]
#     player_position = all_li[5].text
#     sliced_position = player_position[len("Position"):]
#     new_player = player.Player(player_surname, player_last_name, country, league_id, sliced_position, sliced_date_of_birth, team_id, full_url)
#     return new_player
#
# def players_url_download(teams, choosen_league):
#     list_of_players = []
#     for team in teams:
#         if team["league_id"] == choosen_league or choosen_league ==0:
#             full_url = urljoin("https://www.eliteprospects.com/", team["elite_url"]) #zde přepiš na team["elite_url"] a dej 2x tabulator, na zbylý blok funkce + odkomentovat cyklus for
#             print(full_url)
#
#             soup = page_download(full_url)
#
#             found_div = soup.find_all("div", class_="Roster_player__e6EbP")
#             for div_player in found_div:
#                 player_link = div_player.find("a", class_="TextLink_link__RhSiC")
#                 player_url = player_link.get("href")
#                 scraped_player = player_data_download(player_url, team["league_id"], team["team_id"])
#                 print(scraped_player.surname, scraped_player.last_name, scraped_player.nationality, scraped_player.player_position, scraped_player.team_id, scraped_player.league_id, scraped_player.date_of_birth, scraped_player.url)
#                 list_of_players.append(scraped_player)
#     return list_of_players
#
# def teams_download(leagues, choosen_league):
#     teams_data = []
#     for league in leagues:
#         if league["league_id"] == choosen_league or choosen_league ==0:
#             print(league["elite_url"])
#
#             soup = page_download(league["elite_url"])
#             found_teams = soup.find_all(name="a", class_="TextLink_link__RhSiC LabelWithIcon_link__67DL_ TableBody_link__dfR3c TableBody_plainText__KuMY7")
#             for team in found_teams:
#                 scraped_team = teams.Teams(league["league_id"], team.text, team.get("href"))
#                 teams_data.append(scraped_team)
#     return teams_data