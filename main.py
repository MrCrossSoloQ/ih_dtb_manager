import psycopg2.extras
import os
from dotenv import load_dotenv
import sql_queries
import data_downloader
import teams

def data_correct_check(my_con,my_cur, scraped_data):
    """Dotaz, který nám vrátí výsledky z databáze u všech hráčů společně s jejich týmem"""
    dtb_players=sql_queries.get_data_join_condition_results(my_cur,"players","teams","team_id","team_name","team_id","elite_url",scraped_data.url)
    for dtb_player in dtb_players:
        if dtb_player["team_id"] != scraped_data.team_id:
            sql_queries.update_data(my_con,my_cur,"players","team_id",scraped_data.team_id,"player_id",dtb_player["player_id"])
            print(f"Neaktualizovaný hráč: {dtb_player}")
            print(f"Aktuální data z webu: {scraped_data.last_name, scraped_data.team_id}")


"""Funkce, která nám zjistí, zda se tým nalezený na stránce(webscrapovaný tým), již nenachází v databází, pokud ne, vloží se do dtb."""
def duplicity_check(my_cur, my_con, scraped_data, dtb_data, table):
    for item in scraped_data:
        parity_result = any(item.url == dtb_item["elite_url"] for dtb_item in dtb_data)

        if parity_result is False and table == "teams":
            sql_queries.insert_data(my_con, my_cur, "teams", ["team_name", "league_id", "elite_url"],
                                    [item.team_name, item.league_id, item.team_ulr])
        elif parity_result is False and table == "players":
            sql_queries.insert_data(my_con, my_cur, "players", ["surname", "last_name", "nationality", "league_id", "player_position", "date_of_birth", "team_id", "elite_url"],
                                    [item.surname, item.last_name, item.nationality, item.league_id, item.player_position, item.date_of_birth, item.team_id, item.url])
            """Pokud se položka(elite_url) bude již nacházet v dtb a zároveň půjde o tabulku players, zavolá se funkce, která ověří, zda je hodnota(aktuální tým hráče) v DTB aktuální"""
        elif parity_result is True and table == "players":
            data_correct_check(my_con,my_cur,item)
            # dtb_players=sql_queries.get_data(my_cur,"players", "teams", ["players.*", "teams.team_name"],["players.team_id"], ["teams.team_id"])
            # print(dtb_players)
        else:
            print(f"Databáze již obsahuje položku: {item.url}")

def main_menu(my_con, my_cur):
    print("Správa databáze")
    print("[1] - Stažení/Aktualizace týmů v databázi: ")
    print("[2] - Stažení hráčů, do databáze: ")
    user_choice = int(input("Vyber následující hodnotu z nabídky: "))
    if user_choice == 1:
        dtb_returned_leagues = sql_queries.get_data_simple(my_cur, choosen_table="leagues")

        scraped_teams = data_downloader.teams_download(dtb_returned_leagues)
        dtb_teams = sql_queries.get_data_simple(my_cur, choosen_table="teams")

        duplicity_check(my_cur, my_con, scraped_teams, dtb_teams, "teams")

    elif user_choice == 2:
        dtb_returned_leagues = sql_queries.get_data_simple(my_cur, choosen_table="leagues")
        dtb_returned_teams = sql_queries.get_data_simple(my_cur, choosen_table="teams")

        for leagues in dtb_returned_leagues:
            print(f'[{leagues["league_id"]}] - {leagues["league_short_cut"]}')
        print("[0] - Stáhnout hráče, ze všech lig")
        p_menu = int(input("Vyber hodnotu z nabídky: "))


        scraped_players = data_downloader.players_url_download(dtb_returned_teams, p_menu)
        dtb_returned_players = sql_queries.get_data_simple(my_cur, choosen_table="players")
        duplicity_check(my_cur, my_con, scraped_players, dtb_returned_players, "players")


if __name__ == "__main__":
    load_dotenv("dev.env")

    with psycopg2.connect(
        host = os.getenv("POSTGRES_LOCALHOST"),
        database = os.getenv("POSTGRES_DATABASE"),
        user = os.getenv("POSTGRES_USER"),
        password = os.getenv("POSTGRES_PASSWORD"),

    ) as my_con, my_con.cursor(cursor_factory = psycopg2.extras.DictCursor) as my_cur:
        main_menu(my_con, my_cur)

