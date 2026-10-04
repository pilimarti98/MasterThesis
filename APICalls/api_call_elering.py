import pandas as pd
import matplotlib.pyplot as plt
from APIClient import Server, ApiClient

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

def get_market_price():
    """ Request NordPool day-ahead price data in CSV file """

    path = "/api/nps/price/csv"
    parameters_price = {
        'start' : '2026-09-31T00:00:000Z',
        'end' : '2026-10-01T00:00:000Z',
        'fields' : 'ee'
    }
    price = call_api(path=path, params=parameters_price)
    return price

def get_solar_production():
    """ This method gets power system data for selected time period in CSV file """
    path = "/api/system/csv"
    parameters_solar = {
        'start': '2026-09-31T00:00:000Z',
        'end': '2026-10-01T00:00:000Z',
        'fields': 'solar_energy_production'
    }
    solar = call_api(path=path, params=parameters_solar)
    return solar

if __name__ == '__main__':
    get_market_price()
    get_solar_production()