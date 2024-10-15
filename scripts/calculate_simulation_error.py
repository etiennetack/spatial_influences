import sys
from functools import partial
from pathlib import Path
from typing import Type

import numpy as np
import pandas as pd
import geopandas as gpd

from tqdm.contrib.concurrent import process_map
from scipy.spatial import cKDTree

sys.path.append(".")

from multiants import Model, GeoAgent
from multiants.logger import Logger, NoLogger
from multiants.config import load_config
from multiants.influences.gradient import NoValidStartPoint

sys.path.append("./model")

from models.valenicina import Valenicina
from learn.valenicina import Problem as ValenicinaProblem

from models.sn7 import SN7
from learn.sn7 import Problem as SN7Problem

from agents.dwelling import Dwelling
from generation.dwelling_factory import ImpossibleBuild

MODELS = {
    "valenicina": (Valenicina, ValenicinaProblem),
    "spacenet7": (SN7, SN7Problem),
}


def sum_of_min_euclidean_distances(a: gpd.GeoDataFrame, b: gpd.GeoDataFrame) -> float:
    """Return the sum of minimum Euclidean distances between two GeoDataFrames
    based on centroids, ensuring that points in `b` are only used once (without replacement).
    """
    # Extract centroids as NumPy arrays (x, y coordinates)
    centroids_a = np.array(list(zip(a.geometry.centroid.x, a.geometry.centroid.y)))
    centroids_b = np.array(list(zip(b.geometry.centroid.x, b.geometry.centroid.y)))

    # Variable to keep track of the sum of minimum distances
    result = 0.0

    # While there are centroids in both a and b, we match them one by one
    for point in centroids_a:
        # Build KDTree for centroids_b (points left in `b`)
        tree_b = cKDTree(centroids_b)

        # Find the nearest neighbor for the current point in centroids_a
        distance, index = tree_b.query(point, k=1)

        # Add the nearest distance to the result
        result += distance

        # Remove the matched point in centroids_b (without replacement)
        centroids_b = np.delete(centroids_b, index, axis=0)

        # Stop if no more points are available in centroids_b
        if centroids_b.shape[0] == 0:
            break

    return result


def sum_of_min_euclidean_distances2(a: gpd.GeoDataFrame, b: gpd.GeoDataFrame) -> float:
    """Return the sum of minimum Euclidean distances between two GeoDataFrames,
    ensuring that points in `b` are only used once (without replacement), optimized for large datasets.
    """
    # Extract centroids as NumPy arrays (x, y coordinates)
    centroids_a = np.array(list(zip(a.geometry.centroid.x, a.geometry.centroid.y)))
    centroids_b = np.array(list(zip(b.geometry.centroid.x, b.geometry.centroid.y)))

    # Build a KDTree for centroids_b for fast nearest-neighbour search
    tree_b = cKDTree(centroids_b)

    # Array to keep track of which points in b have been used
    used = np.full(len(centroids_b), False)

    # Variable to keep track of the sum of minimum distances
    result = 0.0

    # Iterate over all points in centroids_a
    for point in centroids_a:
        # Initialize a large distance
        min_distance = float("inf")
        min_index = None

        # Find the nearest neighbours for the point in centroids_a
        distances, indices = tree_b.query(point, k=len(centroids_b))

        # Find the first unused nearest neighbor
        for distance, index in zip(distances, indices):
            if not used[index]:  # Find the first unused neighbour
                min_distance = distance
                min_index = index
                break

        # Add the minimum distance to the result
        result += min_distance

        # Mark the used point in centroids_b as used
        used[min_index] = True

    return result


def init_model(config: dict, params, enable_logs=False, model="spacenet7") -> Model:
    """Setup the model with the start date."""
    logger = Logger() if enable_logs else NoLogger()
    model_cls, problem_cls = MODELS[model]
    model = model_cls(config, logger)
    model.change_influences(params)
    n_new_buildings = problem_cls.parse_config__get_n_new_buildings(config)
    problem_cls.change_landowner_rule((25, 75), n_new_buildings)

    return model


def save_model_layer(model: Model, agent_cls: Type[GeoAgent], output: Path):
    gdf = model.grid.get_agents_as_GeoDataFrame(agent_cls)
    gdf = gdf.drop(columns="parametters")
    gdf.to_file(output)


def get_config_path(dataset_name):
    return Path("model/config/sn7") / dataset_name / "all.toml"


def run_model(config, params, i=0):
    try:
        model = init_model(config, params)
        model.step()
        return model.grid.get_agents_as_GeoDataFrame(Dwelling)
    except NoValidStartPoint:
        return None
    except ImpossibleBuild:
        return None
    except Exception as e:
        print("weird error here", e)
        return None


def compute_diff(start, validation_buildings, max_distance, end):
    if end is not None:
        delta = end[~end.isin(start)].dropna()
        distance = sum_of_min_euclidean_distances2(delta, validation_buildings)
        return distance / (max_distance * len(delta))
    else:
        return np.NaN


def make_simulations(
    results,
    output: Path,
    n_sim: int,
    n_proc: int,
    model="spacenet7",
):
    """Make the simulations."""
    output.mkdir(parents=True, exist_ok=True)

    model_cls, problem_cls = MODELS[model]

    res = []

    for index, row in results.iterrows():
        config_path = get_config_path(row["dataset"])
        config = load_config(config_path)
        validation = problem_cls.parse_config__get_validation_dataset(config)
        # border = problem_cls.parse_config__get_border(config)

        params = list(row[problem_cls.params_names()])
        model = init_model(config, params, enable_logs=False)

        start = model.grid.get_agents_as_GeoDataFrame(Dwelling)
        validation_buildings = validation.loc[~validation.intersects(start.union_all())]

        max_distance = model.border.shape.boundary.hausdorff_distance(
            validation_buildings.geometry.centroid
        ).max()

        simulations = process_map(
            partial(run_model, config, params),
            range(n_sim),
            max_workers=n_proc,
            chunksize=1,
            desc=f"{row["dataset"]} | {row["exp"]} | run_model",
        )

        simulation_error = process_map(
            partial(compute_diff, start, validation_buildings, max_distance),
            simulations,
            max_workers=n_proc,
            chunksize=1,
            desc=f"{row["dataset"]} | {row["exp"]} | compute_error",
        )

        subres = pd.DataFrame(
            {
                "dataset": row["dataset"],
                "exp": row["exp"],
                "solution_idx": index,
                "simulation_error": simulation_error,
            }
        )

        subres.to_parquet(output / f"{row["dataset"]}_{row["exp"]}_{index}.parquet")

        res.append(subres)

    res = pd.concat(res)
    res.to_parquet(output / "all.parquet")


if __name__ == "__main__":
    SIM_OUTPUT = Path("simulation_error")
    N_CPU = 10
    N_SIM = 10

    results = pd.read_parquet(Path("results/combined.parquet"))
    make_simulations(results, SIM_OUTPUT, N_SIM, N_CPU)
