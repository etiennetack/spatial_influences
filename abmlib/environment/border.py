# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Optional
from typing import Tuple
from random import random

import geopandas as gpd
from shapely import Point

if TYPE_CHECKING:
    from shapely import Geometry

__all__ = ["Border"]


class Border:
    """Limit the study area to a limited zone.

    TODO: Is this class really useful? We could use a function like the
    commented one (above).

    Args:
        filepath (str): path to a shapefile.
        feature (int): index of the border feature.

    """

    def __init__(
        self,
        filepath: str,
        feature: int = 0,
        crs: Optional[str] = None,
    ) -> None:
        gdf = gpd.read_file(filepath)
        if crs is not None:
            gdf = gdf.to_crs(crs)
        self._shape = gdf.geometry[feature]

    def is_valid(self, obj: Geometry) -> bool:
        """Check if a given object is within this border.

        Args:
            obj: the shapely object to test.

        Returns (bool):
            True: if obj is inside.
            False: otherwise.
        """
        return self.shape.contains(obj)

    @property
    def shape(self) -> Geometry:
        return self._shape

    @property
    def crs(self) -> str:
        return self.shape.crs

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        return self.shape.bounds

    def random_point(self) -> Point:
        """Return a random point within the border."""
        minx, miny, maxx, maxy = self.bounds
        while True:
            p = Point(
                minx + (maxx - minx) * random(),
                miny + (maxy - miny) * random(),
            )
            if self.shape.contains(p):
                return p

    def greatest_distance(self):
        """Return the greatest distance between two points of the border."""
        minx, miny, maxx, maxy = self.bounds
        return Point(minx, miny).distance(Point(maxx, maxy))
