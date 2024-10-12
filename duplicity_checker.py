import sql_queries
import const

class DuplicityChecker:
    def __init__(self, dtb_data, scraped_data, my_con = None, my_cur = None):
        self.dtb_data = dtb_data
        self.scraped_data = scraped_data
        self.my_con = my_con
        self.my_cur = my_cur

    """V případě, že se DTB nachází hráč, který byl znovu stažený z webu, dojde k ověření, zda tým ve kterém hraje je aktuální."""
    def data_correctness_check(self, scraped_data_item):
        dtb_player_stats = sql_queries.get_data_join_condition_results(self.my_cur, "players","teams","team_id","team_name","team_id","elite_url", scraped_data_item.url)
        for player in dtb_player_stats:
            if player["team_id"] != scraped_data_item.team_id:
                sql_queries.update_data(self.my_con, self.my_cur, "players","team_id",scraped_data_item.team_id,"player_id", player["player_id"])
                print(f"Data hráče: {player['surname']}{player['last_name']} aktualizována!")


    """Metoda, která nám ověři, zda se stažená položka již nenachází v DTB, aby nebyla přidána znovu. Ověření probíhá, dle URL adresy"""
    def dtb_duplicity_check(self, table = None):
        """Vytvoří nám list všech url adres z tabulky v DTB, kterou ověřujeme"""
        dtb_items = [dtb_item["elite_url"] for dtb_item in self.dtb_data]

        """Cyklus následně prochází jednotlivé stažené url adresy a porovnává je s url v DTB"""
        for scraped_data_item in self.scraped_data:
            """V případě, že se URL v DTB nenachází, vrátí nám vytvořený objekt, ze stažených dat"""
            if scraped_data_item.url not in dtb_items and table == "teams":
                sql_queries.insert_data(self.my_con, self.my_cur, "teams", ["team_name", "league_id", "elite_url"],[scraped_data_item.team_name, scraped_data_item.league_id,scraped_data_item.url])

            elif scraped_data_item.url not in dtb_items and table == "players":
                sql_queries.insert_data(self.my_con, self.my_cur, "players", ["surname", "last_name", "nationality", "league_id", "player_position", "date_of_birth", "team_id", "elite_url"],[scraped_data_item.surname, scraped_data_item.last_name, scraped_data_item.nationality, scraped_data_item.league_id, scraped_data_item.player_position, scraped_data_item.date_of_birth, scraped_data_item.team_id, scraped_data_item.url])

            elif scraped_data_item.url in dtb_items and table == "players":
                self.data_correctness_check(scraped_data_item)

            else:
                print(f"V DTB se url adresa: {scraped_data_item.url} NACHÁZÍ")

class GameDuplicityChecker(DuplicityChecker):
    def __init__(self, dtb_data, scraped_data, my_con = None, my_cur = None):
        super().__init__(dtb_data, scraped_data, my_con, my_cur)

    def dtb_duplicity_check(self):
        web_game_id_list = [dtb_item["web_game_id"] for dtb_item in self.dtb_data]
        for scraped_data_item in self.scraped_data:
            if scraped_data_item.web_game_id not in web_game_id_list:
                sql_queries.insert_data(self.my_con, self.my_cur, const.IH_GAMES, ["home_team_id", "away_team_id", "home_score", "away_score", "result_type", "league_id", "winner_team_id", "match_date", "season", "season_stage", "web_game_id"], [scraped_data_item.home_team_id, scraped_data_item.away_team_id, scraped_data_item.home_score, scraped_data_item.away_score, scraped_data_item.result_type, scraped_data_item.league_id, scraped_data_item.winner_team_id, scraped_data_item.match_date, scraped_data_item.season, scraped_data_item.season_stage, scraped_data_item.web_game_id])
            else:
                print(f"Hra: {scraped_data_item.web_game_id}, se již nachází v DTB!")