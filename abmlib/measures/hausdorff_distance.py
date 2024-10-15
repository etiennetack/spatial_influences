# -*- coding: utf-8 -*-
import numpy as np
from .base import MeasureDifferenceWithNearest
from scipy.spatial.distance import directed_hausdorff


__all__ = ["HausdorffDistance"]


class HausdorffDistance(MeasureDifferenceWithNearest):
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
            ref_points = list(zip(*ref_object.exterior.coords.xy))
            nearest_points = list(zip(*nearest_object.exterior.coords.xy))
            return max(
                directed_hausdorff(ref_points, nearest_points)[0],
                directed_hausdorff(nearest_points, ref_points)[0],
            )
