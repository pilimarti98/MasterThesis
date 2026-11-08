import logging

import pandas as pd
import numpy as np
from requests import HTTPError

from sklearn.metrics import mean_absolute_error
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor

from InputData.DataRequests.demand import get_demand
from config.config import CONFIG

def load_dataset():
    """ Load Historical Demand Data for a month """
    try:
        df = get_demand()
    except HTTPError:
        # In case the API call falls, relay on the database
        df = pd.read_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/historical_demand.csv")
        df = df.drop(columns=['Unnamed: 0'])
    df.index = pd.to_datetime(df['Timestamp'])
    df = df.set_index('Timestamp').sort_index()
    return df

def split_dataset():
    """ Split data from input data (X) and the response (y) """

    def get_timestamp_features(df_feat:pd.DataFrame):
        """ Get X features from the Timestamps to be fit for the model """
        df_feat['hour'] = df_feat.index.hour
        df_feat['dow'] = df_feat.index.dayofweek
        df_feat['weekend'] = (df_feat['dow'] >= 5).astype(int)
        if 'demand' not in df_feat.columns:
            df_feat['demand'] = np.nan
        df_feat['lag24'] = df_feat['demand'].shift(24) # Value from previous day
        df_feat['lag48'] = df_feat['demand'].shift(48) # Value from two days ago
        return df_feat

    # Get demand dataset
    df = load_dataset()
    df.index = pd.to_datetime(df.index)

    # Chronological split: last 7 days as test
    last = df.index[-1]
    split = last - pd.Timedelta(days=7)
    n_test = (df.index > split).sum()  # rows in the last 7 days

    # Get input (X) and output (y)
    X = get_timestamp_features(df_feat=df)
    X = X.dropna()
    y = X['demand']
    X = X.drop(columns='demand')
    X_train, X_test = X.iloc[:-n_test], X.iloc[-n_test:]
    y_train, y_test = y.iloc[:-n_test], y.iloc[-n_test:]

    # Get dataset with timestamp of demand values to predict
    day_ahead = last - pd.Timedelta(days=1)
    n_test = (df.index > day_ahead).sum()  # rows in the last day
    future_idx = pd.date_range(df.index[-1] + pd.Timedelta(days=1, hours=1), periods=24, freq='h')
    full = pd.concat([df, pd.DataFrame(index=future_idx)])
    predict = get_timestamp_features(df_feat=full).iloc[-n_test:]
    predict = predict.drop(columns='demand')
    return X_train, X_test, y_train, y_test, predict

def build_gradient_boosting_model():
    """ Build GradientBoosting predictor """
    X_train, X_test, y_train, y_test, predict_dataset = split_dataset()
    model = GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=42)
    model.fit(X_train, y_train)

    # Analyze results
    print("Model MAE: ", mean_absolute_error(y_test, model.predict(X_test)))

    # Get predictions
    predict_response = model.predict(predict_dataset)
    predict_dataset['demand'] = predict_response
    return predict_dataset, mean_absolute_error(y_test, model.predict(X_test))

def build_mlp_regressor_model():
    """ Build Multi-Layer Perceptron Regressor """
    X_train, X_test, y_train, y_test, predict_dataset = split_dataset()
    model = MLPRegressor(hidden_layer_sizes=(32,16),
                         alpha=1e-3,
                         early_stopping=True,
                         max_iter=1000,
                         random_state=42)
    model.fit(X_train, y_train)

    # Analyze results
    print("Model MAE: ", mean_absolute_error(y_test, model.predict(X_test)))

    # Get predictions
    predict_response = model.predict(predict_dataset)
    predict_dataset['demand'] = predict_response
    return predict_dataset, mean_absolute_error(y_test, model.predict(X_test))

def return_best_predictor():
    """
    Since we had two methods, the one with the smallest MAE will be selected for the model
    """
    mlp, mlp_mae = build_mlp_regressor_model()
    gradboost, gradboost_mae = build_gradient_boosting_model()

    # Set timestamps back to ISO format
    mlp.index = mlp.index.strftime("%Y-%m-%dT%H:%MZ")
    gradboost.index = gradboost.index.strftime("%Y-%m-%dT%H:%MZ")
    if mlp_mae > gradboost_mae:
        print("Using predicted values from Gradient Booster")
        return gradboost
    else:
        print("Using predicted values from Multi-Layer Perceptron")
        return mlp

if __name__ == '__main__':
    return_best_predictor()