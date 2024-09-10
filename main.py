import psycopg2.extras
import os
from dotenv import load_dotenv
import sql_queries
import data_downloader
import duplicity_checker

def main_menu(my_con, my_cur):
    print("Správa databáze")
    print("[1] - Stažení/Aktualizace týmů v databázi: ")
    print("[2] - Stažení hráčů, do databáze: ")
    user_choice = int(input("Vyber následující hodnotu z nabídky: "))
    if user_choice == 1:
        dtb_returned_leagues = sql_queries.get_data_simple(my_cur, choosen_table="leagues")

        scraped_teams = data_downloader.teams_download(dtb_returned_leagues)
        dtb_teams = sql_queries.get_data_simple(my_cur, choosen_table="teams")

        teams_duplicity_object = duplicity_checker.DuplicityChecker(dtb_teams, scraped_teams)
        team_duplicity_result = teams_duplicity_object.dtb_duplicity_check()
        if team_duplicity_result is not None:
            sql_queries.insert_data(my_con, my_cur, "teams",["team_name", "league_id", "elite_url"], [team_duplicity_result.team_name, team_duplicity_result.league_id, team_duplicity_result.url])

    elif user_choice == 2:
        dtb_returned_leagues = sql_queries.get_data_simple(my_cur, choosen_table="leagues")
        dtb_returned_teams = sql_queries.get_data_simple(my_cur, choosen_table="teams")

        for leagues in dtb_returned_leagues:
            print(f'[{leagues["league_id"]}] - {leagues["league_short_cut"]}')
        print("[0] - Stáhnout hráče, ze všech lig")
        p_menu = int(input("Vyber hodnotu z nabídky: "))

        scraped_players = data_downloader.players_url_download(dtb_returned_teams, p_menu)

        dtb_returned_players = sql_queries.get_data_simple(my_cur, choosen_table="players")
        players_duplicity_object = duplicity_checker.DuplicityChecker(dtb_returned_players, scraped_players, my_con=my_con, my_cur = my_cur)
        p_duplicity_result = players_duplicity_object.dtb_duplicity_check(table="players")
        if p_duplicity_result is not None:
            sql_queries.insert_data(my_con, my_cur, "players", [p_duplicity_result.surname, p_duplicity_result.last_name, p_duplicity_result.nationality, p_duplicity_result.league_id, p_duplicity_result.player_position, p_duplicity_result.date_of_birth, p_duplicity_result.team_id, p_duplicity_result.url])

if __name__ == "__main__":
    load_dotenv("dev.env")

    with psycopg2.connect(
        host = os.getenv("POSTGRES_LOCALHOST"),
        database = os.getenv("POSTGRES_DATABASE"),
        user = os.getenv("POSTGRES_USER"),
        password = os.getenv("POSTGRES_PASSWORD"),

    ) as my_con, my_con.cursor(cursor_factory = psycopg2.extras.DictCursor) as my_cur:
        main_menu(my_con, my_cur)

