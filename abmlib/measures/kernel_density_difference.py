import numpy as np
from math import ceil
from .base import Measure, MeasureDifference
from sklearn.neighbors import KernelDensity

__all__ = ["KernelDensityDifference"]

BoundsT = tuple[tuple[float, float], tuple[float, float]]


def get_bounds(gdf) -> BoundsT:
    return (
        (min(gdf.geometry.centroid.x), max(gdf.geometry.centroid.x)),
        (min(gdf.geometry.centroid.y), max(gdf.geometry.centroid.y)),
    )


def max_bounds(
    bounds_a: BoundsT,
    bounds_b: BoundsT,
) -> BoundsT:
    return (
        (
            min(bounds_a[0][0], bounds_b[0][0]),
            max(bounds_a[0][1], bounds_b[0][1]),
        ),
        (
            min(bounds_a[1][0], bounds_b[1][0]),
            max(bounds_a[1][1], bounds_b[1][1]),
        ),
    )


class KernelDensityEstimation(Measure):
    @staticmethod
    def kde_matrix(gdf, bounds=None, bandwidth=5.0) -> np.ndarray:
        bounds_x, bounds_y = bounds if bounds is not None else get_bounds(gdf)
        size = (
            ceil(bounds_x[1] - bounds_x[0]),
            ceil(bounds_y[1] - bounds_y[0]),
        )
        X = np.array(
            [[c.x - bounds_x[0], c.y - bounds_y[0]] for c in gdf.geometry.centroid]
        )
        Y = np.array([[i, j] for i in range(size[0]) for j in range(size[1])])
        kde = KernelDensity(kernel="cosine", bandwidth=bandwidth).fit(X)
        return np.exp(np.reshape(kde.score_samples(Y), size))

    def apply(self, dataset, **options) -> np.ndarray:
        return self.kde_matrix(dataset, **options)


class KernelDensityDifference(MeasureDifference):
    def apply(self, simulation, validation, **options) -> np.ndarray:
        options = {
            **options,
            "bounds": max_bounds(
                get_bounds(simulation),
                get_bounds(validation),
            ),
        }
        k_sim = KernelDensityEstimation().apply(simulation, **options)
        k_real = KernelDensityEstimation().apply(validation, **options)
        return k_sim - k_real

    def apply_validation(self, simulation, validation, **options) -> float:
        return abs(self.apply(simulation, validation).mean())
