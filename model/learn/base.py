import sys
import numpy as np
import geopandas as gpd

import pymoo.core.problem as pymoo_problem
from pymoo.util.display.multi import MultiObjectiveOutput
from pymoo.util.display.column import Column

from abmlib.measures import (
    ChamferDistance,
    ChamferDistanceMacro,
    GridDensityDifference,
    KernelDensityDifference,
)

from agents.dwelling import Dwelling
from agents.landowner import LandOwner, ImmigrationBulk

__all__ = ["MyOutput", "ProblemBase"]


class MyOutput(MultiObjectiveOutput):
    """Custom output for the multi-objective optimization."""

    def __init__(self, displayed_measures, widths):
        super().__init__()
        self.n_measures = displayed_measures
        for i in range(len(self.n_measures)):
            attrname = f"fmean_{i}"
            setattr(self, attrname, Column(f"F{i}", widths[i]))
        self.columns += [
            getattr(self, f"fmean_{i}") for i in range(len(self.n_measures))
        ]

    def update(self, algorithm):
        super().update(algorithm)
        fmeans = np.array([f.min() for f in algorithm.pop.get("F").T])
        for i in range(len(self.n_measures)):
            column = getattr(self, f"fmean_{i}")
            start = self.n_measures[i][0]
            end = (
                self.n_measures[i][1] if not len(self.n_measures[i]) == 1 else start + 1
            )

            column.set(fmeans[start:end].mean())
        sys.stdout.flush()


class ProblemBase(pymoo_problem.ElementwiseProblem):
    @staticmethod
    def parse_config__get_validation_dataset(config):
        dwelling_config = next(
            filter(
                lambda a: a["class_name"] == "Dwelling",
                config["agents"],
            )
        )
        return gpd.read_file(dwelling_config["files"][config["validation_date"]])

    @staticmethod
    def parse_config__get_n_new_buildings(config):
        return config["timestep"]["building_delta"]

    @staticmethod
    def parse_config__get_border(config):
        return gpd.read_file(config["border"]["file"])

    def apply_measures(self, model, time):
        """Measure the distance between the simulation and the validation data."""
        dwellings = None

        if any(
            (m in ["kdd", "chamfer_macro"] or "density" in m for m in self.measures)
        ):
            dwellings = model.grid.get_agents_as_GeoDataFrame(Dwelling)

        measures = []
        if "time" in self.measures:
            measures.append(time)
        if "kdd" in self.measures:
            measures.append(
                abs(KernelDensityDifference().apply(dwellings, self.validation).mean())
            )
        if "chamfer_macro" in self.measures:
            measures.append(ChamferDistanceMacro().apply(dwellings, self.validation))
        if "chamfer_micro" in self.measures:
            # do not use
            measures.append(ChamferDistance().apply(dwellings, self.validation))
        # "density_mean" in self.measures or "density_max" in self.measures:
        if any(("density" in m for m in self.measures)):
            density_res = GridDensityDifference().apply_grid(
                dwellings,
                self.validation,
                self.grid_density_grid,
            )
            if "density_mean" in self.measures:
                measures.append(density_res.mean())
            if "density_max" in self.measures:
                measures.append(density_res.max())
        return np.concatenate(
            [[m] if not isinstance(m, np.ndarray) else m for m in measures],
            axis=0,
        )

    @staticmethod
    def change_landowner_rule(building_area_range, n_new_buildings):
        # Change the number of generated buildings
        LandOwner.RULES["immigration_bulk"] = ImmigrationBulk(
            area_range=building_area_range,
            number=n_new_buildings,
        )
