from bs4 import BeautifulSoup
import requests
import teams
from urllib.parse import urljoin
import player

# class DataDownloader:
#     def __init__(self, url, ):
#         pass
#
#     def teams_download(self):
#         response = requests.get("https://www.eliteprospects.com/leagues")
#         web = response.text
#         soup = BeautifulSoup(web, "html.parser")
#         find_section = soup.find(name="section", id="page-content")
#         find_teams = soup.find_all(name="a", class_="TextLink_link__RhSiC LabelWithIcon_link__67DL_ TableBody_link__dfR3c")
#         for team in find_teams:
#             print(team.text, team.get("href"))

def player_data_download(player_url, league_id, team_id):
    full_url = urljoin("https://www.eliteprospects.com/", player_url)

    response = requests.get(full_url)
    web = response.text
    soup = BeautifulSoup(web, "html.parser")
    header = soup.find("h1", class_="Profile_headerMain__WPgYE")

    player_surname = header.text.split()[0]
    player_last_name = header.text.split()[1]
    country = header.find('img')['title']

    player_facts = soup.find("ul", class_="PlayerFacts_factsList__Xw_ID")
    all_li = player_facts.find_all("li")
    date_of_birth = all_li[0].text
    sliced_date_of_birth = date_of_birth[len("Date of Birth"):]
    player_position = all_li[5].text
    sliced_position = player_position[len("Position"):]
    new_player = player.Player(player_surname, player_last_name, country, league_id, sliced_position, sliced_date_of_birth, team_id, full_url)
    return new_player

def players_url_download(teams):
    list_of_players = []
    for team in teams:
        full_url = urljoin("https://www.eliteprospects.com/", team["elite_url"])
        print(full_url)

        response = requests.get(full_url)
        web = response.text
        soup = BeautifulSoup(web, "html.parser")
        found_div = soup.find_all("div", class_="Roster_player__e6EbP")
        for div_player in found_div:
            player_link = div_player.find("a", class_="TextLink_link__RhSiC")
            player_url = player_link.get("href")
            scraped_player = player_data_download(player_url, team["league_id"], team["team_id"])
            print(scraped_player.surname, scraped_player.last_name, scraped_player.nationality, scraped_player.player_position, scraped_player.team_id, scraped_player.league_id, scraped_player.date_of_birth, scraped_player.url)
            list_of_players.append(scraped_player)
    return list_of_players


def teams_download(leagues):
    teams_data = []
    for league in leagues:
        print(league["elite_url"])

        response = requests.get(league["elite_url"])
        web = response.text
        soup = BeautifulSoup(web, "html.parser")
        found_teams = soup.find_all(name="a", class_="TextLink_link__RhSiC LabelWithIcon_link__67DL_ TableBody_link__dfR3c TableBody_plainText__KuMY7")
        for team in found_teams:
            scraped_team = teams.Teams(league["league_id"], league["league_short_cut"], team.text, team.get("href"))
            teams_data.append(scraped_team)
    return teams_data