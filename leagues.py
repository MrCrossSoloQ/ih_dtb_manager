from bs4 import BeautifulSoup
import requests
import teams
class Leagues:
    def __init__(self, league_id, league_name, league_short_cut, url, league_official_url):
        self.league_id = league_id
        self.league_name = league_name
        self.league_short_cut = league_short_cut
        self.url = url
        self.league_official_url = league_official_url

    # def teams_download(self, leagues):
    #     teams_data = []
    #     for league in leagues:
    #         print(league["league_elite_url"])
    #
    #         response = requests.get(league["league_elite_url"])
    #         web = response.text
    #         soup = BeautifulSoup(web, "html.parser")
    #         found_teams = soup.find_all(name="a",
    #                                     class_="TextLink_link__RhSiC LabelWithIcon_link__67DL_ TableBody_link__dfR3c TableBody_plainText__KuMY7")
    #         for team in found_teams:
    #             scraped_team = teams.Teams(league["league_id"], league["league_short_cut"], team.text, team.get("href"))
    #             teams_data.append(scraped_team)
    #     return teams_data