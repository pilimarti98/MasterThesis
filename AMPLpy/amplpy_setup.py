import pandas as pd
from amplpy import AMPL, modules
from string import Template
from pathlib import Path
import calendar

from config.config import CONFIG

BASE_CASE_RUN = Template("""\
reset;
model base_case.mod;
data ${year}_${month}_ems.dat;
option solver minos; 
solve;

display Total_Cost;
display {t in 1..Timestamp}(Buy[t], demand[t]);
""")

ONLY_BATTERY_RUN = Template("""\
reset;
model only_battery.mod;
data ${year}_${month}_ems.dat;
option solver minos; 
solve;

display Total_Cost;
display {t in 1..Timestamp}(Discharge[t], SoC[t], Buy[t], Sell[t], Store[t], demand[t]);
""")

EMS_RUN = Template("""\
reset;
model ems.mod;
data ${year}_${month}_ems.dat;
option solver minos; 
solve;

display Total_Benefit;
display {t in 1..Timestamp}(pv_gen[t], Discharge[t], SoC[t], Buy[t], Sell[t], Store[t], demand[t]);
""")

def run_ampl(year:str, month:str):
    """ Simulate the different scenarios: No EMS, Only battery, full EMS """
    # First scenario: No Battery or PV
    base_case_path = Path(f"{year}_{month}_base_case.run")
    base_case_path.write_text(
        BASE_CASE_RUN.substitute(year=year, month=month),
        encoding='utf-8'
    )
    ampl = AMPL()
    ampl.read(str(base_case_path))
    buy = ampl.get_variable("Buy").get_values().to_pandas()
    base_case_cost = ampl.get_objective("Total_Cost").value()
    base_case_df = pd.DataFrame()
    base_case_df['Buy[t]'] = buy



    # Second scenario: Only Battery (No PV)
    only_battery_path = Path(f"{year}_{month}_only_battery.run")
    only_battery_path.write_text(
        ONLY_BATTERY_RUN.substitute(year=year, month=month),
        encoding='utf-8'
    )
    ampl = AMPL()
    ampl.read(str(only_battery_path))
    buy = ampl.get_variable("Buy").get_values().to_pandas()
    store = ampl.get_variable("Store").get_values().to_pandas()
    discharge = ampl.get_variable("Discharge").get_values().to_pandas()
    soc = ampl.get_variable("SoC").get_values().to_pandas()
    battery_cost = ampl.get_objective("Total_Cost").value()
    battery_df = pd.DataFrame()
    battery_df['Buy[t]'] = buy
    battery_df['Store[t]'] = store
    battery_df['Discharge[t]'] = discharge
    battery_df['SoC[t]'] = soc



    # Third scenario: Full System (Battery + PV)
    ems_path = Path(f"{year}_{month}_ems.run")
    ems_path.write_text(
        EMS_RUN.substitute(year=year, month=month),
        encoding='utf-8'
    )
    ampl = AMPL()
    ampl.read(str(ems_path))
    sell = ampl.get_variable("Sell").get_values().to_pandas()
    buy = ampl.get_variable("Buy").get_values().to_pandas()
    store = ampl.get_variable("Store").get_values().to_pandas()
    discharge = ampl.get_variable("Discharge").get_values().to_pandas()
    soc = ampl.get_variable("SoC").get_values().to_pandas()
    ems_benefit = ampl.get_objective("Total_Benefit").value()
    ems_df = pd.DataFrame()
    ems_df['Sell[t]'] = sell
    ems_df['Buy[t]'] = buy
    ems_df['Store[t]'] = store
    ems_df['Discharge[t]'] = discharge
    ems_df['SoC[t]'] = soc

    return base_case_df, battery_df, ems_df, base_case_cost, battery_cost, ems_benefit

def projected_yearly_benefits(dates):
    """ Simplified economical assessment for the previous year """
    yr_benefit = 0.0
    benefit_per_month = {}
    for year, month in dates:
        base_case_df, battery_df, ems_df, base_case_cost, battery_cost, ems_benefit = run_ampl(str(year), str(month))
        monthly_benefit = ems_benefit * calendar.monthrange(year, month)[1]
        benefit_per_month[f"{year}_{month}"] = monthly_benefit
        yr_benefit += float(ems_benefit * calendar.monthrange(year, month)[1])
        # Store dfs to Results dir
        base_case_df.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/Results/{year}{month}_basecase.csv")
        battery_df.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/Results/{year}{month}_battery.csv")
        ems_df.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/Results/{year}{month}_ems.csv")
    print(benefit_per_month, yr_benefit)
    return benefit_per_month, yr_benefit

if __name__ == '__main__':
    previous_yr_dates = [
        [2025, 11],
        [2025, 12],
        [2026, 1],
        [2026, 2],
        [2026, 3],
        [2026, 4],
        [2026, 5],
        [2026, 6],
        [2026, 7],
        [2026, 8],
        [2026, 9],
        [2026, 10],
        [2026, 11]
    ]
    projected_yearly_benefits(dates=previous_yr_dates)