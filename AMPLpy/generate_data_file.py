from InputData.DataRequests.request_all_data import align_future_data
from config.config import CONFIG

import pandas as pd
from pathlib import Path

base = Path(__file__).resolve().parent      # folder containing this script

def create_data_for_ampl():
    """
    Function to request the merged dataframe with the predicted values for day ahead,
    and generate a .dat file suited for AMPL
    """
    df = align_future_data()
    end_date = pd.to_datetime(df['timestamp'].iloc[0])
    year = str(end_date.year)
    month = str(end_date.month)
    # Modify hours, to start from 1 instead of 0
    df['hour'] = df['hour'] + 1
    df = df.rename(columns={'demand':'demand(kWh)', 'pv_gen':'pv_gen(kWh)'})
    ampl_path = f'{CONFIG["ENV"]["PATH_TO_DIR"]}/AMPL_Thesis/{year}_{month}_ems.dat'
    with open(ampl_path, 'w') as f:
        f.write(f'param Timestamp := {len(df)};\n') # Set hour int values from df length
        f.write(f'param agg_rate := {CONFIG["ENV"]["AGG_RATE"]};\nparam dem_rate := {CONFIG["ENV"]["DEMAND_RATE"]};\n') # Initialize rate params
        f.write(f'param store0 := {CONFIG["ENV"]["INITIAL_STORING"]};\nparam battery_capacity := {CONFIG["ENV"]["BATTERY_CAPACITY"]};\n') # Initialize storing params
        f.write(f'param: pv_gen demand market_price :=\n') # Initialize parameters for day ahead dataframe
        for _,r in df.iterrows():
            # Write values from day ahead dataframe for solar generation, demand and market price
            f.write(f'{int(r['hour'])} {r['pv_gen(kWh)']} {r['demand(kWh)']} {r['market_price(€/kWh)']}\n')
        f.write(';\n')

if __name__ == '__main__':
    create_data_for_ampl()