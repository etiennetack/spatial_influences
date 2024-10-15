# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon

from .base import Measure, MeasureDifference

if TYPE_CHECKING:
    from typing import Optional

__all__ = ["GridDensity", "GridDensityDifference"]


class GridDensity(Measure):
    def apply(
        self,
        dataset,
        border: Optional[gpd.GeoDataFrame] = None,
        grid: Optional[gpd.GeoDataFrame] = None,
        size: float = 100,
    ) -> np.ndarray:
        if grid is not None:
            return self.apply2(dataset, grid)
        elif border is not None:
            return self.apply2(dataset, self.build_grid(border, size))
        else:
            raise Exception(
                "GridDensity have neither grid or a border to build the grid."
            )

    def apply2(self, dataset: gpd.GeoDataFrame, grid: gpd.GeoDataFrame) -> np.ndarray:
        centroids = gpd.GeoDataFrame({"geometry": dataset.centroid})

        # Spatial join to find which points fall within which squares
        points_in_grid = gpd.sjoin(centroids, grid, how="left", predicate="within")

        # Count the number of points within each square
        point_counts = points_in_grid.groupby("index_right").size()

        # Recreate a vector containing the 0 values (when a cell isn't populated)
        return point_counts.reindex(grid.index).fillna(0).astype(int).values

    def build_grid(
        self,
        border: gpd.GeoDataFrame,
        size: float,
    ) -> gpd.GeoDataFrame:
        xmin, ymin, xmax, ymax = border.total_bounds

        cols = list(np.arange(xmin, xmax + size, size))
        rows = list(np.arange(ymin, ymax + size, size))

        polygons = []
        for x in cols[:-1]:
            for y in rows[:-1]:
                polygons.append(
                    Polygon(
                        [
                            (x, y),
                            (x + size, y),
                            (x + size, y + size),
                            (x, y + size),
                        ]
                    )
                )

        return gpd.GeoDataFrame(
            {"geometry": polygons},
            crs=border.crs,
        )  # pyright: ignore


class GridDensityDifference(MeasureDifference, GridDensity):
    def apply(self, simulation, validation, border, grid_size=100):
        grid = self.build_grid(border, grid_size)
        return self.apply_grid(simulation, validation, grid)

    def apply_grid(self, simulation, validation, grid):
        density_sim = GridDensity().apply(simulation, grid=grid)
        density_real = GridDensity().apply(validation, grid=grid)
        return abs(density_real - density_sim)
