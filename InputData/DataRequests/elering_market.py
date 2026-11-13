import pandas as pd
import numpy as np

from InputData.helper.data_helper import get_dates, get_day_ahead
from InputData.helper.APIClient import Server, ApiClient
from InputData.helper.data_helper import turn_csv_str_into_df
from config.config import CONFIG

"""
Obtaining Nord Pool market price data for Estonia.
This data will be used for both the demand fee and the fee for selling surplus energy.
"""

def call_api(path: str, params: dict):
    """ Helper function to make a request from Baltic Transparency Dashboard"""
    server = Server(
        name='elering',
        base_url='https://dashboard.elering.ee'
    )
    api = ApiClient(server)

    response = api.request(
        method="GET",
        path=path,
        params=params
    )

    return response

def get_market_price(start_date: str, end_date:str, forecast:bool=False, save:bool=False):
    """ Request NordPool day-ahead price data in CSV file """

    path = "/api/nps/price/csv"
    parameters_price = {
        'start' : start_date,
        'end' : end_date,
        'fields' : 'ee'
    }
    price = call_api(path=path, params=parameters_price)

    if price:
        # Make necessary modifications to data
        df_price = turn_csv_str_into_df(price)
        df_price = df_price.drop(columns=['Ajatempel (UTC)'])
        df_price = df_price.rename(columns={'Kuupäev (Eesti aeg)': 'Timestamp', 'NPS Eesti': 'market_price(€/MWh)'})

        df_price["Timestamp"] = (pd.to_datetime(df_price["Timestamp"], dayfirst=True)
                                    .dt.tz_localize("Europe/Helsinki",
                                          ambiguous=np.full(len(df_price), False),   # treat ambiguous times as EET (UTC+2)
                                          nonexistent="shift_forward",
                                      )
                                    .dt.tz_convert("UTC"))

        df_price['market_price(€/MWh)'] = pd.to_numeric(df_price['market_price(€/MWh)'].str.replace(',','.'), errors='coerce')

        df_price = (
            df_price.set_index("Timestamp")
                    .resample('h')
                    .mean(numeric_only=True)
                    .reset_index()
        )
        start_date = pd.to_datetime(df_price['Timestamp'].iloc[0])
        year = str(start_date.year)
        month = str(start_date.month)
        df_price["Timestamp"] = df_price["Timestamp"].dt.strftime("%Y-%m-%dT%H:%MZ")
        df_price['market_price(€/MWh)'] = df_price['market_price(€/MWh)']/ 1000.0 # Convert the price variable to €/kWh
        df_price = df_price.rename(columns={'market_price(€/MWh)':'market_price(€/kWh)'})

        if save:
            if forecast:
                # Send csv to Data directory
                df_price.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/Market_Prices/{year}_{month}_forecast_market_price.csv")
                return df_price
            else:
                # Send csv to Data directory
                df_price.to_csv(
                    f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/Market_Prices/{year}_{month}_market_price.csv")
                return df_price
    else:
        raise ValueError("No data was returned")

def historical_and_predicted_market_price(start_price:str=CONFIG["ENV"]["START_DATE"], end_price:str=CONFIG["ENV"]["END_DATE"]):
    """ Function to get both historical and forecast pv generation values. """
    day_ahead_start, day_ahead_end = get_day_ahead(last_timestamp=end_price)

    # Request and store results
    historical = get_market_price(start_date=start_price, end_date=end_price)
    prediction = get_market_price(start_date=day_ahead_start, end_date=day_ahead_end, forecast=True)
    return historical, prediction

if __name__ == '__main__':
    historical_and_predicted_market_price()