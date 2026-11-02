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

def get_dates(offset = None, timedelta = None, to_open_meteo:bool=False, to_market:bool=False, to_consumption:bool=False):
    """
    Function to give back a period of time to request de data for.
    This function returns the data range from OFFSET at Start of the Day (00:00h) to TIMEDELTA at EOD (End Of Day)
    """
    now = datetime.now(timezone.utc)
    now = now.replace(hour=0, minute=0, second=0, microsecond=0) # Split the data from historical until today at 00:00h

    if to_market:
        now = now - pd.Timedelta(hours=2)

    # Parse the type ISO8601 into a more readable format
    offset = (now - isodate.parse_duration(offset)).strftime("%Y-%m-%dT%H:%MZ")
    timedelta = (now - isodate.parse_duration(timedelta)).strftime("%Y-%m-%dT%H:%MZ")

    if to_open_meteo:
        offset = offset[:10]
        timedelta = timedelta[:10]

    if offset >= timedelta:
        return timedelta, offset
    else:
        raise ValueError("Timedelta must refer to past values! Since it requests historical data.")

def get_day_ahead(to_open_meteo:bool=False):
    """ Get the Day Ahead start and end time """
    # Split the data from historical until today at 00:00h
    now = datetime.now(timezone.utc)
    now = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Parse the type ISO8601 into a more readable format
    day_ahead_start = (now + pd.Timedelta(days=1)).strftime("%Y-%m-%dT%H:%MZ")

    if to_open_meteo:
        return day_ahead_start[:10]
    now = now - pd.Timedelta(hours=2) # Change from EET to UTC
    day_ahead_start = (now + pd.Timedelta(days=1)).strftime("%Y-%m-%dT%H:%MZ")
    day_ahead_end = (now + pd.Timedelta(days=1,hours=23)).strftime("%Y-%m-%dT%H:%MZ")
    return day_ahead_start, day_ahead_end

def clean_data_dir():
    """ delete all data files from the Data directory """
    answer = input("About to delete all files, are you sure? (Y/n): ").strip().lower()
    if answer in ("y", "yes"):
        folder = f'{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data'
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