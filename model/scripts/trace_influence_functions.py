# -*- coding: utf-8 -*-
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from multiants.influences import render as infl_render
from multiants.influences.functions import (
    make_attraction_repulsion,
    make_open_distance,
)

import sys

sys.path.append("./learn-influences")

from scripts.common import init_model, setup_influences


def extract_best(results_with_errors: pd.DataFrame) -> pd.DataFrame:
    bests = pd.DataFrame()
    for start in results_with_errors["start"].unique():
        for measures in results_with_errors["measures"].unique():
            best = results_with_errors.query(
                f"measures == '{measures}' and start == '{start}'"
            ).nsmallest(1, "error_mean")
            bests = pd.concat([bests, best], ignore_index=True)
    return bests


def trace_influence_functions(
    bests: pd.DataFrame,
    output: Path,
    x_max: int = 150,
    n_samples: int = 100,
):
    """Trace influence function using mathplotlib."""
    output.mkdir(parents=True, exist_ok=True)
    for measures in bests["measures"].unique():
        fig, axs = plt.subplots(2, 2, figsize=(7, 6), dpi=300)
        plt.suptitle(f"{measures}")
        for start in bests["start"].unique():
            for index, row in bests.query(
                f"measures == '{measures}' and start == '{start}'"
            ).iterrows():
                neighbours_fn = make_attraction_repulsion(
                    row["neighbours_l_min"],
                    row["neighbours_l_0"],
                    row["neighbours_l_max"],
                )
                roads_fn = make_attraction_repulsion(
                    row["roads_l_min"],
                    row["roads_l_0"],
                    row["roads_l_max"],
                )
                paths_fn = make_open_distance(
                    row["paths_l_min"],
                    row["paths_l_max"],
                )
                slope_fn = make_open_distance(
                    row["slope_l_min"],
                    row["slope_l_max"],
                )

                def aggregate_fn(distance):
                    neighbours = neighbours_fn(distance) * row["neighbours_w"]
                    if neighbours == -1:
                        return -1
                    roads = roads_fn(distance) * row["roads_w"]
                    if roads == -1:
                        return -1
                    paths = paths_fn(distance) * row["paths_w"]
                    if paths == -1:
                        return -1
                    slope = slope_fn(distance) * row["slope_w"]
                    if slope == -1:
                        return -1
                    return neighbours + roads + paths + slope

                x = np.linspace(0, x_max, n_samples)

                # Neighbours
                axs[0, 0].plot(
                    x,
                    [neighbours_fn(i) * row["neighbours_w"] for i in x],
                    label=f"{start}",
                )
                axs[0, 0].set_ylim(-0.6, 0.6)
                axs[0, 0].set_title("Neighbours")
                axs[0, 0].legend()
                axs[0, 0].set_xlabel("Distance (m)")

                # Roads
                axs[0, 1].plot(
                    x,
                    [roads_fn(i) * row["roads_w"] for i in x],
                    label=f"{start}",
                )
                axs[0, 1].set_ylim(-0.6, 0.6)
                axs[0, 1].set_title("Roads")
                axs[0, 1].legend()
                axs[0, 1].set_xlabel("Distance (m)")

                # Paths
                axs[1, 0].plot(
                    x,
                    [paths_fn(i) * row["paths_w"] for i in x],
                    label=f"{start}",
                )
                axs[1, 0].set_ylim(-0.6, 0.6)
                axs[1, 0].set_title("Paths")
                axs[1, 0].legend()
                axs[1, 0].set_xlabel("Distance (m)")

                # Slope
                slope_x = np.linspace(0, np.pi, n_samples)
                axs[1, 1].plot(
                    slope_x,
                    [slope_fn(i) * row["slope_w"] for i in slope_x],
                    label=f"{start}",
                )
                axs[1, 1].set_ylim(-0.6, 0.6)
                axs[1, 1].set_title("Slope")
                axs[1, 1].legend()
                axs[1, 1].set_xlabel("Slope (rad)")

        fig.tight_layout()
        plt.savefig(output / f"{measures}.png")
        plt.close()


def make_best_inluences_maps(bests: pd.DataFrame, output: Path):
    for _, row in bests.iterrows():
        print(
            "Making influence map for ",
            row["measures"],
            row["start"],
            row["end"],
        )
        model = init_model(row["start"], True)
        setup_influences(model, row)
        map = infl_render.render_influence_map(model, "HouseBuilding", 1.0)
        save_path = (
            output / row["measures"] / f"{row['start']}-{row['end']}.tiff"
        )
        save_path.parent.mkdir(parents=True, exist_ok=True)
        infl_render.save_influence_map(model, map, save_path, 1.0)


if __name__ == "__main__":
    RESULTS_PATH = Path("results")
    results_with_simulation_error = pd.read_parquet(
        RESULTS_PATH / "results_error_column.parquet"
    )
    bests = extract_best(results_with_simulation_error)

    trace_influence_functions(bests, RESULTS_PATH / "best_influences_plots")
    print("Influence functions ploted.")

    if input("Make influence maps? Take a lot of time. (y/n)") == "y":
        make_best_inluences_maps(bests, RESULTS_PATH / "best_influences_maps")
