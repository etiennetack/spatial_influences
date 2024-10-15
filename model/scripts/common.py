import itertools as it
from multiants.influences import DistanceInfluenceGPD, SlopeInfluence
from multiants.influences.functions import (
    make_attraction_repulsion,
    make_open_distance,
)
from multiants.logger import Logger, NoLogger
from multiants.config import load_config
import pandas as pd
import geopandas as gpd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
import shapely as shp

import sys

sys.path.append("./learn-influences")

from model import SospadisModel
from agents.dwelling import Dwelling
from agents.road import Road
from agents.road import Category as RoadCategory
from agents.landowner import LandOwner
from agents.landowner.behaviours import ImmigrationBulk, RandomSimulation


# Parsing tools


def params_names():
    return [
        "neighbours_l_min",
        "neighbours_l_0",
        "neighbours_l_max",
        "neighbours_w",
        "roads_l_min",
        "roads_l_0",
        "roads_l_max",
        "roads_w",
        "paths_l_min",
        "paths_l_max",
        "paths_w",
        "slope_l_min",
        "slope_l_max",
        "slope_w",
    ]


def rebuild_params(X):
    w_sum = X["neighbours_w"] + X["roads_w"] + X["paths_w"] + X["slope_w"]

    X["neighbours_l_0"] += X["neighbours_l_min"]
    X["neighbours_l_max"] += X["neighbours_l_0"]
    X["neighbours_w"] /= w_sum

    X["roads_l_0"] += X["roads_l_min"]
    X["roads_l_max"] += X["roads_l_0"]
    X["roads_w"] /= w_sum

    X["paths_l_max"] += X["paths_l_min"]
    X["paths_w"] /= w_sum

    X["slope_l_max"] += X["slope_l_min"]
    X["slope_w"] /= w_sum

    return X


def extract_jobid(file_name):
    return int(file_name.split("-")[1].split("_")[0])


def make_measures_codes(measure_aliases):
    res = []
    res += [m for m in measure_aliases]
    for i in range(2, len(measure_aliases)):
        res += list("".join(m) for m in it.combinations(measure_aliases, i))
    res += [measure_aliases]
    return res


def get_dates():
    return {
        "94": 1994,
        "02": 2002,
        "09": 2009,
        "19": 2019,
    }


def make_periods(dates):
    return {
        "".join(pair): (dates[pair[0]], dates[pair[1]])
        for pair in it.pairwise(dates.keys())
    }


def get_exp_codes(measures_combs, periods):
    return [f"{m}{p}" for m in measures_combs for p in periods.keys()]


def save_dataframe(data: pd.DataFrame, path: Path) -> None:
    table = pa.Table.from_pandas(data)
    pq.write_table(table, path)


# Tools for doing simulations

N_NEW_BUILDINGS = {
    1994: 26,
    2002: 22,
    2009: 25,
}


def init_model(start_date: int, enable_logs=False) -> SospadisModel:
    """Setup the model with the start date."""
    config = load_config(f"./learn-influences/config/{start_date}.toml")
    logger = Logger() if enable_logs else NoLogger()
    model = SospadisModel(config, logger)
    return model


def setup_influences(
    model: SospadisModel,
    row: pd.Series,
    filter=["neighbours", "roads", "paths", "slope"],
):
    influences_functions = []

    # Household influence
    if "neigbours" in filter:
        influences_functions.append(
            DistanceInfluenceGPD(
                model=model,
                target={"agent_class": Dwelling},
                function=make_attraction_repulsion(
                    row["neighbours_l_min"],
                    row["neighbours_l_0"],
                    row["neighbours_l_max"],
                ),
                weight=row["neighbours_w"],
            )
        )

    if "roads" in filter:
        influences_functions.append(
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
                    row["roads_l_min"],
                    row["roads_l_0"],
                    row["roads_l_max"],
                ),
                weight=row["roads_w"],
            )
        )

    if "paths" in filter:
        influences_functions.append(
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
                function=make_open_distance(
                    row["paths_l_min"],
                    row["paths_l_max"],
                ),
                weight=row["paths_w"],
            )
        )

    if "slope" in filter:
        influences_functions.append(
            SlopeInfluence(
                model=model,
                function=make_open_distance(
                    row["slope_l_min"],
                    row["slope_l_max"],
                ),
                weight=row["slope_w"],
                raster="topography",
            )
        )

    model.add_influence("HouseBuilding", influences_functions)


# Error

VALIDATION_DATE = {
    1994: 2002,
    2002: 2009,
    2009: 2019,
}

FEATURES = Path("data/valenicina/features")


def open_start_dataset(start_date: int):
    """Open the start dataset."""
    return gpd.read_file(FEATURES / f"buildings_{start_date}.geojson")


def open_validation_dataset(start_date: int):
    """Open the validation dataset."""
    return gpd.read_file(
        FEATURES / f"buildings_{VALIDATION_DATE[start_date]}.geojson"
    )


def get_validation_buildings(start_date: int):
    start_buildings = open_start_dataset(start_date)
    end_buildings = open_validation_dataset(start_date)
    return (
        end_buildings
        #
        .loc[~end_buildings.intersects(start_buildings.unary_union)]
        #
        .reset_index(drop=True)
    )


def get_maximum_distance(start_date: int):
    """Return the maximum distance between the validation buildings and the
    border."""
    model = init_model(start_date)
    validation_buildings = get_validation_buildings(start_date)
    # border_bbox = shp.box(*model.border.shape.bounds)
    return (
        model.border.shape.boundary
        # Furthest distance between the AoI border and the validation buildings
        .hausdorff_distance(validation_buildings.geometry.centroid).max()
    )


# def simulation_error(
#     simulation_buildings: gpd.GeoDataFrame,
#     validation_buildings: gpd.GeoDataFrame,
#     max_distance: float,
# ) -> float:
#     """Calculate the error of a simulation."""
#     distance = euclidean_distance(delta, validation_buildings)
#     return distance / (max_distance * len(delta))


def save_buildings(model: SospadisModel, path: Path) -> None:
    buildings = model.grid.get_agents_as_GeoDataFrame(Dwelling)
    buildings = buildings.drop(columns=["parametters"])
    buildings.to_file(path, driver="GeoJSON")


def update_immigration_bulk_rule(n_new_buildings: int) -> None:
    """Update the number of buildings created by the immigration bulk rule."""
    LandOwner.RULES.update(
        {
            "immigration_bulk": ImmigrationBulk(
                area_range=(25, 75),
                number=n_new_buildings,
            ),
        }
    )


def update_random_simulation_rule(n_new_buildings: int) -> None:
    """Update the number of buildings created by the random simulation rule."""
    LandOwner.RULES.update(
        {
            "random_simulation": RandomSimulation(
                area_range=(25, 75),
                number=n_new_buildings,
            ),
        }
    )


def remove_immigration_bulk_rule() -> None:
    """Remove the create_empty_buildings rule."""
    LandOwner.RULES.pop("immigration_bulk", None)


def dummy_building(edge_size: float = 4.5) -> shp.Polygon:
    return shp.Polygon(
        [
            (-edge_size / 2, -edge_size / 2),
            (-edge_size / 2, edge_size / 2),
            (edge_size / 2, edge_size / 2),
            (edge_size / 2, -edge_size / 2),
        ]
    )
