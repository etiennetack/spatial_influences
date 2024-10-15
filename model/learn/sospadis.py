# -*- coding: utf-8 -*-
import numpy as np
from math import pi
from time import time

from multiants.config import load_config
from multiants.logger import NoLogger
from multiants.measures import GridDensity
from multiants.influences.gradient import NoValidStartPoint

from models.sospadis import Sospadis
from generation.dwelling_factory import ImpossibleBuild
from .base import ProblemBase


class Problem(ProblemBase):
    def __init__(
        self,
        measures,
        n_obj: int,
        # model_cls,
        model_config: str,
        **kwargs,
    ):
        self.measures = measures
        self.config_path = model_config

        config = load_config(self.config_path)
        self.validation = self.parse_config__get_validation_dataset(config)
        self.n_new_buildings = self.parse_config__get_n_new_buildings(config)
        border = self.parse_config__get_border(config)
        self.grid_density_grid = GridDensity().build_grid(border, 50)

        # Params MINs
        XL = [0] * 14
        # Params MAXs
        XU = (
            [100, 100, 100, 1]  # Neighbours
            + [100, 100, 100, 1]  # Roads
            + [100, 100, 1]  # Paths
            + [pi / 2, pi / 2, 1]  # Elevation (slope)
        )
        super().__init__(n_var=14, n_obj=n_obj, n_ieq_constr=1, xl=XL, xu=XU, **kwargs)

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
            "paths_l_min",
            "paths_l_max",
            "paths_w",
            "slope_l_min",
            "slope_l_max",
            "slope_w",
        ]

    @staticmethod
    def build_params(X):
        weight_sum = X[3] + X[7] + X[10] + X[13]
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
            # Paths (open distance)
            [
                X[8],  # lambda min
                X[8] + X[9],  # lambda max
                X[10] / weight_sum,  # weight
            ]
            +
            # Slope (open distance)
            [
                X[11],  # lambda min
                X[12],  # lambda max
                X[13] / weight_sum,  # weight
            ]
        )

    def _run_simulation(self, X):
        """Run a simulation with the given parameters."""
        start = time()

        model = Sospadis(load_config(self.config_path), NoLogger())

        params = self.build_params(X)
        model.change_influences(params)

        self.change_landowner_rule((25, 75), self.n_new_buildings)

        try:
            model.step()
        except ImpossibleBuild:
            # When the gradient descent has not found anything
            return np.array([1e8] * self.n_obj)
        except NoValidStartPoint:
            return np.array([1e8] * self.n_obj)

        return self.apply_measures(model, time() - start)

    def _evaluate(self, x, out, *args, **kwargs):
        if x[11] < x[12]:
            out["F"] = self._run_simulation(x)
        else:
            # if constraints are not respected
            out["F"] = np.stack([1e32] * self.n_obj)

        out["G"] = np.stack([x[11] - x[12]])
