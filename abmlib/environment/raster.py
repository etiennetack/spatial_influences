# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional
from typing import Tuple, Generator

import rasterio as rio
import rioxarray as rxr

from math import pi, atan
from shapely import MultiPolygon, Polygon, Point

# from shapely import minimum_rotated_rectangle
# from shapely.geometry import mapping


__all__ = ["Raster"]


class Raster:
    def __init__(self, file: str, undefined_value: float, crs: Optional[str] = None):
        raster = rxr.open_rasterio(file).squeeze()

        # reproject to model's CRS
        if crs is not None:
            raster = raster.rio.reproject(crs)

        self.data = raster.to_numpy()
        self.bounds = self.make_bounds(raster)
        self.transform = self.make_transform(self.bounds, self.matrix_size)
        self._undefined_value = raster.attrs["_FillValue"]
        self._area_or_point = raster.attrs["AREA_OR_POINT"]

    @staticmethod
    def make_bounds(raster):
        lons = raster["x"].values
        lats = raster["y"].values
        return {
            "left": lons.min(),
            "right": lons.max(),
            "bottom": lats.min(),
            "top": lats.max(),
        }

    @staticmethod
    def make_transform(bounds, matrix_size):
        return rio.transform.from_bounds(
            bounds["left"],
            bounds["bottom"],
            bounds["right"],
            bounds["top"],
            matrix_size[0],
            matrix_size[1],
        )

    def is_out_of_bounds(self, point: Point) -> bool:
        """Check if the given point is out of the matrix bounds.

        Args:
            point: GPS coordinates.
        """
        return not (
            self.bounds["left"] <= point.x <= self.bounds["right"]
            and self.bounds["bottom"] <= point.y <= self.bounds["top"]
        )

    @property
    def matrix_size(self) -> Tuple[int, int]:
        """Matrix' height and width."""
        return self.data.shape

    @property
    def real_size(self) -> Tuple[float, float]:
        """Real height and width."""
        return (
            self.bounds["right"] - self.bounds["left"],
            self.bounds["top"] - self.bounds["bottom"],
        )

    @property
    def resolution(self) -> Tuple[float, float]:
        size_x, size_y = self.matrix_size
        size_lon, size_lat = self.real_size
        return (size_lon / size_x, size_lat / size_y)

    def get_coords(self, point: Point) -> Tuple[int, int]:
        """Get matrix coordinates for a given GPS point.

        Args:
            point: GPS coordinates.
        """
        if self._area_or_point == "Area":
            resolution_x, resolution_y = self.resolution
            res = ~self.transform * (
                point.x - resolution_x / 2,
                point.y - resolution_y / 2,
            )
        else:
            res = ~self.transform * (point.x, point.y)
        return round(res[0]), round(res[1])

    def get_value(self, point: Point) -> float | None:
        """Get elevation for a given GPS point, or None if point is not defined
        at this location.

        Args:
            point: GPS coordinates.
        """
        if self.is_out_of_bounds(point):
            return None
        try:
            coords = self.get_coords(point)
            value = self.data[coords]
        except IndexError:
            raise Exception(f"{point} | {coords} not in {self.matrix_size}")
        if value == self._undefined_value:
            return None
        else:
            return value

    def _get_polygon_points(self, shape: Polygon) -> Generator[Point, None, None]:
        for point in (Point(*coords) for coords in shape.exterior.coords[:-1]):
            yield point
        yield Point(*shape.centroid.coords[:])

    def _get_min_elevation(self, shape: Polygon) -> Tuple[Point, float] | None:
        min_point = None
        min_value = float("inf")
        for p in self._get_polygon_points(shape):
            p_value = self.get_value(p)
            if p_value is not None:
                if p_value < min_value:
                    min_point = p
                    min_value = p_value
            else:
                return None
        if min_point:
            return min_point, min_value
        else:
            return None

    def _get_max_elevation(self, shape: Polygon) -> Tuple[Point, float] | None:
        max_point = None
        max_value = float("-inf")
        for p in self._get_polygon_points(shape):
            p_value = self.get_value(p)
            if p_value is not None:
                if p_value > max_value:
                    max_point = p
                    max_value = p_value
            else:
                return None
        if max_point:
            return max_point, max_value
        else:
            return None

    def _get_max_length(self, shape: Polygon) -> float:
        bbox = shape.bounds
        l1 = bbox[2] - bbox[0]
        l2 = bbox[3] - bbox[1]
        return l1 if l1 > l2 else l2

    def get_slope(self, shape: Polygon | MultiPolygon) -> float | None:
        """Get slope by calculate the delta between lowest and highest points
        in the given polygon.

        Args:
            shape: a building's shape
        """
        if isinstance(shape, Polygon):
            min_elevation = self._get_min_elevation(shape)
            max_elevation = self._get_max_elevation(shape)
            if min_elevation and max_elevation:
                min_p, min_el = min_elevation
                max_p, max_el = max_elevation
                distance = min_p.distance(max_p)
                if distance == 0:
                    return 0
                else:
                    return atan((max_el - min_el) / distance)
            else:
                return None
        elif isinstance(shape, MultiPolygon):
            max_slope = float("-inf")
            for sub_p in shape.geoms:
                sub_slope = self.get_slope(sub_p)
                if sub_slope is not None:
                    if sub_slope > max_slope:
                        max_slope = sub_slope
                else:
                    return None

    def check_slope(
        self,
        shape: Polygon | MultiPolygon,
        max_slope: float = pi / 8,
    ) -> bool:
        """Check slope for a given polygon.

        Args:
            shape (shapely.geometry.BaseGeometry): building's geometry.
            max_slope (float): max slope in radians.

        Returns:
            True if slope doesn't exceed max slope parameter, False otherwise.
        """
        slope = self.get_slope(shape)
        return slope is not None and slope <= max_slope
