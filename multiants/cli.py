# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import geopandas as gpd
import os
import click
import dill
from tqdm import tqdm
from mesa_geo import GeoAgent

from .config import load_config, check_config
from .server import Server
from .logger import Logger, NoLogger
from .influences import render as infl_render

from .measures.chamfer_distance import ChamferDistance, ChamferDistanceMacro
from .measures.hausdorff_distance import HausdorffDistance
from .measures.kernel_density_difference import KernelDensityDifference
from .measures.density import GridDensityDifference

__all__ = ["create_cli"]


def parse_params(X):
    weight_sum = sum(
        [
            X[3],
            X[7],
            X[10],
            X[13],
        ]
    )
    return np.array(
        [
            X[0],
            X[0:2].sum(),
            X[0:3].sum(),
            X[3] / weight_sum,
            X[4],
            X[4:6].sum(),
            X[4:7].sum(),
            X[7] / weight_sum,
            X[8],
            X[8:10].sum(),
            X[10] / weight_sum,
            X[11],
            X[11:13].sum(),
            X[13] / weight_sum,
        ]
    )


def read_params(X):
    # TODO: make more generic
    if not isinstance(X, np.ndarray):
        raise Exception(f"X should be an array, it's not it's a {type(X)}")
    elif len(X) == 0:
        raise Exception("X is empty")
    elif not isinstance(X[0], np.ndarray):
        return np.array([parse_params(X)])
    else:
        return np.array([parse_params(x) for x in X])


def read_params_from_result(path):
    with open(path, "rb") as f:
        results_dump = dill.load(f)
        return read_params(results_dump["X"]), results_dump["F"]


def init_base_command(default_model, default_config):
    @click.group()
    @click.option(
        "--model",
        default=default_model,
        help="Which model do you want to use?",
    )
    @click.option(
        "--config",
        default=default_config,
        help="path to configuration file (toml format)",
    )
    @click.pass_context
    def cli(ctx, model, config):
        model_config = load_config(config)
        if not check_config(model_config):
            raise Exception("Configuration file is not valid")
        ctx.ensure_object(dict)
        ctx.obj["CONFIG"] = model_config
        ctx.obj["MODEL"] = model

    return cli


def init_launch_command(cli, models, default_host, default_port):
    @cli.command()
    @click.option(
        "--render-interval",
        default=1,
        help="number of time steps between two renders",
    )
    @click.option(
        "--refresh-time",
        default=0,
        help="minimum time between two renders (in seconds)",
    )
    @click.option("--host", default=default_host, help="websocket listening host")
    @click.option("--port", default=default_port, help="websocker listening port")
    @click.pass_context
    def launch(ctx, render_interval, refresh_time, host, port):
        """
        Main program entry point, initialize the model and launch the server.
        """
        del render_interval  # TODO
        del refresh_time  # TODO
        model = models[ctx.obj["MODEL"]]
        server = Server(model, ctx.obj["CONFIG"])
        server.init_routes()
        server.start(host, port)

    return launch


def init_generate_command(cli, models):
    @cli.command()
    @click.option(
        "--steps",
        default=1,
        help="number of steps to run before output",
    )
    @click.option(
        "--output",
        default="./simulation_results",
        help="path for output",
    )
    @click.pass_context
    def generate(ctx, steps, output):
        model = models[ctx.obj["MODEL"]]
        model_instance = model(ctx.obj["CONFIG"], Logger())
        # Run simulation for the desired number of steps
        for _ in range(steps):
            model_instance.step()
        # Create output directory if it doesn't exists
        if not os.path.exists(output):
            os.makedirs(output)
        # Generate output and save it
        for a_class in model_instance.AGENT_CLASSES:
            # Only save GeoAgents
            if issubclass(a_class, GeoAgent):
                objects = (
                    model_instance.grid.get_agents_as_GeoDataFrame(a_class)
                    # TODO parse parametters
                    .geometry
                )
                objects.to_file(
                    f"{output}/{a_class.__name__.lower()}.geojson",
                    driver="GeoJSON",
                )

    return generate


def init_render_influence_raster_command(cli, models):
    @cli.command()
    @click.option(
        "--influence",
        help="influence name to render",
    )
    @click.option(
        "--output",
        default="./res.tiff",
        help="path for output",
    )
    @click.option(
        "--res",
        default=1.0,
        help="pixel size in meters",
    )
    @click.option(
        "--learningresults",
        default=None,
        help="Learning result file",
    )
    @click.option(
        "--steps",
        type=int,
        default=None,
        help="Steps to generate (if --learningresult is provided)",
    )
    @click.pass_context
    def render_influence_raster(
        ctx,
        influence,
        output,
        res,
        learningresults,
        steps,
    ):
        """Test influence model by rendering a map"""
        params = [None]
        if learningresults is not None:
            params, _ = read_params_from_result(learningresults)

        model = models[ctx.obj["MODEL"]]
        model_instance = model(ctx.obj["CONFIG"], Logger())

        for i, X in enumerate(params):
            if X is not None:
                model_instance._add_influences(X, influence)

            if steps is not None:
                for _ in range(steps):
                    model_instance.step()
            elif learningresults is not None:
                print(
                    "Please provide a number of steps to generate (depending of the validation date and the step size)"
                )
                return

            infl_map = infl_render.render_influence_map(
                model_instance,
                influence,
                res,
            )

            infl_render.save_influence_map(
                model_instance,
                infl_map,
                f"{output.split('.tiff')[0]}_{i}.tiff",
                res,
            )

        return render_influence_raster


