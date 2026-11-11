import pandas as pd
import pvlib.location
from datetime import date, datetime

from InputData.helper.data_helper import float_converter, get_day_ahead
from InputData.DataRequests.weather_and_solar import historical_weather, forecast_weather
from config.config import CONFIG

"""
Solar prediction can be done via a combination of:
Open Meteo forecast values + PVLib simulation based on the forecasted values
"""

def simulate_pv(wx: pd.DataFrame, forecast:bool = False, pdc0:float=None):
    """ Given the fetched data, simulate as the generation of a solar panel with given characteristics """
    location = pvlib.location.Location(float_converter("LAT"), float_converter("LON"), altitude=float_converter("ALT"), tz="UTC")

    # Open-Meteo radiation returns a mean value for the preceding hour
    # Computing the sun position in the middle of that hour
    sol_pos = location.get_solarposition(wx.index - pd.Timedelta("30 min"))
    sol_pos.index = wx.index
    if pdc0 is None:
        pdc0 = float_converter("PDC0_KW")
    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=float_converter("TILT"), surface_azimuth=float_converter("AZIMUTH"),
        solar_zenith=sol_pos["apparent_zenith"], solar_azimuth=sol_pos["azimuth"],
        dni=wx["dni"], ghi=wx["ghi"], dhi=wx["dhi"],
        dni_extra=pvlib.irradiance.get_extra_radiation(wx.index),
        model="haydavies")

    t_params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS["sapm"]["open_rack_glass_glass"]
    t_cell = pvlib.temperature.sapm_cell(poa["poa_global"], wx["temperature_air"],
                                         wx["wind_speed"], **t_params)

    dc_kw = pvlib.pvsystem.pvwatts_dc(poa["poa_global"], t_cell, pdc0, float_converter("GAMMA_PDC"))
    dc_kw *= (1 - float_converter("LOSSES"))
    ac_kw = pvlib.inverter.pvwatts(dc_kw, pdc0/ float_converter("DC_AC_RATIO")).clip(lower=0)

    result = pd.DataFrame({"poa_wm2": poa["poa_global"], "t_cell":t_cell,
                         "dc_kw": dc_kw, "ac_kw":ac_kw})
    start_date = pd.to_datetime(result.index[0])
    year = str(start_date.year)
    month = str(start_date.month)
    result.index = result.index.strftime("%Y-%m-%dT%H:%MZ")
    if forecast:
        result.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/PV_Gen/{year}_{month}_forecast_pv_gen.csv")
    else:
        result.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/PV_Gen/{year}_{month}_pv_gen.csv")
    return result

def get_pv_simulation(start_weather:str=CONFIG["ENV"]["START_DATE"], end_weather:str=CONFIG["ENV"]["END_DATE"], pdc0:float=None):
    """ Function to get both historical and forecast pv generation values. """
    # Get the solar data
    start_weather, end_weather = start_weather[:10], end_weather[:10]
    forecasted_day = get_day_ahead(last_timestamp=end_weather, to_open_meteo=True)
    end_weather = pd.to_datetime(end_weather) - pd.Timedelta(days=1)
    end_weather = end_weather.strftime("%Y-%m-%d")
    historical = historical_weather(start_date=start_weather, end_date=end_weather)
    d = datetime.strptime(forecasted_day, "%Y-%m-%d").date()
    if d < date.today():
        forecast = historical_weather(start_date=forecasted_day, end_date=forecasted_day)
    else:
        forecast = forecast_weather(start_date=forecasted_day, end_date=forecasted_day)

    # Simulate and store results
    historical_results = simulate_pv(historical, pdc0=pdc0)
    forecast_results = simulate_pv(forecast, forecast=True, pdc0=pdc0)
    return historical_results, forecast_results

if __name__ == '__main__':
    get_pv_simulation()