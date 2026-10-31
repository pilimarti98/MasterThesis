import pandas as pd
from datetime import datetime, timedelta

from InputData.helper import get_dates
from APIClient import Server, ApiClient
from helper import turn_csv_str_into_df
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

def get_market_price(start_date: str, end_date:str, forecast:bool=False):
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
        df_price = df_price.rename(columns={'Kuupäev (Eesti aeg)': 'Timestamp', 'NPS Eesti': 'Market Price [€/MWh]'})

        df_price["Timestamp"] = pd.to_datetime(df_price["Timestamp"], dayfirst=True)
        df_price['Market Price [€/MWh]'] = pd.to_numeric(df_price['Market Price [€/MWh]'].str.replace(',','.'), errors='coerce')

        df_price = (
            df_price.set_index("Timestamp")
                    .resample('h')
                    .mean(numeric_only=True)
                    .reset_index()
        )

        df_price["Timestamp"] = df_price["Timestamp"].dt.strftime("%Y-%m-%dT%H:%MZ")
        df_price['Market Price [€/MWh]'] = df_price['Market Price [€/MWh]']/ 1000.0 # Convert the price to kWh
        df_price = df_price.rename(columns={'Market Price [€/MWh]':'Market Price [€/kWh]'})

        if forecast:
            # Send csv to Data directory
            df_price.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/forecast_market_price.csv")
            df_price.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/MasterThesisRStudio/Data/forecast_market_price.csv")  # Save to RStudio project
            return df_price
        else:
            # Send csv to Data directory
            df_price.to_csv(
                f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/historical_market_price.csv")
            df_price.to_csv(
                f"{CONFIG["ENV"]["PATH_TO_DIR"]}/MasterThesisRStudio/Data/historical_market_price.csv")  # Save to RStudio project
            return df_price
    else:
        raise ValueError("No data was returned")

def historical_and_predicted_market_price(start_price:str, end_price:str):
    """ Function to get both historical and forecast pv generation values. """
    forecasted_start = datetime.strptime(end_price, "%Y-%m-%dT%H:%MZ")
    forecasted_start = forecasted_start + timedelta(hours=1)
    forecasted_end = forecasted_start + timedelta(days=1)

    forecasted_start = datetime.strftime(forecasted_start, "%Y-%m-%dT%H:%MZ")
    forecasted_end = datetime.strftime(forecasted_end, "%Y-%m-%dT%H:%MZ")


    # Request and store results
    get_market_price(start_date=start_price, end_date=end_price)
    get_market_price(start_date=forecasted_start, end_date=forecasted_end, forecast=True)

if __name__ == '__main__':
    start, end = get_dates(offset=CONFIG["ENV"]["OFFSET"], timedelta=CONFIG["ENV"]["TIMEDELTA"])
    historical_and_predicted_market_price(start_price=start, end_price=end)