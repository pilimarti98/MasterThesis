import logging
import pandas as pd
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.ensemble import GradientBoostingRegressor

from InputData.consumption import get_consumption
from InputData.helper import get_dates
from config.config import CONFIG


def load_dataset():
    """ Load Historical Consumption Data """
    start, end = get_dates(offset=CONFIG["ENV"]["OFFSET"], timedelta=CONFIG["ENV"]["TIMEDELTA"])
    df = get_consumption(start_meter=start, end_meter=end)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    time_df = df.set_index('Timestamp').sort_index()

    time_df['hour'] = time_df.index.hour
    time_df['dow'] = time_df.index.dayofweek
    time_df['lag_24'] = time_df['consumption'].shift(-24) # Get the value from the next day for prediction comparison
    time_df = time_df.dropna()
    return time_df

def split_dataset():
    """ Split data from input data (X) and the response (y)"""
    time_df = load_dataset()
    time_df.index = pd.to_datetime(time_df.index)

    X = time_df.drop(columns=['consumption'])
    y = time_df['consumption']

    # Chronological split: last 7 days as test
    split = time_df.index.max() - pd.Timedelta(days=7)

    n_test = (time_df.index > split).sum() # rows in the last 7 days
    X_train, X_test = X.iloc[:-n_test], X.iloc[n_test:]
    y_train, y_test = y.iloc[:-n_test], y.iloc[n_test:]

    # Get a dataframe with the next 24 hours timestamps to predict
    last = time_df.index.max()
    timestamps_index = pd.date_range(start=last + pd.Timedelta(hours=1),
                                          periods=24, freq='h', tz='UTC')
    timestamps_df = pd.DataFrame(timestamps_index)
    timestamps_df = timestamps_df.set_index([0])
    future_timestamps = pd.concat(objs=[X, timestamps_df], axis='index')

    return X_train, X_test, y_train, y_test, future_timestamps

def build_model():
    """ Build GradientBoosting predictor """
    X_train, X_test, y_train, y_test, future_timestamps = split_dataset()
    model = GradientBoostingRegressor(random_state=42)
    model.fit(X_train, y_train)

    # Analyze results
    print("Model MAE: ", mean_absolute_error(y_test, model.predict(X_test)))
    print("Naive MAE: ", mean_absolute_error(y_test, X_test['lag_24']))

    print("Model R squared",r2_score(y_test, model.predict(X_test)))
    print("Naive R squared",r2_score(y_test, X_test['lag_24']))

    if r2_score(y_test, model.predict(X_test)) < 0.3:
        logging.warning("R squared score is low")

    future_timestamps.index = pd.to_datetime(future_timestamps.index)
    future_timestamps['hour'] = future_timestamps.index.hour
    future_timestamps['dow'] = future_timestamps.index.dayofweek
    future_timestamps['consumption'] = model.predict(future_timestamps)

    return

if __name__ == '__main__':
    build_model()