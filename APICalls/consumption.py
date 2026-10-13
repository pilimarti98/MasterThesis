from datetime import datetime, timedelta, timezone

import requests



def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def get_token() -> str:
    r = requests.post(TOKEN_URL, data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }, timeout=30)
    r.raise_for_status()
    return r.json()['access_token']

def get_metering_data(token, start, end, resolution="one_hour", eics=None):
    # Limits: max 31 dats and 10 EICs per request, ~1 request/ 5s
    params = {"startDateTime":iso(start), "endDateTime": iso(end), "resolution": resolution}
    if eics:
        params["meteringPointEics"] = ",".join(eics)
    r = requests.get(f"{API}/metering-data", params=params,
                     headers={"Authorization": f"Bearer {token}"}, timeout=30
                     )
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    token=get_token()
    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    data = get_metering_data(token, end - timedelta(days=1), end)
    for meter in data:
        if meter.get("error"):
            print(meter["meteringPointEic"], "ERROR:", meter["error"]["message"])
            continue
