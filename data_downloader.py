from bs4 import BeautifulSoup
import requests
import teams
from urllib.parse import urljoin
import player

"""Funkce, která stáhne obsah webu, převede na bf4 objekt. Obsah stránky je následně parsován jako html"""
def page_download(full_url):
    response = requests.get(full_url)
    web = response.text
    soup = BeautifulSoup(web, "html.parser")
    return soup

def player_data_download(player_url, league_id, team_id):
    full_url = urljoin("https://www.eliteprospects.com/", player_url)

    soup = page_download(full_url)
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

def players_url_download(teams, choosen_league):
    list_of_players = []
    # for team in teams:
    #     if team["league_id"] == choosen_league or choosen_league ==0:
    full_url = urljoin("https://www.eliteprospects.com/", teams[0]["elite_url"])
    print(full_url)

    soup = page_download(full_url)

    found_div = soup.find_all("div", class_="Roster_player__e6EbP")
    for div_player in found_div:
        player_link = div_player.find("a", class_="TextLink_link__RhSiC")
        player_url = player_link.get("href")
        scraped_player = player_data_download(player_url, teams[0]["league_id"], teams[0]["team_id"])
        print(scraped_player.surname, scraped_player.last_name, scraped_player.nationality, scraped_player.player_position, scraped_player.team_id, scraped_player.league_id, scraped_player.date_of_birth, scraped_player.url)
        list_of_players.append(scraped_player)
    return list_of_players


def teams_download(leagues, choosen_league):
    teams_data = []
    for league in leagues:
        if league["league_id"] == choosen_league or choosen_league ==0:
            print(league["elite_url"])

            soup = page_download(league["elite_url"])
            found_teams = soup.find_all(name="a", class_="TextLink_link__RhSiC LabelWithIcon_link__67DL_ TableBody_link__dfR3c TableBody_plainText__KuMY7")
            for team in found_teams:
                scraped_team = teams.Teams(league["league_id"], team.text, team.get("href"))
                teams_data.append(scraped_team)
    return teams_data