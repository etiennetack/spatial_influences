# -*- coding: utf-8 -*-
import numpy as np
from math import pi
from time import time

from multiants.config import load_config
from multiants.logger import NoLogger
from multiants.measures import GridDensity
from multiants.influences.gradient import NoValidStartPoint

from models.sn7 import SN7
from generation.dwelling_factory import ImpossibleBuild
from .base import ProblemBase


class Problem(ProblemBase):
    def __init__(
        self,
        measures,
        n_obj: int,  # objectives functions
        model_config: str,
        **kwargs,
    ):
        self.measures = measures
        self.config_path = model_config

        config = load_config(self.config_path)
        self.validation = self.parse_config__get_validation_dataset(config)
        self.n_new_buildings = self.parse_config__get_n_new_buildings(config)
        border = self.parse_config__get_border(config)
        self.grid_density_grid = GridDensity().build_grid(border, 250)

        # Params MINs
        XL = [0] * 11 + [20, 20]
        # Params MAXs
        XU = (
            [100, 100, 100, 1]  # Neighbours
            + [100, 100, 100, 1]  # Roads
            + [pi / 2, pi / 2, 1]  # Elevation (slope)
            + [1000, 2000]  # area range
        )

        super().__init__(n_var=13, n_obj=n_obj, n_ieq_constr=2, xl=XL, xu=XU, **kwargs)

    @staticmethod
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
            "slope_l_min",
            "slope_l_max",
            "slope_w",
            "area_range_min",
            "area_range_max",
        ]

    @staticmethod
    def build_params(X):
        weight_sum = X[3] + X[7] + X[10]
        return (
            # Neighbours (attraction repulsion)
            [
                X[0],  # lambda min
                X[0] + X[1],  # lambda 0
                X[0] + X[1] + X[2],  # lambda max
                X[3] / weight_sum,  # weight
            ]
            +
            # Roads (attraction repulsion)
            [
                X[4],  # lambda min
                X[4] + X[5],  # lambda 0
                X[4] + X[5] + X[6],  # lambda max
                X[7] / weight_sum,  # weight
            ]
            +
            # Slope (open distance)
            [
                X[8],  # lambda min
                X[9],  # lambda max
                X[10] / weight_sum,  # weight
            ]
            +
            # Area Range
            [
                X[11],  # Min
                X[12],  # Max
            ]
        )

    def _run_simulation(self, X):
        """Run a simulation with the given parameters."""
        start = time()

        model = SN7(load_config(self.config_path), NoLogger())

        params = self.build_params(X)
        model.change_influences(params)

        self.change_landowner_rule(
            (X[11], X[12]),  # try learning those values
            self.n_new_buildings,
        )

        try:
            model.step()
        except ImpossibleBuild:
            # When the gradient descent has not found anything
            return np.array([1e8] * self.n_obj)
        except NoValidStartPoint:
            return np.array([1e8] * self.n_obj)

        return self.apply_measures(model, time() - start)

    def _evaluate(self, x, out, *args, **kwargs):
        if x[8] < x[9]:
            out["F"] = self._run_simulation(x)
        else:
            # if constraints are not respected
            out["F"] = np.stack([1e32] * self.n_obj)

        out["G"] = np.stack(
            [
                x[8] - x[9],
                x[11] - x[12],
            ]
        )
