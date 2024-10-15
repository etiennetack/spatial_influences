# -*- coding: utf-8 -*-
from typing import cast
import numpy as np
from .base import MeasureDifference, MeasureDifferenceWithNearest
from shapely import Polygon
from x2polygons.polygon_distance import chamfer_distance


__all__ = ["ChamferDistance", "ChamferDistanceMacro"]


class ChamferDistance(MeasureDifferenceWithNearest):
    def distance_function(self, ref_object, nearest_object) -> float:
        if ref_object.geom_type == "MultiPolygon":
            return np.array(
                [
                    self.distance_function(ref_subpart, nearest_object)
                    for ref_subpart in ref_object.geoms
                ]
            ).mean()
        elif nearest_object.geom_type == "MultiPolygon":
            return self.distance_function(
                ref_object,
                min(
                    nearest_object.geoms,
                    key=lambda p: p.distance(ref_object),
                ),
            )
        else:
            return cast(float, chamfer_distance(ref_object, nearest_object))


class ChamferDistanceMacro(MeasureDifference):
    def apply(self, simulation, validation, **options) -> float:
        centroids_sim = Polygon([[p.x, p.y] for p in simulation.geometry.centroid])
        centroids_real = Polygon([[p.x, p.y] for p in validation.geometry.centroid])
        return cast(float, chamfer_distance(centroids_sim, centroids_real))
