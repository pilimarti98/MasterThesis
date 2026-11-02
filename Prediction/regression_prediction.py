import logging
import pandas as pd
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor

from InputData.consumption import get_consumption
from InputData.helper import get_dates
from config.config import CONFIG

def load_dataset():
    """ Load Historical Consumption Data for a month """
    start, end = get_dates(offset=CONFIG["ENV"]["OFFSET"], timedelta=CONFIG["ENV"]["TIMEDELTA"])
    df = get_consumption(start_meter=start, end_meter=end)
    df.index = pd.to_datetime(df['Timestamp'])
    df = df.set_index('Timestamp').sort_index()
    return df

def split_dataset():
    """ Split data from input data (X) and the response (y)"""

    def get_timestamp_features(df_X:pd.DataFrame):
        """ Get X features from the Timestamps to be fit for the model """
        X = pd.DataFrame()
        X['hour'] = df_X.index.hour
        X['dow'] = df_X.index.dayofweek
        X['weekend'] = (X['dow'] >= 5).astype(int)
        X['lag24'] = df_X['consumption'].shift(24) # Value from previous day
        X['lag48'] = df_X['consumption'].shift(48) # Value from two days ago
        return X

    # Get consumption dataset
    df = load_dataset()
    df.index = pd.to_datetime(df.index)

    # Chronological split: last 7 days as test
    last = df.index.max()
    split = last - pd.Timedelta(days=7)
    n_test = (df.index > split).sum()  # rows in the last 7 days

    # Append 24 empty future hours so lags get computed for them
    future_idx = pd.date_range(start=last + pd.Timedelta(hours=1),
                                          periods=24, freq='h', tz='UTC')
    future_df = pd.DataFrame(index=future_idx)
    full = pd.concat([df, future_df])
    future_df = get_timestamp_features(df_X=full)

    # Get input (X) and output (y)
    X = get_timestamp_features(df_X=full)
    y = df['consumption']
    X_train, X_test = X.iloc[:-n_test], X.iloc[-n_test:]
    y_train, y_test = y.iloc[:-n_test], y.iloc[-n_test:]

    return X_train, X_test, y_train, y_test, future_df

def build_gradient_boosting_model():
    """ Build GradientBoosting predictor """
    X_train, X_test, y_train, y_test, future_df = split_dataset()
    model = GradientBoostingRegressor(random_state=42)
    model.fit(X_train, y_train)

    # Analyze results
    print("Model MAE: ", mean_absolute_error(y_test, model.predict(X_test)))
    print("Model R squared",r2_score(y_test, model.predict(X_test)))

    if r2_score(y_test, model.predict(X_test)) < 0.3:
        logging.warning("R squared score is low")
    return future_df

def build_mlp_regressor_model():
    """ Build Multi-Layer Perceptron Regressor """
    X_train, X_test, y_train, y_test, future_timestamps = split_dataset()
    model = MLPRegressor(hidden_layer_sizes=(32,16),
                         alpha=1e-3,
                         early_stopping=True,
                         max_iter=1000,
                         random_state=42)
    model.fit(X_train, y_train)

    # Analyze results
    print("Model MAE: ", mean_absolute_error(y_test, model.predict(X_test)))
    print("Model R squared", r2_score(y_test, model.predict(X_test)))

    if r2_score(y_test, model.predict(X_test)) < 0.3:
        logging.warning("R squared score is low")
    future_timestamps['consumption'] = model.predict(future_timestamps['Timestamps'])
    return future_timestamps

if __name__ == '__main__':
    build_gradient_boosting_model()
    build_mlp_regressor_model()