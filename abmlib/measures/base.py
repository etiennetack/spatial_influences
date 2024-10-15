import numpy as np
from typing import Any
from nptyping import NDArray

__all__ = ["Measure", "MeasureDifference", "MeasureDifferenceWithNearest"]


class Measure:
    def apply(self, dataset, **options) -> Any:
        raise NotImplementedError


class MeasureDifference(Measure):
    def apply(self, simulation, validation, **options) -> Any:
        raise NotImplementedError

    def apply_validation(self, simulation, validation, **options) -> Any:
        return self.apply(simulation, validation, **options)


class MeasureDifferenceWithNearest(MeasureDifference):
    """
    Apply a difference function on simulated objects with the
    nearest object in the validation dataset.
    """

    def apply(self, simulation, validation, **options) -> NDArray:
        distances = np.empty(len(validation))
        sindex_sim = simulation.sindex
        for i, ref_object in enumerate(validation.geometry):
            nearest_object = sindex_sim.geometries[sindex_sim.nearest(ref_object)[1][0]]
            distances[i] = self.distance_function(ref_object, nearest_object)
        return distances

    def distance_function(self, ref_object, nearest_object) -> float:
        raise NotImplementedError
