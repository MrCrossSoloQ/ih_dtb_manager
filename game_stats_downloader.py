import requests
from urllib.parse import urljoin
import json
from datetime import datetime

# today = datetime.today()
# date_only = today.date()
# print(date_only)

date = "2024-04-02"

response = requests.get("https://api-web.nhle.com/v1/schedule/2024-04-02")
data = response.json()

# print(json.dumps(data, indent=4))
def todays_games(data):
    game_ids = []
    for gameweek in data["gameWeek"]:
        if gameweek["date"] == date:
            for game in gameweek["games"]:
                game_ids.append(game["id"])
                # game_result_url = urljoin("https://www.nhl.com/", game["gameCenterLink"])
                # game_results.append(game_result_url)

    print(game_ids)
    return game_ids

def game_stats(game_ids):
    for game_id in game_ids:
        game_stats_url = urljoin("https://api-web.nhle.com/v1/gamecenter/", str(game_id) + "/boxscore/")
        print(game_stats_url)

list_of_game_ids = todays_games(data)

game_stats(list_of_game_ids)