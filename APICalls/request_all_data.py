"""
NOT FUNCTIONAL YET
"""

from APICalls.helper import get_dates
from APICalls.pv_simulation import fetch_weather, simulate_pv
from APICalls.elering_market import get_market_price
from APICalls.consumption import convert_to_csv
from config.config import CONFIG

import logging

def get_all_data(start:str, end:str):
    """ Function to request all input data at once """

    # Modify data as Open Meteo requires a different date format
    open_meteo_start, open_meteo_end = get_dates(start=start, end=end, to_open_meteo=True)
    start, end = get_dates(start=start, end=end)
    wx = fetch_weather(start_date=open_meteo_start, end_date=open_meteo_end)
    simulate_pv(wx)
    logging.info("Requesting pv simulated generation data")
    get_market_price(start_date=start, end_date=end)
    logging.info("Requesting Nord Pool D-1 price data")
    convert_to_csv(start_meter=start, end_meter=end)
    logging.info("Requesting residential consumption data")

if __name__ == "__main__":
    start_date = CONFIG["ENV"]["START_DATE"]
    end_date = CONFIG["ENV"]["END_DATE"]
    get_all_data(start=start_date, end=end_date)