import csv
import logging

import pandas as pd
import io
from APIClient import Server, ApiClient

def call_api(path: str, params: dict, file_type:str = 'json'):
    """ Helper function to make a request from Baltic Transparency Dashboard"""
    server = Server(
        name='elering',
        base_url='https://dashboard.elering.ee'
    )
    api = ApiClient(server)

    response = api.request(
        method="GET",
        path=path,
        params=params,
        file_type=file_type
    )

    return response

def get_market_price(start_date: str, end_date:str, file_type:str):
    """ Request NordPool day-ahead price data in CSV file """

    if file_type == 'json':
        path="/api/nps/price"
        parameters_price = {
            'start': start_date,
            'end': end_date
        }
        price = call_api(path=path, params=parameters_price, file_type=file_type)
    elif file_type == 'csv':
        path = "/api/nps/price/csv"
        parameters_price = {
            'start' : start_date,
            'end' : end_date,
            'fields' : 'ee'
        }
        price = call_api(path=path, params=parameters_price, file_type=file_type)
        data_path = r'C:\Users\pilim\Documents\PythonProjects\MasterThesis\Data'
        with open(f"{data_path}\\market_price_{start_date[:11]}-{end_date[:11]}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(csv.reader(io.StringIO(price), delimiter=";"))
    else:
        raise ValueError("Only available file types are csv or json")


def get_solar_production(start_date:str, end_date:str, file_type:str):
    """ This method gets power system data for selected time period in CSV file """

    if file_type == 'json':
        path = "/api/system"
        parameters_solar = {
            'start': start_date,
            'end': end_date
        }
    elif file_type == 'csv':
        path = "/api/system/csv"
        parameters_solar = {
            'start': start_date,
            'end': end_date,
            'fields': 'solar_energy_production'
        }
    else:
        raise ValueError("Only available file types are csv or json")
    solar = call_api(path=path, params=parameters_solar, file_type=file_type)
    data_path = r'C:\Users\pilim\Documents\PythonProjects\MasterThesis\Data'

    with open(f"{data_path}\\solar_{start_date[:11]}-{end_date[:11]}.csv", "w", newline="", encoding="utf-8") as csvfile:
        if solar:
            writer = csv.writer(csvfile)
            writer.writerows(csv.reader(io.StringIO(solar), delimiter=";"))
        else:
            logging.error("API request returned empty")

if __name__ == '__main__':
    start = '2026-10-01T20:59:59.999Z'
    end = '2026-10-10T20:59:59.999Z'

    get_market_price(start_date=start, end_date=end, file_type='csv')
    get_solar_production(start_date=start, end_date=end, file_type='csv')