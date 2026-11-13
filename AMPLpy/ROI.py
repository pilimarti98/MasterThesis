import pandas as pd

from AMPLpy.amplpy_setup import projected_yearly_benefits
from config.config import CONFIG


def roi_params():
    roi_params_dict = {
        '5':    {'solar_purchase_cost': 3000,
              'battery_purchase_cost': 3500,
              'solar_installation_fee': 1500,
              'battery_installation_fee': 750,
              'solar_annual_maintenance': 100,
              'battery_annual_maintenance': 50,
              'years': 20},
        '10': {'solar_purchase_cost': 6000,
              'battery_purchase_cost': 3500,
              'solar_installation_fee': 3000,
              'battery_installation_fee': 750,
              'solar_annual_maintenance': 150,
              'battery_annual_maintenance': 50,
              'years': 20},
        '50': {'solar_purchase_cost': 25000,
              'battery_purchase_cost': 3500,
              'solar_installation_fee': 10000,
              'battery_installation_fee': 750,
              'solar_annual_maintenance': 600,
              'battery_annual_maintenance': 50,
              'years': 20},
        '100': {'solar_purchase_cost': 45000,
              'battery_purchase_cost': 3500,
              'solar_installation_fee': 20000,
              'battery_installation_fee': 750,
              'solar_annual_maintenance': 1200,
              'battery_annual_maintenance': 50,
              'years': 20}
    }
    dates = [[2025, 11],[2025, 12],[2026, 1],[2026, 2],[2026, 3],[2026, 4],
        [2026, 5],[2026, 6],[2026, 7],[2026, 8],[2026, 9],[2026, 10],[2026, 11]]
    pw_cases = [5,10,50,100]
    return roi_params_dict, dates, pw_cases

def solar_battery_roi():
    """
    Return the ROI (as a percentage) of a solar panel + battery system.
    ROI = (total benefit - total cost) / total cost * 100
    """
    roi_params_dict, dates, pw_cases = roi_params()
    results_df = pd.DataFrame()
    for pw in pw_cases:
        years = roi_params_dict[str(pw)]['years']
        solar_purchase_cost = roi_params_dict[str(pw)]['solar_purchase_cost']
        battery_purchase_cost = roi_params_dict[str(pw)]['battery_purchase_cost']
        solar_installation_fee = roi_params_dict[str(pw)]['solar_installation_fee']
        battery_installation_fee = roi_params_dict[str(pw)]['battery_installation_fee']
        solar_annual_maintenance = roi_params_dict[str(pw)]['solar_annual_maintenance']
        battery_annual_maintenance = roi_params_dict[str(pw)]['battery_annual_maintenance']
        if int(years) <= 0:
            raise ValueError("years must be a positive number")

        upfront_cost = (
            solar_purchase_cost
            + battery_purchase_cost
            + solar_installation_fee
            + battery_installation_fee
        )
        total_maintenance = (solar_annual_maintenance + battery_annual_maintenance) * years
        total_cost = upfront_cost + total_maintenance

        if total_cost <= 0:
            raise ValueError("total cost must be greater than zero")
        annual_benefit = 0
        for year, month in dates:
            base_case_cost, battery_cost, ems_cost = projected_yearly_benefits(year=year, month=month, pw=pw)
            monthly_benefit = base_case_cost + ems_cost
            annual_benefit += monthly_benefit

        total_benefit = annual_benefit * years
        print((total_benefit - total_cost) / total_cost * 100)
        roi = (total_benefit - total_cost) / total_cost * 100
        results_df[f'{pw}kWh_roi'] = roi,
    results_df.to_csv(f'{CONFIG["ENV"]["PATH_TO_DIR"]}/Results/roi.csv')

if __name__ == "__main__":
    roi = solar_battery_roi()