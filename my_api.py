from fastapi import FastAPI
import  dtb_driver
import os
from dotenv import load_dotenv

app = FastAPI()

def create_dtb_driver():
    load_dotenv("dev.env")
    my_dtb_controller = dtb_driver.DtbDriver(os.getenv("POSTGRES_LOCALHOST"), os.getenv("POSTGRES_DATABASE"), os.getenv("POSTGRES_USER"), os.getenv("POSTGRES_PASSWORD"))
    return my_dtb_controller

@app.get("/game_results")
async def games_search(game_date: str = None, league_id_value: int = None):
    """Funkce, která vrátí z DTB výsledky zápasů, na základě zadaného data a ID ligy"""
    my_dtb_controller = create_dtb_driver()
    returned_games_stats = my_dtb_controller.get_full_game_info_on_optional_date(game_date, league_id_value)

    list_of_players_stats = get_players_stats(returned_games_stats, my_dtb_controller)

    return list_of_players_stats

def get_players_stats(returned_games_stats, my_dtb_controller):
    for game in returned_games_stats:
        returned_game_id = game["game_id"]
        home_team_id = game["home_team_id"]
        away_team_id = game["away_team_id"]
        dtb_returned_players_stats = my_dtb_controller.get_player_game_stats(returned_game_id)

        home_team_lineup = []
        away_team_lineup = []
        for dtb_returned_player_stats in dtb_returned_players_stats:
            if dtb_returned_player_stats["team_id"] == home_team_id:
                home_team_lineup.append(dtb_returned_player_stats)
            elif dtb_returned_player_stats["team_id"] == away_team_id:
                away_team_lineup.append(dtb_returned_player_stats)
        game["home_team_lineup"] = home_team_lineup
        game["away_team_lineup"] = away_team_lineup

    return returned_games_stats