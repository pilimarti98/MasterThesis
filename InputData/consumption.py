import pandas as pd
import requests

from InputData.helper import get_dates
from config.config import CONFIG


def get_token() -> str:
    r = requests.post(CONFIG["ENV"]["TOKEN_URL"], data={
        "grant_type": "client_credentials",
        "client_id": CONFIG["ENV"]["CLIENT_ID"],
        "client_secret": CONFIG["ENV"]["CLIENT_SECRET"],
    }, timeout=30)
    r.raise_for_status()
    return r.json()['access_token']

def get_metering_data(data_token, start_data, end_data, resolution="one_hour", eics=None):
    # Limits: max 31 dats and 10 EICs per request, ~1 request/ 5s
    params = {"startDateTime":start_data, "endDateTime": end_data, "resolution": resolution}
    if eics:
        params["meteringPointEics"] = ",".join(eics)
    r = requests.get(f"{CONFIG["ENV"]["API"]}/metering-data", params=params,
                     headers={"Authorization": f"Bearer {data_token}"}, timeout=30
                     )
    r.raise_for_status()
    return r.json()

def convert_to_csv(start_meter:str, end_meter:str):
    token = get_token()
    data = get_metering_data(token, start_meter, end_meter)
    for meter in data:
        if meter.get("error"):
            print(meter["meteringPointEic"], "ERROR:", meter["error"]["message"])
            continue
        else:
            df = pd.DataFrame(meter['accountingIntervals'])
            df = df.rename(columns={'periodStart': 'Timestamp', 'consumptionKwh': 'Consumption [kWh]'})
            df = df.drop(columns=['productionKwh'])
            df["Timestamp"] = (pd.to_datetime(df["Timestamp"]))
            df["Timestamp"] = df["Timestamp"].dt.strftime("%Y-%m-%dT%H:%MZ")
            df.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/historical_consumption.csv")
            df.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/MasterThesisRStudio/Data/historical_consumption.csv") # Save to RStudio project
            return df

if __name__ == "__main__":
    start, end = get_dates(offset=CONFIG["ENV"]["OFFSET"], timedelta=CONFIG["ENV"]["TIMEDELTA"])
    convert_to_csv(start_meter=start, end_meter=end)
