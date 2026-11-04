from InputData.DataRequests.request_all_data import align_future_data
from config.config import CONFIG

def create_data_for_ampl():
    """
    Function to request the merged dataframe with the predicted values for day ahead,
    and generate a .dat file suited for AMPL
    """
    df = align_future_data()
    # Modify hours, to start from 1 instead of 0
    df['hour'] = df['hour'] + 1
    with open(f'{CONFIG["ENV"]["PATH_TO_DIR"]}/AMPL_Thesis/ems.dat', 'w') as f:
        f.write(f'param Timestamp := {len(df)};\n') # Set hour int values from df length
        f.write(f'param agg_rate := {CONFIG["ENV"]["AGG_RATE"]};\nparam dem_rate := {CONFIG["ENV"]["DEMAND_RATE"]};\n') # Initialize rate params
        f.write(f'param store0 := {CONFIG["ENV"]["INITIAL_STORING"]};\nparam battery_capacity := {CONFIG["ENV"]["BATTERY_CAPACITY"]};\n') # Initialize storing params
        f.write(f'param: solar_gen demand market_price :=\n') # Initialize parameters for day ahead dataframe
        for _,r in df.iterrows():
            # Write values from day ahead dataframe for solar generation, demand and market price
            f.write(f'{int(r['hour'])} {r['pv_gen']} {r['consumption']} {r['market_price']}\n')
        f.write(';\n')

if __name__ == '__main__':
    create_data_for_ampl()