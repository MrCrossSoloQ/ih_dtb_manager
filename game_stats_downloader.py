import requests
from urllib.parse import urljoin
import json
from datetime import datetime, timedelta
import ih_games

def get_date():
    today = datetime.today()
    yesterday_date_only = today.date() - timedelta(days=1)
    return yesterday_date_only

def get_schedule_url(yesterday_date_only, league_url_source):
    yesterday_game_sheet_url = urljoin(league_url_source, str(yesterday_date_only))
    return yesterday_game_sheet_url

def url_content_downloader(url):
    response = requests.get(url)
    data = response.json()
    return data

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

def game_result_sheet(game_urls, dtb_returned_teams):
    game_list = []
    for game_url in game_urls:
        downloaded_content = url_content_downloader(game_url)
        # print(json.dumps(downloaded_content, indent=4))

        home_team_name = downloaded_content["homeTeam"]["placeName"]["default"] + " " + downloaded_content["homeTeam"]["name"]["default"]
        home_team_score = downloaded_content["homeTeam"]["score"]
        away_team_name = downloaded_content["awayTeam"]["placeName"]["default"] + " " + downloaded_content["awayTeam"]["name"]["default"]
        away_team_score = downloaded_content["awayTeam"]["score"]
        result_type = downloaded_content["periodDescriptor"]["periodType"]
        season = downloaded_content["season"]
        game_type = downloaded_content["gameType"] #na nhl.com tím určují o jaký zápas v sezoně se jedná (1 - preseason, 2 - season, 3 - playoff)
        match_date = downloaded_content["gameDate"]
        web_game_id = downloaded_content["id"]

        print("---------------------------------------------------------------")
        dtb_home_team = dtb_team_searcher(home_team_name, dtb_returned_teams)
        dtb_away_team = dtb_team_searcher(away_team_name, dtb_returned_teams)
        season_stage = get_season_stage(game_type)
        winner_team = get_winner(dtb_home_team, home_team_score, dtb_away_team, away_team_score)

        new_game = ih_games.IhGames(dtb_home_team["team_id"], dtb_away_team["team_id"], home_team_score, away_team_score, result_type, dtb_home_team["league_id"], winner_team["team_id"], match_date, season, season_stage, web_game_id)
        game_list.append(new_game)

        print(season_stage)
        print(season)
        print(match_date)
        print(away_team_name)
        print(away_team_score)
        print(home_team_name)
        print(home_team_score)
        print(result_type)

        return game_list

"""Not done yet"""
def get_winner(dtb_home_team, home_team_score, dtb_away_team, away_team_score):
    if home_team_score > away_team_score:
        return dtb_home_team
    else:
        return dtb_away_team

"""Funkce, která zjistí, o jaký zápas v sezoně se jedná: preseason/season/playoff"""
def get_season_stage(game_type):
    if game_type == 1:
        return "preseason"
    elif game_type == 2:
        return "season"
    elif game_type == 3:
        return "playoff"

"""Funkce, do které pošleme název týmu ze zápasu a podle jeho názvu hledá shodu s týmem, který byl vrácen z DTB, když najde vrátí ho"""
def dtb_team_searcher(team_name, dtb_returned_teams):
    for dtb_team in dtb_returned_teams:
        if dtb_team["team_name"] == team_name:
            print(dtb_team)
            print(f"Index teamu v listu je: {dtb_returned_teams.index(dtb_team)}")
            return dtb_team

def downloader_manager(url_source, dtb_returned_teams):
    yesterday_date = get_date()
    schedule_url = get_schedule_url(yesterday_date, url_source)
    url_content = url_content_downloader(schedule_url)
    list_of_game_ids = todays_games(url_content, yesterday_date)
    list_of_game_urls = game_stats(list_of_game_ids)
    list_of_match_objects = game_result_sheet(list_of_game_urls, dtb_returned_teams)
    print(list_of_game_urls)
    return list_of_match_objects


# game_result = url_content_downloader(list_of_game_urls[-3])
# print(json.dumps(game_result, indent=4))
# print(json.dumps(game_result["playerByGameStats"]["awayTeam"], indent=4))
# player_stats()
