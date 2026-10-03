import requests
import pandas as pd
import matplotlib.pyplot as plt

def process_api(parameters: dict | None = None):
    response = requests.get('https://dashboard.elering.ee/api/transmission/cross-border/latest')

    # Save the json data
    json_data = response.json()
    df = pd.DataFrame(json_data['data']['timeseries'])

if __name__ == '__main__':
    process_api()