from typing import cast
from random import uniform
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import Point, Polygon

__all__ = ["random_point_in_bounds", "random_points_in_bounds"]


def random_point_in_bounds(bounding_polygon: Polygon) -> Point:
    minx, miny, maxx, maxy = bounding_polygon.bounds
    res = None
    while not res:
        x = uniform(minx, maxx)
        y = uniform(miny, maxy)
        random_point = Point(x, y)

        if bounding_polygon.contains(random_point):
            res = random_point

    return res


def random_points_in_bounds(bounding_polygon, number) -> gpd.GeoDataFrame:
    gdf_poly = gpd.GeoDataFrame(
        index=["border"],
        geometry=[bounding_polygon],
    )  # pyright: ignore [reportGeneralTypeIssues]
    minx, miny, maxx, maxy = bounding_polygon.bounds
    x = np.random.uniform(minx, maxx, number)
    y = np.random.uniform(miny, maxy, number)
    df = pd.DataFrame()
    df["points"] = list(zip(x, y))
    df["points"] = df["points"].apply(Point)
    gdf_points = gpd.GeoDataFrame(
        df,
        geometry="points",
    )  # pyright: ignore [reportGeneralTypeIssues]
    sjoin = gpd.sjoin(gdf_points, gdf_poly, predicate="within", how="left")
    res = gdf_points[sjoin.index_right == "border"]
    return cast(gpd.GeoDataFrame, res)
