import pandas as pd
import glob

from pandas.errors import EmptyDataError

from InputData.DataRequests.pv_simulation import get_pv_simulation
from InputData.DataRequests.elering_market import historical_and_predicted_market_price
from InputData.DataRequests.demand import get_demand
from InputData.helper.data_helper import get_all_dates
from Prediction.regression_prediction import return_best_predictor
from config.config import CONFIG

"""
Get all data unified into one dataframe for EDA in RStudio, 
in order to find relations between datasets.
These datasets will be linked by the timestamp, in UTC.
"""

def align_data_by_timestamp(start_time, end_time):
    """ Get all data unified by UTC timestamps """
    # Get historical solar generation
    pv_df = get_pv_simulation(start_time, end_time)[0]
    pv_df = pv_df.reset_index()

    # Get historical market prices
    price_df = historical_and_predicted_market_price(start_time, end_time)[0]

    # Get historical demand values
    demand_df = get_demand(start_time, end_time)

    dataframes = [price_df, demand_df, pv_df]
    merged = pd.concat(
        [d.set_index('Timestamp') for d in dataframes],
        axis=1,
        join='inner'
    ).reset_index()

    end_date = pd.to_datetime(merged['Timestamp'].iloc[0])
    year = str(end_date.year)
    month = str(end_date.month)

    # Modifications for better readability
    merged = merged.rename(columns={'ac_kw': 'pv_gen'})

    # Save directly into directories for processing further
    merged.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/{year}_{month}_historical_merged.csv", index=False)  # For Predictions
    return merged


def align_future_data(start_time:str = CONFIG["ENV"]["START_DATE"], end_time:str = CONFIG["ENV"]["END_DATE"]):
    """ Function to get forecasted aligned data. """
    demand = return_best_predictor(start_time, end_time)
    demand['Timestamp'] = demand.index
    pv_gen = get_pv_simulation(start_time, end_time)[1]
    pv_gen['Timestamp'] = pv_gen.index
    market_price = historical_and_predicted_market_price(start_time, end_time)[1]
    market_price = market_price.set_index('Timestamp')
    end_date = pd.to_datetime(market_price.index[0])
    year = str(end_date.year)
    month = str(end_date.month)
    dataframes = [pv_gen, market_price, demand]
    merged = pd.concat(
        dataframes,
        axis=1,
        join='inner'
    )
    # Cleanup of merged dataframe
    merged = merged.loc[:, ~merged.columns.duplicated(keep='last')]
    merged = merged.drop(columns=['poa_wm2', 't_cell', 'dc_kw', 'dow', 'weekend', 'lag24', 'lag48'])
    merged = merged.rename(columns={'ac_kw': 'pv_gen'})

    merged.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/{year}_{month}_day_ahead_merged.csv",index=False)
    return merged

def merge_all_dfs(future:bool=False):
    for pw in [5,10,50,100]:
        hist_path = f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/{pw}"
        future_path = f"{CONFIG["ENV"]["PATH_TO_DIR"]}/Results/{pw}/DayAheadcsv"
        if future:
            all_files = glob.glob(future_path + '/*kW_day_ahead_merged.csv')
        else:
            all_files = glob.glob(hist_path + '/*kW_historical_merged.csv')
        lst = []

        for filename in all_files:
            try:
                df = pd.read_csv(filename, index_col=None, header=0)
                lst.append(df)
            except EmptyDataError:
                print(f"No data found for {filename}")
                pass
        merged = pd.concat(lst, axis=0, ignore_index=True)
        merged = merged.set_index('Timestamp').sort_index()
        merged['Timestamp'] = merged.index
        if future:
            merged.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/MegaMerge/{pw}/FULL_DAY_AHEAD_merged.csv",
                          index=False)  # For Predictions
        else:
            merged.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/MegaMerge/{pw}/FULL_HISTORICAL_merged.csv",
                          index=False)  # For Predictions

    return merged

def run_all_functions():
    dates = get_all_dates()
    for start_date, end_date in dates:
        align_data_by_timestamp(start_date, end_date)
        align_future_data(start_date, end_date)
    merge_all_dfs()
    merge_all_dfs(True)


if __name__ == "__main__":
    merge_all_dfs(True)