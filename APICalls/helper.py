import pandas as pd
from io import StringIO

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



def unify_data(list_of_dfs: list, path: str):
    """ Get all data from different API calls into a unified dataframe """
    merged_df = pd.concat(list_of_dfs)
    # merge all dataframes into one
    return merged_df.to_csv(f"{path}_merged.csv")