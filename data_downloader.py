from bs4 import BeautifulSoup
import requests
import teams

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

def teams_download(leagues):
    teams_data = []
    for league in leagues:
        print(league["league_elite_url"])

        response = requests.get(league["league_elite_url"])
        web = response.text
        soup = BeautifulSoup(web, "html.parser")
        found_teams = soup.find_all(name="a", class_="TextLink_link__RhSiC LabelWithIcon_link__67DL_ TableBody_link__dfR3c TableBody_plainText__KuMY7")
        for team in found_teams:
            scraped_team = teams.Teams(league["league_id"], league["league_short_cut"], team.text, team.get("href"))
            teams_data.append(scraped_team)
    return teams_data