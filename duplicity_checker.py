class DuplicityChecker:
    def __init__(self, dtb_data, scraped_data, my_dtb_driver):
        self.dtb_data = dtb_data
        self.scraped_data = scraped_data
        self.my_dtb_driver = my_dtb_driver

    """Metoda, která nám ověří, zda již je zápas s výsledkem uložený v dtb, podle unikátního čísla web_game_id"""
    def dtb_game_duplicity_check(self):
        web_game_id_list = [dtb_item["web_game_id"] for dtb_item in self.dtb_data]
        for scraped_data_item in self.scraped_data:
            if scraped_data_item.web_game_id not in web_game_id_list:
                self.dtb_insert_game_result("ih_games", scraped_data_item)
            else:
                print(f"Hra: {scraped_data_item.web_game_id}, se již nachází v DTB!")

    """V případě, že se DTB nachází hráč, který byl znovu stažený z webu, dojde k ověření, zda tým ve kterém hraje je aktuální."""
    def data_correctness_check(self, scraped_data_item):
        dtb_player_stats = self.my_dtb_driver.get_data_join_condition_results("players","teams","team_id","team_name","team_id","elite_url", scraped_data_item.url)
        for player in dtb_player_stats:
            if player["team_id"] != scraped_data_item.team_id:
                self.my_dtb_driver.update_data("players", "team_id", scraped_data_item.team_id,"player_id", player["player_id"])
                print(f"Data hráče: {player['surname']}{player['last_name']} aktualizována!")


    """Metoda, která nám ověři, zda se stažená položka již nenachází v DTB, aby nebyla přidána znovu. Ověření probíhá, dle URL adresy"""
    def dtb_duplicity_check(self, table = None):
        """Vytvoří nám list všech url adres z tabulky v DTB, kterou ověřujeme"""
        dtb_items = [dtb_item["elite_url"] for dtb_item in self.dtb_data]

        """Cyklus následně prochází jednotlivé stažené url adresy a porovnává je s url v DTB"""
        for scraped_data_item in self.scraped_data:
            """V případě, že se URL v DTB nenachází, vrátí nám vytvořený objekt, ze stažených dat"""
            if scraped_data_item.url not in dtb_items and table == "teams":
                self.my_dtb_driver.insert_data("teams", ["team_name", "league_id", "elite_url"],[scraped_data_item.team_name, scraped_data_item.league_id,scraped_data_item.url])

            elif scraped_data_item.url not in dtb_items and table == "players":
                print(f"Do databáze přidána položka: {scraped_data_item.surname} {scraped_data_item.last_name} {scraped_data_item.nationality} {scraped_data_item.league_id} {scraped_data_item.player_position} {scraped_data_item.date_of_birth} {scraped_data_item.team_id} {scraped_data_item.url}")
                self.my_dtb_driver.insert_data("players", ["surname", "last_name", "nationality", "league_id", "player_position", "date_of_birth", "team_id", "elite_url"],[scraped_data_item.surname, scraped_data_item.last_name, scraped_data_item.nationality, scraped_data_item.league_id, scraped_data_item.player_position, scraped_data_item.date_of_birth, scraped_data_item.team_id, scraped_data_item.url])

            elif scraped_data_item.url in dtb_items and table == "players":
                self.data_correctness_check(scraped_data_item)

            else:
                print(f"V DTB se url adresa: {scraped_data_item.url} NACHÁZÍ")

    def dtb_insert_game_result(self, choosen_table, scraped_data_item):
        self.my_dtb_driver.insert_data(choosen_table,["home_team_id", "away_team_id", "home_score", "away_score", "result_type", "league_id", "winner_team_id", "match_date", "season", "season_stage", "web_game_id"],
                                [scraped_data_item.home_team_id, scraped_data_item.away_team_id, scraped_data_item.home_score, scraped_data_item.away_score, scraped_data_item.result_type, scraped_data_item.league_id, scraped_data_item.winner_team_id, scraped_data_item.match_date, scraped_data_item.season, scraped_data_item.season_stage, scraped_data_item.web_game_id])

class GameSheetDuplicityChecker(DuplicityChecker):
    def __init__(self, dtb_data, dtb_returned_games, scraped_data, my_dtb_driver):
        super().__init__(dtb_data, scraped_data, my_dtb_driver)
        self.dtb_returned_games = dtb_returned_games

    def get_dtb_game_id(self, scraped_game):
        for dtb_game in self.dtb_returned_games:
            if dtb_game["web_game_id"] == scraped_game.web_game_id:
                return dtb_game["game_id"]

    def dtb_duplicity_game_sheet_check(self, position):
        dtb_players_id = [dtb_id["player_id"] for dtb_id in self.dtb_data]
        dtb_games_id = [dtb_id["game_id"] for dtb_id in self.dtb_data]
        for scraped_item in self.scraped_data:
            scraped_game_id = self.get_dtb_game_id(scraped_item)
            if position == "player":
                for scraped_player_stats in scraped_item.players_stats_list:
                    if scraped_player_stats.player_id not in dtb_players_id and scraped_game_id not in dtb_games_id:
                        self.dtb_insert_player_stats(scraped_player_stats, "player_game_sheet", scraped_game_id)
                    else:
                        print(f"Staty hráče: {scraped_player_stats.player_id} ve hře {scraped_item.web_game_id} již v DTB existují!")

            elif position == "goalie":
                for scraped_goalie_stats in scraped_item.goalies_stats_list:
                    if scraped_goalie_stats.player_id not in dtb_players_id and scraped_game_id not in dtb_games_id:
                        self.dtb_insert_goalie_stats(scraped_goalie_stats, "goalie_game_sheet", scraped_game_id)
                    else:
                        print(f"Staty hráče: {scraped_goalie_stats.player_id} ve hře {scraped_item.web_game_id} již v DTB existují!")


    def dtb_insert_player_stats(self, scraped_player_stats, choosen_table, scraped_game_id):
        self.my_dtb_driver.insert_data(choosen_table, ["game_id", "player_id", "goals", "assists", "points", "plus_minus", "pim", "sog", "hits", "ppg", "toi", "face_off_percentage", "team_id", "blocked_shots", "season"],
                                [scraped_game_id, scraped_player_stats.player_id, scraped_player_stats.goals, scraped_player_stats.assists, scraped_player_stats.points, scraped_player_stats.plus_minus, scraped_player_stats.pim, scraped_player_stats.sog, scraped_player_stats.hits, scraped_player_stats.ppg, scraped_player_stats.toi, scraped_player_stats.face_off_percentage, scraped_player_stats.team_id, scraped_player_stats.player_blocked_shots, scraped_player_stats.season])

    def dtb_insert_goalie_stats(self, scraped_goalie_stats, choosen_table, scraped_game_id):
        self.my_dtb_driver.insert_data(choosen_table,["game_id", "player_id", "shots", "saves", "save_percentage", "toi", "team_id", "season", "has_played"],
                                [scraped_game_id, scraped_goalie_stats.player_id, scraped_goalie_stats.shots, scraped_goalie_stats.saves, scraped_goalie_stats.save_percentage, scraped_goalie_stats.toi, scraped_goalie_stats.team_id, scraped_goalie_stats.season, scraped_goalie_stats.has_played])