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
        print(id_list)
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
                team_duplicity_result = teams_duplicity_object.dtb_duplicity_check()
                if team_duplicity_result is not None:
                    sql_queries.insert_data(my_con, my_cur, "teams",["team_name", "league_id", "elite_url"], [team_duplicity_result.team_name, team_duplicity_result.league_id, team_duplicity_result.url])

            elif user_choice == 2:
                inner_choice = league_choice(user_choice)
                if inner_choice == "R":
                    continue

                dtb_returned_teams = sql_queries.get_data_simple(my_cur, choosen_table="teams")
                scraped_players = data_downloader.players_url_download(dtb_returned_teams, inner_choice)

                dtb_returned_players = sql_queries.get_data_simple(my_cur, choosen_table="players")
                players_duplicity_object = duplicity_checker.DuplicityChecker(dtb_returned_players, scraped_players, my_con=my_con, my_cur = my_cur)
                p_duplicity_result = players_duplicity_object.dtb_duplicity_check(table="players")
                if p_duplicity_result is not None:
                    sql_queries.insert_data(my_con, my_cur, "players", ["surname", "last_name", "nationality", "league_id", "player_position", "date_of_birth", "team_id", "elite_url"],[p_duplicity_result.surname, p_duplicity_result.last_name, p_duplicity_result.nationality, p_duplicity_result.league_id, p_duplicity_result.player_position, p_duplicity_result.date_of_birth, p_duplicity_result.team_id, p_duplicity_result.url])

            elif user_choice ==3:
                inner_choice = league_choice(user_choice)
                if inner_choice == "R":
                    continue

                dtb_returned_leagues = sql_queries.get_data_simple(my_cur, choosen_table="leagues")
                dtb_returned_teams = sql_queries.get_data_simple(my_cur, choosen_table="teams")

                scraped_games = game_stats_downloader.downloader_manager(dtb_returned_leagues[1][const.SCHEDULE_URL_SOURCE], dtb_returned_teams)

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