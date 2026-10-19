import pandas as pd
import requests
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
            df = df.rename(columns={'periodStart': 'Start Date'})
            df = df.drop(columns=['productionKwh'])
            df.to_csv(f"C:/Users/pilim/Documents/PythonProjects/MasterThesis/Data/consumption_{start_meter[:10]}.csv")
            return df

if __name__ == "__main__":
    start = '2026-10-10T00:00:00.000Z'
    end = '2026-10-20T00:00:00.000Z'
    convert_to_csv(start_meter=start, end_meter=end)
