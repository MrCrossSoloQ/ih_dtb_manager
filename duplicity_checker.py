import sql_queries

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
            if scraped_data_item.url not in dtb_items:
                print(f"V DTB se url adresa: {scraped_data_item.url} NENACHÁZÍ")
                return scraped_data_item
            elif scraped_data_item.url in dtb_items and table == "players":
                self.data_correctness_check(scraped_data_item)
            else:
                print(f"V DTB se url adresa: {scraped_data_item.url} NACHÁZÍ")