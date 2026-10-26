import pandas as pd

from APICalls.helper import get_dates
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

def get_market_price(start_date: str, end_date:str, path_to_directory: str = None):
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

        # Send csv to Data directory
        data_path = f'{CONFIG["ENV"]["PATH_TO_DIR"]}/Data'
        df_price.to_csv(f"{data_path}\\market_price_{start_date[:10]}.csv")
        df_price.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/MasterThesisRStudio/Data/market_price{start_date[:10]}.csv") # Save to RStudio project
        return df_price
    else:
        raise ValueError("No data was returned")

if __name__ == '__main__':
    start, end = get_dates(offset=CONFIG["ENV"]["OFFSET"], timedelta=CONFIG["ENV"]["TIMEDELTA"])
    get_market_price(start_date=start, end_date=end)