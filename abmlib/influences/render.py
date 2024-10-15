# -*- coding: utf-8 -*-
import numpy as np
import rasterio
from shapely import Polygon
from shapely.geometry import Point
from rasterio.transform import Affine

__all__ = ["render_influence_map", "save_influence_map"]


def render_influence_map(model, influence, pixel_size=1.0):
    model.logger.system_log("START INFLUENCE RENDER")

    start = model.bounds["west"], model.bounds["north"]
    width = int((model.bounds["east"] - model.bounds["west"]) // pixel_size)
    height = int((model.bounds["north"] - model.bounds["south"]) // pixel_size)
    edge_size = 4.5
    shape = Polygon(
        [
            (-edge_size / 2, -edge_size / 2),
            (-edge_size / 2, edge_size / 2),
            (edge_size / 2, edge_size / 2),
            (edge_size / 2, -edge_size / 2),
        ]
    )

    res = np.empty((height, width))
    for i in range(height):
        for j in range(width):
            pos = Point(start[0] + j * pixel_size, start[1] - i * pixel_size)
            infl = model.influences[influence]
            res[i, j] = infl.compute_influences({"shape": shape}, pos)
        model.logger.system_log(
            f"RENDER PROGRESS: {round(i * 100 / height, 2)}%",
            add_to_buffer=False,
            print_replace=True,
        )

    model.logger.system_log("INFLUENCE RENDER DONE")
    return res


def save_influence_map(model, inflmap, result_file, pixel_size=1.0):
    transform = Affine.translation(model.bounds["west"], model.bounds["north"])
    transform *= Affine.scale(pixel_size, -pixel_size)

    with rasterio.open(
        result_file,
        "w",
        driver="GTiff",
        height=inflmap.shape[0],
        width=inflmap.shape[1],
        count=1,
        dtype=inflmap.dtype,
        crs=model.config["crs"],
        transform=transform,
    ) as tiff:
        tiff.write(inflmap, 1)
