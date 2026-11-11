from AMPLpy.amplpy_setup import projected_yearly_benefits

def roi_params():
    solar_purchase_cost = 6000
    battery_purchase_cost = 4000
    solar_installation_fee = 1500
    battery_installation_fee = 500
    solar_annual_maintenance = 100
    battery_annual_maintenance = 50
    years = 10
    dates = [[2025, 11],[2025, 12],[2026, 1],[2026, 2],[2026, 3],[2026, 4],
        [2026, 5],[2026, 6],[2026, 7],[2026, 8],[2026, 9],[2026, 10],[2026, 11]]
    benefit_per_month, annual_benefit = projected_yearly_benefits(dates)
    return solar_purchase_cost,battery_purchase_cost,solar_installation_fee,battery_installation_fee,solar_annual_maintenance,battery_annual_maintenance, annual_benefit, years

def solar_battery_roi() -> float:
    """
    Return the ROI (as a percentage) of a solar panel + battery system.
    ROI = (total benefit - total cost) / total cost * 100
    """
    solar_purchase_cost,battery_purchase_cost,solar_installation_fee,battery_installation_fee,solar_annual_maintenance,battery_annual_maintenance, annual_benefit, years = roi_params()

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

    total_benefit = annual_benefit * years
    return (total_benefit - total_cost) / total_cost * 100


if __name__ == "__main__":
    roi = solar_battery_roi()
    print(f"ROI over 10 years: {roi:.1f}%")