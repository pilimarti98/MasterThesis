import pandas as pd

from scentree.io.loader import Dataset, DatasetsLoader
from scentree.fan_generator import StageManager
from scentree.tree_construction.ftc import FTC
from scentree.io.writer import save_json

from config.config import CONFIG

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

df = pd.read_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/InputData/Data/merged.csv", parse_dates=["Timestamp"], index_col="Timestamp")
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

# Dataset Loader that converts NumPy arrays into an appropriate internal representation
dataset_loader = DatasetsLoader(datasets=datasets)
X            = dataset_loader.get_full_values()
num_vars     = dataset_loader.get_num_variables_per_stage()
stage_ids    = dataset_loader.get_sorted_stage_ids()
col_map      = dataset_loader.create_stages_columns_mapping()

fans = StageManager().generate_scenario_fans(
    X=X,
    num_fans=1,                  # 1 = a single day
    num_scenarios=10,
    build_in_sample_fans=False,  # False = forecast the NEXT day; True = backtest on the last day(s)
    seed=42,
)

trees = FTC(
    scenarios=fans["scenarios"],
    num_variables_per_stage=num_vars,
    stage_ids=stage_ids,
).generate_scenario_trees(initial_stage_id_to_cluster=1)

save_json(
    output_dir=f"{CONFIG["ENV"]["PATH_TO_DIR"]}/Prediction",
    num_stages=len(stage_ids),
    predicted_value=fans["predicted_values"],
    observed_value=fans["observed_values"],
    scenario_trees=trees,
    mapping_datasets_columns=col_map,
    multiple_files=True,
)