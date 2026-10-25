import os, shutil
import pandas as pd
from io import StringIO
from config.config import CONFIG
from datetime import datetime, timezone
import isodate

def turn_csv_str_into_df(csv_str: str) -> pd.DataFrame:
    """ Take the csv from an API request and turn into a dataframe to do modifications """
    csv_str = csv_str.strip()
    df = pd.read_csv(StringIO(csv_str), sep=';')
    return df

def float_converter(s:str) -> float:
    """ Helper to turn variables from config file into float for calculations """
    return float(CONFIG["ENV"][s])

def get_dates(offset = None, timedelta = None,start = None, end = None, to_open_meteo:bool=False):
    """
    Function to give back a period of time to request de data for.
    If nothing is given, the last 7 days will be queried.
    """
    now = datetime.now(timezone.utc)
    now = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # Parse the type ISO8601 into a more readable format
    offset = (now + isodate.parse_duration(offset)).strftime("%Y-%m-%dT%H:%MZ")
    timedelta = (now + isodate.parse_duration(timedelta)).strftime("%Y-%m-%dT%H:%MZ")
    if to_open_meteo:
        offset = offset[:10]
        timedelta = timedelta[:10]
    if offset > timedelta:
        return timedelta, offset
    elif offset < timedelta:
        return offset, timedelta
    elif timedelta == offset:
        raise ValueError("Offset and Timedelta cannot be the same date")


def unify_data(list_of_dfs: list, path: str, type_of_data: str):
    """ Stack different calls from different time ranges into a unified dataframe """
    merged_df = pd.concat(list_of_dfs)
    return merged_df.to_csv(f"{path}_merged.csv")

def clean_data_dir():
    """ delete all data files from the Data directory """
    answer = input("About to delete all files, are you sure? (Y/n): ").strip().lower()
    if answer in ("y", "yes"):
        folder = f'{CONFIG["ENV"]["PATH_TO_DIR"]}/Data'
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
    if answer in ("n", "no"):
        return

if __name__ == "__main__":
    clean_data_dir()