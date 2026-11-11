import pandas as pd
from amplpy import AMPL, modules
from string import Template
from pathlib import Path
import calendar

from config.config import CONFIG

BASE_CASE_RUN = Template("""\
reset;
model base_case.mod;
data ${year}_${month}_${pw}_ems.dat;
option solver minos; 
solve;

display Total_Cost;
display {t in 1..Timestamp}(Buy[t], demand[t]);
""")

ONLY_BATTERY_RUN = Template("""\
reset;
model only_battery.mod;
data ${year}_${month}_${pw}_ems.dat;
option solver minos; 
solve;

display Total_Cost;
display {t in 1..Timestamp}(Discharge[t], SoC[t], Buy[t], Sell[t], Store[t], demand[t]);
""")

EMS_RUN = Template("""\
reset;
model ems.mod;
data ${year}_${month}_${pw}_ems.dat;
option solver minos; 
solve;

display Total_Benefit;
display {t in 1..Timestamp}(pv_gen[t], Discharge[t], SoC[t], Buy[t], Sell[t], Store[t], demand[t]);
""")

def run_ampl(year:str, month:str, pw:int):
    """ Simulate the different scenarios: No EMS, Only battery, full EMS """
    # First scenario: No Battery or PV
    base_case_path = Path(f"{year}_{month}_{str(pw)}_base_case.run")
    base_case_path.write_text(
        BASE_CASE_RUN.substitute(year=year, month=month, pw=str(pw)),
        encoding='utf-8'
    )
    ampl = AMPL()
    ampl.read(str(base_case_path))
    buy = ampl.get_variable("Buy").get_values().to_pandas()
    market_price = ampl.get_parameter("market_price").get_values().to_pandas()
    base_case_cost = ampl.get_objective("Total_Cost").value()
    base_case_df = pd.DataFrame()
    base_case_df['Buy[t]'] = buy
    base_case_df['market_price[t]'] = market_price



    # Second scenario: Only Battery (No PV)
    only_battery_path = Path(f"{year}_{month}_{str(pw)}_only_battery.run")
    only_battery_path.write_text(
        ONLY_BATTERY_RUN.substitute(year=year, month=month, pw=str(pw)),
        encoding='utf-8'
    )
    ampl = AMPL()
    ampl.read(str(only_battery_path))
    buy = ampl.get_variable("Buy").get_values().to_pandas()
    store = ampl.get_variable("Store").get_values().to_pandas()
    discharge = ampl.get_variable("Discharge").get_values().to_pandas()
    soc = ampl.get_variable("SoC").get_values().to_pandas()
    market_price = ampl.get_parameter("market_price").get_values().to_pandas()
    battery_cost = ampl.get_objective("Total_Cost").value()
    battery_df = pd.DataFrame()
    battery_df['Buy[t]'] = buy
    battery_df['Store[t]'] = store
    battery_df['Discharge[t]'] = discharge
    battery_df['SoC[t]'] = soc
    base_case_df['market_price[t]'] = market_price



    # Third scenario: Full System (Battery + PV)
    ems_path = Path(f"{year}_{month}_{str(pw)}_ems.run")
    ems_path.write_text(
        EMS_RUN.substitute(year=year, month=month, pw=str(pw)),
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
    market_price = ampl.get_parameter("market_price").get_values().to_pandas()
    ems_df = pd.DataFrame()
    ems_df['Sell[t]'] = sell
    ems_df['Buy[t]'] = buy
    ems_df['Store[t]'] = store
    ems_df['Discharge[t]'] = discharge
    ems_df['SoC[t]'] = soc
    base_case_df['market_price[t]'] = market_price

    return base_case_df, battery_df, ems_df, base_case_cost, battery_cost, ems_benefit

def projected_yearly_benefits(year:int, month:int, pw:int = 5):
    """ Simplified economical assessment for the previous year """
    base_case_df, battery_df, ems_df, base_case_cost, battery_cost, ems_benefit = run_ampl(str(year), str(month), pw=pw)

    # Process Base Case
    base_case_cost_per_month = base_case_cost * calendar.monthrange(year, month)[1]
    # Store dfs to Results dir
    base_case_df.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/Results/{pw}/BaseCase/{str(year)}{str(month)}_basecase.csv")

    # Process Battery
    battery_cost_per_month = battery_cost * calendar.monthrange(year, month)[1]
    # Store dfs to Results dir
    battery_df.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/Results/{pw}/Battery/{str(year)}{str(month)}_battery.csv")

    # Process EMS
    ems_cost_per_month = ems_benefit * calendar.monthrange(year, month)[1]
    # Store dfs to Results dir
    ems_df.to_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/Results/{pw}/EMS/{str(year)}{str(month)}_ems.csv")
    return base_case_cost_per_month, battery_cost_per_month, ems_cost_per_month