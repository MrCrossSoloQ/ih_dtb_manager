from datetime import datetime, timedelta
from urllib.parse import urljoin
import requests
import ih_games
from unidecode import unidecode
from difflib import get_close_matches
import goalie_game_sheet
import player_game_sheet

class NhlGameDownloader:
    def __init__(self, league_schedule_url, dtb_teams, dtb_ih_games, dtb_players):
        self.league_schedule_url = league_schedule_url #https://api-web.nhle.com/v1/schedule/
        self.dtb_teams = dtb_teams
        self.dtb_ih_games = dtb_ih_games
        self.dtb_players = dtb_players

    def get_date(self):
        """Vygeneruje dnešní datum a po odečtu vrátí včerejší"""
        today = datetime.today()
        yesterday_date_only = today.date() - timedelta(days=1)
        return yesterday_date_only

    def get_schedule_url(self, yesterday_date_only, league_url_source):
        """Spojením url + včerejšího data, vrátí url s výsledky včerejších zápasů + rozpis zápasů na 7 dní"""
        yesterday_game_sheet_url = urljoin(league_url_source, str(yesterday_date_only))
        return yesterday_game_sheet_url

    def url_content_downloader(self, url):
        """Zašleme požadavek na server zadané URL, vrátí se nám objekt response s několika atributy"""
        response = requests.get(url)
        data = response.json()  # pokud server vrátí obsah stránky ve formátu json, převedeme je na dictionary
        return data

    def todays_games(self, data, date):
        """Funkce která nám získá id her, které byly odehrány pouze za včerejšího data a vrátí nám je jako list"""
        game_ids = []
        for gameweek in data["gameWeek"]:
            if gameweek["date"] == str(date):
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
        game_list = []

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
            winner_team = self.get_winner(dtb_home_team, home_team_score, dtb_away_team, away_team_score)

            away_team_skaters_stats_list = self.player_stats_sheet(away_team_all_skaters, self.dtb_players,
                                                              dtb_away_team, season)
            away_team_goalies_stats_list = self.goalies_stats_sheet(away_team_goalies_stats, self.dtb_players,
                                                               dtb_away_team, season)

            home_team_skaters_stats_list = self.player_stats_sheet(home_team_all_skaters, self.dtb_players,
                                                              dtb_home_team, season)
            home_team_goalies_stats_list = self.goalies_stats_sheet(home_team_goalies_stats, self.dtb_players,
                                                               dtb_home_team, season)

            all_skaters_stats_list = away_team_skaters_stats_list + home_team_skaters_stats_list
            all_goalies_stats_list = away_team_goalies_stats_list + home_team_goalies_stats_list

            """Z daných údajů ze zápasu, vytvoří objekt podle třídy IhGames uloží ho do proměnné a přidá do listu"""
            new_game = ih_games.IhGames(dtb_home_team["team_id"], dtb_away_team["team_id"], home_team_score,
                                        away_team_score, result_type, dtb_home_team["league_id"],
                                        winner_team["team_id"], match_date, season, season_stage, web_game_id,
                                        all_skaters_stats_list, all_goalies_stats_list)
            game_list.append(new_game)

            # print(season_stage)
            # print(season)
            # print(match_date)
            # print(away_team_name)
            # print(away_team_score)
            # print(home_team_name)
            # print(home_team_score)
            # print(result_type)

        return game_list

    def get_winner(self, dtb_home_team, home_team_score, dtb_away_team, away_team_score):
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

    def goalies_stats_sheet(self, list_of_goalies, dtb_returned_players, dtb_team, season):
        goalies_stats_list = []
        # print(json.dumps(list_of_goalies, indent=4))
        for goalie in list_of_goalies:
            goalie_name = goalie["name"]["default"]
            goalie_toi = goalie["toi"]

            goalie_toi_transfered = self.time_transfer(goalie_toi)
            if goalie_toi == "00:00":
                player_id = self.get_player_id(goalie_name, dtb_returned_players)
                goalie_game_stats = goalie_game_sheet.GoalieGameSheet(player_id, goalie_toi_transfered,
                                                                      dtb_team["team_id"], season, 0, 0, 0.00, False)
                goalies_stats_list.append(goalie_game_stats)
            else:
                goalie_shots = goalie["shotsAgainst"]
                goalie_saves = goalie["saves"]
                goalie_save_percentage = goalie["savePctg"]

                player_id = self.get_player_id(goalie_name, dtb_returned_players)
                goalie_game_stats = goalie_game_sheet.GoalieGameSheet(player_id, goalie_toi_transfered, dtb_team["team_id"], season, goalie_shots, goalie_saves, goalie_save_percentage, True)
                goalies_stats_list.append(goalie_game_stats)
        return goalies_stats_list

    def player_stats_sheet(self, list_of_players, dtb_returned_players, dtb_team, season):
        players_stats_list = []
        for player in list_of_players:
            print(player)
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

            player_id = self.get_player_id(player_name, dtb_returned_players)
            player_pim_adjusted = self.time_transfer(player_pim)
            player_toi_adjusted = self.time_transfer(player_toi)

            player_stats = player_game_sheet.PlayerGameSheet(player_id, player_goals, player_assists, player_points,
                                                             player_plus_minus, player_pim_adjusted, player_sog,
                                                             player_hits, player_ppg, player_toi_adjusted,
                                                             player_faceoff, dtb_team["team_id"], player_blocked_shots,
                                                             season)
            players_stats_list.append(player_stats)

            print(player_name, player_goals, player_assists, player_points, player_plus_minus, player_pim_adjusted,
                  player_sog, player_hits, player_ppg, player_toi_adjusted, player_faceoff, player_blocked_shots)
        return players_stats_list

    def time_transfer(self, time):
        minutes = str(time)[:2]
        seconds = str(time)[3:]
        interval_format = f"{minutes}:{seconds:02}"
        print(interval_format)
        return interval_format

    def get_player_id(self, current_game_player, dtb_returned_players):
        for dtb_returned_player in dtb_returned_players:
            dtb_player = dtb_returned_player["surname"][:1] + ". " + dtb_returned_player["last_name"]
            dtb_player_diacriticsless = unidecode(dtb_player)
            if current_game_player == dtb_player_diacriticsless:
                return dtb_returned_player["player_id"]
        else:
            name_list = [dtb_returned_player["surname"][:1] + ". " + dtb_returned_player["last_name"] for
                         dtb_returned_player in dtb_returned_players]
            closest_match = get_close_matches(current_game_player, name_list, 1, 0.6)
            print(f"Hledám hráče v DTB {current_game_player}")
            print(f"Nejblížší shoda je: {closest_match}")
            for dtb_returned_player in dtb_returned_players:
                if dtb_returned_player["surname"][:1] + ". " + dtb_returned_player["last_name"] == closest_match[0]:
                    return dtb_returned_player["player_id"]
            else:
                print(f"Hráč: {current_game_player} stále nenalezen!")

    def downloader_manager(self):
        yesterday_date = self.get_date()
        schedule_url = self.get_schedule_url(yesterday_date, self.league_schedule_url)
        url_content = self.url_content_downloader(schedule_url)
        list_of_game_ids = self.todays_games(url_content, yesterday_date)
        if not list_of_game_ids:
            return False
        list_of_game_urls = self.url_maker_game_stats(list_of_game_ids)
        list_of_matchs_objects = self.game_result_sheet(list_of_game_urls)
        print(list_of_game_urls)
        print(list_of_matchs_objects)
        return list_of_matchs_objects