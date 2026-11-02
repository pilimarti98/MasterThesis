import pandas as pd

from InputData.helper import get_dates
from InputData.PV_Simulation.pv_simulation import get_pv_simulation
from InputData.elering_market import historical_and_predicted_market_price
from InputData.consumption import get_consumption
from Prediction.regression_prediction import return_best_predictor
from config.config import CONFIG

"""
Get all data unified into one dataframe for EDA in RStudio, 
in order to find relations between datasets.
These datasets will be linked by the timestamp, in UTC.
"""

def align_data_by_timestamp(future:bool = False):
    """ Get all data unified by UTC timestamps """
    # Get historical solar generation
    pv_df = get_pv_simulation()[0]
    pv_df = pv_df.reset_index()

    # Get historical market prices
    price_df = historical_and_predicted_market_price()[0]

    # Get historical consumption values
    consumption_df = get_consumption()

    dataframes = [price_df, consumption_df, pv_df]
    merged = pd.concat(
        [d.set_index('Timestamp') for d in dataframes],
        axis=1,
        join='inner'
    ).reset_index()

    # Modifications for better readability
    merged = merged.drop(columns=['poa_wm2', 't_cell', 'dc_kw'])
    merged = merged.rename(columns={'Market Price [€/kWh]': 'marketprice','Consumption [kWh]':'consumption', 'ac_kw': 'generatedPV'})

    # Save directly into directories for processing further
    merged.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/merged.csv", index=False)  # For Predictions
    merged.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/MasterThesisRStudio/Data/merged.csv", index=False) # For RStudio
    return merged


def align_future_data():
    """ Function to get forecasted aligned data. """
    # consumption = return_best_predictor()
    pv_gen = get_pv_simulation()[1]
    market_price = historical_and_predicted_market_price()[1]
    market_price = market_price.set_index('Timestamp')
    dataframes = [pv_gen, market_price]
    merged = pd.concat(
        dataframes,
        axis=1,
        join='inner'
    )

    merged.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/day_ahead_merged.csv", index=False)  # For Predictions
    merged.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/MasterThesisRStudio/Data/day_ahead_merged.csv", index=False)  # For RStudio
    merged.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/AMPL_Thesis/day_ahead_merged.csv", index=False)  # For AMPL
    return merged

if __name__ == "__main__":
    align_data_by_timestamp()
    align_future_data()