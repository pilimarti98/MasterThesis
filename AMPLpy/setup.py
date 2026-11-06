from amplpy import AMPL, modules

from config.config import CONFIG
from InputData.DataRequests.request_all_data import align_future_data
from InputData.helper.data_helper import float_converter

def run_ampl():
    """ Option to run AMPL ems.run locally"""
    ampl = AMPL()
    ampl.read(f'{CONFIG["ENV"]["PATH_TO_DIR"]}/AMPL_Thesis/ems.run')

    sell = ampl.get_variable("Sell").get_values().to_pandas()
    buy = ampl.get_variable("Buy").get_values().to_pandas()
    store = ampl.get_variable("Store").get_values().to_pandas()
    cost = ampl.get_objective("Total_Cost").value

    print('Total cost:', cost)
    print(sell.join(buy, lsuffix='_sell', rsuffix='_buy'))

def run_ampl_model():
    """ Option to run the ems.mod file """
    df = align_future_data()

    ampl = AMPL()
    ampl.read(f'{CONFIG["ENV"]["PATH_TO_DIR"]}/AMPL_Thesis/ems.mod')

    ampl.param['Timestamp'] = len(df)
    ampl.param['agg_rate'] = float_converter("AGG_RATE")
    ampl.param['dem_rate'] = float_converter("DEMAND_RATE")
    ampl.param['store0'] = float_converter("INITIAL_STORING")
    ampl.param['battery_capacity'] = float_converter("BATTERY_CAPACITY")

    for name in ['pv_gen', 'demand', 'market_price']:
        ampl.get_parameter(name).set_values(df[name])

    ampl.option['solver'] = 'minos'
    ampl.option['minos_options'] = 'outlev=1'
    ampl.solve()

    print(ampl.get_value('solve_result'))
    print(ampl.get_objective('Total_Benefit').value())

if __name__ == '__main__':
    run_ampl_model()