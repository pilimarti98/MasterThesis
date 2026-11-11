from InputData.DataRequests.pv_simulation import get_pv_simulation
from InputData.helper.data_helper import get_all_dates
from AMPLpy.amplpy_setup import projected_yearly_benefits
from config.config import CONFIG

import pandas as pd

def pv_scenarios():
    """
    Change Solar panels capacity and update data.
    Scenario cases are: 5kW, 10kW, 50kW, 100kW
    """
    dates = get_all_dates()
    power_cases = [5, 10, 50, 100]
    for pw in power_cases:
        for start, end in dates:
            year = pd.to_datetime(end).year
            month = pd.to_datetime(end).month
            # To get results, must generate new .dat files and ROI
            # In this function, new csv files are generated
            df = pd.read_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/{year}_{month}_day_ahead_merged.csv")
            df = df.rename(columns={'market_price(€/kWh)': 'market_price'})
            df['hour'] = df['hour'] + 1  # Modify hours, to start from 1 instead of 0

            # New pv_generation
            _, day_ahead = get_pv_simulation(start, end, pdc0=pw)
            df['pv_gen'] = day_ahead['ac_kw'].values
            df.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/Results/{pw}/DayAheadcsv/{year}_{month}_{pw}kW_day_ahead_merged.csv")

            # Generate .dat files for each case
            for case in ['only_battery', 'ems']:
                with open(f"{year}_{month}_{pw}_{case}.dat", "w") as f:
                    print(f"Generating file: {year}_{month}_{pw}_{case}.dat")
                    f.write(f'param Timestamp := {len(df)};\n')  # Set hour int values from df length
                    f.write(
                        f'param agg_rate := {CONFIG["ENV"]["AGG_RATE"]};\nparam dem_rate := {CONFIG["ENV"]["DEMAND_RATE"]};\n\nparam vat_rate := {CONFIG["ENV"]["VAT_RATE"]}')  # Initialize rate params
                    f.write(
                        f'param store0 := {CONFIG["ENV"]["INITIAL_STORING"]};\nparam battery_capacity := {CONFIG["ENV"]["BATTERY_CAPACITY"]};\n')  # Initialize storing params
                    f.write(f'param: pv_gen demand market_price :=\n')  # Initialize parameters for day ahead dataframe
                    for _, r in df.iterrows():
                        f.write(f"{int(r['hour'])} {r['pv_gen']} {r['demand']} {r['market_price']}\n")
                    f.write(";\n")

def run_ampl_scenarios():
    dates = get_all_dates()
    power_cases = [5, 10, 50, 100]
    base_case_dict = dict()
    battery_dict = dict()
    ems_dict = dict()
    for pw in power_cases:
        for start, end in dates:
            year = pd.to_datetime(end).year
            month = pd.to_datetime(end).month
            battery_cost, ems_cost = projected_yearly_benefits(year=year, month=month, pw=pw)
            base_case_dict[f'{year}_{month}_{pw}'] = base_case_cost
            battery_dict[f'{year}_{month}_{pw}'] = battery_cost
            ems_dict[f'{year}_{month}_{pw}'] = ems_cost
    return base_case_dict, battery_dict, ems_dict

if __name__ == '__main__':
    pv_scenarios()
