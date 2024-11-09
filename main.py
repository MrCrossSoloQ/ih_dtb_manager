import os
from dotenv import load_dotenv
import data_downloader
import duplicity_checker
import game_stats_downloader
import dtb_driver

def league_choice(user_choice, my_dtb_driver):
    while True:
        dtb_returned_leagues = my_dtb_driver.get_data_simple("leagues")
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

def main_menu(my_dtb_driver):
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
                inner_choice = league_choice(user_choice, my_dtb_driver)
                if inner_choice == "R":
                    continue
                dtb_returned_leagues = my_dtb_driver.get_data_simple("leagues")
                scraped_teams = data_downloader.teams_download(dtb_returned_leagues, inner_choice)
                dtb_teams = my_dtb_driver.get_data_simple("teams")

                teams_duplicity_object = duplicity_checker.DuplicityChecker(dtb_teams, scraped_teams, my_dtb_driver)
                teams_duplicity_object.dtb_duplicity_check()

            elif user_choice == 2:
                """Z důvodu testování, je data_downloander nastaven pouze na stahování hráčů z týmu s indexem 0 z NHL, aby mi to nestahovalo data 15min :) """
                inner_choice = league_choice(user_choice, my_dtb_driver)
                if inner_choice == "R":
                    continue

                dtb_returned_teams = my_dtb_driver.get_data_simple("teams")
                scraped_players = data_downloader.players_url_download(dtb_returned_teams, inner_choice)

                dtb_returned_players = my_dtb_driver.get_data_simple("players")
                players_duplicity_object = duplicity_checker.DuplicityChecker(dtb_returned_players, scraped_players, my_dtb_driver)
                players_duplicity_object.dtb_duplicity_check("players")

            elif user_choice ==3:
                inner_choice = league_choice(user_choice, my_dtb_driver) #Je jedno jestli zadáš 0,1,2 .. zatím
                if inner_choice == "R":
                    continue

                dtb_returned_leagues = my_dtb_driver.get_data_simple("leagues")
                dtb_returned_teams = my_dtb_driver.get_data_simple("teams")
                dtb_returned_games = my_dtb_driver.get_data_simple("ih_games")
                dtb_returned_players = my_dtb_driver.get_data_simple("players")

                scraped_games = game_stats_downloader.downloader_manager(dtb_returned_leagues[1]["schedule_url_source"], dtb_returned_teams, dtb_returned_games, dtb_returned_players) #dtb_returned_leagues[1] prozatím nastaveno na první index

                g_duplicity_object = duplicity_checker.DuplicityChecker(dtb_returned_games, scraped_games, my_dtb_driver)
                g_duplicity_object.dtb_game_duplicity_check()

                dtb_returned_games = my_dtb_driver.get_data_simple("ih_games")
                dtb_returned_players_game_sheet = my_dtb_driver.get_data_simple("player_game_sheet")
                dtb_returned_goalies_game_sheet = my_dtb_driver.get_data_simple("goalie_game_sheet")

                g_duplicity_object = duplicity_checker.GameSheetDuplicityChecker(dtb_returned_players_game_sheet, dtb_returned_goalies_game_sheet, dtb_returned_games, scraped_games, my_dtb_driver)
                g_duplicity_object.dtb_duplicity_game_sheet_check("player_game_sheet")
                g_duplicity_object.dtb_duplicity_game_sheet_check("goalie_game_sheet")

                dtb_returned_game_results = my_dtb_driver.get_full_game_info_on_optional_date("2024-11-08")
                print(dtb_returned_game_results)

            elif user_choice == 0:
                print("Neplecha ukončena!")
                break

        except ValueError:
            print("Zadat můžeš pouze číslo!")

if __name__ == "__main__":
    load_dotenv("dev.env")
    my_dtb_driver = dtb_driver.DtbDriver(os.getenv("POSTGRES_LOCALHOST"), os.getenv("POSTGRES_DATABASE"), os.getenv("POSTGRES_USER"), os.getenv("POSTGRES_PASSWORD"))
    my_dtb_driver.connection_maker()
    my_dtb_driver.cursor_maker()

    main_menu(my_dtb_driver)

    my_dtb_driver.dtb_disconnection()