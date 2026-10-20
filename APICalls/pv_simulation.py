import pandas as pd
import pvlib.location
import requests
from PIL.ImageChops import offset

from helper import float_converter, get_dates
from config.config import CONFIG

hourly_vars = [
	"shortwave_radiation",
	"direct_normal_irradiance",
	"diffuse_radiation",
	"temperature_2m",
	"wind_speed_10m"
]

def fetch_weather(start_date:str, end_date:str):
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

	df = pd.DataFrame(h).set_index("time")
	df.index = pd.to_datetime(df.index).tz_localize("EET")
	return df.rename(columns={
		"shortwave_radiation": "ghi",
		"direct_normal_irradiance": "dni",
		"diffuse_radiation": "dhi",
		"temperature_2m": "temperature_air",
		"wind_speed_10m": "wind_speed"}).fillna(0)


def simulate_pv(wx: pd.DataFrame):
	""" Given the fetched data, simulate as the generation of a solar panel with given characteristics """
	location = pvlib.location.Location(float_converter("LAT"), float_converter("LON"), altitude=float_converter("ALT"), tz="UTC")

	# Open-Meteo radiation returns a mean value for the preceding hour
	# Computing the sun position in the middle of that hour
	sol_pos = location.get_solarposition(wx.index - pd.Timedelta("30 min"))
	sol_pos.index = wx.index

	poa = pvlib.irradiance.get_total_irradiance(
		surface_tilt=float_converter("TILT"), surface_azimuth=float_converter("AZIMUTH"),
		solar_zenith=sol_pos["apparent_zenith"], solar_azimuth=sol_pos["azimuth"],
		dni=wx["dni"], ghi=wx["ghi"], dhi=wx["dhi"],
		dni_extra=pvlib.irradiance.get_extra_radiation(wx.index),
		model="haydavies")

	t_params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS["sapm"]["open_rack_glass_glass"]
	t_cell = pvlib.temperature.sapm_cell(poa["poa_global"], wx["temperature_air"],
										 wx["wind_speed"], **t_params)

	dc_kw = pvlib.pvsystem.pvwatts_dc(poa["poa_global"], t_cell, float_converter("PDC0_KW"), float_converter("GAMMA_PDC"))
	dc_kw *= (1 - float_converter("LOSSES"))
	ac_kw = pvlib.inverter.pvwatts(dc_kw, float_converter("PDC0_KW")/ float_converter("DC_AC_RATIO")).clip(lower=0)

	result = pd.DataFrame({"poa_wm2": poa["poa_global"], "t_cell":t_cell,
						 "dc_kw": dc_kw, "ac_kw":ac_kw})
	result.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/Data/pv_gen.csv")

if __name__ == "__main__":
	start, end = get_dates(offset=CONFIG["ENV"]["DATE_OFFSET"], timedelta=CONFIG["ENV"]["TIMEDELTA"], to_open_meteo=True)
	meteo_api = fetch_weather(start_date=start, end_date=end)
	simulate_pv(meteo_api)