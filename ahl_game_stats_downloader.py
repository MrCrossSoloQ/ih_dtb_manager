from data_downloader import PlaywrightController
import re
import ih_games
from difflib import get_close_matches
from datetime import timedelta, date
import player_game_sheet
from nhl_game_stats_downloader import NhlGameDownloader
import goalie_game_sheet

# class AhlGameDownloader(PlaywrightController, NhlGameDownloader):
#     def __init__(self, last_game_url, dtb_teams, dtb_games, dtb_players, my_dtb_driver):
#         super().__init__(dtb_data = None)
#         self.last_game_url = last_game_url #https://lscluster.hockeytech.com/game_reports/official-game-report.php?client_code=ahl&game_id=1026931&lang_id=1
#         self.dtb_teams = dtb_teams
#         self.dtb_games = dtb_games
#         self.dtb_players = dtb_players
#         self.my_dtb_driver = my_dtb_driver
#         self.ih_games = []

class AhlGameDownloader(NhlGameDownloader):
    def __init__(self, last_game_url, dtb_teams, dtb_ih_games, my_dtb_driver, downloader_controller):
        super().__init__(dtb_teams, dtb_ih_games, my_dtb_driver, downloader_controller)
        self.last_game_url = last_game_url

    def ahl_game_manager(self):
        while True:
            game_url = self.get_new_game_url(self.last_game_url)
            print(game_url)
            self.downloader_controller.playwright_starter()
            returned_html_content = self.downloader_controller.get_page_content(game_url)
            returned_soup = self.downloader_controller.soup_maker(returned_html_content)
            availability_result = self.game_availability(returned_soup)

            if availability_result is True:
                """V případě, že je hra dostupná, dojde k extrakci výsledku a statistik hráčů"""
                game_id = self.get_game_id(game_url)
                new_game = self.game_extractor(returned_soup, game_id)
                print(new_game)
                self.scraped_ih_games.append(new_game)
                self.last_game_url = game_url

            elif availability_result is False and self.scraped_ih_games:
                print(self.scraped_ih_games[-1].web_game_id)
                last_game_url = "https://lscluster.hockeytech.com/game_reports/official-game-report.php?client_code=ahl&game_id=" + str(self.scraped_ih_games[-1].web_game_id) + "&lang_id=1"
                self.my_dtb_driver.update_data("leagues", "schedule_url_source", last_game_url, "league_id", 2)
                print(self.scraped_ih_games)
                return self.scraped_ih_games

            elif availability_result is False and not self.scraped_ih_games:
                return False

    def get_season_stage(self, table, league_id_value, season_value, home_team_id_value, away_team_id_value, max_num_of_games_per_team):
        num_of_games_in_season = self.my_dtb_driver.get_num_of_all_team_games_in_season(table, league_id_value, season_value, home_team_id_value, away_team_id_value)
        print(f"Počet her v sezoně: {num_of_games_in_season}")
        if num_of_games_in_season[0]["count"] < max_num_of_games_per_team:
            return "season"
        else:
            return "playoff"

    def game_availability(self, returned_soup):
        "Funkce, která zjistí, zda je dostupný výsledek zápasu na stránce"
        body_text = returned_soup.find("body").text

        if body_text == "This game is not available.":
            return False
        else:
            return True

    def get_new_game_url(self, last_game_url):
        "Funkce, která vytvoří odkaz s následujícím zápasem. K ID posledního zápasu, uloženého v DTB přičte jedna, toto nové ID vloží do odkazu."
        last_game_id = self.get_game_id(last_game_url)
        new_game_id = int(last_game_id) + 1
        new_game_url = "https://lscluster.hockeytech.com/game_reports/official-game-report.php?client_code=ahl&game_id=" + str(new_game_id) + "&lang_id=1"
        test_game = "https://lscluster.hockeytech.com/game_reports/official-game-report.php?client_code=ahl&game_id=1026999&lang_id=1"

        return new_game_url

    def get_game_id(self, game_url):
        """Fce, která získá ID zápasu, které se vyskytuje v URL odkazu, dle nastaveného výrazu"""
        match = re.search(r"game_id=(.*?)&lang_id=1", game_url)
        if match:
            game_id = match.group(1)
            return int(game_id)

    def get_season(self, game_date):
        """Funkce na určení aktuální sezóny ve formátu (20242025)"""
        list_of_months = ["Dec", "Nov", "Oct"]
        yesterday_date_splited = game_date.split()
        current_year = int(yesterday_date_splited[2])
        next_year = current_year+1

        if yesterday_date_splited[0] in list_of_months:
            current_season = str(current_year) + str(next_year)
            return current_season
        else:
            current_season = str(current_year-1)+str(current_year)
            return current_season

    def game_extractor(self, game_soup, game_id):
        table = game_soup.find("table", class_ = "tSides")
        all_tr = table.find_all("tr")

        general_info = all_tr[0].find_all("td")
        home_team_list_of_td = all_tr[2].find_all("td")
        away_team_list_od_td = all_tr[1].find_all("td")

        home_team_scraped_name = home_team_list_of_td[0].text
        away_team_scraped_name = away_team_list_od_td[0].text

        home_team_scraped_goals = home_team_list_of_td[-1].text
        away_team_scraped_goals = away_team_list_od_td[-1].text

        dtb_home_team = self.get_dtb_team(home_team_scraped_name)
        home_team_id = dtb_home_team["team_id"]
        dtb_away_team = self.get_dtb_team(away_team_scraped_name)
        away_team_id = dtb_away_team["team_id"]

        print(dtb_home_team)
        print(dtb_away_team)

        game_result_type = self.result_type_finder(general_info)

        winner_team_id = self.get_winner_team(dtb_home_team, home_team_scraped_goals, dtb_away_team, away_team_scraped_goals)

        game_date = self.get_game_date(game_soup)
        game_date_dtb_format = self.game_date_dtb_formatter(game_date)
        season = self.get_season(game_date)

        season_stage = self.get_season_stage("ih_games",  2, season, home_team_id, away_team_id, 72)

        tables = game_soup.find_all("table", class_ = "tSidesC")

        away_team_players = self.players_extractor(tables[0], dtb_away_team, season)
        home_team_players = self.players_extractor(tables[2], dtb_home_team, season)
        all_skaters_stats_list = away_team_players + home_team_players

        away_team_goalies = self.goalies_extractor(tables[1], dtb_away_team, season)
        print(f"Brakáři venkovního týmu: {away_team_goalies}")

        home_team_goalies = self.goalies_extractor(tables[3], dtb_home_team, season)
        print(f"Brakáři domácího týmu: {home_team_goalies}")
        all_goalies_stats_list = away_team_goalies + home_team_goalies


        new_game = ih_games.IhGames(home_team_id, away_team_id, home_team_scraped_goals, away_team_scraped_goals, game_result_type, 2, winner_team_id, game_date_dtb_format, season, season_stage, game_id, all_skaters_stats_list, all_goalies_stats_list)
        return new_game

    def goalies_stats_extractor(self, td_list, dtb_team, season):
        print(td_list)
        jersey_num = td_list[0]
        goalie_name = td_list[1].text
        adjusted_goalie_name = goalie_name.split(" (")[0]
        print(adjusted_goalie_name)
        goalie_toi = td_list[2].text
        goalie_toi_adjusted = self.time_transfer(goalie_toi)
        goalie_shots = int(td_list[3].text)
        goalie_saves = int(td_list[4].text)
        print(goalie_saves)
        print(goalie_shots)
        goalie_save_percentage = round(goalie_saves / goalie_shots, 6)

        dtb_player_id = self.get_player_id(adjusted_goalie_name, dtb_team, jersey_num)

        print(f"player_dtb_id: {dtb_player_id}, goalie_toi: {goalie_toi_adjusted}, team_id: {dtb_team["team_id"]}, season: {season}, goalie_shots: {goalie_shots}, goalie_saves: {goalie_saves}, goalie_save_perc: {goalie_save_percentage}")

        new_goalie = goalie_game_sheet.GoalieGameSheet(dtb_player_id, goalie_toi_adjusted, dtb_team["team_id"], season, goalie_shots, goalie_saves, goalie_save_percentage, True)
        return new_goalie

    def goalies_extractor(self, table, dtb_team, season):
        list_of_goalies = []
        all_tr = table.find_all("tr")
        for tr in all_tr[2:][:-1]:
            all_td = tr.find_all("td")
            if all_td[0].text.strip() != "": #Odstraníme všechny mezery a v případě, že hodnota v řádku není prázdný string, program pokračuje
                new_goalie = self.goalies_stats_extractor(all_td, dtb_team, season)
                list_of_goalies.append(new_goalie)

        return list_of_goalies

    def player_stats_extractor(self, td_list, dtb_team, season):
        print(td_list)
        jersey_num = td_list[1].text
        current_game_player_name = td_list[2].text
        goals = int(td_list[3].text)
        assists = int(td_list[4].text)
        plus_minus = int(td_list[5].text)
        shots = int(td_list[6].text)
        pim = td_list[7].text

        print(jersey_num, current_game_player_name, goals, assists, plus_minus, shots, pim)
        player_id = self.get_player_id(current_game_player_name, dtb_team, jersey_num)
        pim_formatted = self.time_transfer(pim)
        print(player_id, current_game_player_name)

        new_player = player_game_sheet.PlayerGameSheet(player_id, goals, assists, goals+assists, plus_minus, pim_formatted, shots, None, None, None, None, dtb_team["team_id"], None, season)
        return new_player

    def players_extractor(self, table, dtb_team, season):
        list_of_players = []
        list_of_trs = table.find_all("tr")
        for tr in list_of_trs[2:][:-2]:
            td_list = tr.find_all("td")
            if td_list[0].text != "G":
                new_player = self.player_stats_extractor(td_list, dtb_team, season)
                list_of_players.append(new_player)
            else:
                print("Jedná se o golmana")
        return list_of_players

    # def get_dtb_team(self, scraped_team_name):
    #     print(scraped_team_name)
    #     dtb_team_name_list = []
    #     for team in self.dtb_teams:
    #         team_word_list = team["team_name"].split()
    #         words_num = len(team_word_list)
    #         if words_num > 2:
    #             adjusted_team_name = team_word_list[0] + " " + team_word_list[1]
    #             print(adjusted_team_name)
    #             dtb_team_name_list.append(adjusted_team_name)
    #         else:
    #             adjusted_team_name = team_word_list[0]
    #             print(adjusted_team_name)
    #             dtb_team_name_list.append(adjusted_team_name)
    #     print(f"List týmů: {dtb_team_name_list}")
    #
    #     name_match = get_close_matches(scraped_team_name, dtb_team_name_list, 1, 0.7)
    #     print(name_match)
    #     for dtb_team in self.dtb_teams:
    #         if name_match[0] in dtb_team["team_name"]:
    #             print(f"Jméno týmu z databáze: {dtb_team}")
    #             return dtb_team
    #
    # def get_dtb_team(self, scraped_team_name):
    #     print(scraped_team_name)
    #     dtb_team_name_list = [team["team_name"] for team in self.dtb_teams]
    #     print(dtb_team_name_list)
    #     name_match = get_close_matches(scraped_team_name, dtb_team_name_list, 1, 0.7)
    #     print(name_match)
    #     for dtb_team in self.dtb_teams:
    #         if name_match[0] in dtb_team["team_name"]:
    #             print(dtb_team)
    #             return dtb_team

    def get_dtb_team(self, scraped_team_name):
        print(scraped_team_name)
        for team in self.dtb_teams:
            if scraped_team_name in team["team_name"]:
                print(f"Shoda týmu v DTB: {team['team_name']}")
                return team

    def result_type_finder(self, general_info):
        word_list = [item.text for item in general_info]
        if "SO" in word_list:
            return "SO"
        if "OT" in word_list:
            return "OT"
        else:
            return "REG"

    def ahl_all_game_reports_finder(self, returned_soup):
        """Najde veškeré url odkazy, na stránce k daným hrám"""
        list_of_game_urls = []
        all_links = returned_soup.find_all("a", title = "Game Sheet")
        for link in all_links:
            ahl_game_report = link["href"]
            list_of_game_urls.append(ahl_game_report)
        return list_of_game_urls

    def get_game_date(self, game_soup):
        all_br_tags = game_soup.find_all("br")
        date_tag = all_br_tags[2].next_sibling.strip()  # vrátí text, který následuje hned za tagem, který je na druhém indexu v listu
        scraped_word_list = date_tag.split()
        coma_deleted = scraped_word_list[1][:-1]
        scraped_word_list[1] = coma_deleted
        game_date = " ".join(scraped_word_list)
        print(game_date)
        return game_date

    def game_date_dtb_formatter(self, game_date):
        """Najde datum zápasu na stránce a uvedeho do správného tvaru (2024-12-31)"""
        months_dic = {
            "Jan":"1",
            "Feb":"2",
            "Mar":"3",
            "Apr":"4",
            "May":"5",
            "Jun":"6",
            "Jul":"7",
            "Aug":"8",
            "Sep":"9",
            "Oct":"10",
            "Nov":"11",
            "Dec":"12",
        }
        game_date_values_in_list = game_date.split()
        game_date_values_in_list[0], game_date_values_in_list[1], game_date_values_in_list[2] = game_date_values_in_list[2], game_date_values_in_list[0], game_date_values_in_list[1]
        game_date_values_in_list[1] = months_dic[game_date_values_in_list[1]]
        scraped_date_formatted = "-".join(game_date_values_in_list)
        print(scraped_date_formatted)

        return scraped_date_formatted

    # def today_date_generator_and_formatter(self):
    #     """Vygeneruje dnešní datum, ze kterého vytvoří včerejší a uvede ho do správného formátu (Dec 8, 2024)"""
    #     today_date = date.today() - timedelta(days=1)
    #     formatted_date = today_date.strftime("%B %d %Y").replace(" 0", " ")
    #     list_of_words = formatted_date.split()
    #     day_adjust = list_of_words[1]+","
    #     month_adjust = list_of_words[0][:3]
    #     list_of_words[1] = day_adjust
    #     list_of_words[0] = month_adjust
    #     correctly_formatted_date = " ".join(list_of_words)
    #     print(correctly_formatted_date)
    #
    #     return correctly_formatted_date