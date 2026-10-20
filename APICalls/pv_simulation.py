import openmeteo_requests
import pandas as pd
import logging

from config.config import CONFIG

def call_open_meteo_api(start_date:str=None, end_date:str=None):
	# Setup the Open-Meteo API client with cache and retry on error
	openmeteo = openmeteo_requests.Client()

	# Make sure all required weather variables are listed here
	# The order of variables in hourly or daily is important to assign them correctly below
	# Location variables are stored in configuration file as they contain sensitive data
	url = "https://api.open-meteo.com/v1/forecast"
	params = {
		"latitude": float(CONFIG["ENV"]["LAT"]),
		"longitude": float(CONFIG["ENV"]["LON"]),
		"elevation": float(CONFIG["ENV"]["ALT"]),
		"hourly": "shortwave_radiation",
		"start_date": start_date,
		"end_date": end_date
	}
	responses = openmeteo.weather_api(url, params = params)

	return responses

def get_pv_data(start_date:str = None, end_date:str = None, offset:str=None, timedelta:str=None):
	""" Get the solar irradiation given parameters latitude, longitude"""

	# Process first location. Add a for-loop for multiple locations or weather models
	response = call_open_meteo_api()[0]
	logging.info(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
	logging.info(f"Elevation: {response.Elevation()} m asl")
	logging.info(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

	# Process hourly data. The order of variables needs to be the same as requested.
	hourly = response.Hourly()
	hourly_shortwave_radiation = hourly.Variables(0).ValuesAsNumpy()

	hourly_data = {
		"date": pd.date_range(
			start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
			end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
			freq = pd.Timedelta(seconds = hourly.Interval()),
			inclusive = "left"
		)}

	hourly_data["shortwave_radiation"] = hourly_shortwave_radiation

	hourly_dataframe = pd.DataFrame(data = hourly_data)
	logging.info("\nHourly data\n", hourly_dataframe)

	hourly_dataframe.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/Data/pv.csv")

if __name__ == "__main__":
	start = "2026-10-13"
	end = "2026-10-27"
	get_pv_data(start_date=start, end_date=end)