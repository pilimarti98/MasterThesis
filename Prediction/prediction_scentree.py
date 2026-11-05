import pandas as pd

from scentree.io.loader import Dataset, DatasetsLoader
from scentree.fan_generator import StageManager
from scentree.tree_construction.ftc import FTC

"""
###################################### citation ###############################################
@misc{scentree2026,
  author = {Cristian Pachón-García and Albert Solà Vilalta and F.-Javier Heredia},
  title = {{scentree}},
  subtitle = {a framework for generating scenario trees for multistage stochastic programming},
  url = {https://github.com/mmobec/scentree},
  year = {2026}
}
"""

df = pd.read_csv(r"C:\Users\pilim\Documents\PythonProjects\MasterThesis\InputData\Data\merged.csv", parse_dates=["Timestamp"], index_col="Timestamp")
df = df.tz_convert("UTC") if df.index.tz else df     # avoids 23/25-hour DST days

df["date"], df["hour"] = df.index.date, df.index.hour

def to_daily(col):
    m = df.pivot(index="date", columns="hour", values=col)
    return m.dropna()            # drop incomplete days

price = to_daily('marketprice')
demand = to_daily('demand')
solar = to_daily('generatedPV')
common = demand.index.intersection(price.index).intersection(solar.index)
demand, price, solar = (x.loc[common].to_numpy() for x in (demand, price, solar))

# Stages are your modelling choice. Example: price is stage 1 (day-ahead
# bid), consumption and solar are stage 2.
datasets = [
    Dataset(name="price",       values=price, stage_ids=24*[1]),
    Dataset(name="consumption", values=demand,  stage_ids=24*[2]),
    Dataset(name="solar_ac",    values=solar, stage_ids=24*[2]),
]
dsl = DatasetsLoader(datasets=datasets)
X            = dsl.get_full_values()
num_vars     = dsl.get_num_variables_per_stage()
stage_ids    = dsl.get_sorted_stage_ids()
col_map      = dsl.create_stages_columns_mapping()

fans = StageManager().generate_scenario_fans(
    X=X,
    num_fans=1,                  # 1 = a single day
    num_scenarios=50,
    build_in_sample_fans=False,  # False = forecast the NEXT day; True = backtest on the last day(s)
    seed=123,
)

trees = FTC(
    scenarios=fans["scenarios"],
    num_variables_per_stage=num_vars,
    stage_ids=stage_ids,
).generate_scenario_trees(initial_stage_id_to_cluster=1)