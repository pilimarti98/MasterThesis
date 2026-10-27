import pandas as pd

from APICalls.helper import get_dates
from APICalls.weather_and_solar import historical_weather, simulate_pv
from APICalls.elering_market import get_market_price
from APICalls.consumption import convert_to_csv
from config.config import CONFIG

"""

Get all data unified into one dataframe for EDA in RStudio, 
in order to find relations between datasets.
These datasets will be linked by the timestamp, in UTC.

"""

def align_data_by_timestamp():
    """ Get all data unified by UTC timestamps """
    open_meteo_start, open_meteo_end = get_dates(offset=CONFIG["ENV"]["OFFSET"], timedelta=CONFIG["ENV"]["TIMEDELTA"], to_open_meteo=True)
    wx = historical_weather(start_date=open_meteo_start, end_date=open_meteo_end)
    pv_df = simulate_pv(wx)
    pv_df = pv_df.reset_index()

    start, end = get_dates(offset=CONFIG["ENV"]["OFFSET"], timedelta=CONFIG["ENV"]["TIMEDELTA"])
    price_df = get_market_price(start_date=start, end_date=end)
    consumption_df = convert_to_csv(start_meter=start, end_meter=end)

    dataframes = [price_df, consumption_df, pv_df]
    merged = pd.concat(
        [d.set_index('Timestamp') for d in dataframes],
        axis=1,
        join='inner'
    ).reset_index()
    merged.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/MasterThesisRStudio/Data/merged.csv")

if __name__ == "__main__":
    align_data_by_timestamp()