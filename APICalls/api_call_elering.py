import csv
import logging
import io
from xmlrpc.client import Error

import pandas as pd
from pyparsing import Empty

from APIClient import Server, ApiClient
from helper import turn_csv_str_into_df

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

def get_market_price(start_date: str, end_date:str):
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
        df_price = df_price.rename(columns={'Kuupäev (Eesti aeg)': 'Start Date', 'NPS Eesti': 'Market Price'})

        df_price["Start Date"] = (
            pd.to_datetime(df_price["Start Date"], format="%d.%m.%Y %H:%M")
            .dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        df_price['Market Price'] = df_price['Market Price'].str.replace(",",".", regex=False)
        df_price['Market Price'] = df_price['Market Price'].astype(float)

        # Send csv to Data directory
        data_path = r'C:\Users\pilim\Documents\PythonProjects\MasterThesis\Data'
        df_price.to_csv(f"{data_path}\\market_price_{start_date[:10]}.csv")
    else:
        raise ValueError("No data was returned")

def get_solar_production(start_date:str, end_date:str):
    """ This method gets power system data for selected time period in CSV file """

    path = "/api/system/csv"
    parameters_solar = {
        'start': start_date,
        'end': end_date,
        'fields': 'solar_energy_production'
    }
    solar = call_api(path=path, params=parameters_solar)
    if solar:
        # Make necessary modifications to data
        df_price = turn_csv_str_into_df(solar)
        df_price = df_price.drop(columns=['Ajatempel (UTC)'])
        df_price = df_price.rename(columns={'Kuupðev (Eesti aeg)': 'Start Date', 'Pðikseseenergia toodang': 'Solar Generation'})

        df_price["Start Date"] = (
            pd.to_datetime(df_price["Start Date"], format="%d.%m.%Y %H:%M")
            .dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        df_price['Solar Generation'] = df_price['Solar Generation'].str.replace(",", ".", regex=False)
        df_price['Solar Generation'] = df_price['Solar Generation'].astype(float)

        # Send csv to Data directory
        data_path = r'C:\Users\pilim\Documents\PythonProjects\MasterThesis\Data'
        df_price.to_csv(f"{data_path}\\solar_generation_{start_date[:10]}.csv")
    else:
        raise ValueError("No data was returned")


if __name__ == '__main__':
    start = '2026-10-01T20:59:59.999Z'
    end = '2026-10-10T20:59:59.999Z'

    get_solar_production(start_date=start, end_date=end)
    get_market_price(start_date=start, end_date=end)