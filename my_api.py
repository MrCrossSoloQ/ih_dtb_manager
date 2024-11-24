from fastapi import FastAPI
import  dtb_driver
import os
from dotenv import load_dotenv

app = FastAPI()

@app.get("/")
def root():
    load_dotenv("dev.env")
    my_dtb = dtb_driver.DtbDriver(os.getenv("POSTGRES_LOCALHOST"), os.getenv("POSTGRES_DATABASE"), os.getenv("POSTGRES_USER"), os.getenv("POSTGRES_PASSWORD"))
    my_dtb.connection_maker()
    my_dtb.cursor_maker()
    returned_games_stats = my_dtb.get_full_game_info_on_optional_date("2024-11-22")
    transfered_data = [dict(row) for row in returned_games_stats]
    my_dtb.dtb_disconnection()
    return transfered_data