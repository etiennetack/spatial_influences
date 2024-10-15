# -*- coding: utf-8 -*-
from functools import partial
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
from tqdm.contrib.concurrent import process_map

import sys

sys.path.append("./learn-influences")

from scripts.common import (
    init_model,
    setup_influences,
    get_validation_buildings,
    dummy_building,
)


def calculate_influence(model, building):
    influence = model.influences["HouseBuilding"]
    return influence.compute_influences(
        {"shape": dummy_building()},
        building.centroid,
    )


def sample_influences(params, validation_buildings):
    model = init_model(int(params["start"]))
    setup_influences(model, params)
    errors: int = 0
    # for each new building
    for building in validation_buildings[params["start"]].geometry:
        if calculate_influence(model, building) == -1:
            # if the value is -1 count an error
            errors += 1
    # return to total number of errors divided by the number of new buildings
    return errors / (len(validation_buildings[params["start"]]) or 1)


def calculate_influence_error(results, n_proc=4):
    validation_buildings = {
        str(start_date): get_validation_buildings(start_date)
        for start_date in [1994, 2002, 2009]
    }

    error = process_map(
        partial(sample_influences, validation_buildings=validation_buildings),
        [row for _, row in results.iterrows()],
        max_workers=n_proc,
        chunksize=1,
    )

    influence_error = pd.DataFrame(
        {"influence_error": error},
        index=results.index,
    )

    return pd.concat((results, error_rate), axis="columns")


if __name__ == "__main__":
    RESULTS_PATH = Path("results")
    N_CPU = 10

    results = pq.read_table(RESULTS_PATH / "results.parquet").to_pandas()
    results_with_error = calculate_influence_error(results, n_proc=N_CPU)
    results_with_error.to_parquet(
        RESULTS_PATH / "results_w_influence_error.parquet"
    )

# Commands to build the error graphs with seaborn
# import seaborn as sns
# import matplotlib.pyplot as plt
# sns.barplot(error_rate[["measures", "start", "end", "error"]], x="measures", y="error", errorbar="sd")
# plt.show()
# sns.barplot(error_rate[["measures", "start", "end", "error"]], x="start", y="error", errorbar="sd")
# plt.show()
# sns.barplot(error_rate[["measures", "start", "end", "error"]], x="measures", y="error", hue="start", errorbar="sd")
# plt.show()
