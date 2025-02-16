from fastapi import FastAPI
import  dtb_driver
import os
from dotenv import load_dotenv

app = FastAPI()

@app.get("/game_results")
def root():
    load_dotenv("dev.env")
    my_dtb = dtb_driver.DtbDriver(os.getenv("POSTGRES_LOCALHOST"), os.getenv("POSTGRES_DATABASE"), os.getenv("POSTGRES_USER"), os.getenv("POSTGRES_PASSWORD"))
    my_dtb.connection_maker()
    my_dtb.cursor_maker()

    returned_games_stats = my_dtb.get_full_game_info_on_optional_date("2024-12-23")

    list_of_players_stats = get_players_stats(returned_games_stats, my_dtb)

    my_dtb.dtb_disconnection()
    return list_of_players_stats

def get_players_stats(returned_games_stats, my_dtb):
    for game in returned_games_stats:
        returned_game_id = game["game_id"]
        home_team_id = game["home_team_id"]
        away_team_id = game["away_team_id"]
        dtb_returned_players_stats = my_dtb.get_player_game_stats(returned_game_id)

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