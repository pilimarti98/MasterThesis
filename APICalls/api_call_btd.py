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

    return response.json()

def get_afrr_prices():
    """ Requests aFRR bid prices """
    parameters = {
        'id' : 'afrr_bid_prices',
        'start_date' : '2026-10-03T00:00',
        'end_date': '2026-10-02T00:00',
        'output_time_zone' : 'EET',
        'output_format' : 'json'
    }
    json = call_api(params=parameters)
    return json

if __name__ == '__main__':
    get_afrr_prices()

def process_api(parameters):
    response = requests.get('https://api-baltic.transparency-dashboard.eu/api/v1/export', parameters)

    # Save the json data
    json_data = response.json()

    # Save the data pertinent to the graph as a dataframe
    df = pd.DataFrame(json_data['data']['timeseries'])

    # Modify data in order to create the chart
    df_columns = pd.DataFrame(json_data['data']['columns'])

    # Switch timestamps to YYYY-MM-DDTHH
    df['from'] = df['from'].astype(str).apply(lambda x: x[:13])

    df_columns = df_columns.drop(columns=['index', 'res'])

    # Create a new dataframe with only the information needed for the graph
    df_columns = df_columns.pivot(index='col', columns='group_level_0', values='label')

    df = df.drop(columns=['to'])
    df = df.rename(columns={'from': 'MWh - CET'})

    # Add the names for each column and create new one with the power from all the Baltic countries
    df[df_columns.columns[0]] = df['values'].str[0]
    df[df_columns.columns[1]] = df['values'].str[1]
    df[df_columns.columns[2]] = df['values'].str[2]
    df['Baltics'] = df['values'].apply(sum)

    df = df.drop(columns=['values'])

    # Change the granularity from 15 min to hourly in order to have the plot less crowded with information
    df = df.groupby(['MWh - CET']).sum()
    df.reset_index(inplace=True)

    return df


# 1. Inherit data on Baltic imbalance amounts: https://baltic.transparency-dashboard.eu/node/44?mode=table
parameters_imb = {
    "id": "imbalance_volumes_v2",
    'start_date': '2025-02-11T00:00',
    'end_date': '2025-02-17T00:00',
    'output_time_zone': 'CET',
    'output_format': 'json',
}
imbalance = process_api(parameters_imb)
print(imbalance.columns)

imbalance.set_index('MWh - CET', inplace=True)

min_val = imbalance.min().min()
max_val = imbalance.max().max()
y_limit = max(abs(min_val), abs(max_val))

# Plot the imbalances
plt.figure(figsize=(10, 6))
for column in imbalance.columns:
    plt.plot(imbalance.index, imbalance[column], label=column)

plt.xticks(rotation=90)
plt.ylim(-y_limit, y_limit)
plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
plt.xlabel('Timestamp')
plt.ylabel('MWh')
plt.title('Imbalances in the Baltics')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# 2. Inherit data regarding Baltic activations: https://baltic.transparency-dashboard.eu/node/35
parameters_act = {
    "id": "activations_afrr",
    'start_date': '2025-02-07T00:00',
    'end_date': '2025-02-11T00:00',
    'output_time_zone': 'CET',
    'output_format': 'json'
}
activations = process_api(parameters_act)

activations.set_index('MWh - CET', inplace=True)

# Plot the activations
plt.figure(figsize=(10, 6))
for column in activations.columns:
    plt.plot(activations.index, activations[column], label=column)

plt.xticks(rotation=90)
plt.xlabel('Timestamp')
plt.ylabel('MWh')
plt.title('Activations in the Baltics')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()