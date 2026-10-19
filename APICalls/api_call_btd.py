import pandas as pd
import logging

from config.config import CONFIG
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

def get_afrr_prices(start_date: str, end_date:str, path: str = None):
    """ Requests aFRR bid prices and returns a JSON object"""
    parameters = {
        'id' : 'afrr_bid_prices',
        'start_date' : start_date,
        'end_date': end_date,
        'output_time_zone' : 'EET',
        'output_format' : 'json'
    }
    json = call_api(params=parameters)

    # Save the data pertinent to the graph as a dataframe
    df = pd.DataFrame(json['data']['timeseries'])
    if df.empty:
        logging.error("No data was found")
    else:
        # Modify data in order to create the standard format for the csv
        df_columns = pd.DataFrame(json['data']['columns'])
        df_columns = df_columns.drop(columns=['index', 'res'])
        df_columns = df_columns.pivot(index='col', columns='group_level_0', values='label')
        df[df_columns.columns[0]] = df['values'].str[0]
        df = df.drop(columns=['values', 'to'])
        df = df.rename(columns={'from': 'Start Date', 'Estonia': 'aFRR prices [€/MWh]'})
        df["Start Date"] = (
                pd.to_datetime(df["Start Date"], utc=True)
                + pd.Timedelta(hours=3)
        ).dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        df.to_csv(f"C{CONFIG["ENV"]["PATH_TO_DIR"]}/Data/afrr_prices_{start_date[:10]}.csv")
        return df


if __name__ == '__main__':
    start = '2026-10-01T00:00:00.000Z'
    end = '2026-10-10T00:00:00.000Z'
    get_afrr_prices(start_date=start, end_date=end)