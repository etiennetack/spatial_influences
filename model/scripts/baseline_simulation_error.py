# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from tqdm.contrib.concurrent import process_map
from functools import partial
import functools

import sys

sys.path.append("./learn-influences")

from model import SospadisModel
from agents.dwelling import Dwelling
from agents.landowner import LandOwner
from agents.landowner.behaviours import RandomSimulation

from scripts.common import (
    N_NEW_BUILDINGS,
    VALIDATION_DATE,
    get_maximum_distance,
    init_model,
    get_validation_buildings,
    update_random_simulation_rule,
    remove_immigration_bulk_rule,
)

from scripts.calculate_simulation_error import (
    sum_of_min_euclidean_distances,
)


def test_error():
    """Test the error calculation, the distance should be equal to 0."""
    for date in [1994, 2002, 2009]:
        validation_buildings = get_validation_buildings(date)
        error = sum_of_min_euclidean_distances(
            validation_buildings,
            validation_buildings,
        ) / (get_maximum_distance(date) * N_NEW_BUILDINGS[date])
        assert error == 0


def run_model(start_date: int, exp: int):
    # INIT
    model = init_model(start_date)
    start_buildings = model.grid.get_agents_as_GeoDataFrame(Dwelling)
    # SET UP
    remove_immigration_bulk_rule()
    update_random_simulation_rule(N_NEW_BUILDINGS[start_date])
    # RUN
    model.step()
    # CALCULATE ERROR
    end_buildings = model.grid.get_agents_as_GeoDataFrame(Dwelling)
    delta = end_buildings[~end_buildings.isin(start_buildings)].dropna()
    validation_buildings = get_validation_buildings(start_date)
    distance = sum_of_min_euclidean_distances(delta, validation_buildings)
    max_error = get_maximum_distance(start_date) * N_NEW_BUILDINGS[start_date]
    return distance / max_error


def make_baseline(start_date, n_exp=100, n_cpu=4):
    print(f"{start_date}...")
    validation_date = VALIDATION_DATE[start_date]
    random_simulations = np.array(
        process_map(
            partial(run_model, start_date),
            range(n_exp),
            max_workers=n_cpu,
            chunksize=1,
        )
    )
    return {
        "start": start_date,
        "mean": random_simulations.mean(),
        "std": random_simulations.std(),
        "min": random_simulations.min(),
        "max": random_simulations.max(),
    }


def make_baseline_dataframe(n_exp=100, n_cpu=4):
    return (
        pd.DataFrame(
            [
                make_baseline(start_date, n_exp, n_cpu)
                for start_date in [1994, 2002, 2009]
            ]
        )
        #
        .set_index("start")
    )


if __name__ == "__main__":
    test_error()

    print("Calculating baselines for simulation errors...")
    simulation_error_baselines = make_baseline_dataframe(n_exp=1000, n_cpu=6)
    print(simulation_error_baselines)
    simulation_error_baselines.to_parquet(
        "results/simulation_error_baselines.parquet"
    )
