# -*- coding: utf-8 -*-
import sys
from functools import partial
from pathlib import Path

import pandas as pd
import shapely as shp
from shapely.affinity import translate
from tqdm.contrib.concurrent import process_map

sys.path.append(".")

from multiants import Model
from multiants.logger import Logger, NoLogger
from multiants.config import load_config

sys.path.append("./model")

from models.valenicina import Valenicina
from learn.valenicina import Problem as ValenicinaProblem

from models.sn7 import SN7
from learn.sn7 import Problem as SN7Problem

from agents.dwelling import Dwelling

MODELS = {
    "valenicina": (Valenicina, ValenicinaProblem),
    "spacenet7": (SN7, SN7Problem),
}


def init_model(config: dict, params, enable_logs=False, model="spacenet7") -> Model:
    """Setup the model with the start date."""
    logger = Logger() if enable_logs else NoLogger()
    model_cls, problem_cls = MODELS[model]
    model = model_cls(config, logger)
    model.change_influences(params)

    return model


def dummy_building(edge_size: float = 4.5) -> shp.Polygon:
    return shp.Polygon(
        [
            (-edge_size / 2, -edge_size / 2),
            (-edge_size / 2, edge_size / 2),
            (edge_size / 2, edge_size / 2),
            (edge_size / 2, -edge_size / 2),
        ]
    )


def calculate_influence(model, building, use_dummy_building=False):
    influence = model.influences["HouseBuilding"]
    centroid = building.centroid
    if use_dummy_building:
        context = {"shape": dummy_building()}
    else:
        context = {"shape": translate(building, xoff=-centroid.x, yoff=-centroid.y)}
    return influence.compute_influences(context, centroid)


def get_config_path(dataset_name, model_name):
    if model_name == "spacenet7":
        return Path("model/config/sn7") / dataset_name / "all.toml"
    else:
        raise NotImplementedError


def sample_influences(row, model_name):
    model_cls, problem_cls = MODELS[model_name]
    config_path = get_config_path(row["dataset"], model_name)

    config = load_config(config_path)
    params = list(row[problem_cls.params_names()])
    validation = problem_cls.parse_config__get_validation_dataset(config)

    model = init_model(config, params, enable_logs=False)

    start = model.grid.get_agents_as_GeoDataFrame(Dwelling)
    validation_buildings = validation.loc[~validation.intersects(start.union_all())]

    errors: int = 0
    # for each new building
    for building in validation_buildings.geometry:
        if calculate_influence(model, building) == -1:
            # if the value is -1 count an error
            errors += 1
    # return to total number of errors divided by the number of new buildings
    return errors / (len(validation_buildings) or 1)


def calculate_influence_error(results, n_proc=4, model="spacenet7"):
    error = process_map(
        partial(sample_influences, model_name=model),
        [row for _, row in results.iterrows()],
        max_workers=n_proc,
        chunksize=1,
    )

    influence_error = pd.DataFrame(
        {"influence_error": error},
        index=results.index,
    )

    return pd.concat((results, influence_error), axis="columns")


if __name__ == "__main__":
    RESULTS_PATH = Path("results/combined.parquet")
    OUTPUT_PATH = Path("influence_error.parquet")
    N_CPU = 10

    results = pd.read_parquet(RESULTS_PATH)
    results_with_error = calculate_influence_error(results, n_proc=N_CPU)
    results_with_error.to_parquet(OUTPUT_PATH)
