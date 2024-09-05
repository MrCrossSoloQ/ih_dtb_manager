from random import choice

import psycopg2.extras
import os
from dotenv import load_dotenv, dotenv_values
import sql_queries
import data_downloader
import leagues

"""Funkce, která nám zjistí, zda se tým nalezený na stránce(webscrapovaný tým), již nenachází v databází, pokud ne, vloží se do dtb."""
def duplicity_check(my_cur, my_con, scraped_data, dtb_data, choice):
    for item in scraped_data:
        parity_result = any(item.url == dtb_item["elite_url"] for dtb_item in dtb_data)
        if parity_result is False and choice == 1:
            sql_queries.insert_data(my_con, my_cur, "teams", ["team_name", "league_id", "elite_url"],
                                    [item.team_name, item.league_id, item.team_ulr])
        elif parity_result is False and choice == 2:
            sql_queries.insert_data(my_con, my_cur, "players", ["surname", "last_name", "nationality", "league_id", "player_position", "date_of_birth", "team_id", "elite_url"],
                                    [item.surname, item.last_name, item.nationality, item.league_id, item.player_position, item.date_of_birth, item.team_id, item.url])
        else:
            print(f"Databáze již obsahuje položku: {item.url}")

def main_menu(my_con, my_cur):
    print("Správa databáze")
    print("[1] - Stažení/Aktualizace týmů v databázi: ")
    print("[2] - Zobrazí týmy z databáze: ")
    user_choice = int(input("Vyber následující hodnotu z nabídky: "))
    if user_choice == 1:
        dtb_returned_leagues = sql_queries.get_data(my_cur, choosen_table="leagues")

        scraped_teams = data_downloader.teams_download(dtb_returned_leagues)
        dtb_teams = sql_queries.get_data(my_cur, choosen_table="teams")
        duplicity_check(my_cur, my_con, scraped_teams, dtb_teams, 1)

    elif user_choice == 2:
        dtb_returned_teams = sql_queries.get_data(my_cur, choosen_table="teams")
        # for team in dtb_returned_teams:
        #     print(team["elite_url"])
        scraped_players = data_downloader.players_url_download(dtb_returned_teams)
        dtb_returned_players = sql_queries.get_data(my_cur, choosen_table="players")
        duplicity_check(my_cur, my_con, scraped_players, dtb_returned_players, 2)


if __name__ == "__main__":
    load_dotenv("dev.env")

    with psycopg2.connect(
        host = os.getenv("POSTGRES_LOCALHOST"),
        database = os.getenv("POSTGRES_DATABASE"),
        user = os.getenv("POSTGRES_USER"),
        password = os.getenv("POSTGRES_PASSWORD"),

    ) as my_con, my_con.cursor(cursor_factory = psycopg2.extras.DictCursor) as my_cur:
        main_menu(my_con, my_cur)

