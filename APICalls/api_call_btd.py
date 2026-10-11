import pandas as pd
import csv

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
        params=params,
        file_type='json'
    )

    return response

def get_afrr_prices(start_date: str, end_date:str):
    """ Requests aFRR bid prices """
    parameters = {
        'id' : 'afrr_bid_prices',
        'start_date' : start_date,
        'end_date': end_date,
        'output_time_zone' : 'EET',
        'output_format' : 'json'
    }
    json = call_api(params=parameters)

    df = pd.DataFrame(json)

    df.to_csv("afrr_prices")

if __name__ == '__main__':
    start = '2026-10-01T20:59:59'
    end = '2026-10-10T20:59:59'
    get_afrr_prices(start_date=start, end_date=end)