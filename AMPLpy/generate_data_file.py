from InputData.DataRequests.request_all_data import align_future_data
from config.config import CONFIG

import pandas as pd

def create_data_for_ampl(start:str=CONFIG["ENV"]["START_DATE"], end:str=CONFIG["ENV"]["END_DATE"]):
    """
    Function to request the merged dataframe with the predicted values for day ahead,
    and generate a .dat file suited for AMPL
    """
    df = align_future_data(start, end)
    df = df.rename(columns={'market_price(€/kWh)':'market_price'})
    df['hour'] = df['hour'] + 1
    end_date = pd.to_datetime(df['Timestamp'].iloc[0])
    year = str(end_date.year)
    month = str(end_date.month)
    # Modify hours, to start from 1 instead of 0

    with open(f"{year}_{month}_ems.dat", "w") as f:
        print(f"Generating file: {year}_{month}_ems.dat")
        f.write(f'param Timestamp := {len(df)};\n')  # Set hour int values from df length
        f.write(
            f'param agg_rate := {CONFIG["ENV"]["AGG_RATE"]};\nparam dem_rate := {CONFIG["ENV"]["DEMAND_RATE"]};\nparam vat_rate := {CONFIG["ENV"]["VAT_RATE"]};\n')  # Initialize rate params
        f.write(
            f'param store0 := {CONFIG["ENV"]["INITIAL_STORING"]};\nparam battery_capacity := {CONFIG["ENV"]["BATTERY_CAPACITY"]};\n')  # Initialize storing params
        f.write(f'param: pv_gen demand market_price :=\n')  # Initialize parameters for day ahead dataframe
        for _, r in df.iterrows():
            f.write(f"{int(r['hour'])} {r['pv_gen']} {r['demand']} {r['market_price']}\n")
        f.write(";\n")

if __name__ == '__main__':
    create_data_for_ampl()