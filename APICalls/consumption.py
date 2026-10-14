import pandas as pd
import requests

TOKEN_URL = ""
API = ""
CLIENT_ID = ""
CLIENT_SECRET = ""

def get_token() -> str:
    r = requests.post(TOKEN_URL, data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }, timeout=30)
    r.raise_for_status()
    return r.json()['access_token']

def get_metering_data(data_token, start_data, end_data, resolution="one_hour", eics=None):
    # Limits: max 31 dats and 10 EICs per request, ~1 request/ 5s
    params = {"startDateTime":start_data, "endDateTime": end_data, "resolution": resolution}
    if eics:
        params["meteringPointEics"] = ",".join(eics)
    r = requests.get(f"{API}/metering-data", params=params,
                     headers={"Authorization": f"Bearer {data_token}"}, timeout=30
                     )
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    token=get_token()
    start = '2026-10-01T20:59:59Z'
    end = '2026-10-10T20:59:59Z'
    data = get_metering_data(token, start, end)
    for meter in data:
        if meter.get("error"):
            print(meter["meteringPointEic"], "ERROR:", meter["error"]["message"])
            continue
        else:
            df = pd.DataFrame(meter['accountingIntervals'])
            df = df.rename(columns={'periodStart':'Start Date'})
            df = df.drop(columns=['productionKwh'])

            df.to_csv(f"C:/Users/pilim/Documents/PythonProjects/MasterThesis/Data/consumption_{start[:10]}_{end[:10]}.csv")
