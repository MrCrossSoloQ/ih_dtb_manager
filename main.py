import psycopg2.extras
import os
from dotenv import load_dotenv
import sql_queries
import data_downloader
import duplicity_checker
import game_stats_downloader
import const

def league_choice(user_choice):
    while True:
        dtb_returned_leagues = sql_queries.get_data_simple(my_cur, choosen_table="leagues")
        id_list = ["R","0"]

        print("[R] - Zpět")
        for leagues in dtb_returned_leagues:
            id_list.append(str(leagues["league_id"]))
            print(f'[{leagues["league_id"]}] - {leagues["league_short_cut"]}')
        if user_choice == 1:
            print("[0] - Stáhnout týmy, ze všech lig")
            print("Vyber, ze které ligy, chceš aktualizovat/stáhnout týmy: ")
        elif user_choice == 2:
            print("[0] - Stáhnout hráče, ze všech lig")
            print("Vyber, ze které ligy, chceš aktualizovat/stáhnout data hráčů: ")
        elif user_choice ==3:
            print("[0] - Stáhnout výsledky zápasů, ze všech lig")
            print("Vyber, ze které ligy, chceš stáhnout výsledky zápasů: ")

        inner_menu = input("Vyber hodnotu z nabídky: ").upper()

        """V případě, že je zadaná hodnota mimo hodnoty z nabídky, cyklus se spustí znovu"""
        if inner_menu not in id_list:
            print("Vybrat můžeš pouze hodnoty z nabídky!")
            continue
        if inner_menu == "R":
            return "R"

        return int(inner_menu)

def main_menu(my_con, my_cur):
    while True:
        try:
            print("---------------------------------------------------")
            print("Správa databáze")
            print("[1] - Stažení/Aktualizace týmů v databázi ")
            print("[2] - Stažení hráčů, do databáze ")
            print("[3] - Stažení výsledků zápasů, do databáze ")
            print("[0] - Konec")
            user_choice = int(input("Vyber následující hodnotu z nabídky: "))

            if user_choice < 0 or user_choice > 3:
                print("Zadaná hodnota se nenachází v nabídce!")

            elif user_choice == 1:
                inner_choice = league_choice(user_choice)
                if inner_choice == "R":
                    continue

                dtb_returned_leagues = sql_queries.get_data_simple(my_cur, choosen_table="leagues")
                scraped_teams = data_downloader.teams_download(dtb_returned_leagues, inner_choice)
                dtb_teams = sql_queries.get_data_simple(my_cur, choosen_table="teams")

                teams_duplicity_object = duplicity_checker.DuplicityChecker(dtb_teams, scraped_teams)
                teams_duplicity_object.dtb_duplicity_check()

            elif user_choice == 2:
                """Z důvodu testování, je data_downloander nastaven pouze na stahování hráčů z týmu s indexem 0 z NHL, aby mi to nestahovalo data 15min :) """
                inner_choice = league_choice(user_choice)
                if inner_choice == "R":
                    continue

                dtb_returned_teams = sql_queries.get_data_simple(my_cur, choosen_table="teams")
                scraped_players = data_downloader.players_url_download(dtb_returned_teams, inner_choice)

                dtb_returned_players = sql_queries.get_data_simple(my_cur, choosen_table="players")
                players_duplicity_object = duplicity_checker.DuplicityChecker(dtb_returned_players, scraped_players, my_con=my_con, my_cur = my_cur)
                players_duplicity_object.dtb_duplicity_check(table="players")

            elif user_choice ==3:
                inner_choice = league_choice(user_choice) #Je jedno jestli zadáš 0,1,2 .. zatím
                if inner_choice == "R":
                    continue

                dtb_returned_leagues = sql_queries.get_data_simple(my_cur, "leagues")
                dtb_returned_teams = sql_queries.get_data_simple(my_cur, "teams")
                dtb_returned_games = sql_queries.get_data_simple(my_cur, "ih_games")
                dtb_returned_players = sql_queries.get_data_simple(my_cur, "players")

                scraped_games = game_stats_downloader.downloader_manager(dtb_returned_leagues[1]["schedule_url_source"], dtb_returned_teams, dtb_returned_games, dtb_returned_players) #dtb_returned_leagues[1] prozatím nastaveno na první index
                print(scraped_games)

                g_duplicity_object = duplicity_checker.DuplicityChecker(dtb_returned_games, scraped_games, my_con, my_cur)
                g_duplicity_object.dtb_game_duplicity_check()


                dtb_returned_games = sql_queries.get_data_simple(my_cur, "ih_games")
                dtb_returned_players_game_sheet = sql_queries.get_data_simple(my_cur, "player_game_sheet")
                dtb_returned_goalies_game_sheet = sql_queries.get_data_simple(my_cur, "goalie_game_sheet")

                g_duplicity_object = duplicity_checker.GameDuplicityChecker(dtb_returned_players_game_sheet, dtb_returned_goalies_game_sheet, dtb_returned_games, scraped_games, my_con, my_cur,)
                g_duplicity_object.dtb_duplicity_game_sheet_check("player_game_sheet", "player")
                g_duplicity_object.dtb_duplicity_game_sheet_check("goalie_game_sheet", "goalie")

            elif user_choice == 0:
                print("Neplecha ukončena!")
                break

        except ValueError:
            print("Zadat můžeš pouze číslo!")

if __name__ == "__main__":
    load_dotenv("dev.env")

    with psycopg2.connect(
        host = os.getenv("POSTGRES_LOCALHOST"),
        database = os.getenv("POSTGRES_DATABASE"),
        user = os.getenv("POSTGRES_USER"),
        password = os.getenv("POSTGRES_PASSWORD"),

    ) as my_con, my_con.cursor(cursor_factory = psycopg2.extras.DictCursor) as my_cur:
        main_menu(my_con, my_cur)