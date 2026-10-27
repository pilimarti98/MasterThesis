"""
Solar prediction can be done via a combination of:
Open Meteo forecast values + PVLib simulation based on the forecasted values
"""
import pandas as pd
import pvlib.location
from datetime import datetime, timedelta

from APICalls.helper import float_converter, get_dates
from APICalls.weather_and_solar import historical_weather, forecast_weather
from config.config import CONFIG

def simulate_pv(wx: pd.DataFrame, forecast:bool = False):
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
    result.index = result.index.strftime("%Y-%m-%dT%H:%MZ")
    if forecast:
        result.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/Data/forecast_pv_gen.csv")
        result.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/MasterThesisRStudio/Data/forecast_pv_gen.csv")  # Save to RStudio project
    else:
        result.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/Data/historical_pv_gen.csv")
        result.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/MasterThesisRStudio/Data/historical_pv_gen.csv") # Save to RStudio project
    return result

def get_pv_simulation(start_weather:str, end_weather:str):
    """ Function to get both historical and forecast pv generation values. """
    forecast_start = datetime.strptime(start_weather, "%Y-%m-%d")
    forecast_end = forecast_start + timedelta(days=1)
    forecast_start = datetime.strftime(forecast_start, "%Y-%m-%d")
    forecast_end = datetime.strftime(forecast_end, "%Y-%m-%d")

    # Get the solar data
    historical = historical_weather(start_date=start_weather, end_date=end_weather)
    forecast = forecast_weather(start_date=forecast_start, end_date=forecast_end)

    # Simulate and store results
    simulate_pv(historical)
    simulate_pv(forecast, forecast=True)

if __name__ == '__main__':
    start, end = get_dates(offset=CONFIG["ENV"]["OFFSET"], timedelta=CONFIG["ENV"]["TIMEDELTA"], to_open_meteo=True)
    get_pv_simulation(start_weather=start, end_weather=end)