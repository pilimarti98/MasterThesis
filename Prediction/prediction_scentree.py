import numpy as np
from scentree.io import StageColumnsMapping

from scentree.io.loader import Dataset, DatasetsLoader
from scentree.fan_generator import StageManager
from scentree.tree_construction.ftc import FTC
from scentree.io.writer import save_json

np.random.seed(42)
X_a = np.random.normal(size=(50, 5))
X_b = np.random.normal(size=(50, 3))


datasets = [
    Dataset(
        name="a",
        values=X_a,
        stage_ids=[1, 1, 1, 2, 3],
    ),
    Dataset(
        name="b",
        values=X_b,
        stage_ids=[1, 2, 3],
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
scenario_trees = tree_builder.generate_scenario_trees(initial_stage_id_to_cluster=1)

save_json(
    output_dir=".",
    num_stages=len(stage_ids),
    predicted_value=scenario_fans["predicted_values"],
    observed_value=scenario_fans["observed_values"],
    scenario_trees=scenario_trees,
    mapping_datasets_columns=map_columns_names,
    multiple_files=True,
)