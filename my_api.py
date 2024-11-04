from fastapi import FastAPI
from main import dtb_connection, dtb_cursor, close_connection
from sql_queries import get_full_game_info_on_optional_date

app = FastAPI()

@app.get("/")
def root():
    my_con = dtb_connection()
    my_cur = dtb_cursor(my_con)
    retured_games = get_full_game_info_on_optional_date(my_cur,"2024-11-03")
    close_connection(my_con, my_cur)
    transfered_data = [dict(row) for row in retured_games]
    return transfered_data

