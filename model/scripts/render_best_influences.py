from pathlib import Path
import pyarrow.parquet as pq
import sys

from multiants.config import load_config
from multiants.logger import Logger
from multiants.influences import (
    DistanceInfluenceGPD,
    SlopeInfluence,
)
from multiants.influences.functions import make_attraction_repulsion
from multiants.influences.functions import make_open_distance
from multiants.influences import render as infl_render

sys.path.append("./learn-influences")

from model import SospadisModel
from agents.dwelling import Dwelling
from agents.road import Category as RoadCategory
from agents.road import Road
from scripts.common import (
    init_model,
    setup_influences,
)


def change_influences(
    model,
    neighbours=None,
    roads=None,
    paths=None,
    slope=None,
):
    infl_functions = []

    # Household influence
    if neighbours is not None:
        infl_functions.append(
            DistanceInfluenceGPD(
                model=model,
                target={"agent_class": Dwelling},
                function=make_attraction_repulsion(
                    neighbours["l_min"],
                    neighbours["l_0"],
                    neighbours["l_max"],
                ),
                weight=neighbours["w"],
            ),
        )

    # Road influenceZ
    if roads is not None:
        infl_functions.append(
            DistanceInfluenceGPD(
                model=model,
                target={
                    "agent_class": Road,
                    "filter": (
                        lambda params: params["category"]
                        == RoadCategory.Type.ROAD
                        or params["category"] == RoadCategory.Type.SMALL_ROAD
                    ),
                },
                function=make_attraction_repulsion(
                    roads["l_min"],
                    roads["l_0"],
                    roads["l_max"],
                ),
                weight=roads["w"],
            ),
        )

    # Stepway influence
    if paths is not None:
        infl_functions.append(
            DistanceInfluenceGPD(
                model=model,
                target={
                    "agent_class": Road,
                    "filter": (
                        lambda params: params["category"]
                        == RoadCategory.Type.STEPWAY
                        or params["category"] == RoadCategory.Type.PATH
                    ),
                },
                function=make_open_distance(paths["l_min"], paths["l_max"]),
                weight=paths["w"],
            ),
        )

    # Slope
    if slope is not None:
        infl_functions.append(
            SlopeInfluence(
                model=model,
                function=make_open_distance(slope["l_min"], slope["l_max"]),
                weight=slope["w"],
                raster="topography",
            ),
        )

    model.add_influence("HouseBuilding", infl_functions)


def extract_start_date(period):
    START_DATES = {"94": 1994, "02": 2002, "09": 2009}
    return START_DATES[period[:2]]


def render_influence(model, savepath):
    map = infl_render.render_influence_map(
        model,
        "HouseBuilding",
        pixel_size=1.0,
    )
    infl_render.save_influence_map(model, map, savepath)


if __name__ == "__main__":
    bests = pq.read_table(Path("results/bests.parquet")).to_pandas()

    for index, row in bests.iterrows():
        start_date = extract_start_date(row["period"])
        model = init_model(int(start_date))
        influences = {
            "neighbours": {
                "l_min": row["neighbours_l_min"],
                "l_0": row["neighbours_l_0"],
                "l_max": row["neighbours_l_max"],
                "w": row["neighbours_w"],
            },
            "roads": {
                "l_min": row["roads_l_min"],
                "l_0": row["roads_l_0"],
                "l_max": row["roads_l_max"],
                "w": row["roads_w"],
            },
            "paths": {
                "l_min": row["paths_l_min"],
                "l_max": row["paths_l_max"],
                "w": row["paths_w"],
            },
            "slope": {
                "l_min": row["slope_l_min"],
                "l_max": row["slope_l_max"],
                "w": row["slope_w"],
            },
        }
        change_influences(model, **influences)
        render_influence(
            model,
            f"{row['measures']}-{row['period']}-{row['exp']}-{index}.tiff",
        )
        for factor, params in influences.items():
            change_influences(model, **{factor: params})
            render_influence(
                model,
                f"{row['measures']}-{row['period']}-{row['exp']}-{index}-{factor}.tiff",
            )

        # row["K"]
        # row["C"]
        # row["D"]
