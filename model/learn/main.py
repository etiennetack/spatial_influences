import sys

sys.path.append(".")

import multiprocessing
import click
import random
from pathlib import Path

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import StarmapParallelization
from pymoo.termination.ftol import MultiObjectiveSpaceTermination
from pymoo.termination.robust import RobustTermination
from pymoo.termination.max_gen import MaximumGenerationTermination
from pymoo.termination.collection import TerminationCollection
from pymoo.optimize import minimize

sys.path.append("./model")

import learn.save_results as save_results
from learn.base import MyOutput
from learn.sn7 import Problem as SN7Problem
from learn.valenicina import Problem as ValenicinaProblem


MODELS = {
    "valenicina": ValenicinaProblem,
    "spacenet7": SN7Problem,
}


def run_nsga_ii(
    runner,
    measures,
    model_cls,
    model_config,
    pop_size,
    n_max_gen,
    seed=None,
):
    # Setup the optimisation problem
    problem = model_cls(
        elementwise_runner=runner,
        measures=measures,
        n_obj=len(measures),
        model_config=model_config,
    )

    # Initialise the random seed
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    # GA settings
    algorithm = NSGA2(
        pop_size=pop_size,
        # callback=callback,  # TODO check utility
    )

    # https://pymoo.org/interface/termination.html?highlight=termination
    objective_tolerance = 0.05
    termination = TerminationCollection(
        RobustTermination(
            MultiObjectiveSpaceTermination(tol=objective_tolerance, n_skip=5),
            period=30,
        ),
        MaximumGenerationTermination(n_max_gen=n_max_gen),
    )

    res = minimize(
        problem,
        algorithm,
        termination,
        output=MyOutput(
            [(i,) for i in range(len(measures))],
            [13] * len(measures),
        ),
        verbose=True,
        save_history=True,
        seed=seed,
    )

    return res, seed


@click.command()
@click.option(
    "--nprocess",
    default=1,
    help="The number of process for parallelisation",
)
@click.option(
    "--nmaxgen",
    default=100,
    help="The number of generations for the GA",
)
@click.option(
    "--psize",
    default=50,
    help="The size of the populations of each generation",
)
@click.option(
    "--output",
    default="results",
    help="Path to the results save file",
)
@click.option(
    "--seed",
    default=None,
    type=int,
    help="Random seed",
)
@click.option(
    "--measures",
    default="kdd,chamfer_macro,density_max",
    help="Names of the measures to fit",
)
@click.option("--model", help="spacenet7 or valenicina")
@click.option("--config", help="Simulation config file")
def learn(
    nprocess,
    nmaxgen,
    psize,
    output,
    seed,
    measures,
    model,
    config,
):
    # initialize the thread pool and create the runner
    pool = multiprocessing.Pool(nprocess)
    runner = StarmapParallelization(pool.starmap)

    print("Start learning...")
    measures = tuple(measures.split(","))
    res, seed = run_nsga_ii(
        runner,
        measures,
        MODELS[model],
        config,
        psize,
        nmaxgen,
        seed,
    )

    pool.close()

    print("Seed:", seed)
    print("Threads:", res.exec_time)

    save_results.as_parquets(
        res,
        seed,
        psize,
        Path(output),
        MODELS[model],
        measures,
    )


if __name__ == "__main__":
    learn()
