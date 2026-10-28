import pandas as pd
import requests

from APICalls.helper import float_converter

"""
###################################### citation ###############################################
Anderson, K., Hansen, C., Holmgren, W., Jensen, A., Mikofski, M., and Driesse, A. “pvlib python: 2023 project update.” Journal of Open Source Software, 8(92), 5994, (2023). DOI: 10.21105/joss.05994.
"""

hourly_vars = [
	"shortwave_radiation",
	"direct_normal_irradiance",
	"diffuse_radiation",
	"temperature_2m",
	"wind_speed_10m"
]

def historical_weather(start_date:str, end_date:str):
	""" Get archive data request """
	url = "https://archive-api.open-meteo.com/v1/archive"

	params = {
		"latitude": float_converter("LAT"),
		"longitude": float_converter("LON"),
		"altitude": float_converter("ALT"),
		"hourly": ",".join(hourly_vars),
		"timezone": "UTC",
		"wind_speed_unit":"ms",
		"start_date": start_date,
		"end_date": end_date
	}

	r = requests.get(url, params=params, timeout=300)
	r.raise_for_status()
	h = r.json()["hourly"]
	h["Timestamp"] = h.pop("time")

	df = pd.DataFrame(h).set_index("Timestamp")
	df.index = pd.to_datetime(df.index)
	return df.rename(columns={
		"shortwave_radiation": "ghi",
		"direct_normal_irradiance": "dni",
		"diffuse_radiation": "dhi",
		"temperature_2m": "temperature_air",
		"wind_speed_10m": "wind_speed"}).fillna(0)

def forecast_weather(start_date:str, end_date:str):
	""" Get archive data request """
	url = "https://api.open-meteo.com/v1/forecast"

	params = {
		"latitude": float_converter("LAT"),
		"longitude": float_converter("LON"),
		"altitude": float_converter("ALT"),
		"hourly": ",".join(hourly_vars),
		"timezone": "UTC",
		"wind_speed_unit":"ms",
		"start_date": start_date,
		"end_date": end_date
	}

	r = requests.get(url, params=params, timeout=300)
	r.raise_for_status()
	h = r.json()["hourly"]
	h["Timestamp"] = h.pop("time")

	df = pd.DataFrame(h).set_index("Timestamp")
	df.index = pd.to_datetime(df.index)
	return df.rename(columns={
		"shortwave_radiation": "ghi",
		"direct_normal_irradiance": "dni",
		"diffuse_radiation": "dhi",
		"temperature_2m": "temperature_air",
		"wind_speed_10m": "wind_speed"}).fillna(0)