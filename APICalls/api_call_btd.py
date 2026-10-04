import requests
import pandas as pd
import matplotlib.pyplot as plt
from APIClient import Server, ApiClient

def call_api(params: dict):
    """ Helper function to make a request from Baltic Transparency Dashboard"""
    server = Server(
        name='BTD',
        base_url='https://api-baltic.transparency-dashboard.eu'
    )
    api = ApiClient(server)

    response = api.request(
        method="GET",
        path='/api/v1/export',
        params=params
    )

    return response

def get_afrr_prices():
    """ Requests aFRR bid prices """
    parameters = {
        'id' : 'afrr_bid_prices',
        'start_date' : '2026-10-01T00:00',
        'end_date': '2026-10-02T00:00',
        'output_time_zone' : 'EET',
        'output_format' : 'json'
    }
    json = call_api(params=parameters)

    df = pd.DataFrame(json)

    return df

if __name__ == '__main__':
    get_afrr_prices()