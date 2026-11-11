import pandas as pd
from amplpy import AMPL, modules
from string import Template
from pathlib import Path

RUN_TEMPLATE = Template("""\
reset;
model ems.mod;
data ${year}_${month}_ems.dat;
option solver minos; 
solve;

display Total_Benefit;
display {t in 1..Timestamp}(pv_gen[t], Store[t-1], Buy[t], Sell[t], Store[t], demand[t]);
""")

def create_run(year:str,month:str) -> str:
    run_path = Path(f"{year}_{month}_ems.run")
    run_path.write_text(
        RUN_TEMPLATE.substitute(year=year, month=month),
        encoding='utf-8'
    )
    return str(run_path)

def run_ampl(year:str, month:str):
    """ Option to run any AMPL ems.run locally"""
    ampl = AMPL()
    run_file = create_run(year,month)
    ampl.read(run_file)

    sell = ampl.get_variable("Sell").get_values().to_pandas()
    buy = ampl.get_variable("Buy").get_values().to_pandas()
    store = ampl.get_variable("Store").get_values().to_pandas()
    benefit = ampl.get_objective("Total_Benefit").value()

    df = pd.DataFrame()
    df['Sell[t]'] = sell
    df['Buy[t]'] = buy
    df['Store[t]'] = store

    print('Total Benefit:', benefit)

    return df, benefit

def only_battery_sim():
    """ Remove battery data """

def base_sim():
    """ Generate simulation without EMS """

import calendar
def run_month_sample(dates):
    yr_benefit = 0.0
    benefit_per_month = []
    for year, month in dates:
        _, benefit = run_ampl(str(year), str(month))
        benefit_per_month.append(benefit * calendar.monthrange(year, month)[1])
        yr_benefit += float(benefit * calendar.monthrange(year, month)[1])
    return yr_benefit

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
    run_month_sample(dates=previous_yr_dates)