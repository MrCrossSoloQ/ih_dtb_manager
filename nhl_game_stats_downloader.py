from datetime import datetime, timedelta
from urllib.parse import urljoin, unquote
import requests
import ih_games
from unidecode import unidecode
from difflib import get_close_matches
import goalie_game_sheet
import player_game_sheet
import player
# import json

class NhlGameDownloader:
    def __init__(self, dtb_teams, dtb_ih_games, my_dtb_driver, downloader_controller, league_schedule_url = None):
        self.league_schedule_url = league_schedule_url #https://api-web.nhle.com/v1/schedule/
        self.dtb_teams = dtb_teams
        self.dtb_ih_games = dtb_ih_games
        self.dtb_players = None
        self.my_dtb_driver = my_dtb_driver
        self.downloader_controller = downloader_controller
        self.scraped_ih_games = []
        self.yesterday_date_only = None

    def get_date(self):
        """Vygeneruje dnešní datum a po odečtu vrátí včerejší"""
        today = datetime.today()
        self.yesterday_date_only = today.date() - timedelta(days=1)

    def get_schedule_url(self, league_url_source):
        """Spojením url + včerejšího data, vrátí url s výsledky včerejších zápasů + rozpis zápasů na 7 dní"""
        yesterday_game_sheet_url = urljoin(league_url_source, str(self.yesterday_date_only))
        return yesterday_game_sheet_url

    def url_content_downloader(self, url):
        """Zašleme požadavek na server zadané URL, vrátí se nám objekt response s několika atributy"""
        response = requests.get(url)
        data = response.json()  # pokud server vrátí obsah stránky ve formátu json, převedeme je na dictionary
        return data

    def todays_games(self, data):
        """Funkce která nám získá id her, které byly odehrány pouze za včerejšího data a vrátí nám je jako list"""
        game_ids = []
        for gameweek in data["gameWeek"]:
            if gameweek["date"] == str(self.yesterday_date_only):
                for game in gameweek["games"]:
                    game_ids.append(game["id"])

        print(game_ids)

        return game_ids

    def url_maker_game_stats(self, game_ids):
        """Funkce, která ze stažených id zápasů, vytvoří odkaz ke statistikám daného zápasu a vrátí je jako list"""
        list_of_game_urls = []
        for game_id in game_ids:
            game_stats_url = urljoin("https://api-web.nhle.com/v1/gamecenter/", str(game_id) + "/boxscore/")
            list_of_game_urls.append(game_stats_url)
        return list_of_game_urls

    def game_result_sheet(self, game_urls):
        """Funkce, která vezme stažený obsah stránky, každého zápasu, který je jako dictionary a vytahá z něj potřebné údaje, které poukládá do proměnných"""

        for game_url in game_urls:
            print("---------------------------------------------------------------")
            print(f"URL zápasu: {game_url}")
            downloaded_content = self.url_content_downloader(game_url)
            # print(json.dumps(downloaded_content, indent=4))

            home_team_name = downloaded_content["homeTeam"]["placeName"]["default"] + " " + \
                             downloaded_content["homeTeam"]["commonName"]["default"]
            away_team_name = downloaded_content["awayTeam"]["placeName"]["default"] + " " + \
                             downloaded_content["awayTeam"]["commonName"]["default"]
            game_state = downloaded_content["gameState"]

            """Pokud zápas nebyl odehrán, iterace bude přeskočena"""
            if game_state == "FUT":
                print(f"Zápas: {home_team_name} - {away_team_name} nebyl odehrán")
                continue

            home_team_score = downloaded_content["homeTeam"]["score"]
            away_team_score = downloaded_content["awayTeam"]["score"]
            result_type = downloaded_content["periodDescriptor"]["periodType"]
            season = downloaded_content["season"]
            game_type = downloaded_content["gameType"]  # na nhl.com tím určují o jaký zápas v sezoně se jedná (1 - preseason, 2 - season, 3 - playoff)
            match_date = downloaded_content["gameDate"]
            web_game_id = downloaded_content["id"]

            away_team_forwards_stats = downloaded_content["playerByGameStats"]["awayTeam"]["forwards"]
            away_team_defense_stats = downloaded_content["playerByGameStats"]["awayTeam"]["defense"]
            away_team_goalies_stats = downloaded_content["playerByGameStats"]["awayTeam"]["goalies"]
            away_team_all_skaters = away_team_forwards_stats + away_team_defense_stats

            home_team_forwards_stats = downloaded_content["playerByGameStats"]["homeTeam"]["forwards"]
            home_team_defense_stats = downloaded_content["playerByGameStats"]["homeTeam"]["defense"]
            home_team_goalies_stats = downloaded_content["playerByGameStats"]["homeTeam"]["goalies"]
            home_team_all_skaters = home_team_forwards_stats + home_team_defense_stats

            dtb_home_team = self.dtb_team_searcher(home_team_name, self.dtb_teams)
            dtb_away_team = self.dtb_team_searcher(away_team_name, self.dtb_teams)
            season_stage = self.get_season_stage(game_type)
            winner_team = self.get_winner_team(dtb_home_team, home_team_score, dtb_away_team, away_team_score)

            away_team_skaters_stats_list = self.player_stats_sheet(away_team_all_skaters, dtb_away_team, season)
            away_team_goalies_stats_list = self.goalies_stats_sheet(away_team_goalies_stats, dtb_away_team, season)

            home_team_skaters_stats_list = self.player_stats_sheet(home_team_all_skaters,
                                                              dtb_home_team, season)
            home_team_goalies_stats_list = self.goalies_stats_sheet(home_team_goalies_stats,
                                                               dtb_home_team, season)

            all_skaters_stats_list = away_team_skaters_stats_list + home_team_skaters_stats_list
            all_goalies_stats_list = away_team_goalies_stats_list + home_team_goalies_stats_list

            """Z daných údajů ze zápasu, vytvoří objekt podle třídy IhGames uloží ho do proměnné a přidá do listu"""
            new_game = ih_games.IhGames(dtb_home_team["team_id"], dtb_away_team["team_id"], home_team_score,
                                        away_team_score, result_type, dtb_home_team["league_id"],
                                        winner_team["team_id"], match_date, season, season_stage, web_game_id,
                                        all_skaters_stats_list, all_goalies_stats_list)
            self.scraped_ih_games.append(new_game)

            # print(season_stage)
            # print(season)
            # print(match_date)
            # print(away_team_name)
            # print(away_team_score)
            # print(home_team_name)
            # print(home_team_score)
            # print(result_type)

    def get_winner_team(self, dtb_home_team, home_team_score, dtb_away_team, away_team_score):
        """Funkce, která zjistí, který tým vyhrál zápas, následně vrátí vítězný tým s údají z dtb"""
        if home_team_score > away_team_score:
            return dtb_home_team
        else:
            return dtb_away_team

    def get_season_stage(self, game_type):
        """Funkce, která zjistí, o jaký zápas v sezoně se jedná: preseason/season/playoff"""
        game_types = {
            1: "preseason",
            2: "season",
            3: "playoff",
        }
        return game_types[game_type]

    def dtb_team_searcher(self, team_name, dtb_returned_teams):
        """Funkce, do které pošleme název týmu ze zápasu a podle jeho názvu hledá shodu s týmem, který byl vrácen z DTB, když najde vrátí ho"""
        corrected_team_name = self.team_name_correction(team_name)
        for dtb_team in dtb_returned_teams:
            if dtb_team["team_name"] == corrected_team_name:
                print(dtb_team)
                print(f"Index teamu v listu je: {dtb_returned_teams.index(dtb_team)}")
                return dtb_team

        return print(f"Team: {team_name} nenalezen")

    def team_name_correction(self, team_name):
        "Pokud se ve staženém názvu teamu opakuje nějaké slovo dojde k jeho odstranění"
        word_list = team_name.split()
        uniq_word_list = []
        for word in word_list:
            if word not in uniq_word_list:
                uniq_word_list.append(word)
        corrected_team_name = " ".join(uniq_word_list)
        print(len(corrected_team_name))
        print(corrected_team_name)
        return corrected_team_name

    def goalies_stats_sheet(self, list_of_goalies, dtb_team, season):
        """Získání všech statistik golmanů v daném zápase a následně vytvoření objektu goalie_game_stats a vložení do listu"""
        goalies_stats_list = []
        # print(json.dumps(list_of_goalies, indent=4))
        for goalie in list_of_goalies:
            goalie_name = goalie["name"]["default"]
            goalie_toi = goalie["toi"]
            jersey_num = goalie["sweaterNumber"]

            goalie_toi_transfered = self.time_transfer(goalie_toi)
            if goalie_toi == "00:00":
                player_id = self.get_player_id(goalie_name, dtb_team, jersey_num)
                goalie_game_stats = goalie_game_sheet.GoalieGameSheet(player_id, goalie_toi_transfered,
                                                                      dtb_team["team_id"], season, 0, 0, 0.00, False)
                goalies_stats_list.append(goalie_game_stats)
                if player_id is None:
                    self.create_log_file_goalies(goalie_game_stats)
            else:
                goalie_shots = goalie["shotsAgainst"]
                goalie_saves = goalie["saves"]
                goalie_save_percentage = goalie["savePctg"]

                player_id = self.get_player_id(goalie_name, dtb_team, jersey_num)
                goalie_game_stats = goalie_game_sheet.GoalieGameSheet(player_id, goalie_toi_transfered, dtb_team["team_id"], season, goalie_shots, goalie_saves, goalie_save_percentage, True)
                goalies_stats_list.append(goalie_game_stats)
                if player_id is None:
                    self.create_log_file_goalies(goalie_game_stats)
        return goalies_stats_list

    def player_stats_sheet(self, list_of_players, dtb_team, season):
        players_stats_list = []
        for player in list_of_players:
            print(player)
            jersey_num = player["sweaterNumber"]
            player_name = player["name"]["default"]
            player_goals = player["goals"]
            player_assists = player["assists"]
            player_points = player["points"]
            player_plus_minus = player["plusMinus"]
            player_pim = player["pim"]
            player_sog = player["sog"]
            player_hits = player["hits"]
            player_ppg = player["powerPlayGoals"]
            player_toi = player["toi"]
            player_faceoff = player["faceoffWinningPctg"]
            player_blocked_shots = player["blockedShots"]

            dtb_team_id = dtb_team["team_id"]

            player_pim_adjusted = int(player_pim)
            player_toi_adjusted = self.time_transfer(player_toi)

            print(f"player_stats_sheet: {dtb_team}")
            dtb_player_id = self.get_player_id(player_name, dtb_team, jersey_num)

            player_stats = player_game_sheet.PlayerGameSheet(dtb_player_id ,player_goals, player_assists, player_points,
                                                             player_plus_minus, player_pim_adjusted, player_sog,
                                                             player_hits, player_ppg, player_toi_adjusted,
                                                             player_faceoff, dtb_team_id, player_blocked_shots,
                                                             season)

            players_stats_list.append(player_stats)

            print(player_name, player_goals, player_assists, player_points, player_plus_minus, player_pim_adjusted,
                  player_sog, player_hits, player_ppg, player_toi_adjusted, player_faceoff, player_blocked_shots)

            if dtb_player_id is None:
                self.create_log_file_players(player_stats)

        return players_stats_list

    def create_log_file_players(self, player_stats):
        """Vytvoří soubor, do kterého zapíše staty hráče v poli, který nebyl stotožněn s žádným hráčem v DTB nebo na eliteprospects.com"""
        file_name = rf"C:\Users\tomas\Desktop\Python\Projekty\TrackThePlayers\unmached_players\{self.yesterday_date_only}_players.txt"
        with open(file_name, "a", encoding="utf-8") as log_file:
            log_file.write(f"{player_stats.player_name} | {player_stats.player_goals} | {player_stats.player_assists} | {player_stats.player_points} | {player_stats.player_plus_minus} | {player_stats.player_pim_adjusted} | {player_stats.player_sog} | {player_stats.player_hits} | {player_stats.player_ppg} | {player_stats.player_toi_adjusted} | {player_stats.player_faceoff} | {player_stats.player_blocked_shots}\n")

    def create_log_file_goalies(self, goalie_game_stats):
        """Vytvoří soubor, do kterého zapíše staty brankáře, který nebyl stotožněn s žádným hráčem v DTB nebo na eliteprospects.com"""
        file_name = rf"C:\Users\tomas\Desktop\Python\Projekty\TrackThePlayers\unmached_players\{self.yesterday_date_only}_goalies.txt"
        with open(file_name, "a", encoding="utf-8") as log_file:
            log_file.write(f"{goalie_game_stats.goalie_name} | {goalie_game_stats.goalie_toi_transfered} | {goalie_game_stats.dtb_team} | {goalie_game_stats.season} | {goalie_game_stats.goalie_shots} | {goalie_game_stats.goalie_saves} | {goalie_game_stats.goalie_save_percentage} | {goalie_game_stats.played}\n")

    def time_transfer(self, time):
        print(time)
        word_list = str(time).split(":")
        print(word_list)
        minutes, seconds = word_list[0], word_list[1]
        interval_format = f"{minutes}:{seconds}"
        print(interval_format)
        return interval_format

    def get_player_id_second_stage(self, dtb_team_roster, game_searched_player_name):
        print(game_searched_player_name)
        name_list = []

        for dtb_returned_player in dtb_team_roster:
            """Cyklus, který hledá přímou shodu jmen hráčů"""
            dtb_player_name = dtb_returned_player["surname"][:1] + ". " + dtb_returned_player["last_name"]
            # print(f"Variace jmen hráče: {dtb_returned_player['name_variants']}")
            if dtb_player_name == game_searched_player_name or game_searched_player_name in dtb_returned_player["name_variants"]:
                return dtb_returned_player["player_id"]
            else:
                name_list.append(dtb_player_name)
                name_list.extend(dtb_returned_player["name_variants"])

        print(f"List jmen: {name_list}")
        closest_match = get_close_matches(game_searched_player_name, name_list, 1, 0.8)
        print(f"Hledám hráče v DTB {game_searched_player_name}")
        print(f"Nejblížší shoda je: {closest_match}")
        if closest_match:
            for dtb_returned_player in dtb_team_roster:
                dtb_shorted_player_name = dtb_returned_player["surname"][:1] + ". " + dtb_returned_player["last_name"]
                dtb_player_diacriticsless = unidecode(dtb_shorted_player_name)
                if dtb_player_diacriticsless == closest_match[0]:
                    return dtb_returned_player["player_id"]

    def get_player_id(self, game_searched_player_name, dtb_team, jersey_num):
        """Metoda, která nám porovná jméno staženého hráče ze hry s hráčem uloženým v DTB a vrátí jeho id"""
        game_searched_player_name = unidecode(game_searched_player_name) #odstranění diakritiky

        dtb_team_roster = self.my_dtb_driver.get_data_on_simple_condition("players", "team_id", dtb_team["team_id"]) #Vrátí všechny hráče z DTB na základě id teamu
        player_id_result = self.get_player_id_second_stage(dtb_team_roster, game_searched_player_name)
        if player_id_result is not None:
            return player_id_result
        else:
            dtb_affiliated_team_roster = self.my_dtb_driver.get_data_on_simple_condition("players", "team_id", dtb_team["affiliated_team_id_one"]) ##Vrátí všechny hráče z DTB na základě id přidruženého týmu
            player_id_result = self.get_player_id_second_stage(dtb_affiliated_team_roster, game_searched_player_name)
            if player_id_result is not None:
                return player_id_result

            else:
                dtb_returned_players = self.my_dtb_driver.get_data_simple("players") #Vrátí seznam všech hráčů v DTB a hledá v nich
                # print(f"Vrácený seznam všech hráčů z DTB: {dtb_returned_players}")
                player_id_result = self.get_player_id_second_stage(dtb_returned_players, game_searched_player_name)
                if player_id_result is not None:
                    return player_id_result

                else:
                    print(f"Hledaný hráč: {game_searched_player_name} se v DTB nenachází!") #Stažení aktuální sestavy týmu, ve kterém hrál
                    print("Hledám hráče v aktuálním rosteru týmu!")
                    team_full_url = dtb_team["elite_url"] + "/depth-chart"
                    print(f"Stahuji roster aktuálního týmu: {team_full_url}")
                    self.downloader_controller.playwright_starter()
                    page_result = self.downloader_controller.load_page(team_full_url)
                    if page_result is True:
                        page_content = self.downloader_controller.get_page_content()
                        soup = self.downloader_controller.soup_maker(page_content)
                        player_id_result = self.roster_players_extractor(soup, game_searched_player_name, dtb_team, jersey_num)
                        if player_id_result is not None:
                            return player_id_result

                        else:
                            self.downloader_controller.playwright_starter()
                            list_of_scraped_players = self.downloader_controller.elite_prospects_get_player(game_searched_player_name, dtb_team)
                            print(f"List nalezených hráčů v DTB na elite prospects: {list_of_scraped_players}")
                            if len(list_of_scraped_players) == 1:
                                scraped_data_item = list_of_scraped_players[0]
                                player_id_result = self.my_dtb_driver.insert_data_and_return_id("players", ["surname", "last_name", "nationality", "league_id", "player_position", "date_of_birth", "team_id", "elite_url", "name_variants"],[scraped_data_item.surname, scraped_data_item.last_name, scraped_data_item.nationality, scraped_data_item.league_id, scraped_data_item.player_position, scraped_data_item.date_of_birth, scraped_data_item.team_id, scraped_data_item.url, scraped_data_item.name_variants], "player_id")
                                print(f"ID nově přidaného hráře po přidání do DTB: {player_id_result}")
                                if player_id_result is not None:
                                    return player_id_result

    # def get_dtb_team_url(self, dtb_team_id, current_game_player):
    #     """Metoda, která najde tým z dtb, ke kterému hledáme hráče a získá url k jeho sestavě hráčů. """
    #     for team in self.dtb_teams:
    #         if team["team_id"] == dtb_team_id:
    #             team_full_url = "https://www.eliteprospects.com/team" + team["elite_url"]
    #             html_content = self.url_content_downloader(team_full_url)
    #             returned_soup = self.downloader_controller.soup_maker(html_content)
    #             self.roster_players_extractor(returned_soup, current_game_player, dtb_team_id)

    def player_info_exctractor(self, tag_a, dtb_team):
        player_url = tag_a.get("href")
        scraped_player_full_url = "https://www.eliteprospects.com" + player_url
        decoded_player_url = unquote(scraped_player_full_url)

        scraped_player_name = tag_a.text
        player_first_name, player_last_name, shorted_name = self.player_name_splitter(scraped_player_name)

        scraped_player = player.Player(surname=player_first_name, last_name=player_last_name, team_id=dtb_team["team_id"], url=decoded_player_url, player_shorted_name=shorted_name)
        return scraped_player

    def roster_players_extractor(self, soup, searched_player, dtb_team, game_jersey_num):
        """Získáme všechny jména hráčů a URL adresy k jejich profilům z daného týmu. """
        list_of_scraped_roster = []

        section = soup.find("section", id="page-content")
        table = section.find("div", class_="Loader_loadingContentWrapper__i1kEt")
        all_trs = table.find_all("tr", class_="SortTable_tr__L9yVC")

        for tr in all_trs:
            if dtb_team["league_id"] == 1:
                signed = tr.find("span", class_="Icon_signed__oWT9F")
                if signed:
                    tag_a = tr.find("a", class_="TextLink_link__RhSiC LabelWithIcon_link__67DL_")
                    scraped_player = self.player_info_exctractor(tag_a, dtb_team)
                    list_of_scraped_roster.append(scraped_player)
                    print(scraped_player.surname, scraped_player.last_name, scraped_player.url, scraped_player.player_shorted_name)

            elif dtb_team["league_id"] == 2:
                tag_a = tr.find("a", class_="TextLink_link__RhSiC")
                if tag_a is not None:
                    scraped_player = self.player_info_exctractor(tag_a, dtb_team)
                    list_of_scraped_roster.append(scraped_player)
                    print(scraped_player.surname, scraped_player.last_name, scraped_player.url, scraped_player.player_shorted_name)

        player_id = self.player_data_dtb_adjustment(list_of_scraped_roster, searched_player, dtb_team, game_jersey_num)
        print(f"Vrácené ID hráče po stažení aktuální sestavy týmu: {player_id}")
        return player_id

    def player_data_dtb_adjustment(self, list_of_scraped_roster, searched_player, dtb_team, jersey_num):
        """Jestliže hráč v DTB vůbec není, dojde ke stažení jeho dat a přidání do DTB a vrácení jeho ID v DTB.
            Pokud u hledaného hráče došlo ke změně týmu dojde k aktualizaci v DTB.
        """
        reduced_scraped_roster = self.scraped_roster_reduction_by_letter(list_of_scraped_roster, searched_player)
        searched_player = self.get_close_match(searched_player, reduced_scraped_roster, jersey_num)
        print(f"player_data_dtb_adjustment/shody: {searched_player}")
        for player in reduced_scraped_roster:
            if player.player_shorted_name == searched_player:
                dtb_returned_player = self.my_dtb_driver.get_data_on_simple_condition("players", "elite_url", player.url)
                print(f"Stažený hráč ze sestavy se nachází v DTB: {dtb_returned_player}")
                if dtb_returned_player:
                    player_id = dtb_returned_player[0]["player_id"]
                    print(f"Vrácené ID hráče z DTB u kterého proběhne update teamu: {player_id}")
                    self.my_dtb_driver.update_data("players", "team_id", dtb_team["team_id"], "player_id", player_id)
                    return player_id

                elif not dtb_returned_player:
                    self.downloader_controller.playwright_starter()
                    new_player = self.downloader_controller.player_profile_parse(player.url, dtb_team["league_id"], dtb_team["team_id"])
                    player_id = self.my_dtb_driver.insert_data_and_return_id("players", ["surname", "last_name", "nationality", "league_id", "player_position", "date_of_birth", "team_id", "elite_url", "name_variants"],[new_player.surname, new_player.last_name, new_player.nationality, new_player.league_id, new_player.player_position, new_player.date_of_birth, new_player.team_id, new_player.url, new_player.name_variants], "player_id")
                    print(f"ID nově přidaného hráče z aktuální sestavy týmu: {player_id}")
                    return player_id

    def scraped_roster_reduction_by_letter(self, list_of_scraped_roster, searched_player):
        """Zredukuje nám staženou sestavu, ve které hledáme hráče, na základě počátečního písmena, hledaného hráče"""
        reduced_roster = []
        searched_player_innitiall_letter = searched_player[:1]
        for player in list_of_scraped_roster:
            first_name_letter = player.player_shorted_name[:1]
            if first_name_letter == searched_player_innitiall_letter:
                self.downloader_controller.playwright_starter()
                page_result = self.downloader_controller.load_page(player.url)
                if page_result is True:
                    page_content = self.downloader_controller.get_page_content()
                    soup = self.downloader_controller.soup_maker(page_content)
                    h2 = soup.find("h2", class_="Profile_subTitlePlayer__drUwD")
                    word_list = h2.text.strip().split()
                    jersey_num = word_list[0][1:]
                    player.jersey_number = jersey_num
                    reduced_roster.append(player)

        print("Stažená aktuální sestava týmu a redukována, na základě počátečního písmena hledaného hráče.")
        for player in reduced_roster:
            print(player.surname, player.last_name, player.url)
        return reduced_roster

    def jersey_num_comparator(self, current_game_player_name, jersey_num, reduced_scraped_roster):
        for player in reduced_scraped_roster:
            if player.player_shorted_name == current_game_player_name and player.jersey_number == jersey_num:
                return player

    def get_close_match(self, current_game_player, reduced_scraped_roster, jersey_num):
        current_roster_names = [player.player_shorted_name for player in reduced_scraped_roster]
        list_of_close_matches = get_close_matches(current_game_player, current_roster_names, 1, 0.7)

        if len(list_of_close_matches) == 1:
            return list_of_close_matches[0]
        elif len(list_of_close_matches) > 1:
            returned_player = self.jersey_num_comparator(current_game_player, jersey_num, reduced_scraped_roster)
            return returned_player
        elif not list_of_close_matches:
            print("Nebyla nalezena shoda hledaného hráče v aktuální stažené sestavě týmu na eliteprospects.com")

    def player_name_splitter(self, player_fullname):
        """Rozdělí nám jméno staženého hráče na křestní jméno a příjmené"""
        word_list = player_fullname.split()
        player_first_name = word_list[0]
        player_last_name = " ".join(word_list[1:][:-1]) or None
        shorted_name = player_first_name[0] + ". " + player_last_name
        return player_first_name, player_last_name, shorted_name

    def downloader_manager(self):
        self.get_date()
        schedule_url = self.get_schedule_url(self.league_schedule_url)
        url_content = self.url_content_downloader(schedule_url)
        list_of_game_ids = self.todays_games(url_content)
        if not list_of_game_ids:
            return False
        list_of_game_urls = self.url_maker_game_stats(list_of_game_ids)
        self.game_result_sheet(list_of_game_urls)
        print(list_of_game_urls)
        print(self.scraped_ih_games)
        return self.scraped_ih_games