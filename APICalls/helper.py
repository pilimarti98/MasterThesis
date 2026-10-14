from datetime import datetime, timezone
import pandas as pd
from io import StringIO

"""
To do:
1. Unify dataframes by start date
2. Add an option to add rows with new timestamps
3. Create different functions for the different usages:
    3.1 RStudio
    3.2 ML
    3.3 AMPL
"""

def turn_csv_str_into_df(csv_str: str) -> pd.DataFrame:
    """ Take the csv from an API request and turn into a dataframe to do modifications """
    csv_str = csv_str.strip()
    df = pd.read_csv(StringIO(csv_str), sep=';')
    return df


def get_dates(start_date: str = None, end_date: str = None, offset: str = None, timedelta: str = None):

    """
    Function to give back a period of time to request de data for.
    If nothing is given, the last 7 days will be queried.

    """






def unify_data(list_of_dfs: list):
    """ Get all data from different API calls into a unified dataframe """

    # merge all dataframes into one

    # Save into this directory for MasterThesis python use and MasterThesisStudio for R Studio use