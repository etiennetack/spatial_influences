# -*- coding: utf-8 -*-
import sys
import itertools
from multiants.influences.gradient import NoValidStartPoint
import numpy as np
import pandas as pd
import geopandas as gpd

from functools import partial
from pathlib import Path

from tqdm.contrib.concurrent import process_map

sys.path.append("./learn-influences")

from agents.dwelling import Dwelling
from generation.dwelling_factory import ImpossibleBuild

from scripts.common import (
    N_NEW_BUILDINGS,
    # VALIDATION_DATE,
    init_model,
    get_maximum_distance,
    get_validation_buildings,
    save_buildings,
    update_immigration_bulk_rule,
)


def sum_of_min_euclidean_distances(
    a: gpd.GeoDataFrame,
    b: gpd.GeoDataFrame,
) -> float:
    """Return the sum of mininum euclidean distances between two GeoDataFrames
    based on centroids and make the sum of distances between each point and its
    nearest neighbour.
    """
    centroids_a = a.geometry.centroid
    centroids_b = b.geometry.centroid
    result = 0
    for i in range(len(centroids_a)):
        min_distance = float("inf")
        min_index = None
        for j in range(len(centroids_b)):
            distance = centroids_a.iloc[i].distance(centroids_b.iloc[j])
            if distance < min_distance:
                min_distance = distance
                min_index = j
        if len(centroids_b) > 0:
            result += min_distance
            centroids_b = centroids_b.drop(centroids_b.index[min_index])
    return result


def run_model(params, i=0):
    try:
        model = init_model(params)
        n_new_buildings = N_NEW_BUILDINGS[int(params["start"])]
        update_immigration_bulk_rule(n_new_buildings)
        model.step()
        return model.grid.get_agents_as_GeoDataFrame(Dwelling)
    except NoValidStartPoint:
        return None
    except ImpossibleBuild:
        return None


def make_simulations(results, base_path: Path, n_sim: int, n_proc: int):
    """Make the simulations."""
    base_path.mkdir(parents=True, exist_ok=True)
    start_buildings_path = base_path / "start_buildings"
    start_buildings_path.mkdir(parents=True, exist_ok=True)
    # Save start buldings
    for start_date in results["start"].unique():
        save_path = start_buildings_path / f"{start_date}.geojson"
        if save_path.exists():
            print(f"Start buildings for {start_date} already exist")
            continue
        model = init_model(start_date)
        save_buildings(model, save_path)
        print(f"Saved start buildings for {start_date}")
    # Simulate and save resulting buildings
    print(f"Simulating {n_sim} for {len(results)} learning results!")
    for index, row in results.iterrows():
        sub_path = base_path / row["jobid"] / str(index)
        print(sub_path)
        sub_path.mkdir(parents=True, exist_ok=True)
        n_done = len(list(sub_path.iterdir()))
        if n_done >= n_sim:
            print(f"Simulations for {row['jobid']} already exist")
            continue
        results = process_map(
            partial(run_model, row),
            range(n_done, n_sim),
            max_workers=n_proc,
            chunksize=1,
        )
        for i, result in zip(range(n_done, n_sim), results):
            if result is not None:
                result = result.drop(columns=["parametters"])
                result.to_file(sub_path / f"{i}.geojson", driver="GeoJSON")
            else:
                (sub_path / f"{i}.failed").touch()


def calculate_error(
    start_buildings: gpd.GeoDataFrame,
    validation_buildings: gpd.GeoDataFrame,
    max_error: float,
    result_path: Path,
) -> float:
    """Calculate the error."""
    if result_path.suffix == ".geojson":
        end_buildings = gpd.read_file(result_path)
        delta = end_buildings[~end_buildings.isin(start_buildings)].dropna()
        distance = sum_of_min_euclidean_distances(delta, validation_buildings)
        return distance / max_error
    elif result_path.suffix == ".failed":
        return np.NaN


def calculate_simulation_error(
    results: gpd.GeoDataFrame,
    base_path: Path,
    n_sim: int,
    n_proc: int = 4,
):
    start_buildings = {
        start_date: gpd.read_file(
            base_path / "start_buildings" / f"{start_date}.geojson"
        )
        for start_date in results["start"].unique()
    }
    validation_buildings = {
        start_date: get_validation_buildings(int(start_date))
        for start_date in results["start"].unique()
    }
    max_error = {
        start_date: get_maximum_distance(int(start_date))
        * N_NEW_BUILDINGS[int(start_date)]
        for start_date in results["start"].unique()
    }

    res = pd.DataFrame()

    for index, row in results.iterrows():
        error = pd.DataFrame(
            {
                "jobid": row["jobid"],
                "result_index": str(index),
                "error": process_map(
                    partial(
                        calculate_error,
                        start_buildings[row["start"]],
                        validation_buildings[row["start"]],
                        max_error[row["start"]],
                    ),
                    itertools.islice(
                        (base_path / row["jobid"] / str(index)).iterdir(),
                        n_sim,
                    ),
                    max_workers=n_proc,
                    chunksize=1,
                ),
            }
        )
        res = pd.concat([res, error], ignore_index=True)

    return res


if __name__ == "__main__":
    RESULTS_PATH = Path("results")
    SIMULATIONS_PATH = RESULTS_PATH / "simulations"
    N_CPU = 10
    N_SIM = 10

    results = pd.read_parquet(RESULTS_PATH / "results.parquet")
    make_simulations(results, SIMULATIONS_PATH, N_SIM, N_CPU)
    error = calculate_simulation_error(results, SIMULATIONS_PATH, N_SIM, N_CPU)
    error.to_parquet(RESULTS_PATH / "results_w_simulation_error.parquet")
    # ADD concat of results and error
