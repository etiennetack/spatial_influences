# -*- coding: utf-8 -*-
import random
import numpy as np
import pandas as pd
from tqdm import tqdm

import sys

sys.path.append("./learn-influences")

from scripts.common import (
    VALIDATION_DATE,
    get_validation_buildings,
)

from scripts.calculate_influence_error import (
    sample_influences,
)


def make_random_influence_params():
    """Make random influence functions."""
    params = {}
    # Neighbours
    neighbours_l_min = random.uniform(0, 100)
    neighbours_l_0 = neighbours_l_min + random.uniform(0, 100)
    neighbours_l_max = neighbours_l_0 + random.uniform(0, 100)
    neighbours_w = random.uniform(0, 1)
    params.update(
        {
            "neighbours_l_min": neighbours_l_min,
            "neighbours_l_0": neighbours_l_0,
            "neighbours_l_max": neighbours_l_max,
            "neighbours_w": neighbours_w,
        }
    )

    # Roads
    roads_l_min = random.uniform(0, 100)
    roads_l_0 = roads_l_min + random.uniform(0, 100)
    roads_l_max = roads_l_0 + random.uniform(0, 100)
    roads_w = random.uniform(0, 1)
    params.update(
        {
            "roads_l_min": roads_l_min,
            "roads_l_0": roads_l_0,
            "roads_l_max": roads_l_max,
            "roads_w": roads_w,
        }
    )

    # Paths
    paths_l_min = random.uniform(0, 100)
    paths_l_max = paths_l_min + random.uniform(0, 100)
    paths_w = random.uniform(0, 1)
    params.update(
        {
            "paths_l_min": paths_l_min,
            "paths_l_max": paths_l_max,
            "paths_w": paths_w,
        }
    )

    # Slope
    while True:
        slope_l_min = random.uniform(0, np.pi / 2)
        slope_l_max = random.uniform(0, np.pi / 2)
        if slope_l_min < slope_l_max:
            break
    slope_w = random.uniform(0, 1)
    params.update(
        {
            "slope_l_min": slope_l_min,
            "slope_l_max": slope_l_max,
            "slope_w": slope_w,
        }
    )

    return params


def make_random_influences(start_date: int, n_exp=100):
    """Make random influence functions and sample the validation buildings."""
    error_rate = []
    validation_buildings = {
        str(start_date): get_validation_buildings(start_date)
    }
    for _ in tqdm(range(n_exp)):
        params = make_random_influence_params()
        params["start"] = str(start_date)
        params["end"] = str(VALIDATION_DATE[start_date])
        error_rate.append(sample_influences(params, validation_buildings))
    error_rate = np.array(error_rate)
    return {
        "start": start_date,
        "mean": error_rate.mean(),
        "std": error_rate.std(),
        "min": error_rate.min(),
        "max": error_rate.max(),
    }


def build_baselines():
    """Make the baseline for the error presented in the ECAI paper."""
    return pd.DataFrame(
        [
            make_random_influences(start_date, 100)
            for start_date in [1994, 2002, 2009]
        ]
    )


if __name__ == "__main__":
    influence_error_baselines = build_baselines()
    print(influence_error_baselines)
    influence_error_baselines.to_parquet(
        "results/influence_error_baselines.parquet"
    )
