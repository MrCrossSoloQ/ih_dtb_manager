import os
from dotenv import load_dotenv
import data_downloader
import duplicity_checker
import nhl_game_stats_downloader
import dtb_driver
from data_downloader import PlaywrightController
import ahl_game_stats_downloader


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

            if user_choice < 0 or user_choice > 4:
                print("Zadaná hodnota se nenachází v nabídce!")

            elif user_choice == 1:
                inner_choice = league_choice(user_choice, my_dtb_driver)
                if inner_choice == "R":
                    continue

                dtb_returned_leagues = my_dtb_driver.get_data_simple("leagues")

                dtb_league_data_object = data_downloader.PlaywrightController(dtb_returned_leagues)
                dtb_league_data_object.playwright_starter()
                scraped_teams = dtb_league_data_object.get_url("league", inner_choice)
                dtb_league_data_object.playwright_termination()

                dtb_teams = my_dtb_driver.get_data_simple("teams")

                teams_duplicity_object = duplicity_checker.DuplicityChecker(dtb_teams, scraped_teams, my_dtb_driver)
                teams_duplicity_object.dtb_duplicity_check()

            elif user_choice == 2:
                inner_choice = league_choice(user_choice, my_dtb_driver)
                if inner_choice == "R":
                    continue

                dtb_returned_teams = my_dtb_driver.get_data_simple("teams")

                dtb_teams_data_object = PlaywrightController(dtb_returned_teams)
                dtb_teams_data_object.playwright_starter()
                scraped_players = dtb_teams_data_object.get_url("team_roster", inner_choice)
                dtb_teams_data_object.playwright_termination()

                dtb_returned_players = my_dtb_driver.get_data_simple("players")
                players_duplicity_object = duplicity_checker.DuplicityChecker(dtb_returned_players, scraped_players, my_dtb_driver)
                players_duplicity_object.dtb_duplicity_check("players")

            elif user_choice ==3:
                inner_choice = league_choice(user_choice, my_dtb_driver) #volba č. 2,3 zatím nedodělána
                if inner_choice == "R":
                    continue

                elif inner_choice == 1:
                    dtb_returned_leagues = my_dtb_driver.get_data_simple("leagues")
                    nhl_league_schedule_url = dtb_returned_leagues[0]["schedule_url_source"]
                    print(nhl_league_schedule_url)
                    dtb_returned_teams = my_dtb_driver.get_data_on_simple_condition("teams", "league_id", 1)
                    dtb_returned_games = my_dtb_driver.get_data_on_simple_condition("ih_games", "league_id", 1)

                    downloader_controller = data_downloader.PlaywrightController()
                    nhl = nhl_game_stats_downloader.NhlGameDownloader(dtb_returned_teams, dtb_returned_games, my_dtb_driver, downloader_controller, nhl_league_schedule_url)
                    scraped_games = nhl.downloader_manager()
                    print(scraped_games)

                    if scraped_games is False:
                        print("Tento den se neodehrály žádné zápasy!")

                    else:
                        nhl_duplicity = duplicity_checker.DuplicityChecker(dtb_returned_games, scraped_games, my_dtb_driver)
                        nhl_duplicity.dtb_game_duplicity_check()

                        dtb_returned_games = my_dtb_driver.get_data_simple("ih_games")
                        dtb_returned_players_game_sheet = my_dtb_driver.get_data_simple("player_game_sheet")
                        dtb_returned_goalies_game_sheet = my_dtb_driver.get_data_simple("goalie_game_sheet")

                        p_duplicity_object = duplicity_checker.GameSheetDuplicityChecker(dtb_returned_players_game_sheet, dtb_returned_games, scraped_games, my_dtb_driver)
                        p_duplicity_object.dtb_duplicity_game_sheet_check("player_game_sheet")

                        goalies_duplicity_object = duplicity_checker.GameSheetDuplicityChecker(dtb_returned_goalies_game_sheet, dtb_returned_games, scraped_games, my_dtb_driver)
                        goalies_duplicity_object.dtb_duplicity_game_sheet_check("goalie_game_sheet")

                elif inner_choice == 2:

                    dtb_returned_leagues = my_dtb_driver.get_data_simple("leagues")
                    last_game_url = dtb_returned_leagues[1]["schedule_url_source"]
                    dtb_returned_teams = my_dtb_driver.get_data_on_simple_condition("teams", "league_id", 2)
                    dtb_returned_games = my_dtb_driver.get_data_on_simple_condition("ih_games", "league_id", 2)

                    downloader_controller = data_downloader.PlaywrightController()
                    ahl = ahl_game_stats_downloader.AhlGameDownloader(last_game_url, dtb_returned_teams, dtb_returned_games, my_dtb_driver, downloader_controller)

                    scraped_ahl_games = ahl.ahl_game_manager()
                    print(f"Stažené AHL hry: {scraped_ahl_games}")

                    if scraped_ahl_games is False:
                        print("Tento den se neodehrály žádné zápasy!")

                    else:

                        ahl_duplicity = duplicity_checker.DuplicityChecker(dtb_returned_games, scraped_ahl_games, my_dtb_driver)
                        ahl_duplicity.dtb_game_duplicity_check()

                        dtb_returned_games = my_dtb_driver.get_data_simple("ih_games")
                        dtb_returned_players_game_sheet = my_dtb_driver.get_data_simple("player_game_sheet")
                        dtb_returned_goalies_game_sheet = my_dtb_driver.get_data_simple("goalie_game_sheet")

                        p_duplicity = duplicity_checker.GameSheetDuplicityChecker(dtb_returned_players_game_sheet, dtb_returned_games, scraped_ahl_games, my_dtb_driver)
                        p_duplicity.dtb_duplicity_game_sheet_check("player_game_sheet")

                        goalies_duplicity_object = duplicity_checker.GameSheetDuplicityChecker(dtb_returned_goalies_game_sheet, dtb_returned_games, scraped_ahl_games, my_dtb_driver)
                        goalies_duplicity_object.dtb_duplicity_game_sheet_check("goalie_game_sheet")

            elif user_choice == 4:
                """Volba č. 4 pouze pro testování"""
                dtb_returned_player = my_dtb_driver.get_data_on_simple_condition("players", "elite_url", "https://www.eliteprospects.com/player/237071/martin-necas")
                if not dtb_returned_player:
                    print("NIC SE NEVRÁTILO")
                print(dtb_returned_player)
                print(dtb_returned_player[0]["last_name"])

            elif user_choice == 0:
                print("Neplecha ukončena!")
                break

        except ValueError:
            print("Zadat můžeš pouze číslo!")

if __name__ == "__main__":
    load_dotenv("dev.env")
    my_dtb_controller = dtb_driver.DtbDriver(os.getenv("POSTGRES_LOCALHOST", "host.docker.internal"), os.getenv("POSTGRES_DATABASE"), os.getenv("POSTGRES_USER"), os.getenv("POSTGRES_PASSWORD"))

    main_menu(my_dtb_controller)

    my_dtb_controller.dtb_disconnection()