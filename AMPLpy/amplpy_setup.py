from amplpy import AMPL, modules

from config.config import CONFIG
from InputData.DataRequests.request_all_data import align_future_data
from InputData.helper.data_helper import float_converter

def run_ampl():
    """ Option to run AMPL ems.run locally"""
    ampl = AMPL()
    ampl.read('ems.run')

    sell = ampl.get_variable("Sell").get_values().to_pandas()
    buy = ampl.get_variable("Buy").get_values().to_pandas()
    store = ampl.get_variable("Store").get_values().to_pandas()
    benefit = ampl.get_objective("Total_Benefit").value

    print('Total Benefit:', benefit)
    print(sell.join(buy, lsuffix='_sell', rsuffix='_buy'))

if __name__ == '__main__':
    run_ampl()