def init_read_learning_results_command(cli):
    @cli.command
    @click.option(
        "--learningresults",
        default="./density",
        help="Learning result file",
    )
    def read_learning_results(learningresults):
        print(f"Reading {learningresults} ...")
        with open(learningresults, "rb") as f:
            results = dill.load(f)
        params = read_params(results["X"])
        fitness = results["F"]
        if not isinstance(fitness[0], np.ndarray):
            fitness = np.array([fitness])
        for i, X in enumerate(params):
            print(
                f"Params Set: {i}\n"
                "\n"
                "Bâtiments (distance en m, attraction-répulsion):\n"
                f"Lambda MIN:  {X[0]}\n"
                f"Lambda ZERO: {X[1]}\n"
                f"Lambda MAX:  {X[2]}\n"
                f"Poids:       {X[3]}\n"
                "\n"
                "Route (distance en m, attraction-répulsion):\n"
                f"Lambda MIN:  {X[4]}\n"
                f"Lambda ZERO: {X[5]}\n"
                f"Lambda MAX:  {X[6]}\n"
                f"Poids:       {X[7]}\n"
                "\n"
                "Chemins (distance en m, open distance):\n"
                f"Lambda MIN: {X[8]}\n"
                f"Lambda MAX: {X[9]}\n"
                f"Poids:      {X[10]}\n"
                "\n"
                'Pente (en radiants, "open distance"):\n'
                f"Lambda MIN: {X[11]} ≃ {np.rad2deg(X[11])} degrés\n"
                f"Lambda MAX: {X[12]} ≃ {np.rad2deg(X[12])} degrés\n"
                f"Poids:      {X[13]}\n"
                "\n"
                f"Fitness: {fitness[i]}\n"
            )

        pd.DataFrame(fitness).to_csv(f"{learningresults}.csv")

        return read_learning_results


def init_validate_command(cli, models):
    @cli.command()
    @click.option(
        "--output",
        default="./validation_results",
        help="path for output",
    )
    @click.option(
        "--influence-name",
        help="influence name",
    )
    @click.option(
        "--validation-layer",
        type=str,
        help="validation target",
    )
    @click.option(
        "--validation-data",
        type=str,
        help="path to validation data",
    )
    @click.option(
        "--learningresults",
        default=None,
        help="Learning result file",
    )
    @click.option(
        "--model-steps",
        type=int,
        default=None,
        help="Steps to generate (if --learningresult is provided)",
    )
    @click.option(
        "--evaluation-nb",
        default=100,
    )
    @click.option(
        "--measures",
        type=str,
        help="measures for evaluation separated by commas without spaces (measure_a,measure_b)",
    )
    @click.pass_context
    def validate(
        ctx,
        output,
        influence_name,
        validation_layer,
        validation_data,
        learningresults,
        model_steps,
        evaluation_nb,
        measures,
    ):
        model = models[ctx.obj["MODEL"]]

        AVAILABLE_MEASURES = [
            ChamferDistance,
            ChamferDistanceMacro,
            HausdorffDistance,
            KernelDensityDifference,
            GridDensityDifference,
        ]

        def get_layer_data(model_instance, layer: str):
            match_gen = (
                a_class
                for a_class in model.AGENT_CLASSES
                # match with class name
                if a_class.__name__ == layer.replace("_", " ").title().replace(" ", "")
            )
            try:
                a_class = next(match_gen)
            except StopIteration:
                raise Exception(f"Error: {layer} not found in {model.__name__}")
            return model_instance.grid.get_agents_as_GeoDataFrame(a_class)

        def run_model():
            # instanciate a model instance
            model_instance = model(ctx.obj["CONFIG"], NoLogger())
            # set influence paramaters
            model_instance._add_influences(infl_param, influence_name)
            # run the model to the validation date
            for _ in range(model_steps):
                model_instance.step()
            # extract generated objects
            return get_layer_data(model_instance, validation_layer)

        def get_measure_classes(measures):
            measures_names = measures.split(",")
            return [
                measure_class
                for measure_class in AVAILABLE_MEASURES
                if measure_class.__name__
                in (
                    # transform names in PascalCase to snake_case
                    m.replace("_", " ").title().replace(" ", "")
                    for m in measures_names
                )
            ]

        def apply_measures(measures):
            # evaluate using measures and compare with real data
            res = []
            for measure_class in measures:
                res.append(
                    measure_class()
                    # compare with real data
                    .apply_validation(generated_dataset, control_dataset)
                )
            return res

        param_sets, _ = read_params_from_result(learningresults)
        enabled_measures = get_measure_classes(measures)
        control_dataset = gpd.read_file(validation_data, driver="GeoJSON")

        # for each influence set found by the AG
        for i, infl_param in tqdm(enumerate(param_sets)):
            results = np.empty((evaluation_nb, len(enabled_measures)))
            # run the model `evaluation_nb`th
            for j in tqdm(range(evaluation_nb), desc=f"solution {i}:"):
                generated_dataset = run_model()
                results[j] = apply_measures(enabled_measures)

            # save results
            if not os.path.exists(output):
                os.makedirs(output)
            pd.DataFrame(results).to_csv(f"{output}/{i}.csv")


def create_cli(
    models,
    default_model: str = "some_model",
    default_config: str = "config.toml",
    default_host: str = "127.0.0.1",
    default_port: int = 8888,
):
    """
    Create a command line interface for your model to launch the server
    and render influences matrices.
    """
    cli = init_base_command(default_model, default_config)
    init_launch_command(cli, models, default_host, default_port)
    init_generate_command(cli, models)
    init_render_influence_raster_command(cli, models)
    init_read_learning_results_command(cli)
    init_validate_command(cli, models)
    return cli
