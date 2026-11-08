import pandas as pd
from amplpy import AMPL, modules

def run_ampl():
    """ Option to run AMPL ems.run locally"""
    ampl = AMPL()
    ampl.read('ems.run')

    sell = ampl.get_variable("Sell").get_values().to_pandas()
    buy = ampl.get_variable("Buy").get_values().to_pandas()
    store = ampl.get_variable("Store").get_values().to_pandas()
    benefit = ampl.get_objective("Total_Benefit").value

    df = pd.DataFrame()
    df['Sell[t]'] = sell
    df['Buy[t]'] = buy
    df['Store[t]'] = store

    print('Total Benefit:', benefit)

    return df, benefit

if __name__ == '__main__':
    run_ampl()