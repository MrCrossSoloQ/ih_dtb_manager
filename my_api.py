from fastapi import FastAPI
import  dtb_driver
import os
from dotenv import load_dotenv

# app = FastAPI()
#
# @app.get("/")
# def root():
#     my_con = dtb_connection()
#     my_cur = dtb_cursor(my_con)
#     retured_games = get_full_game_info_on_optional_date(my_cur,"2024-11-03")
#     close_connection(my_con, my_cur)
#     transfered_data = [dict(row) for row in retured_games]
#     return transfered_data

app = FastAPI()

@app.get("/")
def root():
    load_dotenv("dev.env")
    my_dtb = dtb_driver.DtbDriver(os.getenv("POSTGRES_LOCALHOST"), os.getenv("POSTGRES_DATABASE"),
                                  os.getenv("POSTGRES_USER"), os.getenv("POSTGRES_PASSWORD"))
    my_dtb.connection_maker()
    my_dtb.cursor_maker()
    returned_leagues = my_dtb.get_data_simple("leagues")
    my_dtb.dtb_disconnection()
    return returned_leagues