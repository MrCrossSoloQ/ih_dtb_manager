import requests
from urllib.parse import urljoin
import json
from datetime import datetime, timedelta

def get_date():
    today = datetime.today()
    yesterday_date_only = today.date() - timedelta(days=1)
    return yesterday_date_only

def get_schedule_url(yesterday_date_only):
    yesterday_game_sheet_url = urljoin("https://api-web.nhle.com/v1/schedule/", str(yesterday_date_only))
    return yesterday_game_sheet_url

def url_content_downloader(url):
    response = requests.get(url)
    data = response.json()
    return data

# print(json.dumps(data, indent=4))
def todays_games(data, date):
    game_ids = []
    for gameweek in data["gameWeek"]:
        if gameweek["date"] == str(date):
            for game in gameweek["games"]:
                game_ids.append(game["id"])

    print(game_ids)
    return game_ids

def game_stats(game_ids):
    list_of_game_urls = []
    for game_id in game_ids:
        game_stats_url = urljoin("https://api-web.nhle.com/v1/gamecenter/", str(game_id) + "/boxscore/")
        list_of_game_urls.append(game_stats_url)
    return list_of_game_urls

# def player_stats():
#     for player_stats in game_result["playerByGameStats"]["awayTeam"]["defense"]:
#         print(player_stats["name"]['default'])

def game_result_sheet(game_urls):
    for game_url in game_urls:
        downloaded_content = url_content_downloader(game_url)
    # print(json.dumps(downloaded_content, indent=4))

        home_team_name = downloaded_content["homeTeam"]["placeName"]["default"] + " " + downloaded_content["homeTeam"]["name"]["default"]
        home_team_score = downloaded_content["homeTeam"]["score"]
        away_team_name = downloaded_content["awayTeam"]["placeName"]["default"] + " " + downloaded_content["awayTeam"]["name"]["default"]
        away_team_score = downloaded_content["awayTeam"]["score"]
        result_type = downloaded_content["periodDescriptor"]["periodType"]
        season = downloaded_content["season"]
        game_played = downloaded_content["gameDate"]
        print(season)
        print(game_played)
        print(away_team_name)
        print(away_team_score)
        print(home_team_name)
        print(home_team_score)
        print(result_type)

yesterday_date = get_date()
schedule_url = get_schedule_url(yesterday_date)
url_content = url_content_downloader(schedule_url)
list_of_game_ids = todays_games(url_content, yesterday_date)
list_of_game_urls = game_stats(list_of_game_ids)
game_result_sheet(list_of_game_urls)
print(list_of_game_urls)


# game_result = url_content_downloader(list_of_game_urls[-3])
# print(json.dumps(game_result, indent=4))
# print(json.dumps(game_result["playerByGameStats"]["awayTeam"], indent=4))
# player_stats()
