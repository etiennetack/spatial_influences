# coding: utf-8
from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Type

import numpy as np
import pymoo.core.problem as pymoo_problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from ..config import load_config
from ..measures.kernel_density_difference import KernelDensityDifference

if TYPE_CHECKING:
    from ..model import Model


class Problem(pymoo_problem.Problem):
    def __init__(self, model, **kwargs):
        self.model = model
        # super().__init__(nvar=2, nobj=2, xl=-2.0, xu=2.0)
        super().__init__(**kwargs)

    def _evaluate(self, x, out, *args, **kwargs):
        # TODO Use expert defined measures here
        # TODO Run model here
        # for each measure
        #     create an optimisation function
        #     and return them into the out["F"] function
        f1 = 100 * (x[:, 0] ** 2 + x[:, 1] ** 2)
        f2 = (x[:, 0] - 1) ** 2 + x[:, 1] ** 2
        out["F"] = np.column_stack([f1, f2])


def create_problem(
    model_cls: Type[Model], model_config, n_var: int, n_obj: int
) -> Type[pymoo_problem.ElementwiseProblem]:
    """Create the optimisation class."""

    class Problem(pymoo_problem.ElementwiseProblem):
        def __init__(
            self,
        ):
            super().__init__(n_var=n_var, n_obj=n_obj, n_ieq_constr=2)

        def run_model(self):
            return None, None

        def _evaluate(self, x, out, *args, **kwargs):
            # get variables for x param
            simulation, validation = self.run_model()
            kdd = KernelDensityDifference().apply(simulation, validation)
            out["F"] = np.sum(kdd)

    return Problem


class ProblemEW(pymoo_problem.ElementwiseProblem):
    def __init__(self, model_cls: Type[Model], model_config, validation_date, **kwargs):
        self.model_cls = model_cls
        self.model_config = model_config
        self.validation_date = validation_date
        # n_var = 3
        # n_obj = 1
        # xl = np.array([-2, -2, -2])  # lower possible value
        # xu = np.array([2, 2, 2])  # upper possible value
        super().__init__(**kwargs)

    def run_model(self, validation_date):
        # change influence system in config
        model = self.model_cls(config=self.model_config)
        # model.add_influence(" ", infl_functions)
        while model.time.current < self.validation_date:
            model.step()
        # Extract generated data
        # Return simulation and validation dataset
        return {}, {}

    def _evaluate(self, x, out, *args, **kwargs):
        simulation, validation = self.run_model()
        KDD = KernelDensityDifference().apply(simulation, validation)
        out["F"] = np.sum(KDD)


def apply_NSGA2(problem):
    algorithm = NSGA2(pop_size=100)
    return minimize(problem, algorithm, ("n_gen", 200), verbose=True)


def learn(model_cls, config_file):
    model = model_cls(config=load_config(config_file))
    problem = ProblemEW(model)
    apply_NSGA2(problem)
