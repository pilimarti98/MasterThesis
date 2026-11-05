from InputData.DataRequests.request_all_data import align_data_by_timestamp
from scentree.io import StageColumnsMapping
from scentree.io.loader import Dataset, DatasetsLoader
from scentree.fan_generator import StageManager
from scentree.tree_construction.ftc import FTC
from scentree.io.writer import save_json

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

df = align_data_by_timestamp()

# Datasets from merged data, where demand and pv generation are the specific datasets to get predictions from
datasets = [
    Dataset(
        name='demand',
        values=df['demand'],
        stage_ids=len(df),
    ),
    Dataset(
        name='pv_gen',
        values=df['pv_gen'],
        stage_ids=len(df),
    )
]
dataset_loader = DatasetsLoader(datasets=datasets)
full_values = dataset_loader.get_full_values()
num_variables_per_stage = dataset_loader.get_num_variables_per_stage()
stage_ids = dataset_loader.get_sorted_stage_ids()
map_columns_names = dataset_loader.create_dataset_column_mapping()

num_fans = 4
num_scenarios = 10
stage_manager = StageManager()
scenario_fans = stage_manager.generate_scenario_fans(
    X=full_values,
    num_fans=num_fans,
    num_scenarios=num_scenarios,
)

tree_builder = FTC(
    scenarios=scenario_fans["scenarios"],
    num_variables_per_stage=num_variables_per_stage,
    stage_ids=stage_ids
)
scenario_trees = tree_builder.generate_scenario_trees(initial_stage_id_to_cluster=1, stage_columns_mapping='')

save_json(
    output_dir=".",
    num_stages=len(stage_ids),
    predicted_value=scenario_fans["predicted_values"],
    observed_value=scenario_fans["observed_values"],
    scenario_trees=scenario_trees,
    mapping_datasets_columns=map_columns_names,
    multiple_files=True,
)